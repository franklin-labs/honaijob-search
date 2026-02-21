import asyncio
import time

from main import (
    TTLCache,
    _cosine_similarity,
    extract_relevant_content,
    infer_query_intent,
)


def test_cosine_similarity_basic():
    a = [1.0, 0.0]
    b = [1.0, 0.0]
    c = [0.0, 1.0]
    assert _cosine_similarity(a, b) == 1.0
    assert _cosine_similarity(a, c) == 0.0


def test_ttlcache_expiration():
    cache = TTLCache(ttl_seconds=0.1)

    async def run():
        await cache.set("k", "v")
        assert await cache.get("k") == "v"
        time.sleep(0.2)
        assert await cache.get("k") is None

    asyncio.run(run())


def test_extract_relevant_content_simple_html():
    html = """
    <html>
      <head><title>Offres d'emploi étudiant à Paris</title></head>
      <body>
        <main>
          <h1>Jobs pour étudiants à Paris</h1>
          <p>Cette page liste plusieurs jobs pour étudiants à Paris.</p>
          <p>Les offres ont été publiées hier et sont encore valides.</p>
        </main>
      </body>
    </html>
    """
    query = "jobs etudiants a paris poster hier"
    extracted = extract_relevant_content(html, query)
    assert "Jobs pour étudiants à Paris" in extracted
    assert "offres ont été publiées hier" in extracted


def test_infer_query_intent_employment_paris():
    query = "jobs etudiants a paris dans la data et python"
    intent = infer_query_intent(query)
    assert intent.domain == "employment"
    assert "paris" in intent.locations
    assert "python" in intent.skills
