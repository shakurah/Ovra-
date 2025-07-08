#!/usr/bin/env python3
"""
Direct test of MCP client without the chat endpoint
"""

import asyncio
import os
import sys
from mcp_use import MCPClient
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent
from dotenv import load_dotenv

load_dotenv()

async def test_mcp_direct():
    """Test MCP client directly"""
    print("🔍 Testing MCP client directly...")
    
    try:
        # Initialize MCP client
        config_path = "/home/ali/development/ovra_ai/backend/boe_mcp_config.json"
        print(f"📄 Loading config from: {config_path}")
        
        client = MCPClient.from_config_file(config_path)
        print("✅ MCP Client initialized")
        
        # Test connection
        print("🔗 Testing connection...")
        
        # Create LLM
        llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.3,
            max_tokens=500
        )
        print("✅ LLM initialized")
        
        # Create agent
        agent = MCPAgent(
            llm=llm,
            client=client,
            max_steps=3
        )
        print("✅ MCP Agent initialized")
        
        # Test query
        query = "Search for information about Spanish tax law for freelancers"
        print(f"🔍 Testing query: {query}")
        
        response = await agent.run(query)
        print(f"✅ Response received: {len(response)} characters")
        print(f"📝 Response preview: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_mcp_direct())
    if result:
        print("\n✅ MCP test successful")
    else:
        print("\n❌ MCP test failed")