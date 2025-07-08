#!/usr/bin/env python3
"""
Startup script for MCP server as a separate process
"""
import subprocess
import sys
import os
import time
import signal
import atexit
from pathlib import Path

class MCPServerManager:
    """Manages MCP server as a separate process"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.mcp_server_path = self.script_dir / "boe_mcp_server_fixed.py"
        self.venv_python = self.script_dir / "venv" / "bin" / "python"
        self.process = None
        
        # Register cleanup on exit
        atexit.register(self.stop_server)
    
    def start_server(self):
        """Start the MCP server process"""
        if self.process:
            print("MCP server already running")
            return True
        
        try:
            # Use venv python if available, otherwise system python
            python_exe = str(self.venv_python) if self.venv_python.exists() else "python"
            
            print(f"Starting MCP server: {python_exe} {self.mcp_server_path}")
            
            # Start the process
            self.process = subprocess.Popen(
                [python_exe, str(self.mcp_server_path)],
                cwd=str(self.script_dir),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0  # Unbuffered
            )
            
            print(f"✅ MCP server started with PID: {self.process.pid}")
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if process is still running
            if self.process.poll() is None:
                print("✅ MCP server is running successfully")
                return True
            else:
                print("❌ MCP server failed to start")
                stdout, stderr = self.process.communicate()
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                self.process = None
                return False
                
        except Exception as e:
            print(f"❌ Failed to start MCP server: {e}")
            self.process = None
            return False
    
    def stop_server(self):
        """Stop the MCP server process"""
        if not self.process:
            return
        
        try:
            print("Stopping MCP server...")
            self.process.terminate()
            
            # Wait up to 5 seconds for graceful shutdown
            try:
                self.process.wait(timeout=5)
                print("✅ MCP server stopped gracefully")
            except subprocess.TimeoutExpired:
                print("⚠️ MCP server didn't stop gracefully, killing...")
                self.process.kill()
                self.process.wait()
                print("✅ MCP server killed")
                
        except Exception as e:
            print(f"❌ Error stopping MCP server: {e}")
        finally:
            self.process = None
    
    def is_running(self):
        """Check if MCP server is running"""
        return self.process is not None and self.process.poll() is None
    
    def get_status(self):
        """Get server status"""
        if self.is_running():
            return {
                "status": "running",
                "pid": self.process.pid,
                "server_path": str(self.mcp_server_path)
            }
        else:
            return {
                "status": "stopped",
                "server_path": str(self.mcp_server_path)
            }

def main():
    """Main function"""
    manager = MCPServerManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "start":
            success = manager.start_server()
            sys.exit(0 if success else 1)
            
        elif command == "stop":
            manager.stop_server()
            sys.exit(0)
            
        elif command == "status":
            status = manager.get_status()
            print(f"MCP Server Status: {status}")
            sys.exit(0)
            
        elif command == "restart":
            manager.stop_server()
            time.sleep(1)
            success = manager.start_server()
            sys.exit(0 if success else 1)
            
        else:
            print("Usage: python start_mcp_server.py [start|stop|status|restart]")
            sys.exit(1)
    else:
        # Default: start server and keep it running
        success = manager.start_server()
        if success:
            try:
                print("MCP server running. Press Ctrl+C to stop.")
                while manager.is_running():
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nReceived interrupt signal")
            finally:
                manager.stop_server()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()