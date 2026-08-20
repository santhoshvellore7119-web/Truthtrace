#!/usr/bin/env python
"""Test claim extractor with mocked LLM."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("Testing claim extractor...")

# Test with mocked LLM that returns a simple response
try:
    import unittest.mock as mock

    # Create a mock LLM manager that returns a simple string
    mock_llm_manager = mock.MagicMock()
    mock_llm_manager.is_available.return_value = False  # Force fallback to regex

    with mock.patch.dict('sys.modules', {
        'utils.llm': mock.MagicMock(llm_manager=mock_llm_manager),
        'utils.llm.llm_manager': mock_llm_manager,
        'utils.llm.get_llm_prompt': mock.Mock(return_value="")
    }):
        from agents.claim_extractor import ClaimExtractorAgent

        # Test instantiation
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

print("Done.")