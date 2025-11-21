import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from evaluation.ragas_evaluator import RagasEvaluator
from evaluation.communication_evaluator import CommunicationEvaluator

class TestEnhancements(unittest.TestCase):
    
    @patch("evaluation.ragas_evaluator.evaluate")
    @patch("evaluation.ragas_evaluator.ChatGoogleGenerativeAI")
    @patch("evaluation.ragas_evaluator.GoogleGenerativeAIEmbeddings")
    def test_ragas_evaluator(self, mock_embeddings, mock_llm, mock_evaluate):
        """Test RAGAS Evaluator wrapper"""
        # Setup mocks
        mock_evaluate.return_value = {"faithfulness": 0.9, "answer_relevancy": 0.8}
        
        # Initialize
        evaluator = RagasEvaluator(api_key="test_key")
        
        # Run evaluate
        results = evaluator.evaluate(
            questions=["q1"],
            answers=["a1"],
            contexts=[["c1"]],
            ground_truths=[["gt1"]]
        )
        
        # Verify
        self.assertEqual(results["faithfulness"], 0.9)
        mock_evaluate.assert_called_once()
        
    @patch("evaluation.communication_evaluator.genai.GenerativeModel")
    @patch("evaluation.communication_evaluator.requests.post")
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
    def test_communication_evaluator(self, mock_post, mock_model_cls):
        """Test Communication Evaluator loop"""
        # Setup mocks
        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model
        
        # Mock question generation
        mock_model.generate_content.side_effect = [
            MagicMock(text='[{"question": "q1", "answer": "a1"}]'), # generate_questions
            MagicMock(text='{"score": 8, "explanation": "good"}')   # grade_answer
        ]
        
        # Mock student query
        mock_response = MagicMock()
        mock_response.json.return_value = {"answer": "student_answer"}
        mock_post.return_value = mock_response
        
        # Initialize
        evaluator = CommunicationEvaluator()
        
        # Create dummy file
        with open("dummy_test.txt", "w") as f:
            f.write("test content")
            
        try:
            # Run evaluation
            results = evaluator.evaluate_communication("dummy_test.txt")
            
            # Verify
            self.assertEqual(results["average_score"], 8.0)
            self.assertEqual(len(results["details"]), 1)
            self.assertEqual(results["details"][0]["question"], "q1")
            
        finally:
            if os.path.exists("dummy_test.txt"):
                os.remove("dummy_test.txt")

if __name__ == "__main__":
    unittest.main()
