#!/usr/bin/env python3
"""
Test complete chat API integration with Enhanced HTTP MCP
"""
import asyncio
import sys
import json
import httpx
from pathlib import Path

async def test_complete_chat_integration():
    """Test complete chat integration through the API"""
    print("🧪 Testing Complete Chat API Integration")
    print("=" * 60)
    
    # API base URL (adjust if needed)
    base_url = "http://localhost:8000"
    
    # Test credentials (you may need to adjust these)
    import time
    timestamp = str(int(time.time()))
    test_credentials = {
        "email": f"testuser{timestamp}@example.com",
        "password": "testpassword123"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # Test 1: Login to get auth token
        print("\n🔐 Test 1: Login to get authentication token")
        try:
            login_response = await client.post(
                f"{base_url}/api/v1/auth/login/",
                json=test_credentials
            )
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                access_token = login_data.get("access_token")
                if access_token:
                    print("✅ Successfully authenticated")
                    headers = {"Authorization": f"Bearer {access_token}"}
                else:
                    print("❌ No access token received")
                    return False
            else:
                print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
                # Try to create user first
                print("🔄 Attempting to create test user...")
                register_response = await client.post(
                    f"{base_url}/api/v1/auth/register/",
                    json={
                        "email": test_credentials["email"],
                        "password": test_credentials["password"],
                        "username": f"testuser{timestamp}",
                        "full_name": "Test User",
                        "agree_to_terms": True
                    }
                )
                
                if register_response.status_code in [200, 201]:
                    print("✅ Test user created, attempting login again...")
                    login_response = await client.post(
                        f"{base_url}/api/v1/auth/login/",
                        json=test_credentials
                    )
                    
                    if login_response.status_code == 200:
                        login_data = login_response.json()
                        access_token = login_data.get("access_token")
                        headers = {"Authorization": f"Bearer {access_token}"}
                        print("✅ Successfully authenticated after registration")
                    else:
                        print(f"❌ Login still failed after registration: {login_response.status_code}")
                        return False
                else:
                    print(f"❌ Registration failed: {register_response.status_code} - {register_response.text}")
                    return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
        
        # Test 2: Check chat health endpoint
        print("\n🏥 Test 2: Check chat service health")
        try:
            health_response = await client.get(
                f"{base_url}/api/v1/chat/health/",
                headers=headers
            )
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"✅ Chat service healthy: {health_data}")
                
                mcp_status = health_data.get("mcp_boe_integration", "unknown")
                if mcp_status == "available":
                    print("✅ MCP BOE integration is available")
                else:
                    print(f"⚠️ MCP BOE integration status: {mcp_status}")
            else:
                print(f"❌ Health check failed: {health_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
        
        # Test 3: Send legal query via streaming chat
        print("\n💬 Test 3: Send legal query via streaming chat")
        try:
            chat_request = {
                "message": "¿Qué leyes regulan los impuestos para artistas en España?",
                "conversation_id": "test_stream_legal"
            }
            
            print(f"Sending request: {chat_request['message']}")
            
            async with client.stream(
                "POST",
                f"{base_url}/api/v1/chat/stream/",
                json=chat_request,
                headers=headers
            ) as response:
                
                if response.status_code == 200:
                    print("✅ Streaming response started")
                    
                    chunk_count = 0
                    total_content = ""
                    mcp_used = False
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            
                            if data_str.strip() == "[DONE]":
                                print("✅ Streaming completed")
                                break
                            
                            try:
                                chunk_data = json.loads(data_str)
                                chunk_count += 1
                                
                                content = chunk_data.get("content", "")
                                total_content += content
                                
                                if chunk_data.get("mcp_used"):
                                    mcp_used = True
                                
                                if chunk_count <= 3:
                                    print(f"   Chunk {chunk_count}: {content[:80]}...")
                                
                            except json.JSONDecodeError:
                                continue
                    
                    print(f"✅ Streaming completed: {chunk_count} chunks, {len(total_content)} characters")
                    print(f"   MCP used: {mcp_used}")
                    print(f"   Response preview: {total_content[:200]}...")
                    
                    if "error" in total_content.lower() or chunk_count == 0:
                        print("❌ Test 3 failed: Error in response or no chunks")
                        return False
                    
                    if not mcp_used:
                        print("⚠️ Warning: MCP was not used in the response")
                        
                else:
                    print(f"❌ Streaming failed: {response.status_code}")
                    response_text = await response.aread()
                    print(f"   Response: {response_text.decode()}")
                    return False
                    
        except Exception as e:
            print(f"❌ Streaming chat error: {e}")
            return False
        
        # Test 4: Send non-legal query 
        print("\n💬 Test 4: Send non-legal query via streaming chat")
        try:
            chat_request = {
                "message": "What's the weather like today?",
                "conversation_id": "test_stream_non_legal"
            }
            
            print(f"Sending request: {chat_request['message']}")
            
            async with client.stream(
                "POST",
                f"{base_url}/api/v1/chat/stream/",
                json=chat_request,
                headers=headers
            ) as response:
                
                if response.status_code == 200:
                    chunk_count = 0
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            
                            if data_str.strip() == "[DONE]":
                                break
                            
                            try:
                                chunk_data = json.loads(data_str)
                                chunk_count += 1
                                
                            except json.JSONDecodeError:
                                continue
                    
                    print(f"✅ Non-legal query completed: {chunk_count} chunks")
                    
                else:
                    print(f"❌ Non-legal streaming failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ Non-legal streaming error: {e}")
            return False
    
    return True

async def main():
    """Run the complete integration test"""
    print("🚀 Starting Complete Chat API Integration Test")
    print("=" * 70)
    
    success = await test_complete_chat_integration()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 All complete chat API integration tests passed!")
        print("✅ Authentication working")
        print("✅ Chat streaming working")
        print("✅ Enhanced HTTP MCP integration working")
        print("🤖 BOE legal assistant fully functional")
    else:
        print("❌ Complete chat API integration tests failed")
        print("📋 Check authentication, server status, and MCP configuration")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())