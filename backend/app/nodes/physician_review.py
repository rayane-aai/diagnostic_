from langgraph.types import interrupt

from app.state import MedicalState


def physician_review_node(state: MedicalState) -> dict:
    """Human-in-the-loop step for the physician treatment or care plan."""
    treatment = interrupt(
        {
            "type": "physician_review",
            "instruction": "Le medecin traitant doit proposer un traitement ou une conduite a tenir.",
            "diagnostic_summary": state.get("diagnostic_summary", ""),
            "interim_care": state.get("interim_care", ""),
            "mcp_red_flags": state.get("mcp_red_flags", []),
        }
    )
    if isinstance(treatment, dict):
        treatment_text = str(treatment.get("treatment") or treatment.get("response") or treatment)
    else:
        treatment_text = str(treatment)
    return {"physician_treatment": treatment_text, "next": "report_agent"}
