#!/usr/bin/env python3
"""
BOE MCP Integration Test Script

This script tests the integration of the BOE MCP server using the mcp-use library.
It queries Spanish tax legislation for salary tax rates 2025 and uses OpenAI to summarize the results.

Requirements:
- pip install mcp-use
- pip install langchain-openai
- pip install python-dotenv

Usage:
    python test_mcp_boe_integration.py
"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient


class BOEMCPTester:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Verify OpenAI API key
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Configuration for BOE MCP server
        self.config = {
            "mcpServers": {
                "boe_mcp": {
                    "command": "uvx",
                    "args": ["boe_mcp"]
                }
            }
        }
        
        # Initialize components
        self.client = None
        self.llm = None
        self.agent = None
        
    async def initialize(self):
        """Initialize MCP client, LLM, and agent"""
        try:
            print("🔧 Initializing BOE MCP client...")
            self.client = MCPClient.from_dict(self.config)
            
            print("🤖 Initializing OpenAI LLM...")
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=self.openai_api_key,
                temperature=0.1
            )
            
            print("🚀 Creating MCP Agent...")
            self.agent = MCPAgent(
                llm=self.llm, 
                client=self.client, 
                max_steps=30
            )
            
            print("✅ Initialization complete!\n")
            
        except Exception as e:
            print(f"❌ Initialization failed: {str(e)}")
            raise
    
    async def test_salary_tax_rates_2025(self):
        """Test querying Spanish salary tax rates for 2025"""
        print("📋 Testing BOE MCP with salary tax rates query...\n")
        
        # Define the query for Spanish tax legislation
        queries = [
            "Buscar legislación consolidada sobre tipos impositivos de IRPF para salarios en 2025",
            "Mostrar las tablas de retenciones del IRPF para trabajadores por cuenta ajena 2025",
            "Consultar normativa vigente sobre deducciones fiscales en el IRPF 2025"
        ]
        
        results = []
        
        for i, query in enumerate(queries, 1):
            print(f"🔍 Query {i}: {query}")
            print("-" * 80)
            
            try:
                # Execute query through BOE MCP
                result = await self.agent.run(query)
                
                print(f"📄 Raw BOE MCP Response {i}:")
                print(result)
                print("\n" + "=" * 80 + "\n")
                
                results.append({
                    "query": query,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                error_msg = f"Error executing query {i}: {str(e)}"
                print(f"❌ {error_msg}")
                results.append({
                    "query": query,
                    "error": error_msg,
                    "timestamp": datetime.now().isoformat()
                })
        
        return results
    
    async def test_streaming_response(self):
        """Test streaming responses from BOE MCP"""
        print("🌊 Testing streaming responses from BOE MCP...\n")
        
        query = "Consultar resumen del BOE sobre modificaciones fiscales del IRPF para 2025"
        print(f"🔍 Streaming Query: {query}")
        print("-" * 80)
        
        try:
            print("📡 Streaming response:")
            full_response = ""
            
            async for chunk in self.agent.astream(query):
                if "messages" in chunk:
                    message_content = chunk["messages"]
                    print(message_content, end="", flush=True)
                    full_response += message_content
            
            print("\n\n" + "=" * 80 + "\n")
            return full_response
            
        except Exception as e:
            error_msg = f"Error in streaming: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    async def summarize_with_openai(self, boe_responses):
        """Use OpenAI to summarize BOE MCP responses"""
        print("🧠 Generating OpenAI summary of BOE responses...\n")
        
        # Prepare content for summarization
        content_to_summarize = "\n\n".join([
            f"Query: {resp.get('query', 'N/A')}\nResponse: {resp.get('result', resp.get('error', 'No response'))}"
            for resp in boe_responses
        ])
        
        summary_prompt = f"""
        Eres un experto en legislación fiscal española. Analiza las siguientes respuestas del BOE sobre tipos impositivos y retenciones del IRPF para 2025.
        
        Proporciona un resumen estructurado que incluya:
        1. Tipos impositivos vigentes para salarios
        2. Tablas de retenciones aplicables
        3. Principales deducciones disponibles
        4. Cambios relevantes respecto a años anteriores
        5. Recomendaciones prácticas
        
        Respuestas del BOE:
        {content_to_summarize}
        
        Resumen:
        """
        
        try:
            # Use the same LLM to generate summary
            summary_response = await self.llm.ainvoke(summary_prompt)
            summary = summary_response.content
            
            print("📊 OpenAI Summary:")
            print("-" * 50)
            print(summary)
            print("\n" + "=" * 80 + "\n")
            
            return summary
            
        except Exception as e:
            error_msg = f"Error generating OpenAI summary: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    async def save_results(self, results, streaming_result, summary):
        """Save test results to a JSON file"""
        output_data = {
            "test_timestamp": datetime.now().isoformat(),
            "test_type": "BOE MCP Integration Test",
            "queries_results": results,
            "streaming_result": streaming_result,
            "openai_summary": summary,
            "configuration": self.config
        }
        
        output_file = f"boe_mcp_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Results saved to: {output_file}")
            
        except Exception as e:
            print(f"❌ Error saving results: {str(e)}")
    
    async def run_full_test(self):
        """Run the complete test suite"""
        print("🚀 Starting BOE MCP Integration Test")
        print("=" * 50)
        print(f"Timestamp: {datetime.now()}")
        print("=" * 50 + "\n")
        
        try:
            # Initialize components
            await self.initialize()
            
            # Test regular queries
            results = await self.test_salary_tax_rates_2025()
            
            # Test streaming
            streaming_result = await self.test_streaming_response()
            
            # Generate OpenAI summary
            summary = await self.summarize_with_openai(results)
            
            # Save results
            await self.save_results(results, streaming_result, summary)
            
            print("✅ BOE MCP Integration Test completed successfully!")
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            raise
        
        finally:
            # Cleanup
            if self.client:
                try:
                    await self.client.close()
                    print("🔒 MCP client closed")
                except:
                    pass


async def main():
    """Main function to run the BOE MCP test"""
    tester = BOEMCPTester()
    await tester.run_full_test()


if __name__ == "__main__":
    print("BOE MCP Integration Tester")
    print("=" * 30)
    print("Testing BOE MCP server integration with mcp-use library")
    print("Query: Spanish salary tax rates 2025\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        exit(1)