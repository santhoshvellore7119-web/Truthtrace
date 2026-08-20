#!/usr/bin/env python
"""Simple import test avoiding LLM."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("Testing simple imports...")

# Test base agent first
try:
    from agents.base_agent import BaseAgent, AgentResult
    print("[PASS] BaseAgent imported")
except Exception as e:
    print(f"[FAIL] BaseAgent failed: {e}")

# Test importing claim_extractor but mocking the llm import
try:
    # Mock the llm module before importing claim_extractor
    import unittest.mock as mock
    with mock.patch.dict('sys.modules', {
        'utils.llm': mock.MagicMock(),
        'utils.llm.llm_manager': mock.MagicMock(),
        'utils.llm.get_llm_prompt': mock.MagicMock()
    }):
        from agents.claim_extractor import ClaimExtractorAgent
        print("[PASS] ClaimExtractorAgent imported with mocked LLM")

        # Test instantiation
        agent = ClaimExtractorAgent()
        print("[PASS] ClaimExtractorAgent instantiated")

except Exception as e:
    print(f"[FAIL] ClaimExtractorAgent failed: {e}")
    import traceback
    traceback.print_exc()

print("Done.")