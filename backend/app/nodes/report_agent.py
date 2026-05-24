from app.state import MedicalState


def _format_answers(patient_answers: list[dict[str, str]]) -> str:
    if not patient_answers:
        return "Aucune reponse patient enregistree."
    return "\n".join(
        f"{index}. Question: {item['question']}\n   Reponse: {item['answer']}"
        for index, item in enumerate(patient_answers, start=1)
    )


def report_agent_node(state: MedicalState) -> dict:
    """Create the final structured report."""
    report = f"""
RAPPORT FINAL D'ORIENTATION CLINIQUE

1. Informations initiales du patient
{state.get('initial_case', 'Non renseigne')}

2. Questions et reponses patient
{_format_answers(state.get('patient_answers', []))}

3. Synthese clinique preliminaire
{state.get('diagnostic_summary', 'Non generee')}

4. Recommandation intermediaire
{state.get('interim_care', 'Non generee')}

5. Revue du medecin traitant
{state.get('physician_treatment', 'Non renseignee')}

6. Trace MCP
Statut MCP: {state.get('mcp_status', 'non renseigne')}
Signes d'alerte MCP: {', '.join(state.get('mcp_red_flags', [])) or 'aucun'}

7. Conclusion
Ce rapport est produit dans un cadre academique pour simuler un workflow d'orientation clinique.
Ce systeme ne remplace pas une consultation medicale.
""".strip()
    return {"final_report": report, "next": "FINISH"}
