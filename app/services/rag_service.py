import os
import uuid
import requests

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

_session_stores: dict[str, InMemoryVectorStore] = {}
_session_files: dict[str, str] = {}


def _get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def process_pdf(file_path: str, session_id: str | None = None) -> str:
    """
    Load and embed a PDF into an in-memory vector store.
    Returns the session_id.
    """
    if session_id is None:
        session_id = str(uuid.uuid4())

    # Load PDF pages
    loader = PyPDFLoader(file_path)
    pages = loader.load()

    if not pages:
        raise ValueError("Could not extract any text from the PDF.")

    # Split into manageable chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(pages)

    if not chunks:
        raise ValueError("No text chunks produced from the PDF.")

    # Embed and store
    embeddings = _get_embeddings()
    vectorstore = InMemoryVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
    )

    _session_stores[session_id] = vectorstore
    _session_files[session_id] = os.path.basename(file_path)
    return session_id


def process_url(url: str, session_id: str | None = None) -> str:
    """
    Load and embed a URL into an in-memory vector store.
    Returns the session_id.
    """
    if session_id is None:
        session_id = str(uuid.uuid4())
        
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
        
    try:
        loader = WebBaseLoader(url)
        pages = loader.load()
    except Exception as e:
        raise ValueError(f"Could not load website content: {str(e)}")
    
    if not pages:
        raise ValueError("Could not extract any text from the URL.")
        
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(pages)
    
    if not chunks:
        raise ValueError("No text chunks produced from the URL.")
        
    embeddings = _get_embeddings()
    vectorstore = InMemoryVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
    )
    
    _session_stores[session_id] = vectorstore
    _session_files[session_id] = url
    return session_id


def get_retriever(session_id: str, k: int = 4):
    """
    Return a retriever for the given session.
    Raises KeyError if session is not found.
    """
    if session_id not in _session_stores:
        raise KeyError(f"No document found for session_id: {session_id}")
    return _session_stores[session_id].as_retriever(search_kwargs={"k": k})


def list_sessions() -> list[dict]:
    """Return all active sessions with metadata."""
    return [
        {"session_id": sid, "filename": _session_files.get(sid, "unknown")}
        for sid in _session_stores
    ]


def delete_session(session_id: str) -> bool:
    """Remove a session from memory."""
    if session_id not in _session_stores:
        return False
    del _session_stores[session_id]
    _session_files.pop(session_id, None)
    return True
