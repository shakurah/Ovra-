#!/usr/bin/env python3
"""
Test reinitializing MCP service and then testing chat
"""

import asyncio
from app.services.mcp_agent_service import mcp_agent_service

async def test_reinit_and_chat():
    """Reinitialize MCP service and test"""
    print("🔄 Reinitializing MCP service...")
    
    # Reinitialize the service
    mcp_agent_service.reinitialize()
    
    # Check if available
    print(f"📊 MCP Service Available: {mcp_agent_service.is_available()}")
    
    if mcp_agent_service.is_available():
        print("✅ MCP service reinitialized successfully!")
        
        # Now test the chat endpoint
        import httpx
        
        API_BASE_URL = "http://localhost:8000"
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzUxOTM5OTczfQ.HuvCyTdMTcGhET3ojrLCrL-lK-4jSMYse0YqNJbctqs"
        
        print("🔍 Testing chat endpoint...")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            chat_data = {
                "message": "¿Cuáles son las obligaciones fiscales específicas para artistas en España?",
                "conversation_id": f"reinit_test_{asyncio.get_event_loop().time()}"
            }
            
            async with client.stream(
                "POST",
                f"{API_BASE_URL}/api/v1/chat/stream/",
                json=chat_data,
                headers=headers
            ) as response:
                
                if response.status_code != 200:
                    print(f"❌ Error: {response.status_code}")
                    return
                
                print("📦 Receiving response chunks...")
                
                full_response = ""
                chunks = 0
                
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        for line in chunk.strip().split('\n'):
                            if line.startswith('data: '):
                                data_str = line[6:]
                                if data_str == "[DONE]":
                                    break
                                
                                try:
                                    import json
                                    chunk_data = json.loads(data_str)
                                    content = chunk_data.get("content", "")
                                    full_response += content
                                    chunks += 1
                                    
                                    if chunks <= 5:  # Show first few chunks
                                        print(f"   Chunk {chunks}: {content[:50]}...")
                                        
                                except json.JSONDecodeError:
                                    pass
                
                print(f"\n✅ Response complete: {len(full_response)} chars, {chunks} chunks")
                print(f"📝 Response preview: {full_response[:200]}...")
                
                # Check if it contains BOE data
                if "BOE" in full_response or "Boletín" in full_response:
                    print("🎯 SUCCESS: Response contains BOE legal data!")
                else:
                    print("⚠️ WARNING: Response doesn't contain BOE data")
                    
    else:
        print("❌ MCP service reinitializetion failed")

if __name__ == "__main__":
    asyncio.run(test_reinit_and_chat())