from app.state import MedicalState


DEFAULT_QUESTIONS = [
    "Depuis combien de temps les symptomes ont-ils commence ?",
    "Avez-vous de la fievre, une douleur importante ou une gene respiratoire ?",
    "Avez-vous des antecedents medicaux, allergies ou traitements en cours ?",
    "Les symptomes s'aggravent-ils, diminuent-ils ou restent-ils stables ?",
    "Y a-t-il un signe inquietant : douleur thoracique, confusion, malaise, perte de conscience ou dehydration ?",
]


def build_patient_question(state: MedicalState) -> str:
    """Return the next patient question. Exactly 5 questions are used for the project."""
    count = int(state.get("question_count", 0))
    if count < len(DEFAULT_QUESTIONS):
        return DEFAULT_QUESTIONS[count]
    return "Aucune question supplementaire."


def normalize_answer(answer: object) -> str:
    """Accept plain text or a JSON-like payload from the frontend."""
    if isinstance(answer, dict):
        return str(answer.get("answer") or answer.get("response") or answer)
    return str(answer)
