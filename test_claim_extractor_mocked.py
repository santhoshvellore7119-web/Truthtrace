#!/usr/bin/env python
"""Test claim extractor with mocked LLM."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("Testing claim extractor...")

# Mock the LLM manager to be unavailable
import unittest.mock as mock

mock_llm_manager = mock.MagicMock()
mock_llm_manager.is_available.return_value = False
mock_llm_manager.generate.return_value = ""  # Empty response for LLM calls

try:
    with mock.patch.dict('sys.modules', {
        'utils.llm': mock.MagicMock(llm_manager=mock_llm_manager),
        'utils.llm.llm_manager': mock_llm_manager,
        'utils.llm.get_llm_prompt': mock.Mock(return_value="")
    }):
        # Import agent
        from agents.claim_extractor import ClaimExtractorAgent

        # Instantiate agent
        agent = ClaimExtractorAgent()
        print("[PASS] ClaimExtractorAgent instantiated")

        # Test execution
        import asyncio

        async def test_execute():
            result = await agent.execute({'claim': 'The Earth is flat. This is a test.'})
            return result

        result = asyncio.run(test_execute())

        if result.success:
            print(f"[PASS] Claim extraction successful: {result.data}")
        else:
            print(f"[FAIL] Claim extraction failed: {result.error}")

except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()