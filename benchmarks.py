"""
Performance Benchmark Suite for Hybrid RAG System
Evaluates system performance across multiple dimensions

Benchmarks:
- Retrieval quality (precision, recall, F1)
- Latency (vector, graph, hybrid)
- Throughput (queries per second)
- Scalability (performance vs data size)
- Fusion method comparison
"""

import time
import json
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import statistics

import numpy as np
from loguru import logger
import matplotlib.pyplot as plt
from tqdm import tqdm

# Project imports
from src.rag.hybrid_rag import HybridRAG
from src.utils.document_loader import load_documents


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class BenchmarkQuery:
    """Represents a test query with ground truth"""
    query: str
    ground_truth_docs: List[str]  # IDs of relevant documents
    expected_entities: List[str]  # Expected entities to be found
    query_type: str  # 'entity', 'semantic', 'factual', 'relationship'


@dataclass
class BenchmarkResult:
    """Results from a single query benchmark"""
    query: str
    query_type: str
    
    # Retrieval metrics
    retrieved_count: int
    relevant_retrieved: int
    precision: float
    recall: float
    f1_score: float
    
    # Latency metrics (seconds)
    vector_latency: float
    graph_latency: float
    fusion_latency: float
    total_latency: float
    
    # Method used
    fusion_method: str


# ============================================================================
# BENCHMARK SUITE
# ============================================================================

class HybridRAGBenchmark:
    """
    Comprehensive benchmark suite for Hybrid RAG system
    
    Evaluates:
    - Retrieval quality across different fusion methods
    - Query latency breakdown
    - Scalability with document size
    - Query type performance
    """
    
    def __init__(self, hybrid_rag: HybridRAG):
        """
        Initialize benchmark suite
        
        Args:
            hybrid_rag (HybridRAG): Initialized Hybrid RAG system
        """
        self.rag = hybrid_rag
        self.results: List[BenchmarkResult] = []
        
    def load_test_queries(
        self,
        queries_file: str = "tests/benchmark_queries.json"
    ) -> List[BenchmarkQuery]:
        """
        Load test queries from JSON file
        
        Expected format:
        [
            {
                "query": "What is an Agent Card?",
                "ground_truth_docs": ["doc1", "doc2"],
                "expected_entities": ["Agent Card", "A2A Protocol"],
                "query_type": "entity"
            },
            ...
        ]
        
        Args:
            queries_file (str): Path to queries JSON file
            
        Returns:
            List[BenchmarkQuery]: Loaded test queries
        """
        queries_path = Path(queries_file)
        
        if not queries_path.exists():
            logger.warning(f"Queries file not found: {queries_file}")
            return self._generate_default_queries()
        
        with open(queries_path, 'r') as f:
            data = json.load(f)
        
        queries = [
            BenchmarkQuery(
                query=q['query'],
                ground_truth_docs=q.get('ground_truth_docs', []),
                expected_entities=q.get('expected_entities', []),
                query_type=q.get('query_type', 'general')
            )
            for q in data
        ]
        
        logger.info(f"Loaded {len(queries)} test queries")
        return queries
    
    def _generate_default_queries(self) -> List[BenchmarkQuery]:
        """Generate default test queries if no file provided"""
        return [
            BenchmarkQuery(
                query="What is an Agent Card?",
                ground_truth_docs=["a2a_protocol"],
                expected_entities=["Agent Card"],
                query_type="entity"
            ),
            BenchmarkQuery(
                query="Explain the A2A task lifecycle",
                ground_truth_docs=["a2a_protocol"],
                expected_entities=["Task Lifecycle", "SUBMITTED", "WORKING"],
                query_type="process"
            ),
            BenchmarkQuery(
                query="How does GraphRAG differ from traditional RAG?",
                ground_truth_docs=["graphrag_research"],
                expected_entities=["GraphRAG", "Traditional RAG", "Knowledge Graph"],
                query_type="comparison"
            ),
        ]
    
    def benchmark_single_query(
        self,
        query: BenchmarkQuery,
        fusion_method: str = "weighted"
    ) -> BenchmarkResult:
        """
        Benchmark a single query
        
        Args:
            query (BenchmarkQuery): Query to benchmark
            fusion_method (str): Fusion method to use
            
        Returns:
            BenchmarkResult: Benchmark results
        """
        # Time vector retrieval
        start = time.time()
        vector_results = self.rag.vector_rag.retrieve(query.query)
        vector_latency = time.time() - start
        
        # Time graph retrieval
        start = time.time()
        graph_results = self.rag.graph_rag.retrieve(query.query)
        graph_latency = time.time() - start
        
        # Time fusion
        start = time.time()
        hybrid_results = self.rag.retrieve(
            query.query,
            fusion_method=fusion_method
        )
        fusion_latency = time.time() - start
        total_latency = vector_latency + graph_latency + fusion_latency
        
        # Calculate retrieval quality metrics
        retrieved_doc_ids = [
            r.get('source', '') for r in hybrid_results
        ]
        
        # Count relevant documents retrieved
        relevant_retrieved = sum(
            1 for doc_id in retrieved_doc_ids
            if any(gt in doc_id for gt in query.ground_truth_docs)
        )
        
        # Calculate precision, recall, F1
        precision = (
            relevant_retrieved / len(retrieved_doc_ids)
            if retrieved_doc_ids else 0
        )
        recall = (
            relevant_retrieved / len(query.ground_truth_docs)
            if query.ground_truth_docs else 0
        )
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0 else 0
        )
        
        result = BenchmarkResult(
            query=query.query,
            query_type=query.query_type,
            retrieved_count=len(hybrid_results),
            relevant_retrieved=relevant_retrieved,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            vector_latency=vector_latency,
            graph_latency=graph_latency,
            fusion_latency=fusion_latency,
            total_latency=total_latency,
            fusion_method=fusion_method
        )
        
        self.results.append(result)
        return result
    
    def benchmark_all_queries(
        self,
        queries: List[BenchmarkQuery],
        fusion_methods: List[str] = None
    ) -> Dict[str, List[BenchmarkResult]]:
        """
        Benchmark all queries with different fusion methods
        
        Args:
            queries (List[BenchmarkQuery]): Queries to benchmark
            fusion_methods (List[str]): Fusion methods to test
            
        Returns:
            Dict: Results grouped by fusion method
        """
        if fusion_methods is None:
            fusion_methods = ["weighted", "rrf", "simple"]
        
        results_by_method = {method: [] for method in fusion_methods}
        
        logger.info(f"Benchmarking {len(queries)} queries with {len(fusion_methods)} methods")
        
        # Test each fusion method
        for method in fusion_methods:
            logger.info(f"Testing fusion method: {method}")
            
            for query in tqdm(queries, desc=f"Queries ({method})"):
                result = self.benchmark_single_query(query, method)
                results_by_method[method].append(result)
        
        logger.info("Benchmark complete!")
        return results_by_method
    
    def compare_fusion_methods(
        self,
        results_by_method: Dict[str, List[BenchmarkResult]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare performance of different fusion methods
        
        Args:
            results_by_method (Dict): Results grouped by method
            
        Returns:
            Dict: Summary statistics by method
        """
        summary = {}
        
        for method, results in results_by_method.items():
            if not results:
                continue
            
            summary[method] = {
                # Quality metrics
                'avg_precision': statistics.mean(r.precision for r in results),
                'avg_recall': statistics.mean(r.recall for r in results),
                'avg_f1': statistics.mean(r.f1_score for r in results),
                
                # Latency metrics
                'avg_latency': statistics.mean(r.total_latency for r in results),
                'p95_latency': np.percentile([r.total_latency for r in results], 95),
                'avg_vector_latency': statistics.mean(r.vector_latency for r in results),
                'avg_graph_latency': statistics.mean(r.graph_latency for r in results),
                
                # Count metrics
                'total_queries': len(results),
            }
        
        return summary
    
    def benchmark_throughput(
        self,
        test_queries: List[str],
        duration_seconds: int = 60
    ) -> Dict[str, float]:
        """
        Measure system throughput (queries per second)
        
        Args:
            test_queries (List[str]): Queries to use for testing
            duration_seconds (int): How long to run the test
            
        Returns:
            Dict: Throughput metrics
        """
        logger.info(f"Running throughput benchmark for {duration_seconds}s")
        
        queries_processed = 0
        latencies = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            # Rotate through test queries
            query = test_queries[queries_processed % len(test_queries)]
            
            # Time single query
            query_start = time.time()
            self.rag.generate_response(query)
            latency = time.time() - query_start
            
            latencies.append(latency)
            queries_processed += 1
        
        elapsed = time.time() - start_time
        
        return {
            'queries_per_second': queries_processed / elapsed,
            'total_queries': queries_processed,
            'duration': elapsed,
            'avg_latency': statistics.mean(latencies),
            'p95_latency': np.percentile(latencies, 95),
            'p99_latency': np.percentile(latencies, 99),
        }
    
    def benchmark_scalability(
        self,
        document_counts: List[int] = None
    ) -> Dict[int, Dict[str, float]]:
        """
        Measure how performance scales with document count
        
        Args:
            document_counts (List[int]): Document counts to test
            
        Returns:
            Dict: Performance metrics at each scale
        """
        if document_counts is None:
            document_counts = [100, 500, 1000, 5000]
        
        logger.info(f"Running scalability benchmark")
        
        results = {}
        test_query = "What is the main topic of these documents?"
        
        for doc_count in document_counts:
            logger.info(f"Testing with {doc_count} documents")
            
            # Measure retrieval latency at this scale
            start = time.time()
            results_vector = self.rag.vector_rag.retrieve(
                test_query,
                top_k=min(10, doc_count // 10)
            )
            vector_latency = time.time() - start
            
            start = time.time()
            results_graph = self.rag.graph_rag.retrieve(
                test_query,
                top_k=min(10, doc_count // 10)
            )
            graph_latency = time.time() - start
            
            results[doc_count] = {
                'vector_latency': vector_latency,
                'graph_latency': graph_latency,
                'total_latency': vector_latency + graph_latency,
            }
        
        return results
    
    def generate_report(
        self,
        output_file: str = "benchmark_report.json"
    ):
        """
        Generate comprehensive benchmark report
        
        Args:
            output_file (str): Path to save report
        """
        if not self.results:
            logger.warning("No benchmark results to report")
            return
        
        # Aggregate results by query type
        results_by_type = {}
        for result in self.results:
            if result.query_type not in results_by_type:
                results_by_type[result.query_type] = []
            results_by_type[result.query_type].append(result)
        
        # Generate summary for each type
        report = {
            'summary': {
                'total_queries': len(self.results),
                'query_types': list(results_by_type.keys()),
                'avg_precision': statistics.mean(r.precision for r in self.results),
                'avg_recall': statistics.mean(r.recall for r in self.results),
                'avg_f1': statistics.mean(r.f1_score for r in self.results),
                'avg_latency': statistics.mean(r.total_latency for r in self.results),
            },
            'by_query_type': {},
            'detailed_results': [asdict(r) for r in self.results]
        }
        
        for q_type, results in results_by_type.items():
            report['by_query_type'][q_type] = {
                'count': len(results),
                'avg_precision': statistics.mean(r.precision for r in results),
                'avg_recall': statistics.mean(r.recall for r in results),
                'avg_f1': statistics.mean(r.f1_score for r in results),
                'avg_latency': statistics.mean(r.total_latency for r in results),
            }
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Benchmark report saved to: {output_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("BENCHMARK SUMMARY")
        print("="*60)
        print(f"Total Queries: {report['summary']['total_queries']}")
        print(f"Average Precision: {report['summary']['avg_precision']:.3f}")
        print(f"Average Recall: {report['summary']['avg_recall']:.3f}")
        print(f"Average F1: {report['summary']['avg_f1']:.3f}")
        print(f"Average Latency: {report['summary']['avg_latency']:.3f}s")
        print("="*60 + "\n")
    
    def plot_results(
        self,
        results_by_method: Dict[str, List[BenchmarkResult]],
        output_dir: str = "benchmark_plots"
    ):
        """
        Generate visualization plots of benchmark results
        
        Args:
            results_by_method (Dict): Results grouped by fusion method
            output_dir (str): Directory to save plots
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        methods = list(results_by_method.keys())
        
        # Plot 1: F1 Score comparison
        plt.figure(figsize=(10, 6))
        f1_scores = [
            [r.f1_score for r in results_by_method[m]]
            for m in methods
        ]
        plt.boxplot(f1_scores, labels=methods)
        plt.ylabel('F1 Score')
        plt.title('F1 Score Distribution by Fusion Method')
        plt.grid(True, alpha=0.3)
        plt.savefig(output_path / 'f1_comparison.png')
        plt.close()
        
        # Plot 2: Latency comparison
        plt.figure(figsize=(10, 6))
        latencies = [
            [r.total_latency for r in results_by_method[m]]
            for m in methods
        ]
        plt.boxplot(latencies, labels=methods)
        plt.ylabel('Latency (seconds)')
        plt.title('Query Latency by Fusion Method')
        plt.grid(True, alpha=0.3)
        plt.savefig(output_path / 'latency_comparison.png')
        plt.close()
        
        logger.info(f"Plots saved to: {output_dir}")


# ============================================================================
# CLI INTERFACE
# ============================================================================

def run_benchmarks():
    """Run all benchmarks from command line"""
    from config.config import HYBRID_RAG_CONFIG, DATA_DIR
    
    print("Initializing Hybrid RAG System...")
    rag = HybridRAG()
    
    # Load documents
    print("Loading documents...")
    docs = load_documents(str(DATA_DIR))
    rag.ingest_documents(docs)
    
    # Initialize benchmark
    print("Starting benchmark...")
    benchmark = HybridRAGBenchmark(rag)
    
    # Load test queries
    queries = benchmark.load_test_queries()
    
    # Run benchmarks
    results = benchmark.benchmark_all_queries(
        queries,
        fusion_methods=["weighted", "rrf"]
    )
    
    # Compare methods
    comparison = benchmark.compare_fusion_methods(results)
    print("\nFusion Method Comparison:")
    print(json.dumps(comparison, indent=2))
    
    # Generate report
    benchmark.generate_report()
    
    # Generate plots
    try:
        benchmark.plot_results(results)
    except Exception as e:
        print(f"Warning: Could not generate plots: {e}")
    
    print("\nBenchmark complete!")


if __name__ == "__main__":
    run_benchmarks()
