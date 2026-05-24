# Diagnostic Medical


## Architecture

```
diagnostic_medical_langgraph/
├── backend/                  # API FastAPI + graphe LangGraph
│   ├── app/
│   │   ├── graph.py          # Définition du StateGraph
│   │   ├── state.py          # MedicalState partagé
│   │   ├── api.py            # Endpoints FastAPI
│   │   ├── nodes/            # Agents : supervisor, diagnostic, physician, report
│   │   └── tools/            # Outils LangChain + client MCP
│   ├── langgraph.json        # Configuration LangGraph CLI
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/                 # Interface Streamlit
│   ├── streamlit_app.py
│   └── requirements.txt
└── mcp_server/               # Serveur MCP (recommandations intermédiaires)
    └── server.py
```

Le graphe enchaîne quatre nœuds :

```
START → supervisor → diagnostic_agent → supervisor
                   → physician_review → supervisor
                   → report_agent    → supervisor → END
```

---


## Installation

###  Backend

```bash
cd backend

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend

```bash
cd ../frontend
pip install -r requirements.txt
```

---

## Configuration

## Lancement

### 1. Démarrer le backend (FastAPI)

Depuis le dossier `backend/` avec l'environnement virtuel activé :

```bash
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

L'API est accessible sur [http://localhost:8000](http://localhost:8000).  
La documentation interactive Swagger est disponible sur [http://localhost:8000/docs](http://localhost:8000/docs).

#### Alternative — LangGraph CLI

Si vous souhaitez utiliser la CLI LangGraph pour le développement :

```bash
pip install langgraph-cli
langgraph dev
```

### 2. Démarrer le frontend (Streamlit)

Dans un nouveau terminal, depuis le dossier `frontend/` :

```bash
streamlit run streamlit_app.py
```

L'interface est accessible sur [http://localhost:8501](http://localhost:8501).

### 3. Serveur MCP (optionnel)

Le serveur MCP est lancé automatiquement par le backend via `subprocess` (transport `stdio`). Si vous souhaitez le tester isolément :

```bash
cd mcp_server
python server.py
```
