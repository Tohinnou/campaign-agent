"""L'état qui circule de node en node — le « dossier » du workflow.

Aucune dépendance au framework ici : c'est du Python pur (`typing`).
LangGraph n'entre qu'au moment du câblage (`graph.py`). Le state, lui,
est lisible et testable sans rien exécuter.
"""

from typing import Literal, TypedDict

# Les stades que le dossier peut traverser. La contrainte devient un *type* :
# si un node écrit "generatng", ça remonte à l'analyse au lieu de router dans le vide.
CampaignStatus = Literal[
    "collecting_information",
    "generating",
    "awaiting_approval",
    "approved",
    "rejected",
]


class CampaignState(TypedDict):
    # ── ce qui ENTRE ────────────────────────────────────────────────
    user_message: str

    # ── ce qui SE REMPLIT : les attributs de la campagne ────────────
    objective: str
    audience: str
    offer: str
    tone: str
    campaign_date: str

    # ── ce qui SE REMPLIT : la sortie ───────────────────────────────
    generated_message: str

    # ── le CONTRÔLE : le canal d'aiguillage ─────────────────────────
    missing_fields: list[str]
    policy_violations: list[str]   # lignes rouges de la policy → reject net (§6 r7-8)
    quality_score: int             # note du juge qualité (0-10) → route_after_quality
    quality_reason: str            # justification du score (trace, §1)
    status: CampaignStatus
    retry_count: int   # borne de la boucle qualité (retry) — chantier A (§3)
    ask_count: int     # borne de la boucle collecte (ask_user) — comptée À PART (§3)
