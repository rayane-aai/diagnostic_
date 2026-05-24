from app.tools.mcp_client import call_mcp_interim_care

answers = [
    {
        "question": "Avez-vous des signes inquietants ?",
        "answer": "Oui, essoufflement au repos et douleur thoracique."
    }
]

result = call_mcp_interim_care(
    "Patient de 68 ans avec fievre elevee, toux importante, essoufflement et douleur thoracique.",
    answers
)

print(result)
