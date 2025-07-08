import asyncio
import os
import logging
from typing import AsyncGenerator, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient
from dotenv import load_dotenv

from app.schemas.chat import ChatRequest, StreamChunk

logger = logging.getLogger(__name__)
load_dotenv()

class MCPAgentHTTPService:
    """MCP Agent service using HTTP transport"""
    
    def __init__(self):
        self.mcp_server_url = "http://localhost:8931/sse"
        self._agent = None
        self._client = None
        self._llm = None
        self._is_initialized = False
        
        # Initialize service
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize MCP Agent service"""
        try:
            logger.info("Initializing MCP Agent HTTP Service")
            self._is_initialized = False
        except Exception as e:
            logger.error(f"Failed to initialize MCP Agent HTTP Service: {e}")
    
    async def _ensure_initialized(self):
        """Ensure async components are initialized"""
        if self._is_initialized:
            return True
        
        try:
            logger.info("Starting MCP Agent HTTP initialization...")
            
            # Configuration for HTTP MCP server
            config = {
                "mcpServers": {
                    "boe_http": {
                        "url": self.mcp_server_url
                    }
                }
            }
            
            # Create MCPClient from config
            self._client = MCPClient.from_dict(config)
            logger.info("MCP Client created successfully")
            
            # Create LLM
            self._llm = ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                api_key=os.getenv("OPENAI_API_KEY"),
                temperature=0.3,
                max_tokens=2000
            )
            logger.info("LLM created successfully")
            
            # Create agent with the client
            self._agent = MCPAgent(
                llm=self._llm, 
                client=self._client, 
                max_steps=10
            )
            logger.info("MCP Agent created successfully")
            
            self._is_initialized = True
            logger.info("MCP Agent HTTP Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to async initialize MCP Agent HTTP Service: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self._is_initialized = False
            return False
    
    def _is_legal_query(self, message: str) -> bool:
        """Determine if query needs BOE legal information"""
        legal_keywords = [
            'ley', 'law', 'legislación', 'legislation', 'boe', 'normativa',
            'regulation', 'decreto', 'decree', 'real decreto', 'royal decree',
            'impuesto', 'tax', 'fiscal', 'tributario', 'iva', 'vat',
            'irpf', 'income tax', 'artista', 'artist', 'cultural',
            'profesional', 'freelance', 'autónomo', 'self-employed',
            'derechos de autor', 'copyright', 'propiedad intelectual',
            'intellectual property', 'facturación', 'billing', 'invoice'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in legal_keywords)
    
    def _format_boe_prompt(self, user_message: str) -> str:
        """Format user query for BOE search using MCPAgent"""
        return f"""
Eres un asistente legal especializado en la legislación española (BOE). 

Consulta del usuario: "{user_message}"

INSTRUCCIONES:
1. Usa las herramientas MCP disponibles para buscar información en el BOE
2. Para búsquedas generales de leyes, usa la herramienta search_laws_list
3. Para información sobre materias/ámbitos/departamentos, usa get_auxiliary_table
4. Para sumarios específicos por fecha, usa get_boe_summary o get_borme_summary
5. Si encuentras información relevante, proporciónala de forma clara y estructurada
6. Incluye referencias BOE específicas cuando estén disponibles
7. SIEMPRE responde en español
8. Si no encuentras información específica, indica claramente las limitaciones

Responde de forma práctica y útil para profesionales del derecho y empresas.
"""
    
    async def query_boe_agent(
        self, 
        request: ChatRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Query BOE using MCP Agent and stream the response
        """
        
        # Ensure service is initialized
        initialized = await self._ensure_initialized()
        
        if not initialized or not self._agent:
            raise Exception("MCP Agent HTTP Service not available - initialization failed")
        
        try:
            # Check if this needs legal information
            needs_legal_info = self._is_legal_query(request.message)
            
            if needs_legal_info:
                # Format prompt for BOE search
                formatted_prompt = self._format_boe_prompt(request.message)
                
                logger.info(f"Querying BOE with MCP Agent for: {request.message[:100]}...")
                
                # Use MCP Agent to process the query
                result = await self._agent.run(
                    formatted_prompt,
                    max_steps=10
                )
                
                logger.info(f"Received response from MCP Agent")
                
                # Process the result
                content = str(result) if result else "No se pudo procesar la consulta legal."
                
                # Add BOE-specific formatting
                formatted_content = f"**🏛️ BOE Legal Assistant (MCP Agent)**\n\n{content}\n\n---\n💡 *Información obtenida mediante consulta automatizada al BOE*\n📖 *Para detalles completos, consulte los documentos originales en boe.es*"
                
                # Stream the response in chunks
                words = formatted_content.split() if formatted_content else ["Procesando", "consulta", "legal..."]
                chunk_size = 12
                
                for i in range(0, len(words), chunk_size):
                    chunk_words = words[i:i + chunk_size]
                    chunk_content = " ".join(chunk_words)
                    
                    if i > 0:  # Add space before continuation chunks
                        chunk_content = " " + chunk_content
                    
                    yield StreamChunk(
                        content=chunk_content,
                        conversation_id=request.conversation_id or "boe_agent",
                        is_complete=i + chunk_size >= len(words)
                    )
                    
                    # Small delay to simulate streaming
                    await asyncio.sleep(0.08)
            
            else:
                # Non-legal query
                yield StreamChunk(
                    content="**ℹ️ Servicio Legal Especializado (MCP Agent)**\n\n" +
                           "Este es un servicio especializado en **consultas legales y fiscales españolas** mediante MCP Agent.\\n\\n" +
                           "**Su consulta no parece ser de naturaleza legal/fiscal.** Este servicio está diseñado para:\\n\\n" +
                           "• 📋 Consultas sobre normativa fiscal\\n" +
                           "• 🏛️ Legislación española\\n" +
                           "• 📊 Impuestos y tributación\\n" +
                           "• 📝 Regulaciones oficiales\\n" +
                           "• 🏢 Derecho mercantil y societario\\n\\n" +
                           "**Para consultas generales**, por favor utilice un servicio de chat general.",
                    conversation_id=request.conversation_id or "general",
                    is_complete=True
                )
        
        except Exception as e:
            logger.error(f"MCP Agent HTTP Service error: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            yield StreamChunk(
                content="**❌ Error del MCP Agent**\\n\\n" +
                       "No se pudo procesar la consulta con el servicio legal especializado.\\n\\n" +
                       f"**Error técnico**: {str(e)}\\n\\n" +
                       "**Recomendaciones:**\\n" +
                       "• Inténtelo nuevamente en unos minutos\\n" +
                       "• Verifique que el servidor MCP HTTP esté disponible\\n" +
                       "• Para consultas urgentes, consulte directamente boe.es",
                conversation_id=request.conversation_id or "error",
                is_complete=True
            )
    
    def is_available(self) -> bool:
        """Check if MCP Agent service is available"""
        return self._is_initialized and self._agent is not None
    
    async def reinitialize(self):
        """Reinitialize the service"""
        logger.info("Reinitializing MCP Agent HTTP Service...")
        self._is_initialized = False
        self._agent = None
        self._client = None
        self._llm = None
        await asyncio.sleep(1)
        await self._ensure_initialized()

# Create service instance
mcp_agent_http_service = MCPAgentHTTPService()