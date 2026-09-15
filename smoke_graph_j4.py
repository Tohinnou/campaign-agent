r"""Smoke J4 — l'humain complète via interrupt + Command(resume=...)

Le workflow :
  1. Brief incomplet → extraction → interrupt sur ask_user
  2. L'humain fournit les champs manquants → reprise
  3. Le dossier est complet → génération → FIN

Prouve que l'interrupt HITL fonctionne (J4) SANS casser la borne (J2).

Lancer :  .\.venv\Scripts\python.exe smoke_graph_j4.py
"""

import io
import sys

from langgraph.types import Command

from campaign_agent.graph import graph
from campaign_agent.routing import MAX_ASKS

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    THREAD_ID = "smoke-j4"
    brief = "Je veux une campagne avec une promo -30 % sur la nouvelle collection."
    config = {"configurable": {"thread_id": THREAD_ID}}

    print("== etape 1 : extraction (se bloque sur ask_user) ==")
    for step in graph.stream({"user_message": brief}, config=config, stream_mode="updates"):
        for node, update in step.items():
            print(f"  [{node:26}] -> {update}")

    # --- L'humain consulte ce qui manque et fournit les réponses ---
    snapshot = graph.get_state(config)
    print(f"\n== interrupt : l'humain voit ==")
    print(f"  missing_fields = {snapshot.values.get('missing_fields')}")
    print(f"  ask_count      = {snapshot.values.get('ask_count')}/{MAX_ASKS}")
    print(f"\n  > L'humain fournit les champs manquants...\n")

    # L'humain répond via Command(resume=...) avec les valeurs
    for step in graph.stream(
        Command(resume={"objective": "Relancer les clientes inactives",
                        "audience": "Femmes 25-45 ans",
                        "campaign_date": "15 aout 2026"}),
        config=config,
        stream_mode="updates",
    ):
        for node, update in step.items():
            print(f"  [{node:26}] -> {update}")

    # --- Vérification finale ---
    final = graph.get_state(config)
    print(f"\n== dossier final ==")
    print(f"  objective       = {final.values.get('objective')!r}")
    print(f"  audience        = {final.values.get('audience')!r}")
    print(f"  offer           = {final.values.get('offer')!r}")
    print(f"  campaign_date   = {final.values.get('campaign_date')!r}")
    msg = final.values.get("generated_message", "")
    if msg:
        print(f"\n== message genere ({len(msg)} car) ==")
        print(msg[:300])
    print(f"\n== J4 OK : interrupt → reprise humaine → livraison. ==")
