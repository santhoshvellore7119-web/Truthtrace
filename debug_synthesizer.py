#!/usr/bin/env python
"""Debug the synthesizer to see what's being passed to _build_dossier"""
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

# Import the synthesizer
from agents.synthesizer import SynthesizerAgent

# Monkey patch the _build_dossier method to add debug info
original_build_dossier = SynthesizerAgent._build_dossier

def debug_build_dossier(self, raw_dossier, claims, provenance, fact_check_results, narrative_analysis, red_team_audit, video_analysis=None):
    print(f"DEBUG: _build_dossier called with:")
    print(f"  raw_dossier type: {type(raw_dossier)}")
    print(f"  claims type: {type(claims)}")
    print(f"  provenance type: {type(provenance)}")
    print(f"  fact_check_results type: {type(fact_check_results)}")
    print(f"  narrative_analysis type: {type(narrative_analysis)}")
    print(f"  red_team_audit type: {type(red_team_audit)}")
    print(f"  red_team_audit value: {red_team_audit}")
    print(f"  video_analysis type: {type(video_analysis)}")

    # Call the original method
    return original_build_dossier(self, raw_dossier, claims, provenance, fact_check_results, narrative_analysis, red_team_audit, video_analysis)

SynthesizerAgent._build_dossier = debug_build_dossier

async def test_synthesizer_debug():
    print('Testing synthesizer with debug...')

    # Instantiate synthesizer
    synthesizer = SynthesizerAgent()

    # Test data
    test_input = {
        'claims': ['The Earth is flat.'],
        'provenance': [
            {
                'claim': 'The Earth is flat.',
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
                    'snapshot_url': 'mock://snapshot/abc123'
                },
                'amplification_events': []
            }
        ],
        'fact_check_results': [
            {
                'claim': 'The Earth is flat.',
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
        },
        'red_team_audit': {
            'flags': [],
            'source_credibility_concerns': [],
            'confidence_adjustment': 0.0
        },
        'video_analysis': []
    }

    print(f"Input red_team_audit type: {type(test_input['red_team_audit'])}")
    print(f"Input red_team_audit value: {test_input['red_team_audit']}")

    result = await synthesizer.execute(test_input)
    print(f'Result: success={result.success}')
    if not result.success:
        print(f'Error: {result.error}')

if __name__ == '__main__':
    asyncio.run(test_synthesizer_debug())