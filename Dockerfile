# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
# Tell HuggingFace / sentence-transformers where to cache models
ENV HF_HOME=/app/.cache/huggingface
ENV SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence_transformers

# Set work directory
WORKDIR /app

# Install only the runtime system libraries needed by PyTorch CPU and
# sentence-transformers (libgomp for OpenMP, libgfortran for BLAS).
# build-essential is NOT needed — all wheels are pre-built.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libgfortran5 \
    && rm -rf /var/lib/apt/lists/*

# ── Install PyTorch CPU-only FIRST ──────────────────────────────────────────
# Explicitly pulling the CPU-only wheel (~250 MB) before requirements.txt
# prevents pip from resolving the default CUDA wheel (~2.5 GB) when
# sentence-transformers / transformers pull in torch as a dependency.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        torch==2.1.0 \
        torchvision==0.16.0 \
        --index-url https://download.pytorch.org/whl/cpu

# ── Install remaining application dependencies ───────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads chroma_db

# Pre-download the HuggingFace embedding model used in the RAG service.
# Baking it into the image avoids a cold-start download on every deploy.
RUN python -c "from langchain_huggingface import HuggingFaceEmbeddings; HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')"

# Expose the port
EXPOSE ${PORT}

# Run the app
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
