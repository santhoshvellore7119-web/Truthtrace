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

            # 1. Check source credibility in provenance and fact check results
            # We'll look at URLs and flag known low-credibility domains or URL patterns.
            low_credibility_indicators = [
                'example.com',  # placeholder, in reality we'd have a list
                'fakenews',
                'hoax',
                # Add more as needed
            ]

            # Helper to check a URL for low credibility indicators
            def check_url_credibility(url: str) -> List[str]:
                concerns = []
                try:
                    parsed = urlparse(url)
                    domain = parsed.netloc.lower()
                    # Check against known low credibility indicators
                    for indicator in low_credibility_indicators:
                        if indicator in domain:
                            concerns.append(f"Domain '{domain}' contains low-credibility indicator '{indicator}'")
                    # Additional checks: URL length, odd characters, etc.
                    if len(domain) > 50:
                        concerns.append(f"Unusually long domain: {domain}")
                except Exception:
                    pass
                return concerns

            # Check provenance URLs
            logger.info(f"RedTeamAuditor checking {len(provenance)} provenance items")
            for i, prov in enumerate(provenance):
                logger.info(f"RedTeamAuditor processing provenance item {i}: {type(prov)}")
                if 'earliest_mention' in prov:
                    mention = prov['earliest_mention']
                    logger.info(f"RedTeamAuditor earliest_mention type: {type(mention)}")
                    logger.info(f"RedTeamAuditor earliest_mention value: {mention}")
                    if not isinstance(mention, dict):
                        logger.error(f"RedTeamAuditor earliest_mention is not a dict! It is: {mention} (type: {type(mention)})")
                        # Skip this item if earliest_mention is not a dict
                        continue
                    url = mention.get('url', '')
                    if url:
                        concerns = check_url_credibility(url)
                        source_credibility_concerns.extend(concerns)
                if 'amplification_events' in prov:
                    logger.info(f"RedTeamAuditor processing amplification_events for provenance {i}")
                    for event in prov['amplification_events']:
                        url = event.get('url', '')
                        if url:
                            concerns = check_url_credibility(url)
                            source_credibility_concerns.extend(concerns)

            # Check fact check result sources (they are usually high credibility, but we check anyway)
            logger.info(f"RedTeamAuditor checking {len(fact_check_results)} fact check results")
            for i, fc in enumerate(fact_check_results):
                logger.info(f"RedTeamAuditor processing fact check result {i}: {type(fc)}")
                for source in fc.get('sources', []):
                    url = source.get('url', '')
                    if url:
                        concerns = check_url_credibility(url)
                        source_credibility_concerns.extend(concerns)
                for snapshot in fc.get('archival_snapshots', []):
                    url = snapshot.get('url', '')
                    if url:
                        concerns = check_url_credibility(url)
                        source_credibility_concerns.extend(concerns)

            # 2. Check if narrative profiler is pattern-matching on tone (heuristic)
            # We'll check if the narrative analysis is too generic or missing specific details.
            logger.info(f"RedTeamAuditor checking narrative_analysis: {type(narrative_analysis)}")
            core_narrative = narrative_analysis.get('core_narrative', '')
            if not core_narrative or len(core_narrative) < 10:
                flags.append("Narrative profiler core narrative is too short or missing")
                confidence_adjustment -= 0.1  # reduce confidence by 0.1

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

            # 3. Check if patient zero attribution is just the first result (placeholder)
            # We'll check if the earliest mention is from a platform known for low credibility or if the handle looks generic.
            # For simplicity, we'll skip this for now and add a flag if we find a generic handle.
            logger.info(f"RedTeamAuditor checking {len(provenance)} provenance items for patient zero")
            for i, prov in enumerate(provenance):
                if 'earliest_mention' in prov:
                    mention = prov['earliest_mention']
                    logger.info(f"RedTeamAuditor provenance {i} earliest_mention type: {type(mention)}")
                    logger.info(f"RedTeamAuditor provenance {i} earliest_mention value: {mention}")
                    if not isinstance(mention, dict):
                        logger.error(f"RedTeamAuditor provenance {i} earliest_mention is not a dict! It is: {mention} (type: {type(mention)})")
                        # Skip this item if earliest_mention is not a dict
                        continue
                    handle = mention.get('handle', '')
                    if handle and re.match(r'^user\d+$', handle):  # e.g., user123
                        flags.append(f"Patient zero handle '{handle}' appears generic; may not be genuine earliest")
                        confidence_adjustment -= 0.1

            # Ensure confidence_adjustment is between -1 and 1
            confidence_adjustment = max(-1.0, min(1.0, confidence_adjustment))

            # Remove duplicate concerns
            source_credibility_concerns = list(set(source_credibility_concerns))
            flags = list(set(flags))

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