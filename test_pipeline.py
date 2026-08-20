#!/usr/bin/env python
"""
Simple test script to verify the TruthTrace pipeline works end-to-end.
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
from agents.red_team_auditor import RedTeamAuditorAgent
from agents.synthesizer import SynthesizerAgent

async def test_pipeline():
    print("Testing TruthTrace pipeline...")

    # Initialize agents
    claim_extractor = ClaimExtractorAgent()
    osint_hunter = OSINTHunterAgent()
    fact_checker = FactCheckAgent()
    narrative_profiler = NarrativeProfilerAgent()
    red_team_auditor = RedTeamAuditorAgent()
    synthesizer = SynthesizerAgent()

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
    narrative_result = await narrative_profiler.execute(narrative_input)
    if not narrative_result.success:
        print(f"   Failed: {narrative_result.error}")
        narrative_data = {'narrative_analysis': {}}
    else:
        narrative_data = narrative_result.data
    print(f"   Narrative analysis completed")

    # Step 5: Red-Team Auditing
    print("\n5. Red-Team auditing...")
    red_team_audit_input = {
        'provenance': osint_data.get('provenance', []),
        'fact_check_results': fact_check_data.get('fact_check_results', []),
        'narrative_analysis': narrative_data.get('narrative_analysis', {})
    }
    red_team_audit_result = await red_team_auditor.execute(red_team_audit_input)
    if not red_team_audit_result.success:
        print(f"   Failed: {red_team_audit_result.error}")
        red_team_audit_data = {'red_team_audit': {}}
    else:
        red_team_audit_data = red_team_audit_result.data
    print(f"   Red-team audit completed")

    # Step 6: Synthesize results
    print("\n6. Synthesizing results...")
    synthesizer_input = {
        'claims': claims_data.get('claims', []),
        'provenance': osint_data.get('provenance', []),
        'fact_check_results': fact_check_data.get('fact_check_results', []),
        'narrative_analysis': narrative_data.get('narrative_analysis', {}),
        'red_team_audit': red_team_audit_data.get('red_team_audit', {})
    }
    synthesizer_result = await synthesizer.execute(synthesizer_input)
    if not synthesizer_result.success:
        print(f"   Failed: {synthesizer_result.error}")
        return False

    dossier = synthesizer_result.data
    print(f"   Generated dossier with ID: {dossier.get('id')}")
    print(f"   Overall verdict: {dossier.get('overall_verdict')}")
    print(f"   Overall confidence: {dossier.get('overall_confidence')}")
    print(f"   Number of sub-claims: {len(dossier.get('sub_claims', []))}")

    # Verify that the dossier has the required structure
    required_fields = ['id', 'input_claim', 'language', 'sub_claims', 'patient_zero',
                      'source_tweaks', 'narrative', 'red_team_audit', 'overall_verdict',
                      'overall_confidence', 'generated_at']
    for field in required_fields:
        if field not in dossier:
            print(f"   ERROR: Missing required field: {field}")
            return False

    # Verify that sub-claims have evidence unless verdict is unverified
    for subclaim in dossier.get('sub_claims', []):
        verdict = subclaim.get('verdict')
        evidence = subclaim.get('evidence', [])
        if verdict != 'unverified' and len(evidence) == 0:
            print(f"   ERROR: Sub-claim with verdict '{verdict}' has no evidence")
            return False
        if verdict == 'unverified' and subclaim.get('unverified_inference') != True:
            print(f"   WARNING: Sub-claim with verdict 'unverified' should have unverified_inference=True")

    print("\nPipeline test passed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_pipeline())
    sys.exit(0 if success else 1)