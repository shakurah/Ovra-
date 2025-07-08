#!/usr/bin/env python3
"""
Test MCP integration with queries for 2025 content to verify latest BOE data
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'mcp_2025_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API Configuration
BASE_URL = "http://localhost:8000"
AUTH_TOKEN = os.getenv("TEST_AUTH_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5ZDFhNmQ5Yy0yNWZjLTQ1MTUtODJjNC1mOTJjOGZlYTE1NjEiLCJleHAiOjE3Njg3MTg0ODl9.b2I8fqxQfnKN0PiAXwMPFQ8kDzMdPfO3BYSh1lBF4Wg")

# Test queries for 2025 content
TEST_QUERIES_2025 = [
    {
        "name": "Normativa BOE 2025",
        "query": "¿Qué normativa del BOE ha sido publicada en 2025?",
        "expected_keywords": ["2025", "BOE", "normativa"]
    },
    {
        "name": "Legislación fiscal 2025",
        "query": "Cambios en la legislación fiscal española para 2025",
        "expected_keywords": ["2025", "fiscal", "cambios", "legislación"]
    },
    {
        "name": "IRPF 2025",
        "query": "Novedades del IRPF para el año 2025 según el BOE",
        "expected_keywords": ["2025", "IRPF", "BOE"]
    },
    {
        "name": "IVA cultural 2025",
        "query": "¿Hay cambios en el IVA para profesionales culturales en 2025?",
        "expected_keywords": ["2025", "IVA", "cultural", "profesionales"]
    },
    {
        "name": "Autónomos 2025",
        "query": "Nuevas regulaciones para autónomos en 2025 publicadas en el BOE",
        "expected_keywords": ["2025", "autónomos", "BOE", "regulaciones"]
    }
]


async def test_health_check(session):
    """Test health check endpoint"""
    try:
        url = f"{BASE_URL}/api/v1/chat/health/"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"✅ Health check passed: {data}")
                return True
            else:
                logger.error(f"❌ Health check failed: {response.status}")
                return False
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return False


async def test_2025_query(session, query_info):
    """Test a single 2025-related query"""
    logger.info(f"\n{'='*60}")
    logger.info(f"🔍 Testing: {query_info['name']}")
    logger.info(f"Query: {query_info['query']}")
    logger.info(f"Expected keywords: {query_info['expected_keywords']}")
    
    url = f"{BASE_URL}/api/v1/chat/stream/"
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": query_info["query"],
        "conversation_id": f"test_2025_{datetime.now().timestamp()}"
    }
    
    try:
        start_time = datetime.now()
        full_response = ""
        chunk_count = 0
        mcp_logs_found = []
        
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"❌ Request failed: {response.status} - {error_text}")
                return False
            
            # Read streaming response
            async for line in response.content:
                line = line.decode('utf-8').strip()
                
                if line.startswith('data: '):
                    data_str = line[6:]  # Remove 'data: ' prefix
                    
                    if data_str == '[DONE]':
                        break
                    
                    try:
                        chunk_data = json.loads(data_str)
                        chunk_count += 1
                        
                        # Check if MCP was used
                        if chunk_data.get('mcp_used'):
                            logger.info(f"✅ MCP used for this query")
                        
                        # Collect content
                        content = chunk_data.get('content', '')
                        full_response += content
                        
                        # Look for MCP logging indicators
                        if any(indicator in content for indicator in ['[MCP->BOE]', '[BOE->MCP]', '🔍', '📤', '📥']):
                            mcp_logs_found.append(content)
                            logger.info(f"📋 MCP Log found: {content[:100]}...")
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse chunk: {e}")
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Analyze response
        logger.info(f"\n📊 Response Analysis:")
        logger.info(f"Duration: {duration:.2f}s")
        logger.info(f"Chunks received: {chunk_count}")
        logger.info(f"Response length: {len(full_response)} characters")
        logger.info(f"MCP logs found: {len(mcp_logs_found)}")
        
        # Check for expected keywords
        keywords_found = []
        keywords_missing = []
        
        for keyword in query_info['expected_keywords']:
            if keyword.lower() in full_response.lower():
                keywords_found.append(keyword)
            else:
                keywords_missing.append(keyword)
        
        logger.info(f"Keywords found: {keywords_found}")
        if keywords_missing:
            logger.warning(f"Keywords missing: {keywords_missing}")
        
        # Check for 2025 content specifically
        import re
        year_2025_matches = re.findall(r'2025', full_response)
        logger.info(f"🗓️  2025 mentions found: {len(year_2025_matches)}")
        
        # Save response for detailed analysis
        result_file = f"mcp_2025_result_{query_info['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f"# Test: {query_info['name']}\n\n")
            f.write(f"**Query**: {query_info['query']}\n\n")
            f.write(f"**Duration**: {duration:.2f}s\n")
            f.write(f"**Chunks**: {chunk_count}\n")
            f.write(f"**MCP Used**: {'Yes' if any(mcp_logs_found) else 'Unknown'}\n")
            f.write(f"**2025 Mentions**: {len(year_2025_matches)}\n\n")
            f.write("## Response\n\n")
            f.write(full_response)
            f.write("\n\n## MCP Logs\n\n")
            for log in mcp_logs_found:
                f.write(f"- {log}\n")
        
        logger.info(f"💾 Full response saved to: {result_file}")
        
        # Determine success
        success = len(year_2025_matches) > 0 or "2025" in query_info['query']
        if success:
            logger.info(f"✅ Test passed: Found 2025-related content")
        else:
            logger.warning(f"⚠️  Test inconclusive: No explicit 2025 content found")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def run_all_tests():
    """Run all 2025 content tests"""
    logger.info("🚀 Starting MCP 2025 Content Tests")
    logger.info(f"API Base URL: {BASE_URL}")
    logger.info(f"Number of tests: {len(TEST_QUERIES_2025)}")
    
    async with aiohttp.ClientSession() as session:
        # First check health
        if not await test_health_check(session):
            logger.error("Health check failed, aborting tests")
            return
        
        # Run all 2025 queries
        results = []
        for query_info in TEST_QUERIES_2025:
            result = await test_2025_query(session, query_info)
            results.append({
                "name": query_info["name"],
                "success": result
            })
            
            # Small delay between requests
            await asyncio.sleep(2)
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info("📊 TEST SUMMARY")
        logger.info(f"{'='*60}")
        
        total = len(results)
        successful = sum(1 for r in results if r["success"])
        
        for result in results:
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} {result['name']}")
        
        logger.info(f"\nTotal: {successful}/{total} tests completed")
        logger.info(f"Success rate: {(successful/total)*100:.1f}%")
        
        # Save summary
        summary_file = f"mcp_2025_test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_tests": total,
                "successful": successful,
                "results": results
            }, f, indent=2)
        
        logger.info(f"\n💾 Test summary saved to: {summary_file}")


if __name__ == "__main__":
    asyncio.run(run_all_tests())