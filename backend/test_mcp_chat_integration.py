#!/usr/bin/env python3
"""
Test MCP integration with chat service
"""
import asyncio
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.mcp_agent_service import mcp_agent_service
from app.schemas.chat import ChatRequest

async def test_mcp_chat_integration():
    """Test MCP integration with fixed server"""
    print("🧪 Testing MCP Chat Integration with Fixed Server")
    print("=" * 60)
    
    # Reinitialize the service to pick up the fixed server
    mcp_agent_service.reinitialize()
    
    # Wait a moment for initialization
    await asyncio.sleep(2)
    
    if not mcp_agent_service.is_available():
        print("❌ MCP service not available after reinitialization")
        return False
    
    print("✅ MCP service reinitialized and available")
    
    # Test 1: Legal query that should trigger BOE search
    print("\n🧪 Test 1: Legal query about taxes for artists")
    test_request = ChatRequest(
        message="¿Qué leyes regulan los impuestos para artistas en España?",
        conversation_id="test_legal_query"
    )
    
    try:
        chunk_count = 0
        total_content = ""
        
        async for chunk in mcp_agent_service.query_boe_and_summarize(test_request):
            chunk_count += 1
            total_content += chunk.content
            
            if chunk_count <= 3:  # Show first few chunks
                print(f"   Chunk {chunk_count}: {chunk.content[:100]}...")
            
            if chunk.is_complete:
                break
        
        print(f"✅ Test 1 completed: {chunk_count} chunks, {len(total_content)} characters")
        
        if "error" in total_content.lower() or chunk_count == 0:
            print("❌ Test 1 failed: Error in response or no chunks")
            return False
        
    except Exception as e:
        print(f"❌ Test 1 failed with exception: {e}")
        return False
    
    # Test 2: Non-legal query
    print("\n🧪 Test 2: Non-legal query")
    test_request2 = ChatRequest(
        message="What's the weather like today?",
        conversation_id="test_non_legal"
    )
    
    try:
        chunk_count = 0
        async for chunk in mcp_agent_service.query_boe_and_summarize(test_request2):
            chunk_count += 1
            if chunk.is_complete:
                break
        
        print(f"✅ Test 2 completed: {chunk_count} chunks (non-legal response)")
        
    except Exception as e:
        print(f"❌ Test 2 failed with exception: {e}")
        return False
    
    # Test 3: Another legal query
    print("\n🧪 Test 3: BOE auxiliary table query")
    test_request3 = ChatRequest(
        message="¿Qué materias están disponibles en el BOE?",
        conversation_id="test_materias"
    )
    
    try:
        chunk_count = 0
        total_content = ""
        
        async for chunk in mcp_agent_service.query_boe_and_summarize(test_request3):
            chunk_count += 1
            total_content += chunk.content
            
            if chunk.is_complete:
                break
        
        print(f"✅ Test 3 completed: {chunk_count} chunks, {len(total_content)} characters")
        
        if "error" in total_content.lower() or chunk_count == 0:
            print("❌ Test 3 failed: Error in response or no chunks")
            return False
        
    except Exception as e:
        print(f"❌ Test 3 failed with exception: {e}")
        return False
    
    return True

async def main():
    """Run the test"""
    print("🚀 Starting MCP Chat Integration Test")
    print("=" * 70)
    
    success = await test_mcp_chat_integration()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 All MCP chat integration tests passed!")
        print("✅ Fixed MCP server is working correctly with chat service")
    else:
        print("❌ MCP chat integration tests failed")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())