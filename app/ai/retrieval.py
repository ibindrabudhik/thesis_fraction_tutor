"""RAG retrieval using LangChain and FAISS vector store."""
from __future__ import annotations

import hashlib
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Sequence, Optional
from concurrent.futures import ThreadPoolExecutor

# Load environment variables from .env file if running outside Streamlit
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, will rely on system env vars or Streamlit secrets

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

BASE_DIR = Path(__file__).resolve().parents[2]
VECTOR_STORE_DIR = BASE_DIR / "data" / "vector_store"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-large"

# Cache for query results to avoid repeated retrieval
_query_cache: Dict[str, List[Dict[str, object]]] = {}
_MAX_CACHE_SIZE = 128


class MissingAPIKeyError(RuntimeError):
    """Raised when the OpenAI API key cannot be located."""


def _read_openai_key() -> str:
    """Retrieve the OpenAI API key from environment variables or Streamlit secrets."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
            key = None
    if not key:
        raise MissingAPIKeyError(
            "OPENAI_API_KEY is missing. Set it via environment variable or Streamlit secrets."
        )
    return key


def _get_cache_key(query: str, top_k: int) -> str:
    """Generate a cache key for query results."""
    return hashlib.md5(f"{query}:{top_k}".encode()).hexdigest()


@lru_cache(maxsize=1)
def load_vector_store():
    """Load the FAISS vector store using LangChain with index warming."""
    # Use the default 'index' name which works with the current vector store structure
    index_name = "index"
    
    faiss_path = VECTOR_STORE_DIR / f"{index_name}.faiss"
    pkl_path = VECTOR_STORE_DIR / f"{index_name}.pkl"
    
    if not faiss_path.exists():
        raise FileNotFoundError(f"FAISS index not found at {faiss_path}")
    if not pkl_path.exists():
        raise FileNotFoundError(f"FAISS pkl not found at {pkl_path}")
    
    # Initialize embeddings model
    embeddings = OpenAIEmbeddings(
        model=OPENAI_EMBEDDING_MODEL,
        openai_api_key=_read_openai_key()
    )
    
    # Load FAISS vector store
    vector_store = FAISS.load_local(
        folder_path=str(VECTOR_STORE_DIR),
        embeddings=embeddings,
        index_name=index_name,
        allow_dangerous_deserialization=True
    )
    print(f"Successfully loaded FAISS index from {VECTOR_STORE_DIR}")
    
    # Warm up the index with a dummy search to avoid first-query latency
    try:
        vector_store.similarity_search("test warmup", k=1)
        print("FAISS index warmed up successfully")
    except Exception as e:
        print(f"Warning: FAISS warmup failed: {e}")
    
    return vector_store


def get_retriever(top_k: int = 5, score_threshold: float = 0.3):
    """Create a LangChain retriever with similarity score threshold.
    
    Note: Not cached because top_k may vary per call.
    """
    vector_store = load_vector_store()
    
    # Create retriever with similarity score threshold
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": top_k,
            "score_threshold": score_threshold
        }
    )
    
    return retriever


# Keep old function name for backwards compatibility
@lru_cache(maxsize=1)
def create_retriever(top_k: int = 5, score_threshold: float = 0.3):
    """Create a LangChain retriever with similarity score threshold."""
    return get_retriever(top_k=top_k, score_threshold=score_threshold)


def retrieve_context(query: str, top_k: int = 5, use_cache: bool = True) -> List[Dict[str, object]]:
    """Return the top-k chunk payloads ranked by cosine similarity using LangChain.
    
    Args:
        query: The search query
        top_k: Number of results to retrieve
        use_cache: Whether to use cached results for identical queries
        
    Returns:
        List of context dicts with 'text' and 'score' keys
    """
    global _query_cache
    
    # Check cache first
    if use_cache:
        cache_key = _get_cache_key(query, top_k)
        if cache_key in _query_cache:
            print(f"Cache hit for query (top_k={top_k})")
            return _query_cache[cache_key]
    
    vector_store = load_vector_store()
    
    # Use similarity_search_with_relevance_scores to get actual cosine-based scores
    results = vector_store.similarity_search_with_relevance_scores(query, k=top_k)
    
    # Filter by score threshold and convert to expected format.
    # Explicitly cast score to native Python float so downstream json.dumps
    # (chat_service / Supabase) never chokes on numpy.float64.
    score_threshold = 0.3
    contexts = []
    for doc, raw_score in results:
        score = float(raw_score)
        if score >= score_threshold:
            contexts.append({"text": doc.page_content, "score": score})
    
    if contexts:
        scores_str = ", ".join(f"{c['score']:.3f}" for c in contexts)
        print(f"Retrieved {len(contexts)} documents (scores: {scores_str}) from {len(results)} candidates")
    else:
        print(f"No documents passed threshold ({score_threshold}) out of {len(results)} candidates")
    
    # Cache the results
    if use_cache and len(_query_cache) < _MAX_CACHE_SIZE:
        cache_key = _get_cache_key(query, top_k)
        _query_cache[cache_key] = contexts
    
    return contexts


def prefetch_problem_context(problem: str, top_k: int = 5) -> List[Dict[str, object]]:
    """Pre-fetch and cache contexts for a problem statement.
    
    Call this at session start to avoid retrieval latency on first interaction.
    
    Args:
        problem: The problem statement
        top_k: Number of results to retrieve
        
    Returns:
        List of context dicts
    """
    return retrieve_context(problem, top_k=top_k, use_cache=True)


def clear_query_cache():
    """Clear the query result cache."""
    global _query_cache
    _query_cache = {}
    print("Query cache cleared")


def explain_contexts(contexts: Sequence[Dict[str, object]]) -> List[str]:
    """Format retrieved contexts for UI display or logging."""
    formatted: List[str] = []
    for idx, ctx in enumerate(contexts, start=1):
        text = str(ctx.get("text", "")).strip()
        score = ctx.get("score")
        # Accept any numeric type (float, int, numpy scalar) — scores
        # may arrive as native float from retrieval or from json.loads.
        try:
            score_str = f" (skor: {float(score):.3f})" if score is not None else ""
        except (TypeError, ValueError):
            score_str = ""
        formatted.append(f"Sumber {idx}{score_str}:\n{text}")
    return formatted
