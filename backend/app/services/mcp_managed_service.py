import asyncio
import os
import subprocess
import time
from typing import AsyncGenerator, Optional, Dict, Any
from datetime import datetime
import logging
from pathlib import Path

from langchain_openai import ChatOpenAI
from mcp_use.client import MCPClient
from mcp_use.adapters.langchain_adapter import LangChainAdapter
from dotenv import load_dotenv

from app.schemas.chat import ChatRequest, StreamChunk

logger = logging.getLogger(__name__)
load_dotenv()

class MCPManagedService:
    """MCP service with managed server process"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent.parent.parent  # backend directory
        self.config_path = self.script_dir / "boe_mcp_config.json"
        self.server_manager_path = self.script_dir / "start_mcp_server.py"
        self.venv_python = self.script_dir / "venv" / "bin" / "python"
        
        self._client = None
        self._llm_with_tools = None
        self._tools = None
        self._server_process = None
        self._is_initialized = False
        
        # Initialize service
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize MCP service"""
        try:
            logger.info("Initializing MCP Managed Service")
            self._is_initialized = False
        except Exception as e:
            logger.error(f"Failed to initialize MCP Managed Service: {e}")
    
    async def _start_mcp_server(self):
        """Start MCP server as separate process"""
        if self._server_process and self._server_process.poll() is None:
            logger.info("MCP server already running")
            return True
        
        try:
            python_exe = str(self.venv_python) if self.venv_python.exists() else "python"
            
            logger.info(f"Starting MCP server: {python_exe} {self.server_manager_path}")
            
            self._server_process = await asyncio.create_subprocess_exec(
                python_exe, str(self.server_manager_path), "start",
                cwd=str(self.script_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for process to complete the start command
            stdout, stderr = await self._server_process.communicate()
            
            if self._server_process.returncode == 0:
                logger.info("✅ MCP server started successfully")
                return True
            else:
                logger.error(f"❌ MCP server failed to start: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            return False
    
    async def _stop_mcp_server(self):
        """Stop MCP server"""
        try:
            python_exe = str(self.venv_python) if self.venv_python.exists() else "python"
            
            process = await asyncio.create_subprocess_exec(
                python_exe, str(self.server_manager_path), "stop",
                cwd=str(self.script_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            logger.info("MCP server stop command sent")
            
        except Exception as e:
            logger.error(f"Error stopping MCP server: {e}")
    
    async def _ensure_initialized(self):
        """Ensure async components are initialized"""
        if self._is_initialized:
            return True
        
        try:
            # Start MCP server first
            server_started = await self._start_mcp_server()
            if not server_started:
                logger.error("Failed to start MCP server")
                return False
            
            # Wait a moment for server to be ready
            await asyncio.sleep(3)
            
            # Initialize MCP client
            self._client = MCPClient.from_config_file(str(self.config_path))
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
            logger.info("MCP Managed Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to async initialize MCP Managed Service: {e}")
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
    
    async def query_boe_managed(
        self, 
        request: ChatRequest
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Query BOE using managed MCP server and stream the response
        """
        
        # Ensure service is initialized
        initialized = await self._ensure_initialized()
        
        if not initialized or not self._llm_with_tools:
            raise Exception("MCP Managed Service not available - initialization failed")
        
        try:
            # Check if this needs legal information
            needs_legal_info = self._is_legal_query(request.message)
            
            if needs_legal_info:
                # Format prompt for BOE search
                formatted_prompt = self._format_boe_prompt(request.message)
                
                logger.info(f"Querying BOE with managed server for: {request.message[:100]}...")
                
                # Use ainvoke to get response with tool calls
                response = await self._llm_with_tools.ainvoke(formatted_prompt)
                
                logger.info(f"Received response from managed MCP service")
                
                # Stream the response content
                content = response.content if response.content else "Procesando consulta legal con servidor gestionado..."
                
                # Check if tools were called
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    logger.info(f"Tools were called: {len(response.tool_calls)} calls")
                    # Add status message about tool usage
                    content = f"🔧 **BOE Tools Ejecutadas**: {len(response.tool_calls)} consultas realizadas\n\n{content}"
                
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
                        conversation_id=request.conversation_id or "boe_managed",
                        is_complete=i + chunk_size >= len(words)
                    )
                    
                    # Small delay to simulate streaming
                    await asyncio.sleep(0.1)
            
            else:
                # Non-legal query
                yield StreamChunk(
                    content="**ℹ️ Información del Servicio Gestionado**\n\n" +
                           "Este es un servicio especializado en **consultas legales y fiscales españolas** con servidor MCP gestionado.\n\n" +
                           "**Su consulta no parece ser de naturaleza legal/fiscal.** Este servicio está diseñado para:\n\n" +
                           "• 📋 Consultas sobre normativa fiscal\n" +
                           "• 🏛️ Legislación española\n" +
                           "• 📊 Impuestos y tributación\n" +
                           "• 📝 Regulaciones oficiales\n" +
                           "• 🏢 Derecho mercantil y societario\n\n" +
                           "**Para consultas generales**, por favor utilice un servicio de chat general.",
                    conversation_id=request.conversation_id or "general",
                    is_complete=True
                )
        
        except Exception as e:
            logger.error(f"MCP Managed Service error: {e}")
            yield StreamChunk(
                content="**❌ Error del Sistema Gestionado**\n\n" +
                       "No se pudo procesar la consulta con el servicio legal especializado gestionado.\n\n" +
                       "**Error técnico**: Sistema temporalmente no disponible\n\n" +
                       "**Recomendaciones:**\n" +
                       "• Inténtelo nuevamente en unos minutos\n" +
                       "• El servidor MCP se reiniciará automáticamente\n" +
                       "• Para consultas urgentes, consulte directamente boe.es",
                conversation_id=request.conversation_id or "error",
                is_complete=True
            )
    
    def is_available(self) -> bool:
        """Check if MCP service is available"""
        return self._is_initialized and self._llm_with_tools is not None
    
    async def reinitialize(self):
        """Reinitialize the service"""
        logger.info("Reinitializing MCP Managed Service...")
        self._is_initialized = False
        await self._stop_mcp_server()
        await asyncio.sleep(2)
        await self._ensure_initialized()

# Create service instance
mcp_managed_service = MCPManagedService()