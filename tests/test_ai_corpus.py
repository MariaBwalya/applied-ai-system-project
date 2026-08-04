from pawpal_system import PRIORITY_ORDER
from ai.corpus import load_corpus, retrieve

VALID_RECURRENCE = {"daily", "weekly", "once"}
REQUIRED_FIELDS = {
    "id", "species", "category", "keywords", "guidance",
    "suggested_duration_minutes", "suggested_priority", "suggested_recurrence",
}


def test_load_corpus_all_entries_have_required_fields():
    corpus = load_corpus()
    assert len(corpus) > 0
    for entry in corpus:
        assert REQUIRED_FIELDS.issubset(entry.keys())
        assert entry["suggested_priority"] in PRIORITY_ORDER
        assert entry["suggested_recurrence"] in VALID_RECURRENCE
        assert isinstance(entry["keywords"], list) and entry["keywords"]


def test_retrieve_prefers_species_and_keyword_matches():
    results = retrieve("dog", "walk the dog outside", top_k=3)
    assert results
    assert results[0]["id"] == "dog_exercise"


def test_retrieve_falls_back_when_no_keywords_match():
    results = retrieve("cat", "asdkjhasd", top_k=3)
    assert results
    assert all(entry["species"] in ("cat", "any") for entry in results)


def test_retrieve_respects_top_k():
    results = retrieve("dog", "feed walk groom medication vet", top_k=2)
    assert len(results) <= 2