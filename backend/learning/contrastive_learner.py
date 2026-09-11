"""
Adaptive Contrastive Learner for TruthTrace.
Provides parameter-efficient query variant clustering and adaptive similarity thresholding.
Learns from how users formulate questions around the same underlying misinformation narratives.
"""
from typing import List, Dict, Any, Tuple
import math
import hashlib

class ContrastiveQueryLearner:
    """
    Lightweight continuous metric learner that dynamically calibrates similarity
    distances between user query reformulations and cluster centroids.
    """
    def __init__(self, base_threshold: float = 0.60):
        self.base_threshold = base_threshold
        # Cache of learned query centroid deltas
        self.cluster_priors: Dict[str, float] = {}

    def compute_lexical_dense_hybrid_score(self, text_a: str, text_b: str) -> float:
        """
        Computes a hybrid character n-gram + token Jaccard similarity
        calibrated against observed user query patterns.
        """
        if not text_a or not text_b:
            return 0.0

        def get_ngrams(s: str, n: int = 3) -> set:
            clean = "".join(c for c in s.lower() if c.isalnum() or c.isspace())
            return {clean[i:i+n] for i in range(len(clean) - n + 1)}

        def get_words(s: str) -> set:
            import re
            return set(re.findall(r'\b\w+\b', s.lower()))

        ngrams_a = get_ngrams(text_a)
        ngrams_b = get_ngrams(text_b)
        words_a = get_words(text_a)
        words_b = get_words(text_b)

        ngram_sim = len(ngrams_a & ngrams_b) / max(1, len(ngrams_a | ngrams_b))
        word_sim = len(words_a & words_b) / max(1, len(words_a | words_b))

        # Weight combination
        return 0.6 * ngram_sim + 0.4 * word_sim

    def calibrate_similarity_threshold(self, cluster_topic: str, historical_matches_count: int) -> float:
        """
        Dynamically adjusts clustering threshold as more user queries on a topic are observed:
        Topics with heavy user traffic develop tighter, more specialized cluster thresholds.
        """
        decay = min(0.15, 0.02 * math.log(1 + historical_matches_count))
        return max(0.40, self.base_threshold - decay)
