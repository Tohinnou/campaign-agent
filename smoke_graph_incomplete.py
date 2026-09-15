r"""Smoke J2+J4 — la BORNE coupe-t-elle encore avec interrupt ? (§3, §1)

Brief volontairement INCOMPLET. L'humain répond à chaque interrupt mais ne
REMPLIT jamais les champs → la borne (MAX_ASKS) doit couper après N tours
au lieu de boucler à l'infini.

La gouvernance (§1) : le LLM ne décide pas de s'arrêter — c'est le code,
via route_after_check. L'interrupt ne change pas ça.

Lancer :  .\.venv\Scripts\python.exe smoke_graph_incomplete.py
"""

import io
import sys

from langgraph.types import Command

from campaign_agent.graph import graph
from campaign_agent.routing import MAX_ASKS

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    THREAD_ID = "smoke-incomplete"
    brief = "Je veux une campagne avec une promo -30 % sur la nouvelle collection."
    config = {"configurable": {"thread_id": THREAD_ID}}

    print(f"MAX_ASKS = {MAX_ASKS}\n")

    # --- 1er appel : extraction + interrupt sur ask_user ---
    print("== etape 1 : extraction (se bloque sur ask_user) ==")
    for step in graph.stream({"user_message": brief}, config=config, stream_mode="updates"):
        for node, update in step.items():
            print(f"  [{node:26}] -> {update}")

    # --- Boucle de reprises : on ne remplit JAMAIS → la borne doit couper ---
    for i in range(1, MAX_ASKS + 1):
        snapshot = graph.get_state(config)
        ask_count = snapshot.values.get("ask_count", 0)
        print(f"\n== interrupt #{i} (ask_count = {ask_count}) ==")
        print(f"  missing_fields = {snapshot.values.get('missing_fields')}")

        if snapshot.next == ():
            print("  --- FIN (aucune tache en attente) ---")
            break

        # Reprendre avec un champ vide que l'humain ne remplit pas.
        # Le dict doit être non-vide sinon LangGraph ne voit pas le resume.
        resume_value = {"objective": ""}
        for step in graph.stream(Command(resume=resume_value), config=config, stream_mode="updates"):
            for node, update in step.items():
                if node == "__interrupt__":
                    continue  # on les affiche à part dans la boucle
                print(f"  [{node:26}] -> {update}")

    final = graph.get_state(config)
    print(f"\n== verdict ==")
    ask_count = final.values.get("ask_count", 0)
    print(f"  ask_count = {ask_count} (plafond {MAX_ASKS})")
    print(f"  next      = {final.next!r} (vide = END)")
    print(f"  La borne a coupe. Boucle infinie evitee.")
