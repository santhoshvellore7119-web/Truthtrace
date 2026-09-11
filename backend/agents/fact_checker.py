"""
Fact Checker Agent for TruthTrace.
Wraps and synthesizes Google Fact Check Tools API responses and registry verifications.
"""
from .base_agent import BaseAgent, AgentResult
from typing import Dict, Any, List, Optional
import logging
import os
import httpx

logger = logging.getLogger(__name__)

class FactCheckAgent(BaseAgent):
    """
    Evaluates claims using Google Fact Check Tools API and verified fact-checking registries.
    """
    def __init__(self):
        super().__init__("FactChecker")
        self.fact_check_api_key = os.getenv("GOOGLE_FACT_CHECK_API_KEY")
        self.timeout = float(os.getenv("TRUTHTRACE_FACTCHECK_TIMEOUT", "10.0"))

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Input: {'claims': List[str], 'provenance': Optional[List[Dict]], 'raw_sources': Optional[Dict]}
        Output: {'fact_check_results': List[Dict]}
        """
        try:
            claims = input_data.get('claims', [])
            if not claims and 'claim' in input_data:
                claims = [input_data['claim']]

            if not claims:
                return AgentResult(success=False, error="No claims provided to Fact Checker")

            provenance = input_data.get('provenance', [])
            results = []

            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                for claim in claims:
                    # 1. Check if provenance already contains Google Fact Check records
                    existing_fc_items = [
                        p for p in provenance 
                        if p.get('source_type') == 'google_fact_check' and p.get('claim') == claim
                    ]

                    # 2. If none present and API key is configured, query directly
                    if not existing_fc_items and self.fact_check_api_key and not self.fact_check_api_key.startswith("your_"):
                        existing_fc_items = await self._query_google_fact_check(client, claim)

                    # 3. Derive verdict and confidence from available fact-checks
                    if existing_fc_items:
                        sources = []
                        ratings = []
                        for item in existing_fc_items:
                            meta = item.get('raw_metadata', item)
                            rating = meta.get('rating', '')
                            ratings.append(rating.lower())
                            sources.append({
                                'name': meta.get('publisher') or meta.get('publisher_site') or 'Fact Check Registry',
                                'url': item.get('url') or meta.get('url', ''),
                                'rating': rating,
                                'review_date': meta.get('timestamp') or meta.get('review_date')
                            })

                        verdict, confidence = self._normalize_verdict(ratings)
                    else:
                        # Fallback heuristic analysis if no direct registry match found
                        sources = [
                            {
                                'name': 'FactCheck Aggregator (Unregistered)',
                                'url': 'https://toolbox.google.com/factcheck/explorer',
                                'rating': 'Unverified Claim',
                                'review_date': None
                            }
                        ]
                        verdict = "unverified"
                        confidence = 0.50

                    results.append({
                        'claim': claim,
                        'verdict': verdict,
                        'confidence': confidence,
                        'sources': sources,
                        'matches_count': len(existing_fc_items)
                    })

            return AgentResult(
                success=True,
                data={'fact_check_results': results}
            )

        except Exception as e:
            logger.error(f"FactChecker agent error: {e}")
            return AgentResult(success=False, error=str(e))

    async def _query_google_fact_check(self, client: httpx.AsyncClient, claim: str) -> List[Dict[str, Any]]:
        """Query Google Fact Check Tools API for a claim."""
        results = []
        try:
            url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
            params = {
                "query": claim[:100],
                "key": self.fact_check_api_key,
                "pageSize": 5
            }
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                for c in data.get("claims", []):
                    for review in c.get("claimReview", []):
                        results.append({
                            "title": review.get("title") or c.get("text", ""),
                            "url": review.get("url", ""),
                            "publisher": review.get("publisher", {}).get("name", "Fact Checker"),
                            "publisher_site": review.get("publisher", {}).get("site", ""),
                            "rating": review.get("textualRating", ""),
                            "timestamp": review.get("reviewDate")
                        })
        except Exception as e:
            logger.debug(f"Fact Checker direct API lookup failed: {e}")
        return results

    def _normalize_verdict(self, ratings: List[str]) -> tuple[str, float]:
        """Normalize textual ratings (e.g. 'False', 'Pants on Fire', 'Mostly False') to canonical verdict."""
        false_count = 0
        true_count = 0
        misleading_count = 0
        satire_count = 0

        for r in ratings:
            r_lower = r.lower()
            if any(w in r_lower for w in ["false", "pants on fire", "incorrect", "fake", "fabricated", "hoax"]):
                false_count += 1
            elif any(w in r_lower for w in ["true", "correct", "accurate"]):
                true_count += 1
            elif any(w in r_lower for w in ["satire", "parody", "joke"]):
                satire_count += 1
            elif any(w in r_lower for w in ["misleading", "mixture", "half true", "unsupported", "out of context", "missing context"]):
                misleading_count += 1

        total = len(ratings)
        if total == 0:
            return "unverified", 0.50

        if false_count > true_count and false_count >= misleading_count:
            return "false", min(0.95, 0.70 + (false_count / total) * 0.25)
        elif misleading_count > 0:
            return "misleading", min(0.90, 0.65 + (misleading_count / total) * 0.25)
        elif satire_count > 0:
            return "satire", 0.85
        elif true_count > false_count:
            return "true", min(0.95, 0.70 + (true_count / total) * 0.25)
        else:
            return "misleading", 0.70