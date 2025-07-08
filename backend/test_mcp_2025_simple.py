#!/usr/bin/env python3
"""
Simple test for MCP integration with 2025 queries
"""

import asyncio
import httpx
import json
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:8000"
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5ZDFhNmQ5Yy0yNWZjLTQ1MTUtODJjNC1mOTJjOGZlYTE1NjEiLCJleHAiOjE3Njg3MTg0ODl9.b2I8fqxQfnKN0PiAXwMPFQ8kDzMdPfO3BYSh1lBF4Wg"


async def test_2025_query():
    """Test a query about 2025 tax rates"""
    query = "¿Cuáles son los nuevos tipos de IRPF para 2025 según las últimas publicaciones del BOE?"
    
    logger.info(f"🧪 Testing 2025 query: {query}")
    
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": query,
        "conversation_id": f"test_2025_{datetime.now().timestamp()}"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Test streaming endpoint
            logger.info("📤 Sending request to streaming endpoint...")
            
            async with client.stream(
                'POST',
                f"{BASE_URL}/api/v1/chat/stream/",
                headers=headers,
                json=payload,
                timeout=30.0
            ) as response:
                
                if response.status_code != 200:
                    logger.error(f"❌ Request failed: {response.status_code}")
                    return
                
                logger.info("✅ Request successful, reading stream...")
                
                full_response = ""
                chunk_count = 0
                mcp_status_found = False
                
                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        data_str = line[6:]
                        
                        if data_str == '[DONE]':
                            break
                        
                        try:
                            chunk_data = json.loads(data_str)
                            chunk_count += 1
                            content = chunk_data.get('content', '')
                            full_response += content
                            
                            # Check for MCP status message
                            if '🔍 **Consultando BOE**' in content:
                                mcp_status_found = True
                                logger.info(f"✅ MCP status message found: {content.strip()}")
                            
                            # Log first few chunks
                            if chunk_count <= 3:
                                logger.info(f"Chunk {chunk_count}: {content[:80]}...")
                            
                        except json.JSONDecodeError:
                            pass
                
                logger.info(f"\n📊 Results:")
                logger.info(f"- Total chunks: {chunk_count}")
                logger.info(f"- Response length: {len(full_response)} chars")
                logger.info(f"- MCP status shown: {'Yes' if mcp_status_found else 'No'}")
                
                # Check for 2025 mentions
                count_2025 = full_response.count('2025')
                logger.info(f"- 2025 mentions: {count_2025}")
                
                # Save response
                filename = f"mcp_2025_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"# MCP 2025 Test Response\n\n")
                    f.write(f"**Query**: {query}\n\n")
                    f.write(f"**Timestamp**: {datetime.now().isoformat()}\n\n")
                    f.write(f"**Stats**:\n")
                    f.write(f"- Chunks: {chunk_count}\n")
                    f.write(f"- Length: {len(full_response)} chars\n")
                    f.write(f"- 2025 mentions: {count_2025}\n")
                    f.write(f"- MCP status shown: {'Yes' if mcp_status_found else 'No'}\n\n")
                    f.write("## Response\n\n")
                    f.write(full_response)
                
                logger.info(f"💾 Response saved to: {filename}")
                
                # Show preview
                if len(full_response) > 300:
                    logger.info(f"\n📄 Response preview:\n{full_response[:300]}...\n")
                else:
                    logger.info(f"\n📄 Full response:\n{full_response}\n")
                
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    logger.info("🚀 Starting MCP 2025 Content Test")
    logger.info(f"Backend URL: {BASE_URL}")
    logger.info("Note: Check backend logs with: sudo journalctl -u ovra-backend -f")
    logger.info("")
    
    asyncio.run(test_2025_query())