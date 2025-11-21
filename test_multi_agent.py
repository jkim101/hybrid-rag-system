import logging
from evaluation.communication_evaluator import CommunicationEvaluator
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_simulation():
    load_dotenv()
    
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEY not found")
        return

    # Create a dummy document
    doc_path = "temp_test_doc.txt"
    with open(doc_path, "w") as f:
        f.write("""
        Machine learning (ML) is a field of study in artificial intelligence concerned with the development and study of statistical algorithms that can learn from data and generalize to unseen data, and thus perform tasks without explicit instructions. Recently, artificial neural networks have been able to surpass many previous approaches in performance.
        
        ML approaches have been applied to many fields including natural language processing, computer vision, speech recognition, email filtering, agriculture, and medicine. ML is known in its application across business problems under the name predictive analytics. Although not all machine learning is statistically based, computational statistics is an important source of the field's methods.
        """)
        
    try:
        logger.info("Initializing Evaluator...")
        evaluator = CommunicationEvaluator(agent_url="http://localhost:8000")
        
        logger.info("Running simulation with 'Novice' persona...")
        results = evaluator.evaluate_communication(doc_path, student_persona="Novice")
        
        if "error" in results:
            logger.error(f"Evaluation failed: {results['error']}")
        else:
            logger.info(f"Evaluation successful! Score: {results['average_score']}")
            for detail in results['details']:
                logger.info(f"\nQ: {detail['exam_question']}")
                logger.info(f"Student Asked: {detail['student_question']}")
                logger.info(f"Student Answered: {detail['student_exam_answer']}")
                logger.info(f"Grade: {detail['score']}")
                
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        if os.path.exists(doc_path):
            os.remove(doc_path)

if __name__ == "__main__":
    test_simulation()
