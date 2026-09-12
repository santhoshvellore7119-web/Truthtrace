"""
Shared text and NLP utility helpers for TruthTrace.
Handles token normalization and political domain keyword extraction.
"""
import re
from typing import List

COMMON_STOP_WORDS = {
    'the', 'is', 'at', 'which', 'on', 'and', 'a', 'an', 'in', 'of', 'to', 
    'for', 'with', 'as', 'by', 'from', 'that', 'this', 'these', 'those', 
    'about', 'says', 'said', 'video', 'photo', 'during', 'published', 
    'statement', 'viral', 'claim', 'claiming', 'be', 'are', 'was', 'were',
    'has', 'have', 'had', 'it', 'its', 'their', 'they', 'he', 'she', 'his', 'her',
    'or', 'so', 'if', 'but', 'out', 'up', 'down', 'over', 'under', 'again'
}

# Domain-specific political parties, institutions, and key actor acronyms
POLITICAL_ACRONYMS = {
    'dmk', 'tvk', 'bjp', 'inc', 'aap', 'cpi', 'cpm', 'vck', 'pmk', 'ntk', 
    'tmc', 'aiadmk', 'eci', 'ed', 'cbi', 'nia', 'cm', 'pm', 'mp', 'mla', 
    'mlc', 'str', 'mk', 'ptr', 'eps', 'ops', 'nda', 'upa', 'india'
}

def extract_search_keywords(query: str, max_tokens: int = 5) -> List[str]:
    """
    Extract meaningful search tokens, preserving essential short political acronyms 
    (DMK, TVK, BJP, CM, MP, ED, ECI) while pruning low-signal stopwords.
    """
    raw_tokens = re.findall(r'[A-Za-z0-9]+', query)
    keywords = []
    seen = set()
    for token in raw_tokens:
        t_lower = token.lower()
        if t_lower in COMMON_STOP_WORDS or t_lower in seen:
            continue
        # Retain if recognized acronym, or uppercase abbreviation >= 2 chars, or standard word >= 3 chars
        if t_lower in POLITICAL_ACRONYMS or (token.isupper() and len(token) >= 2) or len(token) >= 3:
            keywords.append(token)
            seen.add(t_lower)
            if len(keywords) >= max_tokens:
                break
    return keywords
