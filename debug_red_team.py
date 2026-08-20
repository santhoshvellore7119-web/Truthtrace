#!/usr/bin/env python
"""Debug RedTeamAuditor output."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ['TRUTHTRACE_SKIP_LOCAL_LLM'] = '1'
os.environ['TRUTHTRACE_SNAPSHOTTER_MOCK'] = '1'
import unittest.mock as mock
import asyncio

mock_llm_manager = mock.MagicMock()
mock_llm_manager.is_available.return_value = False
mock_llm_manager.generate.return_value = ""

with mock.patch.dict('sys.modules', {
    'utils.llm': mock.MagicMock(llm_manager=mock_llm_manager),
    'utils.llm.llm_manager': mock_llm_manager,
    'utils.llm.get_llm_prompt': mock.Mock(return_value="")
}):
    # Import agents
    from agents.claim_extractor import ClaimExtractorAgent
    from agents.osint_hunter import OSINTHunterAgent
    from agents.fact_checker import FactCheckAgent
    from agents.narrative_profiler import NarrativeProfilerAgent
    from agents.red_team_auditor import RedTeamAuditorAgent

    async def test_red_team():
        print("Testing RedTeamAuditor...")

        # Setup test data similar to pipeline
        claim_extractor = ClaimExtractorAgent()
        osint_hunter = OSINTHunterAgent()
        fact_checker = FactCheckAgent()
        narrative_profiler = NarrativeProfilerAgent()
        red_team_auditor = RedTeamAuditorAgent()

        test_claim = "The Earth is flat."
        print(f"Testing claim: {test_claim}")

        # Extract claims
        claim_result = await claim_extractor.execute({'claim': test_claim})
        if not claim_result.success:
            print(f"Claim extraction failed: {claim_result.error}")
            return
        claims_data = claim_result.data

        # Hunt for provenance
        osint_result = await osint_hunter.execute(claims_data)
        if not osint_result.success:
            print(f"OSINT hunter failed: {osint_result.error}")
            osint_data = {'provenance': []}
        else:
            osint_data = osint_result.data

        # Fact check
        fact_check_input = {
            'claims': claims_data.get('claims', []),
            'provenance': osint_data.get('provenance', [])
        }
        fact_check_result = await fact_checker.execute(fact_check_input)
        if not fact_check_result.success:
            print(f"Fact checker failed: {fact_check_result.error}")
            fact_check_data = {'fact_check_results': []}
        else:
            fact_check_data = fact_check_result.data

        # Narrative profiling
        narrative_input = {
            'claims': claims_data.get('claims', []),
            'fact_check_results': fact_check_data.get('fact_check_results', [])
        }
        narrative_result = await narrative_profiler.execute(narrative_input)
        if not narrative_result.success:
            print(f"Narrative profiler failed: {narrative_result.error}")
            narrative_data = {'narrative_analysis': {}}
        else:
            narrative_data = narrative_result.data

        # Red-team auditing
        red_team_audit_input = {
            'provenance': osint_data.get('provenance', []),
            'fact_check_results': fact_check_data.get('fact_check_results', []),
            'narrative_analysis': narrative_data.get('narrative_analysis', {})
        }
        print(f"Red-team audit input keys: {red_team_audit_input.keys()}")
        print(f"Provenance type: {type(red_team_audit_input.get('provenance'))}")
        print(f"Fact check results type: {type(red_team_audit_input.get('fact_check_results'))}")
        print(f"Narrative analysis type: {type(red_team_audit_input.get('narrative_analysis'))}")

        red_team_audit_result = await red_team_auditor.execute(red_team_audit_input)
        print(f"Red-team auditor success: {red_team_audit_result.success}")
        if not red_team_audit_result.success:
            print(f"Red-team auditor error: {red_team_audit_result.error}")
            return

        red_team_audit_data = red_team_audit_result.data
        print(f"Red-team auditor data type: {type(red_team_audit_data)}")
        print(f"Red-team auditor data: {red_team_audit_data}")

        if isinstance(red_team_audit_data, dict):
            print(f"Red-team auditor data keys: {red_team_audit_data.keys()}")
            if 'red_team_audit' in red_team_audit_data:
                audit = red_team_audit_data['red_team_audit']
                print(f"Actual audit type: {type(audit)}")
                print(f"Actual audit: {audit}")

if __name__ == "__main__":
    asyncio.run(test_red_team())