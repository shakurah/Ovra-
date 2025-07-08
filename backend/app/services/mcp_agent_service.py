import asyncio
import os
from typing import AsyncGenerator, List, Optional, Dict, Any
from datetime import datetime
import logging

from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient
from dotenv import load_dotenv

from app.schemas.chat import ChatRequest, StreamChunk


logger = logging.getLogger(__name__)
load_dotenv()


class MCPAgentService:
    """Service for handling MCP agent interactions with BOE API"""
    
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), '../../boe_mcp_config.json')
        self._client = None
        self._agent = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize MCP client and agent"""
        try:
            logger.info(f"Initializing MCP Agent with config: {self.config_path}")
            
            # Read config file to create dictionary
            import json
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Create MCPClient from configuration dictionary (following your example)
            self._client = MCPClient.from_dict(config)
            logger.info("MCP Client created successfully")
            
            # Create LLM for agent (using same config as chat service)
            llm = ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                api_key=os.getenv("OPENAI_API_KEY"),
                temperature=0.3,  # Lower temperature for more consistent legal responses
                max_tokens=2000
            )
            logger.info("LLM created successfully")
            
            # Create agent with the client (following your example)
            self._agent = MCPAgent(
                llm=llm, 
                client=self._client, 
                max_steps=8  # Limit steps for efficiency as requested
            )
            
            logger.info("MCP Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP Agent: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self._client = None
            self._agent = None
    
    def reinitialize(self):
        """Reinitialize the MCP agent with updated configuration"""
        logger.info("Reinitializing MCP Agent...")
        self._initialize_agent()
    
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
    
    def _format_boe_query(self, user_message: str) -> str:
        """Format user query for BOE MCP server"""
        return f"""
        Busca información legal actualizada sobre: {user_message}
        
        Prioriza:
        1. Legislación específica para profesionales culturales
        2. Normativa fiscal y tributaria relevante
        3. Referencias BOE recientes
        4. Disposiciones sobre derechos de autor si aplica
        
        Proporciona las referencias BOE completas y fechas de publicación.
        """
    
    def _format_summarization_prompt(self, boe_data: str, original_query: str) -> str:
        """Format prompt for OpenAI summarization"""
        return f"""
        Analiza y resume la siguiente información del BOE que ya se ha mostrado al usuario:

        {boe_data}

        Consulta original del usuario: "{original_query}"

        INSTRUCCIONES PARA EL RESUMEN:
        - Proporciona un análisis conciso y claro de la información del BOE
        - Destaca los puntos más relevantes para la consulta del usuario
        - Incluye referencias específicas (números de BOE, fechas, artículos)
        - Enfócate en aspectos prácticos y aplicables
        - Si es relevante para profesionales culturales, destácalo
        - Usa formato markdown con headers y listas para claridad
        - Concluye con recomendaciones prácticas si es apropiado
        - Mantén el resumen entre 200-400 palabras
        
        El usuario ya ha visto la información completa del BOE, ahora necesita un análisis resumido y práctico.
        """
    
    async def query_boe_and_summarize(
        self, 
        request: ChatRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Query BOE MCP server completely, then summarize with OpenAI and stream
        
        Flow:
        1. Check if query needs legal information
        2. Query BOE MCP server completely (no streaming)
        3. Send complete BOE data to OpenAI for analysis
        4. Stream only the OpenAI analysis to user
        """
        
        if not self._agent:
            # MCP agent not available - raise exception
            raise Exception("MCP agent not available - service initialization failed")
        
        try:
            # Check if this needs legal information
            needs_legal_info = self._is_legal_query(request.message)
            
            if needs_legal_info:
                # Format query for BOE
                boe_query = self._format_boe_query(request.message)
                
                logger.info(f"Querying BOE MCP for: {request.message[:100]}...")
                
                # Query BOE MCP server
                try:
                    logger.info(f"🔍 [MCP->BOE] Starting MCP agent query: {boe_query[:100]}...")
                    logger.info(f"📤 [MCP->BOE] Sending query to BOE MCP server...")
                    
                    # Use simple run method to get complete BOE result (following your example)
                    boe_result = await self._agent.run(boe_query)
                    
                    logger.info(f"📥 [BOE->MCP] Received BOE result - length: {len(boe_result)} characters")
                    logger.info(f"✅ [BOE->MCP] BOE result preview: {boe_result[:200]}..." if boe_result else "❌ [BOE->MCP] No result received")
                    
                    # Send MCP status as first chunk to inform user
                    if boe_result and len(boe_result.strip()) > 0:
                        status_message = f"🔍 **Consultando BOE**: Se ha encontrado información legal relevante ({len(boe_result)} caracteres)\n\n"
                        yield StreamChunk(
                            content=status_message,
                            conversation_id=request.conversation_id or "boe_query",
                            is_complete=False
                        )
                    
                    # Log full MCP result to separate file for debugging
                    mcp_result_file = f"mcp_boe_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    with open(mcp_result_file, 'w', encoding='utf-8') as f:
                        f.write(f"User Query: {request.message}\n")
                        f.write(f"BOE Query: {boe_query}\n")
                        f.write(f"Result Length: {len(boe_result)}\n")
                        f.write(f"\n--- BOE RESULT ---\n")
                        f.write(boe_result)
                    logger.info(f"💾 [MCP] Full BOE result saved to: {mcp_result_file}")
                    
                    if boe_result and len(boe_result.strip()) > 0:
                        # Create enhanced prompt that includes BOE data and user query
                        enhanced_prompt = f"""
Consulta del usuario: "{request.message}"

Información legal del BOE (Boletín Oficial del Estado):
{boe_result}

INSTRUCCIONES ESTRICTAS:
- SOLO responde basándote en la información del BOE proporcionada arriba
- NO añadas información que no esté en los datos del BOE
- Si la información del BOE no responde completamente a la pregunta, indícalo claramente
- Cita las referencias BOE específicas (números, fechas, artículos) tal como aparecen en los datos
- Usa formato markdown para organizar la información
- Si los datos del BOE no contienen información sobre algo específico que pregunta el usuario, di explícitamente que no se encontró esa información en el BOE
- NUNCA inventes o asumas información que no esté en los datos proporcionados
"""
                        
                        # Create OpenAI client for analysis
                        from openai import AsyncOpenAI
                        openai_client = AsyncOpenAI(
                            api_key=os.getenv("OPENAI_API_KEY")
                        )
                        
                        # Stream OpenAI analysis directly
                        stream = await openai_client.chat.completions.create(
                            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                            messages=[
                                {
                                    "role": "system", 
                                    "content": "Eres un asistente que SOLO resume y organiza información del BOE. NUNCA añadas información que no esté en los datos proporcionados. Si algo no está en los datos del BOE, debes decir explícitamente que no se encontró esa información. Responde SOLO en formato markdown puro. Limítate ESTRICTAMENTE a la información del BOE proporcionada."
                                },
                                {
                                    "role": "user", 
                                    "content": enhanced_prompt
                                }
                            ],
                            stream=True,
                            max_tokens=2000,
                            temperature=0.3
                        )
                        
                        content_buffer = ""
                        chunk_size = 50
                        
                        async for chunk in stream:
                            if chunk.choices[0].delta.content is not None:
                                content = chunk.choices[0].delta.content
                                content_buffer += content
                                
                                # Send chunks when buffer reaches target size
                                while len(content_buffer) >= chunk_size:
                                    # Find a good breaking point
                                    break_pos = chunk_size
                                    for i in range(min(chunk_size, len(content_buffer) - 1), max(0, chunk_size - 20), -1):
                                        if content_buffer[i] in [' ', '\n', '\t', '.', ',', ';', '!', '?']:
                                            break_pos = i + 1
                                            break
                                    
                                    chunk_content = content_buffer[:break_pos]
                                    content_buffer = content_buffer[break_pos:]
                                    
                                    if chunk_content.strip():
                                        yield StreamChunk(
                                            content=chunk_content,
                                            conversation_id=request.conversation_id or "boe_query",
                                            is_complete=False
                                        )
                        
                        # Send remaining content
                        if content_buffer.strip():
                            yield StreamChunk(
                                content=content_buffer,
                                conversation_id=request.conversation_id or "boe_query",
                                is_complete=True
                            )
                        else:
                            yield StreamChunk(
                                content="",
                                conversation_id=request.conversation_id or "boe_query",
                                is_complete=True
                            )
                    
                    else:
                        # No BOE data found or empty response - raise exception
                        logger.error(f"MCP agent returned empty response for query: {request.message[:100]}")
                        raise Exception(f"MCP agent returned empty response for legal query: {request.message[:50]}...")
                
                except Exception as boe_error:
                    logger.error(f"BOE MCP query failed with exception: {boe_error}")
                    logger.error(f"Exception type: {type(boe_error)}")
                    import traceback
                    logger.error(f"Exception traceback: {traceback.format_exc()}")
                    
                    # Re-raise the exception instead of yielding incomplete response
                    raise Exception(f"BOE MCP service failed: {str(boe_error)[:200]}")
            
            else:
                # Non-legal query - provide complete response explaining service scope
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
            logger.error(f"MCP Agent service error: {e}")
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
        return self._agent is not None and self._client is not None


# Create service instance
mcp_agent_service = MCPAgentService()