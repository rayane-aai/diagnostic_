from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from langgraph.types import Command
from pydantic import BaseModel, Field

from app.graph import api_graph as graph


app = FastAPI(
    title="Diagnostic Medical Multi-Agent API",
    description="Academic LangGraph workflow for preliminary clinical orientation. Not a medical device.",
    version="0.1.0",
)


class SessionResponse(BaseModel):
    thread_id: str


class ConsultationStartRequest(BaseModel):
    initial_case: str = Field(..., examples=["Patient de 25 ans avec toux et fievre depuis 2 jours."])
    thread_id: str | None = None


class ConsultationResumeRequest(BaseModel):
    thread_id: str
    response: str = Field(..., examples=["Les symptomes ont commence il y a 2 jours."])
    role: Literal["patient", "physician"] | None = None


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _interrupt_payload(result: Any) -> Any | None:
    if not isinstance(result, dict) or "__interrupt__" not in result:
        return None
    interrupts = result.get("__interrupt__") or []
    if not interrupts:
        return None
    first = interrupts[0]
    return getattr(first, "value", first)


def _snapshot(thread_id: str) -> dict:
    try:
        snapshot = graph.get_state(_config(thread_id))
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Consultation introuvable: {type(exc).__name__}") from exc
    return dict(snapshot.values or {})


def _response(thread_id: str, result: Any) -> dict:
    interrupt_payload = _interrupt_payload(result)
    state = _snapshot(thread_id)
    status = "completed" if state.get("final_report") else "waiting_input" if interrupt_payload else "running"
    return {
        "thread_id": thread_id,
        "status": status,
        "interrupt": interrupt_payload,
        "state": state,
    }


@app.post("/sessions/start", response_model=SessionResponse, tags=["sessions"])
async def start_session() -> SessionResponse:
    return SessionResponse(thread_id=str(uuid4()))


@app.post("/consultation/start", tags=["consultation"])
async def start_consultation(payload: ConsultationStartRequest) -> dict:
    thread_id = payload.thread_id or str(uuid4())
    initial_state = {
        "thread_id": thread_id,
        "initial_case": payload.initial_case,
        "question_count": 0,
        "patient_answers": [],
        "next": "diagnostic_agent",
    }
    result = await graph.ainvoke(initial_state, config=_config(thread_id))
    return _response(thread_id, result)


@app.post("/consultation/resume", tags=["consultation"])
async def resume_consultation(payload: ConsultationResumeRequest) -> dict:
    result = await graph.ainvoke(Command(resume=payload.response), config=_config(payload.thread_id))
    return _response(payload.thread_id, result)


@app.get("/consultation/{thread_id}", tags=["consultation"])
async def get_consultation(thread_id: str) -> dict:
    state = _snapshot(thread_id)
    return {"thread_id": thread_id, "state": state}


@app.get("/consultation/{thread_id}/report", tags=["consultation"])
async def get_report(thread_id: str) -> dict:
    state = _snapshot(thread_id)
    report = state.get("final_report")
    if not report:
        raise HTTPException(status_code=404, detail="Le rapport final n'est pas encore disponible.")
    return {"thread_id": thread_id, "final_report": report}


@app.get("/health", tags=["system"])
async def health() -> dict:
    return {"status": "ok"}
