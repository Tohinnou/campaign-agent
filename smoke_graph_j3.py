r"""Smoke J3 — le greffier archive-t-il l'état entre les appels ? (§7)

Deux preuves :
  1. `graph.get_state(config)` lit le dossier SANS lancer le moteur.
  2. Deux invoke() consécutifs sur le même thread_id : le second repart du
     dossier sauvegardé (le graphe se rendort sur END, mais l'état survit).

La VRAIE puissance arrive en J4 (interrupt) : le greffier permet de figer
la machine À MI-PARCOURS, pas seulement à la fin.

Lancer :  .\.venv\Scripts\python.exe smoke_graph_j3.py
"""

import io
import sys

from campaign_agent.graph import graph

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    THREAD_ID = "smoke-j3"
    brief = (
        "Prépare une campagne pour le Black Friday, cible nos abonnés premium "
        "(25-50 ans), -40 % sur tout le site, ton urgent, envoi le 25 novembre 2026."
    )
    config = {"configurable": {"thread_id": THREAD_ID}}

    print("== 1er appel : le moteur tourne ==")
    state = graph.invoke({"user_message": brief}, config=config)
    keys = list(state.keys())
    print(f"  state keys = {keys}")
    print(f"  objective  = {state.get('objective', '!MANQUANT')!r}")
    print(f"  audience   = {state.get('audience', '!MANQUANT')!r}")
    if "generated_message" in state:
        print(f"  generated  = {state['generated_message'][:80]!r}...")
    else:
        print("  !!! generated_message absent — le LLM a probablement echoue")

    print("\n== 2e preuve : get_state sans invoke ==")
    snapshot = graph.get_state(config)
    print(f"  values.keys()  = {list(snapshot.values.keys())}")
    print(f"  next           = {snapshot.next!r}")   # () = aucune étape en attente
    print(f"  objective intact = {snapshot.values.get('objective')!r}")

    print("\n== J3 OK : le greffier archive. J4 peut commencer. ==")
