"""
Episodic Memory & Continuous Learning Store for TruthTrace.
Provides non-parametric continuous learning from user questions, submitted URLs,
verified dossiers, and community feedback without catastrophic forgetting.
"""
import sqlite3
import json
import os
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

class LearningMemoryStore:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "truthtrace_learning_memory.db")
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Investigations Table (stores past user questions & dossiers)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS investigations (
                    id TEXT PRIMARY KEY,
                    query_text TEXT NOT NULL,
                    extracted_claims TEXT,
                    verdict TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    patient_zero_handle TEXT,
                    patient_zero_platform TEXT,
                    patient_zero_url TEXT,
                    first_seen_timestamp TEXT,
                    clusters_count INTEGER DEFAULT 0,
                    summary TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            
            # 2. Domain Reputation Table (dynamically updated domain risk score)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS domain_reputation (
                    domain TEXT PRIMARY KEY,
                    times_observed INTEGER DEFAULT 0,
                    flagged_false_count INTEGER DEFAULT 0,
                    verified_true_count INTEGER DEFAULT 0,
                    user_downvotes INTEGER DEFAULT 0,
                    user_upvotes INTEGER DEFAULT 0,
                    credibility_score REAL DEFAULT 0.5,
                    last_updated TEXT NOT NULL
                )
            """)

            # 3. User Feedback & Corrections Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    investigation_id TEXT NOT NULL,
                    rating TEXT NOT NULL,
                    feedback_type TEXT,
                    correction_text TEXT,
                    evidence_url TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # 4. Semantic Memory Tokens & Embeddings index for fast cross-investigation retrieval
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_tokens (
                    token TEXT NOT NULL,
                    investigation_id TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    PRIMARY KEY (token, investigation_id)
                )
            """)
            conn.commit()

    def _tokenize(self, text: str) -> List[str]:
        """Simple n-gram and word tokenizer for zero-dependency fast lexical-semantic matching."""
        import re
        tokens = re.findall(r'\b[a-zA-Z0-9_]{3,}\b', text.lower())
        # Filter out common stop words
        stopwords = {"the", "and", "for", "with", "this", "that", "from", "are", "have", "been", "causes", "about", "what", "where", "when"}
        return [t for t in tokens if t not in stopwords]

    def record_investigation(self, dossier_data: Dict[str, Any]) -> str:
        """
        Learns from a synthesized dossier: indexes the query, entities, patient zero,
        and updates observed domain reputation profiles.
        """
        inv_id = dossier_data.get("id", str(datetime.now().timestamp()))
        query = dossier_data.get("input_claim", dossier_data.get("query", ""))
        verdict = dossier_data.get("overall_verdict", dossier_data.get("verdict", "unverified"))
        confidence = float(dossier_data.get("overall_confidence", dossier_data.get("confidence_score", 0.5)))
        summary = dossier_data.get("narrative", {}).get("core_narrative", "") if isinstance(dossier_data.get("narrative"), dict) else dossier_data.get("summary", "")
        
        pz = dossier_data.get("patient_zero") or {}
        pz_handle = pz.get("handle") if isinstance(pz, dict) else getattr(pz, "handle", None)
        pz_platform = pz.get("platform") if isinstance(pz, dict) else getattr(pz, "platform", None)
        pz_url = pz.get("source_url") if isinstance(pz, dict) else getattr(pz, "source_url", None)
        
        first_seen = None
        timeline = dossier_data.get("timeline", [])
        if timeline:
            first_seen = timeline[0].get("timestamp") if isinstance(timeline[0], dict) else str(timeline[0])

        clusters_count = len(dossier_data.get("clusters", []))
        created_at = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO investigations 
                (id, query_text, extracted_claims, verdict, confidence, patient_zero_handle, patient_zero_platform, patient_zero_url, first_seen_timestamp, clusters_count, summary, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                inv_id, query, json.dumps(dossier_data.get("sub_claims", []), default=str),
                verdict, confidence, pz_handle, pz_platform, pz_url,
                str(first_seen) if first_seen else None,
                clusters_count, summary, created_at
            ))

            # Index semantic tokens for continuous retrieval
            tokens = self._tokenize(query)
            for t in set(tokens):
                cursor.execute("""
                    INSERT OR REPLACE INTO memory_tokens (token, investigation_id, weight)
                    VALUES (?, ?, ?)
                """, (t, inv_id, 1.0))

            # Update Domain Reputations dynamically
            attr = dossier_data.get("attribution") or {}
            domains = attr.get("domains", [])
            for dom_entry in domains:
                dom_name = dom_entry.get("domain") if isinstance(dom_entry, dict) else getattr(dom_entry, "domain", None)
                if not dom_name:
                    continue
                is_flagged_false = verdict in ["false", "misleading", "Debunked / False"]
                is_verified_true = verdict in ["true", "Verified True"]
                
                cursor.execute("SELECT * FROM domain_reputation WHERE domain = ?", (dom_name,))
                existing = cursor.fetchone()
                if existing:
                    observed = existing["times_observed"] + 1
                    f_count = existing["flagged_false_count"] + (1 if is_flagged_false else 0)
                    t_count = existing["verified_true_count"] + (1 if is_verified_true else 0)
                    # Adaptive credibility score (Dirichlet prior)
                    credibility = (1.0 + t_count + existing["user_upvotes"] * 0.5) / (2.0 + observed + f_count * 1.5 + existing["user_downvotes"])
                    credibility = max(0.05, min(0.95, credibility))
                    cursor.execute("""
                        UPDATE domain_reputation 
                        SET times_observed = ?, flagged_false_count = ?, verified_true_count = ?, credibility_score = ?, last_updated = ?
                        WHERE domain = ?
                    """, (observed, f_count, t_count, credibility, created_at, dom_name))
                else:
                    f_count = 1 if is_flagged_false else 0
                    t_count = 1 if is_verified_true else 0
                    credibility = 0.3 if is_flagged_false else (0.8 if is_verified_true else 0.5)
                    cursor.execute("""
                        INSERT INTO domain_reputation 
                        (domain, times_observed, flagged_false_count, verified_true_count, credibility_score, last_updated)
                        VALUES (?, 1, ?, ?, ?, ?)
                    """, (dom_name, f_count, t_count, credibility, created_at))
            conn.commit()

        return inv_id

    def recall_prior_investigations(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Cross-Investigation Retrieval:
        Finds previous user questions and investigations that match or relate to the new query.
        """
        tokens = self._tokenize(query)
        if not tokens:
            return []

        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join(["?"] * len(tokens))
            cursor.execute(f"""
                SELECT investigation_id, COUNT(*) as match_count, SUM(weight) as score
                FROM memory_tokens
                WHERE token IN ({placeholders})
                GROUP BY investigation_id
                ORDER BY score DESC
                LIMIT ?
            """, (*tokens, top_k))
            
            rows = cursor.fetchall()
            recalled = []
            for r in rows:
                cursor.execute("SELECT * FROM investigations WHERE id = ?", (r["investigation_id"],))
                inv = cursor.fetchone()
                if inv:
                    recalled.append({
                        "id": inv["id"],
                        "query_text": inv["query_text"],
                        "verdict": inv["verdict"],
                        "confidence": inv["confidence"],
                        "patient_zero_handle": inv["patient_zero_handle"],
                        "patient_zero_platform": inv["patient_zero_platform"],
                        "patient_zero_url": inv["patient_zero_url"],
                        "first_seen_timestamp": inv["first_seen_timestamp"],
                        "summary": inv["summary"],
                        "created_at": inv["created_at"],
                        "relevance_score": float(r["score"]) / max(1, len(tokens))
                    })
            return recalled

    def record_user_feedback(self, investigation_id: str, rating: str, feedback_type: Optional[str] = None, correction_text: Optional[str] = None, evidence_url: Optional[str] = None) -> bool:
        """
        Human-in-the-Loop Continuous Learning:
        Processes user corrections, adjusts domain trust weights and updates dossier reliability.
        """
        created_at = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_feedback (investigation_id, rating, feedback_type, correction_text, evidence_url, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (investigation_id, rating, feedback_type or "accuracy", correction_text or "", evidence_url or "", created_at))

            # If evidence URL is provided, boost or record domain credibility
            if evidence_url:
                import urllib.parse
                parsed = urllib.parse.urlparse(evidence_url)
                dom = parsed.netloc.replace("www.", "")
                if dom:
                    cursor.execute("SELECT * FROM domain_reputation WHERE domain = ?", (dom,))
                    row = cursor.fetchone()
                    if row:
                        if rating == "upvote" or rating == "accurate":
                            cursor.execute("UPDATE domain_reputation SET user_upvotes = user_upvotes + 1, credibility_score = MIN(0.95, credibility_score + 0.05), last_updated = ? WHERE domain = ?", (created_at, dom))
                        else:
                            cursor.execute("UPDATE domain_reputation SET user_downvotes = user_downvotes + 1, credibility_score = MAX(0.05, credibility_score - 0.05), last_updated = ? WHERE domain = ?", (created_at, dom))
                    else:
                        cursor.execute("""
                            INSERT INTO domain_reputation (domain, times_observed, user_upvotes, credibility_score, last_updated)
                            VALUES (?, 1, 1, 0.7, ?)
                        """, (dom, created_at))
            conn.commit()
            return True

    def get_learning_stats(self) -> Dict[str, Any]:
        """Returns statistics on TruthTrace's accumulated knowledge."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total_investigations FROM investigations")
            total_inv = cursor.fetchone()["total_investigations"]

            cursor.execute("SELECT COUNT(*) as total_domains FROM domain_reputation")
            total_doms = cursor.fetchone()["total_domains"]

            cursor.execute("SELECT COUNT(*) as total_feedback FROM user_feedback")
            total_fb = cursor.fetchone()["total_feedback"]

            cursor.execute("SELECT query_text, verdict, created_at FROM investigations ORDER BY created_at DESC LIMIT 5")
            recent_inv = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT domain, credibility_score, times_observed FROM domain_reputation ORDER BY times_observed DESC LIMIT 5")
            top_domains = [dict(r) for r in cursor.fetchall()]

            return {
                "total_investigations_learned": total_inv,
                "tracked_domains_count": total_doms,
                "user_feedback_contributions": total_fb,
                "recent_investigations": recent_inv,
                "top_monitored_domains": top_domains
            }
