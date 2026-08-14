from .base_agent import BaseAgent, AgentResult
from ..utils.llm import get_llm_prompt
from typing import Dict, Any, List
import logging
import json

logger = logging.getLogger(__name__)

class SynthesizerAgent(BaseAgent):
    """Synthesizes results from all agents into a structured dossier using LLM or fallback."""

    def __init__(self):
        super().__init__("Synthesizer")

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Input: {
            'claims': List[str],
            'provenance': List[Dict],
            'fact_check_results': List[Dict],
            'narrative_analysis': Dict
        }
        Output: Structured dossier ready for API response
        """
        try:
            claims = input_data.get('claims', [])
            provenance = input_data.get('provenance', [])
            fact_check_results = input_data.get('fact_check_results', [])
            narrative_analysis = input_data.get('narrative_analysis', {})

            if not claims:
                return AgentResult(success=False, error="No claims to synthesize")

            # Try LLM-based synthesis if available
            from ..utils.llm import llm_manager
            if llm_manager.is_available():
                # Prepare a concise summary for LLM
                claims_text = " ".join(claims[:2])  # first claim(s)
                fc_summary = ""
                if fact_check_results:
                    fc_items = []
                    for fc in fact_check_results[:3]:
                        fc_items.append(f"Verdict: {fc.get('verdict', 'unknown')}, Confidence: {fc.get('confidence', 0):.2f}")
                    fc_summary = "; ".join(fc_items)
                narrative_summary = ""
                if narrative_analysis:
                    narrative_summary = f"Core narrative: {narrative_analysis.get('core_narrative', 'unknown')}; Intent: {narrative_analysis.get('plausible_intent', 'unknown')}"

                prompt = f"""You are an AI misinformation analyst. Given the following information, produce a structured JSON assessment.

                Claim: {claims_text}
                Fact-check summaries: {fc_summary}
                Narrative analysis: {narrative_summary}

                Provide a JSON object with:
                - verdict: one of ["CONFIRMED", "MOSTLY TRUE", "MISLEADING", "OUT OF CONTEXT", "FABRICATED", "SATIRE", "UNVERIFIED"]
                - credibility_score: float 0-100 (higher means more credible)
                - timeline: list of objects with timestamp and event (you can infer plausible timeline)
                - patient_zero: object with entity, handle, platform, account_created, bio, network_affiliations (if unknown, use null/empty)
                - source_tweaking: object with original_statement, claimed_statement, alterations (list)
                - narrative_intention: object with core_narrative, emotional_hooks (list), target_demographic, plausible_intent
                - evidence: list of objects with source, url, timestamp, type

                Use the provided info as much as possible; if unknown, indicate with empty strings or null.
                Respond with valid JSON only."""
                try:
                    llm_response = get_llm_prompt(prompt, max_tokens=1024, temperature=0.3)
                    # Extract JSON
                    import re
                    json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                    if json_match:
                        dossier = json.loads(json_match.group())
                        # Ensure all required fields exist (provide defaults if missing)
                        required_defaults = {
                            'verdict': 'UNVERIFIED',
                            'credibility_score': 50.0,
                            'timeline': [],
                            'patient_zero': {},
                            'source_tweaking': {'original_statement': '', 'claimed_statement': '', 'alterations': []},
                            'narrative_intention': {'core_narrative': '', 'emotional_hooks': [], 'target_demographic': '', 'plausible_intent': ''},
                            'evidence': []
                        }
                    for key, default in required_defaults.items():
                        if key not in dossier:
                            dossier[key] = default
                        elif isinstance(default, dict) and isinstance(dossier[key], dict):
                            # merge sub-dicts
                            for subkey, subdefault in default.items():
                                if subkey not in dossier[key]:
                                    dossier[key][subkey] = subdefault
                        elif isinstance(default, list) and isinstance(dossier[key], list):
                            # ensure list
                            pass
                    logger.info("Generated dossier using LLM")
                    return AgentResult(success=True, data=dossier)
                except Exception as e:
                    logger.warning(f"LLM synthesis failed: {e}, falling back to rule-based")

            # Fallback: rule-based synthesis (same as before but cleaned up)
            # For simplicity, we'll use the first claim's data if there are multiple
            primary_claim = claims[0] if claims else ""

            # Determine overall verdict based on fact check results
            verdict = self._determine_verdict(fact_check_results)
            credibility_score = self._calculate_credibility_score(fact_check_results)

            # Build timeline from provenance (simplified)
            timeline = self._build_timeline(provenance)

            # Extract patient zero from provenance (first mention)
            patient_zero = self._extract_patient_zero(provenance)

            # Build source tweaking analysis (simplified)
            source_tweaking = self._build_source_tweaking(claims, fact_check_results)

            # Narrative intention is directly from narrative_analysis
            narrative_intention = narrative_analysis

            # Gather evidence from fact check results and provenance
            evidence = self._gather_evidence(fact_check_results, provenance)

            # Construct the final dossier
            dossier = {
                'verdict': verdict,
                'credibility_score': credibility_score,
                'timeline': timeline,
                'patient_zero': patient_zero,
                'source_tweaking': source_tweaking,
                'narrative_intention': narrative_intention,
                'evidence': evidence
            }

            logger.info("Generated dossier using rule-based fallback")
            return AgentResult(success=True, data=dossier)
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return AgentResult(success=False, error=str(e))

    def _determine_verdict(self, fact_check_results: List[Dict]) -> str:
        """Determine overall verdict from fact check results."""
        if not fact_check_results:
            return "UNVERIFIED"

        # Simple aggregation: if any fact check says fabricated, lean towards that
        # In reality, this would be more sophisticated
        verdicts = [result.get('verdict', '').upper() for result in fact_check_results]
        if any(v == 'FABRICATED' for v in verdicts):
            return "FABRICATED"
        elif any(v == 'MISLEADING' for v in verdicts):
            return "MISLEADING"
        elif any(v == 'OUT OF CONTEXT' for v in verdicts):
            return "OUT OF CONTEXT"
        elif any(v == 'SATIRE' for v in verdicts):
            return "SATIRE"
        elif any(v in ['CONFIRMED', 'MOSTLY TRUE'] for v in verdicts):
            return "CONFIRMED"
        else:
            return "UNVERIFIED"

    def _calculate_credibility_score(self, fact_check_results: List[Dict]) -> float:
        """Calculate credibility score from fact check results."""
        if not fact_check_results:
            return 50.0  # Neutral when no data

        # Simple average of confidence scores (inverted for credibility)
        scores = []
        for result in fact_check_results:
            confidence = result.get('confidence', 0.5)
            verdict = result.get('verdict', '').upper()
            # If verdict indicates false, credibility is low; if true, high
            if verdict in ['FABRICATED', 'MISLEADING', 'OUT OF CONTEXT']:
                scores.append((1 - confidence) * 100)  # Invert and scale to 0-100
            else:
                scores.append(confidence * 100)

        return sum(scores) / len(scores) if scores else 50.0

    def _build_timeline(self, provenance: List[Dict]) -> List[Dict]:
        """Build timeline from provenance data."""
        timeline = []
        for i, prov in enumerate(provenance):
            # Add earliest mention
            if 'earliest_mention' in prov:
                mention = prov['earliest_mention']
                timeline.append({
                    'timestamp': mention.get('timestamp', ''),
                    'event': f"First appearance on {mention.get('platform', 'unknown')} by {mention.get('handle', 'unknown user')}"
                })
            # Add amplification events
            if 'amplification_events' in prov:
                for event in prov['amplification_events']:
                    timeline.append({
                        'timestamp': event.get('timestamp', ''),
                        'event': f"Amplified on {event.get('platform', 'unknown')} in {event.get('community', 'unknown community')}"
                    })
        # Sort by timestamp
        timeline.sort(key=lambda x: x['timestamp'])
        return timeline

    def _extract_patient_zero(self, provenance: List[Dict]) -> Dict:
        """Extract patient zero (earliest mention) from provenance."""
        if not provenance:
            return {}

        # Find the earliest mention across all provenance
        earliest = None
        earliest_time = None

        for prov in provenance:
            if 'earliest_mention' in prov:
                mention = prov['earliest_mention']
                timestamp = mention.get('timestamp', '')
                if timestamp and (earliest_time is None or timestamp < earliest_time):
                    earliest_time = timestamp
                    earliest = mention

        if earliest:
            return {
                'entity': earliest.get('entity', 'Unknown'),
                'handle': earliest.get('handle', 'unknown'),
                'platform': earliest.get('platform', 'unknown'),
                'account_created': earliest.get('account_created', 'unknown'),
                'bio': earliest.get('bio', ''),
                'network_affiliations': earliest.get('network_affiliations', [])
            }
        return {}

    def _build_source_tweaking(self, claims: List[str], fact_check_results: List[Dict]) -> Dict:
        """Build source tweaking analysis."""
        # Simplified: if we have fact check results, we can note alterations
        # In a real implementation, we would compare the claim to the original source
        if not fact_check_results:
            return {
                'original_statement': 'No original source found for comparison.',
                'claimed_statement': claims[0] if claims else '',
                'alterations': ['Unable to verify against original source']
            }

        # Use the first fact check result for simplicity
        fact_check = fact_check_results[0]
        original = fact_check.get('original_statement', 'Original statement not available.')
        claimed = claims[0] if claims else ''
        alterations = fact_check.get('alterations', ['No specific alterations noted'])

        return {
            'original_statement': original,
            'claimed_statement': claimed,
            'alterations': alterations
        }

    def _gather_evidence(self, fact_check_results: List[Dict], provenance: List[Dict]) -> List[Dict]:
        """Gather evidence from fact check results and provenance."""
        evidence = []

        # Add fact check sources
        for result in fact_check_results:
            for source in result.get('sources', []):
                evidence.append({
                    'source': source.get('name', 'Unknown'),
                    'url': source.get('url', ''),
                    'timestamp': source.get('timestamp', ''),
                    'type': 'fact_check'
                })
            # Add archival snapshots
            for snapshot in result.get('archival_snapshots', []):
                evidence.append({
                    'source': 'Wayback Machine',
                    'url': snapshot.get('url', ''),
                    'timestamp': snapshot.get('timestamp', ''),
                    'type': 'archival'
                })

        # Add provenance URLs as evidence
        for prov in provenance:
            if 'earliest_mention' in prov:
                mention = prov['earliest_mention']
                evidence.append({
                    'source': f"Provenance ({mention.get('platform', 'unknown')})",
                    'url': mention.get('url', ''),
                    'timestamp': mention.get('timestamp', ''),
                    'type': 'provenance'
                })

        return evidence