import os
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not installed. Fallback to rule-based methods.")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed.")

class LLMManager:
    """Manages LLM interactions with fallback to free models."""

    def __init__(self):
        self.openai_client = None
        self.local_pipeline = None
        self.model_name = None
        self._initialize()

    def _initialize(self):
        """Initialize LLM clients based on available API keys and libraries."""
        # Try OpenAI first if API key available
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and OPENAI_AVAILABLE:
            try:
                self.openai_client = openai.OpenAI(api_key=openai_key)
                self.model_name = "gpt-3.5-turbo"  # or from env
                logger.info("Initialized OpenAI client")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

        # Try HuggingFace Inference API if HF token available (optional)
        hf_token = os.getenv("HF_API_KEY")
        if hf_token:
            # We'll use huggingface_hub for inference API; fallback to local if needed
            try:
                from huggingface_hub import InferenceClient
                self.hf_client = InferenceClient(token=hf_token)
                self.model_name = "google/flan-t5-xl"  # free model
                logger.info("Initialized HuggingFace Inference API client")
                return
            except ImportError:
                logger.warning("huggingface_hub not installed, cannot use HF Inference API")
            except Exception as e:
                logger.warning(f"Failed to initialize HF Inference client: {e}")

        # Fallback to local free model using transformers
        if TRANSFORMERS_AVAILABLE:
            try:
                # Use a small, fast model suitable for CPU
                model_name = "google/flan-t5-small"
                logger.info(f"Loading local model {model_name} for free LLM fallback")
                self.local_pipeline = pipeline(
                    "text2text-generation",
                    model=model_name,
                    tokenizer=model_name,
                    max_length=512,
                    device=-1  # CPU
                )
                self.model_name = model_name
                logger.info("Initialized local transformers pipeline")
                return
            except Exception as e:
                logger.warning(f"Failed to load local transformers model: {e}")

        # If all else fails, we'll use rule-based fallback (already implemented in agents)
        logger.warning("No LLM available; agents will use rule-based fallback")
        self.model_name = None

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """Generate text using available LLM."""
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"OpenAI generation failed: {e}")
                # fall through to fallback

        if hasattr(self, 'hf_client'):
            try:
                # Using HF Inference API
                response = self.hf_client.text_generation(
                    prompt,
                    model=self.model_name,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                )
                return response.strip()
            except Exception as e:
                logger.error(f"HF Inference generation failed: {e}")
                # fall through to fallback

        if self.local_pipeline:
            try:
                result = self.local_pipeline(
                    prompt,
                    max_length=max_tokens,
                    temperature=temperature,
                    do_sample=True
                )
                return result[0]['generated_text'].strip()
            except Exception as e:
                logger.error(f"Local pipeline generation failed: {e}")
                # fall through to fallback

        # Fallback: return empty string or a default response
        logger.warning("No LLM available for generation; returning empty string")
        return ""

    def is_available(self) -> bool:
        """Check if any LLM is available."""
        return bool(self.openai_client or getattr(self, 'hf_client', None) or self.local_pipeline)

# Global instance
llm_manager = LLMManager()

def get_llm_prompt(prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
    """Convenience function to get LLM completion."""
    return llm_manager.generate(prompt, max_tokens=max_tokens, temperature=temperature)