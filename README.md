# Crawler sémantique de recherches d’offres (Python, async)

Ce projet est un **crawler sémantique asynchrone** qui :

- interroge DuckDuckGo pour récupérer une liste d’URLs,
- télécharge le contenu des pages en parallèle,
- vectorise la requête et les pages avec un modèle `sentence-transformers`,
- calcule une **similarité cosinus** entre la requête et chaque page,
- renvoie les résultats les plus proches de l’intention utilisateur (emploi / stages / compétences…).

Il est principalement pensé pour explorer des **offres d’emploi / stages tech** à partir de mots-clés.

## Fonctionnalités principales

- Saisie interactive de la requête directement dans le terminal.
- Chargement de mots-clés de contexte depuis `keywords.json` :
  - mots liés à l’emploi / aux stages,
  - mots liés aux jobs tech,
  - lieux, périodes, compétences.
- Requête DuckDuckGo (via `ddgs` ou `duckduckgo-search`) pour trouver des URLs pertinentes.
- Téléchargement asynchrone des pages avec `aiohttp`.
- Vectorisation de la requête et des pages avec `sentence-transformers`.
- Score de similarité cosinus (via `numpy`) et tri des résultats par pertinence.

## Installation

Depuis le répertoire `crawller` :

```bash
pip install aiohttp duckduckgo-search sentence-transformers numpy
```

Ensuite, assurez-vous d’avoir un fichier `keywords.json` à la racine du projet, par exemple :

```json
{
  "employment_keywords": ["emploi", "offre", "stage", "alternance"],
  "tech_job_keywords": ["développeur", "backend", "frontend", "data", "python"],
  "location_keywords": ["paris", "lyon", "remote"],
  "time_keywords": ["cdl", "cdd", "freelance", "temps plein", "temps partiel"],
  "skill_keywords": ["python", "django", "react", "sql"]
}
```

## Utilisation

Depuis le répertoire `crawller` :

```bash
python main.py
```

Le script va :

1. Vous afficher un en-tête dans le terminal.
2. Vous demander une requête texte (mots-clés, ville, techno).
3. Interroger DuckDuckGo pour récupérer une liste d’URLs (20 résultats par défaut dans `main`).
4. Télécharger les pages de manière asynchrone.
5. Calculer des embeddings pour la requête et chaque page.
6. Calculer la similarité cosinus et trier les résultats.
7. Afficher dans la console :
   - l’URL,
   - la similarité (entre 0 et 1),
   - un court extrait de contenu.

## Structure du code

| Élément              | Rôle principal                                                                 |
|----------------------|-------------------------------------------------------------------------------|
| `EmbeddingModel`     | Enveloppe autour de `SentenceTransformer` pour générer des embeddings async. |
| `_normalize_text`    | Normalisation simple (minuscule, accents, espaces).                          |
| `_tokenize`          | Tokenisation basique en mots alphanumériques.                                |
| `_cosine_similarity` | Calcul de similarité cosinus avec `numpy`.                                   |
| `QueryIntent`        | Représentation de l’intention de la requête (domaine, lieux, compétences).   |
| `infer_query_intent` | Déduit le domaine et les mots-clés à partir de `keywords.json`.              |
| `SemanticResult`     | Structure contenant requête, URL, extrait, embedding, similarité.            |
| `SemanticCrawler`    | Récupère les URLs, télécharge les pages, filtre et score les résultats.      |
| `main`               | Point d’entrée CLI : demande la requête et affiche les résultats.            |

## Licence

Ce projet est distribué sous licence **MIT**.

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
# honaijob-search
