"""
RAG Evaluator

This module provides a comprehensive evaluation framework for RAG systems.
It evaluates both retrieval quality and generation quality.
"""

from typing import List, Dict, Any, Optional
import logging
import time
from .metrics import (
    evaluate_retrieval_batch,
    calculate_relevance_score,
    calculate_faithfulness_score,
    calculate_completeness_score
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEvaluator:
    """
    Comprehensive evaluator for RAG systems
    
    Evaluates:
    1. Retrieval Quality (Precision, Recall, NDCG, MRR, MAP)
    2. Generation Quality (Relevance, Faithfulness, Completeness)
    3. System Performance (Latency)
    """
    
    def __init__(self, k: int = 5):
        """
        Initialize evaluator
        
        Args:
            k: Cutoff for retrieval metrics
        """
        self.k = k
        logger.info(f"RAGEvaluator initialized with k={k}")
    
    def evaluate(self, rag_system, test_queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate RAG system on test queries
        
        Args:
            rag_system: RAG system to evaluate (VectorRAG, GraphRAG, or HybridRAG)
            test_queries: List of test queries with format:
                [
                    {
                        "query": "question text",
                        "relevant_doc_ids": ["doc_1", "doc_2"],
                        "ground_truth": "expected answer" (optional)
                    }
                ]
        
        Returns:
            Dict[str, Any]: Comprehensive evaluation results
        """
        logger.info(f"Starting evaluation on {len(test_queries)} queries")
        
        results = {
            "num_queries": len(test_queries),
            "retrieval_results": [],
            "generation_results": [],
            "latencies": []
        }
        
        for i, test_item in enumerate(test_queries):
            logger.info(f"Evaluating query {i+1}/{len(test_queries)}")
            
            query = test_item["query"]
            relevant_doc_ids = set(test_item.get("relevant_doc_ids", []))
            ground_truth = test_item.get("ground_truth", None)
            
            # Run query and measure latency
            start_time = time.time()
            response = rag_system.query(query, top_k=self.k)
            latency = time.time() - start_time
            
            results["latencies"].append(latency)
            
            # Extract retrieved document IDs
            retrieved_docs = response["retrieved_documents"]
            retrieved_ids = [doc["id"] for doc in retrieved_docs]
            
            # Store retrieval results
            results["retrieval_results"].append({
                "query": query,
                "retrieved_ids": retrieved_ids,
                "relevant_ids": list(relevant_doc_ids)
            })
            
            # Evaluate generation quality
            answer = response["answer"]
            context = "\n".join([doc["text"] for doc in retrieved_docs])
            
            generation_scores = {
                "query": query,
                "answer": answer,
                "relevance": calculate_relevance_score(answer, query, context),
                "faithfulness": calculate_faithfulness_score(answer, context),
                "completeness": calculate_completeness_score(answer, ground_truth)
            }
            
            results["generation_results"].append(generation_scores)
        
        # Calculate aggregate metrics
        results["metrics"] = evaluate_retrieval_batch(results["retrieval_results"], self.k)
        
        # Calculate aggregate generation metrics
        gen_results = results["generation_results"]
        results["generation_metrics"] = {
            "average_relevance": sum(r["relevance"] for r in gen_results) / len(gen_results),
            "average_faithfulness": sum(r["faithfulness"] for r in gen_results) / len(gen_results),
            "average_completeness": sum(r["completeness"] for r in gen_results) / len(gen_results)
        }
        
        # Calculate performance metrics
        results["performance_metrics"] = {
            "average_latency": sum(results["latencies"]) / len(results["latencies"]),
            "min_latency": min(results["latencies"]),
            "max_latency": max(results["latencies"])
        }
        
        logger.info("Evaluation complete")
        logger.info(f"Average Precision@{self.k}: {results['metrics']['average_precision']:.3f}")
        logger.info(f"Average Recall@{self.k}: {results['metrics']['average_recall']:.3f}")
        logger.info(f"Average NDCG@{self.k}: {results['metrics']['average_ndcg']:.3f}")
        logger.info(f"Average Relevance: {results['generation_metrics']['average_relevance']:.3f}")
        
        return results
    
    def compare_systems(self, systems: Dict[str, Any], test_queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare multiple RAG systems
        
        Args:
            systems: Dictionary of {system_name: system_instance}
            test_queries: List of test queries
            
        Returns:
            Dict[str, Any]: Comparison results for all systems
        """
        logger.info(f"Comparing {len(systems)} systems")
        
        comparison = {}
        
        for system_name, system in systems.items():
            logger.info(f"Evaluating {system_name}...")
            comparison[system_name] = self.evaluate(system, test_queries)
        
        # Create comparison summary
        comparison["summary"] = self._create_comparison_summary(comparison)
        
        logger.info("Comparison complete")
        return comparison
    
    def _create_comparison_summary(self, comparison: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create summary comparing all systems
        
        Args:
            comparison: Comparison results
            
        Returns:
            Dict[str, Any]: Summary with rankings
        """
        summary = {
            "rankings": {},
            "best_system": {}
        }
        
        # Metrics to compare
        metrics = [
            ("average_precision", "metrics"),
            ("average_recall", "metrics"),
            ("average_f1", "metrics"),
            ("average_ndcg", "metrics"),
            ("average_mrr", "metrics"),
            ("average_map", "metrics"),
            ("average_relevance", "generation_metrics"),
            ("average_faithfulness", "generation_metrics"),
            ("average_completeness", "generation_metrics"),
            ("average_latency", "performance_metrics")
        ]
        
        for metric_name, metric_category in metrics:
            # Skip summary key
            system_scores = {
                name: results[metric_category][metric_name]
                for name, results in comparison.items()
                if name != "summary"
            }
            
            # Rank systems (lower is better for latency, higher for others)
            reverse = metric_name != "average_latency"
            ranked = sorted(system_scores.items(), key=lambda x: x[1], reverse=reverse)
            
            summary["rankings"][metric_name] = [name for name, _ in ranked]
            summary["best_system"][metric_name] = ranked[0][0]
        
        return summary
    
    def generate_report(self, evaluation_results: Dict[str, Any], output_path: str = None) -> str:
        """
        Generate human-readable evaluation report
        
        Args:
            evaluation_results: Results from evaluate()
            output_path: Optional path to save report
            
        Returns:
            str: Formatted report
        """
        report = []
        report.append("=" * 80)
        report.append("RAG SYSTEM EVALUATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Overview
        report.append(f"Number of Queries: {evaluation_results['num_queries']}")
        report.append("")
        
        # Retrieval Metrics
        report.append("RETRIEVAL METRICS")
        report.append("-" * 80)
        metrics = evaluation_results['metrics']
        report.append(f"  Precision@{self.k}:  {metrics['average_precision']:.4f}")
        report.append(f"  Recall@{self.k}:     {metrics['average_recall']:.4f}")
        report.append(f"  F1@{self.k}:         {metrics['average_f1']:.4f}")
        report.append(f"  NDCG@{self.k}:       {metrics['average_ndcg']:.4f}")
        report.append(f"  MRR:           {metrics['average_mrr']:.4f}")
        report.append(f"  MAP:           {metrics['average_map']:.4f}")
        report.append("")
        
        # Generation Metrics
        report.append("GENERATION QUALITY METRICS")
        report.append("-" * 80)
        gen_metrics = evaluation_results['generation_metrics']
        report.append(f"  Relevance:     {gen_metrics['average_relevance']:.4f}")
        report.append(f"  Faithfulness:  {gen_metrics['average_faithfulness']:.4f}")
        report.append(f"  Completeness:  {gen_metrics['average_completeness']:.4f}")
        report.append("")
        
        # Performance Metrics
        report.append("PERFORMANCE METRICS")
        report.append("-" * 80)
        perf_metrics = evaluation_results['performance_metrics']
        report.append(f"  Average Latency: {perf_metrics['average_latency']:.3f}s")
        report.append(f"  Min Latency:     {perf_metrics['min_latency']:.3f}s")
        report.append(f"  Max Latency:     {perf_metrics['max_latency']:.3f}s")
        report.append("")
        
        report.append("=" * 80)
        
        report_text = "\n".join(report)
        
        # Save if output path provided
        if output_path:
            with open(output_path, 'w') as f:
                f.write(report_text)
            logger.info(f"Report saved to {output_path}")
        
        return report_text
