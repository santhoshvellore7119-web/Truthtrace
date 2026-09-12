from .base_agent import BaseAgent, AgentResult
from typing import Dict, Any, List, Optional
import logging
import os
import httpx
import re
import urllib.parse
from html.parser import HTMLParser

logger = logging.getLogger(__name__)

class FactCheckDDGParser(HTMLParser):
    """HTML parser to extract real fact-check search results from DuckDuckGo Lite."""
    def __init__(self):
        super().__init__()
        self.in_result_link = False
        self.in_snippet = False
        self.current_href = None
        self.current_title = ""
        self.current_snippet = ""
        self.results = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == "a" and "result-link" in attr_dict.get("class", ""):
            self.in_result_link = True
            self.current_href = attr_dict.get("href", "")
            self.current_title = ""
        elif tag == "td" and "result-snippet" in attr_dict.get("class", ""):
            self.in_snippet = True
            self.current_snippet = ""

    def handle_endtag(self, tag):
        if tag == "a" and self.in_result_link:
            self.in_result_link = False
        elif tag == "td" and self.in_snippet:
            self.in_snippet = False
            if self.results and self.current_snippet:
                self.results[-1]["snippet"] = self.current_snippet.strip()

    def handle_data(self, data):
        if self.in_result_link:
            self.current_title += data
            if self.current_href and not any(r.get("url") == self.current_href for r in self.results):
                actual_url = self.current_href
                if "uddg=" in actual_url:
                    try:
                        actual_url = urllib.parse.unquote(actual_url.split("uddg=")[1].split("&")[0])
                    except Exception:
                        pass
                self.results.append({
                    "title": self.current_title.strip(),
                    "url": actual_url,
                    "snippet": ""
                })
        elif self.in_snippet:
            self.current_snippet += data


class FactCheckAgent(BaseAgent):
    """
    Evaluates claims using Google Fact Check Tools API, verified fact-checking registries,
    and real-time keyless registry search.
    """
    def __init__(self):
        super().__init__("FactChecker")
        self.fact_check_api_key = os.getenv("GOOGLE_FACT_CHECK_API_KEY")
        self.timeout = float(os.getenv("TRUTHTRACE_FACTCHECK_TIMEOUT", "4.0"))

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

            fact_check_domains = [
                "newschecker.in", "boomlive.in", "altnews.in", "factly.in", 
                "factcrescendo.com", "snopes.com", "politifact.com", "reuters.com", 
                "apnews.com", "cyberpeace.org", "vishvasnews.com", "thequint.com",
                "southcheck.in", "indiatoday.in", "thehindu.com", "frontline.thehindu.com",
                "eci.gov.in", "elections.tn.gov.in"
            ]

            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                for claim in claims:
                    existing_fc_items = []

                    # 1. Check if provenance contains Google Fact Check or verified fact check domains
                    for p in provenance:
                        if not isinstance(p, dict):
                            continue
                        domain = (p.get('domain') or '').lower()
                        title = (p.get('title') or '').lower()
                        if p.get('source_type') == 'google_fact_check' or any(fcd in domain for fcd in fact_check_domains) or any(w in title for w in ["fact check", "fact-check", "debunk", "is fake", "fabricated", "hoax", "morphed", "recycled"]):
                            if p not in existing_fc_items:
                                existing_fc_items.append(p)

                    # 2. If API key is configured, query Google Fact Check API
                    if self.fact_check_api_key and not self.fact_check_api_key.startswith("your_"):
                        direct_fc = await self._query_google_fact_check(client, claim)
                        existing_fc_items.extend(direct_fc)

                    # 3. If no fact-check items found yet, perform real-time keyless registry lookup
                    if not existing_fc_items:
                        keyless_fc = await self._query_keyless_fact_check(client, claim)
                        existing_fc_items.extend(keyless_fc)

                    # 4. Derive verdict and confidence from available fact-checks
                    if existing_fc_items:
                        sources = []
                        ratings = []
                        for item in existing_fc_items:
                            meta = item.get('raw_metadata', item)
                            rating = meta.get('rating') or ''
                            title = (item.get('title') or '').lower()
                            snippet = (meta.get('snippet') or meta.get('description') or '').lower()
                            combined_text = f"{title} {snippet}"
                            
                            # If no textualRating field was present, extract from title / snippet
                            if not rating:
                                if any(w in combined_text for w in ["is fake", "fake", "fabricated", "false", "hoax", "morphed", "edited", "debunked", "untrue", "no here are the facts", "circulated fake news"]):
                                    rating = "False / Fabricated"
                                elif any(w in combined_text for w in ["old video", "re-dated", "recycled", "out of context", "misleading", "missing context", "misrepresented", "different video", "2016 video", "2024 video"]):
                                    rating = "Misleading / Out of Context"
                                elif any(w in combined_text for w in ["true", "confirmed", "correct", "authentic", "official result", "declared winner", "eci confirms"]):
                                    rating = "True"
                                elif any(w in combined_text for w in ["satire", "parody"]):
                                    rating = "Satire"

                            if rating:
                                ratings.append(rating.lower())

                            sources.append({
                                'name': meta.get('publisher') or item.get('platform') or meta.get('publisher_site') or item.get('domain') or 'Fact Check Registry',
                                'url': item.get('url') or meta.get('url', ''),
                                'rating': rating or 'Analyzed Source',
                                'review_date': meta.get('timestamp') or meta.get('review_date')
                            })

                        verdict, confidence = self._normalize_verdict(ratings)
                    else:
                        sources = []
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

    async def _query_keyless_fact_check(self, client: httpx.AsyncClient, claim: str) -> List[Dict[str, Any]]:
        """Query DuckDuckGo Lite specifically for fact-checks and registry debunks."""
        results = []
        try:
            ddg_url = "https://lite.duckduckgo.com/lite/"
            stop_words = {'published', 'statement', 'during', 'says', 'away', 'video', 'magazine', 'results', 'assembly', 'election', 'tamil', 'nadu', 'about', 'actor', 'leader'}
            tokens = [w for w in re.findall(r'\w+', claim) if len(w) > 2 and w.lower() not in stop_words]
            keywords = ' '.join(tokens[:3]) or claim[:40]
            fact_query = f"{keywords} fact check"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            }
            resp = await client.post(ddg_url, data={"q": fact_query}, headers=headers)
            if resp.status_code == 200:
                parser = FactCheckDDGParser()
                parser.feed(resp.text)
                for res in parser.results[:8]:
                    if res.get("url") and res.get("title"):
                        domain = urllib.parse.urlparse(res["url"]).netloc.lower()
                        title_lower = res["title"].lower()
                        # Match recognized fact checking registries or titles with explicit fact-check markers
                        if any(d in domain for d in ["newschecker.in", "boomlive.in", "altnews.in", "factcrescendo.com", "vishvasnews.com", "cyberpeace.org", "snopes.com", "politifact.com", "reuters.com", "southcheck.in", "newsmeter.in", "thehindu.com", "eci.gov.in", "factly.in"]) or any(w in title_lower for w in ["fact check", "fake", "debunk", "false", "hoax", "misleading", "confirmed", "chased away"]):
                            results.append({
                                "title": res["title"],
                                "url": res["url"],
                                "domain": domain,
                                "source_type": "web_search",
                                "platform": f"Fact Check Registry ({domain})",
                                "raw_metadata": {
                                    "title": res["title"],
                                    "url": res["url"],
                                    "description": res.get("snippet", ""),
                                    "snippet": res.get("snippet", ""),
                                    "publisher": domain
                                }
                            })
        except Exception as e:
            logger.debug(f"Keyless fact check search error: {e}")
        return results

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
            if any(w in r_lower for w in ["false", "pants on fire", "incorrect", "fake", "fabricated", "hoax", "morphed", "edited", "debunked", "untrue", "circulated fake news"]):
                false_count += 1
            elif any(w in r_lower for w in ["true", "correct", "accurate", "confirmed", "authentic", "official result"]):
                true_count += 1
            elif any(w in r_lower for w in ["satire", "parody", "joke"]):
                satire_count += 1
            elif any(w in r_lower for w in ["misleading", "mixture", "half true", "unsupported", "out of context", "missing context", "recycled", "re-dated"]):
                misleading_count += 1

        total = len(ratings)
        if total == 0:
            return "unverified", 0.50

        if false_count > true_count and false_count >= misleading_count:
            return "false", min(0.95, 0.80 + (false_count / total) * 0.15)
        elif misleading_count > 0:
            return "misleading", min(0.90, 0.70 + (misleading_count / total) * 0.20)
        elif satire_count > 0:
            return "satire", 0.85
        elif true_count > false_count:
            return "true", min(0.95, 0.80 + (true_count / total) * 0.15)
        else:
            return "misleading", 0.70