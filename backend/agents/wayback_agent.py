"""
Wayback Machine CDX API Agent for TruthTrace.
Queries the Wayback Machine CDX API to fetch the earliest archived timestamp and snapshot for any URL.
"""
from .base_agent import BaseAgent, AgentResult
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
import logging
import os
import asyncio

logger = logging.getLogger(__name__)

class WaybackAgent(BaseAgent):
    """
    Hits the Wayback Machine CDX API to retrieve the earliest archived snapshot
    and timestamp for discovered URLs.
    """
    def __init__(self):
        super().__init__("WaybackAgent")
        self.cdx_api_url = os.getenv("WAYBACK_CDX_API_URL", "https://web.archive.org/cdx/search/cdx")
        self.timeout = float(os.getenv("TRUTHTRACE_CDX_TIMEOUT", "2.5"))

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Input: {'urls': List[str]} or {'provenance': List[Dict]}
        Output: {'snapshots': Dict[str, Dict[str, Any]]}
        """
        try:
            urls = input_data.get('urls', [])
            if not urls and 'provenance' in input_data:
                # Extract URLs from provenance
                urls = []
                for prov in input_data.get('provenance', []):
                    if isinstance(prov, dict):
                        if prov.get('url'):
                            urls.append(prov['url'])
                        if prov.get('earliest_mention', {}).get('url'):
                            urls.append(prov['earliest_mention']['url'])
            
            # Deduplicate URLs and cap at 5
            unique_urls = list(dict.fromkeys([u for u in urls if u and isinstance(u, str) and u.startswith("http")]))[:5]
            if not unique_urls:
                return AgentResult(success=True, data={'snapshots': {}})

            # Run parallel lookups with rate limiting
            semaphore = asyncio.Semaphore(5)
            headers = {"User-Agent": "TruthTraceOSINTBot/1.0"}
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
                tasks = [self._fetch_earliest_snapshot(client, semaphore, url) for url in unique_urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)

            snapshots = {}
            for url, res in zip(unique_urls, results):
                if isinstance(res, dict) and res.get('earliest_timestamp'):
                    snapshots[url] = res
                else:
                    snapshots[url] = {
                        "url": url,
                        "earliest_timestamp": None,
                        "earliest_snapshot_url": None,
                        "status": "not_archived_or_failed"
                    }

            return AgentResult(
                success=True,
                data={'snapshots': snapshots}
            )
        except Exception as e:
            logger.error(f"Wayback agent execution error: {e}")
            return AgentResult(success=False, error=str(e))

    async def _fetch_earliest_snapshot(self, client: httpx.AsyncClient, semaphore: asyncio.Semaphore, url: str) -> Dict[str, Any]:
        """Fetch earliest CDX archive record for a URL."""
        async with semaphore:
            try:
                params = {
                    "url": url,
                    "output": "json",
                    "limit": "1",
                    "fl": "timestamp,original,mimetype,statuscode,digest",
                    "filter": "statuscode:200",
                    "collapse": "digest"
                }
                resp = await client.get(self.cdx_api_url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    # CDX returns [[headers], [first_row]]
                    if isinstance(data, list) and len(data) >= 2:
                        row = data[1]
                        raw_ts = row[0] # YYYYMMDDhhmmss
                        original_url = row[1] if len(row) > 1 else url
                        
                        try:
                            parsed_dt = datetime.strptime(raw_ts, "%Y%m%d%H%M%S")
                            iso_ts = parsed_dt.isoformat()
                        except Exception:
                            iso_ts = raw_ts

                        snapshot_url = f"https://web.archive.org/web/{raw_ts}/{original_url}"
                        return {
                            "url": url,
                            "earliest_timestamp": iso_ts,
                            "earliest_snapshot_url": snapshot_url,
                            "status": "archived"
                        }
            except Exception as e:
                logger.debug(f"Wayback CDX lookup failed for {url}: {e}")
            
            return {
                "url": url,
                "earliest_timestamp": None,
                "earliest_snapshot_url": None,
                "status": "not_found"
            }
