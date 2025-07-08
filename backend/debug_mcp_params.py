#!/usr/bin/env python3
"""
Debug script to test MCP parameter validation
"""
import asyncio
import json
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

async def test_mcp_server_directly():
    """Test the MCP server function directly"""
    print("🧪 Testing MCP Server Functions Directly")
    print("=" * 50)
    
    try:
        # Import the server functions directly
        from boe_mcp.server import search_laws_list, get_auxiliary_table
        
        print("\n1. Testing get_auxiliary_table with 'materias'")
        try:
            result = await get_auxiliary_table("materias")
            print(f"✅ get_auxiliary_table succeeded: {type(result)}")
            if isinstance(result, dict):
                print(f"   Keys: {list(result.keys())}")
        except Exception as e:
            print(f"❌ get_auxiliary_table failed: {e}")
        
        print("\n2. Testing search_laws_list with basic params")
        try:
            result = await search_laws_list(
                query_value="impuestos",
                offset=0,
                limit=5
            )
            print(f"✅ search_laws_list succeeded: {type(result)}")
            if isinstance(result, dict):
                print(f"   Keys: {list(result.keys())}")
        except Exception as e:
            print(f"❌ search_laws_list failed: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
        
        print("\n3. Testing search_laws_list with solo_vigente param")
        try:
            result = await search_laws_list(
                query_value="derechos de autor",
                solo_vigente=True,
                limit=5,
                offset=0
            )
            print(f"✅ search_laws_list with solo_vigente succeeded: {type(result)}")
        except Exception as e:
            print(f"❌ search_laws_list with solo_vigente failed: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            
    except ImportError as e:
        print(f"❌ Failed to import MCP server functions: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

async def test_mcp_client_call():
    """Test MCP client calls to see parameter format"""
    print("\n🔗 Testing MCP Client Parameter Format")
    print("=" * 50)
    
    try:
        from app.services.mcp_agent_service import mcp_agent_service
        
        if not mcp_agent_service.is_available():
            print("❌ MCP agent service not available")
            return False
        
        # Let's check what parameters the client is actually sending
        print("MCP Agent available, checking client parameters...")
        
        # Try to access the client directly to see available tools
        if hasattr(mcp_agent_service, '_client') and mcp_agent_service._client:
            print("✅ MCP client exists")
            
            # Check if we can see tool schemas
            try:
                # This might give us insight into expected parameters
                client = mcp_agent_service._client
                print(f"   Client type: {type(client)}")
                
                # Try to see if there are sessions
                if hasattr(client, 'sessions'):
                    print(f"   Sessions: {len(client.sessions) if client.sessions else 0}")
                
            except Exception as e:
                print(f"   Error accessing client details: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing MCP client: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Run all debug tests"""
    print("🚀 Starting MCP Parameter Debug")
    print("=" * 60)
    
    success = True
    
    # Test server functions directly
    if not await test_mcp_server_directly():
        success = False
    
    # Test client parameter format
    if not await test_mcp_client_call():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Debug completed successfully.")
    else:
        print("❌ Debug found issues.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())