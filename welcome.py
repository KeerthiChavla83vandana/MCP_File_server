from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP(
    name="Hello MCP Server",
    host="0.0.0.0",
    port=3000,
    stateless_http=True,
    debug=False,
)

@mcp.tool(
    title="Welcome a to AI Technologies",
    description="Return a friendly welcome message for the user.",
)
def welcome(
    name: str = Field(description="Name of the user")
) -> str:
    return f"Welcome {name} from this amazing application!"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")