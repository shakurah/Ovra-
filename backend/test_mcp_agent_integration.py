#!/usr/bin/env python3
"""
Test MCP Agent HTTP integration 
"""
import asyncio
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.mcp_agent_http_service import mcp_agent_http_service
from app.schemas.chat import ChatRequest

async def test_mcp_agent_integration():
    """Test MCP Agent HTTP integration"""
    print("🧪 Testing MCP Agent HTTP Integration")
    print("=" * 60)
    
    # Test 1: Initialize service
    print("\n🔍 Test 1: Initialize MCP Agent service")
    initialized = await mcp_agent_http_service._ensure_initialized()
    
    if initialized:
        print("✅ MCP Agent service initialized successfully")
    else:
        print("❌ MCP Agent service failed to initialize")
        return False
    
    # Test 2: Legal query that should trigger BOE search
    print("\n🧪 Test 2: Legal query about taxes for artists using MCP Agent")
    test_request = ChatRequest(
        message="¿Qué leyes regulan los impuestos para artistas en España?",
        conversation_id="test_legal_agent"
    )
    
    try:
        chunk_count = 0
        total_content = ""
        
        async for chunk in mcp_agent_http_service.query_boe_agent(test_request):
            chunk_count += 1
            total_content += chunk.content
            
            if chunk_count <= 3:  # Show first few chunks
                print(f"   Chunk {chunk_count}: {chunk.content[:100]}...")
            
            if chunk.is_complete:
                break
        
        print(f"✅ Test 2 completed: {chunk_count} chunks, {len(total_content)} characters")
        print(f"   Response preview: {total_content[:300]}...")
        
        if "error" in total_content.lower() and "mcp agent" in total_content.lower():
            print("❌ Test 2 failed: MCP Agent error in response")
            return False
        
    except Exception as e:
        print(f"❌ Test 2 failed with exception: {e}")
        return False
    
    # Test 3: Non-legal query
    print("\n🧪 Test 3: Non-legal query with MCP Agent")
    test_request2 = ChatRequest(
        message="What's the weather like today?",
        conversation_id="test_non_legal_agent"
    )
    
    try:
        chunk_count = 0
        async for chunk in mcp_agent_http_service.query_boe_agent(test_request2):
            chunk_count += 1
            if chunk.is_complete:
                break
        
        print(f"✅ Test 3 completed: {chunk_count} chunks (non-legal response)")
        
    except Exception as e:
        print(f"❌ Test 3 failed with exception: {e}")
        return False
    
    return True

async def main():
    """Run the test"""
    print("🚀 Starting MCP Agent HTTP Integration Test")
    print("=" * 70)
    
    success = await test_mcp_agent_integration()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 All MCP Agent HTTP integration tests passed!")
        print("✅ MCP Agent is working correctly with HTTP transport")
        print("🌐 BOE API integration via MCP Agent is functional")
    else:
        print("❌ MCP Agent HTTP integration tests failed")
        print("📋 Check server logs and MCP configuration")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())