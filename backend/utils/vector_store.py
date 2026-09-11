"""
Vector storage and semantic clustering abstraction for TruthTrace.
Supports Chroma, in-memory vector storage, and semantic clustering of Claim objects into ClaimCluster objects.
"""
import os
import math
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from models.schemas import Claim, ClaimCluster

logger = logging.getLogger(__name__)

# Optional sentence-transformers support
_EMBEDDING_MODEL = None

def get_embedding_model():
    """Lazy load sentence-transformers model."""
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            _EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Loaded sentence-transformers all-MiniLM-L6-v2 model")
        except Exception as e:
            logger.warning(f"Could not load sentence_transformers: {e}. Falling back to hash/char-embedding.")
            _EMBEDDING_MODEL = "fallback"
    return _EMBEDDING_MODEL

def compute_embedding(text: str) -> List[float]:
    """Compute dense vector embedding for a given text string."""
    model = get_embedding_model()
    if model != "fallback" and model is not None:
        try:
            emb = model.encode(text, convert_to_numpy=True)
            return emb.tolist()
        except Exception as e:
            logger.warning(f"Error computing sentence-transformer embedding: {e}")
    
    # Deterministic 128-dimensional hashed bag-of-words + character n-grams
    tokens = re.findall(r'\w+', text.lower())
    dim = 128
    vec = [0.0] * dim
    if not tokens:
        return vec

    # Word unigrams
    for token in tokens:
        idx = hash(token) % dim
        vec[idx] += 3.0

    # Character trigrams for sub-word similarity
    clean_text = " " + " ".join(tokens) + " "
    for i in range(len(clean_text) - 2):
        trigram = clean_text[i:i+3]
        idx = hash(trigram) % dim
        vec[idx] += 1.0

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return max(-1.0, min(1.0, dot / (norm1 * norm2)))

class VectorStore:
    """
    In-memory and Chroma-backed vector store for Claim objects and cluster tracking.
    """
    def __init__(self, collection_name: str = "truthtrace_claims"):
        self.collection_name = collection_name
        self.claims: Dict[str, Claim] = {}
        self.db_type = os.getenv("VECTOR_DB_TYPE", "in_memory").lower()
        self.chroma_client = None
        self.chroma_collection = None

        if self.db_type == "chroma":
            try:
                import chromadb
                persist_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
                self.chroma_client = chromadb.PersistentClient(path=persist_dir)
                self.chroma_collection = self.chroma_client.get_or_create_collection(name=collection_name)
                logger.info(f"Connected to ChromaDB collection: {collection_name}")
            except Exception as e:
                logger.warning(f"ChromaDB initialization failed: {e}. Using in-memory fallback.")
                self.db_type = "in_memory"

    def add_claim(self, claim: Claim) -> Claim:
        """Add or update a single Claim object in the vector store."""
        if not claim.embedding:
            claim.embedding = compute_embedding(claim.text)
        
        self.claims[claim.id] = claim

        if self.chroma_collection:
            try:
                self.chroma_collection.upsert(
                    ids=[claim.id],
                    embeddings=[claim.embedding],
                    documents=[claim.text],
                    metadatas=[{
                        "source_platform": claim.source_platform or "",
                        "source_url": claim.source_url or "",
                        "timestamp": claim.timestamp.isoformat() if claim.timestamp else "",
                        "cluster_id": claim.cluster_id or ""
                    }]
                )
            except Exception as e:
                logger.warning(f"Chroma upsert error: {e}")
        return claim

    def add_claims(self, claims: List[Claim]) -> List[Claim]:
        """Add multiple Claim objects."""
        return [self.add_claim(c) for c in claims]

    def similarity_search(self, query: str, top_k: int = 5, threshold: float = 0.20) -> List[Tuple[Claim, float]]:
        """Search claims similar to query text above a similarity threshold."""
        query_emb = compute_embedding(query)
        scored = []
        for claim in self.claims.values():
            if claim.embedding:
                sim = cosine_similarity(query_emb, claim.embedding)
                if sim >= threshold:
                    scored.append((claim, sim))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def cluster_claims(self, similarity_threshold: float = 0.20) -> List[ClaimCluster]:
        """
        Cluster near-duplicate and paraphrased claims into ClaimCluster objects.
        Surfaces the earliest timestamp and patient zero candidate inside each cluster.
        """
        all_claims = list(self.claims.values())
        if not all_claims:
            return []

        # Ensure embeddings
        for c in all_claims:
            if not c.embedding:
                c.embedding = compute_embedding(c.text)

        # Build adjacency graph
        n = len(all_claims)
        adj: Dict[int, List[int]] = {i: [] for i in range(n)}
        for i in range(n):
            for j in range(i + 1, n):
                sim = cosine_similarity(all_claims[i].embedding, all_claims[j].embedding)
                if sim >= similarity_threshold:
                    adj[i].append(j)
                    adj[j].append(i)

        visited = set()
        cluster_list: List[ClaimCluster] = []
        cluster_idx = 0

        def _sort_ts(c: Claim):
            ts = c.timestamp
            if ts and ts.tzinfo:
                ts = ts.replace(tzinfo=None)
            return ts or datetime.max

        for i in range(n):
            if i not in visited:
                cluster_id = f"cluster_{cluster_idx}"
                cluster_idx += 1
                group: List[Claim] = []
                queue = [i]
                visited.add(i)
                while queue:
                    curr = queue.pop(0)
                    claim_obj = all_claims[curr]
                    claim_obj.cluster_id = cluster_id
                    group.append(claim_obj)
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                
                # Sort claims in the cluster by timestamp ascending (earliest first)
                group.sort(key=_sort_ts)
                
                earliest_ts = group[0].timestamp if group and _sort_ts(group[0]) != datetime.max else None
                patient_zero_source = (
                    group[0].source_url or group[0].source_platform or group[0].text[:30]
                ) if group else None

                cluster_label = f"Narrative: {group[0].text[:45]}..." if group else f"Cluster {cluster_id}"

                cluster_list.append(ClaimCluster(
                    cluster_id=cluster_id,
                    label=cluster_label,
                    claim_count=len(group),
                    earliest_timestamp=earliest_ts,
                    patient_zero_source=patient_zero_source,
                    claims=group
                ))

        return cluster_list

# Global singleton
vector_store = VectorStore()
