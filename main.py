import asyncio
import json
import logging
from dataclasses import dataclass
from typing import List, Optional

import aiohttp
import unicodedata
import numpy as np

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        raise ImportError(
            "Neither 'ddgs' nor 'duckduckgo_search' is installed. "
            "Install one of them, for example: pip install duckduckgo-search"
        )

from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("semantic_crawler")

# -------------------------------
# Charger mots-clés depuis JSON
# -------------------------------
with open("keywords.json", "r", encoding="utf-8") as f:
    kws = json.load(f)

EMPLOYMENT_KEYWORDS = set(kws.get("employment_keywords", []))
TECH_JOB_KEYWORDS = set(kws.get("tech_job_keywords", []))
LOCATION_KEYWORDS = set(kws.get("location_keywords", []))
TIME_KEYWORDS = set(kws.get("time_keywords", []))
SKILL_KEYWORDS = set(kws.get("skill_keywords", []))

# -------------------------------
# Utilitaires
# -------------------------------
def _normalize_text(text: str) -> str:
    text = text.lower()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )
    return " ".join(text.split())

def _tokenize(text: str) -> List[str]:
    return [t for t in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split() if t]

def _cosine_similarity(a, b) -> float:
    a, b = np.asarray(a), np.asarray(b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# -------------------------------
# Embeddings
# -------------------------------
class EmbeddingModel:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    async def encode(self, texts: List[str]) -> List[List[float]]:
        return await asyncio.to_thread(lambda: [list(map(float, v)) for v in self.model.encode(texts, show_progress_bar=False)])

# -------------------------------
# Intent
# -------------------------------
@dataclass
class QueryIntent:
    raw: str
    normalized: str
    domain: str
    locations: List[str]
    time_expressions: List[str]
    skills: List[str]

def infer_query_intent(query: str) -> QueryIntent:
    normalized = _normalize_text(query)
    tokens = normalized.split()
    domain = "other"
    if any(t in EMPLOYMENT_KEYWORDS for t in tokens):
        domain = "employment"
    elif any(t in TECH_JOB_KEYWORDS for t in tokens):
        domain = "tech"
    locations = [t for t in tokens if t in LOCATION_KEYWORDS]
    time_expressions = [t for t in tokens if t in TIME_KEYWORDS]
    skills = [t for t in tokens if t in SKILL_KEYWORDS]
    return QueryIntent(query, normalized, domain, locations, time_expressions, skills)

# -------------------------------
# Result
# -------------------------------
@dataclass
class SemanticResult:
    query: str
    url: str
    content: str
    embedding: List[float]
    similarity: float

# -------------------------------
# Semantic Crawler
# -------------------------------
class SemanticCrawler:
    def __init__(self, embedding_model: Optional[EmbeddingModel] = None):
        self.embedding_model = embedding_model or EmbeddingModel()

    def _search_sync(self, query: str, max_results=10) -> List[str]:
        urls = []
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    href = r.get("href")
                    if href and "duckduckgo.com" not in href:
                        urls.append(href)
        except Exception as e:
            logger.warning("Erreur lors de la recherche DuckDuckGo: %s", e)
        return urls

    async def _fetch_page(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        try:
            async with session.get(url, timeout=10) as resp:
                return await resp.text(errors="ignore")
        except Exception as e:
            logger.warning("Erreur lors du téléchargement de %s: %s", url, e)
            return None

    async def search(self, query: str, max_results=10) -> List[SemanticResult]:
        urls = await asyncio.to_thread(self._search_sync, query, max_results)
        query_vec = (await self.embedding_model.encode([query]))[0]
        results = []

        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_page(session, url) for url in urls]
            pages = await asyncio.gather(*tasks)

        for url, text in zip(urls, pages):
            if not text:
                continue
            tokens = set(_tokenize(text))
            if not any(t in EMPLOYMENT_KEYWORDS.union(SKILL_KEYWORDS) for t in tokens):
                continue  # ignore irrelevant pages
            page_vec = (await self.embedding_model.encode([text[:1000]]))[0]
            sim = _cosine_similarity(query_vec, page_vec)
            results.append(SemanticResult(query=query, url=url, content=text[:1000], embedding=page_vec, similarity=sim))
        results.sort(key=lambda r: r.similarity, reverse=True)
        return results

# -------------------------------
# Main
# -------------------------------
async def main():
    print("=== Crawler sémantique d’offres / stages tech ===")
    query = input("Entrez votre requête de recherche (mots-clés, ville, techno) : ").strip()
    if not query:
        query = "offre de stage étudiant Paris python"
        print("Aucune requête saisie, utilisation de la requête par défaut :")
        print(f"  {query}")
    crawler = SemanticCrawler()
    results = await crawler.search(query, max_results=20)
    if not results:
        print("Aucun résultat pertinent n’a été trouvé pour cette requête.")
        return
    for r in results:
        print(f"{r.url} | similarité = {r.similarity:.2f}")
        print(f"Extrait : {r.content[:300]}...\n")

if __name__ == "__main__":
    asyncio.run(main())
