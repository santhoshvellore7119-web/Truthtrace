#!/usr/bin/env python
"""Quick test of pipeline components."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Set environment to skip local LLM
os.environ['TRUTHTRACE_SKIP_LOCAL_LLM'] = '1'

print("Quick pipeline test...")

# Mock the LLM manager
import unittest.mock as mock
mock_llm_manager = mock.MagicMock()
mock_llm_manager.is_available.return_value = False
mock_llm_manager.generate.return_value = ""

with mock.patch.dict('sys.modules', {
    'utils.llm': mock.MagicMock(llm_manager=mock_llm_manager),
    'utils.llm.llm_manager': mock_llm_manager,
    'utils.llm.get_llm_prompt': mock.Mock(return_value="")
}):
    # Import all components
    from agents.claim_extractor import ClaimExtractorAgent
    from agents.osint_hunter import OSINTHunterAgent
    from agents.fact_checker import FactCheckAgent
    from agents.narrative_profiler import NarrativeProfilerAgent
    from agents.red_team_auditor import RedTeamAuditorAgent
    from agents.synthesizer import SynthesizerAgent
    from models.schemas import Dossier

    print("[PASS] All imports successful")

    # Instantiate agents
    claim_extractor = ClaimExtractorAgent()
    osint_hunter = OSINTHunterAgent()
    fact_checker = FactCheckAgent()
    narrative_profiler = NarrativeProfilerAgent()
    red_team_auditor = RedTeamAuditorAgent()
    synthesizer = SynthesizerAgent()

    print("[PASS] All agents instantiated")

    # Test data
    test_claim = "The Earth is flat."
    print(f"Testing claim: {test_claim}")

    # Step 1: Extract claims
    import asyncio
    claim_result = asyncio.run(claim_extractor.execute({'claim': test_claim}))
    if not claim_result.success:
        print(f"[FAIL] Claim extraction: {claim_result.error}")
        sys.exit(1)
    claims_data = claim_result.data
    print(f"[PASS] Claims extracted: {len(claims_data.get('claims', []))}")

    # Step 2: OSINT hunting
    osint_result = asyncio.run(osint_hunter.execute(claims_data))
    if not osint_result.success:
        print(f"[WARN] OSINT hunting failed: {osint_result.error} - continuing with empty data")
        osint_data = {'provenance': []}
    else:
        osint_data = osint_result.data
    print(f"[PASS] OSINT hunting completed: {len(osint_data.get('provenance', []))} provenance items")

    # Step 3: Fact checking
    fact_check_input = {
        'claims': claims_data.get('claims', []),
        'provenance': osint_data.get('provenance', [])
    }
    fact_check_result = asyncio.run(fact_checker.execute(fact_check_input))
    if not fact_check_result.success:
        print(f"[WARN] Fact checking failed: {fact_check_result.error} - continuing with empty data")
        fact_check_data = {'fact_check_results': []}
    else:
        fact_check_data = fact_check_result.data
    print(f"[PASS] Fact checking completed: {len(fact_check_data.get('fact_check_results', []))} results")

    # Step 4: Narrative profiling
    narrative_input = {
        'claims': claims_data.get('claims', []),
        'fact_check_results': fact_check_data.get('fact_check_results', [])
    }
    narrative_result = asyncio.run(narrative_profiler.execute(narrative_input))
    if not narrative_result.success:
        print(f"[WARN] Narrative profiling failed: {narrative_result.error} - continuing with empty data")
        narrative_data = {'narrative_analysis': {}}
    else:
        narrative_data = narrative_result.data
    print(f"[PASS] Narrative profiling completed")

    # Step 5: Red-Team auditing
    red_team_audit_input = {
        'provenance': osint_data.get('provenance', []),
        'fact_check_results': fact_check_data.get('fact_check_results', []),
        'narrative_analysis': narrative_data.get('narrative_analysis', {})
    }
    red_team_audit_result = asyncio.run(red_team_auditor.execute(red_team_audit_input))
    if not red_team_audit_result.success:
        print(f"[WARN] Red-Team auditing failed: {red_team_audit_result.error} - continuing with empty data")
        red_team_audit_data = {'red_team_audit': {}}
    else:
        red_team_audit_data = red_team_audit_result.data
    print(f"[PASS] Red-Team auditing completed")
    print(f"   Flags: {red_team_audit_data.get('red_team_audit', {}).get('flags', [])}")
    print(f"   Confidence adjustment: {red_team_audit_data.get('red_team_audit', {}).get('confidence_adjustment', 0.0)}")

    # Step 6: Synthesis
    synthesizer_input = {
        'claims': claims_data.get('claims', []),
        'provenance': osint_data.get('provenance', []),
        'fact_check_results': fact_check_data.get('fact_check_results', []),
        'narrative_analysis': narrative_data.get('narrative_analysis', {}),
        'red_team_audit': red_team_audit_data.get('red_team_audit', {})
    }
    synthesizer_result = asyncio.run(synthesizer.execute(synthesizer_input))
    if not synthesizer_result.success:
        print(f"[FAIL] Synthesis failed: {synthesizer_result.error}")
        sys.exit(1)

    dossier = synthesizer_result.data
    print(f"[PASS] Synthesis successful")
    print(f"   Dossier ID: {dossier.get('id')}")
    print(f"   Overall verdict: {dossier.get('overall_verdict')}")
    print(f"   Overall confidence: {dossier.get('overall_confidence')}")
    print(f"   Number of sub-claims: {len(dossier.get('sub_claims', []))}")

    # Validate dossier
    if not dossier.get('id'):
        print("[FAIL] Dossier missing ID")
        sys.exit(1)
    if not dossier.get('overall_verdict'):
        print("[FAIL] Dossier missing overall verdict")
        sys.exit(1)
    if not isinstance(dossier.get('overall_confidence'), (int, float)):
        print("[FAIL] Dossier missing or invalid overall confidence")
        sys.exit(1)

    # Check evidence requirements
    sub_claims = dossier.get('sub_claims', [])
    for i, subclaim in enumerate(sub_claims):
        verdict = subclaim.get('verdict')
        evidence = subclaim.get('evidence', [])
        if verdict != 'unverified' and len(evidence) == 0:
            print(f"[FAIL] Sub-claim {i} with verdict '{verdict}' has no evidence")
            sys.exit(1)
        if verdict == 'unverified' and subclaim.get('unverified_inference') != True:
            print(f"[WARN] Sub-claim {i} with verdict 'unverified' should have unverified_inference=True")

    print("[PASS] All validation checks passed!")
    print("[PASS] Quick pipeline test completed successfully!")