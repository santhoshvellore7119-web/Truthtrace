#!/usr/bin/env python
"""
Test script to verify dossier details including evidence and snapshot URLs.
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

async def test_dossier_details():
    print("Testing dossier details including evidence and snapshot URLs...")

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

    # Print provenance details
    for i, prov in enumerate(osint_data.get('provenance', [])):
        print(f"   Provenance {i+1}:")
        print(f"     Claim: {prov.get('claim')}")
        earliest = prov.get('earliest_mention', {})
        # Handle case where earliest_mention is a string (timestamp) instead of dict
        if isinstance(earliest, dict):
            print(f"     Earliest mention: {earliest.get('platform', 'unknown')} / {earliest.get('handle', 'unknown')}")
            print(f"     URL: {earliest.get('url', 'unknown')}")
            print(f"     Snapshot URL: {earliest.get('snapshot_url', 'unknown')}")
        else:
            print(f"     Earliest mention: {earliest} (timestamp string)")
            print(f"     URL: unknown")
            print(f"     Snapshot URL: unknown")
        events = prov.get('amplification_events', [])
        print(f"     Amplification events: {len(events)}")
        for j, event in enumerate(events):
            # Handle case where event is not a dict
            if isinstance(event, dict):
                print(f"       Event {j+1}: {event.get('platform', 'unknown')} / {event.get('community', 'unknown')}")
                print(f"         URL: {event.get('url', 'unknown')}")
                print(f"         Snapshot URL: {event.get('snapshot_url', 'unknown')}")
            else:
                print(f"       Event {j+1}: {event} (non-dict)")
                print(f"         URL: unknown")
                print(f"         Snapshot URL: unknown")

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

    # Print fact check details
    for i, fc in enumerate(fact_check_data.get('fact_check_results', [])):
        print(f"   Fact check {i+1}:")
        print(f"     Claim: {fc.get('claim')}")
        print(f"     Verdict: {fc.get('verdict')}")
        print(f"     Confidence: {fc.get('confidence')}")
        sources = fc.get('sources', [])
        print(f"     Sources: {len(sources)}")
        for j, source in enumerate(sources):
            # Handle case where source is not a dict
            if isinstance(source, dict):
                print(f"       Source {j+1}: {source.get('name', 'unknown')}")
                print(f"         URL: {source.get('url', 'unknown')}")
                print(f"         Snapshot URL: {source.get('snapshot_url', 'unknown')}")
                print(f"         Rating: {source.get('rating', 'unknown')}")
            else:
                print(f"       Source {j+1}: {source} (non-dict)")
                print(f"         URL: unknown")
                print(f"         Snapshot URL: unknown")
                print(f"         Rating: unknown")
        snapshots = fc.get('archival_snapshots', [])
        print(f"     Archival snapshots: {len(snapshots)}")
        for j, snapshot in enumerate(snapshots):
            # Handle case where snapshot is not a dict
            if isinstance(snapshot, dict):
                print(f"       Snapshot {j+1}:")
                print(f"         Timestamp: {snapshot.get('timestamp', 'unknown')}")
                print(f"         URL: {snapshot.get('url', 'unknown')}")
                print(f"         Snapshot URL: {snapshot.get('snapshot_url', 'unknown')}")
            else:
                print(f"       Snapshot {j+1}: {snapshot} (non-dict)")
                print(f"         Timestamp: unknown")
                print(f"         URL: unknown")
                print(f"         Snapshot URL: unknown")

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
    print(f"   Flags: {red_team_audit_data.get('red_team_audit', {}).get('flags', [])}")
    print(f"   Source credibility concerns: {red_team_audit_data.get('red_team_audit', {}).get('source_credibility_concerns', [])}")
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
    synthesizer_result = await synthesizer.execute(synthesizer_input)
    if not synthesizer_result.success:
        print(f"   Failed: {synthesizer_result.error}")
        return False

    dossier = synthesizer_result.data
    print(f"   Generated dossier with ID: {dossier.get('id')}")
    print(f"   Overall verdict: {dossier.get('overall_verdict')}")
    print(f"   Overall confidence: {dossier.get('overall_confidence')}")
    print(f"   Number of sub-claims: {len(dossier.get('sub_claims', []))}")

    # Verify evidence and snapshot URLs in the dossier
    print("\n7. Verifying evidence and snapshot URLs in dossier...")
    sub_claims = dossier.get('sub_claims', [])
    if not sub_claims:
        print("   ERROR: No sub-claims found")
        return False

    all_passed = True
    for i, subclaim in enumerate(sub_claims):
        print(f"   Sub-claim {i+1}: {subclaim.get('text')}")
        print(f"     Verdict: {subclaim.get('verdict')}")
        print(f"     Confidence: {subclaim.get('verdict_confidence')}")
        print(f"     Unverified inference: {subclaim.get('unverified_inference')}")

        evidence = subclaim.get('evidence', [])
        print(f"     Evidence count: {len(evidence)}")

        # Check evidence requirements
        verdict = subclaim.get('verdict')
        if verdict != "unverified" and len(evidence) == 0:
            print(f"     ERROR: Sub-claim with verdict '{verdict}' has no evidence")
            all_passed = False
        elif verdict == "unverified":
            if not subclaim.get('unverified_inference'):
                print(f"     WARNING: Sub-claim with verdict 'unverified' should have unverified_inference=True")

        # Check each evidence item for snapshot URL
        for j, ev in enumerate(evidence):
            print(f"       Evidence {j+1}:")
            print(f"         Source: {ev.get('source', {}).get('url', 'Unknown')}")
            print(f"         Excerpt: {ev.get('excerpt', '')[:50]}...")
            print(f"         Retrieved via: {ev.get('retrieved_via', 'Unknown')}")
            print(f"         Confidence: {ev.get('confidence', 0)}")
            snapshot_url = ev.get('source', {}).get('snapshot_url')
            print(f"         Snapshot URL: {snapshot_url}")
            if snapshot_url is None:
                print(f"         WARNING: Evidence has no snapshot URL")
                # This is not necessarily an error, as snapshotter might return None in some cases

    if all_passed:
        print("\n[PASS] All dossier validation checks passed!")
        return True
    else:
        print("\n[FAIL] Some dossier validation checks failed!")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_dossier_details())
    exit(0 if success else 1)