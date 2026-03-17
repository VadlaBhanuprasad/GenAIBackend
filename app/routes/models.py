"""
Models route — returns available OpenRouter models.
"""
from fastapi import APIRouter
from app.config import OPEN_ROUTER_MODEL

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
async def list_models():
    """Return the configured OpenRouter model."""
    return {"models": [OPEN_ROUTER_MODEL]}
