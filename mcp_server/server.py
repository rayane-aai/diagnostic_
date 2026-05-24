from __future__ import annotations

from typing import Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("medical_orientation_tools")

RED_FLAG_WORDS = [
    "douleur thoracique",
    "essoufflement",
    "confusion",
    "malaise",
    "perte de connaissance",
    "saignement",
    "paralysie",
    "grossesse",
    "fievre elevee",
    "fièvre élevée",
    "difficulte respiratoire",
    "difficulté respiratoire",
]


def _flatten(case_text: str, answers: list[dict[str, Any]] | None) -> str:
    text = case_text or ""

    for item in answers or []:
        text += "\n"
        text += str(item.get("question", ""))
        text += " "
        text += str(item.get("answer", ""))

    return text.lower()


@mcp.tool(name="recommend_interim_care")
def recommend_interim_care(case_text: str, answers: list[dict[str, Any]] | None = None) -> str:
    """
    Outil MCP qui produit une recommandation intermediaire prudente
    pour un workflow academique d'orientation clinique.
    """

    text = _flatten(case_text, answers)
    has_red_flag = any(word in text for word in RED_FLAG_WORDS)

    if has_red_flag:
        return (
            "Recommandation intermediaire generale: des signes d'alerte sont presents ou possibles. "
            "Le patient doit etre oriente vers une consultation medicale rapide, voire les urgences "
            "en cas d'essoufflement, douleur thoracique, confusion, malaise, saignement important "
            "ou aggravation. Cette recommandation reste prudente et ne remplace pas l'avis du medecin."
        )

    return (
        "Recommandation intermediaire generale: repos relatif, hydratation, surveillance de l'evolution, "
        "mesure de la temperature si fievre, et consultation si les symptomes persistent ou s'aggravent. "
        "Cette recommandation reste prudente et ne remplace pas l'avis du medecin."
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
