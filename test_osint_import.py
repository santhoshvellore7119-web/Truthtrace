#!/usr/bin/env python
"""Test OSINT hunter import."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("Testing OSINT hunter import...")

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
        # Import agents
        from agents.osint_hunter import OSINTHunterAgent
        print("[PASS] OSINT hunter imported")

        # Instantiate agent
        agent = OSINTHunterAgent()
        print("[PASS] OSINT hunter instantiated")

except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()