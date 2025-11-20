"""
Evaluation Metrics for RAG Systems

This module implements standard information retrieval and generation quality metrics:

Retrieval Metrics:
- Precision@K: Proportion of relevant documents in top-K
- Recall@K: Proportion of relevant documents retrieved
- F1@K: Harmonic mean of precision and recall
- NDCG@K: Normalized Discounted Cumulative Gain
- MRR: Mean Reciprocal Rank
- MAP: Mean Average Precision

Generation Metrics:
- Relevance: How well answer addresses the query
- Faithfulness: How well answer is grounded in retrieved context
- Completeness: How comprehensive the answer is
"""

import math
from typing import List, Dict, Any, Set
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== Retrieval Metrics ====================

def precision_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int = None) -> float:
    """
    Calculate Precision@K
    
    Precision@K = (# relevant docs in top-K) / K
    
    Args:
        retrieved_ids: List of retrieved document IDs (in rank order)
        relevant_ids: Set of relevant document IDs
        k: Number of top results to consider (default: all)
        
    Returns:
        float: Precision score [0, 1]
    """
    if not retrieved_ids:
        return 0.0
    
    if k is None:
        k = len(retrieved_ids)
    
    top_k = retrieved_ids[:k]
    relevant_in_top_k = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    
    return relevant_in_top_k / k


def recall_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int = None) -> float:
    """
    Calculate Recall@K
    
    Recall@K = (# relevant docs in top-K) / (total # relevant docs)
    
    Args:
        retrieved_ids: List of retrieved document IDs
        relevant_ids: Set of relevant document IDs
        k: Number of top results to consider (default: all)
        
    Returns:
        float: Recall score [0, 1]
    """
    if not relevant_ids:
        return 0.0
    
    if k is None:
        k = len(retrieved_ids)
    
    top_k = retrieved_ids[:k]
    relevant_in_top_k = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    
    return relevant_in_top_k / len(relevant_ids)


def f1_score_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int = None) -> float:
    """
    Calculate F1 Score@K
    
    F1@K = 2 * (Precision@K * Recall@K) / (Precision@K + Recall@K)
    
    Args:
        retrieved_ids: List of retrieved document IDs
        relevant_ids: Set of relevant document IDs
        k: Number of top results to consider (default: all)
        
    Returns:
        float: F1 score [0, 1]
    """
    precision = precision_at_k(retrieved_ids, relevant_ids, k)
    recall = recall_at_k(retrieved_ids, relevant_ids, k)
    
    if precision + recall == 0:
        return 0.0
    
    return 2 * (precision * recall) / (precision + recall)


def dcg_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int = None) -> float:
    """
    Calculate Discounted Cumulative Gain@K
    
    DCG@K = sum(rel_i / log2(i+1)) for i in [1, K]
    
    Args:
        retrieved_ids: List of retrieved document IDs
        relevant_ids: Set of relevant document IDs
        k: Number of top results to consider (default: all)
        
    Returns:
        float: DCG score
    """
    if not retrieved_ids:
        return 0.0
    
    if k is None:
        k = len(retrieved_ids)
    
    dcg = 0.0
    for i, doc_id in enumerate(retrieved_ids[:k]):
        # Binary relevance: 1 if relevant, 0 otherwise
        relevance = 1 if doc_id in relevant_ids else 0
        # Position is 1-indexed
        dcg += relevance / math.log2(i + 2)
    
    return dcg


def ndcg_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int = None) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain@K
    
    NDCG@K = DCG@K / IDCG@K
    
    Args:
        retrieved_ids: List of retrieved document IDs
        relevant_ids: Set of relevant document IDs
        k: Number of top results to consider (default: all)
        
    Returns:
        float: NDCG score [0, 1]
    """
    if not relevant_ids:
        return 0.0
    
    if k is None:
        k = len(retrieved_ids)
    
    # Calculate DCG
    dcg = dcg_at_k(retrieved_ids, relevant_ids, k)
    
    # Calculate IDCG (ideal DCG - all relevant docs at top)
    ideal_retrieved = list(relevant_ids) + [f"dummy_{i}" for i in range(k - len(relevant_ids))]
    ideal_retrieved = ideal_retrieved[:k]
    idcg = dcg_at_k(ideal_retrieved, relevant_ids, k)
    
    if idcg == 0:
        return 0.0
    
    return dcg / idcg


def mean_reciprocal_rank(retrieved_ids: List[str], relevant_ids: Set[str]) -> float:
    """
    Calculate Mean Reciprocal Rank (MRR)
    
    MRR = 1 / rank of first relevant document
    
    Args:
        retrieved_ids: List of retrieved document IDs
        relevant_ids: Set of relevant document IDs
        
    Returns:
        float: MRR score [0, 1]
    """
    if not retrieved_ids or not relevant_ids:
        return 0.0
    
    for i, doc_id in enumerate(retrieved_ids):
        if doc_id in relevant_ids:
            return 1.0 / (i + 1)
    
    return 0.0


def average_precision(retrieved_ids: List[str], relevant_ids: Set[str]) -> float:
    """
    Calculate Average Precision (AP)
    
    AP = (sum of Precision@i for all relevant docs) / (total # relevant docs)
    
    Args:
        retrieved_ids: List of retrieved document IDs
        relevant_ids: Set of relevant document IDs
        
    Returns:
        float: AP score [0, 1]
    """
    if not relevant_ids:
        return 0.0
    
    if not retrieved_ids:
        return 0.0
    
    precisions = []
    num_relevant = 0
    
    for i, doc_id in enumerate(retrieved_ids):
        if doc_id in relevant_ids:
            num_relevant += 1
            precision = num_relevant / (i + 1)
            precisions.append(precision)
    
    if not precisions:
        return 0.0
    
    return sum(precisions) / len(relevant_ids)


def mean_average_precision(results: List[Dict[str, Any]]) -> float:
    """
    Calculate Mean Average Precision (MAP) across multiple queries
    
    MAP = mean(AP for all queries)
    
    Args:
        results: List of result dictionaries with 'retrieved_ids' and 'relevant_ids'
        
    Returns:
        float: MAP score [0, 1]
    """
    if not results:
        return 0.0
    
    aps = []
    for result in results:
        ap = average_precision(result['retrieved_ids'], set(result['relevant_ids']))
        aps.append(ap)
    
    return sum(aps) / len(aps) if aps else 0.0


# ==================== Generation Quality Metrics ====================

def calculate_relevance_score(answer: str, query: str, context: str = None) -> float:
    """
    Calculate relevance score (simplified version)
    
    In production, use LLM-based evaluation or learned metrics
    
    Args:
        answer: Generated answer
        query: Original query
        context: Retrieved context (optional)
        
    Returns:
        float: Relevance score [0, 1]
    """
    # Simple keyword-based relevance (for demonstration)
    # In production, use more sophisticated methods (BERTScore, LLM judge, etc.)
    
    if not answer or not query:
        return 0.0
    
    # Extract keywords from query (simple approach)
    query_words = set(query.lower().split())
    answer_words = set(answer.lower().split())
    
    # Calculate overlap
    overlap = len(query_words & answer_words)
    
    if len(query_words) == 0:
        return 0.0
    
    # Simple overlap-based score
    score = min(overlap / len(query_words), 1.0)
    
    # Bonus for answer length (not too short, not too long)
    length_factor = 1.0
    if len(answer.split()) < 10:
        length_factor = 0.8
    elif len(answer.split()) > 500:
        length_factor = 0.9
    
    return score * length_factor


def calculate_faithfulness_score(answer: str, context: str) -> float:
    """
    Calculate faithfulness score (how grounded answer is in context)
    
    Args:
        answer: Generated answer
        context: Retrieved context
        
    Returns:
        float: Faithfulness score [0, 1]
    """
    if not answer or not context:
        return 0.0
    
    # Simple approach: check if key phrases in answer appear in context
    # In production, use NLI models or LLM-based evaluation
    
    answer_sentences = answer.split('.')
    context_lower = context.lower()
    
    grounded_sentences = 0
    for sentence in answer_sentences:
        sentence = sentence.strip().lower()
        if not sentence:
            continue
        
        # Check if main content words appear in context
        words = [w for w in sentence.split() if len(w) > 3]
        if not words:
            continue
        
        # If most words appear in context, consider sentence grounded
        grounded_words = sum(1 for w in words if w in context_lower)
        if grounded_words / len(words) > 0.5:
            grounded_sentences += 1
    
    total_sentences = len([s for s in answer_sentences if s.strip()])
    
    if total_sentences == 0:
        return 0.0
    
    return grounded_sentences / total_sentences


def calculate_completeness_score(answer: str, ground_truth: str = None) -> float:
    """
    Calculate completeness score
    
    Args:
        answer: Generated answer
        ground_truth: Ground truth answer (optional)
        
    Returns:
        float: Completeness score [0, 1]
    """
    if not answer:
        return 0.0
    
    # If ground truth provided, compare coverage
    if ground_truth:
        gt_words = set(ground_truth.lower().split())
        answer_words = set(answer.lower().split())
        
        if not gt_words:
            return 0.5
        
        # Calculate coverage of ground truth concepts
        coverage = len(gt_words & answer_words) / len(gt_words)
        return min(coverage, 1.0)
    
    # Without ground truth, use heuristics
    # Check answer length and structure
    score = 0.0
    
    # Length check (50-500 words is good)
    word_count = len(answer.split())
    if 50 <= word_count <= 500:
        score += 0.5
    elif 20 <= word_count < 50 or 500 < word_count <= 1000:
        score += 0.3
    else:
        score += 0.1
    
    # Structure check (has multiple sentences)
    sentence_count = len([s for s in answer.split('.') if s.strip()])
    if sentence_count >= 3:
        score += 0.3
    elif sentence_count >= 2:
        score += 0.2
    else:
        score += 0.0
    
    # Has some detail (longer sentences)
    avg_sentence_length = word_count / max(sentence_count, 1)
    if avg_sentence_length >= 10:
        score += 0.2
    else:
        score += 0.0
    
    return min(score, 1.0)


# ==================== Batch Evaluation ====================

def evaluate_retrieval_batch(results: List[Dict[str, Any]], k: int = 5) -> Dict[str, float]:
    """
    Evaluate retrieval quality across multiple queries
    
    Args:
        results: List of result dictionaries with 'retrieved_ids' and 'relevant_ids'
        k: Cutoff for metrics
        
    Returns:
        Dict[str, float]: Dictionary of averaged metrics
    """
    if not results:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "ndcg": 0.0,
            "mrr": 0.0,
            "map": 0.0
        }
    
    metrics = {
        "precision": [],
        "recall": [],
        "f1": [],
        "ndcg": [],
        "mrr": [],
        "ap": []
    }
    
    for result in results:
        retrieved = result['retrieved_ids']
        relevant = set(result['relevant_ids'])
        
        metrics["precision"].append(precision_at_k(retrieved, relevant, k))
        metrics["recall"].append(recall_at_k(retrieved, relevant, k))
        metrics["f1"].append(f1_score_at_k(retrieved, relevant, k))
        metrics["ndcg"].append(ndcg_at_k(retrieved, relevant, k))
        metrics["mrr"].append(mean_reciprocal_rank(retrieved, relevant))
        metrics["ap"].append(average_precision(retrieved, relevant))
    
    # Calculate averages
    averaged_metrics = {
        "average_precision": sum(metrics["precision"]) / len(metrics["precision"]),
        "average_recall": sum(metrics["recall"]) / len(metrics["recall"]),
        "average_f1": sum(metrics["f1"]) / len(metrics["f1"]),
        "average_ndcg": sum(metrics["ndcg"]) / len(metrics["ndcg"]),
        "average_mrr": sum(metrics["mrr"]) / len(metrics["mrr"]),
        "average_map": sum(metrics["ap"]) / len(metrics["ap"])
    }
    
    return averaged_metrics
