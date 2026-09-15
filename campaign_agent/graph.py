"""Le câblage — là où LangGraph assemble les nodes en une machine exécutable.

Chaque node marche isolément ; ici le dossier (`CampaignState`) circule d'un node
à l'autre en une seule chaîne qu'on invoque d'un coup.

J2 = collecte BORNÉE. Après `check_missing_information`, un aiguillage conditionnel
(`route_after_check`, fonction pure) tranche en trois :

    START → understand_request → check_missing_information
                                        │  route_after_check (pur) :
                                        ├─ "proceed" → load_brand_context → generate_campaign → evaluate_campaign
                                        ├─ "ask"     → ask_user → (retour) check_missing_information   ← LE CYCLE
                                        └─ "stop"    → END   (plafond MAX_ASKS atteint : la borne coupe)

    … generate_campaign → evaluate_campaign
                                        │  route_after_evaluation (pur) : lit policy_violations
                                        ├─ "reject"  → reject_campaign → END   (refus net, status="rejected")
                                        └─ "approve" → judge_quality
                                                          │  route_after_quality (pur) : lit quality_score
                                                          ├─ "retry" → increment_retry → generate_campaign   ← LA boucle bornée
                                                          └─ "pass"  → request_human_approval → END   (interrupt → aval humain)

La flèche de retour `ask_user → check` crée un cycle — infini en soi, borné par
`route_after_check`. On l'a câblée APRÈS que sa condition d'arrêt existe et soit
verte (§3, dans l'ordre — jamais la flèche avant le ciseau).

J3/J4 — la pause humaine est désormais RÉELLE : `ask_user` se fige via `interrupt()`
et reprend sur `Command(resume=...)`, l'état survivant grâce au checkpointer branché
dans `build_graph`. La borne MAX_ASKS (dans `route_after_check`) coupe toujours le
cycle — ajouter l'interrupt n'a PAS déplacé le ciseau (§3).

Le gate POLICY d'`evaluate_campaign` est CÂBLÉ : "reject" → `reject_campaign` (scelle
status="rejected"). "approve" ne va plus droit au HITL — il passe par le juge QUALITÉ
(couche b) : `judge_quality` PROPOSE un score, `route_after_quality` (pur) DISPOSE →
"retry" (→ `increment_retry` → `generate_campaign`, LA boucle bornée) ou "pass" (→
`request_human_approval`, le HITL). Les 3 couches de défense (policy déterministe →
juge contextuel → humain) sont câblées.

La seule vraie boucle du graphe (le retry qualité) a été câblée APRÈS sa borne
(`route_after_quality`), jamais avant (§3). Le graphe du §7 est complet.
"""

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from campaign_agent.nodes import (
    ask_user,
    check_missing_information,
    evaluate_campaign,
    generate_campaign,
    increment_retry,
    judge_quality,
    load_brand_context,
    reject_campaign,
    request_human_approval,
    understand_request,
)
from campaign_agent.routing import (
    route_after_check,
    route_after_evaluation,
    route_after_quality,
)
from campaign_agent.state import CampaignState


def build_graph():
    """Assemble et compile le graphe. Renvoie l'objet invocable.

    Fonction-usine (et pas un graphe global tout nu) : on peut en fabriquer un
    frais quand on veut, sans dépendre d'un ordre d'import. Compiler ne déclenche
    AUCUN appel LLM — les nodes n'appellent OpenRouter qu'au moment de l'invoke.

    J3 : InMemorySaver branché. Le graphe archive son état entre les appels :
    deux invoke() avec le même `thread_id` parlent du même dossier. Deux
    `thread_id` différents = deux conversations indépendantes.

    Le checkpointer est aussi le PRÉREQUIS de J4 (interrupt + resume) : sans
    lui, un `Command(resume=...)` lèverait RuntimeError.
    """
    builder = StateGraph(CampaignState)

    # Les nodes : chacun une responsabilité, déjà vérifié isolément.
    builder.add_node("understand_request", understand_request)
    builder.add_node("check_missing_information", check_missing_information)
    builder.add_node("ask_user", ask_user)
    builder.add_node("load_brand_context", load_brand_context)
    builder.add_node("generate_campaign", generate_campaign)
    builder.add_node("evaluate_campaign", evaluate_campaign)
    builder.add_node("judge_quality", judge_quality)
    builder.add_node("increment_retry", increment_retry)
    builder.add_node("reject_campaign", reject_campaign)
    builder.add_node("request_human_approval", request_human_approval)

    builder.add_edge(START, "understand_request")
    builder.add_edge("understand_request", "check_missing_information")

    # L'aiguillage borné : le ciseau (route_after_check, pur) décide l'étiquette,
    # le path_map la lie à sa cible. "stop" → END, c'est la borne qui coupe.
    builder.add_conditional_edges(
        "check_missing_information",
        route_after_check,
        {"proceed": "load_brand_context", "ask": "ask_user", "stop": END},
    )
    # L'arête de retour : le cycle de collecte. Infini SANS le ciseau ci-dessus.
    builder.add_edge("ask_user", "check_missing_information")

    builder.add_edge("load_brand_context", "generate_campaign")
    builder.add_edge("generate_campaign", "evaluate_campaign")

    # Le gate policy : le ciseau (route_after_evaluation, pur) lit policy_violations.
    # "reject" → node terminal ; "approve" ne va plus DROIT au HITL mais au juge (b).
    builder.add_conditional_edges(
        "evaluate_campaign",
        route_after_evaluation,
        {"reject": "reject_campaign", "approve": "judge_quality"},
    )

    # Le juge QUALITÉ (couche b) : il PROPOSE un score, route_after_quality (pur)
    # DISPOSE. "retry" → increment_retry → generate_campaign (LA boucle bornée) ;
    # "pass" → le HITL d'approbation. La borne (route_after_quality) est verte AVANT
    # que la flèche de retour n'existe (§3, dans l'ordre — jamais l'inverse).
    builder.add_conditional_edges(
        "judge_quality",
        route_after_quality,
        {"retry": "increment_retry", "pass": "request_human_approval"},
    )
    builder.add_edge("increment_retry", "generate_campaign")   # la flèche de retour

    # reject : refus policy scellé (status="rejected"). request_human_approval : le
    # HITL fige le graphe (interrupt), montre le Vibe Diff, reprend sur resume.
    builder.add_edge("reject_campaign", END)
    builder.add_edge("request_human_approval", END)

    return builder.compile(checkpointer=InMemorySaver())


# Graphe compilé prêt à l'emploi (compilation = pur câblage + instanciation du
# greffier mémoire — pas d'appel réseau).
graph = build_graph()
