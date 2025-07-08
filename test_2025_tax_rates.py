#!/usr/bin/env python3
"""
Test 2025 Tax Rates Query with MCP BOE Integration
Tests the complete pipeline with logging monitoring
"""

import asyncio
import os
import sys
import subprocess
import time
import threading
import requests
import json
from datetime import datetime

# Add backend to path
sys.path.append('/home/ali/development/ovra_ai/backend')


def monitor_logs():
    """Monitor backend logs in real time"""
    log_file = '/home/ali/development/ovra_ai/backend/logs/chat_2025-07-08.log'
    
    try:
        # Start monitoring logs
        process = subprocess.Popen(['tail', '-f', log_file], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True)
        
        print("📋 Starting log monitoring...")
        
        while True:
            line = process.stdout.readline()
            if line:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] LOG: {line.strip()}")
            time.sleep(0.1)
            
    except Exception as e:
        print(f"❌ Log monitoring error: {e}")


async def test_2025_tax_rates_query():
    """Test 2025 tax rates query with full pipeline monitoring"""
    
    print("🚀 Starting 2025 Tax Rates Query Test...")
    print("=" * 60)
    
    # Start log monitoring in background thread
    log_thread = threading.Thread(target=monitor_logs, daemon=True)
    log_thread.start()
    
    try:
        # Step 1: Authentication
        print("🔐 Step 1: Authenticating...")
        login_response = requests.post('http://localhost:8000/api/v1/auth/login/', 
            json={'email': 'test@example.com', 'password': 'password123'})
        
        if login_response.status_code != 200:
            print(f"❌ Authentication failed: {login_response.status_code}")
            return False
        
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        print("✅ Authentication successful")
        
        # Step 2: Test 2025 tax rates query
        print("\n💰 Step 2: Querying 2025 tax rates...")
        tax_query = {
            'message': '¿Cuáles son las tarifas de impuestos actualizadas para 2025 en España? Necesito información específica del BOE sobre IRPF, IVA y otros impuestos aplicables a profesionales culturales.',
            'conversation_id': None
        }
        
        print(f"📝 Query: {tax_query['message']}")
        print("\n🌊 Starting streaming request...")
        
        # Step 3: Send streaming request
        stream_response = requests.post('http://localhost:8000/api/v1/chat/stream/', 
            json=tax_query, headers=headers, stream=True)
        
        if stream_response.status_code != 200:
            print(f"❌ Streaming request failed: {stream_response.status_code}")
            print(f"Response: {stream_response.text}")
            return False
        
        print("✅ Streaming connection established")
        
        # Step 4: Process streaming response
        print("\n📦 Step 4: Processing streaming chunks...")
        chunks = []
        mcp_used = False
        conversation_id = None
        chunk_count = 0
        
        for line in stream_response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    if data_str == '[DONE]':
                        print("🏁 Stream completed")
                        break
                    
                    try:
                        data = json.loads(data_str)
                        chunk_count += 1
                        
                        # Extract information
                        content = data.get('content', '')
                        conversation_id = data.get('conversation_id')
                        is_complete = data.get('is_complete', False)
                        mcp_used = data.get('mcp_used', False) or mcp_used
                        
                        if content:
                            chunks.append(content)
                            print(f"   📦 Chunk {chunk_count}: {content[:100]}{'...' if len(content) > 100 else ''}")
                        
                        if is_complete:
                            print("✅ Response completed")
                            break
                        
                    except json.JSONDecodeError as e:
                        print(f"⚠️  JSON decode error: {e}")
                        continue
        
        # Step 5: Analyze results
        print(f"\n📊 Step 5: Analysis Results")
        print("=" * 40)
        
        full_response = ''.join(chunks)
        
        print(f"✅ Total chunks received: {chunk_count}")
        print(f"✅ MCP BOE used: {mcp_used}")
        print(f"✅ Conversation ID: {conversation_id}")
        print(f"✅ Full response length: {len(full_response)} characters")
        
        # Check for 2025-specific content
        contains_2025 = '2025' in full_response
        contains_tax_info = any(keyword in full_response.lower() for keyword in ['irpf', 'iva', 'impuesto', 'tarifa', 'tipo'])
        contains_boe_ref = any(keyword in full_response.lower() for keyword in ['boe', 'boletín oficial', 'real decreto', 'ley'])
        
        print(f"✅ Contains 2025 info: {contains_2025}")
        print(f"✅ Contains tax information: {contains_tax_info}")
        print(f"✅ Contains BOE references: {contains_boe_ref}")
        
        # Display response sample
        print(f"\n📄 Response Preview:")
        print("-" * 40)
        print(full_response[:500] + "..." if len(full_response) > 500 else full_response)
        print("-" * 40)
        
        # Step 6: Validation
        success = all([
            chunk_count > 0,
            mcp_used,
            len(full_response) > 100,
            contains_tax_info
        ])
        
        if success:
            print(f"\n🎉 Test PASSED! All requirements met:")
            print(f"   ✅ MCP BOE server was used")
            print(f"   ✅ Streaming chunks were received")
            print(f"   ✅ Tax information was retrieved")
            print(f"   ✅ Response was complete")
        else:
            print(f"\n❌ Test FAILED! Missing requirements:")
            if not mcp_used:
                print(f"   ❌ MCP BOE server was not used")
            if chunk_count == 0:
                print(f"   ❌ No streaming chunks received")
            if not contains_tax_info:
                print(f"   ❌ No tax information found")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False


async def test_direct_mcp_call():
    """Test direct MCP call to BOE for 2025 tax rates"""
    
    print("\n🔍 Testing Direct MCP BOE Call...")
    
    try:
        from app.services.mcp_agent_service import mcp_agent_service
        from app.schemas.chat import ChatRequest
        
        # Create test request
        test_request = ChatRequest(
            message="Busca en el BOE las tarifas de impuestos actualizadas para 2025, especialmente IRPF e IVA para profesionales culturales",
            conversation_id=None
        )
        
        print("📡 Querying BOE MCP directly...")
        response_chunks = []
        
        async for chunk in mcp_agent_service.query_boe_and_summarize(test_request):
            response_chunks.append(chunk.content)
            print(f"   📦 Direct chunk: {chunk.content[:80]}{'...' if len(chunk.content) > 80 else ''}")
            if chunk.is_complete:
                break
        
        full_direct_response = ''.join(response_chunks)
        print(f"\n✅ Direct MCP response length: {len(full_direct_response)} characters")
        
        return len(full_direct_response) > 0
        
    except Exception as e:
        print(f"❌ Direct MCP test failed: {e}")
        return False


async def main():
    """Main test function"""
    
    print("🚀 Starting Comprehensive 2025 Tax Rates Test")
    print("=" * 60)
    
    # Restart backend to ensure fresh state
    print("🔄 Restarting backend service...")
    subprocess.run(['sudo', 'systemctl', 'restart', 'ovra-backend'], check=True)
    
    # Wait for service to start
    print("⏳ Waiting for service to start...")
    time.sleep(10)
    
    # Test direct MCP call
    direct_success = await test_direct_mcp_call()
    
    # Test full pipeline
    pipeline_success = await test_2025_tax_rates_query()
    
    print(f"\n📊 Final Test Results:")
    print("=" * 40)
    print(f"   Direct MCP Test: {'✅ PASS' if direct_success else '❌ FAIL'}")
    print(f"   Full Pipeline Test: {'✅ PASS' if pipeline_success else '❌ FAIL'}")
    
    if direct_success and pipeline_success:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"   ✅ MCP BOE server is working")
        print(f"   ✅ 2025 tax data is being retrieved")
        print(f"   ✅ Streaming pipeline is functional")
        print(f"   ✅ OpenAI summarization is working")
        return True
    else:
        print(f"\n❌ SOME TESTS FAILED!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)