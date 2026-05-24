from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class MedicalState(TypedDict, total=False):
    """Shared graph state for the academic medical orientation workflow."""

    messages: Annotated[list, add_messages]
    next: Literal["diagnostic_agent", "physician_review", "report_agent", "FINISH"]

    thread_id: str
    initial_case: str
    question_count: int
    patient_answers: list[dict[str, str]]

    diagnostic_summary: str
    interim_care: str
    mcp_red_flags: list[str]
    mcp_status: str

    physician_treatment: str
    final_report: str
