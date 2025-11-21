"""
Communication Evaluator

This module evaluates the effectiveness of knowledge transfer from the Representative Agent
to external agents. It implements a "Teacher-Student-Examiner" loop.
"""

import logging
import requests
import json
from typing import List, Dict, Any
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommunicationEvaluator:
    """
    Evaluates knowledge transfer to external agents.
    """
    
    def __init__(self, agent_url: str = "http://localhost:8000"):
        """
        Initialize evaluator
        
        Args:
            agent_url: URL of the Representative Agent
        """
        self.agent_url = agent_url
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        self.model = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self.api_key,
            temperature=0
        )
        
    def generate_questions_from_doc(self, doc_text: str, num_questions: int = 3) -> List[Dict[str, str]]:
        """
        Generate test questions based on a document (Examiner role)
        """
        prompt = f"""
        Based on the following text, generate {num_questions} pairs of questions and answers 
        to test someone's understanding of the content.
        
        Text:
        {doc_text[:2000]}... (truncated)
        
        Output format (JSON):
        [
            {{"question": "...", "answer": "..."}},
            ...
        ]
        """
        
        try:
            response = self.model.invoke([HumanMessage(content=prompt)])
            text = response.content.strip()
            # Clean up json string if needed
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            return json.loads(text)
        except Exception as e:
            logger.error(f"Failed to generate questions: {e}")
            return []

    def simulate_student_agent(self, question: str) -> str:
        """
        Simulate an external agent asking the Representative Agent (Student role)
        """
        try:
            response = requests.post(
                f"{self.agent_url}/query",
                json={"query": question},
                timeout=30
            )
            response.raise_for_status()
            return response.json()["answer"]
        except Exception as e:
            logger.error(f"Student agent failed to query teacher: {e}")
            return "I could not get an answer."

    def grade_answer(self, question: str, student_answer: str, ground_truth: str) -> Dict[str, Any]:
        """
        Grade the student's answer against ground truth (Examiner role)
        """
        prompt = f"""
        You are an examiner grading a student's answer.
        
        Question: {question}
        Ground Truth: {ground_truth}
        Student Answer: {student_answer}
        
        Grade the student's answer on a scale of 0 to 10 based on how well it conveys the key information 
        from the Ground Truth. Also provide a brief explanation.
        
        Output format (JSON):
        {{"score": 8, "explanation": "..."}}
        """
        
        try:
            response = self.model.invoke([HumanMessage(content=prompt)])
            text = response.content.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            return json.loads(text)
        except Exception as e:
            logger.error(f"Grading failed: {e}")
            return {"score": 0, "explanation": "Grading failed"}

    def evaluate_communication(self, doc_path: str) -> Dict[str, Any]:
        """
        Run the full evaluation loop for a document
        """
        logger.info(f"Evaluating communication for {doc_path}...")
        
        # 1. Read document
        try:
            with open(doc_path, 'r') as f:
                doc_text = f.read()
        except Exception as e:
            return {"error": f"Failed to read file: {e}"}
            
        # 2. Generate questions (Examiner)
        qa_pairs = self.generate_questions_from_doc(doc_text)
        logger.info(f"Generated {len(qa_pairs)} test questions.")
        
        results = []
        total_score = 0
        
        for item in qa_pairs:
            q = item["question"]
            gt = item["answer"]
            
            # 3. Student asks Teacher
            logger.info(f"Student asking: {q}")
            student_ans = self.simulate_student_agent(q)
            
            # 4. Examiner grades Student
            grade = self.grade_answer(q, student_ans, gt)
            logger.info(f"Grade: {grade['score']}/10")
            
            results.append({
                "question": q,
                "student_answer": student_ans,
                "ground_truth": gt,
                "score": grade["score"],
                "explanation": grade["explanation"]
            })
            total_score += grade["score"]
            
        avg_score = total_score / len(results) if results else 0
        
        return {
            "document": doc_path,
            "average_score": avg_score,
            "details": results
        }
