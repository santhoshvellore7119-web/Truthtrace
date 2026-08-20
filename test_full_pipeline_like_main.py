#!/usr/bin/env python
"""Test full pipeline exactly like main.py"""
import os
os.environ['TRUTHTRACE_SKIP_LOCAL_LLM'] = '1'
os.environ['TRUTHTRACE_SNAPSHOTTER_MOCK'] = '1'
import asyncio
from unittest.mock import MagicMock
import traceback

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
from agents.video_analyst import VideoAnalystAgent

async def test_full_pipeline_like_main():
    print('Testing full pipeline exactly like main.py...')

    # Initialize agents (exactly like main.py)
    claim_extractor = ClaimExtractorAgent()
    osint_hunter = OSINTHunterAgent()
    fact_checker = FactCheckAgent()
    narrative_profiler = NarrativeProfilerAgent()
    red_team_auditor = RedTeamAuditorAgent()
    video_analyst = VideoAnalystAgent()
    synthesizer = SynthesizerAgent()

    # Test input (exactly like main.py AnalyzeRequest)
    test_claim = 'The Earth is flat.'
    claim_input = {'claim': test_claim}

    print(f'Step 1: Extracting claims...')
    # Step 1: Extract claims
    claim_result = await claim_extractor.execute(claim_input)
    if not claim_result.success:
        print(f'FAIL: Claim extraction failed: {claim_result.error}')
        return
    claims_data = claim_result.data
    print(f'PASS: Extracted {len(claims_data.get("claims", []))} claims')
    print(f'  claims_data: {claims_data}')

    # Step 2: Hunt for provenance
    print(f'Step 2: Hunting for provenance...')
    osint_result = await osint_hunter.execute(claims_data)
    if not osint_result.success:
        # Continue with empty provenance rather than failing
        print(f'WARN: OSINT hunter failed: {osint_result.error} - continuing with empty provenance')
        osint_data = {'provenance': []}
    else:
        osint_data = osint_result.data
    print(f'PASS: Found provenance for {len(osint_data.get("provenance", []))} claims')
    print(f'  osint_data keys: {list(osint_data.keys()) if isinstance(osint_data, dict) else "NOT A DICT"}')

    # Step 3: Fact check
    print(f'Step 3: Fact checking...')
    fact_check_input = {
        'claims': claims_data.get('claims', []),
        'provenance': osint_data.get('provenance', [])
    }
    fact_check_result = await fact_checker.execute(fact_check_input)
    if not fact_check_result.success:
        fact_check_data = {'fact_check_results': []}
    else:
        fact_check_data = fact_check_result.data
    print(f'PASS: Got {len(fact_check_data.get("fact_check_results", []))} fact check results')
    print(f'  fact_check_data keys: {list(fact_check_data.keys()) if isinstance(fact_check_data, dict) else "NOT A DICT"}')

    # Step 4: Narrative profiling
    print(f'Step 4: Narrative profiling...')
    narrative_input = {
        'claims': claims_data.get('claims', []),
        'fact_check_results': fact_check_data.get('fact_check_results', [])
    }
    narrative_result = await narrative_profiler.execute(narrative_input)
    if not narrative_result.success:
        narrative_data = {'narrative_analysis': {}}
    else:
        narrative_data = narrative_result.data
    print(f'PASS: Narrative analysis completed')
    print(f'  narrative_data keys: {list(narrative_data.keys()) if isinstance(narrative_data, dict) else "NOT A DICT"}')

    # Step 4.5: Red-Team Auditing
    print(f'Step 4.5: Red-Team Auditing...')
    red_team_audit_input = {
        'provenance': osint_data.get('provenance', []),
        'fact_check_results': fact_check_data.get('fact_check_results', []),
        'narrative_analysis': narrative_data.get('narrative_analysis', {})
    }
    print(f'  red_team_audit_input keys: {list(red_team_audit_input.keys())}')
    print(f'  red_team_audit_input provenance type: {type(red_team_audit_input["provenance"])}')
    print(f'  red_team_audit_input fact_check_results type: {type(red_team_audit_input["fact_check_results"])}')
    print(f'  red_team_audit_input narrative_analysis type: {type(red_team_audit_input["narrative_analysis"])}')

    red_team_audit_result = await red_team_auditor.execute(red_team_audit_input)
    print(f'  RedTeamAuditor result: success={red_team_audit_result.success}')
    if not red_team_audit_result.success:
        # Continue with empty audit rather than failing
        print(f'  WARN: Red-Team auditing failed: {red_team_audit_result.error} - continuing with empty audit')
        red_team_audit_data = {'red_team_audit': {}}
    else:
        red_team_audit_data = red_team_audit_result.data
    print(f'  PASS: Red-Team auditing completed')
    print(f'  red_team_audit_data: {red_team_audit_data}')
    print(f'  red_team_audit_data type: {type(red_team_audit_data)}')

    # Step 5: Video Forensic Analysis (NEW)
    print(f'Step 5: Video Forensic Analysis...')
    # Only run video analysis if we have claims that might benefit from video content
    video_analysis_data = {'video_analysis': []}
    try:
        # In a full implementation, we might intelligently decide when to run video analysis
        # For now, we'll run it on all analyses to demonstrate the capability
        video_input = {
            'claims': claims_data.get('claims', []),
            # We could also pass specific video URLs if we had them from OSINT hunting
        }
        video_result = await video_analyst.execute(video_input)
        if video_result.success:
            video_analysis_data = video_result.data
        else:
            print(f'  WARN: Video analysis failed: {video_result.error}')
            video_analysis_data = {'video_analysis': []}
    except Exception as e:
        print(f'  WARN: Video analysis error: {e}')
        video_analysis_data = {'video_analysis': []}
    print(f'  PASS: Video analysis completed')
    print(f'  video_analysis_data: {video_analysis_data}')

    # Step 6: Synthesize results
    print(f'Step 6: Synthesizing results...')
    synthesizer_input = {
        'claims': claims_data.get('claims', []),
        'provenance': osint_data.get('provenance', []),
        'fact_check_results': fact_check_data.get('fact_check_results', []),
        'narrative_analysis': narrative_data.get('narrative_analysis', {}),
        'red_team_audit': red_team_audit_data.get('red_team_audit', {}),
        'video_analysis': video_analysis_data.get('video_analysis', [])
    }
    print(f'  synthesizer_input keys: {list(synthesizer_input.keys())}')
    print(f'  synthesizer_input red_team_audit type: {type(synthesizer_input["red_team_audit"])}')
    print(f'  synthesizer_input red_team_audit value: {synthesizer_input["red_team_audit"]}')

    synthesizer_result = await synthesizer.execute(synthesizer_input)
    print(f'  Synthesizer result: success={synthesizer_result.success}')
    if not synthesizer_result.success:
        print(f'  FAIL: Synthesis failed: {synthesizer_result.error}')
        # Print traceback if available
        if hasattr(synthesizer_result, 'traceback'):
            print(f'    Traceback: {synthesizer_result.traceback}')
        import traceback
        traceback.print_exc()
    else:
        print(f'  PASS: Synthesis successful')
        dossier = synthesizer_result.data
        print(f'    Dossier ID: {dossier.get("id")}')
        print(f'    Overall verdict: {dossier.get("overall_verdict")}')
        print(f'    Overall confidence: {dossier.get("overall_confidence")}')
        print(f'    Number of sub-claims: {len(dossier.get("sub_claims", []))}')
        if 'red_team_audit' in dossier:
            print(f'    Red team audit: {dossier["red_team_audit"]}')

if __name__ == '__main__':
    asyncio.run(test_full_pipeline_like_main())