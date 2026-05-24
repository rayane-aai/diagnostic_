from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


RED_FLAG_KEYWORDS = [
    "douleur thoracique",
    "essoufflement",
    "difficulte respiratoire",
    "difficulté respiratoire",
    "confusion",
    "malaise",
    "perte de connaissance",
    "perte de conscience",
    "saignement",
    "paralysie",
    "fievre elevee",
    "fièvre élevée",
    "dehydration",
    "dehydratation",
    "déshydratation",
    "39",
    "39,5",
    "urgence",
]


def _flatten(case_text: str, answers: list[dict[str, Any]] | None = None) -> str:
    text = case_text or ""

    for item in answers or []:
        text += "\n"
        text += str(item.get("question", ""))
        text += " "
        text += str(item.get("answer", ""))

    return text.lower()


async def _call_mcp_recommend(case_text: str, answers: list[dict[str, Any]] | None = None) -> str:
    project_root = Path(__file__).resolve().parents[3]
    server_path = project_root / "mcp_server" / "server.py"

    params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
    )

    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                "recommend_interim_care",
                {
                    "case_text": case_text,
                    "answers": answers or [],
                },
            )

            chunks = []

            for item in getattr(result, "content", []) or []:
                text = getattr(item, "text", None)
                if text:
                    chunks.append(text)

            return "\n".join(chunks).strip()


def get_red_flags_via_mcp(case_text: str, answers: list[dict[str, Any]] | None = None) -> list[str]:
    """
    Fonction utilisee par care_tools.py.
    Elle detecte les signes d'alerte a partir du cas patient et des reponses.
    """

    text = _flatten(case_text, answers)
    found = []

    for keyword in RED_FLAG_KEYWORDS:
        if keyword in text:
            found.append(keyword)

    return found


def call_mcp_interim_care(case_text: str, answers: list[dict[str, Any]] | None = None) -> str:
    """
    Appelle l'outil MCP recommend_interim_care.
    En cas de probleme, retourne une recommandation prudente de secours.
    """

    try:
        value = asyncio.run(_call_mcp_recommend(case_text, answers or []))

        if value:
            return value

    except Exception as exc:
        return (
            "Recommandation intermediaire generale: repos relatif, hydratation, "
            "surveillance des symptomes et consultation rapide en cas d'aggravation. "
            f"Note technique MCP: appel non disponible ({exc})."
        )

    return (
        "Recommandation intermediaire generale: repos relatif, hydratation, "
        "surveillance des symptomes et consultation rapide en cas d'aggravation."
    )
