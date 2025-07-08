#!/usr/bin/env python3
"""
Test MCP integration with enhanced logging to show MCP->BOE communication
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
        logging.FileHandler(f'mcp_logging_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API Configuration
BASE_URL = "http://localhost:8000"
AUTH_TOKEN = os.getenv("TEST_AUTH_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5ZDFhNmQ5Yy0yNWZjLTQ1MTUtODJjNC1mOTJjOGZlYTE1NjEiLCJleHAiOjE3Njg3MTg0ODl9.b2I8fqxQfnKN0PiAXwMPFQ8kDzMdPfO3BYSh1lBF4Wg")


async def test_with_mcp_logging(query: str, test_name: str):
    """Test a query and capture MCP logging"""
    logger.info(f"\n{'='*60}")
    logger.info(f"🧪 Test: {test_name}")
    logger.info(f"📝 Query: {query}")
    
    url = f"{BASE_URL}/api/v1/chat/stream/"
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": query,
        "conversation_id": f"test_logging_{datetime.now().timestamp()}"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            start_time = datetime.now()
            full_response = ""
            chunk_count = 0
            mcp_communication_log = []
            
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Request failed: {response.status} - {error_text}")
                    return
                
                logger.info(f"✅ Request successful, streaming response...")
                
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
                            
                            # Extract content
                            content = chunk_data.get('content', '')
                            full_response += content
                            
                            # Check for MCP usage
                            if chunk_data.get('mcp_used') and chunk_count == 1:
                                logger.info(f"✅ MCP integration active for this query")
                            
                            # Display chunk info for debugging
                            if chunk_count <= 5:
                                logger.debug(f"Chunk {chunk_count}: {content[:50]}...")
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse chunk: {e}")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Check backend logs for MCP communication
            # In real scenario, these would be captured from the backend logs
            logger.info(f"\n📊 Response Summary:")
            logger.info(f"⏱️  Duration: {duration:.2f}s")
            logger.info(f"📦 Chunks received: {chunk_count}")
            logger.info(f"📏 Response length: {len(full_response)} characters")
            
            # Save detailed response
            result_file = f"mcp_logging_result_{test_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(result_file, 'w', encoding='utf-8') as f:
                f.write(f"# MCP Logging Test: {test_name}\n\n")
                f.write(f"**Query**: {query}\n\n")
                f.write(f"**Timestamp**: {datetime.now().isoformat()}\n")
                f.write(f"**Duration**: {duration:.2f}s\n")
                f.write(f"**Chunks**: {chunk_count}\n\n")
                f.write("## Expected MCP Communication Flow\n\n")
                f.write("1. 🔍 [MCP->BOE] Starting MCP agent query\n")
                f.write("2. 📤 [MCP->BOE] Sending query to BOE MCP server\n")
                f.write("3. 📥 [BOE->MCP] Received BOE result\n")
                f.write("4. 💾 [MCP] Full BOE result saved to file\n\n")
                f.write("## Response Content\n\n")
                f.write(full_response)
            
            logger.info(f"💾 Full response saved to: {result_file}")
            
            # Display first part of response
            logger.info(f"\n📄 Response Preview:")
            preview = full_response[:500] + "..." if len(full_response) > 500 else full_response
            logger.info(preview)
            
        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}")
            import traceback
            logger.error(traceback.format_exc())


async def run_mcp_logging_tests():
    """Run tests to verify MCP logging is working"""
    logger.info("🚀 Starting MCP Logging Tests")
    logger.info(f"API Base URL: {BASE_URL}")
    
    # Test queries
    test_queries = [
        {
            "name": "Tax Rates 2025",
            "query": "¿Cuáles son las tarifas del IRPF para 2025 según el BOE?"
        },
        {
            "name": "Cultural VAT 2025",
            "query": "Tipos de IVA aplicables a servicios culturales en 2025"
        },
        {
            "name": "Artist Regulations 2025",
            "query": "Nuevas regulaciones BOE 2025 para artistas y profesionales culturales"
        }
    ]
    
    # Instructions for checking backend logs
    logger.info("\n📋 To see MCP->BOE communication logs:")
    logger.info("1. Check the FastAPI service logs: sudo journalctl -u ovra-backend -f")
    logger.info("2. Look for messages with emojis: 🔍, 📤, 📥, 💾")
    logger.info("3. Check for saved MCP result files: mcp_boe_result_*.txt")
    
    # Run tests
    for test in test_queries:
        await test_with_mcp_logging(test["query"], test["name"])
        await asyncio.sleep(3)  # Delay between tests
    
    logger.info("\n✅ All tests completed!")
    logger.info("Check the backend logs to see the MCP->BOE communication details")


if __name__ == "__main__":
    asyncio.run(run_mcp_logging_tests())