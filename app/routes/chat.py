"""
Chat route — handles general, coding, and document (RAG) modes with SSE streaming.

POST /api/chat
Body: { "message": str, "mode": "general"|"coding"|"document", "session_id": str|None }

Streams: text/event-stream with data: <chunk>\n\n format
"""
import asyncio
import traceback
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.llm_service import get_openrouter_response, get_system_prompt
from app.services.rag_service import get_retriever

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    mode: str = "general"          # "general" | "coding" | "document"
    session_id: str | None = None  # Required when mode="document"


async def _stream_chain(system_prompt: str, question: str, retriever=None):
    try:
        messages = [{"role": "system", "content": system_prompt}]

        if retriever:
            docs = retriever.invoke(question)
            context = "\n\n".join(doc.page_content for doc in docs)
            messages[0]["content"] += f"\n\nContext:\n{context}"

        messages.append({"role": "user", "content": question})

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

@router.post("/chat")
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    retriever = None
    if req.mode == "document":
        if not req.session_id:
            raise HTTPException(status_code=400, detail="session_id is required for document mode. Upload a PDF first.")
        try:
            retriever = get_retriever(req.session_id)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"No document found for session_id: {req.session_id}")

    system_prompt = get_system_prompt(req.mode)
    return StreamingResponse(
        _stream_chain(system_prompt, req.message, retriever),
        media_type="text/event-stream; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/chat/health")
async def health():
    """Quick health check for the chat service."""
    return {"status": "ok", "service": "chat"}
