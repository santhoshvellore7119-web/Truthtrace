#!/usr/bin/env python
"""
Demo script to show TruthTrace analysis without running the server.
This uses the agents directly with rule-based fallback (since no LLM API keys are set).
"""
import asyncio
import sys
import os

# Add the backend directory to the path so we can import agents
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from agents.claim_extractor import ClaimExtractorAgent
from agents.osint_hunter import OSINTHunterAgent
from agents.fact_checker import FactCheckAgent
from agents.narrative_profiler import NarrativeProfilerAgent
from agents.synthesizer import SynthesizerAgent

async def demo_analysis(claim_text: str):
    print(f"���🔍 Analyzing claim: \"{claim_text}\"")
    print("=" * 60)

    # Initialize agents
    claim_extractor = ClaimExtractorAgent()
    osint_hunter = OSINTHunterAgent()
    fact_checker = FactCheckAgent()
    narrative_profiler = NarrativeProfilerAgent()
    synthesizer = SynthesizerAgent()

    # Step 1: Extract claims
    print("\n���📝 Step 1: Extracting claims...")
    claim_input = {'claim': claim_text}
    claim_result = await claim_extractor.execute(claim_input)
    if not claim_result.success:
        print(f"��❌ Claim extraction failed: {claim_result.error}")
        return
    claims_data = claim_result.data
    claims = claims_data.get('claims', [])
    print(f"��✅ Extracted {len(claims)} claim(s):")
    for i, c in enumerate(claims, 1):
        print(f"   {i}. {c}")

    # Step 2: Hunt for provenance
    print("\n���🕵��️‍�♂��️ Step 2: Hunting for provenance...")
    osint_result = await osint_hunter.execute(claims_data)
    if not osint_result.success:
        print(f"��⚠��️  OSINT hunt failed: {osint_result.error} (continuing with empty provenance)")
        osint_data = {'provenance': []}
    else:
        osint_data = osint_result.data
    provenance = osint_data.get('provenance', [])
    print(f"��✅ Found {len(provenance)} provenance item(s)")

    # Step 3: Fact check
    print("\n���🔎 Step 3: Fact checking...")
    fact_check_input = {
        'claims': claims,
        'provenance': provenance
    }
    fact_check_result = await fact_checker.execute(fact_check_input)
    if not fact_check_result.success:
        print(f"��⚠��️  Fact check failed: {fact_check_result.error} (continuing with empty results)")
        fact_check_data = {'fact_check_results': []}
    else:
        fact_check_data = fact_check_result.data
    fact_check_results = fact_check_data.get('fact_check_results', [])
    print(f"��✅ Completed {len(fact_check_results)} fact check(s)")

    # Step 4: Narrative profiling
    print("\n���🧠 Step 4: Profiling narrative...")
    narrative_input = {
        'claims': claims,
        'fact_check_results': fact_check_results
    }
    narrative_result = await narrative_profiler.execute(narrative_input)
    if not narrative_result.success:
        print(f"��⚠��️  Narrative profiling failed: {narrative_result.error} (continuing with empty analysis)")
        narrative_data = {'narrative_analysis': {}}
    else:
        narrative_data = narrative_result.data
    narrative_analysis = narrative_data.get('narrative_analysis', {})
    print("��✅ Narrative analysis completed")

    # Step 5: Synthesize results
    print("\n���🧩 Step 5: Synthesizing final dossier...")
    synthesizer_input = {
        'claims': claims,
        'provenance': provenance,
        'fact_check_results': fact_check_results,
        'narrative_analysis': narrative_analysis
    }
    synthesizer_result = await synthesizer.execute(synthesizer_input)
    if not synthesizer_result.success:
        print(f"��❌ Synthesis failed: {synthesizer_result.error}")
        return
    dossier = synthesizer_result.data
    print("��✅ Dossier synthesized")

    # Display results
    print("\n" + "=" * 60)
    print("���📋 TRUTHtrace ANALYSIS DOSSIER")
    print("=" * 60)

    # Verdict and credibility score
    verdict = dossier.get('verdict', 'UNVERIFIED')
    credibility = dossier.get('credibility_score', 0.0)
    verdict_emoji = {
        'CONFIRMED': '��✅',
        'MOSTLY TRUE': '��✅',
        'MISLEADING': '��⚠��️',
        'OUT OF CONTEXT': '��⚠��️',
        'FABRICATED': '��❌',
        'SATIRE': '���😏',
        'UNVERIFIED': '��❓'
    }.get(verdict, '��❓')
    print(f"{verdict_emoji} Verdict: {verdict}")
    print(f"���📊 Credibility Score: {credibility:.1f}%")

    # Timeline
    print("\n���📅 Timeline & Provenance:")
    timeline = dossier.get('timeline', [])
    if timeline:
        for event in timeline:
            print(f"   • [{event.get('timestamp', 'unknown')}] {event.get('event', 'No description')}")
    else:
        print("   No timeline data available.")

    # Patient Zero
    print("\n���🎯 Patient Zero & Origin Profile:")
    pz = dossier.get('patient_zero', {})
    if pz:
        print(f"   Entity: {pz.get('entity', 'Unknown')}")
        print(f"   Handle: @{pz.get('handle', 'unknown')}")
        print(f"   Platform: {pz.get('platform', 'unknown')}")
        print(f"   Account Created: {pz.get('account_created', 'unknown')}")
        print(f"   Bio: {pz.get('bio', 'No bio available')}")
        affils = pz.get('network_affiliations', [])
        if affils:
            print(f"   Network Affiliations: {', '.join(affils)}")
        else:
            print("   Network Affiliations: None identified")
    else:
        print("   No patient zero data available.")

    # Source Tweaking
    print("\n���🔧 Source Tweaking Analysis:")
    st = dossier.get('source_tweaking', {})
    if st:
        print(f"   Original Statement: {st.get('original_statement', 'Not available')}")
        print(f"   Claimed Statement:  {st.get('claimed_statement', 'Not available')}")
        alterations = st.get('alterations', [])
        if alterations:
            print("   Alterations Detected:")
            for alt in alterations:
                print(f"     • {alt}")
        else:
            print("   Alterations Detected: None identified")
    else:
        print("   No source tweaking data available.")

    # Narrative & Intention
    print("\n���🎭 Narrative & Intention Matrix:")
    ni = dossier.get('narrative_intention', {})
    if ni:
        print(f"   Core Narrative: {ni.get('core_narrative', 'Not identified')}")
        hooks = ni.get('emotional_hooks', [])
        if hooks:
            print(f"   Emotional Hooks: {', '.join(hooks)}")
        else:
            print("   Emotional Hooks: None identified")
        print(f"   Target Demographic: {ni.get('target_demographic', 'Not identified')}")
        print(f"   Plausible Intent: {ni.get('plausible_intent', 'Not identified')}")
    else:
        print("   No narrative intention data available.")

    # Evidence
    print("\n���📚 Evidence & Sources:")
    evidence = dossier.get('evidence', [])
    if evidence:
        for i, ev in enumerate(evidence, 1):
            print(f"   [{i}] {ev.get('source', 'Unknown Source')}")
            print(f"       URL: {ev.get('url', 'No URL')}")
            print(f"       Timestamp: {ev.get('timestamp', 'No timestamp')}")
            print(f"       Type: {ev.get('type', 'unknown')}")
            print()
    else:
        print("   No evidence collected.")

    print("=" * 60)
    print("���🔍 Analysis complete. This is a demonstration using rule-based fallback.")
    print("   With API keys, the system would use LLMs for enhanced analysis.")
    print("=" * 60)

if __name__ == "__main__":
    # Example claim - you can change this
    claim = "The Earth is flat and NASA is hiding the truth."
    asyncio.run(demo_analysis(claim))