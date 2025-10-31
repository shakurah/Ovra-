"""
Unit tests for RegressionTestingService
"""

from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import pytest
from django.test import TestCase
from django.utils import timezone

from ..models.test_models import TestCaseModel, TestResultModel
from ..services.regression_testing import RegressionTestingService

class TestRegressionTestingService(TestCase):
    def setUp(self):
        self.service = RegressionTestingService()
        
        # Create sample test case
        self.test_case = TestCaseModel.objects.create(
            test_id="test_001",
            query="Test query",
            expected_response="Expected response",
            tags=["test", "sample"],
            metadata={"priority": "high"}
        )

    def test_create_test_case(self):
        """Test creating a new test case"""
        test_case = self.service.create_test_case(
            query="What is the capital of France?",
            expected_response="The capital of France is Paris.",
            tags=["geography", "cities"],
            metadata={"difficulty": "easy"}
        )
        
        self.assertIsNotNone(test_case)
        self.assertTrue(test_case.test_id.startswith("test_"))
        self.assertEqual(test_case.query, "What is the capital of France?")
        self.assertEqual(test_case.expected_response, "The capital of France is Paris.")
        self.assertEqual(test_case.tags, ["geography", "cities"])
        self.assertEqual(test_case.metadata, {"difficulty": "easy"})

    @patch('sentence_transformers.SentenceTransformer.encode')
    @patch('sentence_transformers.util.pytorch_cos_sim')
    def test_run_test(self, mock_cos_sim, mock_encode):
        """Test running a single test case"""
        # Mock similarity calculation
        mock_encode.return_value = MagicMock()
        mock_cos_sim.return_value = [[0.9]]  # High similarity score
        
        result = self.service.run_test(
            self.test_case,
            "Actual response"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result.test_case_id, "test_001")
        self.assertEqual(result.actual_response, "Actual response")
        self.assertEqual(result.similarity_score, 0.9)
        self.assertTrue(result.passed)
        self.assertGreaterEqual(result.execution_time, 0)

    def test_run_test_suite(self):
        """Test running multiple test cases"""
        # Create additional test cases
        TestCaseModel.objects.create(
            test_id="test_002",
            query="Another query",
            expected_response="Another response",
            tags=["test"]
        )
        
        results = self.service.run_test_suite(tags=["test"])
        
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIsNotNone(result.test_case_id)
            self.assertIsNotNone(result.timestamp)

    def test_get_test_history(self):
        """Test retrieving test history"""
        # Create some test results
        for i in range(3):
            TestResultModel.objects.create(
                test_case_id="test_001",
                actual_response=f"Response {i}",
                similarity_score=0.8 + (i * 0.1),
                passed=True,
                execution_time=1.0
            )
        
        history = self.service.get_test_history("test_001", limit=2)
        
        self.assertEqual(len(history), 2)
        self.assertTrue(all(r.test_case_id == "test_001" for r in history))
        # Verify descending order by timestamp
        self.assertTrue(history[0].timestamp >= history[1].timestamp)

    def test_get_regression_report(self):
        """Test generating regression report"""
        # Create mix of passing and failing results
        TestResultModel.objects.create(
            test_case_id="test_001",
            actual_response="Good response",
            similarity_score=0.9,
            passed=True,
            execution_time=1.0,
            timestamp=timezone.now()
        )
        TestResultModel.objects.create(
            test_case_id="test_001",
            actual_response="Bad response",
            similarity_score=0.6,
            passed=False,
            execution_time=1.0,
            timestamp=timezone.now()
        )
        
        regressions, pass_rate = self.service.get_regression_report()
        
        self.assertEqual(len(regressions), 1)  # One failing test
        self.assertEqual(pass_rate, 0.5)  # 50% pass rate
        self.assertIn('test_id', regressions[0])
        self.assertIn('similarity_score', regressions[0])

    @patch('sentence_transformers.SentenceTransformer.encode')
    @patch('sentence_transformers.util.pytorch_cos_sim')
    def test_calculate_similarity(self, mock_cos_sim, mock_encode):
        """Test similarity calculation"""
        # Mock similarity calculation
        mock_encode.return_value = MagicMock()
        mock_cos_sim.return_value = [[0.75]]
        
        similarity = self.service._calculate_similarity(
            "First text",
            "Second text"
        )
        
        self.assertEqual(similarity, 0.75)
        self.assertTrue(mock_encode.called)
        self.assertTrue(mock_cos_sim.called)

    def test_calculate_similarity_error_handling(self):
        """Test error handling in similarity calculation"""
        with patch('sentence_transformers.SentenceTransformer.encode', 
                  side_effect=Exception("Test error")):
            similarity = self.service._calculate_similarity(
                "First text",
                "Second text"
            )
            self.assertEqual(similarity, 0.0)