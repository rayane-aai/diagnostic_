from langgraph.types import interrupt

from app.state import MedicalState
from app.tools.care_tools import detect_red_flags, recommend_interim_care
from app.tools.patient_tools import build_patient_question, normalize_answer


TOTAL_QUESTIONS = 5


def _format_answers(patient_answers: list[dict[str, str]]) -> str:
    lines = []
    for index, item in enumerate(patient_answers, start=1):
        lines.append(f"Q{index}. {item['question']}\nR{index}. {item['answer']}")
    return "\n".join(lines)


def _build_summary(initial_case: str, patient_answers: list[dict[str, str]], red_flags: list[str]) -> str:
    answers_text = _format_answers(patient_answers)
    flags_text = ", ".join(red_flags) if red_flags else "aucun signe d'alerte evident declare"
    return (
        "Synthese clinique preliminaire academique\n"
        f"Cas initial: {initial_case}\n\n"
        "Reponses patient:\n"
        f"{answers_text}\n\n"
        f"Signes d'alerte reperes: {flags_text}.\n"
        "Cette synthese est une orientation preliminaire et ne constitue pas un diagnostic definitif."
    )


async def diagnostic_agent_node(state: MedicalState) -> dict:
    """Ask exactly 5 patient questions, then produce a preliminary summary."""
    question_count = int(state.get("question_count", 0))
    patient_answers = list(state.get("patient_answers", []))

    if question_count < TOTAL_QUESTIONS:
        question = build_patient_question(state)
        raw_answer = interrupt(
            {
                "type": "patient_question",
                "question_number": question_count + 1,
                "total_questions": TOTAL_QUESTIONS,
                "question": question,
                "instruction": "Repondre a la question du patient pour continuer le workflow.",
            }
        )
        answer = normalize_answer(raw_answer)
        patient_answers.append({"question": question, "answer": answer})
        question_count += 1

    if question_count < TOTAL_QUESTIONS:
        return {
            "question_count": question_count,
            "patient_answers": patient_answers,
            "next": "diagnostic_agent",
        }

    symptom_text = state.get("initial_case", "") + "\n" + _format_answers(patient_answers)
    red_flag_result = await detect_red_flags(symptom_text)
    red_flags = list(red_flag_result.get("red_flags", []))
    summary = _build_summary(state.get("initial_case", ""), patient_answers, red_flags)
    interim = recommend_interim_care(red_flags)

    return {
        "question_count": question_count,
        "patient_answers": patient_answers,
        "diagnostic_summary": summary,
        "interim_care": interim,
        "mcp_red_flags": red_flags,
        "mcp_status": str(red_flag_result.get("mcp_status", "ok")),
        "next": "physician_review",
    }
