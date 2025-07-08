#!/usr/bin/env python3
"""
Fix for BOE MCP Server Parameter Validation Issues

This script patches the BOE MCP server to fix parameter validation errors.
The main issues are:
1. offset=0 is not being sent because 0 is falsy in Python
2. Parameters might need to be strings instead of integers
3. Better error handling is needed

Run this to patch the BOE MCP server in your virtual environment.
"""

import os
import shutil
from pathlib import Path

def create_fixed_server():
    """Create a fixed version of the BOE MCP server"""
    
    fixed_server_code = '''import json
from typing import Any, Literal, Union, Annotated
import httpx
import logging
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BOE-MCPServer")

mcp = FastMCP(
    "boe-mcp",
    description="MCP server for querying the Spanish Official State Gazette (BOE) API"
)

BOE_API_BASE = "https://www.boe.es"
USER_AGENT = "boe-mcp-client/1.0"

async def make_boe_request(
    endpoint: str,
    params: dict[str, Any] | None = None,
    accept: str = "application/json"
) -> dict[str, Any] | None:
    """
    Realiza una solicitud HTTP GET a la API del BOE.

    Args:
        endpoint: Ruta relativa del endpoint (ej. '/datosabiertos/api/...').
        params: Parámetros de consulta (query string).
        accept: Tipo de contenido esperado ('application/json' por defecto).

    Returns:
        Diccionario con los datos JSON de respuesta o None si ocurre un error.
    """
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
            print(f"[BOE] HTTP error: {http_err.response.status_code} - {http_err.response.text}")
        except Exception as e:
            logger.error(f"[BOE] Error: {e}")
            print(f"[BOE] Error: {e}")

        return None

async def make_boe_raw_request(endpoint: str, accept: str = "application/xml") -> str | None:

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
            print(f"[BOE] HTTP error {http_err.response.status_code}")
        except Exception as e:
            print(f"[BOE] Error: {e}")

        return None

# ----------- 1. LEGISLACIÓN CONSOLIDADA -------------------

@mcp.tool()
async def search_laws_list(
    
    from_date: str | None = None,
    to_date: str | None = None,
    offset: int = 0,  # FIXED: Always default to 0, not None
    limit: int = 50,   # FIXED: Always default to 50, not None

    query_value: str | None = None,

    search_in_title_only: bool = True,
    solo_vigente: bool = True,
    solo_consolidada: bool = False,

    ambito: Literal["Estatal", "Autonómico", "Europeo"] | None = None,
    must: dict[str, str] | None = None,
    should: dict[str, str] | None = None,
    must_not: dict[str, str] | None = None,
    range_filters: dict | None = None,
    sort_by: list[dict] | None = None,

) -> Union[dict, str]:
    
    """
    Búsqueda avanzada de normas del BOE.

    Args:
        -from_date: Fecha mínima (AAAAMMDD).
        -to_date: Fecha máxima (AAAAMMDD).
        -offset: Índice inicial. Es obligatorio incluírlo en la llamada a la función.
        -limit: Máximo de resultados (-1 para todos).

        -query_value: Texto libre. Usar preferentemente palabras, no frases.

        -search_in_title_only: True para buscar solo en el título (True por defecto).
        -solo_vigente: True para buscar solamente normas vigentes (True por defecto).
        -solo_consolidada: true para buscar solamente normas consolidadas (False por defecto).

        -ambito: Filtra por ámbito ('Estatal', 'Autonómico', 'Europeo').
        -must: Condiciones que deben cumplirse (and).
        -should: Condiciones opcionales (or).
        -must_not: Condiciones excluidas (not).
        -range_filters: Filtros por fechas.
        -sort_by: Ordenamiento personalizado.
    """

    endpoint = "/datosabiertos/api/legislacion-consolidada"
    
    params: dict[str, Union[str, int, None]] = {}

    # FIXED: Always include offset and limit
    params["offset"] = str(offset)  # Convert to string
    params["limit"] = str(limit)    # Convert to string
    
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date

    if (query_value or ambito or must or should or must_not or range_filters or sort_by):

        logger.info(f"Building query with query_value: {query_value}")

        # Construcción del objeto query según especificación BOE con tipos explícitos
        query_obj_def: dict[str, Any] = {"query": {}}
        
        # ⏳ Rango por fechas
        if range_filters:
            query_obj_def["query"]["range"] = range_filters

        # 📥 Ordenamiento
        if sort_by:
            query_obj_def["sort"] = sort_by

        if (query_value or ambito or must or should or must_not):
            # 1. Query String (condiciones principales)
            query_string = {}
            clauses = []

            # 🔍 Búsqueda textual
            if query_value:
                # FIXED: Use OR instead of 'or' (uppercase)
                if search_in_title_only:
                    clauses.append(f"titulo:({query_value})")
                else:
                    clauses.append(f"(titulo:({query_value}) OR texto:({query_value}))")

            # ✅ Vigencia
            if solo_vigente:
                clauses.append('vigencia_agotada:"N"')
            
            # 📄 Estado de consolidación
            estado_map = {
                "Consolidada": "3", 
                "Parcial": "2", 
                "No consolidada": "1"
            }
            if solo_consolidada:
                clauses.append(f'estado_consolidacion@codigo:"{estado_map["Consolidada"]}"')
            
            # 🌐 Filtro de ámbito
            # Mapeo de códigos de ámbito para la API del BOE
            ambito_map = {
                "Estatal": "1",
                "Autonómico": "2",
                "Europeo": "3"
            }
            if ambito and ambito in ambito_map:
                clauses.append(f'ambito@codigo:"{ambito_map[ambito]}"')
            
            # 🧱 Condiciones adicionales - FIXED
            if must:
                must_clauses = [f"{k}:{v}" for k, v in must.items()]
                if must_clauses:
                    clauses.append(f"({' AND '.join(must_clauses)})")
            
            if should:
                should_clauses = [f"{k}:{v}" for k, v in should.items()]
                if should_clauses:
                    clauses.append(f"({' OR '.join(should_clauses)})")
            
            # 🚫 Exclusiones
            if must_not:
                for k, v in must_not.items():
                    clauses.append(f"NOT {k}:{v}")
            
            if clauses:
                # FIXED: Use AND instead of 'and' (uppercase)
                query_string["query"] = " AND ".join(clauses)
                query_obj_def["query"]["query_string"] = query_string
            
        params["query"] = json.dumps(query_obj_def, ensure_ascii=False)

    logger.info(f"Final params: {params}")
    data = await make_boe_request(endpoint, params=params)

    if not data:
        # FIXED: Return proper error structure
        error_msg = f"Failed to get data from BOE API. Endpoint: {endpoint}, Params: {params}"
        logger.error(error_msg)
        return {"error": error_msg, "endpoint": endpoint, "params": params}

    return {"endpoint": endpoint, "params": params, "data": data}

@mcp.tool()
async def get_law_section(
    identifier: str,
    section: Literal[
        "completa", "metadatos", "analisis", "metadata-eli", "texto", "indice", "bloque"
    ],
    block_id: str | None = None,  # FIXED: Made optional with default None
    format: Literal["xml", "json"] = "xml"
) -> Union[str, bytes]:
    """
    Recupera una parte específica de una norma consolidada del BOE.

    Args:
        identifier: ID de la norma (ej. "BOE-A-2023-893").
        section: Parte de la norma a obtener:
            - "completa": Toda la norma
            - "metadatos": Solo metadatos
            - "analisis": Datos analíticos (materias, referencias)
            - "metadata-eli": Metadatos ELI
            - "texto": Texto completo consolidado
            - "indice": Índice de bloques
            - "bloque": Un bloque específico (requiere block_id)
        block_id: Solo requerido si section="bloque"
        format: Formato de respuesta (xml o json, si disponible)
    
    Returns:
        Contenido de la norma o parte solicitada (como string XML o JSON).
    """
    base = f"/datosabiertos/api/legislacion-consolidada/id/{identifier}"

    # Construir el endpoint correcto
    match section:
        case "completa":
            endpoint = base
        case "bloque":
            if not block_id:
                return "Para obtener un bloque, debes proporcionar block_id."
            endpoint = f"{base}/texto/bloque/{block_id}"
        case "indice":
            endpoint = f"{base}/texto/indice"
        case _:
            endpoint = f"{base}/{section}"

    accept = "application/xml" if format == "xml" else "application/json"

    data = await make_boe_raw_request(endpoint, accept=accept)

    if data is None:
        return f"No se pudo recuperar la sección '{section}' de la norma {identifier}."

    return data

# ----------- 2. SUMARIO BOE -------------------------------

class boe_summaryParams(BaseModel):
    fecha: Annotated[str, Field(description="Fecha del sumario solicitado")]

@mcp.tool()
async def get_boe_summary(params: boe_summaryParams) -> Union[dict, str]:
    """
    Obtener sumario del BOE para una fecha (AAAAMMDD).
    
    Args:
        fecha: Fecha del BOE (ej: 20240501)
    """
    fecha = params.fecha

    endpoint = f"/datosabiertos/api/boe/sumario/{fecha}"
    data = await make_boe_request(endpoint)

    if not data or "data" not in data or "sumario" not in data["data"]:
        return f"No se pudo obtener el sumario del BOE para {fecha}."

    return data

# ----------- 3. SUMARIO BORME -----------------------------

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
        return f"No se pudo obtener el sumario del BORME para {fecha}."

    return data

# ----------- 4. TABLAS AUXILIARES -------------------------

@mcp.tool()
async def get_auxiliary_table(table_name: str) -> Union[dict, str]:
    """
    Consultar tablas auxiliares disponibles en la API del BOE. Dichas tabls incluyem los 
    códigos de materias, ámbitos, estados de consolidación, departamentos, rangos y relaciones.
    Estos códigos se pueden usar para usar en las queries de la función search_consolidated_laws_list
    
    Args:
        table_name: Una de las siguientes:
        'materias', 'ambitos', 'estados-consolidacion',
        'departamentos', 'rangos', 'relaciones-anteriores', 'relaciones-posteriores'
    """
    valid_tables = [
        "materias", "ambitos", "estados-consolidacion",
        "departamentos", "rangos", "relaciones-anteriores", "relaciones-posteriores"
    ]
    if table_name not in valid_tables:
        return f"Tabla no válida. Usa una de: {', '.join(valid_tables)}"

    endpoint = f"/datosabiertos/api/datos-auxiliares/{table_name}"
    data = await make_boe_request(endpoint)

    if not data:
        return f"No se pudo recuperar la tabla {table_name}."

    return data

# ------------------- ENTRY POINT ---------------------------

# Main function
def main():
    """Arrancar el servidor mcp"""
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
'''
    
    return fixed_server_code

def patch_boe_mcp_server():
    """Patch the BOE MCP server in the virtual environment"""
    
    # Find the BOE MCP server file
    venv_path = Path("/home/ali/development/ovra_ai/backend/venv")
    server_path = venv_path / "lib/python3.12/site-packages/boe_mcp/server.py"
    
    if not server_path.exists():
        print(f"❌ BOE MCP server not found at: {server_path}")
        return False
    
    # Backup the original file
    backup_path = server_path.with_suffix('.py.backup')
    if not backup_path.exists():
        shutil.copy(server_path, backup_path)
        print(f"✅ Created backup at: {backup_path}")
    
    # Write the fixed version
    fixed_code = create_fixed_server()
    with open(server_path, 'w', encoding='utf-8') as f:
        f.write(fixed_code)
    
    print(f"✅ Patched BOE MCP server at: {server_path}")
    print("\nKey fixes applied:")
    print("1. ✅ Always include offset and limit parameters (converted to strings)")
    print("2. ✅ Fixed boolean operators (OR/AND instead of or/and)")
    print("3. ✅ Better error handling and logging")
    print("4. ✅ Made block_id optional with default None")
    print("\n⚠️  Please restart your backend service for changes to take effect:")
    print("   sudo systemctl restart ovra-backend")
    
    return True

if __name__ == "__main__":
    print("BOE MCP Server Parameter Fix")
    print("=" * 50)
    
    if patch_boe_mcp_server():
        print("\n✅ Patch applied successfully!")
    else:
        print("\n❌ Failed to apply patch!")