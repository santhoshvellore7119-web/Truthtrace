"""
Unit tests for text_helpers and domain keyword extraction.
Verifies preservation of short political acronyms (DMK, TVK, BJP, CM, MP, ED, ECI)
and proper stopword pruning.
"""
import pytest
from backend.utils.text_helpers import extract_search_keywords

def test_extract_search_keywords_political_acronyms():
    # Verify the reviewer's exact test case
    sample = "TVK, the party founded by... DMK and AIADMK..."
    keywords = extract_search_keywords(sample, max_tokens=6)
    assert "TVK" in keywords
    assert "DMK" in keywords
    assert "AIADMK" in keywords
    assert keywords == ["TVK", "party", "founded", "DMK", "AIADMK"]

def test_extract_search_keywords_institutional_acronyms():
    sample = "CM Stalin and MP Kanimozhi targeted by ED and BJP"
    keywords = extract_search_keywords(sample, max_tokens=8)
    assert "CM" in keywords
    assert "MP" in keywords
    assert "ED" in keywords
    assert "BJP" in keywords
    assert "ECI" not in keywords

def test_extract_search_keywords_stopword_pruning():
    sample = "The video published during the election claiming victory is fake"
    keywords = extract_search_keywords(sample, max_tokens=5)
    assert "election" in keywords
    assert "victory" in keywords
    assert "fake" in keywords
    assert "the" not in [k.lower() for k in keywords]
    assert "during" not in [k.lower() for k in keywords]
