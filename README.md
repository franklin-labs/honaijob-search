<!--
README du projet HonaïJob-search.
Ce fichier décrit le fonctionnement de l’outil défini dans main.py (crawler sémantique asynchrone).
-->

# HonaïJob-search 1.0

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Async](https://img.shields.io/badge/Async-asyncio%20%2B%20aiohttp-5c8df6)](#-fonctionnement)
[![Search](https://img.shields.io/badge/Search-DuckDuckGo-DD6829)](#-fonctionnement)
[![LLM](https://img.shields.io/badge/LLM-aucun_utilisé-success)](#-fonctionnement-sans-llm)
[![Status](https://img.shields.io/badge/Status-Prototype-orange)](#-defauts-actuels)

HonaïJob-search est un **prototype de crawler sémantique asynchrone** pour explorer des
**offres d’emploi / stages tech** à partir d’une simple requête texte (Python).

Il interroge DuckDuckGo, télécharge les pages en parallèle, extrait le texte, calcule une
similarité sémantique avec la requête, puis affiche les résultats les plus pertinents
dans un tableau richement formaté dans le terminal.

---

## Navigation

Utilisez ces “onglets” cliquables pour naviguer rapidement dans le README :

| Navigation | |
|-----------|--|
| [Accueil](#accueil) | [Fonctionnement](#fonctionnement) |
| [Installation](#installation) | [Utilisation](#utilisation) |
| [Architecture](#architecture-technique) | [Défis rencontrés](#défis-rencontrés) |
| [Défauts actuels](#analyse-des-défauts-actuels) | [Perspectives d’amélioration](#perspectives-damélioration) |

---

## Accueil

HonaïJob-search 1.0 est un outil en ligne de commande qui :

- récupère une liste d’URLs via DuckDuckGo (librairie **`ddgs`**),
- télécharge les pages de manière asynchrone avec **`aiohttp`**,
- extrait le contenu textuel avec **`BeautifulSoup`**,
- encode la requête utilisateur et le contenu avec **`sentence-transformers`**,
- calcule une **similarité cosinus** entre la requête et chaque page,
- applique un filtrage métier (mots-clés emploi / compétences / contrat),
- affiche un **tableau coloré** des résultats dans le terminal via **`rich`**.

Usage principal : trouver rapidement des pages web susceptibles de contenir des
**offres d’emploi ou de stage tech** liées à une requête donnée (ville, techno, type de contrat, etc.).

---

## Fonctionnement

### Vue d’ensemble

Le cœur du système se trouve dans [`main.py`](./main.py) et repose sur :

- une classe **`EmbeddingModel`** pour générer des embeddings de phrases,
- une structure **`QueryIntent`** pour représenter l’intention de la requête,
- une structure **`SemanticResult`** pour stocker les résultats scorés,
- une classe **`HonaïJobCrawler`** qui orchestre la recherche,
- une fonction **`main()`** qui gère l’interface CLI et l’affichage.

Flux global :

1. L’utilisateur saisit une requête dans le terminal.
2. Le crawler interroge DuckDuckGo pour obtenir une liste d’URLs.
3. Les pages sont téléchargées en parallèle (asyncio + aiohttp).
4. Le texte est extrait (paragraphes, listes, titres…).
5. La requête et chaque page sont encodées en vecteurs via `SentenceTransformer`.
6. Une **similarité cosinus** et des **heuristiques de mots-clés** sont calculées.
7. Les résultats sont triés par score décroissant.
8. Un tableau synthétique est affiché dans le terminal (titre, URL, score, contrat, skills, extrait).

### Fonctionnement sans LLM

L’outil **ne fait appel à aucun LLM externe** (type ChatGPT / GPT-4, API cloud, etc.).

À la place, dans la version actuelle, il utilise :

- un **modèle d’embedding local** (`sentence-transformers/all-MiniLM-L6-v2`) chargé via
  `SentenceTransformer`,
- des **mots-clés métier** chargés depuis un fichier `keywords.json`,
- des **heuristiques de scoring** simples basées sur la similarité cosinus et la présence de mots-clés.

#### Mots-clés métier (keywords.json)

Le fichier `keywords.json` contient des listes de mots-clés qui décrivent votre “métier” ou votre contexte
de recherche (emploi, technologies, lieux, types de contrat, compétences, etc.).

Au démarrage, ces listes sont chargées en mémoire et converties en ensembles Python :

- `EMPLOYMENT_KEYWORDS` : mots liés à l’emploi et aux offres (emploi, offre, stage, alternance…),
- `TECH_JOB_KEYWORDS` : mots décrivant des postes ou domaines techniques (développeur, backend, data…),
- `LOCATION_KEYWORDS` : villes ou contextes géographiques (paris, lyon, remote…),
- `TIME_KEYWORDS` : termes liés au temps ou à la fraîcheur (aujourd’hui, récent, nouveau…),
- `SKILL_KEYWORDS` : compétences techniques (python, django, react, sql…),
- `CONTRACT_KEYWORDS` : types de contrat (cdi, cdd, freelance, stage, alternance, intérim…).

Ces ensembles sont ensuite utilisés pour :

- interpréter l’intention de la requête (fonction `infer_query_intent`),
- filtrer les pages qui ne parlent pas du tout d’emploi ou de compétences,
- détecter et afficher, pour chaque page, les compétences et le type de contrat repérés.

Pourquoi ce choix ?

- ✅ **Indépendance vis-à-vis des API externes** : pas de clé API, pas de coût variable.
- ✅ **Reproductibilité** : à environnement égal, même requête ⇒ mêmes scores.
- ✅ **Simplicité de déploiement** : tout tourne en local, dans un simple script Python.
- ✅ **Contrôle explicite du comportement** : pas de génération de texte “boîte noire”.

Limitations de cette approche sans LLM :

- ❌ **Compréhension limitée** : pas de raisonnement complexe ni de reformulation fine.
- ❌ **Pas de résumé ni d’extraction avancée** : seule une portion brute de texte est affichée.
- ❌ **Adaptation au domaine réduite** : la pertinence dépend fortement de la qualité des mots-clés dans `keywords.json`.

### Algorithmes et méthodes utilisées

1. **Recherche de pages**  
   - Utilisation de **`ddgs.DDGS().text(...)`** pour exécuter une recherche DuckDuckGo.
   - Filtrage des URLs internes DuckDuckGo.

2. **Téléchargement asynchrone**  
   - Création d’une **`aiohttp.ClientSession`**.
   - Lancement concurrent de requêtes HTTP via `asyncio.gather`.
   - Timeout par requête (15s) et gestion des erreurs réseau avec logs.

3. **Extraction de texte**  
   - Parsing HTML avec **`BeautifulSoup`**.
   - Extraction du texte sur les balises `p`, `li`, `article`, `h1`, `h2`, `h3`.
   - Nettoyage du texte (espaces, séparateurs).

4. **Prétraitement et embeddings**
   - Normalisation du texte : minuscules, suppression des accents (`unicodedata`), trimming.
   - Tokenisation simple alphanumérique.
   - Encodage des textes (requête + contenu tronqué) en vecteurs à l’aide de
     **`SentenceTransformer`** exécuté dans un thread via `asyncio.to_thread`.

5. **Scoring sémantique**
   - Calcul de la **similarité cosinus** avec **`numpy`** entre vecteurs requête / page.
   - Calcul d’un ratio de **mots-clés de la requête présents dans la page**.
   - Détection de termes de récence (`"24h"`, `"aujourd'hui"`, `"hier"`, `"récent"`, `"nouveau"`).
   - Score final combiné :

     ```text
     score = 0.5 * similarité_cosinus
           + 0.4 * ratio_mots_clés
           + 0.1 * bonus_si_date_récente
     ```

6. **Détection de compétences et type de contrat**
   - Détection de **skills** : intersection entre les tokens de la page et `SKILL_KEYWORDS`.
   - Détection de **contrat** : premier token présent dans `CONTRACT_KEYWORDS`.

7. **Affichage**
   - Construction d’un tableau `rich.Table` :
     - colonnes : `Titre`, `URL`, `Score`, `Contrat`, `Skills`, `Extrait`.
   - Affichage dans une `rich.Console`.

---

## Installation

### Prérequis

- Python **3.10+** (recommandé)
- Accès réseau sortant (pour interroger DuckDuckGo et télécharger les pages)

### Cloner le projet

```bash
git clone https://github.com/franklin-labs/honaijob-search.git
cd honaijob-search/crawller
```

### (Optionnel) Créer un environnement virtuel

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### Installer les dépendances

Installation directe :

```bash
pip install aiohttp ddgs sentence-transformers numpy beautifulsoup4 rich
```

Vous pouvez également utiliser un `requirements.txt` (à compléter si besoin) :

```bash
pip install -r requirements.txt
```

### Configurer les mots-clés (keywords.json)

À la racine du dossier `crawller`, créer un fichier `keywords.json` si ce n’est pas déjà fait :

```json
{
  "employment_keywords": ["emploi", "offre", "stage", "alternance"],
  "tech_job_keywords": ["développeur", "backend", "frontend", "data", "python"],
  "location_keywords": ["paris", "lyon", "remote"],
  "time_keywords": ["aujourd'hui", "hier", "récent", "nouveau"],
  "skill_keywords": ["python", "django", "react", "sql"],
  "contract_keywords": ["cdi", "cdd", "freelance", "temps plein", "temps partiel", "stage", "alternance", "intérim"]
}
```

Ce fichier alimente les constantes :

- `EMPLOYMENT_KEYWORDS`
- `TECH_JOB_KEYWORDS`
- `LOCATION_KEYWORDS`
- `TIME_KEYWORDS`
- `SKILL_KEYWORDS`
- `CONTRACT_KEYWORDS`

chargées au démarrage du script.

---

## Utilisation

### Lancer le crawler

Depuis le dossier `crawller` :

```bash
python main.py
```

Le programme :

1. Demande une requête de recherche dans le terminal.
2. Si vous laissez la ligne vide, il utilisera par défaut :  
   `offre de stage étudiant Paris python`.
3. Lance la recherche, télécharge les pages, calcule les scores.
4. Affiche un tableau trié par pertinence.

### Exemple de requêtes

```text
offre de stage étudiant Paris python
alternance data engineer lyon
emploi développeur backend remote django
```

### Exemple de sortie (simplifiée)

```text
╔══════════════════════════════════════════════════════════════════════════════╗
║                  Résultats de recherche pour : offre stage python           ║
╠══════════════╤═════════════════════════════╤═══════╤════════╤═══════╤═══════╣
║ Titre        │ URL                         │ Score │ Contrat│ Skills│ Extrait
╟──────────────┼─────────────────────────────┼───────┼────────┼───────┼───────╢
║ Stage Python │ https://exemple.com/offre…  │ 0.87  │ stage  │ python│ ...   │
╚══════════════╧═════════════════════════════╧═══════╧════════╧═══════╧═══════╝
```

> Remarque : le script écrit également quelques informations dans la sortie standard
> (`print(title)`, `print(url)`), ce qui permet un debug rapide en plus du tableau `rich`.

---

## Architecture technique

### Vue textuelle

```text
                ┌────────────────────┐
                │   Utilisateur CLI  │
                └─────────┬──────────┘
                          │ requête texte
                          ▼
                ┌────────────────────┐
                │     main.main()    │
                └─────────┬──────────┘
                          │ instancie
                          ▼
                ┌────────────────────┐
                │  HonaïJobCrawler   │
                └─────────┬──────────┘
        ┌─────────────────┼──────────────────┐
        ▼                 ▼                  ▼
 ┌─────────────┐   ┌───────────────┐   ┌──────────────────┐
 │ _search_sync│   │ _fetch_page   │   │ _extract_text     │
 │ (DDGS)      │   │ (aiohttp)     │   │ (BeautifulSoup)   │
 └─────────────┘   └───────────────┘   └──────────────────┘
        │                 │                  │
        └─────────────────┴──────────┬───────┘
                                     ▼
                            ┌────────────────┐
                            │ EmbeddingModel │
                            │ (SentenceTrans.)│
                            └────────┬───────┘
                                     ▼
                           ┌──────────────────┐
                           │ _compute_score   │
                           │ + _detect_skills │
                           └────────┬─────────┘
                                    ▼
                           ┌──────────────────┐
                           │ SemanticResult   │
                           └────────┬─────────┘
                                    ▼
                           ┌──────────────────┐
                           │  Affichage rich  │
                           └──────────────────┘
```

### Principales classes / fonctions

- `EmbeddingModel` : encapsule `SentenceTransformer` pour produire des embeddings en tâche de fond.
- `QueryIntent` / `infer_query_intent(...)` : prépare l’intention de la requête (domaine, lieux, skills).
- `SemanticResult` : structure de données pour les résultats scorés.
- `HonaïJobCrawler` :
  - `_search_sync` : interroge DuckDuckGo,
  - `_fetch_page` : télécharge les pages (async),
  - `_extract_text` : récupère le texte utile,
  - `_detect_skills_contract` : repère compétences et type de contrat,
  - `_compute_score` : combine similarité cosinus, match de mots-clés, récence,
  - `search` : méthode principale orchestrant l’ensemble.
- `main()` :
  - lit la requête utilisateur,
  - appelle `HonaïJobCrawler.search`,
  - construit et affiche le tableau `rich`.

---

## Défis rencontrés

Quelques défis clé lors du développement :

- **Asynchronisme réseau**  
  Gérer plusieurs téléchargements HTTP en parallèle tout en restant robuste aux timeouts
  et aux erreurs (sites inaccessibles, HTML mal formé, etc.).

- **Extraction de texte générique**  
  Les pages d’offres sont très hétérogènes (CMS, mise en page, publicités). L’extraction
  basée sur quelques balises (`p`, `li`, `article`, `h1`, `h2`, `h3`) est un compromis
  entre simplicité et efficacité, mais ne couvre pas tous les cas.

- **Pertinence sans LLM**  
  Obtenir des résultats utilisables en se limitant à :
  - des embeddings statiques,
  - un score simple,
  - des mots-clés fournis par l’utilisateur (fichier JSON).

- **Performance des embeddings**  
  Même si le modèle `all-MiniLM-L6-v2` est léger, encoder un grand nombre de pages
  reste coûteux. D’où le choix de tronquer le contenu (`text[:1500]`) et d’exécuter
  l’encodage dans un thread séparé (`asyncio.to_thread`).

- **Détection de compétences et de contrats**  
  La détection purement lexicale (intersection de sets) est sensible :
  - à la qualité du texte extrait,
  - au vocabulaire exact utilisé par les sites.

---

## Analyse des défauts actuels

L’outil est un **prototype** et présente des limitations importantes :

- **Fiabilité de l’extraction HTML**  
  - certains sites peuvent renvoyer du contenu vide ou obfusqué,
  - l’outil peut ignorer des offres si le texte est dans des balises non couvertes.

- **Scoring heuristique simpliste**
  - le score est une combinaison linéaire à 3 termes (`similarité`, `keyword_match`, `date_récente`),
  - aucun apprentissage supervisé n’est utilisé,
  - des résultats peu pertinents peuvent malgré tout être bien scorés si les mots-clés
    sont présents plusieurs fois.

- **Gestion limitée des erreurs**
  - absence de gestion fine des codes HTTP (403, 429, etc.),
  - pas de retry / backoff automatique,
  - pas de limite stricte de concurrence ou de rate limiting.

- **Pas de configuration externe avancée**
  - les poids de scoring sont codés en dur,
  - les paramètres (timeout, nombre de résultats, liste de balises HTML à analyser)
    ne sont pas exposés via arguments CLI ou fichier de configuration.

- **Pas de tests automatisés**
  - absence de tests unitaires / d’intégration,
  - aucune garantie de non-régression lors des modifications.

- **Affichage parfois verbeux**
  - à la fois des `print()` et un tableau `rich` (double sortie),
  - pas de mode “silencieux” ou “debug” paramétrable.

---

## Perspectives d’amélioration

### Priorité haute

- **1. Rendre la configuration flexible**
  - exposer les paramètres clés via des options CLI (`argparse`),
  - introduire un fichier `config.toml` ou `yaml` pour les réglages par défaut,
  - permettre de définir plusieurs profils de recherche (stage, CDI, freelance…).

- **2. Améliorer le scoring**
  - ajouter des signaux : longueur du texte, présence d’email / téléphone, mots-clés négatifs,
  - expérimenter des variantes du score (logarithmes, normalisation par taille de page),
  - ajouter un petit module de réordonnancement (re-ranking) basé sur des règles.

- **3. Renforcer la robustesse réseau**
  - implémenter un système de retry exponentiel,
  - plafonner le nombre de requêtes parallèles,
  - journaliser plus finement les erreurs par domaine.

- **4. Introduire un petit modèle local pour remplacer `keywords.json`**
  - concevoir un **petit modèle de classification ou de tagging**, léger, capable de tourner sur CPU,
  - l’entraîner à partir d’exemples annotés (requêtes, extraits de pages) pour prédire :
    - le domaine (emploi / tech / autre),
    - les compétences principales,
    - éventuellement le type de contrat,
  - utiliser ce modèle pour remplacer ou compléter :
    - l’interprétation de l’intention (`infer_query_intent`),
    - la détection de compétences et de contrat,
  - conserver la philosophie du projet :
    - modèle **local**, sans dépendance à une API distante,
    - suffisamment léger pour tourner sur un **CPU standard**, même sur une machine modeste.

### Priorité moyenne

- **4. Qualité du texte extrait**
  - adapter dynamiquement les balises scannées selon le site,
  - filtrer les menus, footers, et contenus peu informatifs,
  - ajouter des heuristiques pour détecter les sections “Description du poste”, “Profil recherché”, etc.

- **5. UX en ligne de commande**
  - proposer un mode “interactif” (plusieurs requêtes successives dans la même session),
  - ajouter une option pour exporter les résultats (CSV / JSON),
  - amélioration du design du tableau (troncature conditionnelle, colonnes optionnelles).

### Priorité basse

- **6. Industrialisation**
  - packager l’outil en module installable (`pip install honaijob-search`),
  - fournir une image Docker prête à l’emploi,
  - intégrer un système de logs configurable (fichiers, JSON, niveaux).

- **7. Intégrations externes**
  - permettre de pousser les résultats vers un outil externe (Notion, Airtable, etc.),
  - exposer une petite API HTTP locale (FastAPI) pour déclencher la recherche depuis d’autres services.

- **8. Expérimenter un petit LLM local sur CPU**
  - évaluer un **petit modèle de langage** (taille réduite) capable de tourner sur un PC basique uniquement avec le CPU,
  - l’utiliser en option pour des tâches ciblées :
    - re-ranking plus fin des offres les plus pertinentes,
    - génération de courts résumés d’offres,
    - reformulation de la requête utilisateur pour explorer des variantes,
  - conserver l’architecture actuelle comme base :
    - embeddings + heuristiques restent le cœur robuste et reproductible,
    - le petit LLM vient en surcouche facultative, activable/désactivable selon les ressources de la machine.

---

## Licence MIT

Ce projet est distribué sous licence **MIT**.

Voir le texte complet de la licence dans ce dépôt si nécessaire.

---

## 🤝 Contributions

Les contributions sont les bienvenues (corrections de bugs, amélioration du scoring,
ajout de nouvelles heuristiques métier, documentation).  
Proposez une _issue_ ou une _pull request_ avec une description claire de votre changement.
