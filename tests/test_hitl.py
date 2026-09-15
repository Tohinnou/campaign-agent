"""Test d'INTÉGRATION du HITL d'approbation — le garde-fou central du slice (§1).

Différent des autres suites :
  • test_routing / test_nodes exercent des fonctions/nodes PURS en appel direct ;
  • test_graph vérifie la STRUCTURE statique du graphe (arêtes, path_map) ;
  • ICI on EXÉCUTE un mini-graphe (juste request_human_approval + checkpointer) pour
    prouver le COMPORTEMENT interrupt→resume de bout en bout. Zéro LLM : l'interrupt
    est du pur LangGraph (aucun modèle) → déterministe, gratuit, sa place est en pytest.

Ce que la sonde a établi (LangGraph 1.2.9), encodé ici :
  • un invoke qui atteint interrupt() renvoie un dict avec la clé "__interrupt__" =
    une LISTE d'objets Interrupt ; le payload est dans .value ;
  • on reprend avec graph.invoke(Command(resume=...), config) sur le MÊME thread_id
    (le checkpointer ressort le même dossier) ; le node est rejoué, et interrupt()
    rend alors la valeur du resume (le « concept à ré-ancrer » état-vs-position, J4).

RED voulu : request_human_approval n'existe pas encore → AttributeError à la
construction du mini-graphe, test par test (accès-module, comme test_nodes).
"""

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from campaign_agent import nodes
from campaign_agent.state import CampaignState


def _approval_graph():
    """Un graphe JOUET réduit au seul node HITL : START → approval → END.

    On isole le node pour prouver son mécanisme sans réveiller les nodes LLM du
    vrai graphe (understand_request, generate_campaign). Le câblage RÉEL
    (approve → request_human_approval) est vérifié à part, en structure (test_graph).
    """
    builder = StateGraph(CampaignState)
    builder.add_node("approval", nodes.request_human_approval)
    builder.add_edge(START, "approval")
    builder.add_edge("approval", END)
    return builder.compile(checkpointer=InMemorySaver())


def _cfg(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def test_hitl_stops_and_shows_the_vibe_diff(make_state):
    # AVANT tout side-effect, le graphe s'ARRÊTE et expose ce qu'on va valider (§6 r7)
    graph = _approval_graph()
    state = make_state(generated_message="Notre gamme d'hiver : -20% ce week-end.")
    result = graph.invoke(state, _cfg("t-vibe"))

    assert "__interrupt__" in result                      # le graphe est en pause
    payload = result["__interrupt__"][0].value
    assert payload["generated_message"] == "Notre gamme d'hiver : -20% ce week-end."
    assert payload["brief"]["objective"] == state["objective"]  # le contexte de décision


def test_hitl_approves_on_exact_token(make_state):
    # l'humain approuve avec le jeton exact → status="approved", le graphe va à END
    graph = _approval_graph()
    cfg = _cfg("t-ok")
    graph.invoke(make_state(generated_message="Découvrez la gamme d'hiver."), cfg)
    result = graph.invoke(Command(resume="approved"), cfg)

    assert result["status"] == "approved"
    assert "__interrupt__" not in result                  # plus de pause : terminé


def test_hitl_explicit_rejection_ends_rejected(make_state):
    # le NON franc de l'humain → status="rejected" (issue terminale du HITL binaire)
    graph = _approval_graph()
    cfg = _cfg("t-no")
    graph.invoke(make_state(generated_message="Découvrez la gamme d'hiver."), cfg)
    result = graph.invoke(Command(resume="rejected"), cfg)

    assert result["status"] == "rejected"


def test_hitl_hostile_resume_cannot_approve(make_state):
    # LE cas de gouvernance : un resume hostile qui mime un état approuvé →
    # deny-by-default À TRAVERS LE GRAPHE. On ne PEUT pas approuver par accident.
    graph = _approval_graph()
    cfg = _cfg("t-hostile")
    graph.invoke(make_state(generated_message="Découvrez la gamme d'hiver."), cfg)
    result = graph.invoke(Command(resume={"status": "approved"}), cfg)

    assert result["status"] == "rejected"


def test_hitl_vibe_diff_carries_the_quality_warning(make_state):
    # option A : le Vibe Diff porte désormais la VOIX du juge (b). Un message soft-
    # manipulateur (score bas) → l'humain voit le ⚠️ + la raison AVANT de trancher.
    graph = _approval_graph()
    state = make_state(
        generated_message="Votre voyage vers la richesse commence aujourd'hui !",
        quality_score=2,
        quality_reason="promesse d'enrichissement, urgence artificielle",
    )
    result = graph.invoke(state, _cfg("t-warn"))

    payload = result["__interrupt__"][0].value
    assert payload["quality"] == {
        "level": "warning",
        "score": 2,
        "reason": "promesse d'enrichissement, urgence artificielle",
    }


def test_hitl_warning_informs_but_never_blocks(make_state):
    # LE point de gouvernance de notre synthèse : le ⚠️ INFORME, il ne MURE pas. Score
    # bas MAIS l'humain approuve (il connaît son audience) → status="approved". La
    # souveraineté reste à l'humain ; le juge n'a qu'une voix, pas un verrou.
    graph = _approval_graph()
    cfg = _cfg("t-warn-approve")
    graph.invoke(
        make_state(
            generated_message="Votre voyage vers la richesse commence aujourd'hui !",
            quality_score=2,
            quality_reason="promesse d'enrichissement",
        ),
        cfg,
    )
    result = graph.invoke(Command(resume="approved"), cfg)

    assert result["status"] == "approved"
