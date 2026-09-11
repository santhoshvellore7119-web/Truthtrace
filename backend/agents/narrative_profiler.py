from .base_agent import BaseAgent, AgentResult
from typing import Dict, Any
from utils.llm import get_llm_prompt
import json
import logging
import re

logger = logging.getLogger(__name__)

class NarrativeProfilerAgent(BaseAgent):
    """Analyzes narrative, intent, and psychological drivers using LLM or fallback."""

    def __init__(self):
        super().__init__("NarrativeProfiler")

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Input: {'claims': List[str], 'fact_check_results': List[Dict]}
        Output: {'narrative_analysis': Dict}
        """
        try:
            claims = input_data.get('claims', [])
            fact_check = input_data.get('fact_check_results', [])
            if not claims:
                return AgentResult(success=False, error="No claims to analyze")

            # Try LLM-based analysis if available
            from utils.llm import llm_manager
            if llm_manager.is_available():
                # Prepare context
                claims_text = "\n".join([f"- {c}" for c in claims[:5]])  # limit claims
                fc_summary = ""
                if fact_check:
                    fc_summary = "\nFact-check signals: " + "; ".join([
                        f"{fc.get('verdict', 'unknown')} (confidence: {fc.get('confidence', 0):.2f})"
                        for fc in fact_check[:3]
                    ])
                prompt = f"""Analyze the following claims for underlying narrative, intent, and psychological drivers.
                Claims:
                {claims_text}
                {fc_summary}

                Provide a JSON object with the following fields:
                - core_narrative: string (the main story or theme being pushed)
                - emotional_hooks: list of strings (e.g., fear, anger, hope, outrage)
                - target_demographic: string (who is likely targeted)
                - plausible_intent: string (what the actor likely hopes to achieve)
                - motive_indicators: list of strings (observable signs of motive)
                - narrative_score: float (0-1, how strongly this fits a coordinated disinformation campaign)

                Respond with valid JSON only."""
                try:
                    llm_response = get_llm_prompt(prompt, max_tokens=512, temperature=0.4)
                    # Try to parse JSON
                    # Find JSON in response
                    json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group())
                        # Validate expected fields
                        expected = ['core_narrative', 'emotional_hooks', 'target_demographic', 'plausible_intent']
                        if all(k in analysis for k in expected):
                            logger.info("Generated narrative analysis using LLM")
                            return AgentResult(success=True, data={'narrative_analysis': analysis})
                    else:
                        logger.warning("LLM response did not contain JSON")
                except Exception as e:
                    logger.warning(f"LLM narrative analysis failed: {e}, falling back to rule-based")

            # Dynamic content-aware rule-based analysis
            analysis = self._analyze_rule_based(claims, fact_check)
            logger.info("Using dynamic content-aware narrative analysis")
            return AgentResult(success=True, data={'narrative_analysis': analysis})
        except Exception as e:
            logger.error(f"Narrative profiling error: {e}")
            return AgentResult(success=False, error=str(e))

    def _analyze_rule_based(self, claims: list, fact_check: list) -> Dict[str, Any]:
        """Derive narrative, intent, and demographic profile dynamically from claim content."""
        full_text = " ".join(claims).lower()

        # Check for media impersonation
        has_media_tweak = any(w in full_text for w in ["cover", "magazine", "frontline", "newspaper", "headline", "leak", "broadcast", "anchor", "exclusive"])

        if any(w in full_text for w in ["vijay", "tvk", "dmk", "aiadmk", "bjp", "congress", "stalin", "modi", "election", "poll", "vote", "seat", "assembly", "wave", "minister", "politics", "chief"]):
            core = "Electoral narrative shaping & regional political mobilization"
            if has_media_tweak:
                core = "Fabrication of mainstream media authority to manufacture political momentum"
            return {
                'core_narrative': core,
                'emotional_hooks': ['Partisan pride', 'Outrage', 'Electoral anticipation', 'Validation'],
                'target_demographic': 'Regional electorate, political cadres, and social media news consumers',
                'plausible_intent': 'Fabricate electoral momentum and shape voter perception ahead of upcoming polls',
                'motive_indicators': [
                    'Timing aligned with election / political mobilization cycles',
                    'Forged publication branding to bypass skepticism',
                    'High engagement across partisan social channels'
                ],
                'narrative_score': 0.88
            }
        elif any(w in full_text for w in ["vaccine", "cure", "cancer", "fda", "who", "virus", "5g", "poison", "hospital", "pharma", "medicine", "health"]):
            return {
                'core_narrative': 'Public health alarmism and institutional skepticism',
                'emotional_hooks': ['Health anxiety', 'Institutional distrust', 'Fear of medical harm'],
                'target_demographic': 'General public and health-conscious communities',
                'plausible_intent': 'Erode trust in official medical institutions and promote unverified alternatives',
                'motive_indicators': [
                    'Pseudoscience phrasing and unverified medical claims',
                    'Contradiction of established health regulator guidance'
                ],
                'narrative_score': 0.79
            }
        elif any(w in full_text for w in ["crypto", "bitcoin", "rupee", "dollar", "scheme", "scam", "bank", "stock", "tax", "inflation", "finance"]):
            return {
                'core_narrative': 'Financial anxiety and speculative wealth manipulation',
                'emotional_hooks': ['Financial urgency', 'FOMO', 'Fear of monetary loss'],
                'target_demographic': 'Retail investors, taxpayers, and online banking users',
                'plausible_intent': 'Induce economic panic or drive traffic to fraudulent financial schemes',
                'motive_indicators': [
                    'Unverified monetary policies or urgent payout promises',
                    'High-urgency calls to action'
                ],
                'narrative_score': 0.74
            }
        elif any(w in full_text for w in ["war", "military", "strike", "treaty", "sanction", "border", "espionage", "terror"]):
            return {
                'core_narrative': 'Geopolitical destabilization and national security tension',
                'emotional_hooks': ['National security fear', 'Patriotic outrage', 'Conflict anxiety'],
                'target_demographic': 'Geopolitically engaged citizens and defense observers',
                'plausible_intent': 'Polarize public opinion on foreign affairs and erode diplomatic trust',
                'motive_indicators': [
                    'Unverified defense intelligence claims',
                    'Sensationalized conflict reporting'
                ],
                'narrative_score': 0.82
            }
        else:
            first_claim = claims[0] if claims else "unspecified topic"
            return {
                'core_narrative': f"Viral amplification concerning '{first_claim[:60]}...'",
                'emotional_hooks': ['Sensationalism', 'Curiosity', 'Social validation'],
                'target_demographic': 'General social media audience',
                'plausible_intent': 'Information sharing, sensationalism, or engagement farming',
                'motive_indicators': [
                    'Sensationalist wording lacking primary source documentation',
                    'Rapid social diffusion without editorial attribution'
                ],
                'narrative_score': 0.55
            }
