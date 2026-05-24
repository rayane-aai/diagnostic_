import requests
import streamlit as st

st.set_page_config(
    page_title="Diagnostic Médical LangGraph",
    page_icon="🩺",
    layout="wide",
)

DEFAULT_API_URL = "http://127.0.0.1:8000"


def init_state() -> None:
    defaults = {
        "api_url": DEFAULT_API_URL,
        "thread_id": None,
        "status": "not_started",
        "interrupt": None,
        "state": {},
        "final_report": None,
        "initial_case": "",
        "history": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def api_post(path: str, payload: dict) -> dict:
    url = st.session_state.api_url.rstrip("/") + path
    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def api_get(path: str) -> dict:
    url = st.session_state.api_url.rstrip("/") + path
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.json()


def save_api_result(data: dict) -> None:
    st.session_state.thread_id = data.get("thread_id", st.session_state.thread_id)
    st.session_state.status = data.get("status", st.session_state.status)
    st.session_state.interrupt = data.get("interrupt")
    st.session_state.state = data.get("state", st.session_state.state or {})

    final_report = st.session_state.state.get("final_report")
    if final_report:
        st.session_state.final_report = final_report
        st.session_state.status = "completed"


def start_consultation(initial_case: str) -> None:
    data = api_post("/consultation/start", {"initial_case": initial_case})
    save_api_result(data)
    st.session_state.history = [
        {"role": "patient", "content": f"Cas initial : {initial_case}"}
    ]


def resume_consultation(answer: str, role: str) -> None:
    if not st.session_state.thread_id:
        st.error("Aucune consultation active.")
        return

    data = api_post(
        "/consultation/resume",
        {
            "thread_id": st.session_state.thread_id,
            "response": answer,
            "role": role,
        },
    )
    st.session_state.history.append({"role": role, "content": answer})
    save_api_result(data)


def refresh_report() -> None:
    if not st.session_state.thread_id:
        return
    data = api_get(f"/consultation/{st.session_state.thread_id}/report")
    st.session_state.final_report = data.get("final_report")


def reset_consultation() -> None:
    for key in [
        "thread_id",
        "status",
        "interrupt",
        "state",
        "final_report",
        "initial_case",
        "history",
    ]:
        if key in st.session_state:
            del st.session_state[key]
    init_state()


def render_sidebar() -> None:
    with st.sidebar:
        st.title("🩺 Diagnostic Médical")
        st.caption("Projet académique LangGraph + FastAPI + MCP")

        st.session_state.api_url = st.text_input(
            "URL Backend FastAPI",
            value=st.session_state.api_url,
        )

        if st.button("Tester le backend"):
            try:
                health = api_get("/health")
                st.success(f"Backend connecté : {health.get('status', 'ok')}")
            except Exception as exc:
                st.error(f"Backend inaccessible : {exc}")

        st.divider()
        st.write("**Thread ID**")
        st.code(st.session_state.thread_id or "Aucune consultation")

        st.write("**Statut**")
        st.info(st.session_state.status)

        if st.button("Nouvelle consultation"):
            reset_consultation()
            st.rerun()


def render_stepper() -> None:
    state = st.session_state.state or {}
    question_count = state.get("question_count", 0)
    has_physician = bool(state.get("physician_treatment"))
    has_report = bool(state.get("final_report") or st.session_state.final_report)

    cols = st.columns(4)
    cols[0].metric("1. Cas initial", "OK" if st.session_state.thread_id else "À faire")
    cols[1].metric("2. Questions patient", f"{question_count}/5")
    cols[2].metric("3. Revue médecin", "OK" if has_physician else "À faire")
    cols[3].metric("4. Rapport final", "OK" if has_report else "À faire")


def render_start_screen() -> None:
    st.header("1. Saisie du cas initial patient")
    st.write("Entrez le cas initial pour démarrer le workflow LangGraph.")

    initial_case = st.text_area(
        "Cas initial",
        value=st.session_state.initial_case,
        placeholder="Exemple : Patient de 25 ans avec toux, fatigue et fièvre légère depuis 2 jours.",
        height=140,
    )

    if st.button("Démarrer la consultation", type="primary"):
        if not initial_case.strip():
            st.warning("Veuillez saisir un cas initial.")
        else:
            try:
                st.session_state.initial_case = initial_case.strip()
                start_consultation(initial_case.strip())
                st.rerun()
            except Exception as exc:
                st.error(f"Erreur lors du démarrage : {exc}")


def render_patient_question(interrupt: dict) -> None:
    st.header("2. Questions / réponses patient")

    question_number = interrupt.get("question_number", "?")
    total_questions = interrupt.get("total_questions", 5)
    question = interrupt.get("question", "Question non disponible")

    st.info(f"Question {question_number}/{total_questions}")
    st.subheader(question)

    answer = st.text_area(
        "Réponse du patient",
        key=f"patient_answer_{question_number}",
        placeholder="Écrivez la réponse du patient ici...",
        height=100,
    )

    if st.button("Envoyer la réponse patient", type="primary"):
        if not answer.strip():
            st.warning("Veuillez saisir une réponse.")
        else:
            try:
                resume_consultation(answer.strip(), role="patient")
                st.rerun()
            except Exception as exc:
                st.error(f"Erreur lors de l'envoi : {exc}")


def render_physician_review(interrupt: dict) -> None:
    st.header("3. Revue du médecin traitant")

    st.warning("Human-in-the-Loop : le médecin doit valider et proposer une conduite à tenir.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Synthèse clinique préliminaire")
        st.text_area(
            "Synthèse",
            value=interrupt.get("diagnostic_summary", ""),
            height=260,
            disabled=True,
        )

    with col2:
        st.subheader("Recommandation intermédiaire")
        st.text_area(
            "Recommandation",
            value=interrupt.get("interim_care", ""),
            height=180,
            disabled=True,
        )
        red_flags = interrupt.get("mcp_red_flags", [])
        st.write("**Signes d'alerte MCP :**")
        if red_flags:
            for flag in red_flags:
                st.error(flag)
        else:
            st.success("Aucun signe d'alerte détecté")

    treatment = st.text_area(
        "Traitement ou conduite à tenir proposé par le médecin",
        placeholder="Exemple : Repos, hydratation, surveillance 48h, consultation si aggravation...",
        height=120,
    )

    if st.button("Valider la revue médecin", type="primary"):
        if not treatment.strip():
            st.warning("Veuillez saisir la conduite à tenir du médecin.")
        else:
            try:
                resume_consultation(treatment.strip(), role="physician")
                st.rerun()
            except Exception as exc:
                st.error(f"Erreur lors de la validation médecin : {exc}")


def render_report_screen() -> None:
    st.header("4. Rapport final")

    if not st.session_state.final_report:
        try:
            refresh_report()
        except Exception:
            pass

    if st.session_state.final_report:
        st.success("Rapport final généré avec succès.")
        st.text_area(
            "Rapport final structuré",
            value=st.session_state.final_report,
            height=520,
        )
        st.download_button(
            "Télécharger le rapport (.txt)",
            data=st.session_state.final_report,
            file_name=f"rapport_{st.session_state.thread_id}.txt",
            mime="text/plain",
        )
    else:
        st.info("Le rapport final n'est pas encore disponible.")


def render_state_debug() -> None:
    with st.expander("Voir l'état du graphe"):
        st.json(st.session_state.state or {})


def render_history() -> None:
    with st.expander("Historique des réponses"):
        if not st.session_state.history:
            st.write("Aucun historique pour le moment.")
            return
        for item in st.session_state.history:
            role = item.get("role", "user")
            content = item.get("content", "")
            st.write(f"**{role} :** {content}")


def main() -> None:
    init_state()
    render_sidebar()

    st.title("Système multi-agents d'orientation clinique")
    st.caption("Ce système ne remplace pas une consultation médicale.")

    render_stepper()
    st.divider()

    interrupt = st.session_state.interrupt

    if st.session_state.final_report or st.session_state.status == "completed":
        render_report_screen()
    elif not st.session_state.thread_id:
        render_start_screen()
    elif isinstance(interrupt, dict) and interrupt.get("type") == "patient_question":
        render_patient_question(interrupt)
    elif isinstance(interrupt, dict) and interrupt.get("type") == "physician_review":
        render_physician_review(interrupt)
    else:
        st.header("Workflow en cours")
        st.info("Le graphe est en cours d'exécution. Actualisez ou consultez l'état du graphe.")
        if st.button("Actualiser la consultation"):
            try:
                data = api_get(f"/consultation/{st.session_state.thread_id}")
                st.session_state.state = data.get("state", {})
                if st.session_state.state.get("final_report"):
                    st.session_state.final_report = st.session_state.state["final_report"]
                st.rerun()
            except Exception as exc:
                st.error(f"Erreur d'actualisation : {exc}")

    st.divider()
    render_history()
    render_state_debug()


if __name__ == "__main__":
    main()
