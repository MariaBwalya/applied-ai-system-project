"""Static pet-care knowledge base and keyword-based retrieval.

No embeddings, no external service — the corpus is a small curated JSON file
and retrieval is plain keyword overlap scoring. This keeps grounding for the
AI parser fully offline and deterministic to test.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

_CORPUS_PATH = Path(__file__).parent / "care_corpus.json"
_TOKEN_RE = re.compile(r"\w+")


@lru_cache(maxsize=1)
def load_corpus(path: str | Path | None = None) -> list[dict]:
    """Load and cache the care-guideline corpus from disk."""
    corpus_path = Path(path) if path else _CORPUS_PATH
    with open(corpus_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _tokenize(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def retrieve(species: str, query_text: str, top_k: int = 3) -> list[dict]:
    """Return up to top_k corpus entries most relevant to query_text for species.

    Score = keyword-overlap count + 1 if the entry applies to this species
    (or to any species). Entries scoring 0 are dropped; if nothing scores
    above 0, falls back to species-matching entries so the caller always has
    some grounding context to work with.
    """
    species_lower = species.lower()
    query_tokens = _tokenize(query_text)
    corpus = load_corpus()

    def score(entry: dict) -> int:
        overlap = len(query_tokens & set(entry["keywords"]))
        species_match = 1 if entry["species"] in (species_lower, "any") else 0
        return overlap + species_match

    scored = [(score(entry), entry) for entry in corpus]
    matched = [(s, e) for s, e in scored if s > 0]

    if not matched:
        fallback = [e for e in corpus if e["species"] in (species_lower, "any")]
        return fallback[:top_k]

    matched.sort(key=lambda pair: pair[0], reverse=True)
    return [entry for _, entry in matched[:top_k]]