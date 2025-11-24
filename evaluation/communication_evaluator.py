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
from typing import Union

from ragc_core.document_processor import DocumentProcessor
from .agents import StudentAgent

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
            model="gemini-2.0-flash-exp",
            google_api_key=self.api_key,
            temperature=0
        )
        self.doc_processor = DocumentProcessor()
        
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
        from the Ground Truth. 
        
        CRITICAL: The student answer might be rephrased or summarized. 
        Do NOT penalize for different wording if the core concept is correct.
        Penalize if the answer is vague, incorrect, or missing key details.
        
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

    def evaluate_communication(self, doc_path: Union[str, List[str]], student_persona: str = "Novice") -> Dict[str, Any]:
        """
        Run the full evaluation loop for a document or list of documents (aggregated)
        """
        if isinstance(doc_path, list):
            doc_display_name = f"Combined ({len(doc_path)} files)"
            paths = doc_path
        else:
            doc_display_name = doc_path
            paths = [doc_path]
            
        logger.info(f"Evaluating communication for {doc_display_name} with persona: {student_persona}...")
        
        # 1. Read documents using DocumentProcessor
        combined_text = ""
        loaded_files = []
        
        for path in paths:
            try:
                # Use DocumentProcessor to handle various formats (including PPTX)
                logger.info(f"Loading document: {path} (type: {type(path)})")
                text = self.doc_processor.load_document(path)
                combined_text += f"\n\n--- Document: {os.path.basename(path)} ---\n\n" + text
                loaded_files.append(path)
            except Exception as e:
                error_msg = f"Failed to read {path} (type: {type(path)}): {e}"
                logger.error(error_msg)
                # Return error immediately for debugging
                return {"error": error_msg}
        
        if not combined_text:
            return {"error": f"Failed to read any content from provided paths."}
            
        doc_text = combined_text
            
        # 2. Generate questions (Examiner)
        qa_pairs = self.generate_questions_from_doc(doc_text)
        logger.info(f"Generated {len(qa_pairs)} test questions.")
        
        # Initialize Student
        student = StudentAgent(persona=student_persona, api_key=self.api_key)
        
        results = []
        total_score = 0
        
        for item in qa_pairs:
            exam_q = item["question"]
            gt = item["answer"]
            
            # 3. Student asks Teacher (Representative Agent)
            # Student formulates their own question based on the exam topic
            student_q = student.ask(exam_q)
            logger.info(f"Student asking: {student_q}")
            
            # 4. Teacher answers
            try:
                response = requests.post(
                    f"{self.agent_url}/query",
                    json={"query": student_q},
                    timeout=30
                )
                response.raise_for_status()
                teacher_ans = response.json()["answer"]
            except Exception as e:
                logger.error(f"Teacher failed to answer: {e}")
                teacher_ans = "I cannot answer that right now."
            
            # 5. Student learns (Digests answer)
            student.learn(teacher_ans)
            
            # 6. Student takes Exam (Answers original question)
            student_exam_ans = student.answer_exam(exam_q)
            logger.info(f"Student Exam Answer: {student_exam_ans[:100]}...")
            
            # 7. Examiner grades Student
            grade = self.grade_answer(exam_q, student_exam_ans, gt)
            logger.info(f"Grade: {grade['score']}/10")
            
            results.append({
                "exam_question": exam_q,
                "student_question": student_q,
                "teacher_answer": teacher_ans,
                "student_exam_answer": student_exam_ans,
                "ground_truth": gt,
                "score": grade["score"],
                "explanation": grade["explanation"]
            })
            total_score += grade["score"]
            
        avg_score = total_score / len(results) if results else 0
        
        return {
            "document": doc_display_name,
            "student_persona": student_persona,
            "average_score": avg_score,
            "details": results
        }
