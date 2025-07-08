#!/usr/bin/env python3
"""
Test script to verify BOE MCP parameter fix
"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient

load_dotenv()

async def test_boe_fix():
    """Test if the BOE MCP fix works"""
    
    print("🧪 Testing BOE MCP Fix")
    print("=" * 50)
    
    # Configuration
    config = {
        "mcpServers": {
            "boe_mcp": {
                "command": "/home/ali/development/ovra_ai/backend/venv/bin/python",
                "args": [
                    "/home/ali/development/ovra_ai/backend/venv/lib/python3.12/site-packages/boe_mcp/server.py"
                ]
            }
        }
    }
    
    try:
        print("🔧 Initializing MCP client...")
        client = MCPClient.from_dict(config)
        
        print("🤖 Initializing LLM...")
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.1
        )
        
        print("🚀 Creating MCP Agent...")
        agent = MCPAgent(
            llm=llm, 
            client=client, 
            max_steps=5
        )
        
        # Test queries
        test_queries = [
            "Buscar normativa sobre facturación para profesionales culturales",
            "Consultar legislación sobre autónomos 2024",
            "Buscar leyes sobre derechos de autor vigentes"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: {query}")
            print("-" * 50)
            
            try:
                result = await agent.run(query)
                
                # Check if result contains error
                if "Invalid request parameters" in str(result):
                    print(f"❌ FAILED: Still getting parameter error")
                    print(f"Result: {result[:200]}...")
                elif "Error executing MCP tool" in str(result):
                    print(f"❌ FAILED: MCP tool execution error")
                    print(f"Result: {result[:200]}...")
                else:
                    print(f"✅ SUCCESS: Query executed without parameter errors")
                    print(f"Result preview: {result[:300]}...")
                    
            except Exception as e:
                print(f"❌ Exception: {str(e)}")
        
        # Close the client
        await client.close()
        print("\n✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_boe_fix())