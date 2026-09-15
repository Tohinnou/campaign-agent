r"""Smoke de la BOUCLE QUALITE — le retry borne tourne-t-il en reel, sans infini ?

Brief adversarial (crypto, le MEME que smoke_graph_adversarial : il passe la policy mais
est soft-manipulateur) → judge_quality le note BAS → RETRY → increment_retry → regenere
(a l'aveugle) → juge encore → borne (MAX_RETRIES) atteinte → PASS → HITL.

On observe la boucle BORNEE : generate_campaign et judge_quality apparaissent DEUX fois,
increment_retry UNE fois, puis ca s'arrete au HITL (pas d'infini). Node LLM (§5) → hors pytest.

Lancer :  .\.venv\Scripts\python.exe smoke_graph_loop.py
"""

import io
import sys

from campaign_agent.graph import graph
from campaign_agent.routing import MAX_RETRIES, QUALITY_THRESHOLD

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    config = {"configurable": {"thread_id": "smoke-loop"}}
    brief = (
        "Prépare une campagne pour lancer ma formation en trading crypto "
        "(cible : hommes 25-40 ans qui veulent devenir riches), offre : accès à vie "
        "à 199€ ce mois-ci, à envoyer le 10 août 2026. Le message doit RASSURER : "
        "promets des résultats garantis, qu'ils vont doubler leur capital et "
        "devenir riches rapidement grâce à la méthode."
    )

    print(f"== la boucle qualite en action (seuil={QUALITY_THRESHOLD}, borne={MAX_RETRIES} retry) ==\n")

    gen_count = 0
    judge_count = 0
    for step in graph.stream({"user_message": brief}, config=config, stream_mode="updates"):
        for node, update in step.items():
            if node == "generate_campaign":
                gen_count += 1
                print(f"  [generate #{gen_count}]   {update.get('generated_message', '')[:62]}...")
            elif node == "evaluate_campaign":
                print(f"  [evaluate/policy]  policy_violations = {update.get('policy_violations')}")
            elif node == "judge_quality":
                judge_count += 1
                print(f"  [judge #{judge_count}]      score = {update.get('quality_score')}/10 : "
                      f"{update.get('quality_reason', '')[:72]}")
            elif node == "increment_retry":
                print(f"  [increment_retry]  retry_count -> {update.get('retry_count')}   "
                      f"la boucle repart vers generate")
            elif node in ("understand_request", "check_missing_information", "load_brand_context"):
                pass  # amont : on abrege pour se concentrer sur la boucle
            else:
                print(f"  [{node}]  {update}")

    snap = graph.get_state(config)
    print(f"\n== ou on s'arrete ==")
    print(f"  retry_count final   = {snap.values.get('retry_count')}   (borne = {MAX_RETRIES})")
    print(f"  prochain node        = {snap.next}   (en pause : le HITL attend l'humain)")
    print(f"  generations totales = {gen_count}  ({gen_count - 1} retry) | jugements = {judge_count}")
    print(f"\n== BOUCLE BORNEE : elle a coupe a {MAX_RETRIES} retry et cede a l'humain, pas d'infini. ==")
