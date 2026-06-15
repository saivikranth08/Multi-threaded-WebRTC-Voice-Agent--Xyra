from fastmcp import FastMCP
from xyra.tools.system import register_system_tools
from xyra.tools.web import register_web_tools
from xyra.tools.communication import register_communication_tools

# Create the XYRA MCP server
mcp = FastMCP(
    name="XYRA",
    instructions="You are XYRA, an intelligent AI assistant. Use the available tools to help the user."
)

# ── Register Tools ────────────────────────────
register_system_tools(mcp)
register_web_tools(mcp)
register_communication_tools(mcp)

# ── Run the server ────────────────────────────
def main():
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()
