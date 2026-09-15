# CLAUDE.md — campaign-agent (Project DNA)

> Auto-chargé en premier par tout agent qui ouvre ce repo. Définit l'identité, la façon
> de travailler avec William, les règles d'ingénierie, la roadmap.
> **Handoff depuis deux projets de référence** (à consulter, pas à recopier) :
> `C:\laragon\www\langchain-lab` (le COMMENT de LangGraph) et `C:\laragon\www\kaggle`
> (le POURQUOI des garde-fous agentiques). Ici = la **construction**.

---

## 1. Identité

**Produit visé :** Un système agentique accessible depuis WhatsApp, permettant de lancer
des campagnes et d'exécuter des tâches à travers des outils MCP.

**Ce premier cycle (le vertical slice) :** UNIQUEMENT le cœur métier de la campagne,
sans canal ni delivery :

> Un utilisateur décrit une campagne → le système collecte les infos manquantes →
> génère un aperçu → vérifie une politique → demande une validation humaine.

**Statut :** cas **(b) — précurseur MVP** menant à de vrais premiers utilisateurs, pas un
exercice privé. On apprend en construisant, mais le domaine est modélisé sérieusement.

**Ligne d'arrivée du slice (definition of done) :** du code qui marche **+ un artefact
PUBLIC** — démo 2 min *ou* teardown écrit « comment je gouverne cet agent ». Engagement
pris le 2026-07-17. Le slice est **montrable publiquement à ~2 semaines**, jamais repoussé
au « vrai MVP » (cette phrase-là boucle à l'infini).

**Revue 2026-09-15 :** l'engagement n'a pas été tenu (code fini le 2026-08-17, rien de
public au 2026-09-15). La ligne d'arrivée est re-bornée, DURE cette fois : **teardown
rédigé par William et publié au plus tard le 2026-09-22** (chantier C2, §7). Zéro
nouvelle feature avant (règle 14).

**Le différenciateur (ce qui doit crever l'écran) :** PAS « je sais construire un agent »
(nouveau CRUD — l'IA le fait pour tous). Mais **« je sais le rendre FIABLE et le
GOUVERNER »** : evals, policy gating, adversarial, gap 80→99 %. Donc les garde-fous du §6
ne sont **pas de l'overhead** — **ce sont la démo. On les met au premier plan, jamais
cachés.**

**Ce projet N'EST PAS encore :** pas d'envoi WhatsApp réel, pas de Baileys, pas de
Temporal, pas de MCP branché, pas de multi-tenant, pas de mémoire épisodique sophistiquée,
pas de 1000 contacts. Chacun viendra **quand un besoin réel l'exigera** (voir §7).

---

## 2. Comment travailler avec William (disciplines — NON négociables)

> Reportées de sa mémoire globale, car un projet neuf a un dossier mémoire vide.

- **Réponds en français.**
- **Mode mentor :** rythme les explications, diffère les livrables collaboratifs, donne
  **toujours le WHY**.
- **Purpose-first :** avant tout nouveau module/sous-phase, énonce le WHY en 2-4 phrases
  et **attends validation**. Le quiz rétrospectif seul ne suffit pas.
- **Active Review > recopie :** William lit ton code de référence, questionne le design,
  le ré-explique. Il ne retape que pour un pattern syntaxique inédit ou sur demande.
  **Ne copie jamais un plan externe — il le réécrit dans ses mots.**
- **Analogy-first :** s'il dit « flou / trop technique », recommence par analogie du
  quotidien → exemple concret → pont vers le jargon. Ne reformule pas le jargon.
- **Feynman en fin de phase :** 2-3 questions ouvertes qu'il répond sans regarder le code ;
  tu critiques ce qui glisse. Non optionnel.
- **Persiste les WHY :** chaque WHY produit va aussi dans `meta/learning_notes.md`.
- **Autonomie mesurée (revue 2026-09-15) :** sur les chantiers désignés (C4 pour
  commencer), William écrit le **PREMIER JET**, l'agent review ensuite — l'inverse du
  mode référence. Le Feynman vérifie la compréhension ; seul le premier jet vérifie la
  capacité à produire seul.

---

## 3. Point faible identifié (à surveiller activement)

**L'aiguillage** — `should_continue`, les arêtes conditionnelles, les règles d'arrêt.
C'est l'organe qui a glissé **deux fois** au labo (qui décide la route ? qui coupe la
boucle ?). Conséquence directe ici :

> **Ne jamais câbler une flèche de retour (retry, ask_user) avant d'avoir écrit la
> condition qui la coupe.** Chaque boucle rend sa borne explicite dès le premier jet.

**Post-scriptum (revue 2026-09-15) : ce point faible vaut aussi pour le PROJET.** Le
slice a tourné à 4× son délai, puis s'est arrêté 18 jours à 95 % du chemin — une boucle
sans borne, un niveau au-dessus du graphe. La borne du projet vit désormais dans les
dates du §7 et la règle 14 : **un chantier sans date n'est pas un chantier.**

---

## 4. Stack & boundaries

```yaml
runtime:        python >=3.11
orchestration:  langgraph        # StateGraph, checkpointer, interrupt
llm_facade:     langchain
llm_backend:    openrouter       # modèle RÉEL dès le jour 1 (voir §5), pas de mock
api:            "[plus tard, par besoin] fastapi"   # le slice se pilote par scripts/tests ; un canal réel le réclamera. Honnêteté de spec (revue 2026-09-15) : on ne déclare pas ce qu'on ne fait pas
testing:        pytest
observability:  langsmith        # données JOUET uniquement
versioning:     git + github     # dépôt PUBLIC dès 2026-09-15 — l'artefact public commence là (r11)
ci:             github actions   # la suite déterministe verte sur chaque push (r11)

forbidden_for_now:
  - baileys / toute lib WhatsApp non officielle   # reverse-engineered → ban + anti-slopsquatting
  - temporal                                       # tant qu'un checkpointer suffit
  - langchain "partout pour montrer qu'on maîtrise"

verify_before_install: true   # anti-slopsquatting : vérifier tout package avant l'install
```

---

## 5. Le modèle : OpenRouter dès le jour 1 — et la ligne à ne pas franchir

**Décision (2026-07-17) :** on RUN sur OpenRouter (`openai/gpt-4o-mini`, `temperature=0`)
dès le début, **pas de mock**. Raison : ce workflow a de vrais nodes de compréhension
(comprendre une demande, détecter un champ manquant, générer une campagne) — un fake
scripté ne montrerait rien de réel. Le mock du labo était une erreur de rythme.

**MAIS la testabilité déterministe reste sacrée** — le mock n'était jamais le but, les
tests reproductibles l'étaient (le `pass^k` du sandbox). On l'obtient autrement, **mieux** :

1. **Les décisions vivent dans des fonctions pures, pas dans les nodes LLM.** Le routage
   (`should_continue`), la détection de champ manquant, la borne de retry, la policy =
   Python pur, testable sans modèle. **Le LLM propose, le code dispose.**
2. **Le LLM reste HORS de la suite de tests déterministe.** OpenRouter fait tourner l'app,
   pas les tests (sinon : coût par run + non-déterminisme → `pass^k` s'effondre + flaky en
   CI). Les nodes LLM : stub, ou smoke-test à part.
3. **Clé dans `.env`, jamais dans le code ni le chat.** `load_dotenv()`.
4. **Données : réalistes en ENTRÉE, synthétiques pour le SENSIBLE.** L'input (brief de
   campagne, ton de marque, demande) doit être **réaliste et ambigu** — inspiré d'exemples
   réels/publics du web si utile — *parce que l'ambiguïté que le workflow doit attraper
   (`check_missing_information`, la policy) vit là*. Un stub « propre » de 2 lignes ferait
   croire que ça marche sans jamais exercer le cœur (piège du « marche en démo », 80% Problem).
   **Mais** les données **sensibles** (listes de contacts, numéros, PII, actifs privés d'une
   marque) restent **synthétiques** — *l'ambiguïté est dans la demande, pas dans la base
   clients*. Contenu web ingéré ou tracé = **public / non sensible** uniquement.
   *Mécanisme :* aujourd'hui **nous** sourçons ces exemples réalistes pour bâtir les cas ;
   un agent qui **va chercher** le web au runtime est un « besoin » ultérieur (tool à
   side-effect + surface d'injection → §6 règles 7-8, §7).

---

## 6. Règles d'ingénierie (les porteuses)

| # | Règle | Pourquoi |
|---|---|---|
| 1 | **Vertical slice** avant big-bang | Isole la variable : si ça casse, tu sais d'où |
| 2 | **Un node = une responsabilité** | Évite l'agent opaque `run_agent` ; testable |
| 3 | **Décisions en fonctions pures** (routage/gates hors LLM) | Testabilité déterministe malgré OpenRouter (§5) |
| 4 | **Borne explicite sur CHAQUE boucle** avant la flèche de retour | Ton point faible (§3) ; évite la récursion infinie |
| 5 | **Tests avant code** (EDD) : 3-5 cas par feature | Empêche le « marche en démo seulement » |
| 6 | **Spec du domaine front-loadée** ; framework appris au besoin | On apprend le checkpointer quand il manque ; on ne « découvre pas en route » ce qu'est une campagne valide |
| 7 | **Vibe Diff / HITL avant tout side-effect** (envoi, dépense, delete) | Le produit va vers WhatsApp+MCP = actions réelles ; Confused Deputy |
| 8 | **Tool calls via un point de contrôle** (policy) | Le produit exécute des tâches via MCP = surface d'attaque |
| 9 | **Context Hygiene** : PII → `[[VAR]]` résolu au runtime | WhatsApp = numéros, noms = PII réelle |
| 10 | **AgBOM** : inventorier deps / MCP / modèles ajoutés | Supply chain ; anti-slopsquatting |
| 11 | **Git dès maintenant ; chaque session finit par un commit ; CI verte sur chaque push** | Sans dépôt : pas d'artefact public, pas d'historique-preuve ; le `pass^k` se vérifie en machine, pas de mémoire |
| 12 | **Le différenciateur = des ARTEFACTS d'eval** (golden + adversarial rejouables, scores trackés), pas un argument | La 1ʳᵉ question d'un pair : « où sont tes evals ? » ; « 80→99 % » ne se cite que métrique à l'appui |
| 13 | **Chaque node LLM a un chemin d'échec** (timeout, 429, sortie invalide) : échec bruyant, route propre | En prod, la panne est plus fréquente que l'attaque ; un crash brut n'est pas « fiable » |
| 14 | **Gouvernance du temps = même rigueur que les boucles** : chaque chantier daté, ≥3 sessions/sem., zéro feature tant qu'un livrable public attend | Le projet est une boucle ; sa borne = une date (revue 2026-09-15, P1) |

---

## 7. Roadmap (le vertical slice, puis l'expansion par besoin)

Le premier graphe :

```
START → understand_request → check_missing_information
          ├─ manque    → ask_user → (retour, borné)
          └─ complet   → load_brand_context → generate_campaign → evaluate_campaign
                                                                    ├─ retry (borné !)
                                                                    ├─ request_human_approval
                                                                    └─ reject
```

Progression — **chaque notion répond à un besoin réel** :

- **J1 ✅ (2026-07-20)** — squelette **LINÉAIRE** qui tourne (state + nodes principaux sur
  OpenRouter, `evaluate` off). Un pipeline avec 2 boucles bornées, **pas la boucle agent**.
- **J2 ✅ (2026-07-30)** — collecte multi-champs → `conditional edges`, `structured
  outputs`, cycle `ask_user` borné.
- **J3 ✅ (2026-07-30)** — persistance conversation → `checkpointer`, `thread_id`.
- **J4 ✅ (2026-08-04)** — attente de validation → `interrupt()`, reprise
  `Command(resume=...)`, HITL.
- **J5 ⏸ jamais branché** — LangSmith. Absorbé par C3 (les datasets/evaluators y vivent).
- **Hors plan initial ✅ (2026-08-04 → 2026-08-17)** — policy gate, juge qualité (couche
  b), Vibe Diff, audit adversarial (injection LLM→LLM mitigée : `quote_untrusted`).

**Chantiers courants (revue 2026-09-15 — dans CET ordre, règle 14) :**

- **C1 (2026-09-15)** — git + premier commit + GitHub **PUBLIC** + CI (règle 11).
- **C2 (≤ 2026-09-22, borne DURE)** — le **teardown**, rédigé par **WILLIAM** depuis
  `meta/teardown_draft.md` (S2/S4/S5 d'abord), puis PUBLIÉ. Aucun code avant (règle 14).
- **C3 (cible 2026-09-29)** — la couche eval (règle 12) : 12-15 briefs golden +
  adversarial en YAML, runner pytest marqué `llm` (HORS suite déterministe), scores
  trackés en JSONL — port du pattern `kaggle` — + LangSmith branché (l'ex-J5).
- **C4 (1 session, après C3)** — chemin d'échec LLM (règle 13) : timeout / 429 /
  ValidationError → échec bruyant, route propre. **Premier jet par WILLIAM** (rôles
  inversés, §2 — la mesure d'autonomie).
- **[plus tard, par besoin]** — Temporal (multi-jours) → MCP/Airtable/Gmail (outils) →
  WhatsApp (`MessagingProvider`) → Delivery Engine.

---

## 8. En cas de doute

1. Le besoin actuel est-il déjà cadré ici (§1, §6, §7) ?
2. Réfère au labo `C:\laragon\www\langchain-lab` (comment LangGraph marche —
   `02_langgraph/agent_memoire.py` = le checkpointer) et au sandbox
   `C:\laragon\www\kaggle` (pourquoi les garde-fous existent — son `CLAUDE.md`).
3. Vérifie la doc officielle avant de coder une spécificité LangGraph de mémoire
   (réflexe anti-amateur).
4. Pose une question avant 100 lignes dans la mauvaise direction.

---

*Décisions §5 et §6 = invariants. Toute modification nécessite une discussion explicite.*

---

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Product ideas/brainstorming → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Design system/plan review → invoke /design-consultation or /plan-design-review
- Full review pipeline → invoke /autoplan
- Bugs/errors → invoke /investigate
- QA/testing site behavior → invoke /qa or /qa-only
- Code review/diff check → invoke /review
- Visual polish → invoke /design-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save progress → invoke /context-save
- Resume context → invoke /context-restore
