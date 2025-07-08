"""
Fixed version of the search_laws_list function for BOE MCP server
This addresses the parameter validation issues
"""

async def search_laws_list_fixed(
    from_date: str | None = None,
    to_date: str | None = None,
    offset: int = 0,  # Remove None default, always include offset
    limit: int = 50,  # Remove None default, always include limit
    
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
    Fixed version of search_laws_list with proper parameter handling
    """
    
    endpoint = "/datosabiertos/api/legislacion-consolidada"
    
    # Always include offset and limit as strings
    params: dict[str, Union[str, int, None]] = {
        "offset": str(offset),  # Convert to string
        "limit": str(limit)     # Convert to string
    }
    
    # Add date filters if provided
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    
    # Build query object if any search criteria provided
    if (query_value or ambito or must or should or must_not or range_filters or sort_by):
        
        query_obj_def: dict[str, Any] = {"query": {}}
        
        # Range filters
        if range_filters:
            query_obj_def["query"]["range"] = range_filters
        
        # Sort options
        if sort_by:
            query_obj_def["sort"] = sort_by
        
        if (query_value or ambito or must or should or must_not):
            # Build query string
            query_string = {}
            clauses = []
            
            # Text search
            if query_value:
                # Clean the query value - remove special characters that might cause issues
                clean_query = query_value.strip()
                if search_in_title_only:
                    clauses.append(f"titulo:({clean_query})")
                else:
                    clauses.append(f"(titulo:({clean_query}) OR texto:({clean_query}))")
            
            # Vigencia filter
            if solo_vigente:
                clauses.append('vigencia_agotada:"N"')
            
            # Consolidation state
            if solo_consolidada:
                clauses.append('estado_consolidacion@codigo:"3"')
            
            # Ambito filter
            ambito_map = {
                "Estatal": "1",
                "Autonómico": "2", 
                "Europeo": "3"
            }
            if ambito and ambito in ambito_map:
                clauses.append(f'ambito@codigo:"{ambito_map[ambito]}"')
            
            # Additional conditions
            if must:
                must_clauses = [f"{k}:{v}" for k, v in must.items()]
                if must_clauses:
                    clauses.append(f"({' AND '.join(must_clauses)})")
            
            if should:
                should_clauses = [f"{k}:{v}" for k, v in should.items()]
                if should_clauses:
                    clauses.append(f"({' OR '.join(should_clauses)})")
            
            # Exclusions
            if must_not:
                for k, v in must_not.items():
                    clauses.append(f"NOT {k}:{v}")
            
            if clauses:
                query_string["query"] = " AND ".join(clauses)
                query_obj_def["query"]["query_string"] = query_string
        
        # Serialize query object
        params["query"] = json.dumps(query_obj_def, ensure_ascii=False)
    
    # Log the request for debugging
    logger.info(f"BOE API Request - Endpoint: {endpoint}")
    logger.info(f"BOE API Request - Params: {json.dumps(params, indent=2, ensure_ascii=False)}")
    
    # Make the request
    data = await make_boe_request(endpoint, params=params)
    
    if not data:
        # Return more informative error
        return {
            "error": "Failed to get response from BOE API",
            "endpoint": endpoint,
            "params": params,
            "status": "no_data"
        }
    
    # Return successful response with metadata
    return {
        "endpoint": endpoint,
        "params": params,
        "data": data,
        "status": "success"
    }