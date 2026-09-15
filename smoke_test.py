r"""Smoke test — la plomberie OpenRouter répond-elle ? (§5 r2)

Hors suite pytest : c'est un appel RÉEL au modèle (coût + réseau + non-déterministe).
But unique : confirmer que `.env` → clé → `ChatOpenAI` pointé sur OpenRouter
renvoie bien une réponse, AVANT de bâtir le moindre node dessus. Voir l'eau couler.

Lancer :  .\.venv\Scripts\python.exe smoke_test.py
"""

from campaign_agent.llm import get_llm

if __name__ == "__main__":
    llm = get_llm()
    response = llm.invoke("Réponds exactement : OK")
    print("Réponse du modèle :", repr(response.content))
