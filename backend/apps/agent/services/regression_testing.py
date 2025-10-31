"""
RegressionTestingService - Manages test execution and result tracking
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sentence_transformers import SentenceTransformer, util
import torch

from .models.test_models import TestCaseModel, TestResultModel

logger = logging.getLogger(__name__)

class RegressionTestingService:
    """Service to manage test case execution and regression detection"""

    def __init__(self):
        self.similarity_model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def create_test_case(self, query: str, expected_response: str, tags: List[str] = None,
                        metadata: Dict = None) -> TestCaseModel:
        """Create and store a new test case"""
        test_case = TestCaseModel.objects.create(
            test_id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            query=query,
            expected_response=expected_response,
            tags=tags or [],
            metadata=metadata or {}
        )
        logger.info(f"Created test case {test_case.test_id}")
        return test_case

    def run_test(self, test_case: TestCaseModel, actual_response: str) -> TestResultModel:
        """Execute a single test and store results"""
        start_time = datetime.now()
        
        # Calculate similarity between expected and actual responses
        similarity_score = self._calculate_similarity(
            test_case.expected_response, 
            actual_response
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        passed = similarity_score >= 0.85  # Threshold for test success

        # Store test result
        result = TestResultModel.objects.create(
            test_case_id=test_case.test_id,
            actual_response=actual_response,
            similarity_score=similarity_score,
            passed=passed,
            execution_time=execution_time
        )

        # Update test case last run timestamp
        test_case.last_run = datetime.now()
        test_case.save()

        return result

    def run_test_suite(self, tags: List[str] = None) -> List[TestResultModel]:
        """Run all test cases, optionally filtered by tags"""
        query = TestCaseModel.objects.all()
        if tags:
            # Filter test cases by provided tags
            query = query.filter(tags__contains=tags)

        results = []
        for test_case in query:
            try:
                # Here we would get the actual response from the AI system
                # Placeholder for now - would integrate with actual system
                actual_response = "Placeholder response"
                result = self.run_test(test_case, actual_response)
                results.append(result)
            except Exception as e:
                logger.error(f"Error running test {test_case.test_id}: {str(e)}")
                # Create failed result
                results.append(TestResultModel.objects.create(
                    test_case_id=test_case.test_id,
                    actual_response="",
                    similarity_score=0.0,
                    passed=False,
                    execution_time=0.0,
                    error_message=str(e)
                ))

        return results

    def get_test_history(self, test_case_id: str, limit: int = 10) -> List[TestResultModel]:
        """Retrieve historical test results for a specific test case"""
        return TestResultModel.objects.filter(
            test_case_id=test_case_id
        ).order_by('-timestamp')[:limit]

    def get_regression_report(self) -> Tuple[List[Dict], float]:
        """Generate a regression analysis report"""
        # Get all test results from last 24 hours
        recent_results = TestResultModel.objects.filter(
            timestamp__gte=datetime.now() - datetime.timedelta(days=1)
        )

        # Calculate regression metrics
        total_tests = len(recent_results)
        if total_tests == 0:
            return [], 0.0

        passing_tests = sum(1 for r in recent_results if r.passed)
        pass_rate = passing_tests / total_tests

        # Identify potential regressions
        regressions = []
        for result in recent_results:
            if not result.passed:
                test_case = TestCaseModel.objects.get(test_id=result.test_case_id)
                regressions.append({
                    'test_id': result.test_case_id,
                    'similarity_score': result.similarity_score,
                    'query': test_case.query,
                    'expected': test_case.expected_response,
                    'actual': result.actual_response,
                    'timestamp': result.timestamp.isoformat()
                })

        return regressions, pass_rate

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts using sentence embeddings"""
        try:
            # Convert texts to embeddings
            embeddings1 = self.similarity_model.encode(text1, convert_to_tensor=True)
            embeddings2 = self.similarity_model.encode(text2, convert_to_tensor=True)
            
            # Calculate cosine similarity
            similarity = util.pytorch_cos_sim(embeddings1, embeddings2)
            
            return float(similarity[0][0])  # Convert tensor to float
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0