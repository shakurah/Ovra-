import asyncio
import os
import logging
from typing import AsyncGenerator, Optional, Dict, Any
from datetime import datetime
import httpx

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from app.schemas.chat import ChatRequest, StreamChunk

logger = logging.getLogger(__name__)
load_dotenv()

class EnhancedHTTPMCPService:
    """Enhanced HTTP MCP Service with OpenAI integration"""
    
    def __init__(self):
        self.mcp_server_url = "http://localhost:8931"
        self.client = None
        self.llm = None
        self._is_available = False
        self._is_initialized = False
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client
    
    async def _get_llm(self) -> ChatOpenAI:
        """Get or create LLM"""
        if self.llm is None:
            self.llm = ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                api_key=os.getenv("OPENAI_API_KEY"),
                temperature=0.3,
                max_tokens=2000
            )
        return self.llm
    
    async def check_server_health(self) -> bool:
        """Check if MCP HTTP server is available"""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.mcp_server_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                self._is_available = data.get("status") == "healthy"
                self._is_initialized = True
                return self._is_available
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self._is_available = False
        
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
    
    async def search_laws(self, query_value: str) -> Dict[str, Any]:
        """Search laws using HTTP MCP server"""
        try:
            client = await self._get_client()
            
            request_data = {
                "query_value": query_value,
                "search_in_title_only": True,
                "solo_vigente": True,
                "limit": 10
            }
            
            response = await client.post(
                f"{self.mcp_server_url}/search_laws_list",
                json=request_data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Search laws failed: {response.status_code} - {response.text}")
                return {"error": f"Search failed with status {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Search laws error: {e}")
            return {"error": str(e)}
    
    async def get_auxiliary_table(self, table_name: str) -> Dict[str, Any]:
        """Get auxiliary table using HTTP MCP server"""
        try:
            client = await self._get_client()
            
            request_data = {"table_name": table_name}
            
            response = await client.post(
                f"{self.mcp_server_url}/get_auxiliary_table",
                json=request_data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Get auxiliary table failed: {response.status_code} - {response.text}")
                return {"error": f"Request failed with status {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Get auxiliary table error: {e}")
            return {"error": str(e)}
    
    def _analyze_query_and_extract_keywords(self, message: str) -> Dict[str, str]:
        """Enhanced keyword extraction for BOE queries"""
        message_lower = message.lower()
        
        # Extract potential search terms
        query_terms = []
        context_info = []
        
        # Tax-related terms
        if any(term in message_lower for term in ['impuesto', 'tax', 'fiscal', 'tributario']):
            query_terms.append("impuesto")
            context_info.append("fiscal")
        
        # Artist-related terms
        if any(term in message_lower for term in ['artista', 'artist', 'cultural']):
            query_terms.append("artista")
            context_info.append("cultural")
        
        # Law-related terms
        if any(term in message_lower for term in ['ley', 'law', 'legislación', 'normativa']):
            query_terms.append("ley")
            context_info.append("legislation")
        
        # Professional terms
        if any(term in message_lower for term in ['profesional', 'freelance', 'autónomo']):
            query_terms.append("profesional")
            context_info.append("professional")
        
        # Copyright terms
        if any(term in message_lower for term in ['derechos de autor', 'copyright', 'propiedad intelectual']):
            query_terms.append("derechos de autor")
            context_info.append("intellectual_property")
        
        return {
            "query_value": " ".join(query_terms) if query_terms else "normativa",
            "search_context": message_lower,
            "context_info": context_info
        }
    
    async def _get_enhanced_response(self, boe_data: Dict[str, Any], original_query: str) -> str:
        """Get enhanced response using OpenAI to analyze BOE data"""
        try:
            llm = await self._get_llm()
            
            # Prepare BOE data summary for LLM
            boe_summary = ""
            if "data" in boe_data and isinstance(boe_data["data"], dict):
                data = boe_data["data"]
                
                if "hits" in data and "hits" in data["hits"]:
                    hits = data["hits"]["hits"]
                    total = data["hits"]["total"]["value"] if "total" in data["hits"] else len(hits)
                    
                    boe_summary = f"Total de resultados BOE: {total}\n\n"
                    
                    if hits:
                        boe_summary += "Principales resultados:\n"
                        for i, hit in enumerate(hits[:5], 1):
                            source = hit.get("_source", {})
                            titulo = source.get("titulo", "Sin título")
                            fecha = source.get("fecha_disposicion", "")
                            identifier = source.get("identifier", "")
                            
                            boe_summary += f"{i}. {titulo}\n"
                            if fecha:
                                boe_summary += f"   Fecha: {fecha}\n"
                            if identifier:
                                boe_summary += f"   ID: {identifier}\n"
                            boe_summary += "\n"
            
            # Create prompt for LLM analysis
            analysis_prompt = f"""
Eres un asistente legal especializado en legislación española. 

CONSULTA DEL USUARIO: "{original_query}"

DATOS DEL BOE ENCONTRADOS:
{boe_summary}

INSTRUCCIONES:
1. Analiza los datos del BOE en relación a la consulta del usuario
2. Proporciona una respuesta clara y práctica
3. Explica la relevancia de las normas encontradas
4. Incluye recomendaciones específicas si es aplicable
5. Mantén un tono profesional pero accesible
6. Responde SIEMPRE en español
7. Si no hay datos suficientes, explica las limitaciones

FORMATO DE RESPUESTA:
- Comienza con un breve resumen
- Lista las normas más relevantes
- Incluye consejos prácticos
- Termina con referencias BOE específicas

Responde de forma útil para profesionales y empresas.
"""
            
            # Get LLM response
            response = await llm.ainvoke(analysis_prompt)
            
            return response.content if response.content else "No se pudo analizar la información del BOE."
            
        except Exception as e:
            logger.error(f"Enhanced response generation failed: {e}")
            return self._format_basic_boe_response(boe_data, original_query)
    
    def _format_basic_boe_response(self, boe_data: Dict[str, Any], original_query: str) -> str:
        """Format basic BOE response without LLM enhancement"""
        if "error" in boe_data:
            return f"**Error en consulta BOE**: {boe_data['error']}"
        
        response_parts = [
            "**📋 Consulta Legal - Resultados del BOE**\n",
            f"*Consulta original*: {original_query}\n"
        ]
        
        # Handle search results
        if "data" in boe_data and isinstance(boe_data["data"], dict):
            data = boe_data["data"]
            
            if "hits" in data and "hits" in data["hits"]:
                hits = data["hits"]["hits"]
                total = data["hits"]["total"]["value"] if "total" in data["hits"] else len(hits)
                
                response_parts.append(f"**Total de resultados encontrados**: {total}\n")
                
                if hits:
                    response_parts.append("**📖 Principales resultados**:\n")
                    
                    for i, hit in enumerate(hits[:3], 1):
                        source = hit.get("_source", {})
                        titulo = source.get("titulo", "Sin título")
                        identifier = source.get("identifier", "")
                        fecha = source.get("fecha_disposicion", "")
                        
                        response_parts.append(f"**{i}. {titulo}**")
                        if fecha:
                            response_parts.append(f"   - *Fecha*: {fecha}")
                        if identifier:
                            response_parts.append(f"   - *Identificador*: {identifier}")
                        response_parts.append("")
                else:
                    response_parts.append("No se encontraron resultados específicos para su consulta.")
        
        # Add footer
        response_parts.extend([
            "\n---",
            "💡 *Información proporcionada por el Boletín Oficial del Estado (BOE)*",
            "📖 *Para información detallada, consulte el texto completo en boe.es*"
        ])
        
        return "\n".join(response_parts)
    
    async def query_boe_enhanced(self, request: ChatRequest) -> AsyncGenerator[StreamChunk, None]:
        """Query BOE using HTTP MCP server with OpenAI enhancement and stream response"""
        
        # Check if server is available
        server_available = await self.check_server_health()
        
        if not server_available:
            yield StreamChunk(
                content="**❌ Servidor BOE no disponible**\n\n" +
                       "El servidor de consultas legales no está actualmente disponible.\n\n" +
                       "**Recomendaciones:**\n" +
                       "• Verifique que el servidor HTTP MCP esté ejecutándose en el puerto 8931\n" +
                       "• Inténtelo nuevamente en unos minutos\n" +
                       "• Para consultas urgentes, consulte directamente boe.es",
                conversation_id=request.conversation_id or "error",
                is_complete=True
            )
            return
        
        # Check if this needs legal information
        needs_legal_info = self._is_legal_query(request.message)
        
        if not needs_legal_info:
            yield StreamChunk(
                content="**ℹ️ Servicio Legal Especializado (Enhanced)**\n\n" +
                       "Este servicio está especializado en **consultas legales y fiscales españolas** con análisis inteligente.\n\n" +
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
            return
        
        try:
            logger.info(f"Processing enhanced legal query: {request.message[:100]}...")
            
            # Extract keywords and determine search strategy
            query_analysis = self._analyze_query_and_extract_keywords(request.message)
            
            # Perform BOE search
            search_results = await self.search_laws(query_analysis["query_value"])
            
            # Get enhanced response using OpenAI
            enhanced_response = await self._get_enhanced_response(search_results, request.message)
            
            # Add enhanced header
            final_response = f"**🤖 BOE Legal Assistant (Enhanced with AI)**\n\n{enhanced_response}\n\n---\n💡 *Respuesta generada mediante análisis inteligente de datos del BOE*\n📖 *Para información detallada, consulte los documentos originales en boe.es*"
            
            # Stream the response in chunks
            words = final_response.split()
            chunk_size = 15
            
            for i in range(0, len(words), chunk_size):
                chunk_words = words[i:i + chunk_size]
                chunk_content = " ".join(chunk_words)
                
                if i > 0:  # Add space before continuation chunks
                    chunk_content = " " + chunk_content
                
                yield StreamChunk(
                    content=chunk_content,
                    conversation_id=request.conversation_id or "boe_enhanced",
                    is_complete=i + chunk_size >= len(words)
                )
                
                # Small delay to simulate streaming
                await asyncio.sleep(0.08)
        
        except Exception as e:
            logger.error(f"Enhanced HTTP MCP Service error: {e}")
            yield StreamChunk(
                content="**❌ Error en Servicio Enhanced**\n\n" +
                       "No se pudo procesar la consulta con el servicio legal enhanced.\n\n" +
                       f"**Error técnico**: {str(e)}\n\n" +
                       "**Recomendaciones:**\n" +
                       "• Inténtelo nuevamente en unos minutos\n" +
                       "• Verifique la conexión del servidor HTTP MCP\n" +
                       "• Para consultas urgentes, consulte directamente boe.es",
                conversation_id=request.conversation_id or "error",
                is_complete=True
            )
    
    def is_available(self) -> bool:
        """Check if Enhanced HTTP MCP service is available"""
        return self._is_available and self._is_initialized
    
    async def reinitialize(self):
        """Reinitialize the service"""
        logger.info("Reinitializing Enhanced HTTP MCP Service...")
        if self.client:
            await self.client.aclose()
            self.client = None
        
        self.llm = None
        self._is_initialized = False
        
        # Check server health
        await self.check_server_health()

# Create service instance
enhanced_http_mcp_service = EnhancedHTTPMCPService()