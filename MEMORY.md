# MEMORY.md — campaign-agent (handoff + journal)

> Chargé au démarrage de chaque session ici. `CLAUDE.md` = l'ADN (règles) ; ce fichier =
> l'état courant + le fil de l'apprentissage. Handoff écrit depuis la session
> langchain-lab/kaggle le **2026-07-17**.

---

## Où on en est (2026-09-15)

- **Le slice est CONSTRUIT** (2026-07-19 → 2026-08-17) : J1-J4 + policy gate + juge
  qualité + HITL d'approbation + audit adversarial (injection LLM→LLM mitigée par
  `quote_untrusted`). **87 tests déterministes verts** (2,4 s, zéro LLM). J5 (LangSmith)
  jamais branché — absorbé par C3.
- **Revue senior le 2026-09-15** (constats : 18 jours d'arrêt, DoD non tenue à 4× le
  délai, pas de git, pas d'evals, pas de chemin d'échec LLM) → `CLAUDE.md` amendé :
  règles 11-14 + chantiers **C1-C4 datés** (§7) + autonomie mesurée (§2).
- **C1 lancé le 2026-09-15 :** dépôt git, premier commit, CI ; publication GitHub dès
  l'authentification `gh`.
- **Prochaine action = C2, et elle est à WILLIAM seul : rédiger le teardown** depuis
  `meta/teardown_draft.md` (S2/S4/S5 d'abord, comme l'ossature l'indique), publier
  **≤ 2026-09-22**. Aucun code avant (règle 14).

---

## La vision (verbatim de William)

> Un système agentique accessible depuis WhatsApp, permettant de lancer des campagnes et
> d'exécuter des tâches à travers des outils MCP.

Ce cycle = le **cœur campagne seul** (comprendre → collecter → générer → évaluer →
approuver). Exercice qui **fonde un vrai produit**.

---

## Le plan de départ (à s'approprier, PAS à copier)

Un plan externe (voix générée) a posé la bonne intuition — sa valeur ne se réalise que
quand William le réécrit en **son** spec (règle « code disposable, spec source of truth »).

- **Graphe :** `understand_request → check_missing_information → (ask_user ↺ | load_brand_context
  → generate_campaign → evaluate_campaign → {retry borné | request_human_approval | reject})`.
- **State (esquisse à réécrire) :** `user_message, objective, audience, offer, tone,
  campaign_date, missing_fields, generated_message, evaluation_score, status
  (collecting_information | generating | awaiting_approval | approved | rejected), retry_count`.
- **5 cas de test (à écrire AVANT le code) :** (1) demande complète → aperçu direct ;
  (2) date manquante → question ciblée ; (3) promesse interdite → policy bloque ;
  (4) éval faible → **une seule** régénération ; (5) valide → attente d'approbation.
- **Ratio :** 70 % build / 20 % doc ciblée / 10 % notes.

---

## Décisions verrouillées ce tour (2026-07-17)

1. **Nom** `campaign-agent`, sous `C:\laragon\www\`.
2. **OpenRouter dès le jour 1** (pas de mock) pour RUN — **MAIS** routage/gates en fonctions
   pures + **LLM hors des tests déterministes** (voir `CLAUDE.md §5`). Le LLM propose, le
   code dispose.
3. **Exercice-fondation-de-produit** → garde-fous **durcis** (WhatsApp + MCP + multi-tenant
   = vraies contraintes futures, pas des notes).
4. Ce projet **remplace** le port `orchestrator.py` du labo (étape 5) : modéliser un domaine
   neuf > traduire un jouet connu.
5. **Données réalistes en ENTRÉE (anti-toy-data), synthétiques pour le SENSIBLE.**
   L'ambiguïté vit dans la *demande* (brief ambigu, réel/public), pas dans la base clients
   (contacts/PII restent faux). Web = sourcé par nous pour bâtir les cas ; fetch runtime =
   besoin ultérieur (tool + surface d'injection). Voir `CLAUDE.md §5`.
6. **(b) précurseur-MVP + artefact PUBLIC obligatoire en fin de slice** (démo 2 min OU
   teardown gouvernance ; engagement pris 2026-07-17, William « j'ai pas peur de l'artefact
   public »). Différenciateur = l'étage **fiabilité/gouvernance** (evals, policy, adversarial,
   80→99), PAS le fait de construire un agent. **Les garde-fous = la démo, au premier plan.**
   Slice montrable à ~2 semaines, pas repoussé au « vrai MVP ». Sert aussi la candidature à
   des offres (artefact inspectable = signal fort). Voir `CLAUDE.md §1`.

---

## Le fil conducteur (pourquoi ce projet, maintenant)

- **Sandbox (`kaggle`)** = le **POURQUOI** des garde-fous (Policy Server, Vibe Diff,
  Context Hygiene, AgBOM), agents codés à la main.
- **Labo (`langchain-lab`)** = le **COMMENT** de LangGraph (state/reducer, aiguillage,
  checkpointer, `interrupt`, LangSmith).
- **Ici = la fusion :** les garde-fous du sandbox, sur la machinerie du labo, autour d'un
  **vrai domaine**. Le produit (agent + tools MCP + policy + HITL + WhatsApp) est
  littéralement le threat-model du sandbox, en vrai.

---

## Point faible à border (rappel)

**L'aiguillage** (`should_continue` / arêtes conditionnelles / règles d'arrêt). Chaque
boucle (`ask_user`, `retry`) : **borne explicite AVANT la flèche de retour.**

---

## Références

- **Labo LangGraph :** `C:\laragon\www\langchain-lab`
  (`02_langgraph/agent_memoire.py` = le checkpointer ; `meta/learning_notes.md` = journal WHY).
- **Sandbox agentique :** `C:\laragon\www\kaggle`
  (`CLAUDE.md` = les garde-fous + le vocabulaire verbatim du cours).
