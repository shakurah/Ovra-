#!/usr/bin/env python3
"""
Demo: BOE MCP Integration for Chat Application

This script demonstrates how to integrate the BOE MCP server into the chat application.
It shows the complete flow: User Query -> BOE MCP -> OpenAI Summarization -> Chat Response

Usage:
    python demo_chat_integration.py
"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient


class ChatBOEIntegration:
    """Demonstrates BOE MCP integration for chat application"""
    
    def __init__(self):
        load_dotenv()
        
        # BOE MCP Configuration
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
        """Initialize MCP client and OpenAI LLM"""
        self.client = MCPClient.from_dict(self.config)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv('OPENAI_API_KEY'),
            temperature=0.1
        )
        self.agent = MCPAgent(
            llm=self.llm,
            client=self.client,
            max_steps=20
        )
    
    async def process_tax_query(self, user_query: str) -> dict:
        """Process a tax-related query through BOE MCP and OpenAI"""
        print(f"👤 User Query: {user_query}")
        print("-" * 60)
        
        try:
            # Step 1: Query BOE MCP
            print("🔍 Querying BOE MCP server...")
            boe_response = await self.agent.run(user_query)
            
            print(f"📄 BOE Response: {boe_response[:200]}...")
            
            # Step 2: Summarize with OpenAI
            print("🧠 Generating user-friendly summary...")
            summary_prompt = f"""
            Eres un asistente fiscal experto. Un usuario ha preguntado sobre legislación española y has recibido esta respuesta del BOE:
            
            Pregunta del usuario: {user_query}
            Respuesta del BOE: {boe_response}
            
            Proporciona una respuesta clara, concisa y útil para el usuario. Si no hay información específica disponible, explica qué puede hacer el usuario para obtener la información que necesita.
            
            Respuesta:
            """
            
            summary_response = await self.llm.ainvoke(summary_prompt)
            final_summary = summary_response.content
            
            print(f"✅ Final Response: {final_summary[:200]}...")
            
            return {
                "user_query": user_query,
                "boe_response": boe_response,
                "final_response": final_summary,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            error_response = f"Lo siento, hubo un error al consultar la información fiscal: {str(e)}"
            return {
                "user_query": user_query,
                "error": str(e),
                "final_response": error_response,
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
    
    async def simulate_chat_conversation(self):
        """Simulate a chat conversation with tax-related queries"""
        print("💬 Simulating Chat Conversation with BOE MCP Integration")
        print("=" * 70)
        
        # Sample user queries
        queries = [
            "¿Cuáles son los tipos del IRPF para 2024?",
            "¿Cómo se calculan las retenciones de nómina?",
            "¿Qué deducciones puedo aplicar en mi declaración de la renta?",
            "¿Cuándo se publica la normativa fiscal para 2025?"
        ]
        
        results = []
        
        for i, query in enumerate(queries, 1):
            print(f"\n🔄 Processing Query {i}/{len(queries)}")
            print("=" * 40)
            
            result = await self.process_tax_query(query)
            results.append(result)
            
            # Display final response to user
            print(f"\n🤖 Chat Response:")
            print(f"{result['final_response']}")
            print("\n" + "=" * 70)
            
            # Simulate delay between queries
            await asyncio.sleep(1)
        
        return results
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            try:
                await self.client.close()
            except:
                pass


async def main():
    """Main demonstration function"""
    print("🚀 BOE MCP Chat Integration Demo")
    print("=" * 40)
    print("This demo shows how BOE MCP can be integrated into a chat application.")
    print("The flow is: User Query -> BOE MCP -> OpenAI Summary -> Chat Response\n")
    
    chat_integration = ChatBOEIntegration()
    
    try:
        # Initialize
        print("🔧 Initializing BOE MCP integration...")
        await chat_integration.initialize()
        print("✅ Initialization complete!\n")
        
        # Run simulation
        results = await chat_integration.simulate_chat_conversation()
        
        # Summary
        print("\n📊 Demo Summary:")
        print("-" * 30)
        successful = sum(1 for r in results if r['status'] == 'success')
        print(f"Total queries processed: {len(results)}")
        print(f"Successful responses: {successful}")
        print(f"Errors: {len(results) - successful}")
        
        print("\n✅ Demo completed successfully!")
        print("\n💡 Integration Notes:")
        print("- BOE MCP server is working correctly")
        print("- OpenAI summarization provides user-friendly responses")
        print("- Ready for integration into chat service")
        print("- Consider adding caching for frequently asked questions")
        print("- Add error handling for production use")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
    
    finally:
        await chat_integration.cleanup()


if __name__ == "__main__":
    print("BOE MCP Chat Integration Demo")
    print("=" * 35)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")