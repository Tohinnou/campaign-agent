r"""Smoke du SLICE COMPLET — les 5 etapes, de bout en bout, sur OpenRouter (chantier B, §1).

Difference avec smoke_graph.py (J1) : le HITL d'approbation est desormais cable. Un brief
COMPLET traverse donc tout le graphe et s'ARRETE sur request_human_approval (l'interrupt) —
le garde-fou central. On lit le Vibe Diff, puis l'humain approuve via Command(resume="approved")
et le dossier se scelle sur status="approved".

Ce que les tests ne montrent pas et que ceci prouve : les 5 etapes s'enchainent VRAIMENT avec
le vrai modele, jusqu'a la pause d'approbation et sa reprise. (understand_request +
generate_campaign = LLM reels → hors pytest, §5.)

API confirmee par sonde (LangGraph 1.2.9) : un invoke qui atteint interrupt() renvoie un dict
avec "__interrupt__" = liste d'Interrupt (payload dans .value) ; on reprend par
graph.invoke(Command(resume=...), config) sur le MEME thread_id.

Lancer :  .\.venv\Scripts\python.exe smoke_graph_slice.py
"""

import io
import sys

from langgraph.types import Command

from campaign_agent.graph import graph

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    config = {"configurable": {"thread_id": "smoke-slice-approve"}}
    brief = (
        "Prépare une campagne pour relancer nos clientes inactives depuis 6 mois "
        "(femmes 25-45 ans, déjà clientes chez nous), avec une promo -30 % sur la "
        "nouvelle collection valable une semaine. Ton dynamique et chaleureux, "
        "à envoyer le 1er août 2026."
    )

    print("== etape 1 : le graphe tourne (LLM reel) et s'arrete sur le HITL d'approbation ==")
    paused = graph.invoke({"user_message": brief}, config=config)

    print("  -- ce que le graphe a rempli en chemin --")
    for key in ("objective", "audience", "offer", "tone", "campaign_date"):
        print(f"    {key:14} = {paused.get(key)!r}")
    print(f"    missing_fields    = {paused.get('missing_fields')!r}")
    print(f"    policy_violations = {paused.get('policy_violations')!r}")
    print(f"    status (avant aval) = {paused.get('status')!r}")

    print("\n== interrupt : le Vibe Diff expose a l'humain (ce qu'il valide) ==")
    vibe = paused["__interrupt__"][0].value
    print("    -- message a envoyer --")
    print(f"    {vibe['generated_message']}")
    print(f"    -- brief auquel il repond --")
    print(f"    {vibe['brief']}")

    print("\n  > L'humain approuve : Command(resume='approved')\n")
    final = graph.invoke(Command(resume="approved"), config=config)

    print(f"== dossier final : status = {final.get('status')!r} ==")
    assert final.get("status") == "approved", "le HITL aurait du sceller 'approved'"
    print("== SLICE OK : comprehension -> generation -> policy(clean) -> aval humain -> approved ==")
