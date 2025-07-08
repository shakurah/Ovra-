#!/usr/bin/env python3
"""
Test HTTP MCP integration with chat service
"""
import asyncio
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.http_mcp_service import http_mcp_service
from app.schemas.chat import ChatRequest

async def test_http_mcp_integration():
    """Test HTTP MCP integration"""
    print("🧪 Testing HTTP MCP Integration")
    print("=" * 60)
    
    # Test 1: Check server health
    print("\n🔍 Test 1: Check HTTP MCP server health")
    health_ok = await http_mcp_service.check_server_health()
    
    if health_ok:
        print("✅ HTTP MCP server is healthy and available")
    else:
        print("❌ HTTP MCP server is not available")
        return False
    
    # Test 2: Legal query that should trigger BOE search
    print("\n🧪 Test 2: Legal query about taxes for artists")
    test_request = ChatRequest(
        message="¿Qué leyes regulan los impuestos para artistas en España?",
        conversation_id="test_legal_query"
    )
    
    try:
        chunk_count = 0
        total_content = ""
        
        async for chunk in http_mcp_service.query_boe_http(test_request):
            chunk_count += 1
            total_content += chunk.content
            
            if chunk_count <= 3:  # Show first few chunks
                print(f"   Chunk {chunk_count}: {chunk.content[:100]}...")
            
            if chunk.is_complete:
                break
        
        print(f"✅ Test 2 completed: {chunk_count} chunks, {len(total_content)} characters")
        print(f"   Response preview: {total_content[:200]}...")
        
        if "error" in total_content.lower() or chunk_count == 0:
            print("❌ Test 2 failed: Error in response or no chunks")
            return False
        
    except Exception as e:
        print(f"❌ Test 2 failed with exception: {e}")
        return False
    
    # Test 3: Non-legal query
    print("\n🧪 Test 3: Non-legal query")
    test_request2 = ChatRequest(
        message="What's the weather like today?",
        conversation_id="test_non_legal"
    )
    
    try:
        chunk_count = 0
        async for chunk in http_mcp_service.query_boe_http(test_request2):
            chunk_count += 1
            if chunk.is_complete:
                break
        
        print(f"✅ Test 3 completed: {chunk_count} chunks (non-legal response)")
        
    except Exception as e:
        print(f"❌ Test 3 failed with exception: {e}")
        return False
    
    # Test 4: Direct BOE search test
    print("\n🧪 Test 4: Direct BOE search for 'ley fiscal'")
    try:
        search_result = await http_mcp_service.search_laws("ley fiscal")
        
        if "error" in search_result:
            print(f"❌ Test 4 failed: {search_result['error']}")
            return False
        
        if "data" in search_result:
            print("✅ Test 4 completed: Successfully searched BOE API")
            # Show some data from the result
            data = search_result["data"]
            if "hits" in data.get("data", {}):
                total_hits = data["data"]["hits"]["total"]["value"]
                print(f"   Found {total_hits} results for 'ley fiscal'")
        else:
            print("❌ Test 4 failed: No data in search result")
            return False
            
    except Exception as e:
        print(f"❌ Test 4 failed with exception: {e}")
        return False
    
    # Test 5: Auxiliary table test
    print("\n🧪 Test 5: Get auxiliary table 'materias'")
    try:
        table_result = await http_mcp_service.get_auxiliary_table("materias")
        
        if "error" in table_result:
            print(f"❌ Test 5 failed: {table_result['error']}")
            return False
        
        if "data" in table_result:
            print("✅ Test 5 completed: Successfully retrieved materias table")
            data = table_result["data"]
            if isinstance(data.get("data"), list):
                print(f"   Found {len(data['data'])} materias")
        else:
            print("❌ Test 5 failed: No data in table result")
            return False
            
    except Exception as e:
        print(f"❌ Test 5 failed with exception: {e}")
        return False
    
    return True

async def main():
    """Run the test"""
    print("🚀 Starting HTTP MCP Integration Test")
    print("=" * 70)
    
    success = await test_http_mcp_integration()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 All HTTP MCP integration tests passed!")
        print("✅ HTTP MCP server is working correctly with chat service")
        print("🌐 BOE API integration is functional")
    else:
        print("❌ HTTP MCP integration tests failed")
        print("📋 Check server logs and BOE API availability")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())