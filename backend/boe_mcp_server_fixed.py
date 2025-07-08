import json
from typing import Any, Literal, Union, Optional
import httpx
import logging
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BOE-MCPServer-Fixed")

mcp = FastMCP(
    "boe-mcp-fixed",
    description="Fixed MCP server for querying the Spanish Official State Gazette (BOE) API"
)

BOE_API_BASE = "https://www.boe.es"
USER_AGENT = "boe-mcp-client/1.0"

async def make_boe_request(
    endpoint: str,
    params: Optional[dict[str, Any]] = None,
    accept: str = "application/json"
) -> Optional[dict[str, Any]]:
    """Make HTTP GET request to BOE API"""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": accept,
    }
    url = f"{BOE_API_BASE}{endpoint}"

    logger.info(f"Making request to BOE API: {url} with params: {params}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as http_err:
            logger.error(f"[BOE] HTTP error: {http_err.response.status_code} - {http_err.response.text}")
        except Exception as e:
            logger.error(f"[BOE] Error: {e}")

        return None

async def make_boe_raw_request(endpoint: str, accept: str = "application/xml") -> Optional[str]:
    """Make raw HTTP GET request to BOE API"""
    headers = {
        "User-Agent": "boe-mcp-client/1.0",
        "Accept": accept,
    }
    url = f"{BOE_API_BASE}{endpoint}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as http_err:
            logger.error(f"[BOE] HTTP error {http_err.response.status_code}")
        except Exception as e:
            logger.error(f"[BOE] Error: {e}")

        return None

# Pydantic models for all functions to ensure consistent parameter handling

class SearchLawsParams(BaseModel):
    """Parameters for search_laws_list function"""
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    offset: int = 0
    limit: int = 50
    query_value: Optional[str] = None
    search_in_title_only: bool = True
    solo_vigente: bool = True
    solo_consolidada: bool = False
    ambito: Optional[Literal["Estatal", "Autonómico", "Europeo"]] = None

class LawSectionParams(BaseModel):
    """Parameters for get_law_section function"""
    identifier: str
    section: Literal["completa", "metadatos", "analisis", "metadata-eli", "texto", "indice", "bloque"]
    block_id: Optional[str] = None
    format: Literal["xml", "json"] = "xml"

class SummaryParams(BaseModel):
    """Parameters for summary functions"""
    fecha: str = Field(description="Fecha del sumario (AAAAMMDD)")

class AuxiliaryTableParams(BaseModel):
    """Parameters for get_auxiliary_table function"""
    table_name: str = Field(description="Nombre de la tabla auxiliar")

# MCP Tools with consistent Pydantic models

@mcp.tool()
async def search_laws_list(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
    query_value: Optional[str] = None,
    search_in_title_only: bool = True,
    solo_vigente: bool = True,
    solo_consolidada: bool = False,
    ambito: Optional[Literal["Estatal", "Autonómico", "Europeo"]] = None
) -> Union[dict, str]:
    """
    Búsqueda avanzada de normas del BOE.
    
    Args:
        from_date: Fecha mínima (AAAAMMDD)
        to_date: Fecha máxima (AAAAMMDD)
        offset: Índice inicial
        limit: Máximo de resultados
        query_value: Texto libre a buscar
        search_in_title_only: Buscar solo en títulos
        solo_vigente: Solo normas vigentes
        solo_consolidada: Solo normas consolidadas
        ambito: Ámbito de la norma
    """
    endpoint = "/datosabiertos/api/legislacion-consolidada"
    
    # Build request parameters
    request_params = {
        "offset": str(offset),
        "limit": str(limit)
    }
    
    if from_date:
        request_params["from"] = from_date
    if to_date:
        request_params["to"] = to_date

    # Build query if search criteria provided
    if query_value or ambito:
        query_obj_def = {"query": {}}
        query_string = {}
        clauses = []

        # Text search
        if query_value:
            if search_in_title_only:
                clauses.append(f"titulo:({query_value})")
            else:
                clauses.append(f"(titulo:({query_value}) OR texto:({query_value}))")

        # Vigencia filter
        if solo_vigente:
            clauses.append('vigencia_agotada:"N"')
        
        # Consolidation state
        if solo_consolidada:
            clauses.append('estado_consolidacion@codigo:"3"')
        
        # Ambito filter
        ambito_map = {"Estatal": "1", "Autonómico": "2", "Europeo": "3"}
        if ambito and ambito in ambito_map:
            clauses.append(f'ambito@codigo:"{ambito_map[ambito]}"')
        
        if clauses:
            query_string["query"] = " AND ".join(clauses)
            query_obj_def["query"]["query_string"] = query_string
        
        request_params["query"] = json.dumps(query_obj_def, ensure_ascii=False)

    logger.info(f"Final params: {request_params}")
    data = await make_boe_request(endpoint, params=request_params)

    if not data:
        error_msg = f"Failed to get data from BOE API. Endpoint: {endpoint}, Params: {request_params}"
        logger.error(error_msg)
        return {"error": error_msg, "endpoint": endpoint, "params": request_params}

    return {"endpoint": endpoint, "params": request_params, "data": data}

@mcp.tool()
async def get_law_section(
    identifier: str,
    section: Literal["completa", "metadatos", "analisis", "metadata-eli", "texto", "indice", "bloque"],
    block_id: Optional[str] = None,
    format: Literal["xml", "json"] = "xml"
) -> Union[str, dict]:
    """
    Recupera una parte específica de una norma consolidada del BOE.
    
    Args:
        identifier: ID de la norma
        section: Sección a obtener
        block_id: ID del bloque (solo para section='bloque')
        format: Formato de respuesta
    """
    base = f"/datosabiertos/api/legislacion-consolidada/id/{identifier}"

    # Build endpoint
    if section == "completa":
        endpoint = base
    elif section == "bloque":
        if not block_id:
            return {"error": "block_id required for bloque section"}
        endpoint = f"{base}/texto/bloque/{block_id}"
    elif section == "indice":
        endpoint = f"{base}/texto/indice"
    else:
        endpoint = f"{base}/{section}"

    accept = "application/xml" if format == "xml" else "application/json"
    data = await make_boe_raw_request(endpoint, accept=accept)

    if data is None:
        return {"error": f"Could not retrieve section '{section}' for law {identifier}"}

    return {"data": data, "format": format, "section": section}

@mcp.tool()
async def get_boe_summary(fecha: str) -> Union[dict, str]:
    """
    Obtener sumario del BOE para una fecha (AAAAMMDD).
    
    Args:
        fecha: Fecha del BOE (ej: 20240501)
    """
    endpoint = f"/datosabiertos/api/boe/sumario/{fecha}"
    data = await make_boe_request(endpoint)

    if not data or "data" not in data or "sumario" not in data["data"]:
        return {"error": f"Could not get BOE summary for {fecha}"}

    return data

@mcp.tool()
async def get_borme_summary(fecha: str) -> Union[dict, str]:
    """
    Obtener sumario del BORME para una fecha (AAAAMMDD).
    
    Args:
        fecha: Fecha del BORME (ej: 20240501)
    """
    endpoint = f"/datosabiertos/api/borme/sumario/{fecha}"
    data = await make_boe_request(endpoint)

    if not data or "data" not in data or "sumario" not in data["data"]:
        return {"error": f"Could not get BORME summary for {fecha}"}

    return data

@mcp.tool()
async def get_auxiliary_table(table_name: str) -> Union[dict, str]:
    """
    Consultar tablas auxiliares disponibles en la API del BOE.
    
    Args:
        table_name: Nombre de la tabla auxiliar
    """
    valid_tables = [
        "materias", "ambitos", "estados-consolidacion",
        "departamentos", "rangos", "relaciones-anteriores", "relaciones-posteriores"
    ]
    
    if table_name not in valid_tables:
        return {"error": f"Invalid table. Use one of: {', '.join(valid_tables)}"}

    endpoint = f"/datosabiertos/api/datos-auxiliares/{table_name}"
    data = await make_boe_request(endpoint)

    if not data:
        return {"error": f"Could not retrieve table {table_name}"}

    return data

# Main function
def main():
    """Start the MCP server"""
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()