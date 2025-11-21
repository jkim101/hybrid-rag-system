"""
RAGAS Evaluator Wrapper

This module integrates the RAGAS framework for advanced RAG evaluation.
It configures RAGAS to use Google Gemini as the judge LLM.
"""

import os
import logging
from typing import List, Dict, Any
import pandas as pd
from datasets import Dataset

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RagasEvaluator:
    """
    Wrapper for RAGAS evaluation framework
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize RAGAS evaluator with Gemini
        
        Args:
            api_key: Gemini API Key (optional, defaults to env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for RAGAS evaluation")
            
        # Initialize Gemini LLM and Embeddings for RAGAS
        # RAGAS uses these to judge the quality of answers
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self.api_key,
            temperature=0
        )
        
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=self.api_key
        )
        
        # Define metrics to use
        self.metrics = [
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall
        ]
        
    def evaluate(self, 
                 questions: List[str], 
                 answers: List[str], 
                 contexts: List[List[str]], 
                 ground_truths: List[List[str]] = None) -> Dict[str, Any]:
        """
        Run RAGAS evaluation
        
        Args:
            questions: List of questions
            answers: List of generated answers
            contexts: List of retrieved contexts (list of strings per query)
            ground_truths: List of ground truth answers (list of strings per query)
            
        Returns:
            Dict: Evaluation results
        """
        logger.info(f"Starting RAGAS evaluation for {len(questions)} queries...")
        
        # Prepare dataset
        data = {
            "question": questions,
            "answer": answers,
            "contexts": contexts
        }
        
        if ground_truths:
            data["ground_truth"] = ground_truths
            
        dataset = Dataset.from_dict(data)
        
        # Run evaluation
        # Note: We need to pass the LLM and embeddings to RAGAS
        # RAGAS 0.1+ allows passing llm/embeddings in the evaluate function or via metrics
        
        # Configure metrics with our LLM
        # This is a bit tricky in RAGAS as it defaults to OpenAI
        # We might need to set global config or pass it explicitly
        
        try:
            results = evaluate(
                dataset=dataset,
                metrics=self.metrics,
                llm=self.llm,
                embeddings=self.embeddings
            )
            
            logger.info("RAGAS evaluation complete")
            return results
            
        except Exception as e:
            logger.error(f"RAGAS evaluation failed: {e}")
            raise

    def evaluate_system(self, rag_system, test_dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate a RAG system using RAGAS
        
        Args:
            rag_system: The RAG system instance
            test_dataset: List of dicts with 'question' and 'ground_truth'
            
        Returns:
            Dict: Evaluation results
        """
        questions = []
        answers = []
        contexts = []
        ground_truths = []
        
        for item in test_dataset:
            q = item["question"]
            gt = item.get("ground_truth")
            
            # Run query
            result = rag_system.query(q)
            
            questions.append(q)
            answers.append(result["answer"])
            
            # Extract context texts
            ctx = [doc["text"] for doc in result["retrieved_documents"]]
            contexts.append(ctx)
            
            if gt:
                ground_truths.append([gt]) # RAGAS expects list of strings for GT
                
        return self.evaluate(questions, answers, contexts, ground_truths if ground_truths else None)
