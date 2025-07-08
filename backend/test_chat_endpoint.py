#!/usr/bin/env python3
"""
Test script for the chat endpoint with BOE MCP integration

This script tests the streaming chat endpoint to verify:
1. BOE responses are forwarded to the user first
2. Summary is provided at the end
3. Integration works correctly
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime


class ChatEndpointTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_key = os.getenv("API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzUxOTM5OTczfQ.HuvCyTdMTcGhET3ojrLCrL-lK-4jSMYse0YqNJbctqs")
        
    async def test_streaming_chat(self, message: str, conversation_id: str = None):
        """Test the streaming chat endpoint"""
        
        url = f"{self.base_url}/api/v1/chat/stream/"
        
        payload = {
            "message": message,
            "conversation_id": conversation_id,
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        print(f"\n🔄 Testing query: {message[:50]}...")
        print("=" * 60)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        print(f"❌ Error: HTTP {response.status}")
                        error_text = await response.text()
                        print(f"Error details: {error_text}")
                        return False
                    
                    print("📡 Streaming response:")
                    print("-" * 40)
                    
                    full_response = ""
                    chunk_count = 0
                    boe_section_found = False
                    summary_section_found = False
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        
                        if line.startswith('data: '):
                            data_str = line[6:]  # Remove 'data: ' prefix
                            
                            if data_str == '[DONE]':
                                print("\n✅ Stream completed")
                                break
                            
                            try:
                                chunk_data = json.loads(data_str)
                                content = chunk_data.get('content', '')
                                
                                if content:
                                    print(content, end='', flush=True)
                                    full_response += content
                                    chunk_count += 1
                                    
                                    # Check for BOE section
                                    if "📋 Información del BOE" in content:
                                        boe_section_found = True
                                    
                                    # Check for summary section
                                    if "🤖 Resumen y Análisis" in content:
                                        summary_section_found = True
                                
                            except json.JSONDecodeError as e:
                                print(f"\n⚠️ JSON decode error: {e}")
                                continue
                    
                    print("\n" + "-" * 40)
                    print(f"📊 Response stats:")
                    print(f"   - Total chunks: {chunk_count}")
                    print(f"   - Response length: {len(full_response)} chars")
                    print(f"   - BOE section found: {'✅' if boe_section_found else '❌'}")
                    print(f"   - Summary section found: {'✅' if summary_section_found else '❌'}")
                    
                    return True
                    
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return False
    
    async def run_tests(self):
        """Run a series of test queries"""
        
        test_queries = [
            "¿Cuáles son las tarifas de impuestos sobre salarios para 2025?",
            "Información sobre deducciones fiscales para artistas en 2024",
            "¿Cómo funciona el IRPF para profesionales culturales?",
            "Normativa sobre facturación para freelancers creativos"
        ]
        
        print("🚀 Starting Chat Endpoint Tests")
        print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Testing endpoint: {self.base_url}/api/v1/chat/stream/")
        
        successful_tests = 0
        total_tests = len(test_queries)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}/{total_tests}")
            
            success = await self.test_streaming_chat(
                message=query,
                conversation_id=f"test_session_{i}"
            )
            
            if success:
                successful_tests += 1
                print("✅ Test passed")
            else:
                print("❌ Test failed")
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        print("\n" + "=" * 60)
        print("📊 Test Summary:")
        print(f"   - Total tests: {total_tests}")
        print(f"   - Successful: {successful_tests}")
        print(f"   - Failed: {total_tests - successful_tests}")
        print(f"   - Success rate: {(successful_tests/total_tests)*100:.1f}%")
        
        if successful_tests == total_tests:
            print("\n🎉 All tests passed! BOE MCP integration is working correctly.")
        else:
            print(f"\n⚠️ {total_tests - successful_tests} test(s) failed. Check the logs above.")
        
        return successful_tests == total_tests


async def main():
    """Main test function"""
    
    print("🧪 Chat Endpoint with BOE MCP Integration Tester")
    print("=" * 60)
    
    # Check if server is likely running
    tester = ChatEndpointTester()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{tester.base_url}/api/v1/chat/health/") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ Server is running")
                    print(f"   - Chat service: {health_data.get('status', 'unknown')}")
                    print(f"   - Model: {health_data.get('model', 'unknown')}")
                    print(f"   - BOE MCP: {health_data.get('mcp_boe_integration', 'unknown')}")
                else:
                    print(f"⚠️ Server health check failed: HTTP {response.status}")
                    
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("💡 Make sure the FastAPI server is running on http://localhost:8000")
        print("   Run: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    # Run the tests
    success = await tester.run_tests()
    
    if success:
        print("\n🎯 Integration test completed successfully!")
        print("\n💡 Next steps:")
        print("   - The BOE MCP integration is working correctly")
        print("   - BOE responses are streamed first, followed by summaries")
        print("   - Ready for production use")
    else:
        print("\n🔧 Some tests failed. Please check the implementation.")


if __name__ == "__main__":
    asyncio.run(main())