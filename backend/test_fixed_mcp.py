#!/usr/bin/env python3
"""
Test the fixed MCP server
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

load_dotenv()

async def test_fixed_mcp_server():
    """Test the fixed MCP server with actual tool execution"""
    print("🧪 Testing Fixed MCP Server")
    print("=" * 50)
    
    try:
        from langchain_openai import ChatOpenAI
        from mcp_use.client import MCPClient
        from mcp_use.adapters.langchain_adapter import LangChainAdapter
        from langchain.agents import AgentExecutor, create_tool_calling_agent
        from langchain_core.prompts import ChatPromptTemplate
        
        print("✅ Imports successful")
        
        # Initialize MCP client with fixed server
        config_path = "/home/ali/development/ovra_ai/backend/boe_mcp_config.json"
        client = MCPClient.from_config_file(config_path)
        print("✅ MCP Client created")
        
        # Create LLM
        llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.3
        )
        print("✅ LLM created")
        
        # Create adapter and tools
        adapter = LangChainAdapter()
        tools = await adapter.create_tools(client)
        print(f"✅ Created {len(tools)} tools")
        
        # Create a simple agent
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that can query the Spanish BOE (Official State Gazette) using the available tools."),
            ("user", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        
        print("✅ Agent created")
        
        # Test 1: Simple auxiliary table query
        print("\n🧪 Test 1: Get auxiliary table 'materias'")
        result1 = await agent_executor.ainvoke({
            "input": "Use the get_auxiliary_table tool to retrieve the 'materias' table from BOE"
        })
        print(f"✅ Test 1 result: {result1['output'][:200]}...")
        
        # Test 2: Search laws
        print("\n🧪 Test 2: Search for laws about 'impuestos'")
        result2 = await agent_executor.ainvoke({
            "input": "Search for laws related to 'impuestos' (taxes) using search_laws_list with limit 3"
        })
        print(f"✅ Test 2 result: {result2['output'][:200]}...")
        
        # Test 3: BOE summary
        print("\n🧪 Test 3: Get BOE summary for recent date")
        result3 = await agent_executor.ainvoke({
            "input": "Get the BOE summary for date 20241201 using get_boe_summary"
        })
        print(f"✅ Test 3 result: {result3['output'][:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing fixed MCP server: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Run the test"""
    print("🚀 Starting Fixed MCP Server Test")
    print("=" * 60)
    
    success = await test_fixed_mcp_server()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Fixed MCP server test completed successfully!")
    else:
        print("❌ Fixed MCP server test failed.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())