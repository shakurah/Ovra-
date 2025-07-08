#!/usr/bin/env python3
"""
Debug MCP using custom agent approach
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

# Enable debug mode
import mcp_use
mcp_use.set_debug(2)  # Full verbose output

async def debug_mcp_with_custom_agent():
    """Debug MCP using LangChain adapter"""
    print("🔍 Debugging MCP with Custom Agent")
    print("=" * 50)
    
    try:
        from langchain_openai import ChatOpenAI
        from mcp_use.client import MCPClient
        from mcp_use.adapters.langchain_adapter import LangChainAdapter
        
        print("✅ Imports successful")
        
        # Initialize MCP client
        config_path = "/home/ali/development/ovra_ai/backend/boe_mcp_config.json"
        print(f"📁 Loading config from: {config_path}")
        
        client = MCPClient.from_config_file(config_path)
        print("✅ MCP Client created")
        
        # Create LLM
        llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.3
        )
        print("✅ LLM created")
        
        # Create adapter
        adapter = LangChainAdapter()
        print("✅ Adapter created")
        
        # Get tools
        print("🔧 Creating LangChain tools...")
        tools = await adapter.create_tools(client)
        print(f"✅ Created {len(tools)} tools")
        
        # List available tools
        print("\n📋 Available tools:")
        for i, tool in enumerate(tools):
            print(f"  {i+1}. {tool.name}: {tool.description}")
        
        # Test a simple tool call
        print("\n🧪 Testing get_auxiliary_table tool...")
        llm_with_tools = llm.bind_tools(tools)
        
        # Try to call get_auxiliary_table
        result = await llm_with_tools.ainvoke(
            "Use the get_auxiliary_table tool to get the 'materias' table from BOE. "
            "Call the tool with table_name set to 'materias'."
        )
        print(f"✅ Tool call result: {result}")
        
        # Check for tool calls in the result
        if hasattr(result, 'tool_calls') and result.tool_calls:
            print(f"\n🔧 Tool calls found: {len(result.tool_calls)}")
            for i, tool_call in enumerate(result.tool_calls):
                print(f"  Tool {i+1}: {tool_call}")
        else:
            print("❌ No tool calls found in result")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in custom agent debug: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

async def debug_direct_tool_call():
    """Test direct tool calling"""
    print("\n🔧 Testing Direct Tool Calls")
    print("=" * 50)
    
    try:
        from mcp_use.client import MCPClient
        
        # Initialize client
        config_path = "/home/ali/development/ovra_ai/backend/boe_mcp_config.json"
        client = MCPClient.from_config_file(config_path)
        
        # Try to call tool directly
        print("🔧 Calling get_auxiliary_table directly...")
        
        # Get available tools first
        sessions = client.sessions
        if sessions:
            session = list(sessions.values())[0]
            print(f"✅ Using session: {session}")
            
            # List tools
            tools = await session.list_tools()
            print(f"📋 Available tools: {[tool.name for tool in tools.tools]}")
            
            # Try calling get_auxiliary_table
            result = await session.call_tool("get_auxiliary_table", {"table_name": "materias"})
            print(f"✅ Direct tool call result: {result}")
            
        else:
            print("❌ No sessions available")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in direct tool call: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Run debug tests"""
    print("🚀 Starting MCP Custom Debug")
    print("=" * 60)
    
    success = True
    
    # Test custom agent approach
    if not await debug_mcp_with_custom_agent():
        success = False
    
    # Test direct tool calls
    if not await debug_direct_tool_call():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Debug completed successfully.")
    else:
        print("❌ Debug found issues.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())