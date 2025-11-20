"""
RAG Evaluation Framework

This package provides comprehensive evaluation capabilities for RAG systems:
- Retrieval quality metrics (Precision, Recall, NDCG, MRR, MAP)
- Generation quality metrics (Relevance, Faithfulness, Completeness)
- Comparative analysis tools
"""

from .evaluator import RAGEvaluator
from .metrics import (
    precision_at_k,
    recall_at_k,
    f1_score_at_k,
    ndcg_at_k,
    mean_reciprocal_rank,
    mean_average_precision
)

__version__ = "1.0.0"
__all__ = [
    "RAGEvaluator",
    "precision_at_k",
    "recall_at_k",
    "f1_score_at_k",
    "ndcg_at_k",
    "mean_reciprocal_rank",
    "mean_average_precision"
]
