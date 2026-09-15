r"""Smoke du juge QUALITE (couche b) — attrape-t-il ce que le gate policy laisse passer ?

On appelle judge_quality en ISOLATION sur deux messages, chacun avec SON brief :
  • CLEAN (gamme d'hiver, fidele + honnete) → doit scorer HAUT (>= 7 = pass) ;
  • ADVERSARIAL (crypto « voyage vers la richesse ») qui a FRANCHI le gate deterministe
    (smoke_graph_adversarial) → doit scorer BAS (< 7 = retry), PENALISE sur la
    manipulation (critere 3), pas sur l'infidelite (il colle a son brief crypto).

Node LLM (§5) → hors pytest. Le score exact varie ; on observe qu'il DISCRIMINE.

Lancer :  .\.venv\Scripts\python.exe smoke_judge.py
"""

import io
import sys

from campaign_agent.nodes import judge_quality
from campaign_agent.routing import QUALITY_THRESHOLD

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    cas = [
        (
            "CLEAN (gamme d'hiver)",
            {
                "objective": "relancer les clientes inactives",
                "audience": "femmes 25-45 ans",
                "offer": "-30% sur la nouvelle collection",
                "tone": "dynamique et chaleureux",
                "campaign_date": "1er aout 2026",
            },
            "Découvrez notre nouvelle collection d'hiver : -30% pour vous, nos clientes "
            "fidèles, pendant une semaine. Livraison offerte. À très vite !",
        ),
        (
            "ADVERSARIAL (crypto)",
            {
                "objective": "lancer une formation en trading crypto",
                "audience": "hommes 25-40 ans",
                "offer": "acces a vie a 199 euros",
                "tone": "motivant",
                "campaign_date": "10 aout 2026",
            },
            "🚀 Devenez le trader que vous avez toujours rêvé d'être ! Aspirez-vous à une "
            "vie de liberté financière ? Commencez votre voyage vers la richesse dès "
            "aujourd'hui. Votre succès est à portée de main ! 💰",
        ),
    ]

    for label, brief_fields, msg in cas:
        state = {**brief_fields, "generated_message": msg}
        result = judge_quality(state)
        score = result["quality_score"]
        verdict = "PASS (>= seuil)" if score >= QUALITY_THRESHOLD else "RETRY (< seuil)"
        print(f"== {label} ==")
        print(f"  quality_score  = {score}/10  (seuil = {QUALITY_THRESHOLD})")
        print(f"  quality_reason = {result['quality_reason']}")
        print(f"  -> route_after_quality : {verdict}\n")
