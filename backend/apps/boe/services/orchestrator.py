"""
Service orchestrator that coordinates all legal services and maintains system state.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from .legal_validation import LegalValidationService
from .contextual_reasoning import ContextualReasoningService, LegalContext, EntityType
from ..agent.services.regression_testing import RegressionTestingService

logger = logging.getLogger(__name__)

class ServiceOrchestrator:
    """
    Central orchestration service that coordinates:
    - Legal validation
    - Contextual reasoning
    - Regression testing
    - System state management
    """

    def __init__(self):
        self.legal_validator = LegalValidationService()
        self.contextual_reasoner = ContextualReasoningService()
        self.regression_tester = RegressionTestingService()
        self.system_state = {}

    async def process_legal_query(self, 
                                query: str,
                                context_data: Dict,
                                domain: str) -> Dict:
        """
        Process a legal query through the complete pipeline with validations
        and contextual reasoning
        """
        try:
            # Convert raw context data to LegalContext
            context = self._create_legal_context(context_data)
            
            # Validate input context
            context_validation = self.contextual_reasoner.validate_input_context(
                context, domain
            )
            if not context_validation['valid']:
                return {
                    'error': 'Insufficient context',
                    'missing_fields': context_validation['missing_fields']
                }

            # Extract and validate legal references
            references = await self._extract_and_validate_references(query)
            if not references['valid']:
                return references

            # Generate contextualized response
            response = self.contextual_reasoner.generate_contextualized_response(
                query=query,
                context=context,
                legal_references=references['validated_refs'],
                domain=domain
            )

            # Run regression test
            await self._run_regression_test(query, response, context_data)

            # Update system state
            self._update_system_state({
                'last_query': query,
                'last_context': context_data,
                'last_response': response
            })

            return response

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {'error': str(e)}

    def _create_legal_context(self, context_data: Dict) -> LegalContext:
        """Create LegalContext instance from raw context data"""
        try:
            return LegalContext(
                entity_type=EntityType(context_data.get('entity_type', 'individual')),
                fiscal_year=context_data.get('fiscal_year'),
                sector=context_data.get('sector'),
                contract_type=context_data.get('contract_type'),
                professional_category=context_data.get('professional_category'),
                region=context_data.get('region'),
                additional_context=context_data.get('additional_context', {})
            )
        except ValueError as e:
            logger.error(f"Invalid context data: {str(e)}")
            raise ValueError(f"Invalid context data: {str(e)}")

    async def _extract_and_validate_references(self, query: str) -> Dict:
        """Extract and validate all legal references in the query"""
        try:
            # Extract references from query (implementation needed)
            references = self._extract_references(query)
            
            # Validate all references
            validated_refs = await self.legal_validator.validate_multiple_references(
                references
            )
            
            # Check if all references are valid
            invalid_refs = [
                ref for ref, data in validated_refs.items() 
                if not data['valid']
            ]
            
            if invalid_refs:
                return {
                    'valid': False,
                    'error': 'Invalid references found',
                    'invalid_references': invalid_refs
                }

            return {
                'valid': True,
                'validated_refs': validated_refs
            }

        except Exception as e:
            logger.error(f"Error validating references: {str(e)}")
            return {
                'valid': False,
                'error': str(e)
            }

    async def _run_regression_test(self,
                                 query: str,
                                 response: Dict,
                                 context: Dict) -> None:
        """Run regression test for the current query-response pair"""
        try:
            test_case = self.regression_tester.create_test_case(
                query=query,
                expected_response=str(response),  # Convert to string for storage
                tags=[context.get('entity_type', 'general'), 
                      context.get('domain', 'general')],
                metadata=context
            )
            
            # Run the test immediately
            self.regression_tester.run_test(test_case, str(response))

        except Exception as e:
            logger.error(f"Error running regression test: {str(e)}")

    def _update_system_state(self, new_state: Dict) -> None:
        """Update the shared system state"""
        self.system_state.update(new_state)

    def _extract_references(self, text: str) -> List[str]:
        """Extract legal references from text"""
        # Implementation needed for reference extraction
        # This could use regex patterns or more sophisticated NLP
        pass

    def get_system_state(self) -> Dict:
        """Get current system state"""
        return self.system_state.copy()

    async def validate_and_format_reference(self, 
                                          reference: str,
                                          date: Optional[datetime] = None) -> str:
        """Validate and format a single legal reference"""
        validation_result = await self.legal_validator.validate_reference(
            reference, date
        )
        return await self.legal_validator.format_citation(validation_result)