@echo off
echo Starting GenAI Chat Backend...
call .venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
