# GenAI Chat Backend (FastAPI)

FastAPI-powered AI backend with RAG (Retrieval-Augmented Generation) for PDF and Web querying, leveraging OpenRouter for LLM access and HuggingFace for embeddings.

## 🚀 Deployment (Render)

This repository includes a `render.yaml` blueprint for easy deployment on Render.

1.  Push this code to your GitHub repo.
2.  Go to [Render Dashboard](https://dashboard.render.com/blueprints).
3.  Choose **New Blueprint Instance**.
4.  Connect this repository.
5.  Provide the `OPEN_ROUTER_KEY` when prompted.

### Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `OPEN_ROUTER_KEY` | Your OpenRouter API Key | |
| `OPEN_ROUTER_MODEL` | Preferred model (e.g., `stepfun/step-3.5-flash:free`) | `stepfun/step-3.5-flash:free` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000` |
| `PORT` | The port the server listens on | `8000` |

## 🛠 Local Setup

1.  **Clone the Repo**:
    ```bash
    git clone https://github.com/VadlaBhanuprasad/GenAIBackend.git
    cd GenAIBackend
    ```

2.  **Install dependencies**:
    ```bash
    python -m venv .venv
    # Windows:
    .venv\Scripts\activate
    # Linux/MacOS:
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configure environment**: 
    Create a `.env` file from the variables listed above.

4.  **Run with uvicorn**:
    ```bash
    uvicorn main:app --reload
    ```

## 🔌 API Endpoints

- **GET `/health`**: Check system status.
- **POST `/api/chat`**: Standard LLM chat.
- **POST `/api/pdf/upload`**: Upload and process PDF for RAG.
- **POST `/api/pdf/query`**: Stream questions against documents using RAG.
