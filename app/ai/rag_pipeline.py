"""Main RAG pipeline - imports and re-exports from modular components.

This module maintains backward compatibility while the logic is now split across:
- answer_evaluator.py: LLM-based answer checking
- retrieval.py: RAG context retrieval with LangChain
- feedback_generator.py: Feedback generation orchestration

For new code, import directly from the specific modules.
"""
from __future__ import annotations

from typing import Dict, List, Sequence

# Import from specialized modules
from ai.answer_evaluator import evaluate_student_answer
from ai.feedback_generator import generate_tutor_feedback
from ai.retrieval import (
    create_retriever,
    explain_contexts,
    load_vector_store,
    retrieve_context,
)

# Re-export for backward compatibility
__all__ = [
    "evaluate_student_answer",
    "generate_tutor_feedback",
    "load_vector_store",
    "create_retriever",
    "retrieve_context",
    "explain_contexts",
]


# Deprecated aliases for backward compatibility
def _retrieve_context(query: str, top_k: int = 5) -> List[Dict[str, object]]:
    """Deprecated: Use retrieve_context() from ai.retrieval instead."""
    return retrieve_context(query, top_k)