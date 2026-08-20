#!/usr/bin/env python
"""Debug the types returned by each agent in the pipeline."""
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
    # Import all agents
    from agents.claim_extractor import ClaimExtractorAgent
    from agents.osint_hunter import OSINTHunterAgent
    from agents.fact_checker import FactCheckAgent
    from agents.narrative_profiler import NarrativeProfilerAgent
    from agents.red_team_auditor import RedTeamAuditorAgent
    from agents.synthesizer import SynthesizerAgent

    async def debug_pipeline():
        print("=== DEBUGGING PIPELINE TYPES ===")

        # Instantiate agents
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
        print(f"   Claim extractor success: {claim_result.success}")
        if not claim_result.success:
            print(f"   ERROR: {claim_result.error}")
            return
        claims_data = claim_result.data
        print(f"   Claims data type: {type(claims_data)}")
        print(f"   Claims data: {claims_data}")
        print(f"   Number of claims: {len(claims_data.get('claims', []))}")

        # Step 2: Hunt for provenance
        print("\n2. Hunting for provenance...")
        osint_result = await osint_hunter.execute(claims_data)
        print(f"   OSINT hunter success: {osint_result.success}")
        if not osint_result.success:
            print(f"   ERROR: {osint_result.error}")
            osint_data = {'provenance': []}
        else:
            osint_data = osint_result.data
        print(f"   OSINT data type: {type(osint_data)}")
        print(f"   OSINT data keys: {osint_data.keys() if isinstance(osint_data, dict) else 'NOT A DICT'}")
        if isinstance(osint_data, dict):
            print(f"   Provenance type: {type(osint_data.get('provenance'))}")
            print(f"   Number of provenance items: {len(osint_data.get('provenance', []))}")
            if osint_data.get('provenance'):
                first_prov = osint_data['provenance'][0]
                print(f"   First provenance item type: {type(first_prov)}")
                print(f"   First provenance item keys: {first_prov.keys() if isinstance(first_prov, dict) else 'NOT A DICT'}")
                if isinstance(first_prov, dict):
                    print(f"   Has 'earliest_mention': {'earliest_mention' in first_prov}")
                    if 'earliest_mention' in first_prov:
                        mention = first_prov['earliest_mention']
                        print(f"   Earliest mention type: {type(mention)}")
                        print(f"   Earliest mention keys: {mention.keys() if isinstance(mention, dict) else 'NOT A DICT'}")
                    if 'amplification_events' in first_prov:
                        events = first_prov['amplification_events']
                        print(f"   Amplification events type: {type(events)}")
                        print(f"   Number of amplification events: {len(events)}")
                        if events:
                            first_event = events[0]
                            print(f"   First amplification event type: {type(first_event)}")
                            print(f"   First amplification event keys: {first_event.keys() if isinstance(first_event, dict) else 'NOT A DICT'}")

        # Step 3: Fact check
        print("\n3. Fact checking...")
        fact_check_input = {
            'claims': claims_data.get('claims', []),
            'provenance': osint_data.get('provenance', [])
        }
        print(f"   Fact check input claims type: {type(fact_check_input.get('claims'))}")
        print(f"   Fact check input provenance type: {type(fact_check_input.get('provenance'))}")
        fact_check_result = await fact_checker.execute(fact_check_input)
        print(f"   Fact checker success: {fact_check_result.success}")
        if not fact_check_result.success:
            print(f"   ERROR: {fact_check_result.error}")
            fact_check_data = {'fact_check_results': []}
        else:
            fact_check_data = fact_check_result.data
        print(f"   Fact check data type: {type(fact_check_data)}")
        print(f"   Fact check data keys: {fact_check_data.keys() if isinstance(fact_check_data, dict) else 'NOT A DICT'}")
        if isinstance(fact_check_data, dict):
            print(f"   Fact check results type: {type(fact_check_data.get('fact_check_results'))}")
            print(f"   Number of fact check results: {len(fact_check_data.get('fact_check_results', []))}")
            if fact_check_data.get('fact_check_results'):
                first_fc = fact_check_data['fact_check_results'][0]
                print(f"   First fact check result type: {type(first_fc)}")
                print(f"   First fact check result keys: {first_fc.keys() if isinstance(first_fc, dict) else 'NOT A DICT'}")
                if isinstance(first_fc, dict):
                    print(f"   Has 'sources': {'sources' in first_fc}")
                    if 'sources' in first_fc:
                        sources = first_fc['sources']
                        print(f"   Sources type: {type(sources)}")
                        print(f"   Number of sources: {len(sources)}")
                        if sources:
                            first_source = sources[0]
                            print(f"   First source type: {type(first_source)}")
                            print(f"   First source keys: {first_source.keys() if isinstance(first_source, dict) else 'NOT A DICT'}")
                    print(f"   Has 'archival_snapshots': {'archival_snapshots' in first_fc}")
                    if 'archival_snapshots' in first_fc:
                        snapshots = first_fc['archival_snapshots']
                        print(f"   Archival snapshots type: {type(snapshots)}")
                        print(f"   Number of archival snapshots: {len(snapshots)}")
                        if snapshots:
                            first_snapshot = snapshots[0]
                            print(f"   First archival snapshot type: {type(first_snapshot)}")
                            print(f"   First archival snapshot keys: {first_snapshot.keys() if isinstance(first_snapshot, dict) else 'NOT A DICT'}")

        # Step 4: Narrative profiling
        print("\n4. Narrative profiling...")
        narrative_input = {
            'claims': claims_data.get('claims', []),
            'fact_check_results': fact_check_data.get('fact_check_results', [])
        }
        print(f"   Narrative input claims type: {type(narrative_input.get('claims'))}")
        print(f"   Narrative input fact_check_results type: {type(narrative_input.get('fact_check_results'))}")
        narrative_result = await narrative_profiler.execute(narrative_input)
        print(f"   Narrative profiler success: {narrative_result.success}")
        if not narrative_result.success:
            print(f"   ERROR: {narrative_result.error}")
            narrative_data = {'narrative_analysis': {}}
        else:
            narrative_data = narrative_result.data
        print(f"   Narrative data type: {type(narrative_data)}")
        print(f"   Narrative data keys: {narrative_data.keys() if isinstance(narrative_data, dict) else 'NOT A DICT'}")
        if isinstance(narrative_data, dict):
            print(f"   Narrative analysis type: {type(narrative_data.get('narrative_analysis'))}")
            narrative_analysis = narrative_data.get('narrative_analysis', {})
            print(f"   Narrative analysis type: {type(narrative_analysis)}")
            print(f"   Narrative analysis keys: {narrative_analysis.keys() if isinstance(narrative_analysis, dict) else 'NOT A DICT'}")
            if isinstance(narrative_analysis, dict):
                for key in ['core_narrative', 'emotional_hooks', 'target_demographic', 'plausible_intent']:
                    val = narrative_analysis.get(key)
                    print(f"   {key}: {type(val)} = {val}")

        # Step 5: Red-Team Auditing (just check what would be passed to it)
        print("\n5. Red-Team Auditing input check...")
        red_team_audit_input = {
            'provenance': osint_data.get('provenance', []),
            'fact_check_results': fact_check_data.get('fact_check_results', []),
            'narrative_analysis': narrative_data.get('narrative_analysis', {})
        }
        print(f"   Red-team audit input provenance type: {type(red_team_audit_input.get('provenance'))}")
        print(f"   Red-team audit input fact_check_results type: {type(red_team_audit_input.get('fact_check_results'))}")
        print(f"   Red-team audit input narrative_analysis type: {type(red_team_audit_input.get('narrative_analysis'))}")

        # Actually run the RedTeamAuditor to see if it works with these inputs
        print("\n6. Running RedTeamAuditor with pipeline inputs...")
        red_team_audit_result = await red_team_auditor.execute(red_team_audit_input)
        print(f"   Red-team auditor success: {red_team_audit_result.success}")
        if not red_team_audit_result.success:
            print(f"   ERROR: {red_team_audit_result.error}")
            # Let's see what each input looks like that might be causing the issue
            provenance = red_team_audit_input.get('provenance', [])
            fact_check_results = red_team_audit_input.get('fact_check_results', [])
            narrative_analysis = red_team_audit_input.get('narrative_analysis', {})

            print(f"   Debugging inputs:")
            print(f"     Provenance is list: {isinstance(provenance, list)}")
            if provenance and len(provenance) > 0:
                print(f"     First provenance item is dict: {isinstance(provenance[0], dict)}")
                if isinstance(provenance[0], dict):
                    print(f"     First provenance item has earliest_mention: {'earliest_mention' in provenance[0]}")
                    if 'earliest_mention' in provenance[0]:
                        mention = provenance[0]['earliest_mention']
                        print(f"     Earliest mention is dict: {isinstance(mention, dict)}")

            print(f"     Fact check results is list: {isinstance(fact_check_results, list)}")
            if fact_check_results and len(fact_check_results) > 0:
                print(f"     First fact check result is dict: {isinstance(fact_check_results[0], dict)}")
                if isinstance(fact_check_results[0], dict):
                    print(f"     First fact check result has sources: {'sources' in fact_check_results[0]}")
                    if 'sources' in fact_check_results[0]:
                        sources = fact_check_results[0]['sources']
                        print(f"     Sources is list: {isinstance(sources, list)}")
                        if sources and len(sources) > 0:
                            print(f"     First source is dict: {isinstance(sources[0], dict)}")

                    print(f"     First fact check result has archival_snapshots: {'archival_snapshots' in fact_check_results[0]}")
                    if 'archival_snapshots' in fact_check_results[0]:
                        snapshots = fact_check_results[0]['archival_snapshots']
                        print(f"     Archival snapshots is list: {isinstance(snapshots, list)}")
                        if snapshots and len(snapshots) > 0:
                            print(f"     First archival snapshot is dict: {isinstance(snapshots[0], dict)}")

            print(f"     Narrative analysis is dict: {isinstance(narrative_analysis, dict)}")
            if isinstance(narrative_analysis, dict):
                print(f"     Narrative analysis has core_narrative: {'core_narrative' in narrative_analysis}")
                print(f"     Narrative analysis has emotional_hooks: {'emotional_hooks' in narrative_analysis}")
                print(f"     Narrative analysis has target_demographic: {'target_demographic' in narrative_analysis}")
                print(f"     Narrative analysis has plausible_intent: {'plausible_intent' in narrative_analysis}")
        else:
            red_team_audit_data = red_team_audit_result.data
            print(f"   Red-team auditor data type: {type(red_team_audit_data)}")
            print(f"   Red-team auditor data: {red_team_audit_data}")

            # Check what would be passed to synthesizer
            red_team_audit_for_synthesizer = red_team_audit_data.get('red_team_audit', {})
            print(f"   Red-team audit for synthesizer type: {type(red_team_audit_for_synthesizer)}")
            print(f"   Red-team audit for synthesizer: {red_team_audit_for_synthesizer}")

if __name__ == "__main__":
    asyncio.run(debug_pipeline())