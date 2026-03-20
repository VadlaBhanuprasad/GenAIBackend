# Use a lightweight Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Set work directory
WORKDIR /app

# Install system dependencies (build-essential needed for some scikit/numpy builds)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Force the installation of the CPU-only version of PyTorch
# This is CRITICAL to keep the image size small (< 1GB instead of 8GB+)
# Railway and Render do not provide GPUs on free/standard tiers
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy and install rest of dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Ensure storage directories exist
RUN mkdir -p uploads chroma_db

# Pre-download the embedding model (~400MB) during build to speed up cold starts
# This avoids downloading the 400MB+ model every time the container spins up
RUN python -c "from langchain_huggingface import HuggingFaceEmbeddings; HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')"

# Expose the assigned PORT (defaulted to 8000)
EXPOSE 8000

# Run the FastAPI app via uvicorn
# We use the PORT environment variable to allow cloud platform overrides
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
