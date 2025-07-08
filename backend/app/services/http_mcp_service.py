import asyncio
import json
import logging
from typing import AsyncGenerator, Optional, Dict, Any
from datetime import datetime
import httpx
from pathlib import Path

from app.schemas.chat import ChatRequest, StreamChunk

logger = logging.getLogger(__name__)

class HTTPMCPService:
    """HTTP MCP Service for BOE queries"""
    
    def __init__(self):
        self.mcp_server_url = "http://localhost:8931"
        self.client = None
        self._is_available = False
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client
    
    async def check_server_health(self) -> bool:
        """Check if MCP HTTP server is available"""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.mcp_server_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                self._is_available = data.get("status") == "healthy"
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
    
    async def get_boe_summary(self, fecha: str) -> Dict[str, Any]:
        """Get BOE summary using HTTP MCP server"""
        try:
            client = await self._get_client()
            
            request_data = {"fecha": fecha}
            
            response = await client.post(
                f"{self.mcp_server_url}/get_boe_summary",
                json=request_data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Get BOE summary failed: {response.status_code} - {response.text}")
                return {"error": f"Request failed with status {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Get BOE summary error: {e}")
            return {"error": str(e)}
    
    def _analyze_query_and_extract_keywords(self, message: str) -> Dict[str, str]:
        """Simple keyword extraction for BOE queries"""
        message_lower = message.lower()
        
        # Extract potential search terms
        query_terms = []
        
        # Tax-related terms
        if any(term in message_lower for term in ['impuesto', 'tax', 'fiscal', 'tributario']):
            query_terms.append("impuesto")
        
        # Artist-related terms
        if any(term in message_lower for term in ['artista', 'artist', 'cultural']):
            query_terms.append("artista")
        
        # Law-related terms
        if any(term in message_lower for term in ['ley', 'law', 'legislación', 'normativa']):
            query_terms.append("ley")
        
        # Professional terms
        if any(term in message_lower for term in ['profesional', 'freelance', 'autónomo']):
            query_terms.append("profesional")
        
        # Copyright terms
        if any(term in message_lower for term in ['derechos de autor', 'copyright', 'propiedad intelectual']):
            query_terms.append("derechos de autor")
        
        return {
            "query_value": " ".join(query_terms) if query_terms else "normativa",
            "search_context": message_lower
        }
    
    def _format_boe_response(self, boe_data: Dict[str, Any], original_query: str) -> str:
        """Format BOE response for user display"""
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
                    
                    for i, hit in enumerate(hits[:3], 1):  # Show top 3 results
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
            
            # Handle auxiliary table results
            elif "data" in data and isinstance(data["data"], list):
                items = data["data"]
                response_parts.append(f"**Total de elementos**: {len(items)}\n")
                
                if items:
                    response_parts.append("**📊 Elementos disponibles**:\n")
                    for i, item in enumerate(items[:10], 1):  # Show first 10 items
                        if isinstance(item, dict):
                            name = item.get("descripcion", item.get("nombre", str(item)))
                            response_parts.append(f"{i}. {name}")
                        else:
                            response_parts.append(f"{i}. {item}")
        
        # Add footer
        response_parts.extend([
            "\n---",
            "💡 *Información proporcionada por el Boletín Oficial del Estado (BOE)*",
            "📖 *Para información detallada, consulte el texto completo en boe.es*"
        ])
        
        return "\n".join(response_parts)
    
    async def query_boe_http(self, request: ChatRequest) -> AsyncGenerator[StreamChunk, None]:
        """Query BOE using HTTP MCP server and stream response"""
        
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
                content="**ℹ️ Servicio Especializado en Consultas Legales**\n\n" +
                       "Este servicio está especializado en **consultas legales y fiscales españolas**.\n\n" +
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
            logger.info(f"Processing legal query via HTTP MCP: {request.message[:100]}...")
            
            # Extract keywords and determine search strategy
            query_analysis = self._analyze_query_and_extract_keywords(request.message)
            
            # Perform BOE search
            search_results = await self.search_laws(query_analysis["query_value"])
            
            # Format response
            formatted_response = self._format_boe_response(search_results, request.message)
            
            # Stream the response in chunks
            words = formatted_response.split()
            chunk_size = 15
            
            for i in range(0, len(words), chunk_size):
                chunk_words = words[i:i + chunk_size]
                chunk_content = " ".join(chunk_words)
                
                if i > 0:  # Add space before continuation chunks
                    chunk_content = " " + chunk_content
                
                yield StreamChunk(
                    content=chunk_content,
                    conversation_id=request.conversation_id or "boe_http",
                    is_complete=i + chunk_size >= len(words)
                )
                
                # Small delay to simulate streaming
                await asyncio.sleep(0.1)
        
        except Exception as e:
            logger.error(f"HTTP MCP Service error: {e}")
            yield StreamChunk(
                content="**❌ Error en Servicio HTTP**\n\n" +
                       "No se pudo procesar la consulta con el servicio legal HTTP.\n\n" +
                       f"**Error técnico**: {str(e)}\n\n" +
                       "**Recomendaciones:**\n" +
                       "• Inténtelo nuevamente en unos minutos\n" +
                       "• Verifique la conexión del servidor HTTP MCP\n" +
                       "• Para consultas urgentes, consulte directamente boe.es",
                conversation_id=request.conversation_id or "error",
                is_complete=True
            )
    
    def is_available(self) -> bool:
        """Check if HTTP MCP service is available"""
        return self._is_available
    
    async def reinitialize(self):
        """Reinitialize the service"""
        logger.info("Reinitializing HTTP MCP Service...")
        if self.client:
            await self.client.aclose()
            self.client = None
        
        # Check server health
        await self.check_server_health()

# Create service instance
http_mcp_service = HTTPMCPService()