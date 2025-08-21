# NAI Project Planner

Lightweight Streamlit app that helps users define hardware projects via an agent-driven chat and saves a structured Markdown project document.

Quick start
- Install dependencies (Python 3.10+): `pip install -r requirements.txt` or use `pip install -e .` if available.
- Run the app: `streamlit run app.py`

What it does
- Conversational Product Manager agent guides users through requirements gathering.
- Engineer and PMO agents produce and maintain a Markdown project document at `project_docs/NAI_system_configuration.md`.
- Use the UI to view and download the generated project document.

Layout
- `app.py`: Streamlit frontend and session handling
- `naii_agents/agents.py`: Agent definitions and workflows
- `naii_agents/tools.py`: Document helpers (read/overwrite current doc)
- `project_docs/`: Generated Markdown project document