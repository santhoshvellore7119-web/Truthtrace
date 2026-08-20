#!/usr/bin/env python
"""
Test script to verify narrative profiler output.
"""
import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from agents.claim_extractor import ClaimExtractorAgent
from agents.osint_hunter import OSINTHunterAgent
from agents.fact_checker import FactCheckAgent
from agents.narrative_profiler import NarrativeProfilerAgent

async def test_narrative_profiler():
    print("Testing narrative profiler...")

    # Initialize agents
    claim_extractor = ClaimExtractorAgent()
    osint_hunter = OSINTHunterAgent()
    fact_checker = FactCheckAgent()
    narrative_profiler = NarrativeProfilerAgent()

    # Test input
    test_claim = "The Earth is flat."
    print(f"Testing claim: {test_claim}")

    # Step 1: Extract claims
    print("\n1. Extracting claims...")
    claim_input = {'claim': test_claim}
    claim_result = await claim_extractor.execute(claim_input)
    if not claim_result.success:
        print(f"   Failed: {claim_result.error}")
        return False
    claims_data = claim_result.data
    print(f"   Extracted {len(claims_data.get('claims', []))} claims")

    # Step 2: Hunt for provenance
    print("\n2. Hunting for provenance...")
    osint_result = await osint_hunter.execute(claims_data)
    if not osint_result.success:
        print(f"   Failed: {osint_result.error}")
        osint_data = {'provenance': []}
    else:
        osint_data = osint_result.data
    print(f"   Found provenance for {len(osint_data.get('provenance', []))} claims")

    # Step 3: Fact check
    print("\n3. Fact checking...")
    fact_check_input = {
        'claims': claims_data.get('claims', []),
        'provenance': osint_data.get('provenance', [])
    }
    fact_check_result = await fact_checker.execute(fact_check_input)
    if not fact_check_result.success:
        print(f"   Failed: {fact_check_result.error}")
        fact_check_data = {'fact_check_results': []}
    else:
        fact_check_data = fact_check_result.data
    print(f"   Got {len(fact_check_data.get('fact_check_results', []))} fact check results")

    # Step 4: Narrative profiling
    print("\n4. Narrative profiling...")
    narrative_input = {
        'claims': claims_data.get('claims', []),
        'fact_check_results': fact_check_data.get('fact_check_results', [])
    }
    print(f"   Narrative input keys: {narrative_input.keys()}")
    print(f"   Number of claims: {len(narrative_input.get('claims', []))}")
    print(f"   Number of fact check results: {len(narrative_input.get('fact_check_results', []))}")

    narrative_result = await narrative_profiler.execute(narrative_input)
    if not narrative_result.success:
        print(f"   Failed: {narrative_result.error}")
        return False

    narrative_data = narrative_result.data
    print(f"   Got narrative data of type: {type(narrative_data)}")
    if isinstance(narrative_data, dict):
        print(f"   Narrative data keys: {narrative_data.keys()}")
        print(f"   Core narrative: {narrative_data.get('core_narrative', 'NOT FOUND')}")
        print(f"   Emotional hooks: {narrative_data.get('emotional_hooks', 'NOT FOUND')}")
        print(f"   Target demographic: {narrative_data.get('target_demographic', 'NOT FOUND')}")
        print(f"   Plausible intent: {narrative_data.get('plausible_intent', 'NOT FOUND')}")

    print("\nNarrative profiler test passed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_narrative_profiler())
    exit(0 if success else 1)