"""
FastAPI Application Entry Point (Reloaded to apply CORS changes)

Routes:
  POST   /api/chat              — Stream chat (general/coding/document modes)
  POST   /api/pdf/upload        — Upload PDF (async background processing)
  POST   /api/pdf/upload/sync   — Upload + process PDF synchronously
  POST   /api/pdf/query         — Stream RAG answer from uploaded PDF
  GET    /api/pdf/sessions      — List active PDF sessions
  DELETE /api/pdf/session/{id}  — Delete a PDF session
  GET    /api/models            — List available OpenRouter models
  GET    /health                — Health check
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.routes import chat, pdf, models

app = FastAPI(
    title="GenAI Chat API",
    description="Real-time AI chat with OpenRouter API and RAG pipeline for PDF Q&A",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────────────────────
app.include_router(chat.router)
app.include_router(pdf.router)
app.include_router(models.router)


# ── Root health check ───────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health():
    return {
        "status": "ok",
        "message": "GenAI Chat API is running",
        "docs": "/docs",
    }


@app.get("/", tags=["health"])
async def root():
    return {
        "api": "GenAI Chat API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "chat": "POST /api/chat",
            "upload_pdf": "POST /api/pdf/upload/sync",
            "query_pdf": "POST /api/pdf/query",
            "list_sessions": "GET /api/pdf/sessions",
            "list_models": "GET /api/models",
        },
    }
