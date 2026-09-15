r"""Smoke J5 — observabilité LangSmith : traces, latence, arbre d'appel.

Preuves :
  1. Chaque `graph.invoke()` produit un run visible dans le projet.
  2. Chaque node est un sous-run avec sa latence individuelle.
  3. Les appels LLM (ChatOpenAI) sont visibles en feuille de l'arbre.
  4. On interroge les runs programmatiquement via le SDK.

Lancer :  .\.venv\Scripts\python.exe smoke_graph_j5.py

Nécessite LANGSMITH_API_KEY et LANGSMITH_TRACING=true dans le .env.
"""

import io
import sys
import uuid

from langsmith import Client

from campaign_agent.graph import graph

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    client = Client()
    project = "campaign-agent"

    # --- 1. Lancer le graphe (trace auto) ---
    print("== 1. Appel du graphe (trace envoyee automatiquement) ==")
    brief = (
        "Relance nos clientes inactives depuis 6 mois, femmes 25-45 ans, "
        "promo -30% sur la nouvelle collection valable une semaine, "
        "ton dynamique et chaleureux, envoi le 1er aout 2026."
    )
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    state = graph.invoke({"user_message": brief}, config=config)
    print(f"  thread_id    = {thread_id}")
    print(f"  message gen. = {len(state.get('generated_message', ''))} chars\n")

    # --- 2. Recuperer le run et ses sous-runs ---
    print("== 2. Arbre des traces ==")
    runs = list(client.list_runs(project_name=project, execution_order=1))
    if not runs:
        print("  ! Aucun run trouve dans LangSmith.")
        exit()

    top = runs[0]
    print(f"  {top.run_type:8} {top.name:28} statut={top.status}")

    def print_tree(run_id, depth=2, indent=2):
        """Affiche recursivement les sous-runs jusqu'aux appels LLM."""
        subs = list(client.list_runs(project_name=project, parent_run_id=run_id))
        for s in subs:
            lat = (s.end_time - s.start_time).total_seconds() * 1000 if s.end_time and s.start_time else 0
            print(f'  {" " * indent}{s.run_type:8} {s.name:28} {lat:6.0f}ms')
            if depth > 0:
                print_tree(s.id, depth - 1, indent + 4)

    print_tree(top.id)

    count = len(list(client.list_runs(project_name=project)))
    print(f"\n== J5 OK : {count} traces dans le projet ==")
