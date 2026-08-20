#!/usr/bin/env python
"""Test RedTeamAuditor directly with mock data."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Set environment variables
os.environ['TRUTHTRACE_SKIP_LOCAL_LLM'] = '1'

print("Testing RedTeamAuditor directly...")

try:
    # Import the agent
    from agents.red_team_auditor import RedTeamAuditorAgent
    from agents.base_agent import AgentResult
    print("[PASS] RedTeamAuditor imported")

    # Create instance
    auditor = RedTeamAuditorAgent()
    print("[PASS] RedTeamAuditor instantiated")

    # Test data - similar to what would come from pipeline
    test_input = {
        'provenance': [
            {
                'claim': 'The Earth is flat',
                'source_type': 'surface_web_social',
                'platform': 'Twitter/X',
                'earliest_mention': {
                    'timestamp': '2026-08-20T10:00:00Z',
                    'platform': 'Twitter/X',
                    'handle': 'test_user',
                    'url': 'https://twitter.com/test_user/status/123',
                    'content_type': 'text_post',
                    'engagement': {'likes': 10, 'shares': 5, 'comments': 3},
                    'geotag': None,
                    'language_detected': 'en',
                    'snapshot_url': 'https://twitter.com/test_user/status/123'
                },
                'amplification_events': []
            }
        ],
        'fact_check_results': [
            {
                'claim': 'The Earth is flat',
                'verdict': 'MISLEADING',
                'confidence': 0.78,
                'sources': [
                    {
                        'name': 'Snopes',
                        'url': 'https://snopes.com/fact-check/example',
                        'rating': 'Mixture',
                        'snapshot_url': 'https://snopes.com/fact-check/example'
                    }
                ],
                'archival_snapshots': []
            }
        ],
        'narrative_analysis': {
            'core_narrative': 'The claim that the Earth is flat appears to be part of a broader pattern of scientific skepticism.',
            'emotional_hooks': ['fear', 'distrust'],
            'target_demographic': 'individuals sceptical of mainstream science',
            'plausible_intent': 'to challenge established scientific consensus'
        }
    }

    print("[PASS] Test input prepared")
    print(f"Input keys: {test_input.keys()}")
    print(f"Provenance type: {type(test_input['provenance'])}")
    print(f"Fact check results type: {type(test_input['fact_check_results'])}")
    print(f"Narrative analysis type: {type(test_input['narrative_analysis'])}")

    # Import asyncio and run
    import asyncio

    async def run_test():
        result = await auditor.execute(test_input)
        return result

    print("[INFO] Executing RedTeamAuditor...")
    audit_result = asyncio.run(run_test())

    print(f"[RESULT] Success: {audit_result.success}")
    if not audit_result.success:
        print(f"[RESULT] Error: {audit_result.error}")
    else:
        print(f"[RESULT] Data type: {type(audit_result.data)}")
        print(f"[RESULT] Data: {audit_result.data}")

        if isinstance(audit_result.data, dict):
            print(f"[RESULT] Data keys: {audit_result.data.keys()}")
            if 'red_team_audit' in audit_result.data:
                audit = audit_result.data['red_team_audit']
                print(f"[RESULT] Audit type: {type(audit)}")
                print(f"[RESULT] Audit: {audit}")

except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()