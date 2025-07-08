#!/usr/bin/env python3
"""
Test MCP results and log them separately to understand what's being returned
"""

import asyncio
import json
import os
from datetime import datetime
import logging
from app.services.mcp_agent_service import mcp_agent_service
from app.schemas.chat import ChatRequest

# Setup separate logger for MCP results
mcp_logger = logging.getLogger('mcp_results')
mcp_logger.setLevel(logging.DEBUG)

# Create file handler for MCP results
fh = logging.FileHandler(f'mcp_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
fh.setLevel(logging.DEBUG)

# Create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# Add handlers to logger
mcp_logger.addHandler(fh)
mcp_logger.addHandler(ch)

async def test_mcp_direct_results():
    """Test MCP agent directly and log all results"""
    print("🔍 Testing MCP Agent Direct Results")
    print("=" * 60)
    
    # Check if service is available
    if not mcp_agent_service.is_available():
        print("❌ MCP service not available")
        return
    
    print("✅ MCP service available")
    
    # Test queries
    test_queries = [
        "¿Cuáles son las obligaciones fiscales para artistas freelance?",
        "¿Qué normativa BOE regula el IVA para profesionales culturales?",
        "Deducciones fiscales para artistas según el BOE"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📋 Test {i}/{len(test_queries)}: {query}")
        print("-" * 60)
        
        try:
            # Log the query
            mcp_logger.info(f"QUERY {i}: {query}")
            
            # Get the BOE query format
            boe_query = mcp_agent_service._format_boe_query(query)
            mcp_logger.debug(f"FORMATTED QUERY {i}: {boe_query}")
            
            # Run the MCP agent directly
            print("🔄 Running MCP agent...")
            start_time = datetime.now()
            
            # Call the agent run method directly
            result = await mcp_agent_service._agent.run(boe_query)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Log the complete result
            mcp_logger.info(f"RESULT {i} - Duration: {duration:.2f}s")
            mcp_logger.info(f"RESULT {i} - Type: {type(result)}")
            mcp_logger.info(f"RESULT {i} - Length: {len(str(result))}")
            mcp_logger.info(f"RESULT {i} - Content:\n{result}")
            
            # Print summary to console
            print(f"✅ MCP Result received in {duration:.2f}s")
            print(f"📊 Result type: {type(result)}")
            print(f"📏 Result length: {len(str(result))} characters")
            
            # Show preview
            result_str = str(result)
            if len(result_str) > 500:
                print(f"📄 Result preview: {result_str[:250]}...")
                print(f"    ... {result_str[-250:]}")
            else:
                print(f"📄 Full result: {result_str}")
            
            # Save individual result to file
            result_file = f"mcp_result_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(result_file, 'w', encoding='utf-8') as f:
                f.write(f"Query: {query}\n")
                f.write(f"BOE Query: {boe_query}\n")
                f.write(f"Duration: {duration:.2f}s\n")
                f.write(f"\nResult:\n{result}")
            print(f"💾 Result saved to: {result_file}")
            
        except Exception as e:
            error_msg = f"ERROR in query {i}: {type(e).__name__}: {str(e)}"
            print(f"❌ {error_msg}")
            mcp_logger.error(error_msg)
            
            import traceback
            tb = traceback.format_exc()
            mcp_logger.error(f"TRACEBACK {i}:\n{tb}")
            print(f"🔍 Check log file for full traceback")
        
        # Add delay between queries
        if i < len(test_queries):
            print("\n⏳ Waiting 2 seconds before next query...")
            await asyncio.sleep(2)
    
    print(f"\n📁 MCP results log saved to: {fh.baseFilename}")

async def test_mcp_service_flow():
    """Test the complete MCP service flow including streaming"""
    print("\n\n🔄 Testing Complete MCP Service Flow")
    print("=" * 60)
    
    request = ChatRequest(
        message="¿Cuáles son las deducciones fiscales específicas para artistas según el BOE?",
        conversation_id="test_flow_123"
    )
    
    print(f"📨 Request: {request.message}")
    
    try:
        # Track what we receive
        chunks_received = []
        total_content = ""
        
        print("🌊 Starting streaming...")
        async for chunk in mcp_agent_service.query_boe_and_summarize(request):
            chunks_received.append({
                "content": chunk.content,
                "length": len(chunk.content),
                "is_complete": chunk.is_complete,
                "conversation_id": chunk.conversation_id
            })
            total_content += chunk.content
            
            # Log each chunk
            mcp_logger.debug(f"STREAM CHUNK {len(chunks_received)}: {chunk.content[:50]}... (complete: {chunk.is_complete})")
            
            # Show progress
            if len(chunks_received) % 10 == 0:
                print(f"📦 Received {len(chunks_received)} chunks...")
        
        # Log summary
        mcp_logger.info(f"STREAMING COMPLETE - Total chunks: {len(chunks_received)}")
        mcp_logger.info(f"STREAMING COMPLETE - Total content length: {len(total_content)}")
        mcp_logger.info(f"STREAMING COMPLETE - First 500 chars: {total_content[:500]}")
        
        # Print summary
        print(f"\n✅ Streaming complete!")
        print(f"📊 Total chunks: {len(chunks_received)}")
        print(f"📏 Total content: {len(total_content)} characters")
        print(f"📄 Content preview: {total_content[:200]}...")
        
        # Save streaming result
        stream_file = f"mcp_stream_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stream_file, 'w', encoding='utf-8') as f:
            json.dump({
                "request": {
                    "message": request.message,
                    "conversation_id": request.conversation_id
                },
                "chunks": chunks_received,
                "total_content": total_content,
                "total_chunks": len(chunks_received),
                "total_length": len(total_content)
            }, f, indent=2, ensure_ascii=False)
        print(f"💾 Streaming result saved to: {stream_file}")
        
    except Exception as e:
        error_msg = f"STREAMING ERROR: {type(e).__name__}: {str(e)}"
        print(f"❌ {error_msg}")
        mcp_logger.error(error_msg)
        
        import traceback
        tb = traceback.format_exc()
        mcp_logger.error(f"STREAMING TRACEBACK:\n{tb}")

async def main():
    """Run all MCP tests"""
    print("🚀 MCP Results Logger Test")
    print("=" * 60)
    
    # Test direct MCP results
    await test_mcp_direct_results()
    
    # Test streaming flow
    await test_mcp_service_flow()
    
    print("\n✅ All tests complete!")
    print(f"📁 Check log files for detailed results")

if __name__ == "__main__":
    asyncio.run(main())