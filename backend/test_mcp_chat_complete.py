#!/usr/bin/env python3
"""
Complete test for MCP chat endpoint integration
Tests the full flow: user query -> MCP BOE -> ChatGPT summary -> user response
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any, List
import httpx
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = f"mcp_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
TEST_USER_PASSWORD = "testpass123"

class MCPChatTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.auth_token = None
        self.test_results = []
        
    async def authenticate(self) -> bool:
        """Use provided JWT token for authentication"""
        try:
            # Use the provided token directly
            self.auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzUxOTM5OTczfQ.HuvCyTdMTcGhET3ojrLCrL-lK-4jSMYse0YqNJbctqs"
            
            # Test the token by calling a protected endpoint
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            test_response = await self.client.get(
                f"{API_BASE_URL}/api/v1/chat/health/",
                headers=headers
            )
            
            if test_response.status_code == 200:
                logger.info("✅ Authentication successful using provided token")
                return True
            else:
                logger.error(f"Token validation failed: {test_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    async def test_chat_health(self) -> Dict[str, Any]:
        """Test chat health endpoint"""
        test_name = "Chat Health Check"
        logger.info(f"🔍 Testing: {test_name}")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = await self.client.get(
                f"{API_BASE_URL}/api/v1/chat/health/",
                headers=headers
            )
            
            result = {
                "test_name": test_name,
                "status": "✅ PASS" if response.status_code == 200 else "❌ FAIL",
                "status_code": response.status_code,
                "response_data": response.json() if response.status_code == 200 else response.text,
                "timestamp": datetime.now().isoformat()
            }
            
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"✅ Health check passed - MCP Status: {health_data.get('mcp_boe_integration', 'unknown')}")
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                
            return result
            
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return {
                "test_name": test_name,
                "status": "❌ ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_streaming_chat(self, query: str, expected_keywords: List[str] = None) -> Dict[str, Any]:
        """Test streaming chat endpoint with MCP integration"""
        test_name = f"Streaming Chat: {query[:50]}..."
        logger.info(f"🔍 Testing: {test_name}")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            chat_data = {
                "message": query,
                "conversation_id": f"test_{datetime.now().timestamp()}"
            }
            
            # Use streaming request
            async with self.client.stream(
                "POST",
                f"{API_BASE_URL}/api/v1/chat/stream/",
                json=chat_data,
                headers=headers
            ) as response:
                
                if response.status_code != 200:
                    logger.error(f"❌ Streaming failed: {response.status_code}")
                    return {
                        "test_name": test_name,
                        "status": "❌ FAIL",
                        "status_code": response.status_code,
                        "error": await response.aread(),
                        "timestamp": datetime.now().isoformat()
                    }
                
                # Collect streaming response
                full_response = ""
                chunks_received = 0
                mcp_used = False
                conversation_id = None
                
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        # Parse each chunk
                        for line in chunk.strip().split('\n'):
                            if line.startswith('data: '):
                                data_str = line[6:]  # Remove 'data: ' prefix
                                
                                if data_str == "[DONE]":
                                    logger.info("🏁 Stream completed")
                                    break
                                    
                                try:
                                    chunk_data = json.loads(data_str)
                                    content = chunk_data.get("content", "")
                                    full_response += content
                                    chunks_received += 1
                                    
                                    if chunk_data.get("mcp_used"):
                                        mcp_used = True
                                    
                                    conversation_id = chunk_data.get("conversation_id")
                                    
                                    # Log progress every 10 chunks
                                    if chunks_received % 10 == 0:
                                        logger.info(f"📦 Received {chunks_received} chunks...")
                                    
                                except json.JSONDecodeError:
                                    logger.warning(f"⚠️ Invalid JSON chunk: {data_str}")
                
                # Analyze response
                keyword_matches = []
                if expected_keywords:
                    for keyword in expected_keywords:
                        if keyword.lower() in full_response.lower():
                            keyword_matches.append(keyword)
                
                success = len(full_response) > 0 and chunks_received > 0
                
                result = {
                    "test_name": test_name,
                    "status": "✅ PASS" if success else "❌ FAIL",
                    "query": query,
                    "response_length": len(full_response),
                    "chunks_received": chunks_received,
                    "mcp_used": mcp_used,
                    "conversation_id": conversation_id,
                    "keyword_matches": keyword_matches,
                    "response_preview": full_response[:200] + "..." if len(full_response) > 200 else full_response,
                    "timestamp": datetime.now().isoformat()
                }
                
                if success:
                    logger.info(f"✅ Streaming test passed - {chunks_received} chunks, MCP: {mcp_used}")
                else:
                    logger.error(f"❌ Streaming test failed - Response length: {len(full_response)}")
                
                return result
                
        except Exception as e:
            logger.error(f"❌ Streaming test error: {e}")
            return {
                "test_name": test_name,
                "status": "❌ ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_comprehensive_tests(self):
        """Run comprehensive MCP chat integration tests"""
        logger.info("🚀 Starting comprehensive MCP chat integration tests")
        
        # Test cases with expected behavior
        test_cases = [
            {
                "query": "¿Cuál es la normativa fiscal para artistas freelance en España?",
                "keywords": ["ley", "fiscal", "artista", "BOE", "impuesto"],
                "description": "Legal query about freelance artists taxation"
            },
            {
                "query": "¿Cómo funciona el IVA para profesionales culturales?",
                "keywords": ["iva", "cultural", "profesional", "BOE"],
                "description": "VAT query for cultural professionals"
            },
            {
                "query": "¿Qué es el Real Decreto sobre derechos de autor?",
                "keywords": ["real decreto", "derechos de autor", "BOE"],
                "description": "Copyright legislation query"
            },
            {
                "query": "¿Cuál es la capital de Francia?",
                "keywords": ["servicio", "legal", "fiscal"],
                "description": "Non-legal query (should trigger service scope message)"
            }
        ]
        
        # Authenticate first
        if not await self.authenticate():
            logger.error("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Test health endpoint
        health_result = await self.test_chat_health()
        self.test_results.append(health_result)
        
        # Test each query
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n--- Test {i}/{len(test_cases)}: {test_case['description']} ---")
            
            result = await self.test_streaming_chat(
                test_case["query"],
                test_case["keywords"]
            )
            
            self.test_results.append(result)
            
            # Add delay between tests
            await asyncio.sleep(2)
        
        # Generate report
        await self.generate_test_report()
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("\n📊 Generating test report...")
        
        # Count results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["status"] == "✅ PASS")
        failed_tests = sum(1 for r in self.test_results if r["status"] == "❌ FAIL")
        error_tests = sum(1 for r in self.test_results if r["status"] == "❌ ERROR")
        
        # Create report
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "success_rate": f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%"
            },
            "test_timestamp": datetime.now().isoformat(),
            "detailed_results": self.test_results
        }
        
        # Save report
        report_file = f"mcp_chat_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"🎯 MCP CHAT INTEGRATION TEST REPORT")
        print(f"{'='*60}")
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"🔥 Errors: {error_tests}")
        print(f"📈 Success Rate: {report['test_summary']['success_rate']}")
        print(f"📄 Report saved to: {report_file}")
        
        # Print detailed results
        print(f"\n{'='*60}")
        print(f"📋 DETAILED TEST RESULTS")
        print(f"{'='*60}")
        
        for i, result in enumerate(self.test_results, 1):
            print(f"\n{i}. {result['test_name']}")
            print(f"   Status: {result['status']}")
            
            if result.get("response_length"):
                print(f"   Response Length: {result['response_length']} chars")
            
            if result.get("chunks_received"):
                print(f"   Chunks Received: {result['chunks_received']}")
            
            if result.get("mcp_used") is not None:
                print(f"   MCP Used: {'Yes' if result['mcp_used'] else 'No'}")
            
            if result.get("keyword_matches"):
                print(f"   Keywords Found: {result['keyword_matches']}")
            
            if result.get("error"):
                print(f"   Error: {result['error']}")
            
            if result.get("response_preview"):
                print(f"   Response Preview: {result['response_preview'][:100]}...")
        
        print(f"\n{'='*60}")
        
        # Close client
        await self.client.aclose()
    
    async def quick_test(self, query: str):
        """Quick test for a single query"""
        logger.info(f"🔍 Quick test for: {query}")
        
        if not await self.authenticate():
            logger.error("❌ Authentication failed")
            return
        
        result = await self.test_streaming_chat(query)
        
        print(f"\n{'='*50}")
        print(f"🎯 QUICK TEST RESULT")
        print(f"{'='*50}")
        print(f"Query: {query}")
        print(f"Status: {result['status']}")
        print(f"Response Length: {result.get('response_length', 0)} chars")
        print(f"Chunks Received: {result.get('chunks_received', 0)}")
        print(f"MCP Used: {'Yes' if result.get('mcp_used') else 'No'}")
        
        if result.get('response_preview'):
            print(f"\nResponse Preview:")
            print(result['response_preview'])
        
        await self.client.aclose()


async def main():
    """Main test execution"""
    tester = MCPChatTester()
    
    # Check if quick test mode
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        await tester.quick_test(query)
    else:
        await tester.run_comprehensive_tests()


if __name__ == "__main__":
    asyncio.run(main())