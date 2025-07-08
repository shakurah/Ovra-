#!/usr/bin/env python3
"""
Debug the MCP service implementation
"""

import asyncio
import os
import logging
from app.services.mcp_agent_service import mcp_agent_service
from app.schemas.chat import ChatRequest

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_mcp_service():
    """Debug MCP service implementation"""
    print("🔍 Debugging MCP service...")
    
    # Check if service is available
    print(f"📊 MCP Service Available: {mcp_agent_service.is_available()}")
    
    if not mcp_agent_service.is_available():
        print("❌ MCP service not available")
        return False
    
    # Create test request
    request = ChatRequest(
        message="¿Cuál es la normativa fiscal para artistas freelance en España?",
        conversation_id="debug_test_123"
    )
    
    print(f"🔍 Testing query: {request.message}")
    
    # Test the query
    try:
        full_response = ""
        chunk_count = 0
        
        async for chunk in mcp_agent_service.query_boe_and_summarize(request):
            chunk_count += 1
            full_response += chunk.content
            
            print(f"📦 Chunk {chunk_count}: {len(chunk.content)} chars")
            print(f"   Content: {chunk.content[:100]}...")
            print(f"   Complete: {chunk.is_complete}")
            
            if chunk.is_complete:
                break
        
        print(f"✅ Complete response: {len(full_response)} chars")
        print(f"📝 Full response preview: {full_response[:300]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in MCP service: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(debug_mcp_service())
    if result:
        print("\n✅ MCP service debug successful")
    else:
        print("\n❌ MCP service debug failed")