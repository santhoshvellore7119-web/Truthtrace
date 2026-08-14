from .base_agent import BaseAgent, AgentResult
from ..utils.llm import get_llm_prompt
import re
import logging

logger = logging.getLogger(__name__)

class ClaimExtractorAgent(BaseAgent):
    """Extracts atomic claims from text or URL using LLM or fallback."""

    def __init__(self):
        super().__init__("ClaimExtractor")

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Input: {'claim': str, 'url': Optional[str]}
        Output: {'claims': List[str]}
        """
        try:
            text = input_data.get('claim', '')
            if not text and input_data.get('url'):
                # In real implementation, fetch URL content
                text = f"Content from URL: {input_data['url']}"

            if not text:
                return AgentResult(success=False, error="No claim text provided")

            # Try LLM-based extraction if available
            from ..utils.llm import llm_manager
            if llm_manager.is_available():
                prompt = f"""Extract atomic, verifiable claims from the following text.
                Return each claim on a new line, numbered or bulleted.
                Focus on factual statements that can be checked for truthfulness.
                Text: {text}

                Claims:"""
                try:
                    llm_response = get_llm_prompt(prompt, max_tokens=256, temperature=0.3)
                    # Parse lines
                    lines = [line.strip() for line in llm_response.split('\n') if line.strip()]
                    # Remove numbering/bullets
                    claims = []
                    for line in lines:
                        # Remove leading numbers, bullets, etc.
                        cleaned = re.sub(r'^[\d\-\*\•\.\s]+', '', line).strip()
                        if cleaned and len(cleaned) > 10:  # minimal length
                            claims.append(cleaned)
                    if claims:
                        logger.info(f"Extracted {len(claims)} claims using LLM")
                        return AgentResult(success=True, data={'claims': claims})
                except Exception as e:
                    logger.warning(f"LLM claim extraction failed: {e}, falling back to regex")

            # Fallback: simple sentence splitting
            sentences = re.split(r'[.!?]+', text)
            claims = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
            logger.info(f"Extracted {len(claims)} claims using regex fallback")
            return AgentResult(success=True, data={'claims': claims})
        except Exception as e:
            logger.error(f"Claim extraction error: {e}")
            return AgentResult(success=False, error=str(e))