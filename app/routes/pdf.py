"""
PDF upload and RAG query routes.

POST  /api/pdf/upload          — Upload a PDF, process it into ChromaDB, return session_id
POST  /api/pdf/query           — Query the uploaded PDF via RAG (streaming)
GET   /api/pdf/sessions        — List all active sessions
DELETE /api/pdf/session/{id}   — Delete a session and its vector store
"""
import os
import uuid
import asyncio
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import aiofiles

from app.config import UPLOAD_DIR
from app.services.rag_service import process_pdf, process_url, get_retriever, list_sessions, delete_session
from app.services.llm_service import get_openrouter_response, get_system_prompt

router = APIRouter(prefix="/api/pdf", tags=["pdf"])

ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE_MB = 50


def _validate_pdf(filename: str):
    ext = os.path.splitext(filename)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")


# ─────────────────────────────────────────────
# Upload endpoint
# ─────────────────────────────────────────────
@router.post("/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Upload a PDF and process it into a ChromaDB vector store.
    Returns: { session_id, filename, pages_hint }
    """
    _validate_pdf(file.filename)

    session_id = str(uuid.uuid4())
    safe_name = f"{session_id}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    # Save file to disk asynchronously
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size is {MAX_FILE_SIZE_MB} MB.",
            )
        await f.write(content)

    # Process in background so the response returns quickly
    # (for large files this prevents timeout)
    def _process():
        try:
            process_pdf(file_path, session_id=session_id)
        except Exception as e:
            print(f"[RAG] Error processing PDF: {e}")

    background_tasks.add_task(_process)

    return {
        "session_id": session_id,
        "filename": file.filename,
        "message": "PDF uploaded and is being processed. Use the session_id to query it shortly.",
        "status": "processing",
    }


# ─────────────────────────────────────────────
# Synchronous upload + process (smaller files)
# ─────────────────────────────────────────────
@router.post("/upload/sync")
async def upload_pdf_sync(file: UploadFile = File(...)):
    """
    Upload and fully process a PDF before returning.
    Suitable for smaller files (< 10 MB).
    Returns: { session_id, filename, chunk_count }
    """
    _validate_pdf(file.filename)

    session_id = str(uuid.uuid4())
    safe_name = f"{session_id}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    try:
        returned_session = process_pdf(file_path, session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

    return {
        "session_id": returned_session,
        "filename": file.filename,
        "status": "ready",
        "message": "PDF processed successfully. You can now query it.",
    }


class URLRequest(BaseModel):
    url: str

@router.post("/url/sync")
async def upload_url_sync(req: URLRequest):
    """
    Process a web URL directly into a session.
    """
    if not req.url:
        raise HTTPException(status_code=400, detail="URL is required")

    session_id = str(uuid.uuid4())

    try:
        returned_session = process_url(req.url, session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process URL: {str(e)}")

    return {
        "session_id": returned_session,
        "filename": req.url,
        "status": "ready",
        "message": "URL processed successfully. You can now query it.",
    }


# ─────────────────────────────────────────────
# Query endpoint (streaming)
# ─────────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str
    session_id: str
    top_k: int = 4


async def _stream_rag(retriever, question: str):
    """SSE token stream for RAG using OpenRouter."""
    import traceback
    try:
        system_prompt = get_system_prompt("document")
        docs = retriever.invoke(question)
        context = "\n\n".join(doc.page_content for doc in docs)
        messages = [
            {"role": "system", "content": system_prompt + f"\n\nContext:\n{context}"},
            {"role": "user", "content": question},
        ]
        import json
        content = await get_openrouter_response(messages)
        chunk_size = 8
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i+chunk_size]
            yield f"data: {json.dumps(chunk)}\n\n".encode("utf-8")
            await asyncio.sleep(0.01)
    except Exception as exc:
        traceback.print_exc()
        yield f"data: [ERROR] {str(exc)}\n\n".encode("utf-8")
    finally:
        yield b"data: [DONE]\n\n"


@router.post("/query")
async def query_pdf(req: QueryRequest):
    """
    Ask a question about an uploaded PDF using the RAG pipeline.
    Streams the answer as Server-Sent Events.
    """
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        retriever = get_retriever(req.session_id, k=req.top_k)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No document found for session_id '{req.session_id}'. "
                "Please upload a PDF first."
            ),
        )

    return StreamingResponse(
        _stream_rag(retriever, req.question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ─────────────────────────────────────────────
# Session management
# ─────────────────────────────────────────────
@router.get("/sessions")
async def get_sessions():
    """List all active PDF sessions."""
    return {"sessions": list_sessions()}


@router.delete("/session/{session_id}")
async def remove_session(session_id: str):
    """Delete a PDF session and remove its vector store from disk."""
    success = delete_session(session_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found.",
        )
    return {"message": f"Session '{session_id}' deleted successfully."}
