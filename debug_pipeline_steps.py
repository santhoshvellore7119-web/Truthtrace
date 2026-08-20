#!/usr/bin/env python
"""Debug each step of the pipeline to see where the issue occurs"""
import os
os.environ['TRUTHTRACE_SKIP_LOCAL_LLM'] = '1'
os.environ['TRUTHTRACE_SNAPSHOTTER_MOCK'] = '1'
import asyncio
from unittest.mock import MagicMock

# Mock LLM
mock_llm_manager = MagicMock()
mock_llm_manager.is_available.return_value = False
mock_llm_manager.generate.return_value = ''

import sys
sys.modules['utils.llm'] = MagicMock()
sys.modules['utils.llm'].llm_manager = mock_llm_manager
sys.modules['utils.llm'].get_llm_prompt = MagicMock(return_value='')

# Import agents
from agents.claim_extractor import ClaimExtractorAgent
from agents.osint_hunter import OSINTHunterAgent
from agents.fact_checker import FactCheckAgent
from agents.narrative_profiler import NarrativeProfilerAgent
from agents.red_team_auditor import RedTeamAuditorAgent
from agents.synthesizer import SynthesizerAgent

async def debug_pipeline_steps():
    print('Debugging pipeline steps...')

    # Initialize agents
    claim_extractor = ClaimExtractorAgent()
    osint_hunter = OSINTHunterAgent()
    fact_checker = FactCheckAgent()
    narrative_profiler = NarrativeProfilerAgent()
    red_team_auditor = RedTeamAuditorAgent()
    synthesizer = SynthesizerAgent()

    # Test input
    test_claim = 'The Earth is flat.'
    print(f'Testing claim: {test_claim}')

    # Step 1: Extract claims
    print('\n--- Step 1: Claim Extraction ---')
    claim_input = {'claim': test_claim}
    claim_result = await claim_extractor.execute(claim_input)
    print(f'Claim extractor success: {claim_result.success}')
    if not claim_result.success:
        print(f'  ERROR: {claim_result.error}')
        return
    claims_data = claim_result.data
    print(f'  claims_data type: {type(claims_data)}')
    print(f'  claims_data: {claims_data}')

    # Step 2: Hunt for provenance
    print('\n--- Step 2: OSINT Hunting ---')
    osint_result = await osint_hunter.execute(claims_data)
    print(f'OSINT hunter success: {osint_result.success}')
    if not osint_result.success:
        print(f'  WARN: {osint_result.error} - continuing with empty provenance')
        osint_data = {'provenance': []}
    else:
        osint_data = osint_result.data
    print(f'  osint_data type: {type(osint_data)}')
    print(f'  osint_data keys: {list(osint_data.keys()) if isinstance(osint_data, dict) else "NOT A DICT"}')
    if isinstance(osint_data, dict) and 'provenance' in osint_data:
        print(f'  provenance type: {type(osint_data["provenance"])}')
        print(f'  provenance length: {len(osint_data["provenance"])}')
        if len(osint_data["provenance"]) > 0:
            first_prov = osint_data["provenance"][0]
            print(f'  first provenance item type: {type(first_prov)}')
            if isinstance(first_prov, dict) and 'earliest_mention' in first_prov:
                mention = first_prov['earliest_mention']
                print(f'  first earliest_mention type: {type(mention)}')
                print(f'  first earliest_mention value: {mention}')

    # Step 3: Fact check
    print('\n--- Step 3: Fact Checking ---')
    fact_check_input = {
        'claims': claims_data.get('claims', []),
        'provenance': osint_data.get('provenance', [])
    }
    print(f'  fact_check_input claims type: {type(fact_check_input["claims"])}')
    print(f'  fact_check_input provenance type: {type(fact_check_input["provenance"])}')
    fact_check_result = await fact_checker.execute(fact_check_input)
    print(f'Fact checker success: {fact_check_result.success}')
    if not fact_check_result.success:
        print(f'  WARN: {fact_check_result.error} - continuing with empty results')
        fact_check_data = {'fact_check_results': []}
    else:
        fact_check_data = fact_check_result.data
    print(f'  fact_check_data type: {type(fact_check_data)}')
    print(f'  fact_check_data keys: {list(fact_check_data.keys()) if isinstance(fact_check_data, dict) else "NOT A DICT"}')
    if isinstance(fact_check_data, dict) and 'fact_check_results' in fact_check_data:
        print(f'  fact_check_results type: {type(fact_check_data["fact_check_results"])}')
        print(f'  fact_check_results length: {len(fact_check_data["fact_check_results"])}')
        if len(fact_check_data["fact_check_results"]) > 0:
            first_fc = fact_check_data["fact_check_results"][0]
            print(f'  first fact check result type: {type(first_fc)}')
            if isinstance(first_fc, dict):
                print(f'  first fact check result keys: {list(first_fc.keys())}')
                if 'sources' in first_fc:
                    sources = first_fc['sources']
                    print(f'  sources type: {type(sources)}')
                    print(f'  sources length: {len(sources)}')
                    if len(sources) > 0:
                        first_source = sources[0]
                        print(f'  first source type: {type(first_source)}')
                        if isinstance(first_source, dict):
                            print(f'  first source keys: {list(first_source.keys())}')

    # Step 4: Narrative profiling
    print('\n--- Step 4: Narrative Profiling ---')
    narrative_input = {
        'claims': claims_data.get('claims', []),
        'fact_check_results': fact_check_data.get('fact_check_results', [])
    }
    print(f'  narrative_input claims type: {type(narrative_input["claims"])}')
    print(f'  narrative_input fact_check_results type: {type(narrative_input["fact_check_results"])}')
    narrative_result = await narrative_profiler.execute(narrative_input)
    print(f'Narrative profiler success: {narrative_result.success}')
    if not narrative_result.success:
        print(f'  WARN: {narrative_result.error} - continuing with empty analysis')
        narrative_data = {'narrative_analysis': {}}
    else:
        narrative_data = narrative_result.data
    print(f'  narrative_data type: {type(narrative_data)}')
    print(f'  narrative_data keys: {list(narrative_data.keys()) if isinstance(narrative_data, dict) else "NOT A DICT"}')
    if isinstance(narrative_data, dict) and 'narrative_analysis' in narrative_data:
        print(f'  narrative_analysis type: {type(narrative_data["narrative_analysis"])}')
        print(f'  narrative_analysis value: {narrative_data["narrative_analysis"]}')

    # Step 5: Red-Team Auditing
    print('\n--- Step 5: Red-Team Auditing ---')
    red_team_audit_input = {
        'provenance': osint_data.get('provenance', []),
        'fact_check_results': fact_check_data.get('fact_check_results', []),
        'narrative_analysis': narrative_data.get('narrative_analysis', {})
    }
    print(f'  red_team_audit_input provenance type: {type(red_team_audit_input["provenance"])}')
    print(f'  red_team_audit_input fact_check_results type: {type(red_team_audit_input["fact_check_results"])}')
    print(f'  red_team_audit_input narrative_analysis type: {type(red_team_audit_input["narrative_analysis"])}')

    red_team_audit_result = await red_team_auditor.execute(red_team_audit_input)
    print(f'RedTeamAuditor success: {red_team_audit_result.success}')
    if not red_team_audit_result.success:
        print(f'  ERROR: {red_team_audit_result.error}')
        red_team_audit_data = {'red_team_audit': {}}
    else:
        red_team_audit_data = red_team_audit_result.data
    print(f'  red_team_audit_data type: {type(red_team_audit_data)}')
    print(f'  red_team_audit_data: {red_team_audit_data}')

    # CRITICAL: Check what we're extracting for the synthesizer
    print(f'\n--- CRITICAL CHECK: What we pass to synthesizer ---')
    extracted_red_team_audit = red_team_audit_data.get('red_team_audit', {})
    print(f'  extracted_red_team_audit type: {type(extracted_red_team_audit)}')
    print(f'  extracted_red_team_audit value: {extracted_red_team_audit}')

    # Step 6: Synthesis
    print('\n--- Step 6: Synthesis ---')
    synthesizer_input = {
        'claims': claims_data.get('claims', []),
        'provenance': osint_data.get('provenance', []),
        'fact_check_results': fact_check_data.get('fact_check_results', []),
        'narrative_analysis': narrative_data.get('narrative_analysis', {}),
        'red_team_audit': extracted_red_team_audit,  # This is what we're passing
        'video_analysis': []
    }
    print(f'  synthesizer_input red_team_audit type: {type(synthesizer_input["red_team_audit"])}')
    print(f'  synthesizer_input red_team_audit value: {synthesizer_input["red_team_audit"]}')

    synthesizer_result = await synthesizer.execute(synthesizer_input)
    print(f'Synthesizer success: {synthesizer_result.success}')
    if not synthesizer_result.success:
        print(f'  ERROR: {synthesizer_result.error}')
        # Let's also check the synthesizer input right before the error
        print(f'  Debugging synthesizer input:')
        for key, value in synthesizer_input.items():
            print(f'    {key}: {type(value)} = {value}')

if __name__ == '__main__':
    asyncio.run(debug_pipeline_steps())