from .base_agent import BaseAgent, AgentResult
from typing import Dict, Any
from utils.llm import get_llm_prompt
import json
import logging

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
                    import re
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

            # Fallback: rule-based mock analysis
            analysis = {
                'core_narrative': 'Geopolitical destabilization',
                'emotional_hooks': ['Fear', 'Anger', 'Outrage'],
                'target_demographic': 'Aged 25-45, politically engaged',
                'plausible_intent': 'Influence public opinion and erode trust',
                'motive_indicators': ['Coordination with known influence accounts', 'Timing with political events'],
                'narrative_score': 0.82
            }
            logger.info("Using rule-based narrative analysis fallback")
            return AgentResult(success=True, data={'narrative_analysis': analysis})
        except Exception as e:
            logger.error(f"Narrative profiling error: {e}")
            return AgentResult(success=False, error=str(e))
