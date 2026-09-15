r"""Smoke bout-en-bout — le graphe J1 tourne-t-il d'un bout à l'autre ? (§5)

Appel RÉEL (2 nodes LLM : understand_request + generate_campaign) → hors pytest.
On invoque la chaîne compilée sur un brief COMPLET et on lit le dossier final :
les 5 attributs extraits, le ton (comblé par la marque si l'utilisateur se tait),
missing_fields, et le message généré.

C'est le capstone de J1 : la preuve que les 4 nodes, câblés, forment une machine.

Lancer :  .\.venv\Scripts\python.exe smoke_graph.py
"""

import io
import sys

from campaign_agent.graph import graph

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    brief = (
        "Prépare une campagne pour relancer nos clientes inactives depuis 6 mois "
        "(femmes 25-45 ans, déjà clientes chez nous), avec une promo -30 % sur la "
        "nouvelle collection valable une semaine. Ton dynamique et chaleureux, "
        "à envoyer le 1er août 2026."
    )

    config = {"configurable": {"thread_id": "smoke-complete"}}
    final_state = graph.invoke({"user_message": brief}, config=config)

    print("== dossier final ==")
    for key in ("objective", "audience", "offer", "tone", "campaign_date", "missing_fields"):
        print(f"  {key:15} = {final_state.get(key)!r}")
    print("== message genere ==")
    print(final_state.get("generated_message"))
