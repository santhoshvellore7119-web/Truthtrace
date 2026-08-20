#!/usr/bin/env python
"""Test synthesizer with mocked inputs."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("Testing synthesizer with mocked inputs...")

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
        from agents.synthesizer import SynthesizerAgent
        from models.schemas import Dossier

        print("[PASS] Synthesizer imported")

        # Instantiate synthesizer
        synthesizer = SynthesizerAgent()
        print("[PASS] Synthesizer instantiated")

        # Test input with mock data
        synthesizer_input = {
            'claims': ['The Earth is flat.'],
            'provenance': [{
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
            }],
            'fact_check_results': [{
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
            }],
            'narrative_analysis': {
                'core_narrative': 'The claim that the Earth is flat appears to be part of a broader pattern of scientific skepticism.',
                'emotional_hooks': ['fear', 'distrust'],
                'target_demographic': 'individuals sceptical of mainstream science',
                'plausible_intent': 'to challenge established scientific consensus'
            },
            'red_team_audit': {
                'flags': [],
                'source_credibility_concerns': [],
                'confidence_adjustment': -0.1
            }
        }

        print("[PASS] Test input prepared")

        # Test execution
        import asyncio

        async def test_execute():
            result = await synthesizer.execute(synthesizer_input)
            return result

        print("[INFO] Executing synthesizer...")
        result = asyncio.run(test_execute())
        print("[INFO] Synthesizer execution completed")

        if result.success:
            print(f"[PASS] Synthesis successful")
            dossier = result.data
            print(f"Dossier ID: {dossier.get('id')}")
            print(f"Overall verdict: {dossier.get('overall_verdict')}")
            print(f"Overall confidence: {dossier.get('overall_confidence')}")
            print(f"Number of sub-claims: {len(dossier.get('sub_claims', []))}")

            # Validate the dossier
            if not dossier.get('id'):
                print("[FAIL] Dossier missing ID")
                sys.exit(1)
            if not dossier.get('overall_verdict'):
                print("[FAIL] Dossier missing overall verdict")
                sys.exit(1)
            if not isinstance(dossier.get('overall_confidence'), (int, float)):
                print("[FAIL] Dossier missing or invalid overall confidence")
                sys.exit(1)

            print("[PASS] Dossier validation passed")
        else:
            print(f"[FAIL] Synthesis failed: {result.error}")
            sys.exit(1)

except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("[PASS] Synthesizer test completed successfully!")