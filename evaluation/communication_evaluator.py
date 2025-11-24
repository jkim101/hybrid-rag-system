"""
Communication Evaluator

This module evaluates the effectiveness of knowledge transfer from the Representative Agent
to external agents. It implements a "Teacher-Student-Examiner" loop.
"""

import logging
import requests
import json
import time
import os
from typing import List, Dict, Any, Union, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from ragc_core.document_processor import DocumentProcessor
from .agents import StudentAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting configuration
API_CALL_DELAY = 2.0  # Delay between API calls in seconds
QUESTION_DELAY = 1.5  # Delay between questions in evaluation loop

class CommunicationEvaluator:
    """
    Evaluates knowledge transfer to external agents.
    """
    
    def __init__(self, rag_system=None, doc_processor=None, agent_url: str = "http://localhost:8000"):
        """
        Initialize evaluator
        
        Args:
            rag_system: Optional direct reference to HybridRAG instance
            doc_processor: Optional DocumentProcessor instance
            agent_url: URL of the Representative Agent (fallback if rag_system not provided)
        """
        self.rag_system = rag_system
        self.agent_url = agent_url
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=self.api_key,
            temperature=0
        )
        self.doc_processor = doc_processor or DocumentProcessor()
        
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
            time.sleep(API_CALL_DELAY)  # Rate limiting
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


    def ask_teacher(self, question: str) -> str:
        """
        Ask the teacher (RAG system) a question
        
        Args:
            question: Question to ask
            
        Returns:
            str: Teacher's answer
        """
        if self.rag_system:
            # Direct call if running in same process
            try:
                result = self.rag_system.query(question)
                time.sleep(API_CALL_DELAY)  # Rate limiting
                return result["answer"]
            except Exception as e:
                logger.error(f"Error querying RAG system directly: {e}")
                return "I encountered an error while trying to answer that."
        else:
            # HTTP call if running remotely
            try:
                response = requests.post(
                    f"{self.agent_url}/query",
                    json={"query": question}
                )
                time.sleep(API_CALL_DELAY)  # Rate limiting
                if response.status_code == 200:
                    return response.json()["answer"]
                else:
                    return "I encountered an error while trying to answer that."
            except Exception as e:
                logger.error(f"Error querying agent: {e}")
                return "I encountered an error while trying to answer that."

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
            time.sleep(API_CALL_DELAY)  # Rate limiting
            text = response.content.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            return json.loads(text)
        except Exception as e:
            logger.error(f"Grading failed: {e}")
            return {"score": 0, "explanation": "Grading failed"}

    def evaluate_communication(
        self, 
        doc_path: Union[str, List[str]], 
        student_persona: str = "Novice",
        qa_pairs: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Run the full evaluation loop for a document or list of documents (aggregated)
        
        Args:
            doc_path: Path(s) to document(s) to evaluate
            student_persona: Student difficulty level
            qa_pairs: Optional pre-defined questions/answers. If None, auto-generate from document.
        """
        progress_logs = []  # Track detailed progress
        
        if isinstance(doc_path, list):
            doc_display_name = f"Combined ({len(doc_path)} files)"
            paths = doc_path
        else:
            doc_display_name = doc_path
            paths = [doc_path]
            
        logger.info(f"Evaluating communication for {doc_display_name} with persona: {student_persona}...")
        progress_logs.append(f"📋 Starting evaluation for {doc_display_name}")
        progress_logs.append(f"👤 Student Persona: {student_persona}")
        
        # Determine evaluation mode
        if qa_pairs:
            progress_logs.append(f"📄 Using pre-defined evaluation questions ({len(qa_pairs)} questions)")
            logger.info(f"Using {len(qa_pairs)} pre-defined questions from evaluation file")
        else:
            progress_logs.append("🤖 Auto-generating evaluation questions from document")
        
        # 1. Read documents using DocumentProcessor (only if auto-generating questions)
        if qa_pairs is None:
            combined_text = ""
            loaded_files = []
            
            progress_logs.append(f"📂 Loading {len(paths)} document(s)...")
            for path in paths:
                try:
                    # Use DocumentProcessor to handle various formats (including PPTX)
                    logger.info(f"Loading document: {path} (type: {type(path)})")
                    text = self.doc_processor.load_document(path)
                    combined_text += f"\n\n--- Document: {os.path.basename(path)} ---\n\n" + text
                    loaded_files.append(path)
                    progress_logs.append(f"  ✓ Loaded: {os.path.basename(path)}")
                except Exception as e:
                    error_msg = f"Failed to read {path} (type: {type(path)}): {e}"
                    logger.error(error_msg)
                    progress_logs.append(f"  ✗ Error: {os.path.basename(path)}")
                    # Return error immediately for debugging
                    return {"error": error_msg, "progress_logs": progress_logs}
            
            if not combined_text:
                return {"error": f"Failed to read any content from provided paths.", "progress_logs": progress_logs}
                
            doc_text = combined_text
                
            # 2. Generate questions (Examiner)
            progress_logs.append("🎓 Examiner generating test questions...")
            qa_pairs = self.generate_questions_from_doc(doc_text)
            logger.info(f"Generated {len(qa_pairs)} test questions.")
            progress_logs.append(f"  ✓ Generated {len(qa_pairs)} questions")
        
        # Initialize Student
        progress_logs.append(f"👨‍🎓 Initializing {student_persona} student agent...")
        student = StudentAgent(persona=student_persona, api_key=self.api_key)
        
        results = []
        total_score = 0
        
        for idx, item in enumerate(qa_pairs, 1):
            # Handle various key formats (case-insensitive)
            item_lower = {k.lower(): v for k, v in item.items()}
            
            # Prioritize standard RAG evaluation format: 'query' and 'ground_truth'
            exam_q = item_lower.get("query") or item_lower.get("question") or item_lower.get("q")
            gt = item_lower.get("ground_truth") or item_lower.get("answer") or item_lower.get("a")
            
            if not exam_q:
                logger.warning(f"Skipping item {idx}: Missing 'query' or 'question' key. Keys found: {list(item.keys())}")
                progress_logs.append(f"⚠️ Skipping question {idx}: Invalid format")
                continue
                
            progress_logs.append(f"\n📝 Question {idx}/{len(qa_pairs)}: {exam_q[:80]}...")
            
            # 3. Student asks Teacher (Representative Agent)
            # Student formulates their own question based on the exam topic
            student_q = student.ask(exam_q)
            logger.info(f"Student asking: {student_q}")
            progress_logs.append(f"  👨‍🎓 Student asks: {student_q[:80]}...")
            
            # 4. Teacher answers
            progress_logs.append(f"  👨‍🏫 Teacher (RAG) answering...")
            teacher_ans = self.ask_teacher(student_q)
            logger.info(f"Teacher answered: {teacher_ans[:100]}...")
            progress_logs.append(f"  ✓ Teacher answered ({len(teacher_ans)} chars)")
            
            # 5. Student learns (Digests answer)
            progress_logs.append(f"  📚 Student learning from answer...")
            student.learn(teacher_ans)
            
            # 6. Student takes Exam (Answers original question)
            progress_logs.append(f"  ✍️ Student taking exam...")
            student_exam_ans = student.answer_exam(exam_q)
            logger.info(f"Student Exam Answer: {student_exam_ans[:100]}...")
            progress_logs.append(f"  ✓ Student answered ({len(student_exam_ans)} chars)")
            
            # 7. Examiner grades Student
            progress_logs.append(f"  🎓 Examiner grading...")
            grade = self.grade_answer(exam_q, student_exam_ans, gt)
            logger.info(f"Grade: {grade['score']}/10")
            progress_logs.append(f"  ⭐ Grade: {grade['score']}/10 - {grade.get('explanation', '')[:50]}...")
            
            results.append({
                "exam_question": exam_q,
                "student_question": student_q,
                "teacher_answer": teacher_ans,
                "student_exam_answer": student_exam_ans,
                "grade": grade["score"],
                "explanation": grade.get("explanation", "")
            })
            
            total_score += grade["score"]
            
            # Add delay between questions to avoid rate limiting
            if len(results) < len(qa_pairs):  # Don't delay after last question
                logger.info(f"Waiting {QUESTION_DELAY}s before next question...")
                progress_logs.append(f"  ⏳ Waiting {QUESTION_DELAY}s to avoid rate limits...")
                time.sleep(QUESTION_DELAY)
            
        avg_score = total_score / len(results) if results else 0
        progress_logs.append(f"\n✅ Evaluation complete! Average score: {avg_score:.1f}/10")
        
        return {
            "document": doc_display_name,
            "student_persona": student_persona,
            "average_score": avg_score,
            "details": results,
            "progress_logs": progress_logs
        }
