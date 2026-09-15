"""Test de STRUCTURE du graphe — le câblage, pas le comportement (§3).

Compiler un graphe LangGraph n'appelle aucun LLM (§5) : on peut donc inspecter
sa FORME — nodes et arêtes — de façon 100 % déterministe. Ici on ne vérifie pas
ce que le gate décide (ça, c'est `route_after_evaluation`, testé dans
test_routing), mais qu'il est bien BRANCHÉ : le bon node, la bonne arête d'entrée,
les bonnes branches en sortie. L'aiguillage (§3, mon point faible) se prouve ici
au niveau du câblage, sans invoquer un modèle.

`get_graph()` expose `.nodes` (dict d'ids) et `.edges` (source, target, conditional,
data = l'étiquette). START/END y apparaissent comme '__start__' / '__end__'. ATTENTION :
c'est une vue de DESSIN — elle FUSIONNE deux arêtes parallèles vers la même cible et
n'en garde qu'une (le piège rencontré quand reject/approve pointaient tous deux sur
END). Le path_map réel vit dans `builder.branches` : c'est là qu'on relit les
étiquettes du gate sans perte — on garde cette lecture même si les cibles diffèrent
aujourd'hui, elle reste la vérité de l'aiguillage (§3).
"""

from langgraph.graph import END

from campaign_agent.graph import build_graph


def _edges(graph) -> set:
    """Les arêtes en triplets (source, target, étiquette) — comparables directement."""
    return {(e.source, e.target, e.data) for e in graph.get_graph().edges}


def _nodes(graph) -> set:
    return set(graph.get_graph().nodes.keys())


def _branch_ends(graph, node: str) -> dict:
    """Le path_map RÉEL d'un node conditionnel : {étiquette: cible}.

    Lu dans `builder.branches`, PAS dans get_graph() : la vue dessinée fusionne
    reject/approve (même cible END) et n'en garderait qu'une. Ici chaque étiquette
    est conservée — c'est la vérité de l'aiguillage (§3).
    """
    (branch,) = graph.builder.branches[node].values()
    return branch.ends


def test_evaluate_campaign_node_is_wired():
    # le node du gate policy existe dans le graphe compilé
    assert "evaluate_campaign" in _nodes(build_graph())


def test_generation_flows_into_evaluation():
    # generate_campaign ne va plus DROIT à END : il passe d'abord par le gate
    edges = _edges(build_graph())
    assert ("generate_campaign", "evaluate_campaign", None) in edges
    assert ("generate_campaign", END, None) not in edges


def test_policy_approve_flows_into_the_quality_judge():
    # le gate policy ne va plus DROIT au HITL : "approve" passe d'abord par le juge (b).
    # "reject" garde son node terminal. On lit le path_map RÉEL, pas get_graph().
    ends = _branch_ends(build_graph(), "evaluate_campaign")
    assert ends == {
        "reject": "reject_campaign",
        "approve": "judge_quality",
    }


def test_terminal_nodes_are_wired():
    # les deux nodes terminaux du chantier B existent dans le graphe compilé
    nodes = _nodes(build_graph())
    assert "reject_campaign" in nodes
    assert "request_human_approval" in nodes


def test_terminal_nodes_end_the_graph():
    # après le tampon (reject_campaign) ou l'aval humain (request_human_approval),
    # le workflow s'ARRÊTE : branchement terminal → pas de boucle, pas de borne (§3)
    edges = _edges(build_graph())
    assert ("reject_campaign", END, None) in edges
    assert ("request_human_approval", END, None) in edges


def test_quality_nodes_are_wired():
    # le juge (couche b) et le compteur de boucle existent dans le graphe compilé
    nodes = _nodes(build_graph())
    assert "judge_quality" in nodes
    assert "increment_retry" in nodes


def test_quality_branches_retry_and_pass():
    # le ciseau qualité : "retry" → increment_retry (la boucle), "pass" → HITL
    ends = _branch_ends(build_graph(), "judge_quality")
    assert ends == {"retry": "increment_retry", "pass": "request_human_approval"}


def test_retry_loops_back_to_generation():
    # LA flèche de retour bornée : increment_retry → generate_campaign. Le cycle
    # (generate → evaluate → judge → retry → generate) est coupé par la borne dans
    # route_after_quality (§3 : la flèche APRÈS sa borne, déjà verte).
    edges = _edges(build_graph())
    assert ("increment_retry", "generate_campaign", None) in edges
