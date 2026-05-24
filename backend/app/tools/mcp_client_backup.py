import json
import os
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SERVER_PATH = PROJECT_ROOT / "mcp_server" / "server.py"


def _extract_text_content(result: Any) -> str:
    """Best effort extraction for MCP tool results across SDK versions."""
    content = getattr(result, "content", None)
    if content:
        first = content[0]
        return getattr(first, "text", str(first))
    structured = getattr(result, "structured_content", None) or getattr(result, "structuredContent", None)
    if structured is not None:
        return json.dumps(structured)
    return str(result)


async def get_red_flags_via_mcp(symptoms: str) -> dict[str, Any]:
    """Call the MCP red flag tool through stdio."""
    server_path = Path(os.getenv("MCP_SERVER_PATH", str(DEFAULT_SERVER_PATH)))
    params = StdioServerParameters(
        command="python",
        args=[str(server_path)],
        env=None,
    )

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("get_red_flags", {"symptoms": symptoms})
            text = _extract_text_content(result)
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"raw": text, "red_flags": [], "mcp_status": "parsed_as_text"}
