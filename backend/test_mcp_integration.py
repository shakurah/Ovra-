#!/usr/bin/env python3
"""
Test script for MCP BOE integration
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.mcp_agent_service import mcp_agent_service
from app.schemas.chat import ChatRequest
import json

async def test_mcp_integration():
    """Test the MCP integration functionality"""
    print("🧪 Testing MCP BOE Integration")
    print("=" * 50)
    
    # Test 1: Check MCP service availability
    print("\n1. Testing MCP Service Availability")
    is_available = mcp_agent_service.is_available()
    print(f"✅ MCP Service Available: {is_available}")
    
    if not is_available:
        print("❌ MCP service not available. Cannot proceed with tests.")
        return False
    
    # Test 2: Test MCP agent direct access
    print("\n2. Testing MCP Agent")
    try:
        if hasattr(mcp_agent_service, '_agent') and mcp_agent_service._agent:
            print("✅ MCP agent object exists")
            
            # Test a simple query
            simple_query = "Busca información sobre materias en el BOE"
            result = await mcp_agent_service._agent.run(simple_query)
            
            if result:
                print("✅ MCP agent query successful")
                print(f"   Result length: {len(result)} characters")
                if len(result) > 100:
                    preview = result[:100] + "..."
                else:
                    preview = result
                print(f"   Preview: {preview}")
            else:
                print("❌ MCP agent query returned empty result")
                return False
        else:
            print("❌ MCP agent not properly initialized")
            return False
    except Exception as e:
        print(f"❌ MCP agent test failed: {e}")
        return False
    
    # Test 3: Test chat integration (query_boe_and_summarize)
    print("\n3. Testing Chat Integration")
    try:
        # Create a test chat request
        test_request = ChatRequest(
            message="¿Qué leyes regulan los impuestos para artistas en España?",
            conversation_id="test_conversation"
        )
        
        print(f"Processing chat request: {test_request.message}")
        
        # Test the streaming response
        chunk_count = 0
        total_content = ""
        
        async for chunk in mcp_agent_service.query_boe_and_summarize(test_request):
            chunk_count += 1
            total_content += chunk.content
            print(f"   Received chunk {chunk_count}: {len(chunk.content)} chars")
            
            if chunk.is_complete:
                break
        
        if chunk_count > 0:
            print(f"✅ Chat integration successful")
            print(f"   Received {chunk_count} chunks, total content: {len(total_content)} chars")
            if total_content:
                preview = total_content[:200] + "..." if len(total_content) > 200 else total_content
                print(f"   Content preview: {preview}")
        else:
            print("❌ Chat integration failed - no chunks received")
            return False
            
    except Exception as e:
        print(f"❌ Chat integration failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ All MCP integration tests passed!")
    return True

async def test_direct_server():
    """Test the MCP server directly"""
    print("\n🔗 Testing Direct MCP Server")
    print("=" * 50)
    
    try:
        # Test if we can import and run the server
        from boe_mcp.server import main
        print("✅ MCP server module imported successfully")
        
        # The server runs in stdio mode, so we can't test it directly here
        # but we can verify the import works
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import MCP server: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting MCP Integration Tests")
    print("=" * 60)
    
    success = True
    
    # Test direct server import
    if not await test_direct_server():
        success = False
    
    # Test MCP integration
    if not await test_mcp_integration():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! MCP integration is working correctly.")
    else:
        print("❌ Some tests failed. Please check the output above.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())