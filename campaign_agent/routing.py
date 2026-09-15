
import re
from typing import Literal

from campaign_agent.state import CampaignState


REQUIRED_FIELDS = ("objective", "audience", "offer", "campaign_date")

MAX_ASKS = 2   # plafond dur de la boucle de collecte : au-delà, on cesse de redemander (§3)

def detect_missing_fields(state: CampaignState) -> list[str]:
    """Renvoie les champs requis absents ou vides. Zéro LLM."""
    missing_fields = []
    for field in REQUIRED_FIELDS:
        if not state.get(field):
            missing_fields.append(field)
    return missing_fields


def route_after_check(state: CampaignState) -> Literal["proceed", "ask", "stop"]:
    """Le ciseau de la boucle de collecte. Zéro LLM, 100% déterministe (§3, §6 r3).

    Décide la route APRÈS check_missing_information, en trois issues :
      • "proceed" — dossier complet, on avance vers la génération ;
      • "ask"     — des trous, mais encore sous le plafond → on redemande ;
      • "stop"    — des trous ET plafond atteint → on coupe (pas de boucle infinie).

    Renvoie une ÉTIQUETTE, pas un node : c'est graph.py qui liera l'étiquette à
    sa cible (path_map). La fonction nomme la route ; le graphe la câble.
    """
    if not state.get("missing_fields"):
        return "proceed"
    if state.get("ask_count", 0) < MAX_ASKS:
        return "ask"
    return "stop"


def merge_user_answer(missing: list[str], answer) -> dict:
    """Ne retient que les champs DEMANDÉS, non vides, strippés. Le reste est ignoré."""
    if not isinstance(answer, dict):
        return {}
    return {f: answer[f].strip() for f in missing if isinstance(answer.get(f), str) and answer[f].strip()}


# ── quote_untrusted : citer un contenu de LLM sans lui donner la parole (§6 r7-9) ──
# 3e membre d'une famille déjà là : merge_user_answer whitelist l'entrée UTILISATEUR,
# interpret_approval whitelist le verdict HUMAIN, celui-ci neutralise l'entrée LLM. Même
# nature — valider ce qui vient du dehors — autre provenance.
#
# Le besoin : en retry, build_generation_brief réinjecte le reproche du juge ET la version
# précédente dans le prompt du rédacteur. C'est la feature qui fait qu'un retry APPREND
# (4→6 au smoke) — donc on ne peut pas la supprimer. Mais ces deux contenus sortent d'un
# modèle qu'un brief hostile influence : le prompt est une chaîne assemblée à partir de
# DONNÉES. Si le juge y écrit « --- RÉ-ÉCRITURE --- », il cesse d'être une donnée pour
# devenir du CODE — l'injection SQL, autre substrat.
#
# La règle posée : NOTRE VOCABULAIRE DE STRUCTURE EST RÉSERVÉ. Un marqueur de section
# écrit par un LLM est retiré ; le reste passe intact, encadré comme citation. On ENCADRE,
# on ne CENSURE pas — sinon on tuerait la finesse du reproche, c'est-à-dire la feature.
#
# Limite assumée : l'échappement dépend de la liste ci-dessous. Un marqueur inventé qu'on
# n'a pas prévu passerait (mitigé par la consigne de cadrage côté prompt). La parade
# complète — une balise à valeur imprévisible que l'attaquant ne peut pas deviner —
# viendra quand un contenu VRAIMENT tiers entrera (MCP, web), pas avant : ici les deux
# sources sont nos propres modèles.
_QUOTE_CLOSE = "[FIN DONNÉE NON FIABLE]"
_REDACTED = "[marqueur retiré]"

# `[ée]` PARTOUT, jamais `é` seul : un LLM écrit « RE-ECRITURE » aussi facilement que
# « RÉ-ÉCRITURE », et un échappement qui dépend des accents se contourne au clavier.
# Trouvé à la main en lisant un prompt sous attaque, pas par les tests — même trou que
# la policy sur « resultat garanti » (audit externe). La leçon est générale : tout filtre
# par liste dépend d'abord de sa NORMALISATION.
_RESERVED_MARKERS = (
    re.compile(r"-{2,}\s*r[ée]-?\s*[ée]criture\s*-{2,}", re.IGNORECASE),  # l'en-tête de section
    re.compile(r"r[ée]-?\s*[ée]cris\s+le\s+message", re.IGNORECASE),      # la consigne finale
    re.compile(r"\[\s*(?:fin\s+)?donn[ée]e\s+non\s+fiable[^\]]*\]?", re.IGNORECASE),  # les balises
)


def quote_untrusted(text: str, label: str) -> str:
    """Encadre `text` (produit par un LLM) en CITATION, marqueurs réservés neutralisés.

    Symétrique de merge_user_answer : là on garde une whitelist de champs, ici on retire
    une blacklist de marqueurs — la différence tient à la forme de l'entrée (un dict aux
    clés connues vs du texte libre), pas à l'intention. `label` vient de NOUS, jamais du
    modèle : il nomme la citation pour que le prompt reste lisible.
    """
    quoted = text
    for marker in _RESERVED_MARKERS:
        quoted = marker.sub(_REDACTED, quoted)
    return f"[DONNÉE NON FIABLE — {label}]\n{quoted}\n{_QUOTE_CLOSE}"


# ── La policy : le gate déterministe avant tout side-effect (§6 r7-8) ─────────
# Gate ÉTROIT (un seul niveau, BLOCK). Deux lignes rouges UNIVERSELLES, choisies
# pour un quasi-zéro faux positif et l'indépendance au domaine. On ne bloque pas
# « garanti » seul (« satisfait ou remboursé » est licite) mais « garanti »
# ADOSSÉ à un résultat / un revenu. Le LLM PROPOSE une campagne ; ici le code
# DISPOSE — sans modèle, testable, reproductible (§5).
_FORBIDDEN_PROMISES = (
    ("guaranteed_result", (
        r"résultats?\s+garantis?",                 # « résultat garanti », « résultats garantis »
    )),
    ("guaranteed_income", (
        r"revenus?\s+garantis?",                   # « revenus garantis »
        r"doublez\s+votre\s+(?:capital|argent)",   # « doublez votre capital »
        r"devenez\s+riche",                        # « devenez riche »
    )),
)


def detect_forbidden_promises(text: str) -> list[str]:
    """Renvoie les lignes rouges violées par `text` (slugs), [] si aucune. Zéro LLM.

    Symétrique de `detect_missing_fields` : une liste ordonnée, déterministe. Une
    violation NON vide = reject NET côté graphe (pas de retry, pas de validation
    humaine) — le retry reste réservé à la qualité insuffisante, pas à une
    promesse interdite.
    """
    lowered = text.lower()
    violations = []
    for slug, patterns in _FORBIDDEN_PROMISES:
        if any(re.search(pattern, lowered) for pattern in patterns):
            violations.append(slug)
    return violations


def route_after_evaluation(state: CampaignState) -> Literal["reject", "approve"]:
    """Le ciseau du gate policy. Zéro LLM, 100% déterministe (§3, §6 r3).

    Lit `policy_violations` (rempli par le node evaluate_campaign) et tranche :
      • "reject"  — au moins une ligne rouge → refus NET, sans retry ;
      • "approve" — rien à signaler → on passe à la validation humaine.

    Fail-open assumé : champ absent/vide → "approve" (comme route_after_check sur
    `missing_fields`). Sans danger — "approve" ne fait qu'ACHEMINER vers le HITL,
    qui reste le dernier filet. Deux issues TERMINALES : aucune boucle, aucune
    borne à ce stade (la borne retry_count viendra avec le juge qualité).
    """
    if state.get("policy_violations"):
        return "reject"
    return "approve"


# ── interpret_approval : le verdict humain validé, avant le side-effect (chantier B) ──
# Après route_after_evaluation → "approve", le HITL demande l'aval d'un humain.
# Ce filtre whitelist la RÉPONSE (le resume), comme merge_user_answer whitelist les
# champs de la collecte : même nature (validation d'entrée, §6 r7-8), autre moment.
def interpret_approval(decision) -> Literal["approved", "rejected"]:
    """Traduit le verdict humain (canal `resume`) en `status`, DENY-BY-DEFAULT.

    Cousin de `merge_user_answer` : le node request_human_approval fait
    `interrupt()` (il lève hors graphe → non testable en unitaire, cf. J4), donc
    la décision « ce verdict vaut-il approbation ? » est extraite ICI, pure. Le
    `resume` est une entrée EXTÉRIEURE (demain, le « oui » WhatsApp) : seul le
    jeton exact "approved" approuve ; tout le reste — refus explicite, faute de
    frappe, dict hostile, None, vide — retombe sur "rejected". On ne peut pas
    approuver par accident ; le silence ne vaut pas oui (§6 r7-8). HITL binaire :
    deux issues TERMINALES, aucune boucle, aucune borne (§3).
    """
    return "approved" if decision == "approved" else "rejected"


# ── Le juge QUALITE : la couche (b), entre la policy et l'humain (chantier A) ──
# La policy (deterministe) laisse passer le soft-manipulateur (cf. smoke adversarial) ;
# le juge LLM PROPOSE un quality_score, ce ciseau DISPOSE. Retry BORNE : une VRAIE
# boucle (→ generate_campaign), donc sa borne s'ecrit ICI, avant la fleche (§3).
QUALITY_THRESHOLD = 7   # score minimal (0-10) pour passer au HITL sans regenerer
MAX_RETRIES = 1         # plafond dur de la boucle qualite (§3), cousin de MAX_ASKS


def route_after_quality(state: CampaignState) -> Literal["retry", "pass"]:
    """Le ciseau de la boucle qualite. Zero LLM, 100% deterministe (§3, §6 r3).

    Lit `quality_score` (propose par le juge) et tranche :
      • "pass"  — score >= QUALITY_THRESHOLD → on avance vers le HITL ;
      • "retry" — score insuffisant ET encore sous MAX_RETRIES → on regenere ;
      • "pass"  — score insuffisant MAIS borne atteinte → on cede a l'humain.

    Les DEUX "pass" menent au HITL pour des raisons OPPOSEES : l'un parce que le
    message est bon, l'autre parce que la borne COUPE la boucle (§3, mon point
    faible) — sans quoi un message obstinement mauvais rebouclerait a l'infini. On
    ne rejette PAS a la borne : l'humain reste le dernier filet. Fail-open assume :
    score absent (juge pas passe) → "pass", comme route_after_evaluation.
    """
    score = state.get("quality_score")
    if score is None or score >= QUALITY_THRESHOLD:
        return "pass"
    if state.get("retry_count", 0) < MAX_RETRIES:
        return "retry"
    return "pass"


# ── assess_quality_signal : la VOIX du juge dans le Vibe Diff (option A, §1) ───
# route_after_quality DÉCIDE la route (retry/pass) ; celui-ci, lui, ne décide RIEN sur
# le flux — il TRADUIT le score du juge en signal AFFICHABLE pour l'humain. Séparés à
# dessein : router et informer sont deux responsabilités (§6 r2). Le juge PROPOSE le
# score, cette fonction DISPOSE de l'alerte, l'humain DÉCIDE (interpret_approval) — mais
# ici « disposer » veut dire « mettre en garde », jamais « bloquer » (souveraineté de
# l'humain sur son propre message : notre synthèse « informer, pas murer »).
def assess_quality_signal(state: CampaignState) -> dict:
    """Traduit `quality_score` en signal pour le Vibe Diff. JAMAIS bloquant.

    Option A (validée) : on affiche TOUJOURS le score — "warning" sous le seuil, "ok"
    au-dessus — pour que « 9/10 RAS » construise la confiance autant qu'un ⚠️ met en
    garde. Réutilise QUALITY_THRESHOLD (le MÊME seuil que route_after_quality : une
    seule vérité). Fail-open cohérent : juge pas passé (score absent) → "none", rien à
    signaler — comme route_after_quality « pass » sur un score manquant.
    """
    score = state.get("quality_score")
    if score is None:
        return {"level": "none"}
    level = "warning" if score < QUALITY_THRESHOLD else "ok"
    return {"level": level, "score": score, "reason": state.get("quality_reason", "")}