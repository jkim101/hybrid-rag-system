import argparse
import logging
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from evaluation.communication_evaluator import CommunicationEvaluator
# from evaluation.ragas_evaluator import RagasEvaluator # Import only if needed to avoid heavy imports if not used

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evaluation_runner")

# Load environment variables
load_dotenv()

def run_communication_eval(doc_path):
    """Run communication evaluation"""
    if not os.path.exists(doc_path):
        logger.error(f"Document not found: {doc_path}")
        return

    logger.info(f"Running communication evaluation on {doc_path}...")
    try:
        evaluator = CommunicationEvaluator()
        results = evaluator.evaluate_communication(doc_path)
        
        print("\n" + "="*50)
        print(f"EVALUATION REPORT: {doc_path}")
        print("="*50)
        print(f"Average Score: {results.get('average_score', 0):.1f}/10")
        print("-" * 50)
        
        for detail in results.get("details", []):
            print(f"\nQ: {detail['question']}")
            print(f"Student Answer: {detail['student_answer']}")
            print(f"Ground Truth: {detail['ground_truth']}")
            print(f"Score: {detail['score']}/10")
            print(f"Explanation: {detail['explanation']}")
            
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")

def run_ragas_eval():
    """Run RAGAS evaluation (demo)"""
    logger.info("Running RAGAS evaluation demo...")
    try:
        from evaluation.ragas_evaluator import RagasEvaluator
        evaluator = RagasEvaluator()
        
        # Demo data
        questions = ["머신러닝의 지도 학습이란?"]
        answers = ["지도 학습은 레이블이 지정된 데이터를 사용하여 모델을 훈련시키는 것입니다."]
        contexts = [["지도 학습은 레이블된 데이터에 대해 모델을 학습시키는 것을 포함합니다."]]
        ground_truths = [["지도 학습은 정답이 주어진 데이터로 모델을 학습시키는 방법입니다."]]
        
        results = evaluator.evaluate(questions, answers, contexts, ground_truths)
        print("\n" + "="*50)
        print("RAGAS EVALUATION RESULTS")
        print("="*50)
        print(results)
        
    except Exception as e:
        logger.error(f"RAGAS evaluation failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Run RAG System Evaluations")
    parser.add_argument("--mode", choices=["communication", "ragas"], default="communication", help="Evaluation mode")
    parser.add_argument("--doc", default="data/documents/example_ml_basics.md", help="Document path for communication eval")
    
    args = parser.parse_args()
    
    if args.mode == "communication":
        run_communication_eval(args.doc)
    elif args.mode == "ragas":
        run_ragas_eval()

if __name__ == "__main__":
    main()
