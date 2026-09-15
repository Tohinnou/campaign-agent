"""Fixtures partagées par toute la suite — pytest les injecte SANS import.

`make_state` était dupliqué dans test_routing puis test_nodes. Au 3e consommateur
(load_brand_context), on le lève ici : une seule source pour l'état de référence.

C'est une fixture-USINE : elle ne rend pas un état, elle rend une FONCTION qui
en fabrique. Un test réclame `make_state` en paramètre, puis n'exprime que ce
qui diffère de la base — réaliste et crédible, pas du « foo/bar » (§5).
"""

import pytest


@pytest.fixture
def make_state():
    def _make(**overrides) -> dict:
        base = {
            "user_message": (
                "Prépare une campagne pour le lancement de notre gamme d'hiver, "
                "à envoyer début février."
            ),
            "objective": "faire connaître le lancement de la gamme d'hiver",
            "audience": "clientes 25-40 ans déjà abonnées à la newsletter",
            "offer": "-20 % sur toute la gamme les trois premiers jours",
            "tone": "chaleureux et complice",
            "campaign_date": "2026-02-01",
            "generated_message": "",
            "missing_fields": [],
            "status": "collecting_information",
            "retry_count": 0,
            "ask_count": 0,
        }
        base.update(overrides)
        return base

    return _make
