#!/usr/bin/env python
"""
Test script to verify fact checker output.
"""
import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from agents.claim_extractor import ClaimExtractorAgent
from agents.osint_hunter import OSINTHunterAgent
from agents.fact_checker import FactCheckAgent

async def test_fact_checker():
    print("Testing fact checker...")

    # Initialize agents
    claim_extractor = ClaimExtractorAgent()
    osint_hunter = OSINTHunterAgent()
    fact_checker = FactCheckAgent()

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

    # Print first provenance item to see structure
    provenance_list = osint_data.get('provenance', [])
    if provenance_list:
        print(f"   First provenance item: {provenance_list[0]}")

    # Step 3: Fact check
    print("\n3. Fact checking...")
    fact_check_input = {
        'claims': claims_data.get('claims', []),
        'provenance': osint_data.get('provenance', [])
    }
    print(f"   Fact check input keys: {fact_check_input.keys()}")
    print(f"   Number of claims: {len(fact_check_input.get('claims', []))}")
    print(f"   Number of provenance items: {len(fact_check_input.get('provenance', []))}")

    fact_check_result = await fact_checker.execute(fact_check_input)
    if not fact_check_result.success:
        print(f"   Failed: {fact_check_result.error}")
        return False

    fact_check_data = fact_check_result.data
    print(f"   Got fact check data of type: {type(fact_check_data)}")
    if isinstance(fact_check_data, dict):
        print(f"   Fact check data keys: {fact_check_data.keys()}")
        if 'fact_check_results' in fact_check_data:
            results = fact_check_data['fact_check_results']
            print(f"   Got {len(results)} fact check results")
            if results:
                print(f"   First result: {results[0]}")
                print(f"   First result type: {type(results[0])}")

    print("\nFact checker test passed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_fact_checker())
    exit(0 if success else 1)