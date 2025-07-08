#!/usr/bin/env python3
"""
Test Enhanced HTTP MCP integration 
"""
import asyncio
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.enhanced_http_mcp_service import enhanced_http_mcp_service
from app.schemas.chat import ChatRequest

async def test_enhanced_mcp_integration():
    """Test Enhanced HTTP MCP integration"""
    print("🧪 Testing Enhanced HTTP MCP Integration")
    print("=" * 60)
    
    # Test 1: Check server health
    print("\n🔍 Test 1: Check Enhanced HTTP MCP server health")
    health_ok = await enhanced_http_mcp_service.check_server_health()
    
    if health_ok:
        print("✅ Enhanced HTTP MCP server is healthy and available")
    else:
        print("❌ Enhanced HTTP MCP server is not available")
        return False
    
    # Test 2: Legal query that should trigger BOE search with AI enhancement
    print("\n🧪 Test 2: Legal query about taxes for artists (Enhanced)")
    test_request = ChatRequest(
        message="¿Qué leyes regulan los impuestos para artistas en España?",
        conversation_id="test_legal_enhanced"
    )
    
    try:
        chunk_count = 0
        total_content = ""
        
        async for chunk in enhanced_http_mcp_service.query_boe_enhanced(test_request):
            chunk_count += 1
            total_content += chunk.content
            
            if chunk_count <= 3:  # Show first few chunks
                print(f"   Chunk {chunk_count}: {chunk.content[:100]}...")
            
            if chunk.is_complete:
                break
        
        print(f"✅ Test 2 completed: {chunk_count} chunks, {len(total_content)} characters")
        print(f"   Response preview: {total_content[:300]}...")
        
        if "error" in total_content.lower() or chunk_count == 0:
            print("❌ Test 2 failed: Error in response or no chunks")
            return False
        
        # Check if response has AI enhancement indicators
        if "enhanced" in total_content.lower() or "ai" in total_content.lower():
            print("✅ AI enhancement detected in response")
        
    except Exception as e:
        print(f"❌ Test 2 failed with exception: {e}")
        return False
    
    # Test 3: Non-legal query
    print("\n🧪 Test 3: Non-legal query with Enhanced service")
    test_request2 = ChatRequest(
        message="What's the weather like today?",
        conversation_id="test_non_legal_enhanced"
    )
    
    try:
        chunk_count = 0
        async for chunk in enhanced_http_mcp_service.query_boe_enhanced(test_request2):
            chunk_count += 1
            if chunk.is_complete:
                break
        
        print(f"✅ Test 3 completed: {chunk_count} chunks (non-legal response)")
        
    except Exception as e:
        print(f"❌ Test 3 failed with exception: {e}")
        return False
    
    # Test 4: Direct BOE search test
    print("\n🧪 Test 4: Direct BOE search for 'ley fiscal' (Enhanced)")
    try:
        search_result = await enhanced_http_mcp_service.search_laws("ley fiscal")
        
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
    
    # Test 5: Complex legal query to test AI enhancement
    print("\n🧪 Test 5: Complex legal query for AI enhancement")
    test_request3 = ChatRequest(
        message="Soy un artista freelance que factura desde España a clientes europeos. ¿Qué obligaciones fiscales tengo con el IVA y el IRPF?",
        conversation_id="test_complex_legal"
    )
    
    try:
        chunk_count = 0
        total_content = ""
        
        async for chunk in enhanced_http_mcp_service.query_boe_enhanced(test_request3):
            chunk_count += 1
            total_content += chunk.content
            
            if chunk.is_complete:
                break
        
        print(f"✅ Test 5 completed: {chunk_count} chunks, {len(total_content)} characters")
        print(f"   Complex query response preview: {total_content[:200]}...")
        
        if "error" in total_content.lower() or chunk_count == 0:
            print("❌ Test 5 failed: Error in response or no chunks")
            return False
            
    except Exception as e:
        print(f"❌ Test 5 failed with exception: {e}")
        return False
    
    return True

async def main():
    """Run the test"""
    print("🚀 Starting Enhanced HTTP MCP Integration Test")
    print("=" * 70)
    
    success = await test_enhanced_mcp_integration()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 All Enhanced HTTP MCP integration tests passed!")
        print("✅ Enhanced HTTP MCP server is working correctly with AI integration")
        print("🤖 OpenAI analysis of BOE data is functional")
        print("🌐 BOE API integration is stable")
    else:
        print("❌ Enhanced HTTP MCP integration tests failed")
        print("📋 Check server logs and OpenAI API configuration")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())