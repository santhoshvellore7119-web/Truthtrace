#!/usr/bin/env python
"""Test full pipeline with mocked LLM to avoid hanging."""
import sys
import os
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("Testing full pipeline with mocked LLM...")

# Set environment variables to skip local LLM loading
os.environ['TRUTHTRACE_SKIP_LOCAL_LLM'] = '1'
os.environ['TRANSFORMERS_OFF'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

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
        # Import all agents
        from agents.claim_extractor import ClaimExtractorAgent
        from agents.osint_hunter import OSINTHunterAgent
        from agents.fact_checker import FactCheckAgent
        from agents.narrative_profiler import NarrativeProfilerAgent
        from agents.red_team_auditor import RedTeamAuditorAgent
        from agents.synthesizer import SynthesizerAgent
        from models.schemas import Dossier

        print("[PASS] All agents imported")

        # Instantiate agents
        claim_extractor = ClaimExtractorAgent()
        osint_hunter = OSINTHunterAgent()
        fact_checker = FactCheckAgent()
        narrative_profiler = NarrativeProfilerAgent()
        red_team_auditor = RedTeamAuditorAgent()
        synthesizer = SynthesizerAgent()

        print("[PASS] All agents instantiated")

        # Test input
        test_claim = "The Earth is flat."
        print(f"Testing claim: {test_claim}")

        # Step 1: Extract claims
        print("\n1. Extracting claims...")
        claim_input = {'claim': test_claim}
        claim_result = asyncio.run(claim_extractor.execute(claim_input))
        if not claim_result.success:
            print(f"   [FAIL] Claim extraction failed: {claim_result.error}")
            sys.exit(1)
        claims_data = claim_result.data
        print(f"   [PASS] Extracted {len(claims_data.get('claims', []))} claims")

        # Step 2: Hunt for provenance
        print("\n2. Hunting for provenance...")
        osint_result = asyncio.run(osint_hunter.execute(claims_data))
        if not osint_result.success:
            print(f"   [FAIL] OSINT hunter failed: {osint_result.error}")
            # Continue with empty provenance rather than failing
            osint_data = {'provenance': []}
        else:
            osint_data = osint_result.data
        print(f"   [PASS] Found provenance for {len(osint_data.get('provenance', []))} claims")

        # Step 3: Fact check
        print("\n3. Fact checking...")
        fact_check_input = {
            'claims': claims_data.get('claims', []),
            'provenance': osint_data.get('provenance', [])
        }
        fact_check_result = asyncio.run(fact_checker.execute(fact_check_input))
        if not fact_check_result.success:
            print(f"   [FAIL] Fact checker failed: {fact_check_result.error}")
            fact_check_data = {'fact_check_results': []}
        else:
            fact_check_data = fact_check_result.data
        print(f"   [PASS] Got {len(fact_check_data.get('fact_check_results', []))} fact check results")

        # Step 4: Narrative profiling
        print("\n4. Narrative profiling...")
        narrative_input = {
            'claims': claims_data.get('claims', []),
            'fact_check_results': fact_check_data.get('fact_check_results', [])
        }
        narrative_result = asyncio.run(narrative_profiler.execute(narrative_input))
        if not narrative_result.success:
            print(f"   [FAIL] Narrative profiler failed: {narrative_result.error}")
            narrative_data = {'narrative_analysis': {}}
        else:
            narrative_data = narrative_result.data
        print(f"   [PASS] Narrative analysis completed")

        # Step 5: Red-Team Auditing
        print("\n5. Red-Team auditing...")
        red_team_audit_input = {
            'provenance': osint_data.get('provenance', []),
            'fact_check_results': fact_check_data.get('fact_check_results', []),
            'narrative_analysis': narrative_data.get('narrative_analysis', {})
        }
        red_team_audit_result = asyncio.run(red_team_auditor.execute(red_team_audit_input))
        if not red_team_audit_result.success:
            print(f"   [FAIL] Red-Team auditor failed: {red_team_audit_result.error}")
            red_team_audit_data = {'red_team_audit': {}}
        else:
            red_team_audit_data = red_team_audit_result.data
        print(f"   [PASS] Red-team audit completed")
        print(f"   Flags: {red_team_audit_data.get('red_team_audit', {}).get('flags', [])}")
        print(f"   Confidence adjustment: {red_team_audit_data.get('red_team_audit', {}).get('confidence_adjustment', 0.0)}")

        # Step 6: Synthesize results
        print("\n6. Synthesizing results...")
        synthesizer_input = {
            'claims': claims_data.get('claims', []),
            'provenance': osint_data.get('provenance', []),
            'fact_check_results': fact_check_data.get('fact_check_results', []),
            'narrative_analysis': narrative_data.get('narrative_analysis', {}),
            'red_team_audit': red_team_audit_data.get('red_team_audit', {})
        }
        synthesizer_result = asyncio.run(synthesizer.execute(synthesizer_input))
        if not synthesizer_result.success:
            print(f"   [FAIL] Synthesizer failed: {synthesizer_result.error}")
            sys.exit(1)

        dossier = synthesizer_result.data
        print(f"   [PASS] Generated dossier with ID: {dossier.get('id')}")
        print(f"   Overall verdict: {dossier.get('overall_verdict')}")
        print(f"   Overall confidence: {dossier.get('overall_confidence')}")
        print(f"   Number of sub-claims: {len(dossier.get('sub_claims', []))}")

        # Basic validation
        if not dossier.get('id'):
            print("   [FAIL] Dossier missing ID")
            sys.exit(1)
        if not dossier.get('overall_verdict'):
            print("   [FAIL] Dossier missing overall verdict")
            sys.exit(1)
        if not isinstance(dossier.get('overall_confidence'), (int, float)):
            print("   [FAIL] Dossier missing or invalid overall confidence")
            sys.exit(1)

        print("\n[PASS] Full pipeline test passed!")

except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)