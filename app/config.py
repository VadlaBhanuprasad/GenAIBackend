"""
Configuration settings loaded from .env
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

OPEN_ROUTER_KEY: str = os.getenv("OPEN_ROUTER_KEY", "").strip().strip('"').strip("'")
OPEN_ROUTER_MODEL: str = os.getenv("OPEN_ROUTER_MODEL", "stepfun/step-3.5-flash:free").strip().strip('"').strip("'")
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
CORS_ORIGINS: list[str] = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000"
).split(",")

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)
