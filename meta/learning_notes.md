# learning_notes.md — campaign-agent

> Journal des **WHY**. Chaque WHY produit pendant une phase est appendé ici (discipline
> reportée du sandbox et du labo). Format libre, mais toujours : *quelle décision, quel
> pourquoi, quelle analogie si utile.* Les quiz Feynman de fin de phase et les
> « Concepts à ré-ancrer » vivent aussi ici.

---

## Concepts à ré-ancrer (à retester en priorité)

- **L'aiguillage** (`should_continue` / arêtes conditionnelles / règles d'arrêt) — a glissé
  deux fois au labo. Règle : borne explicite AVANT la flèche de retour. À vérifier à chaque
  boucle (`ask_user`, `retry`).
  - **[2026-07-20]** Le Feynman de fin de J1 a fait glisser la Q3 *exactement* ici (la boucle
    nommée sans sa borne). Confirmé en vrai : c'est LE point à surveiller quand J2 câblera
    `ask_user` — J2 s'ouvrira *par* la condition d'arrêt, pas par la flèche.
  - **[2026-07-30]** Feynman J2→J4 : la borne (Q2) est passée **juste** — « le ciseau reste
    dans `route_after_check` pour ne pas mêler déterministe et non-déterministe », dit
    spontanément, pas récité. Le §3 se **stabilise** (il se déplace, il ne disparaît pas) →
    re-vérifier au `retry` de `evaluate_campaign`.
  - **[2026-08-04]** Feynman de la brique policy gate : la Q1 (« pourquoi le gate n'a PAS eu
    besoin de borne ? ») **n'a pas été sue** — le §3 re-glisse. Nuance (re)posée : le gate est
    un **branchement terminal** (`reject`/`approve` → END) → **aucune boucle, aucune borne** ;
    une borne ne protège que ce qui *revient*. La VRAIE borne (§3) s'exercera au `retry_count`
    du **juge qualité** (chantier A), qui s'ouvrira *par* sa condition d'arrêt — **pas** sur
    `evaluate_campaign` (policy, terminal). La formule du 07-30 est corrigée en ce sens.
  - **[2026-08-04] (chantier B)** Feynman du HITL : Q3 « pourquoi l'interrupt n'exige-t-il pas de
    borne ? » **à moitié**. La distinction *retour dans le graphe* vs *suspend/avance* est venue
    **après reformulation** — mais inversée : « retour **grâce à** MAX_ASKS ». Corrigé : la flèche
    de retour, c'est `add_edge(ask_user → check)` ; **MAX_ASKS ne crée pas la boucle, il la
    coupe**. *La flèche et sa borne sont DEUX choses.* Le §3 progresse (la distinction pause/boucle
    est neuve et acquise) mais reste à consolider au `retry_count` du juge qualité (chantier A).
  - **[2026-08-07]** LE test décisif annoncé (le `retry_count` du juge qualité) a eu lieu — et la
    borne a **tenu** : au smoke, la boucle a coupé à `MAX_RETRIES=1` et cédé au HITL, zéro infini.
    Mais le vrai acquis §3 est ailleurs : le « retry qui apprend » a modifié le **corps** de la
    boucle (ce qu'elle FAIT) **sans toucher à sa condition** (ce qui la COUPE — borne, compteur,
    seuil intouchés). Distinction gravée : **corps de boucle ≠ condition de boucle** ; on change
    l'un sans re-borner tant qu'on ne touche pas l'autre. Le §3 se **stabilise** (ne glisse plus
    sur cette famille de cas) — prochain front réel : quand un vrai side-effect (envoi) ira SOUS
    un interrupt.

- **Checkpointer = ÉTAT, pas POSITION** — a glissé au Feynman J4 (Q3). Intuition fausse : « le
  checkpointer est là, donc on reprend où on s'était arrêté ». L'armoire range le *dossier*
  (données, clé `thread_id`), jamais *où l'agent en était* ni ses variables locales (`missing`,
  `ask_count`) → d'où le **rejeu du node depuis le début** au `resume`. À reverbaliser dès que
  `interrupt` revient (HITL d'approbation, J-later).
  - **[2026-08-04]** Reverbalisé au Feynman du chantier B (Q2) : « au resume la fonction est
    rejouée → sinon duplication d'envoi », **juste et spontané**. Le concept **tient** — c'est
    lui qui fonde la règle « rien d'irréversible au-dessus de l'interrupt » (le node rejoué EN
    ENTIER découle de « état, pas position »).

---

## Journal

### 2026-07-17 — Données réalistes en entrée (anti-toy-data)

**WHY :** un stub « propre » de 2 lignes fait passer le workflow en démo verte sans jamais
exercer son cœur (`check_missing_information`, la policy) — le piège du « 80% / marche en
démo ». On alimente donc l'ENTRÉE avec du réaliste et de l'ambigu (briefs réels/publics),
*parce que l'ambiguïté qu'on veut attraper vit dans la demande*. Distinction clé :
réalisme de la **TÂCHE** (oui) ≠ réalisme des **DONNÉES SENSIBLES** (non — contacts/PII
synthétiques). Web = public/non sensible ; un fetch au runtime = surface d'injection,
reporté en « besoin » ultérieur.

### 2026-07-17 — Le différenciateur en ère IA = la gouvernance, pas l'agent

**WHY :** quand 80 % des devs codent avec l'IA, « savoir construire un agent » se
commoditise (l'IA le fait pour eux — un agent qui tourne = le nouveau CRUD). Ce qui reste
rare et cher = l'étage que les codeurs-standard **sautent** : fiabilité + gouvernance
(evals, policy gating, adversarial, gap 80→99 %). C'est le moat construit en kaggle,
sous-estimé parce qu'il ressemblait à « juste le cours ». **Corollaire dur :** une
différenciation invisible vaut 0 → elle doit être **légible au marché** → un artefact
public (démo + teardown gouvernance) fait partie de la *definition-of-done*, pas en option.
« Solidifier les notions avant le vrai MVP » est la phrase qui boucle → le slice lui-même
doit être montrable. Le meilleur artefact ne montre pas « ça génère une campagne »
(commodité) mais **les garde-fous qui se déclenchent** (refus d'une promesse interdite,
arrêt pour approbation humaine, retry borné) — c'est ça, le différenciateur, rendu visible.

### 2026-07-20 — La frontière de test = la NATURE du node (§5, §6 r3/r5)

**WHY :** un test `pytest` *affirme une valeur exacte* (`== ["audience"]`). Cette affirmation
n'a de sens que si le même input redonne toujours le même output. Un node LLM : même brief →
texte potentiellement différent, + coût + réseau → aucune cible stable à écrire, et *flaky*
en CI. Le déterminisme n'est donc pas un confort, c'est la **précondition de l'assertion**.
Levier de design qui en découle : on **pousse les décisions dans des fonctions pures**
(`routing.py`, `check_missing_information`) *pour* qu'elles soient assertables, et on garde le
LLM hors de la suite (smoke test à part). La frontière n'est pas le fichier mais la nature du
node — un pur et un LLM cohabitent dans `nodes.py` ; seul l'`.invoke()` du LLM coûterait,
importer le module ne coûte rien (prouvé : la collecte pytest a échoué sur le nom manquant,
jamais sur un appel réseau).

### 2026-07-20 — Le node REMPLIT, la fonction pure DÉCIDE (§3, l'aiguillage)

**WHY :** l'aiguillage (mon point faible) ne vit JAMAIS dans un node. Patron déjà bâti :
`understand_request` *remplit* les 5 attributs → `detect_missing_fields` (pur) *décide* ce qui
manque. Le node fournit la matière ; le code pur tranche la route. Ça se rejouera à
l'identique : `evaluate_campaign` *remplira* un score, une **fonction pure sur arête
conditionnelle** décidera « retry borné / approve / reject ». Analogie : le node est le
greffier qui remplit le dossier, la fonction pure est le juge qui lit et oriente — deux rôles,
jamais la même main.

### 2026-07-20 — L'output structuré = levier de FIABILITÉ, pas confort (§1)

**WHY :** demander du texte libre au LLM puis le re-parser au regex est fragile (le « 80% »).
`.with_structured_output(SchémaPydantic)` force un OBJET typé — le modèle ne *peut* pas
déborder. Appliqué deux fois : extraction (`CampaignBrief`, champs vides si absents) et
génération (`GeneratedCampaign`, qui a retiré le « Bien sûr ! Voici… » au smoke). Ce n'est pas
de l'overhead : rendre le LLM fiable EST le différenciateur du projet — donc au premier plan,
jamais caché.

### 2026-07-20 — Borne AVANT la flèche de retour (§3, §6 r4)

**WHY :** J1 est une ligne droite → zéro boucle → récursion infinie *impossible par
construction*. La protection n'est pas un garde-fou ajouté, c'est l'absence d'arête de retour.
À J2, `ask_user` n'arrivera JAMAIS seule : sa borne s'écrit en même temps, et d'abord. Ciseau
= `missing_fields` devient `[]` (sortie naturelle : chaque réponse remplit un champ → la liste
rétrécit) **+ plafond dur** de relances (si l'utilisateur ne donne jamais le champ). Nommer la
flèche sans le ciseau = le glissement qui a coûté deux fois au labo.

### 2026-07-20 — Filet, pas écrasement (§1, respect de l'intention)

**WHY :** `load_brand_context` pose le ton par défaut de la marque UNIQUEMENT si `tone` est
vide ; si l'utilisateur a précisé un ton, il n'y touche pas (`return {}`). Le défaut est un
filet, jamais un override — écraser l'intention utilisateur serait un défaut de gouvernance.
C'est aussi ce node qui *justifie* que `tone` soit hors de `REQUIRED_FIELDS` : le trou est
toujours comblé ici, donc jamais bloquant en amont.

### 2026-07-20 — Convention « absent → "" » (une seule règle d'absence)

**WHY :** le LLM renvoie `""` pour un champ non mentionné (jamais inventé). Du coup
`not state.get(field)` attrape `""` ET `None` d'une seule règle, et `state.py` reste tout en
`str` (pas de `Optional`/`None` à mélanger). L'ambiguïté « vide = manquant » est tranchée une
fois, au même endroit.

### 2026-07-20 — Notes techniques J1 (en vrac)

- **Partial-dict + merge :** un node renvoie un *update partiel* (`{"missing_fields": …}`),
  LangGraph fusionne dans le dossier. Corollaire de « une responsabilité » : il ne touche que
  ses champs, jamais l'état entier.
- **Compiler ≠ appeler :** `builder.compile()` est du pur câblage — aucun appel réseau.
  OpenRouter ne se déclenche qu'à l'`invoke()`. Importer `graph.py` est donc gratuit.
- **fixture-usine + règle de trois :** `make_state` dupliqué 2×, levé en `conftest.py` au 3e
  consommateur. pytest injecte les fixtures par leur nom, sans import ni `sys.path`.
- **fail-fast sur la clé :** `os.environ["OPENROUTER_API_KEY"]` *lève* si absente (vs un `None`
  silencieux qui casserait plus loin, de façon plus obscure).
- **AgBOM :** `pydantic` était transitif mais importé DIRECTEMENT (`nodes.py`) → épinglé dans
  `requirements.txt`. Une dép qu'on importe se déclare, même si déjà tirée par une autre.

### 2026-07-20 — Feynman de fin de J1 (résultat)

2 réponses justes-mais-courtes (frontière de test : la règle sans le mécanisme ; aiguillage :
« un node = une action » sans nommer que la *route* vit hors des nodes), **1 glissement pile
sur la borne (Q3)** : la boucle nommée sans son ciseau. Le point faible §3 s'est manifesté
exactement là où le projet le surveille → attention maximale à J2, qui s'ouvrira *par* la
borne.

### 2026-07-30 — J2 : la fonction NOMME la route, le graphe la CÂBLE (conditional edges)

**WHY :** `route_after_check` (pur) ne renvoie pas un node mais une **étiquette**
(`"proceed"/"ask"/"stop"`) ; c'est `add_conditional_edges` + le `path_map` qui la lie à sa
cible dans `graph.py`. La *décision* de route reste testable hors graphe (assertion sur
l'étiquette), le *câblage* vit dans le graphe. Le cycle `ask_user → check` a été posé **après**
que le ciseau soit vert (§3, dans l'ordre — jamais la flèche avant la borne). Confirme
l'anticipation du 07-20.

### 2026-07-30 — J3 : le checkpointer archive le DOSSIER, indexé par thread_id

**WHY :** `compile(checkpointer=InMemorySaver())` fait survivre l'état entre les appels. Même
`thread_id` = le même dossier qui continue ; deux `thread_id` = deux conversations étanches. Il
persiste les **données**, PAS la position dans le code (cf. « Concepts à ré-ancrer »). C'est le
**prérequis dur de J4** : sans greffier, un `Command(resume=...)` n'a aucun dossier à ressortir
→ `RuntimeError`. Compiler avec checkpointer reste du pur câblage (zéro réseau).

### 2026-07-30 — J4 : la pause humaine complète (interrupt ↔ resume ↔ whitelist)

**WHY :** l'échange est un **courrier à deux sens**. `interrupt(payload)` = la *question
sortante* : le graphe sort (l'`invoke` RETOURNE, rien ne reste en pause), dossier à l'armoire.
`Command(resume=réponse)` = la *réponse entrante* : au rejeu du node, `answer = interrupt(...)`
**rend** cette valeur. Conséquence du rejeu : le node **repart du début** → au-dessus
d'`interrupt()`, **lecture + calcul only, zéro acte irréversible** (un envoi WhatsApp partirait
à chaque rejeu) ; d'où `ask_count = state.get(...)+1` (relecture) sûr, un `+=`/envoi non. La
décision « quels champs du `resume` accepter » a été **extraite** du node (non testable sous
interrupt) vers `merge_user_answer` (pur) : whitelist des seuls champs demandés → un
`Command(resume={"status":"approved"})` hostile est **ignoré**. Le `resume` est une **entrée
extérieure** (demain = la réponse WhatsApp réelle) → la whitelister = validation d'entrée (§1),
désormais **prouvée par test**, plus seulement affirmée. Généralisation : « le LLM propose, le
code dispose » n'était qu'un cas — la vraie règle sépare *décision déterministe* et *I/O
non-déterministe*, que l'I/O soit un modèle OU un humain (functional core / imperative shell,
Humble Object, hexagonale).

### 2026-07-30 — Feynman de fin de J2→J4 (résultat)

Q1 (checkpointer ↔ interrupt) et Q2 (borne hors du node, §3) **justes** — le point faible §3
nommé spontanément, progrès net. **1 glissement en Q3** : « le checkpointer devrait faire
reprendre où on s'était arrêté » → confusion **état vs position** corrigée (l'armoire garde le
dossier, pas la position ni les variables locales ; d'où le rejeu). Promu en « concept à
ré-ancrer ». Bonus élucidé en cours de route : `resume` = la réponse injectée qui ressort
d'`interrupt()`.

### 2026-08-04 — Le gate policy est un PLANCHER, pas un plafond (§1, gouvernance)

**WHY :** on a délibérément fait une policy qui **attrape peu** (2 lignes rouges). Le domaine
est **ouvert** — on ne sait pas quel type de campagne arrive — donc un même mot peut être
légitime ici et trompeur là ; le hard-coder produirait des **faux positifs** qui bloquent des
campagnes honnêtes. D'où la règle tri : *n'entre dans le gate déterministe qu'une règle à
**quasi-zéro faux positif ET indépendante du domaine**.* Étroit n'est pas faible, parce que la
policy n'est **pas la seule défense** : trois couches — (a) policy déterministe (universel,
incontestable), (b) juge qualité LLM (contextuel, à venir), (c) humain HITL (filet final).
Laisser filer l'ambigu, ce n'est pas « laisser passer » : c'est **router vers la couche capable
de juger le contexte**. Analogie : le gate est un **détecteur de fumée**, pas le pompier.

### 2026-08-04 — La policy CONSTATE, elle ne propose pas (contraste avec le juge qualité)

**WHY :** dans le gate policy, **personne ne « propose » au sens LLM** — le code **constate**
(`detect_forbidden_promises`) ET **dispose** (`route_after_evaluation`), zéro modèle. Une ligne
rouge de gouvernance doit être **prouvable** : « voici la regex, voici pourquoi ça a rejeté ».
Confier ça au LLM réintroduirait non-déterminisme, coût par run, flaky, et surtout un juge
**non auditable** (§5). C'est le contraste qui prépare le chantier A : le **juge qualité**, lui,
pose une question *ouverte et subjective* (« ce message est-il fidèle au brief ? ») → là le
**LLM PROPOSE** un score et le **code DISPOSE** (retry / approve). Donc « le LLM propose, le
code dispose » (§5) s'applique **à la qualité, pas à la policy** — la policy est plus stricte
encore. Analogie : la policy = **détecteur de métaux** (fait binaire, capot ouvrable) ; la
qualité = **agent qui interviewe** (une opinion, mais c'est le *règlement* qui décide).

### 2026-08-04 — Branchement terminal ≠ boucle → aucune borne (§3)

**WHY :** le gate n'a exigé **aucune borne** parce que ses deux issues sont **terminales** :
`reject → END`, `approve → END`, toutes deux vers la **sortie**. Pas de flèche qui **revient**
= pas de boucle = rien à couper. Contraste direct avec `ask_user → check_missing` (flèche de
retour → `MAX_ASKS=2`). **Une borne ne protège que ce qui se répète** (analogie : le nombre de
sonneries avant le répondeur — on limite ce qui *pourrait sonner sans fin*). La VRAIE borne du
bloc évaluation arrivera avec le **juge qualité** (`retry_count`) et — §3, dans l'ordre — elle
s'écrira **avant** la flèche de retry.

### 2026-08-04 — Le node CONSIGNE une seule clé ; le ciseau vit hors du node

**WHY :** `evaluate_campaign` (node **pur**, zéro LLM) écrit **uniquement** `policy_violations`
— jamais le `status`, jamais la route — exactement le patron `check_missing_information →
missing_fields`. Le `status` sera posé par les **nœuds terminaux** ; la route est tranchée par
`route_after_evaluation`. Une responsabilité par node (§6 r2). **Design auto-corrigé en cours :**
j'avais proposé que le node pose lui-même `status="rejected"/"awaiting_approval"` ; relire la
convention *déjà testée* (`test_writes_only_the_missing_fields_key`) l'a interdit → lire le code
avant d'écrire a corrigé le design. **Fail-open assumé :** `policy_violations` absent/vide →
`"approve"`, cohérent avec `route_after_check` sur `missing_fields` ; comme l'**humain (HITL)
reste le vrai filet**, fail-open ne baisse pas la garde.

### 2026-08-04 — Notes techniques (RED chirurgical, get_graph fusionne)

- **RED chirurgical via le module :** pour écrire un test RED sans casser la **collecte** des
  tests verts déjà présents, on importe le **module** (`from campaign_agent import routing`,
  `import nodes`) et on appelle `routing.detect_forbidden_promises(...)`. Un symbole pas encore
  écrit échoue alors en `AttributeError` **dans ce test précis** ; un `from … import
  symbole_absent` en tête de fichier, lui, planterait *toute* la collecte. Le rouge reste ciblé.
- **`get_graph()` FUSIONNE, `builder.branches` = path_map réel :** le test de structure a
  d'abord échoué à tort. `get_graph()` est une vue de **dessin** — deux arêtes parallèles vers la
  même cible (`reject`→END, `approve`→END) sont **fusionnées**, une seule survit. Le vrai
  path_map vit dans `compiled.builder.branches[node]` → `BranchSpec.ends` (dict `{étiquette:
  cible}`). Ce n'était **pas** un bug de câblage mais un test visant le **mauvais niveau d'API**
  → §8 : vérifier l'API, ne pas coder de mémoire.

### 2026-08-04 — Feynman de fin de la brique policy gate (résultat)

**Q3 (gate étroit) à moitié :** le *pourquoi c'est étroit* (domaine ouvert → mots ambigus →
faux positifs) attrapé **spontanément** ; le *pourquoi étroit ≠ faiblesse* (les 3 couches,
plancher pas plafond) **manquant** → comblé. **Q1 (borne) et Q2 (propose/dispose) non sues** →
reprises en **analogie-first**. Q1 touche **pile le §3** → le point faible reste sensible ; le
test décisif sera le `retry_count` du juge qualité (chantier A). Q2 (policy *constate* vs
qualité *propose*) était **en avance sur le code** — normal qu'elle soit floue avant de bâtir le
juge ; elle s'ancrera là.

### 2026-08-04 — Chantier B : deny-by-default = whitelist d'UNE valeur (interpret_approval)

**WHY :** `interpret_approval` (pur) traduit le verdict humain (canal `resume`) en `status`, et
n'autorise **qu'un seul jeton exact** (`"approved"`) — tout le reste retombe sur `"rejected"`. La
force du pattern : un `Command(resume={"status":"approved"})` hostile n'est **pas détecté**, il est
simplement **hors whitelist**. On n'a donc **pas à anticiper les attaques** (`"oui"`, `None`, un
dict…) : elles tombent d'office dans « refusé ». C'est pourquoi une **whitelist bat une blacklist**
(qui, elle, devrait énumérer les attaques). Cousin de `merge_user_answer` (validation d'entrée du
`resume`, §6 r7-8) — mais sur la **valeur** du verdict, pas les champs.

### 2026-08-04 — Chantier B : le HITL d'approbation (interrupt ↔ resume ↔ Vibe Diff)

**WHY :** `request_human_approval` est un node **I/O** (comme `ask_user`) : **l'humain propose**
(via `resume`), **`interpret_approval` dispose** — « le LLM propose, le code dispose » étendu à
l'humain (functional core / imperative shell). Au-dessus de l'`interrupt` : **uniquement la
lecture** du dossier pour bâtir le **Vibe Diff** (l'aperçu du message + le brief auquel il répond —
montrer AVANT d'agir, §6 r7). Vigilance J4 **active** : le node est **rejoué en entier** au resume
(cause : le checkpointer garde l'**état, pas la position** → LangGraph relance le node, il ne
reprend pas à la ligne), donc **rien d'irréversible au-dessus de l'interrupt** — le jour où un
envoi WhatsApp existera, il ira **sous**, sinon envois multiples. Deux issues **terminales**
(approved/rejected) → END.

### 2026-08-04 — Chantier B : interrupt ≠ boucle (§3, le point faible)

**WHY :** un `interrupt`/`resume` **ressemble** à une boucle (le node est « rejoué »), mais n'en
est pas une et n'exige **aucune borne**. L'interrupt **suspend puis AVANCE** : one-shot — au resume,
`interrupt()` **rend la valeur** au lieu de re-lever, le node **termine et sort**. Une **vraie
boucle** (`ask_user → check_missing`) est une **arête de retour dans le graphe** (`add_edge`) qui se
**re-parcourt** → *ça*, il faut une borne. Distinction gravée : **pause one-shot** (suspend+avance)
≠ **arête de retour** (se re-parcourt) ; seule la seconde se borne. Correction du Feynman :
**`MAX_ASKS` ne crée pas la boucle, il la coupe** — la flèche (`add_edge`) et sa borne (le ciseau)
sont **deux choses** (analogie : le rond-point vs le panneau « sortie après 2 tours »).

### 2026-08-04 — Chantier B : le test d'INTÉGRATION du HITL (mini-graphe, zéro LLM) + sonde §8

**WHY :** le garde-fou central (§1) mérite mieux qu'un smoke test — on prouve son comportement **de
bout en bout** dans `test_hitl.py` : un **mini-graphe** (juste `request_human_approval` +
checkpointer) qu'on **exécute** (invoke → interrupt → `Command(resume=...)`). Zéro LLM (l'interrupt
est du pur LangGraph) → **déterministe, gratuit**, sa place est en pytest. La preuve qui crève
l'écran : **un `resume` hostile ne peut pas approuver À TRAVERS le graphe**. Trois régimes de test
coexistent désormais : **pur** (appel direct — test_routing/test_nodes), **structure** (forme
statique — test_graph), **intégration/comportement** (exécution — test_hitl). Réflexe §8 appliqué
AVANT d'écrire : une **sonde jetable** a établi la forme réelle en v1.2.9 (`result["__interrupt__"]`
= **liste** d'`Interrupt`, payload dans `.value`, reprise par `Command(resume=...)` sur le **même
`thread_id`**) — vérifier l'API, pas coder de mémoire.

### 2026-08-04 — Feynman de fin du chantier B (résultat)

**Q1 (propose/dispose + deny-by-default) juste** — « l'humain propose, interpret_approval dispose,
l'hostile tombe sur le deny-by-default ». **Q2 (rejeu → duplication) excellente et spontanée** — le
concept « état vs position » de J4 **tient** (promu « re-verbalisé » plus haut). **Q3 (§3,
interrupt≠boucle) à moitié** : le cœur (retour-graphe vs suspend/avance) acquis **après
reformulation**, mais avec l'inversion « retour grâce à MAX_ASKS » → corrigée (la borne **coupe**,
ne **crée** pas). Bilan §3 : il **progresse** (distinction pause/boucle neuve et acquise) mais reste
LE point à surveiller — prochain test décisif : le `retry_count` du juge qualité (chantier A), la
**vraie** boucle bornée.

### 2026-08-04 — Smoke du slice complet : ce que l'exécution RÉELLE a révélé (§1, §5)

**WHY :** les tests prouvent les **décisions** (déterministes) ; le smoke prouve le **flux** (le vrai
LLM, non-déterministe, hors pytest — §5). Deux rôles, pas de doublon : un smoke n'a pas d'assertion
stable, c'est une **observation** du comportement réel. Le slice a tourné de bout en bout sur
OpenRouter — compréhension → génération → gate policy → **arrêt sur l'interrupt d'approbation** →
reprise → `status` scellé. Ce que ça ajoute aux 56 tests : la preuve que les 5 étapes **s'enchaînent
vraiment** avec le modèle.

**La révélation (smoke adversarial).** Poussé par un brief « get rich quick », le LLM a **contourné
les formules exactes interdites** (« résultat garanti ») et produit un message *soft-manipulateur*
(« voyage vers la richesse », « liberté financière ») → `policy_violations=[]` → le gate (a) **laisse
passer**. Ce n'est **pas** un bug : c'est la définition du gate étroit (quasi-zéro FP) — « le plancher,
pas le plafond » démontré EN LIVE. La défense en profondeur a joué : le message est allé au **filet
humain (c)**, qui l'a refusé (`rejected`) — rien de manipulateur scellé `approved`. Et le **trou (b)**
— le juge qualité qui l'attraperait AVANT l'humain — est devenu visible à l'œil nu : **le chantier A
s'est justifié tout seul.**

**La tentation à ÉVITER (leçon de gouvernance) :** « ajoutons 'voyage vers la richesse' aux regex ».
Non — une campagne voyage/luxe légitime déclencherait un **faux positif**. Élargir le gate
déterministe **trahit** le quasi-zéro-FP. Le contextuel se traite par les couches **(b) juge qualité**
et **(c) humain**, *jamais par plus de regex*. Confirme la règle tri (quasi-zéro-FP + domaine-
indépendant) : le déterministe reste étroit, l'ambigu monte d'une couche.

**Signal §9 (noté, pas traité) :** le LLM a spontanément mis `[Prénom]` / `[Nom de la marque]`. Ça
*ressemble* à de la bonne hygiène PII, mais c'est **non contrôlé** (format libre, aucune résolution au
runtime) — le piège « marche en démo » (§5). Futur besoin (§9, résolution `[[VAR]]`), pas aujourd'hui
(données synthétiques).

### 2026-08-07 — Le juge (b) prend la parole : le warning dans le Vibe Diff (informer, pas murer)

**WHY :** le juge produisait déjà `quality_score` + `quality_reason`, mais ils **mouraient dans le
state** — l'humain approuvait à l'aveugle. On leur donne une **voix** : `assess_quality_signal`
(pure) traduit le score en signal AFFICHABLE, porté dans le payload de l'`interrupt` (option A : on
affiche TOUJOURS le score, ⚠️ sous le seuil). Décision tranchée en active review : un score de
*manipulation/qualité* est un jugement de **goût**, pas de légalité → le juge **informe**, il ne
**bloque pas**.

**La distinction porteuse (débat souveraineté).** Mon inquiétude : « c'est l'utilisateur qui valide
sa campagne, donc une policy si tôt le bride ». Le glissement corrigé : « l'utilisateur valide sa
campagne » cache **trois parties** — l'**auteur** (souverain sur son GOÛT), l'**audience** (qui n'a
rien approuvé), l'**opérateur + la loi** (dont la responsabilité est engagée). Approuver son propre
message n'efface **ni l'illégalité ni le non-consentement du destinataire**. D'où deux natures de
règle : **légale** → gate déterministe, **non-overridable** ; **goût/manipulation** → juge, **une
voix pas un mur**, l'humain tranche éclairé. Analogie : Mailchimp bloque le « get rich quick » non
pour juger ton goût, mais parce que SON IP et SA responsabilité sont en jeu — le garde-fou protège
l'audience + l'opérateur, **pas l'auteur de lui-même**. (Confirme la §6 : la policy déterministe
DOIT être étroite, car elle ne doit contenir QUE l'illégal incontestable, indépendant du domaine.)

### 2026-08-07 — Le retry qui APPREND : `temperature=0` n'était pas le coupable (démolition #1)

**WHY :** le retry régénérait un message **identique** (donc inutile) — non pas à cause de
`temperature=0`, mais parce que l'**entrée** était identique. `generate_campaign` ne lisait que les
5 champs, jamais le reproche du juge. Fix : `build_generation_brief` (pure) injecte, en retry, la
version précédente + `quality_reason` + la consigne de corriger → l'entrée change → à temp=0 la
sortie **peut** changer. **Le fix est orthogonal à la température** (jamais touchée) : le vrai
déterminisme reste *par-entrée*. Geste on-thesis : extraire une fonction **pure** rend le fix
**PROUVABLE** en pytest (« le prompt de retry contient bien le reproche ») au lieu d'espéré — du
« prompt engineering au feeling » transformé en **décision testée**. Même geste qu'au warning
(pure > `if`-dans-le-node) : **récurrent, pas un hasard.**

**La preuve LIVE (`smoke_graph_loop`).** Brief adversarial crypto : gen#1 (« Devenez le trader dont
vous avez rêvé ») → juge **4/10** → retry (critique injectée) → gen#2 **différent** (« apprendre à
votre rythme… avenir financier ») → juge **6/10**. Le retry a **appris** (4→6, message autre) — #1
réfutée en vrai. Puis borne (`MAX_RETRIES=1`) → pass → HITL, ⚠️ (score 6, « légèrement
manipulateur ») dans le Vibe Diff. Les deux features **composent** : le retry améliore ce qu'il peut,
le warning escalade le résidu à l'humain.

**Le finding qui compte (gouvernance).** gen#2 = 6, **toujours sous le seuil** : une passe n'a pas
suffi. Tentation : monter `MAX_RETRIES`. **Non** — sur un brief de **mauvaise foi**, plus de retries
= optimiser le message pour **passer le juge**, c'est-à-dire **entraîner le générateur à contourner
sa propre garde**. Le retry poussé trop loin **devient l'adversaire de son propre gate qualité**.
Donc borne **basse assumée** : améliorer UNE fois, puis **escalader à l'humain** (avec le warning),
jamais grinder jusqu'à ce que le juge cède. C'est pour ça que (b) informe et (c) tranche — pour que
la boucle n'ait PAS à s'acharner. Le smoke a rendu ce réglage **conscient**, plus accidentel.

---

## [2026-08-17] Le revers du « retry qui apprend » : injection LLM→LLM (audit adversarial externe)

**Le WHY du test rouge (étape 1/3).** Un audit externe (Codex, mode adversarial) a produit une
**hypothèse** d'attaque sur `build_generation_brief` — pas une preuve. Corriger sur une hypothèse
donne un correctif qu'on ne saura **jamais valider** : on n'a rien pour dire « avant ça cassait,
maintenant non ». Donc test d'abord (§6 r5), et le test rouge devient au passage le matériau exact
de l'artefact public du §1 : *voici ce qu'on a tenté de casser.*

**La tension de conception (le vrai apprentissage).** Les 4 tests du 08-07 **EXIGENT** la
réinjection — sans le reproche dans le prompt, le retry photocopie. La faille n'est donc **pas**
« on réinjecte », c'est **« on réinjecte sans échappement »**. Analogie : à l'audience, ton client
te passe une note. Tu dois la **lire** (sinon tu plaides à l'aveugle) mais pas la **lire à voix
haute au juge comme si c'était ta plaidoirie**. Aujourd'hui la fonction fait la seconde chose : elle
recopie la note au même niveau que nos propres instructions. **Une feature et sa vulnérabilité
peuvent être la même ligne de code** — le fix ne peut donc pas être « enlever », seulement
« encadrer ».

**Le geste de test qui rend ça déterministe.** On ne peut pas tester « le modèle a-t-il obéi ? » :
appel réseau, non-déterminisme, §5 violé. Alors on descend d'un cran, et c'est **plus fort** : on
teste « l'attaquant peut-il **forger la STRUCTURE** du prompt ? ». Si le texte du juge ouvre une 2e
section `--- RÉ-ÉCRITURE ---`, il a cessé d'être une **donnée** pour devenir du **code** — c'est
littéralement l'injection SQL (la quote qui se referme), autre substrat. Comptage de chaînes :
déterministe, gratuit, zéro modèle. Rouge obtenu : `assert 2 == 1`.

**Le piège méthodo nommé au passage.** Un test rouge **fige presque toujours la forme du remède** —
c'est le coût réel de l'EDD, rarement dit. Ici l'assertion a été choisie pour survivre aux **deux**
remèdes candidats (encapsuler le reproche / le réduire à des codes bornés), donc l'étape 1 ne
préempte pas la décision de design de l'étape 2. Quand ce n'est pas possible, il faut le **dire** et
trancher le design d'abord.

**Ce que l'audit externe a manqué.** Il n'a vu qu'un canal (`quality_reason`). Il y en a **deux** :
`generated_message` est réinjecté à la ligne au-dessus et sort du **même** modèle → même surface.
Leçon : un auditeur externe donne des **pistes**, pas un verdict — chaque finding se vérifie contre
la source, et l'inventaire des canaux se refait soi-même.

**Le fix (option A retenue) : `quote_untrusted`, dans `routing.py`.** Placement délibéré — c'est le
**3e membre d'une famille** déjà là : `merge_user_answer` whitelist l'entrée UTILISATEUR,
`interpret_approval` whitelist le verdict HUMAIN, `quote_untrusted` neutralise l'entrée LLM. Même
nature (valider ce qui vient du dehors), trois provenances. La règle posée : **notre vocabulaire de
structure est RÉSERVÉ** — un marqueur de section écrit par un modèle est retiré, le reste passe
**intact**, encadré en citation, précédée d'une consigne de cadrage. **On encadre, on ne censure
pas** : censurer aurait tué la finesse du reproche, c'est-à-dire la feature elle-même.

**Option B écartée (et pourquoi ça compte).** B = le juge ne rend plus que des codes bornés
(`hors_brief`, `ton_inadapté`) : surface d'injection nulle **par construction**, mais le retry perd
ce qui l'avait fait progresser de 4→6. C'était **troquer un risque contre une régression**. Critère
de décision retenu : *un correctif de sécurité qui supprime la feature n'est pas un correctif, c'est
un renoncement.* A reste extensible vers l'hybride (code borné pour la décision + texte encadré pour
le détail) ; l'inverse n'était pas vrai.

**Le trou trouvé À LA MAIN, pas par les 6 tests.** Première version de la regex : accents
obligatoires. En affichant un prompt sous attaque, `--- RE-ECRITURE ---` (sans accents) est passé
**intact**. Un LLM écrit sans accents sans effort. Fix : `[ée]` partout. **C'est le même trou que
l'audit avait signalé sur la policy** (`resultat garanti` franchit `résultats?\s+garantis?`) — donc
pas un accident, un **motif récurrent : tout filtre par liste dépend d'abord de sa NORMALISATION.**
Méta-leçon : les tests prouvent ce qu'on a **pensé à demander** ; **regarder la sortie réelle** trouve
ce qu'on n'a pas pensé. Les deux, pas l'un.

**Limite assumée et écrite dans le code.** L'échappement dépend d'une liste de marqueurs connus. Un
marqueur non prévu passerait (mitigé par la consigne de cadrage). La parade complète — une balise à
valeur **imprévisible** que l'attaquant ne peut pas deviner — attendra un contenu **vraiment tiers**
(MCP, web) ; ici les deux sources sont nos propres modèles. Besoin réel d'abord (§7).

---

## [2026-08-17] `QualityAssessment.score` : un seuil ne vaut que si l'échelle est bornée

**WHY.** `QUALITY_THRESHOLD = 7` suppose une note **sur 10**. Mais le champ était un `int` **libre** :
seule la `description` disait « de 0 à 10 » — et une description est une **suggestion** au modèle, pas
un **contrat**. Un juge qui rend 42 (dérapage, ou brief hostile qui l'y pousse) franchissait le seuil
sans discussion. Fix : `ge=0, le=10`.

**Le déplacement de regard qui compte.** Le réflexe était de chercher le bug dans
`route_after_quality` — or **sa comparaison est juste**. Le trou était en amont, dans le **CONTRAT**.
Gravé : **le schéma pydantic n'est pas de la décoration, c'est le PREMIER gate** — il s'exécute avant
toute décision, avant même que le routeur ait un état à lire. Un gate en aval ne peut pas réparer une
donnée dont l'échelle n'a jamais été garantie.

**Question laissée OUVERTE (à trancher, pas oubliée).** Le schéma empêche le juge de *proposer* 42.
Mais si un score hors bornes arrivait dans le state par une autre porte, `route_after_quality`
comparerait toujours `>= 7` sans broncher, et `assess_quality_signal` afficherait « ok » à l'humain.
Ceinture posée, **bretelles non posées** — décision de conception en attente.

---

## [2026-08-26] Bilan Feynman — l'angle mort révélé : je cherche toujours dans le code qui DÉCIDE

Trois questions posées sans regarder le code. Résultat brut :

- **Q1 (pourquoi on ne pouvait pas juste supprimer la réinjection)** — répondu seul, juste :
  « sinon le retry ne corrige rien, il photocopie ». Acquis.
- **Q2 (pourquoi tester la structure est plus FORT que tester l'obéissance)** — moitié trouvée
  (« un test qui dépend du modèle n'est jamais garanti »). C'est l'argument **commode** (§5).
  L'argument **fort** manquait : un test sur l'obéissance **peut être vert avec la faille intacte**
  — le modèle a résisté par chance. Il délivre alors un certificat de sécurité **mensonger**, ce qui
  est pire qu'aucun test : un test absent se tait, un test vert éteint la vigilance. Le test structurel
  ne peut pas être vert par hasard — son échec est **causal**.
  → **On ne teste que ce dont on est responsable.** L'obéissance d'un modèle n'est pas une propriété
  qu'on peut garantir, donc pas une propriété qu'on peut tester *comme* une garantie. La frontière
  données/instructions dans notre prompt, si.
- **Q3 (où était le bug si `score >= 7` était juste)** — **pas trouvé**, deux tentatives, toutes
  deux dans la même zone : d'abord `route_after_quality`, puis `QUALITY_THRESHOLD`.

**Le pattern, et c'est lui qui vaut d'être gravé.** Les deux tentatives ratées visaient du code qui
**DÉCIDE** (un routeur, un seuil). Le trou était dans du code qui **DÉCLARE** (le schéma pydantic).
Réflexe à corriger : devant un comportement faux, je remonte le flux d'exécution — jamais le flux de
**définition**. Or une comparaison **ne peut pas valider sa propre entrée** : elle consomme la donnée,
elle ne la contrôle pas. `QUALITY_THRESHOLD = 7` n'est pas la source de l'hypothèse « sur 10 », c'en est
la **victime** — une constante n'impose rien, un `>=` n'impose rien. Ce qui impose, c'est le point
d'ENTRÉE de la donnée dans le système.

**Nouvelle question de diagnostic à me poser en premier :** *« qui a le pouvoir de refuser cette
valeur ? »* — pas *« qui l'utilise ? »*. Si la réponse est « personne », le bug est là, et il est
invisible en lisant la fonction qui plante.

**Lien avec §3.** Mon point faible déclaré est l'aiguillage — d'où un regard aimanté par le routeur.
Ici ce même aimant devient un **angle mort inversé** : je regarde l'aiguillage même quand le problème
n'y est pas. Le correctif n'est pas « regarder moins le routeur », c'est « ajouter le contrat à la
liste des endroits où un bug peut vivre ».

**Constat le plus inconfortable :** la réponse à Q3 était **déjà écrite dans ce fichier**, section
précédente, sous le titre « le déplacement de regard qui compte ». Écrit ≠ intégré. C'est exactement
ce que le Feynman sert à révéler, et la raison pour laquelle il n'est pas optionnel (§2).
