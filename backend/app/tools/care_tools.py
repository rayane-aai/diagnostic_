import re

from app.tools.mcp_client import get_red_flags_via_mcp


RED_FLAG_KEYWORDS = {
    "dyspnee": [
        "dyspnee",
        "dyspnée",
        "respiratoire",
        "essoufflement",
        "difficulte a respirer",
        "difficulté à respirer",
        "gene respiratoire",
        "gêne respiratoire",
    ],
    "douleur_thoracique": [
        "douleur thoracique",
        "poitrine",
        "thorax",
    ],
    "confusion": [
        "confusion",
        "desorientation",
        "désorientation",
        "trouble de conscience",
    ],
    "perte_conscience": [
        "perte de conscience",
        "perte de connaissance",
        "malaise",
        "syncope",
    ],
    "fievre_persistante": [
        "fievre persistante",
        "fièvre persistante",
        "forte fievre",
        "forte fièvre",
        "fievre elevee",
        "fièvre élevée",
        "39",
        "39,5",
    ],
    "deshydratation": [
        "deshydratation",
        "déshydratation",
        "dehydratation",
        "dehydration",
        "urine rare",
        "bouche seche",
        "bouche sèche",
    ],
}


def clean_text_for_detection(text: str) -> str:
    """
    Nettoie le texte pour éviter de détecter les signes d'alerte présents
    dans les questions elles-mêmes.
    On garde le cas initial et les réponses, mais on ignore les lignes de questions.
    """
    useful_lines: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        lowered = line.lower()

        if not line:
            continue

        # Ignorer les questions, car elles contiennent déjà les mots red flags.
        if re.match(r"^(q\d+|question)\s*[:.\-]", lowered):
            continue

        # Garder seulement le contenu après "Réponse:" ou "R1."
        match = re.match(
            r"^(r[eé]ponse|r\d+|answer)\s*[:.\-]\s*(.+)$",
            line,
            flags=re.IGNORECASE,
        )
        if match:
            useful_lines.append(match.group(2))
            continue

        useful_lines.append(line)

    return "\n".join(useful_lines)


def local_red_flag_detection(text: str) -> list[str]:
    cleaned_text = clean_text_for_detection(text)
    lowered = cleaned_text.lower()

    flags: list[str] = []

    for label, keywords in RED_FLAG_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            flags.append(label)

    return flags


async def detect_red_flags(symptom_text: str) -> dict:
    """
    Utilise la détection MCP/fonction outil.
    En cas d'échec, garde le backend utilisable avec une vérification locale.
    """
    cleaned_text = clean_text_for_detection(symptom_text)

    try:
        # IMPORTANT : pas de await ici, car get_red_flags_via_mcp n'est pas async.
        result = get_red_flags_via_mcp(cleaned_text)

        if isinstance(result, dict):
            red_flags = result.get("red_flags", [])
            mcp_status = result.get("mcp_status", "ok")
        else:
            red_flags = result or []
            mcp_status = "ok"

        return {
            "red_flags": red_flags,
            "mcp_status": mcp_status,
        }

    except Exception as exc:
        return {
            "red_flags": local_red_flag_detection(symptom_text),
            "mcp_status": f"fallback_local_check: {type(exc).__name__}",
        }


def recommend_interim_care(red_flags: list[str]) -> str:
    """Generate a cautious, non-diagnostic interim recommendation."""
    base = [
        "Orientation clinique preliminaire uniquement.",
        "Repos, hydratation et surveillance de l'evolution des symptomes.",
        "Eviter l'automedication risquee et demander un avis medical en cas de doute.",
    ]

    if red_flags:
        base.append(
            "Des signes d'alerte possibles ont ete identifies. "
            "Une consultation medicale rapide est recommandee, surtout en cas d'aggravation."
        )
    else:
        base.append(
            "Aucun signe d'alerte evident n'a ete detecte dans les informations fournies, "
            "mais la prudence reste necessaire."
        )

    base.append("Ce systeme ne remplace pas une consultation medicale.")

    return "\n".join(base)