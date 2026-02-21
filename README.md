# HonaïJob-search 1.0

HonaïJob-search est un **crawler sémantique asynchrone** qui :

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
- Requête DuckDuckGo (via `ddgs`) pour trouver des URLs pertinentes.
- Téléchargement asynchrone des pages avec `aiohttp`.
- Vectorisation de la requête et des pages avec `sentence-transformers`.
- Score de similarité cosinus (via `numpy`) et tri des résultats par pertinence.

## Installation

Depuis le répertoire `crawller` :

```bash
pip install aiohttp ddgs sentence-transformers numpy beautifulsoup4 rich
```

(Optionnel) Vous pouvez aussi mettre ces dépendances dans un `requirements.txt` puis faire :

```bash
pip install -r requirements.txt
```

Ensuite, assurez-vous d’avoir un fichier `keywords.json` à la racine du projet, par exemple :

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

## Utilisation

Depuis le répertoire `crawller` :

```bash
python main.py
```

Le script va :

1. Vous demander une requête texte (mots-clés, ville, techno).
2. Interroger DuckDuckGo pour récupérer une liste d’URLs (20 résultats par défaut dans `main`).
3. Télécharger les pages de manière asynchrone.
4. Calculer des embeddings pour la requête et chaque page.
5. Calculer la similarité cosinus et trier les résultats.
6. Afficher dans la console un tableau enrichi (via `rich`) contenant :
   - le titre de la page,
   - l’URL,
   - la similarité (score),
   - le type de contrat détecté (si présent),
   - les compétences détectées,
   - un court extrait de contenu.

## Guide pas à pas (sous forme d’onglets)

<div>

<details open>
<summary><strong>Onglet 1 — Préparer l’environnement Python</strong></summary>

- Installer Python 3.10+.
- (Optionnel) Créer un environnement virtuel :

  ```bash
  python -m venv .venv
  # Linux / macOS
  source .venv/bin/activate
  # Windows
  .venv\Scripts\activate
  ```

- Se placer dans le dossier du projet :

  ```bash
  cd crawller
  ```

</details>

<details>
<summary><strong>Onglet 2 — Installer les dépendances</strong></summary>

- Installer les bibliothèques nécessaires :

  ```bash
  pip install aiohttp ddgs sentence-transformers numpy beautifulsoup4 rich
  # ou, si vous avez renseigné un requirements.txt :
  pip install -r requirements.txt
  ```

- Vérifier que le fichier `keywords.json` existe à la racine et contient vos mots-clés.

</details>

<details>
<summary><strong>Onglet 3 — Lancer une recherche</strong></summary>

- Lancer le programme :

  ```bash
  python main.py
  ```

- Saisir une requête, par exemple :

  ```text
  offre de stage étudiant Paris python
  ```

- Attendre le téléchargement des pages et le calcul des scores sémantiques.

</details>

<details>
<summary><strong>Onglet 4 — Lire et interpréter les résultats</strong></summary>

- Chaque ligne du tableau correspond à une page trouvée.
- La colonne **Score** combine :
  - une similarité cosinus entre l’embedding de la requête et celui de la page,
  - la présence de mots-clés (emploi, compétences, etc.),
  - une légère bonification si le texte semble récent.
- Plus le score est élevé, plus l’offre est pertinente pour votre requête.

</details>

</div>

## Affichage des résultats dans le terminal

L’affichage utilise la bibliothèque **`rich`** pour construire un tableau coloré (`Console` + `Table`).

Les colonnes affichées sont :
- **Titre** : titre HTML de la page ou, à défaut, l’URL.
- **URL** : lien direct vers la ressource.
- **Score** : score de similarité agrégé.
- **Contrat** : type de contrat détecté (stage, alternance, CDD, CDI, etc.).
- **Skills** : compétences repérées dans le texte.
- **Extrait** : début du contenu de la page.

Pour installer uniquement ce qui concerne l’affichage des résultats :

```bash
pip install rich
```

Dans la pratique, `rich` est déjà inclus dans la commande d’installation complète ci-dessus.

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
| `HonaïJobCrawler`    | Récupère les URLs, télécharge les pages, filtre et score les résultats.      |
| `main`               | Point d’entrée CLI : lit la requête et affiche le tableau de résultats.      |

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
