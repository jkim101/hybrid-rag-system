import logging
from typing import List, Dict, Any, Optional
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StudentAgent:
    """
    Simulates an external agent (Student) that learns from the Representative Agent (Teacher).
    """
    
    def __init__(self, persona: str = "Novice", api_key: str = None):
        """
        Initialize Student Agent
        
        Args:
            persona: Description of the student's knowledge level and attitude
                     (e.g., "Novice", "Expert", "Skeptical")
            api_key: Gemini API Key
        """
        self.persona = persona
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for StudentAgent")
            
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=self.api_key,
            temperature=0.7 # Slight creativity for "understanding"
        )
        
        # Internal memory of what has been learned
        self.memory: List[str] = []
        
        # Conversation history with Teacher
        self.conversation_history: List[Dict[str, str]] = []

    def ask(self, topic: str) -> str:
        """
        Formulate a question about a topic based on persona
        """
        prompt = f"""
        You are a student with the following persona: {self.persona}.
        You need to ask a question to a teacher about: "{topic}".
        
        Formulate a question that reflects your persona. 
        If you are a novice, ask basic questions.
        If you are an expert, ask specific, technical questions.
        
        Question:
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            question = response.content.strip()
            self.conversation_history.append({"role": "student", "content": question})
            return question
        except Exception as e:
            logger.error(f"Student failed to ask question: {e}")
            return f"Can you tell me about {topic}?"

    def learn(self, teacher_answer: str) -> None:
        """
        Digest the teacher's answer and update memory
        """
        self.conversation_history.append({"role": "teacher", "content": teacher_answer})
        
        prompt = f"""
        You are a student with the following persona: {self.persona}.
        The teacher gave you this answer:
        "{teacher_answer}"
        
        Summarize what you learned from this answer in your own words. 
        Focus on the key concepts.
        
        Your Summary:
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            summary = response.content.strip()
            self.memory.append(summary)
            logger.info(f"Student ({self.persona}) learned: {summary[:100]}...")
        except Exception as e:
            logger.error(f"Student failed to learn: {e}")
            # Fallback: just store the raw answer
            self.memory.append(teacher_answer)

    def answer_exam(self, question: str) -> str:
        """
        Answer an exam question using ONLY learned memory
        """
        memory_context = "\n\n".join(self.memory)
        
        prompt = f"""
        You are taking an exam. Answer the following question using ONLY what you have learned so far.
        Do not use outside knowledge.
        
        Your Learned Knowledge:
        {memory_context}
        
        Exam Question: {question}
        
        Answer (in your own words):
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            logger.error(f"Student failed to answer exam: {e}")
            return "I don't know the answer."

    def clear_memory(self):
        self.memory = []
        self.conversation_history = []
