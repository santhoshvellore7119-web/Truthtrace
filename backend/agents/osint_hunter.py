"""
OSINT Hunter Agent for TruthTrace.
Queries GDELT 2.0 Doc API, NewsAPI, and Google Fact Check Tools API in parallel
using asyncio and httpx to discover global provenance, news citations, and claim variants.
"""
from .base_agent import BaseAgent, AgentResult
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import httpx
import logging
import os
import re
import email.utils
import xml.etree.ElementTree as ET
import urllib.parse
from html.parser import HTMLParser
from utils.text_helpers import extract_search_keywords

logger = logging.getLogger(__name__)

class DDGLiteParser(HTMLParser):
    """HTML parser to extract real search results from DuckDuckGo Lite."""
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


class OSINTHunterAgent(BaseAgent):
    """
    Hunts for provenance across GDELT, DuckDuckGo Lite, Wikipedia, NewsAPI, and Google Fact Check API in parallel.
    """
    def __init__(self):
        super().__init__("OSINTHunter")
        self.gdelt_url = os.getenv("GDELT_API_URL", "https://api.gdeltproject.org/api/v2/doc/doc")
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self.fact_check_api_key = os.getenv("GOOGLE_FACT_CHECK_API_KEY")
        self.timeout = float(os.getenv("TRUTHTRACE_OSINT_TIMEOUT", "4.0"))

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Input: {'claims': List[str]} or {'claim': str}
        Output: {'provenance': List[Dict], 'raw_sources': Dict[str, List[Dict]]}
        """
        try:
            claims = input_data.get('claims', [])
            if not claims and 'claim' in input_data:
                claims = [input_data['claim']]
            
            if not claims:
                return AgentResult(success=False, error="No claims provided to OSINT Hunter")

            all_provenance = []
            raw_sources = {
                "web_search": [],
                "wikipedia": [],
                "google_news": [],
                "gdelt": [],
                "news_api": [],
                "fact_check": []
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            }

            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
                for idx, claim in enumerate(claims):
                    # Query Google News RSS, DDG Lite, Wikipedia, GDELT, NewsAPI, and Google Fact Check in parallel
                    tasks = [
                        self._query_google_news_rss(client, claim),
                        self._query_web_search(client, claim),
                        self._query_wikipedia(client, claim),
                        self._query_gdelt(client, claim),
                        self._query_newsapi(client, claim),
                        self._query_google_fact_check(client, claim)
                    ]
                    
                    gnews_results, web_results, wiki_results, gdelt_results, news_results, fact_check_results = await asyncio.gather(*tasks, return_exceptions=True)

                    gnews_items = gnews_results if isinstance(gnews_results, list) else []
                    web_items = web_results if isinstance(web_results, list) else []
                    wiki_items = wiki_results if isinstance(wiki_results, list) else []
                    gdelt_items = gdelt_results if isinstance(gdelt_results, list) else []
                    news_items = news_results if isinstance(news_results, list) else []
                    fc_items = fact_check_results if isinstance(fact_check_results, list) else []

                    raw_sources["google_news"].extend(gnews_items)
                    raw_sources["web_search"].extend(web_items)
                    raw_sources["wikipedia"].extend(wiki_items)
                    raw_sources["gdelt"].extend(gdelt_items)
                    raw_sources["news_api"].extend(news_items)
                    raw_sources["fact_check"].extend(fc_items)

                    # Build unified provenance records for each discovered item
                    claim_prov = []

                    # 0. Live Google News RSS items (Free, keyless, real-time indexed)
                    for item in gnews_items:
                        domain = item.get("domain", "").lower()
                        is_gov = domain.endswith('.gov') or domain.endswith('.gov.in') or domain.endswith('.nic.in') or 'eci.gov.in' in domain
                        is_registry = any(d in domain for d in ["newschecker.in", "boomlive.in", "altnews.in", "factly.in", "factcrescendo.com", "vishvasnews.com", "cyberpeace.org", "snopes.com", "politifact.com", "reuters.com", "apnews.com"])
                        is_mainstream = is_gov or any(d in domain for d in ["thehindu.com", "frontline.thehindu.com", "indianexpress.com", "bbc.com", "ndtv.com", "indiatoday.in", "newsonair.gov.in", "deccanherald.com", "deccanchronicle.com", "economictimes.indiatimes.com", "timesofindia.indiatimes.com", "indiatimes.com", "livemint.com", "hindustantimes.com", "thewire.in", "thenewsminute.com", "thefederal.com", "ddnews.gov.in", "bhaskar", "fortuneindia.com", "thesouthfirst.com"])

                        if is_registry:
                            tier = "registry"
                        elif is_mainstream:
                            tier = "mainstream"
                        else:
                            tier = "unverified"

                        claim_prov.append({
                            "claim": claim,
                            "source_type": "google_news",
                            "platform": f"News: {item.get('source_name') or domain}",
                            "title": item.get("title"),
                            "url": item.get("url"),
                            "domain": domain,
                            "timestamp": item.get("timestamp") or datetime.now().isoformat(),
                            "language": "en",
                            "credibility_tier": tier,
                            "raw_metadata": item
                        })
                    
                    # 1. Real Web search items
                    for item in web_items:
                        domain = urllib.parse.urlparse(item.get("url", "")).netloc.lower()
                        is_gov = domain.endswith('.gov') or domain.endswith('.gov.in') or domain.endswith('.nic.in') or 'eci.gov.in' in domain
                        is_registry = any(d in domain for d in ["newschecker.in", "boomlive.in", "altnews.in", "factly.in", "factcrescendo.com", "vishvasnews.com", "cyberpeace.org", "snopes.com", "politifact.com", "reuters.com", "apnews.com"])
                        is_mainstream = is_gov or any(d in domain for d in ["thehindu.com", "frontline.thehindu.com", "indianexpress.com", "bbc.com", "ndtv.com", "indiatoday.in", "newsonair.gov.in", "deccanherald.com", "deccanchronicle.com", "economictimes.indiatimes.com", "timesofindia.indiatimes.com", "indiatimes.com", "livemint.com", "hindustantimes.com", "thewire.in", "thenewsminute.com", "thefederal.com", "ddnews.gov.in", "bhaskar", "fortuneindia.com", "thesouthfirst.com"])

                        if is_registry:
                            tier = "registry"
                        elif is_mainstream:
                            tier = "mainstream"
                        else:
                            tier = "unverified"
                        if any(d in domain for d in ["newschecker.in", "boomlive.in", "altnews.in", "factly.in", "factcrescendo.com", "snopes.com", "politifact.com", "reuters.com", "apnews.com"]):
                            tier = "registry"
                        elif any(d in domain for d in ["thehindu.com", "frontline.thehindu.com", "indianexpress.com", "bbc.com", "ndtv.com", "indiatoday.in"]):
                            tier = "mainstream"

                        claim_prov.append({
                            "claim": claim,
                            "source_type": "web_search",
                            "platform": f"Web: {domain}",
                            "title": item.get("title"),
                            "url": item.get("url"),
                            "domain": domain,
                            "timestamp": datetime.now().isoformat(),
                            "language": "en",
                            "credibility_tier": tier,
                            "raw_metadata": item
                        })

                    # 2. Wikipedia knowledge items
                    for item in wiki_items:
                        claim_prov.append({
                            "claim": claim,
                            "source_type": "wikipedia",
                            "platform": "Wikipedia Reference",
                            "title": item.get("title"),
                            "url": item.get("url"),
                            "domain": "en.wikipedia.org",
                            "timestamp": datetime.now().isoformat(),
                            "language": "en",
                            "credibility_tier": "mainstream",
                            "raw_metadata": item
                        })

                    # 3. GDELT Global news
                    for item in gdelt_items:
                        claim_prov.append({
                            "claim": claim,
                            "source_type": "gdelt",
                            "platform": "GDELT Global News",
                            "title": item.get("title"),
                            "url": item.get("url"),
                            "domain": item.get("domain"),
                            "timestamp": item.get("timestamp"),
                            "language": item.get("language", "en"),
                            "credibility_tier": "mainstream" if item.get("domain") in ["reuters.com", "apnews.com", "bbc.com", "thehindu.com"] else "unverified",
                            "raw_metadata": item
                        })

                    # 4. NewsAPI items
                    for item in news_items:
                        claim_prov.append({
                            "claim": claim,
                            "source_type": "news_api",
                            "platform": f"NewsAPI ({item.get('source_name', 'News')})",
                            "title": item.get("title"),
                            "url": item.get("url"),
                            "domain": urllib.parse.urlparse(item.get("url", "")).netloc,
                            "timestamp": item.get("timestamp"),
                            "language": "en",
                            "credibility_tier": "mainstream",
                            "raw_metadata": item
                        })

                    # 5. Fact Check items
                    for item in fc_items:
                        claim_prov.append({
                            "claim": claim,
                            "source_type": "google_fact_check",
                            "platform": f"Fact Check ({item.get('publisher', 'Registry')})",
                            "title": item.get("title"),
                            "url": item.get("url"),
                            "domain": urllib.parse.urlparse(item.get("url", "")).netloc,
                            "timestamp": item.get("timestamp"),
                            "rating": item.get("rating"),
                            "credibility_tier": "registry",
                            "raw_metadata": item
                        })

                    all_provenance.extend(claim_prov)

            return AgentResult(
                success=True,
                data={
                    "provenance": all_provenance,
                    "raw_sources": raw_sources
                }
            )

        except Exception as e:
            logger.error(f"OSINT Hunter agent error: {e}")
            return AgentResult(success=False, error=str(e))

    async def _query_web_search(self, client: httpx.AsyncClient, query: str) -> List[Dict[str, Any]]:
        """Query DuckDuckGo Lite for keyless real-time web search results."""
        results = []
        try:
            ddg_url = "https://lite.duckduckgo.com/lite/"
            # Clean query
            clean_q = query[:120].strip()
            resp = await client.post(ddg_url, data={"q": clean_q})
            if resp.status_code == 200:
                parser = DDGLiteParser()
                parser.feed(resp.text)
                for res in parser.results[:8]:
                    if res.get("url") and res.get("title"):
                        results.append({
                            "title": res["title"],
                            "url": res["url"],
                            "description": res.get("snippet", "")
                        })
        except Exception as e:
            logger.debug(f"Web search error: {e}")
        return results

    async def _query_wikipedia(self, client: httpx.AsyncClient, query: str) -> List[Dict[str, Any]]:
        """Query Wikipedia OpenSearch API for relevant background entity knowledge."""
        results = []
        try:
            tokens = extract_search_keywords(query, 4)
            search_terms = " ".join(tokens)
            if not search_terms:
                return results

            wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(search_terms)}&limit=3&namespace=0&format=json"
            resp = await client.get(wiki_url)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) >= 4:
                    titles = data[1]
                    snippets = data[2] if len(data) > 2 else []
                    urls = data[3]
                    for i in range(len(titles)):
                        results.append({
                            "title": titles[i],
                            "description": snippets[i] if i < len(snippets) else "",
                            "url": urls[i] if i < len(urls) else ""
                        })
        except Exception as e:
            logger.debug(f"Wikipedia lookup error: {e}")
        return results

    async def _query_gdelt(self, client: httpx.AsyncClient, query: str) -> List[Dict[str, Any]]:
        """Query GDELT 2.0 Doc API for earliest news mentions."""
        results = []
        try:
            # Format query keywords preserving political acronyms (DMK, TVK, BJP, CM, MP)
            keywords = " ".join(extract_search_keywords(query, 5))
            if not keywords:
                keywords = query[:50]
                
            params = {
                "query": keywords,
                "mode": "artlist",
                "maxrecords": "10",
                "format": "json",
                "sort": "DateAsc" # Earliest first
            }
            resp = await client.get(self.gdelt_url, params=params)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    articles = data.get("articles", [])
                    for art in articles:
                        # Parse seendate YYYYMMDDTHHMMSSZ
                        raw_date = art.get("seendate")
                        parsed_date = None
                        if raw_date:
                            try:
                                parsed_date = datetime.strptime(raw_date, "%Y%m%dT%H%M%SZ").isoformat()
                            except Exception:
                                parsed_date = raw_date

                        results.append({
                            "title": art.get("title", ""),
                            "url": art.get("url", ""),
                            "domain": art.get("domain", ""),
                            "timestamp": parsed_date,
                            "language": art.get("language", "en"),
                            "source_country": art.get("sourcecountry", "")
                        })
                except Exception as e:
                    logger.debug(f"GDELT JSON parse warning: {e}")
        except Exception as e:
            logger.debug(f"GDELT API request failed: {e}")
        return results

    async def _query_newsapi(self, client: httpx.AsyncClient, query: str) -> List[Dict[str, Any]]:
        """Query NewsAPI Everything endpoint."""
        results = []
        if not self.news_api_key or self.news_api_key.startswith("your_"):
            return results

        try:
            keywords = " ".join(extract_search_keywords(query, 6))
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": keywords or query[:50],
                "sortBy": "publishedAt",
                "pageSize": 10,
                "apiKey": self.news_api_key
            }
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                for art in data.get("articles", []):
                    results.append({
                        "source_name": art.get("source", {}).get("name", "News"),
                        "title": art.get("title", ""),
                        "url": art.get("url", ""),
                        "description": art.get("description", ""),
                        "timestamp": art.get("publishedAt"),
                        "author": art.get("author")
                    })
        except Exception as e:
            logger.debug(f"NewsAPI request error: {e}")
        return results

    async def _query_google_fact_check(self, client: httpx.AsyncClient, query: str) -> List[Dict[str, Any]]:
        """Query Google Fact Check Tools API."""
        results = []
        if not self.fact_check_api_key or self.fact_check_api_key.startswith("your_"):
            return results

        try:
            url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
            params = {
                "query": query[:100],
                "key": self.fact_check_api_key,
                "pageSize": 10
            }
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                for claim_item in data.get("claims", []):
                    for review in claim_item.get("claimReview", []):
                        results.append({
                            "title": review.get("title") or claim_item.get("text", ""),
                            "url": review.get("url", ""),
                            "publisher": review.get("publisher", {}).get("name", "Fact Checker"),
                            "publisher_site": review.get("publisher", {}).get("site", ""),
                            "rating": review.get("textualRating", ""),
                            "timestamp": review.get("reviewDate") or claim_item.get("claimDate")
                        })
        except Exception as e:
            logger.debug(f"Google Fact Check API error: {e}")
        return results

    async def _query_google_news_rss(self, client: httpx.AsyncClient, query: str) -> List[Dict[str, Any]]:
        """Query Google News RSS for live news and fact-check citations (keyless)."""
        results = []
        try:
            tokens = extract_search_keywords(query, 5)
            clean_query = ' '.join(tokens) or query[:50]
            url = f"https://news.google.com/rss/search?q={urllib.parse.quote(clean_query)}&hl=en-IN&gl=IN&ceid=IN:en"

            resp = await client.get(url)
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                for item in root.findall('.//item')[:10]:
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    pubdate_elem = item.find('pubDate')
                    source_elem = item.find('source')

                    title = title_elem.text if title_elem is not None else ""
                    link = link_elem.text if link_elem is not None else ""
                    raw_date = pubdate_elem.text if pubdate_elem is not None else ""
                    source_name = source_elem.text if source_elem is not None else ""
                    source_url = source_elem.get('url', '') if source_elem is not None else ""

                    domain = ""
                    if source_url:
                        domain = urllib.parse.urlparse(source_url).netloc.lower()
                    if not domain and link:
                        domain = urllib.parse.urlparse(link).netloc.lower()

                    iso_date = None
                    if raw_date:
                        try:
                            dt = email.utils.parsedate_to_datetime(raw_date)
                            iso_date = dt.isoformat()
                        except Exception:
                            iso_date = raw_date

                    results.append({
                        "title": title,
                        "url": link,
                        "domain": domain,
                        "source_name": source_name,
                        "timestamp": iso_date or datetime.now().isoformat(),
                        "language": "en"
                    })
        except Exception as e:
            logger.debug(f"Google News RSS query error: {e}")
        return results