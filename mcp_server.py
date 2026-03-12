import asyncio
import os
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# 1. Initialize Core Server (No FastMCP Magic)
app = Server("LocalFileSystem")
ROOT_DIR = Path(os.getcwd())

# 2. Explicitly Define the Tool Schema
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="read_local_file",
            description="Reads the actual content of a file from the hard drive.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The name of the .py or .txt file to read"
                    }
                },
                "required": ["filename"]
            }
        )
    ]

# 3. Explicitly Handle the Tool Execution
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name != "read_local_file":
        raise ValueError(f"Unknown tool: {name}")

    filename = arguments.get("filename")
    if not filename:
        return [types.TextContent(type="text", text="Error: filename argument is required.")]

    file_path = ROOT_DIR / filename
    
    # Security check
    if not file_path.resolve().is_relative_to(ROOT_DIR.resolve()):
        return [types.TextContent(type="text", text="Error: Access denied.")]
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [types.TextContent(type="text", text=f.read())]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error reading file: {str(e)}")]

# 4. Run the Standard IO Server
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())