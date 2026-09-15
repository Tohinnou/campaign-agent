"""Le client LLM — le SEUL point qui parle à OpenRouter (§5).

La clé vit dans `.env`, jamais dans le code ni le chat. `temperature=0` :
on veut la sortie modèle la plus reproductible possible (le vrai déterminisme,
lui, vit dans les fonctions pures — `routing.py`).
"""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()  # charge .env une fois, au premier import


def get_llm() -> ChatOpenAI:
    """Construit le client, pointé vers OpenRouter.

    OpenRouter est compatible avec l'API OpenAI → on réutilise `ChatOpenAI`
    en changeant seulement `base_url` + la clé.

    `os.environ[...]` (et pas `.get`) est volontaire : si la clé manque,
    on veut planter tout de suite (fail-fast) plutôt qu'un `None` silencieux.
    """
    return ChatOpenAI(
        model=os.environ["OPENROUTER_MODEL"],
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
        temperature=0,
    )
