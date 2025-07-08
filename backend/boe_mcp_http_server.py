#!/usr/bin/env python3
"""
HTTP MCP Server for BOE API - converted from your original MCP server
"""
import json
from typing import Any, Literal, Union, Annotated
import httpx
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BOE-HTTP-Server")

app = FastAPI(title="BOE MCP HTTP Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        except Exception as e:
            logger.error(f"[BOE] Error: {e}")

        return None

async def make_boe_raw_request(endpoint: str, accept: str = "application/xml") -> str | None:
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

# Pydantic models for request/response
class SearchLawsRequest(BaseModel):
    from_date: str | None = None
    to_date: str | None = None
    offset: int = 0
    limit: int = 50
    query_value: str | None = None
    search_in_title_only: bool = True
    solo_vigente: bool = True
    solo_consolidada: bool = False
    ambito: Literal["Estatal", "Autonómico", "Europeo"] | None = None
    must: dict[str, str] | None = None
    should: dict[str, str] | None = None
    must_not: dict[str, str] | None = None
    range_filters: dict | None = None
    sort_by: list[dict] | None = None

class LawSectionRequest(BaseModel):
    identifier: str
    section: Literal["completa", "metadatos", "analisis", "metadata-eli", "texto", "indice", "bloque"]
    block_id: str | None = None
    format: Literal["xml", "json"] = "xml"

class SummaryRequest(BaseModel):
    fecha: str = Field(description="Fecha del sumario (AAAAMMDD)")

class AuxiliaryTableRequest(BaseModel):
    table_name: str

# HTTP Endpoints - converted from MCP tools

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "BOE HTTP Server", 
        "version": "1.0.0",
        "endpoints": [
            "/search_laws_list",
            "/get_law_section", 
            "/get_boe_summary",
            "/get_borme_summary",
            "/get_auxiliary_table"
        ]
    }

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "BOE HTTP Server"}

@app.post("/search_laws_list")
async def search_laws_list(request: SearchLawsRequest) -> Union[dict, str]:
    """
    Búsqueda avanzada de normas del BOE.
    """
    endpoint = "/datosabiertos/api/legislacion-consolidada"
    
    params: dict[str, Union[str, int, None]] = {}

    if request.from_date:
        params["from"] = request.from_date
    if request.to_date:
        params["to"] = request.to_date
    if request.offset:
        params["offset"] = request.offset
    if request.limit:
        params["limit"] = request.limit

    if (request.query_value or request.ambito or request.must or request.should or 
        request.must_not or request.range_filters or request.sort_by):

        # Construcción del objeto query según especificación BOE
        query_obj_def: dict[str, Any] = {"query": {}}
        
        # Rango por fechas
        if request.range_filters:
            query_obj_def["query"]["range"] = request.range_filters

        # Ordenamiento
        if request.sort_by:
            query_obj_def["sort"] = request.sort_by

        if (request.query_value or request.ambito or request.must or request.should or request.must_not):
            # Query String (condiciones principales)
            query_string = {}
            clauses = []

            # Búsqueda textual
            if request.query_value:
                if request.search_in_title_only:
                    clauses.append(f"titulo:({request.query_value})")
                else:
                    clauses.append(f"(titulo:({request.query_value}) or texto:({request.query_value}))")

            # Vigencia
            if request.solo_vigente:
                clauses.append("vigencia_agotada:\"N\"")
            
            # Estado de consolidación
            estado_map = {
                "Consolidada": "3", 
                "Parcial": "2", 
                "No consolidada": "1"
            }
            if request.solo_consolidada:
                clauses.append(f"estado_consolidacion@codigo:{estado_map['Consolidada']}")
            
            # Filtro de ámbito
            ambito_map = {
                "Estatal": "1",
                "Autonómico": "2",
                "Europeo": "3"
            }
            if request.ambito:
                clauses.append(f'ambito@codigo:"{ambito_map.get(request.ambito)}"')
            
            # Condiciones adicionales
            for cond_type, operator in [("must", "and"), ("should", "or")]:
                cond_data = getattr(request, cond_type)
                if cond_data:
                    cond_clause = f" {operator} ".join(
                        f"{k}:{v}" for k, v in cond_data.items()
                    )
                    clauses.append(f"({cond_clause})")
            
            # Exclusiones
            if request.must_not:
                clauses.extend(f"not {k}:{v}" for k, v in request.must_not.items())
            
            if clauses:
                query_string["query"] = " and ".join(clauses)
                query_obj_def["query"]["query_string"] = query_string
            
        params["query"] = json.dumps(query_obj_def)

    data = await make_boe_request(endpoint, params=params)

    if not data:
        return {"error": f"Failed to get data from BOE API. Endpoint: {endpoint}, Params: {params}"}

    return {"endpoint": endpoint, "params": params, "data": data}

@app.post("/get_law_section")
async def get_law_section(request: LawSectionRequest) -> Union[str, dict]:
    """
    Recupera una parte específica de una norma consolidada del BOE.
    """
    base = f"/datosabiertos/api/legislacion-consolidada/id/{request.identifier}"

    # Construir el endpoint correcto
    if request.section == "completa":
        endpoint = base
    elif request.section == "bloque":
        if not request.block_id:
            return {"error": "Para obtener un bloque, debes proporcionar block_id."}
        endpoint = f"{base}/texto/bloque/{request.block_id}"
    elif request.section == "indice":
        endpoint = f"{base}/texto/indice"
    else:
        endpoint = f"{base}/{request.section}"

    accept = "application/xml" if request.format == "xml" else "application/json"

    data = await make_boe_raw_request(endpoint, accept=accept)

    if data is None:
        return {"error": f"No se pudo recuperar la sección '{request.section}' de la norma {request.identifier}."}

    return {"data": data, "format": request.format, "section": request.section}

@app.post("/get_boe_summary")
async def get_boe_summary(request: SummaryRequest) -> Union[dict, str]:
    """
    Obtener sumario del BOE para una fecha (AAAAMMDD).
    """
    endpoint = f"/datosabiertos/api/boe/sumario/{request.fecha}"
    data = await make_boe_request(endpoint)

    if not data or "data" not in data or "sumario" not in data["data"]:
        return {"error": f"No se pudo obtener el sumario del BOE para {request.fecha}."}

    return data

@app.post("/get_borme_summary")
async def get_borme_summary(request: SummaryRequest) -> Union[dict, str]:
    """
    Obtener sumario del BORME para una fecha (AAAAMMDD).
    """
    endpoint = f"/datosabiertos/api/borme/sumario/{request.fecha}"
    data = await make_boe_request(endpoint)

    if not data or "data" not in data or "sumario" not in data["data"]:
        return {"error": f"No se pudo obtener el sumario del BORME para {request.fecha}."}

    return data

@app.post("/get_auxiliary_table")
async def get_auxiliary_table(request: AuxiliaryTableRequest) -> Union[dict, str]:
    """
    Consultar tablas auxiliares disponibles en la API del BOE.
    """
    valid_tables = [
        "materias", "ambitos", "estados-consolidacion",
        "departamentos", "rangos", "relaciones-anteriores", "relaciones-posteriores"
    ]
    if request.table_name not in valid_tables:
        return {"error": f"Tabla no válida. Usa una de: {', '.join(valid_tables)}"}

    endpoint = f"/datosabiertos/api/datos-auxiliares/{request.table_name}"
    data = await make_boe_request(endpoint)

    if not data:
        return {"error": f"No se pudo recuperar la tabla {request.table_name}."}

    return data

def main():
    """Start the HTTP server"""
    logger.info("Starting BOE HTTP Server on port 8931")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8931,
        log_level="info"
    )

if __name__ == "__main__":
    main()