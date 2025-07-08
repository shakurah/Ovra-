import asyncio
import os
from typing import AsyncGenerator, Optional, Dict, Any
from datetime import datetime
import logging

from langchain_openai import ChatOpenAI
from mcp_use.client import MCPClient
from mcp_use.adapters.langchain_adapter import LangChainAdapter
from dotenv import load_dotenv

from app.schemas.chat import ChatRequest, StreamChunk

logger = logging.getLogger(__name__)
load_dotenv()

class MCPDirectService:
    """Direct MCP service using LangChain adapter with persistent llm_with_tools"""
    
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), '../../boe_mcp_config.json')
        self._client = None
        self._llm_with_tools = None
        self._tools = None
        self._is_initialized = False
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize MCP client and LLM with tools"""
        try:
            logger.info(f"Initializing MCP Direct Service with config: {self.config_path}")
            
            # This will be called synchronously, but we'll handle async initialization later
            self._is_initialized = False
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP Direct Service: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _ensure_initialized(self):
        """Ensure async components are initialized"""
        if self._is_initialized:
            return
        
        try:
            # Initialize MCP client
            self._client = MCPClient.from_config_file(self.config_path)
            logger.info("MCP Client created successfully")
            
            # Create LLM
            llm = ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                api_key=os.getenv("OPENAI_API_KEY"),
                temperature=0.3,
                max_tokens=2000
            )
            logger.info("LLM created successfully")
            
            # Create adapter and get tools
            adapter = LangChainAdapter()
            self._tools = await adapter.create_tools(self._client)
            logger.info(f"Created {len(self._tools)} LangChain tools")
            
            # Create LLM with tools bound
            self._llm_with_tools = llm.bind_tools(self._tools)
            logger.info("LLM with tools bound successfully")
            
            self._is_initialized = True
            logger.info("MCP Direct Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to async initialize MCP Direct Service: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self._is_initialized = False
    
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
        """Format user query for BOE search"""
        return f"""
Eres un asistente legal especializado en la legislación española (BOE). 

Consulta del usuario: "{user_message}"

INSTRUCCIONES:
1. Si la consulta es sobre legislación española, usa las herramientas disponibles para buscar información en el BOE
2. Para búsquedas generales de leyes, usa search_laws_list con query_value apropiado
3. Para información sobre materias/ámbitos/departamentos, usa get_auxiliary_table
4. Para sumarios específicos por fecha, usa get_boe_summary o get_borme_summary
5. Proporciona información práctica y referencias específicas del BOE
6. Si no encuentras información específica, indícalo claramente
7. SIEMPRE responde en español
8. Incluye referencias BOE cuando estén disponibles

Responde de forma clara, estructurada y práctica para profesionales del derecho y empresas.
"""
    
    async def query_boe_direct(
        self, 
        request: ChatRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Query BOE using direct LLM tool calls and stream the response
        """
        
        # Ensure service is initialized
        await self._ensure_initialized()
        
        if not self._is_initialized or not self._llm_with_tools:
            raise Exception("MCP Direct Service not available - initialization failed")
        
        try:
            # Check if this needs legal information
            needs_legal_info = self._is_legal_query(request.message)
            
            if needs_legal_info:
                # Format prompt for BOE search
                formatted_prompt = self._format_boe_prompt(request.message)
                
                logger.info(f"Querying BOE with formatted prompt for: {request.message[:100]}...")
                
                # Use ainvoke to get response with tool calls
                response = await self._llm_with_tools.ainvoke(formatted_prompt)
                
                logger.info(f"Received response from LLM with tools")
                
                # Check if tools were called
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    logger.info(f"Tools were called: {len(response.tool_calls)} calls")
                    
                    # If we have tool calls, we need to execute them and get a final response
                    # For now, let's stream the content we have
                    content = response.content if response.content else "Procesando consulta legal..."
                    
                    # Stream the response in chunks
                    words = content.split() if content else ["Procesando", "consulta", "legal..."]
                    chunk_size = 10
                    
                    for i in range(0, len(words), chunk_size):
                        chunk_words = words[i:i + chunk_size]
                        chunk_content = " ".join(chunk_words)
                        
                        if i > 0:  # Add space before continuation chunks
                            chunk_content = " " + chunk_content
                        
                        yield StreamChunk(
                            content=chunk_content,
                            conversation_id=request.conversation_id or "boe_direct",
                            is_complete=i + chunk_size >= len(words)
                        )
                        
                        # Small delay to simulate streaming
                        await asyncio.sleep(0.1)
                
                else:
                    # No tools called, stream the direct response
                    content = response.content if response.content else "No se pudo procesar la consulta"
                    
                    # Stream the response
                    words = content.split()
                    chunk_size = 10
                    
                    for i in range(0, len(words), chunk_size):
                        chunk_words = words[i:i + chunk_size]
                        chunk_content = " ".join(chunk_words)
                        
                        if i > 0:
                            chunk_content = " " + chunk_content
                        
                        yield StreamChunk(
                            content=chunk_content,
                            conversation_id=request.conversation_id or "boe_direct",
                            is_complete=i + chunk_size >= len(words)
                        )
                        
                        await asyncio.sleep(0.1)
            
            else:
                # Non-legal query
                yield StreamChunk(
                    content="**ℹ️ Información del Servicio**\n\n" +
                           "Este es un servicio especializado en **consultas legales y fiscales españolas** que accede al Boletín Oficial del Estado (BOE).\n\n" +
                           "**Su consulta no parece ser de naturaleza legal/fiscal.** Este servicio está diseñado para:\n\n" +
                           "• 📋 Consultas sobre normativa fiscal\n" +
                           "• 🏛️ Legislación española\n" +
                           "• 📊 Impuestos y tributación\n" +
                           "• 📝 Regulaciones oficiales\n" +
                           "• 🏢 Derecho mercantil y societario\n\n" +
                           "**Para consultas generales**, por favor utilice un servicio de chat general o reformule su pregunta con un enfoque legal/fiscal si es aplicable.",
                    conversation_id=request.conversation_id or "general",
                    is_complete=True
                )
        
        except Exception as e:
            logger.error(f"MCP Direct Service error: {e}")
            yield StreamChunk(
                content="**❌ Error del Sistema**\n\n" +
                       "No se pudo procesar la consulta con el servicio legal especializado.\n\n" +
                       "**Error técnico**: Sistema temporalmente no disponible\n\n" +
                       "**Recomendaciones:**\n" +
                       "• Inténtelo nuevamente en unos minutos\n" +
                       "• Verifique que su consulta sea de naturaleza legal/fiscal\n" +
                       "• Para consultas urgentes, consulte directamente boe.es\n" +
                       "• Contacte con soporte técnico si el problema persiste",
                conversation_id=request.conversation_id or "error",
                is_complete=True
            )
    
    def is_available(self) -> bool:
        """Check if MCP service is available"""
        return self._is_initialized and self._llm_with_tools is not None

# Create service instance
mcp_direct_service = MCPDirectService()