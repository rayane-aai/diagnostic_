from app.state import MedicalState


def supervisor_node(state: MedicalState) -> dict:
    """Route the workflow to the next required step."""
    if not state.get("diagnostic_summary"):
        return {"next": "diagnostic_agent"}
    if not state.get("physician_treatment"):
        return {"next": "physician_review"}
    if not state.get("final_report"):
        return {"next": "report_agent"}
    return {"next": "FINISH"}


def route_from_supervisor(state: MedicalState) -> str:
    return state.get("next", "diagnostic_agent")
