import asyncio
import json
import logging
from dataclasses import dataclass
from typing import List, Optional
import aiohttp
import unicodedata
import numpy as np
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table

try:
    from ddgs import DDGS
except ImportError:
    raise ImportError("Installez ddgs : pip install ddgs")

from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HonaïJobCrawler")

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
CONTRACT_KEYWORDS = set(kws.get("contract_keywords", []))  # stage, alternance, intérim

# -------------------------------
# Utilitaires
# -------------------------------
def _normalize_text(text: str) -> str:
    text = text.lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
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
    title: str
    content: str
    embedding: List[float]
    similarity: float
    contract_type: str = ""
    skills: List[str] = None

# -------------------------------
# Semantic Crawler
# -------------------------------
class HonaïJobCrawler:
    def __init__(self, embedding_model: Optional[EmbeddingModel] = None):
        self.embedding_model = embedding_model or EmbeddingModel()

    def _search_sync(self, query: str, max_results=20) -> List[str]:
        urls = []
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    href = r.get("href")
                    if href and "duckduckgo.com" not in href:
                        urls.append(href)
        except Exception as e:
            logger.warning("DuckDuckGo error: %s", e)
        return urls

    async def _fetch_page(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        try:
            async with session.get(url, timeout=15) as resp:
                return await resp.text(errors="ignore")
        except Exception as e:
            logger.warning("Erreur fetch %s: %s", url, e)
            return None

    def _extract_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        text_parts = []
        for tag in soup.find_all(["p","li","article","h1","h2","h3"]):
            text = tag.get_text(separator=" ", strip=True)
            if text:
                text_parts.append(text)
        return " ".join(text_parts)

    def _detect_skills_contract(self, text: str):
        tokens = set(_tokenize(text))
        skills = [t for t in tokens if t in SKILL_KEYWORDS]
        contract = next((t for t in tokens if t in CONTRACT_KEYWORDS), "")
        return skills, contract

    def _compute_score(self, query_vec, page_vec, keyword_match, date_recent=False):
        score = 0.5 * _cosine_similarity(query_vec, page_vec)
        score += 0.4 * keyword_match
        if date_recent:
            score += 0.1
        return score

    async def search(self, query: str, max_results=20) -> List[SemanticResult]:
        urls = await asyncio.to_thread(self._search_sync, query, max_results)
        query_vec = (await self.embedding_model.encode([query]))[0]
        results = []

        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_page(session, url) for url in urls]
            pages = await asyncio.gather(*tasks)

        for url, html in zip(urls, pages):
            if not html:
                continue
            text = self._extract_text(html)
            if not any(t in EMPLOYMENT_KEYWORDS.union(SKILL_KEYWORDS) for t in _tokenize(text)):
                continue

            page_vec = (await self.embedding_model.encode([text[:1500]]))[0]
            keyword_match = sum(1 for t in _tokenize(query) if t in _tokenize(text)) / max(len(_tokenize(text)),1)
            date_recent = any(t in text.lower() for t in ["24h","aujourd'hui","hier","récent","nouveau"])
            score = self._compute_score(query_vec, page_vec, keyword_match, date_recent)

            skills, contract = self._detect_skills_contract(text)
            title = BeautifulSoup(html, "html.parser").title.string if BeautifulSoup(html, "html.parser").title else url

            results.append(SemanticResult(
                query=query,
                url=url,
                title=title,
                content=text[:1000],
                embedding=page_vec,
                similarity=score,
                contract_type=contract,
                skills=skills
            ))

        results.sort(key=lambda r: r.similarity, reverse=True)
        return results

# -------------------------------
# Main tableau
# -------------------------------
async def main():
    query = input("Entrez votre requête de recherche: ").strip()
    if not query:
        query = "offre de stage étudiant Paris python"
    crawler = HonaïJobCrawler()
    results = await crawler.search(query, max_results=30)

    console = Console()
    table = Table(title=f"Résultats de recherche pour : {query}")
    table.add_column("Titre", style="cyan", overflow="fold")
    table.add_column("URL", style="blue", overflow="fold")
    table.add_column("Score", justify="center", style="green")
    table.add_column("Contrat", style="magenta")
    table.add_column("Skills", style="yellow")
    table.add_column("Extrait", style="white", overflow="fold")

    for r in results:
        skills_str = ", ".join(r.skills) if r.skills else ""
        excerpt = r.content[:150] + ("..." if len(r.content) > 150 else "")
        table.add_row(
            f"{r.title}",
            f"{r.url}",
            f"{r.similarity:.2f}",
            r.contract_type,
            skills_str,
            excerpt,
        )
        print(f"{r.title}")
        print(f"{r.url}")
        print("------------------------------------------------------------------------")


    console.print(table)

if __name__ == "__main__":
    asyncio.run(main())