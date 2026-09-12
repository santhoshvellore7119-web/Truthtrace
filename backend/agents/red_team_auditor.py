from .base_agent import BaseAgent, AgentResult
from typing import Dict, Any, List
import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class RedTeamAuditorAgent(BaseAgent):
    """Red-Team Auditor that actively tries to break the outputs of other agents."""

    def __init__(self):
        super().__init__("RedTeamAuditor")

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Input: {
            'provenance': List[Dict],   # from OSINT Hunter
            'fact_check_results': List[Dict], # from Fact Checker
            'narrative_analysis': Dict   # from Narrative Profiler
        }
        Output: {
            'red_team_audit': {
                'flags': List[str],
                'source_credibility_concerns': List[str],
                'confidence_adjustment': float   # applied to final dossier confidence (negative reduces confidence)
            }
        }
        """
        try:
            logger.info(f"RedTeamAuditor received input_data: {input_data}")
            provenance = input_data.get('provenance', [])
            fact_check_results = input_data.get('fact_check_results', [])
            narrative_analysis = input_data.get('narrative_analysis', {})

            logger.info(f"RedTeamAuditor extracted: provenance={type(provenance)}, fact_check_results={type(fact_check_results)}, narrative_analysis={type(narrative_analysis)}")

            flags = []
            source_credibility_concerns = []
            confidence_adjustment = 0.0  # start neutral, we'll subtract for concerns

            # 1. Check source credibility in provenance, social provenance, and fact check results
            # We look at all URLs and flag known low-credibility domains, suspicious TLDs, or URL patterns.
            low_credibility_indicators = [
                'example.com',
                'fakenews',
                'hoax',
                'buzzfeed.fake',
                'conspiracy',
                'clickbait',
                'unverified-source'
            ]
            suspicious_tlds = ['.xyz', '.top', '.buzz', '.news-update', '.click', '.tk', '.gq', '.cf', '.ga', '.ml']

            # Helper to check a URL for low credibility indicators
            def check_url_credibility(url: str) -> List[str]:
                concerns = []
                if not url or not isinstance(url, str):
                    return concerns
                try:
                    parsed = urlparse(url)
                    domain = parsed.netloc.lower()
                    if not domain:
                        domain = url.lower()
                    # Check against known low credibility indicators
                    for indicator in low_credibility_indicators:
                        if indicator in domain:
                            concerns.append(f"Domain '{domain}' contains low-credibility indicator '{indicator}'")
                    # Check suspicious TLDs
                    for tld in suspicious_tlds:
                        if domain.endswith(tld):
                            concerns.append(f"Domain '{domain}' uses suspicious TLD '{tld}' commonly associated with throwaway disinformation sites")
                    # Check URL length, odd patterns
                    if len(domain) > 50:
                        concerns.append(f"Unusually long domain name: {domain}")
                except Exception:
                    pass
                return concerns

            # Helper to extract all candidate URLs from any item
            def extract_urls(item: Any) -> List[str]:
                urls = []
                if isinstance(item, dict):
                    if item.get('url'):
                        urls.append(item['url'])
                    if item.get('source_url'):
                        urls.append(item['source_url'])
                    if isinstance(item.get('earliest_mention'), dict) and item['earliest_mention'].get('url'):
                        urls.append(item['earliest_mention']['url'])
                    if isinstance(item.get('raw_metadata'), dict):
                        meta_url = item['raw_metadata'].get('url') or item['raw_metadata'].get('source_url')
                        if meta_url:
                            urls.append(meta_url)
                    if isinstance(item.get('amplification_events'), list):
                        for event in item['amplification_events']:
                            if isinstance(event, dict) and event.get('url'):
                                urls.append(event['url'])
                elif isinstance(item, str) and item.startswith(('http://', 'https://')):
                    urls.append(item)
                return urls

            # Check provenance URLs (flat and nested)
            logger.info(f"RedTeamAuditor checking {len(provenance)} provenance items")
            inspected_urls = set()
            for i, prov in enumerate(provenance):
                urls = extract_urls(prov)
                for u in urls:
                    if u and u not in inspected_urls:
                        inspected_urls.add(u)
                        concerns = check_url_credibility(u)
                        source_credibility_concerns.extend(concerns)

            # Check fact check result sources & snapshots
            logger.info(f"RedTeamAuditor checking {len(fact_check_results)} fact check results")
            for i, fc in enumerate(fact_check_results):
                if isinstance(fc, dict):
                    for source in fc.get('sources', []):
                        if isinstance(source, dict):
                            u = source.get('url', '')
                            if u and u not in inspected_urls:
                                inspected_urls.add(u)
                                concerns = check_url_credibility(u)
                                source_credibility_concerns.extend(concerns)
                    for snapshot in fc.get('archival_snapshots', []):
                        if isinstance(snapshot, dict):
                            u = snapshot.get('url', '')
                            if u and u not in inspected_urls:
                                inspected_urls.add(u)
                                concerns = check_url_credibility(u)
                                source_credibility_concerns.extend(concerns)

            # 2. Check if narrative profiler is pattern-matching on tone (heuristic)
            logger.info(f"RedTeamAuditor checking narrative_analysis: {type(narrative_analysis)}")
            core_narrative = narrative_analysis.get('core_narrative', '')
            if not core_narrative or len(core_narrative) < 10:
                flags.append("Narrative profiler core narrative is too short or missing")
                confidence_adjustment -= 0.10

            emotional_hooks = narrative_analysis.get('emotional_hooks', [])
            if not emotional_hooks:
                flags.append("Narrative profiler did not identify any emotional hooks")
                confidence_adjustment -= 0.05

            target_demographic = narrative_analysis.get('target_demographic', '')
            if not target_demographic:
                flags.append("Narrative profiler did not identify a target demographic")
                confidence_adjustment -= 0.05

            plausible_intent = narrative_analysis.get('plausible_intent', '')
            if not plausible_intent:
                flags.append("Narrative profiler did not identify a plausible intent")
                confidence_adjustment -= 0.05

            # 3. Check for generic / suspicious patient zero handles
            logger.info(f"RedTeamAuditor checking provenance items for patient zero handle anomalies")
            generic_handle_patterns = [r'^user\d+$', r'^redditor$', r'^viral_hunter_\d+$', r'^unknown_user$', r'^telegram_broadcast$']
            for i, prov in enumerate(provenance):
                if isinstance(prov, dict):
                    handle = prov.get('handle')
                    if not handle and isinstance(prov.get('earliest_mention'), dict):
                        handle = prov['earliest_mention'].get('handle')
                    if handle:
                        for pat in generic_handle_patterns:
                            if re.match(pat, str(handle)):
                                flags.append(f"Patient zero handle '{handle}' appears generic/synthetic; may not represent authentic originator")
                                confidence_adjustment -= 0.05
                                break

            # 4. Check evidence diversity: flag if only unverified sources were found
            if provenance:
                tiers = [p.get('credibility_tier') for p in provenance if isinstance(p, dict) and p.get('credibility_tier')]
                has_authoritative = any(t in ['registry', 'mainstream', 'primary'] for t in tiers)
                if not has_authoritative:
                    flags.append("No authoritative mainstream news or IFCN registry sources found in provenance")
                    confidence_adjustment -= 0.10

            # If any source credibility concerns were found, adjust confidence
            if source_credibility_concerns:
                flags.append(f"Identified {len(source_credibility_concerns)} source credibility concern(s)")
                confidence_adjustment -= min(0.20, len(source_credibility_concerns) * 0.05)

            # Ensure confidence_adjustment is bounded between -0.40 and 0.20
            confidence_adjustment = max(-0.40, min(0.20, confidence_adjustment))

            # Deduplicate concerns and flags
            source_credibility_concerns = list(dict.fromkeys(source_credibility_concerns))
            flags = list(dict.fromkeys(flags))

            audit = {
                'flags': flags,
                'source_credibility_concerns': source_credibility_concerns,
                'confidence_adjustment': confidence_adjustment
            }

            logger.info(f"RedTeamAudit generated: {audit}")
            return AgentResult(success=True, data={'red_team_audit': audit})
        except Exception as e:
            logger.error(f"RedTeamAuditor error: {e}", exc_info=True)
            return AgentResult(success=False, error=str(e))