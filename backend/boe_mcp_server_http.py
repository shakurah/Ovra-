#!/usr/bin/env python3
"""
Simple HTTP wrapper for BOE MCP Server
"""
import json
import asyncio
import subprocess
import signal
import os
import sys
from typing import Any, Optional
import httpx
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BOE-MCP-HTTP-Wrapper")

class MCPHTTPServer:
    """HTTP wrapper for MCP server running on stdio"""
    
    def __init__(self):
        self.mcp_process = None
        self.app = FastAPI(title="BOE MCP HTTP Server", version="1.0.0")
        self.setup_routes()
        self.setup_middleware()
        
        # Path to the fixed MCP server
        self.script_dir = Path(__file__).parent
        self.mcp_server_path = self.script_dir / "boe_mcp_server_fixed.py"
        
    def setup_middleware(self):
        """Setup CORS and other middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Setup HTTP routes"""
        
        @self.app.get("/")
        async def root():
            return {
                "message": "BOE MCP HTTP Server", 
                "version": "1.0.0", 
                "status": "running" if self.mcp_process else "stopped"
            }
        
        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy" if self.mcp_process else "unhealthy",
                "mcp_process_running": self.mcp_process is not None,
                "tools": ["search_laws_list", "get_law_section", "get_boe_summary", "get_borme_summary", "get_auxiliary_table"]
            }
        
        @self.app.post("/mcp")
        async def mcp_request(request: Request):
            """Handle MCP requests over HTTP"""
            try:
                # Get request body
                body = await request.body()
                
                if not self.mcp_process:
                    raise HTTPException(status_code=503, detail="MCP server not running")
                
                # Send request to MCP process
                self.mcp_process.stdin.write(body + b'\n')
                await asyncio.to_thread(self.mcp_process.stdin.flush)
                
                # Read response from MCP process
                response_line = await asyncio.to_thread(self.mcp_process.stdout.readline)
                
                if not response_line:
                    raise HTTPException(status_code=500, detail="No response from MCP server")
                
                # Parse and return response
                response_data = json.loads(response_line.decode())
                return JSONResponse(content=response_data)
                
            except Exception as e:
                logger.error(f"MCP request error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/sse")
        async def sse_endpoint(request: Request):
            """SSE endpoint for MCP communication"""
            
            async def sse_generator():
                try:
                    body = await request.body()
                    
                    if not self.mcp_process:
                        error_response = {
                            "jsonrpc": "2.0",
                            "error": {"code": -32000, "message": "MCP server not running"}
                        }
                        yield f"data: {json.dumps(error_response)}\n\n"
                        return
                    
                    # Send request to MCP process
                    self.mcp_process.stdin.write(body + b'\n')
                    await asyncio.to_thread(self.mcp_process.stdin.flush)
                    
                    # Read response from MCP process
                    response_line = await asyncio.to_thread(self.mcp_process.stdout.readline)
                    
                    if response_line:
                        yield f"data: {response_line.decode()}\n\n"
                    else:
                        error_response = {
                            "jsonrpc": "2.0",
                            "error": {"code": -32001, "message": "No response from MCP server"}
                        }
                        yield f"data: {json.dumps(error_response)}\n\n"
                
                except Exception as e:
                    logger.error(f"SSE error: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32002, "message": str(e)}
                    }
                    yield f"data: {json.dumps(error_response)}\n\n"
            
            return StreamingResponse(
                sse_generator(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                }
            )
        
        @self.app.post("/start")
        async def start_mcp():
            """Start the MCP server process"""
            if self.mcp_process:
                return {"status": "already_running"}
            
            await self.start_mcp_process()
            return {"status": "started"}
        
        @self.app.post("/stop")
        async def stop_mcp():
            """Stop the MCP server process"""
            if not self.mcp_process:
                return {"status": "not_running"}
            
            await self.stop_mcp_process()
            return {"status": "stopped"}
    
    async def start_mcp_process(self):
        """Start the MCP server process"""
        try:
            logger.info(f"Starting MCP server: {self.mcp_server_path}")
            
            # Get python executable from virtual environment
            venv_python = self.script_dir / "venv" / "bin" / "python"
            python_exe = str(venv_python) if venv_python.exists() else "python"
            
            self.mcp_process = await asyncio.create_subprocess_exec(
                python_exe, str(self.mcp_server_path),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.script_dir)
            )
            
            logger.info(f"MCP server started with PID: {self.mcp_process.pid}")
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            self.mcp_process = None
            raise
    
    async def stop_mcp_process(self):
        """Stop the MCP server process"""
        if self.mcp_process:
            try:
                self.mcp_process.terminate()
                await asyncio.wait_for(self.mcp_process.wait(), timeout=5.0)
                logger.info("MCP server stopped gracefully")
            except asyncio.TimeoutError:
                logger.warning("MCP server didn't stop gracefully, killing...")
                self.mcp_process.kill()
                await self.mcp_process.wait()
            finally:
                self.mcp_process = None
    
    async def run(self, host="0.0.0.0", port=8931):
        """Run the HTTP server"""
        # Start MCP process
        await self.start_mcp_process()
        
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal")
            asyncio.create_task(self.stop_mcp_process())
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Start HTTP server
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        try:
            logger.info(f"Starting BOE MCP HTTP Server on {host}:{port}")
            await server.serve()
        finally:
            await self.stop_mcp_process()

# Create server instance
mcp_http_server = MCPHTTPServer()

def main():
    """Main entry point"""
    try:
        asyncio.run(mcp_http_server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    main()