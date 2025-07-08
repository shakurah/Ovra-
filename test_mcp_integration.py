#!/usr/bin/env python3
"""
Comprehensive test for MCP BOE integration
Tests the full pipeline: BOE MCP -> OpenAI Summarization -> Frontend
"""

import asyncio
import os
import sys
sys.path.append('/home/ali/development/ovra_ai/backend')

from app.services.mcp_agent_service import mcp_agent_service
from app.schemas.chat import ChatRequest
import requests
import json


async def test_mcp_direct():
    """Test MCP service directly"""
    print("🔍 Testing MCP Agent Service directly...")
    
    try:
        # Test availability
        is_available = mcp_agent_service.is_available()
        print(f"✅ MCP Service Available: {is_available}")
        
        if not is_available:
            print("❌ MCP Service not available - cannot proceed with tests")
            return False
        
        # Test legal query detection
        legal_queries = [
            "Cuáles son las obligaciones fiscales de un artista freelance?",
            "Normativa sobre derechos de autor en España",
            "BOE legislación cultural"
        ]
        
        non_legal_queries = [
            "Hola, ¿cómo estás?",
            "What's the weather like?",
            "Tell me a joke"
        ]
        
        print("\n🔍 Testing legal query detection...")
        for query in legal_queries:
            is_legal = mcp_agent_service._is_legal_query(query)
            print(f"   '{query[:30]}...' -> Legal: {is_legal}")
        
        for query in non_legal_queries:
            is_legal = mcp_agent_service._is_legal_query(query)
            print(f"   '{query[:30]}...' -> Legal: {is_legal}")
        
        # Test BOE query with streaming
        print("\n🔍 Testing BOE MCP streaming query...")
        test_request = ChatRequest(
            message="¿Cuáles son las obligaciones fiscales de un artista autónomo en España?",
            conversation_id=None
        )
        
        response_chunks = []
        async for chunk in mcp_agent_service.query_boe_and_summarize(test_request):
            response_chunks.append(chunk.content)
            print(f"   📦 Chunk: {chunk.content[:50]}{'...' if len(chunk.content) > 50 else ''}")
            if chunk.is_complete:
                break
        
        full_response = ''.join(response_chunks)
        print(f"\n✅ Full BOE MCP Response Length: {len(full_response)} characters")
        print(f"   Sample: {full_response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP Direct Test Failed: {e}")
        return False


def test_backend_api():
    """Test backend API endpoints"""
    print("\n🔍 Testing Backend API Integration...")
    
    try:
        # Test health endpoint
        health_response = requests.get('http://localhost:8000/api/v1/chat/health/')
        print(f"✅ Health Status: {health_response.status_code}")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   MCP Integration: {health_data.get('mcp_boe_integration', 'Unknown')}")
        
        # Test authentication
        login_response = requests.post('http://localhost:8000/api/v1/auth/login/', 
            json={'email': 'test@example.com', 'password': 'password123'})
        
        if login_response.status_code != 200:
            print("❌ Authentication failed - cannot test chat")
            return False
        
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        print("✅ Authentication successful")
        
        # Test legal query via streaming API
        print("\n🔍 Testing streaming chat with legal query...")
        chat_request = {
            'message': '¿Qué obligaciones fiscales tiene un artista freelance en España según el BOE?',
            'conversation_id': None
        }
        
        stream_response = requests.post('http://localhost:8000/api/v1/chat/stream/', 
            json=chat_request, headers=headers, stream=True)
        
        if stream_response.status_code == 200:
            print("✅ Streaming endpoint accessible")
            chunks = []
            mcp_used = False
            
            for line in stream_response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if data.get('content'):
                                chunks.append(data['content'])
                            if data.get('mcp_used'):
                                mcp_used = True
                            print(f"   📦 Chunk: {data.get('content', '')[:50]}{'...' if len(data.get('content', '')) > 50 else ''}")
                        except json.JSONDecodeError:
                            continue
            
            full_response = ''.join(chunks)
            print(f"\n✅ Streaming Response Length: {len(full_response)} characters")
            print(f"✅ MCP Used in Response: {mcp_used}")
            print(f"   Sample: {full_response[:200]}...")
            
            return True
        else:
            print(f"❌ Streaming failed: {stream_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Backend API Test Failed: {e}")
        return False


async def test_complete_pipeline():
    """Test complete pipeline end-to-end"""
    print("\n🔍 Testing Complete Pipeline...")
    
    try:
        # Direct MCP test
        mcp_success = await test_mcp_direct()
        
        # Backend API test
        api_success = test_backend_api()
        
        print(f"\n📊 Test Results Summary:")
        print(f"   MCP Direct Test: {'✅ PASS' if mcp_success else '❌ FAIL'}")
        print(f"   Backend API Test: {'✅ PASS' if api_success else '❌ FAIL'}")
        
        if mcp_success and api_success:
            print("\n🎉 All tests passed! MCP BOE integration is working correctly.")
            return True
        else:
            print("\n⚠️  Some tests failed. Check the output above for details.")
            return False
            
    except Exception as e:
        print(f"❌ Complete Pipeline Test Failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting MCP BOE Integration Tests...\n")
    success = asyncio.run(test_complete_pipeline())
    
    if success:
        print("\n✅ MCP Integration is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ MCP Integration has issues!")
        sys.exit(1)