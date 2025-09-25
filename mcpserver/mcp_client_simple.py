"""
Simple MCP Client for Filesystem Server
Handles stdio transport connection to fs_server.py
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class SimpleMCPClient:
    """Simple client for connecting to the MCP filesystem server via stdio transport."""
    
    def __init__(self, config_file: str = "server/fs.json"):
        """Initialize the MCP client with configuration."""
        self.config_file = config_file
        self._load_config()
    
    def _load_config(self):
        """Load MCP server configuration from fs.json."""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Extract filesystem server configuration
            fs_config = config["mcpServers"]["filesystem"]
            self.command = fs_config["command"]
            self.args = fs_config["args"]
            self.cwd = fs_config["cwd"]   ## "/home/keerthichavlavandana/mcp2/mcpserver"
            self.env = fs_config.get("env", {})
            
            print(f"✅ Loaded MCP config: {self.command} {' '.join(self.args)}")
            print(f"   Working directory: {self.cwd}")
            print(f"   Environment: {self.env}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load MCP config from {self.config_file}: {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a specific tool on the MCP server."""
        try:
            # Set up server parameters for stdio transport
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                cwd=self.cwd,
                env=self.env
            )
            
            print(f"🔧 Calling tool: {tool_name} with args: {arguments}")
            '''
            📝 stdin: Client sends JSON-RPC requests to server
            📤 stdout: Server sends JSON-RPC responses to client
            stdin:  {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "list_directory",
                        "arguments": {"path": "Desktop"}
                    }
                }


            stdio:  server sent back results
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "content": [{"text": "[{\"name\": \"file1.txt\", \"is_dir\": false, \"size\": 1024}]"}]
                }
                }
            '''    
            # # This creates the stdio transport connection
            async with stdio_client(server_params) as (read_stream, write_stream):
                #JSON-RPC 2.0 protocol is handled by the MCP library
                async with ClientSession(read_stream, write_stream) as session:
                    # Initialize the connection
                    await session.initialize()
                    
                    # Call the tool
                    result = await session.call_tool(tool_name, arguments)
                    
                    # Extract text content from result
                    if result.content and len(result.content) > 0:
                        return result.content[0].text
                    else:
                        return "No content returned from tool."
                        
        except Exception as e:
            error_msg = f"Error calling tool '{tool_name}': {e}"
            print(f"❌ {error_msg}")
            return error_msg
    
    async def list_directory(self, path: str = ".") -> str:
        """List directory contents."""
        return await self.call_tool("list_directory", {"path": path})
    
    async def read_file(self, path: str) -> str:
        """Read file contents."""
        return await self.call_tool("read_file", {"path": path})
    
    async def write_file(self, path: str, content: str) -> str:
        """Write content to file."""
        return await self.call_tool("write_file", {"path": path, "content": content})
    
    async def create_directory(self, path: str) -> str:
        """Create a new directory."""
        return await self.call_tool("create_directory", {"path": path})
    
    async def delete_file(self, path: str) -> str:
        """Delete a file or directory."""
        return await self.call_tool("delete_file", {"path": path})
    
    async def search_files(self, directory: str, pattern: str) -> str:
        """Search for files by name pattern."""
        return await self.call_tool("search_files", {"directory": directory, "pattern": pattern})
    
    async def search_in_files(self, directory: str, query: str) -> str:
        """Search for text within files."""
        return await self.call_tool("search_in_files", {"directory": directory, "query": query})
    
    async def get_file_info(self, path: str) -> str:
        """Get file information and metadata."""
        return await self.call_tool("get_file_info", {"path": path})
    
    async def copy_file(self, source: str, destination: str) -> str:
        """Copy a file."""
        return await self.call_tool("copy_file", {"source": source, "destination": destination})
    
    async def move_file(self, source: str, destination: str) -> str:
        """Move or rename a file."""
        return await self.call_tool("move_file", {"source": source, "destination": destination})
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [
            "list_directory", "read_file", "write_file", "create_directory",
            "delete_file", "search_files", "search_in_files", "get_file_info",
            "copy_file", "move_file"
        ]


# Test function
async def test_simple_mcp_client():
    """Test the simple MCP client connection and basic functionality."""
    client = SimpleMCPClient()
    
    print("\n🧪 Testing simple MCP client...")
    
    # Test list directory
    result = await client.list_directory(".")
    print(f"📁 Current directory contents:\n{result}")
    
    # Test list Desktop
    result = await client.list_directory("Desktop")
    print(f"🖥️  Desktop contents:\n{result}")
    
    print("✅ Simple MCP client test completed!")


if __name__ == "__main__":
    asyncio.run(test_simple_mcp_client())
