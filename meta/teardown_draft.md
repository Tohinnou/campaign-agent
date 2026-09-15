# Teardown — ossature de travail

> **Ce fichier n'est PAS le teardown.** C'est le squelette : pour chaque section, la
> question à laquelle tu réponds **dans tes mots**, et la matière factuelle vérifiée
> (relevée dans ton code et tes notes, pas rédigée).
>
> Les puces « matière » sont volontairement **plates et sèches**. Si elles étaient bien
> écrites tu les recopierais, et ce serait mon teardown, pas le tien.
>
> **Cible :** ~1200-1600 mots, 7-8 min de lecture.
> **Lecteur visé :** un pair technique ou quelqu'un qui évalue des compétences en IA
> appliquée. Pas un débutant LangGraph — ce n'est pas un tutoriel.
> **Ton :** autopsie, pas brochure. On raconte ce qui a cassé.

---

## S0 — L'accroche

**Ta question :** *Un agent qui rédige du marketing à ta place — qu'est-ce qui peut mal
tourner ? Et pourquoi le vrai risque n'est-il pas qu'il plante ?*

**Matière vérifiée :**
- Le produit visé : lancer des campagnes depuis WhatsApp via des outils MCP.
- Ce cycle ne fait que le cœur métier : décrire une campagne → collecter les infos
  manquantes → générer → vérifier une politique → demander une validation humaine.
- Aucun envoi réel n'existe encore.

**Piège :** ne pas commencer par « j'ai construit un agent avec LangGraph ». Commencer par
ce qui se passe si personne ne surveille.

**Longueur :** 100-150 mots.

---

## S1 — Le système, en 30 secondes

**Ta question :** *À quoi ressemble le graphe, et quelle est la seule règle d'architecture
qui compte ?*

**Matière vérifiée :**
- 10 nodes ; 3 aiguillages conditionnels.
- Les 3 aiguillages (`route_after_check`, `route_after_evaluation`, `route_after_quality`)
  vivent dans `routing.py` — fonctions pures, zéro LLM.
- Un node ne route jamais : il remplit ou consigne une clé du state.
- `state.py` = `TypedDict` pur, aucune dépendance framework.
- Modèle réel dès le jour 1 : `openai/gpt-4o-mini`, `temperature=0`. Pas de mock.
- 87 tests déterministes ; aucun n'appelle le modèle.

**Piège :** ne pas dérouler les 10 nodes un par un. Le lecteur veut la **forme**, pas
l'inventaire. Le diagramme du docstring de `graph.py` en dit plus que trois paragraphes.

**Longueur :** 150-200 mots + le schéma ASCII.

---

## S2 — Mise en défaut n°1 : le gate déterministe laisse passer

**Ta question :** *La policy code en dur a laissé passer un message manipulateur, et je
n'ai PAS élargi la policy. Pourquoi ?*

**Matière vérifiée :**
- Smoke sur brief adversarial « get rich quick ».
- Le modèle a évité les formules interdites (`résultats garantis`, `revenus garantis`,
  `doublez votre capital`, `devenez riche`) et produit : « voyage vers la richesse »,
  « liberté financière ».
- Résultat : `policy_violations = []` → le gate laisse passer.
- Le message est allé jusqu'au filet humain, qui l'a refusé (`status = "rejected"`).
- Tentation écartée : ajouter « voyage vers la richesse » aux regex. Raison notée : une
  campagne voyage/luxe légitime deviendrait un faux positif.
- Règle qui en découle : le gate déterministe ne contient QUE l'illégal incontestable,
  indépendant du domaine. L'ambigu monte d'une couche.

**Ce qui rend cette section forte :** ce n'est pas un bug corrigé, c'est un **choix
défendu**. Le système a fait exactement ce pour quoi il était conçu, et le résultat avait
l'air d'un échec. Explique pourquoi ce n'en était pas un.

**Longueur :** 200-250 mots.

---

## S3 — Trois couches, et pourquoi trois

**Ta question :** *Qu'est-ce que chaque couche attrape que les deux autres ratent ?*

**Matière vérifiée :**
- (a) `detect_forbidden_promises` — déterministe, le code CONSTATE. Étroit par conception.
- (b) `judge_quality` — LLM, question OUVERTE (fidèle ? manipulateur ?), PROPOSE un score
  0-10 + une raison.
- (c) `interpret_approval` — humain, deny-by-default : seul le jeton exact `"approved"`
  approuve ; refus, faute de frappe, `None`, dict hostile → `"rejected"`.
- Le juge ne bloque pas : `assess_quality_signal` affiche toujours le score dans l'aperçu
  (⚠️ sous le seuil), l'humain tranche éclairé.
- La distinction qui a tranché ce choix : règle **légale** → gate non-overridable ; règle
  de **goût / manipulation** → une voix, pas un mur.
- L'argument des trois parties : l'auteur (souverain sur son goût), l'audience (qui n'a
  rien approuvé), l'opérateur + la loi (dont la responsabilité est engagée).

**Piège :** « défense en profondeur » est un slogan. Ce qui convainc, c'est le cas concret
de S2 qui montre (a) échouant et (c) rattrapant.

**Longueur :** 250-300 mots.

---

## S4 — Mise en défaut n°2 : le retry qui photocopie

**Ta question :** *Mon retry régénérait un message identique. Pourquoi `temperature=0`
n'était pas le coupable — et qu'est-ce que le vrai fix m'a appris sur où placer un fix ?*

**Matière vérifiée :**
- Cause réelle : l'entrée était identique. `generate_campaign` ne lisait que les 5 champs,
  jamais le reproche du juge.
- Fix : `build_generation_brief` (pure) injecte en retry la version précédente +
  `quality_reason` + la consigne de corriger.
- Preuve live : gen#1 « Devenez le trader dont vous avez rêvé » → juge **4/10** → retry →
  gen#2 « apprendre à votre rythme… avenir financier » → juge **6/10**.
- Le fix est orthogonal à la température (jamais touchée).
- Extraire une fonction **pure** rend le fix prouvable en pytest au lieu qu'espéré.
- gen#2 = 6, toujours sous le seuil de 7. **Je n'ai pas monté `MAX_RETRIES`.** Raison :
  sur un brief de mauvaise foi, plus de retries = optimiser le message pour passer le
  juge, donc entraîner le générateur à contourner sa propre garde.

**Ce qui rend cette section forte :** la dernière puce. Refuser d'améliorer un chiffre est
plus intéressant que l'améliorer.

**Longueur :** 250-300 mots.

---

## S5 — Mise en défaut n°3 : l'audit adversarial

**Ta question :** *J'ai fait auditer mon agent par un modèle adverse. Qu'a-t-il trouvé que
mes 77 tests verts ne voyaient pas — et pourquoi « enlever la feature » n'était pas une
option ?*

**Matière vérifiée :**
- 14 constats rendus.
- Le constat central : **injection LLM→LLM**. `build_generation_brief` réinjectait le
  reproche du juge dans le prompt du rédacteur, sans échappement. Un juge influencé par un
  brief hostile pouvait y écrire `--- RÉ-ÉCRITURE ---` et cesser d'être une donnée pour
  devenir une instruction.
- **La feature de S4 et la vulnérabilité étaient la même ligne de code.**
- L'audit avait manqué un second canal : le `generated_message` précédent, réinjecté lui
  aussi.
- Fix : `quote_untrusted` — encadre en citation, neutralise les marqueurs réservés.
  On encadre, on ne censure pas (censurer aurait tué la finesse du reproche = la feature).
- Les tests comptent les occurrences d'un marqueur, jamais « le modèle a-t-il obéi ». Un
  test sur l'obéissance peut être vert avec la faille intacte.
- Trouvé **à la main**, pas par les tests : l'échappement ne marchait qu'avec les accents.
  `RE-ECRITURE` passait. Même trou de normalisation que la policy sur `resultat garanti`.
- Second constat : `QualityAssessment.score` n'avait aucune borne. Un juge rendant 42
  franchissait `>= 7` sans discussion. La comparaison était juste ; le **contrat** était
  troué. Fix : `ge=0, le=10`.

**Piège :** cette section peut avaler tout le teardown. Tiens-la serrée. Deux idées
suffisent — « une feature et sa faille peuvent être la même ligne » et « le schéma est le
premier gate, et il ne ressemble pas à un gate ».

**Longueur :** 300-350 mots. C'est la section la plus longue, et c'est normal.

---

## S6 — Ce que je n'ai pas couvert

**Ta question :** *Qu'est-ce qui reste ouvert dans ce système, et pourquoi j'ai choisi de
le laisser ouvert plutôt que de le boucher ?*

**Matière vérifiée :**
- Deux fail-opens assumés : `route_after_evaluation` et `route_after_quality` renvoient la
  route permissive sur un champ absent. Justification écrite dans le code : elles
  n'acheminent que vers le HITL, qui reste le dernier filet.
- La sortie `MAX_ASKS` (`route_after_check` → `"stop"` → `END`) n'écrit **aucun status**.
  3 des 5 valeurs de `CampaignStatus` (`collecting_information`, `generating`,
  `awaiting_approval`) ne sont écrites nulle part.
- « Ceinture posée, bretelles non posées » : le schéma empêche le juge de proposer 42, mais
  `route_after_quality` ne valide toujours pas l'échelle de ce qu'il lit.
- `quote_untrusted` repose sur une liste de marqueurs. Un marqueur inventé passerait. La
  parade complète (balise à valeur imprévisible) est différée jusqu'à l'entrée d'un contenu
  vraiment tiers (MCP, web).
- Le LLM a spontanément produit `[Prénom]` / `[Nom de la marque]` : ça **ressemble** à de
  l'hygiène PII mais c'est non contrôlé, aucune résolution au runtime.
- Pas encore : LangSmith, WhatsApp, MCP, multi-tenant.

**Ce qui rend cette section forte — et c'est la signature du teardown :** gouverner un
agent, ce n'est pas prétendre tout couvrir. C'est pouvoir énoncer précisément ce qu'on ne
couvre pas, et pourquoi. Un lecteur technique croira le reste **à cause** de cette section.

**Piège :** ne pas t'excuser. Ce sont des décisions, pas des oublis. Écris-les comme telles.

**Longueur :** 200-250 mots.

---

## S7 — La leçon (optionnel, court)

**Ta question :** *Après tout ça, quelle est la seule question que je me pose maintenant
devant un comportement faux, et que je ne me posais pas avant ?*

**Matière :** tu l'as trouvée hier, elle est dans `learning_notes.md`. Ne la recopie pas —
reformule-la, et dis ce qu'elle t'aurait fait trouver plus tôt.

**Longueur :** 80-120 mots. Une seule idée. Si tu en mets trois, aucune ne reste.

---

## Ordre d'écriture conseillé

Pas S0 → S7. Écris **S2, S4, S5 d'abord** (les trois mises en défaut) : c'est là qu'est la
matière et l'énergie. S0, S1, S3 se rédigent tout seuls après, parce que tu sauras ce
qu'ils doivent préparer. S6 en avant-dernier, S7 en dernier.

Si tu bloques sur une section : écris la réponse à la question **à l'oral**, en une phrase,
sans chercher à bien écrire. La phrase orale est presque toujours la bonne.
