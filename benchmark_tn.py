"""
TruthTrace Ground-Truth Benchmark Evaluation Script for Tamil Nadu 2026 Political Claims.

Benchmark Suite:
1. Frontline 'Vijay wave' cover        | Ground truth: FALSE (fabricated)
2. STR video 'no regime change'        | Ground truth: FALSE / MISLEADING (2016 video re-dated)
3. Kanimozhi 'chased by voters' video  | Ground truth: FALSE / MISLEADING (2024 video out of context)
4. TVK won outright majority           | Ground truth: TRUE (confirmed result)

Run:
    python benchmark_tn.py
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from agents.claim_extractor import ClaimExtractorAgent
from agents.osint_hunter import OSINTHunterAgent
from agents.social_hunter import SocialHunterAgent
from agents.wayback_agent import WaybackAgent
from agents.fact_checker import FactCheckAgent
from agents.narrative_profiler import NarrativeProfilerAgent
from agents.red_team_auditor import RedTeamAuditorAgent
from agents.attribution_agent import AttributionAgent
from agents.video_analyst import VideoAnalystAgent
from agents.synthesizer import SynthesizerAgent

BENCHMARK_CASES = [
    {
        "claim": "Frontline magazine published cover on Vijay wave in Tamil Nadu election 2026",
        "ground_truth": "FALSE (fabricated)",
        "expected": ["false"],
        "label": "Frontline Vijay wave cover"
    },
    {
        "claim": "Actor STR video statement says no regime change in Tamil Nadu",
        "ground_truth": "FALSE (2016 video, re-dated)",
        "expected": ["false", "misleading"],
        "label": "STR video 'no regime change'"
    },
    {
        "claim": "DMK leader Kanimozhi chased away by angry voters during election campaign video",
        "ground_truth": "FALSE (2024 video, reversed)",
        "expected": ["false", "misleading"],
        "label": "Kanimozhi 'chased by voters'"
    },
    {
        "claim": "TVK won outright majority in Tamil Nadu Assembly Election results confirmed by ECI",
        "ground_truth": "TRUE (confirmed by ECI)",
        "expected": ["true"],
        "label": "TVK won outright majority"
    }
]

async def run_benchmark():
    print("=" * 85)
    print("TruthTrace Ground-Truth Benchmark Evaluation: Tamil Nadu 2026 Election Claims")
    print("=" * 85)

    extractor = ClaimExtractorAgent()
    osint_hunter = OSINTHunterAgent()
    social_hunter = SocialHunterAgent()
    wayback_agent = WaybackAgent()
    fact_checker = FactCheckAgent()
    narrative_profiler = NarrativeProfilerAgent()
    red_team = RedTeamAuditorAgent()
    attribution_agent = AttributionAgent()
    video_analyst = VideoAnalystAgent()
    synthesizer = SynthesizerAgent()

    scorecard = []

    for idx, case in enumerate(BENCHMARK_CASES, start=1):
        claim = case["claim"]
        label = case["label"]
        gt = case["ground_truth"]
        expected = case["expected"]

        print(f"\n[{idx}/4] Analyzing: {label}...")

        # Phase 0: Extraction
        extract_res = await extractor.execute({"claim": claim})
        claims_list = extract_res.data.get("claims", [claim])

        # Phase 1: Parallel Investigation
        phase1_tasks = [
            osint_hunter.execute({"claims": claims_list}),
            social_hunter.execute({"claims": claims_list}),
            wayback_agent.execute({"urls": []}),
            fact_checker.execute({"claims": claims_list}),
            narrative_profiler.execute({"claims": claims_list}),
            attribution_agent.execute({"claims": claims_list, "urls": []}),
            video_analyst.execute({"claims": claims_list})
        ]

        p1_res = await asyncio.gather(*phase1_tasks, return_exceptions=True)

        osint_res = p1_res[0].data if hasattr(p1_res[0], 'data') else {}
        social_res = p1_res[1].data if hasattr(p1_res[1], 'data') else {}
        wayback_res = p1_res[2].data if hasattr(p1_res[2], 'data') else {}
        fc_res = p1_res[3].data if hasattr(p1_res[3], 'data') else {}
        narrative_res = p1_res[4].data if hasattr(p1_res[4], 'data') else {}
        attr_res = p1_res[5].data if hasattr(p1_res[5], 'data') else {}
        video_res = p1_res[6].data if hasattr(p1_res[6], 'data') else {}

        prov = osint_res.get("provenance", [])
        soc_prov = social_res.get("provenance", [])

        # Phase 2: Red Team Audit
        audit_res = await red_team.execute({
            "provenance": prov + soc_prov,
            "domains": [d.get("domain") for d in attr_res.get("domains", []) if d.get("domain")],
            "fact_checks": fc_res.get("fact_check_results", []),
            "snapshots": wayback_res.get("snapshots", {})
        })
        audit_data = audit_res.data if audit_res.success else {}

        # Phase 3: Synthesis
        synth_res = await synthesizer.execute({
            "claims": claims_list,
            "provenance": prov,
            "social_provenance": soc_prov,
            "fact_check_results": fc_res.get("fact_check_results", []),
            "wayback_snapshots": wayback_res.get("snapshots", {}),
            "narrative_analysis": narrative_res,
            "red_team_audit": audit_data,
            "attribution": attr_res,
            "video_forensics": video_res
        })

        dossier = synth_res.data
        verdict = dossier.get("overall_verdict", "unverified")
        conf = dossier.get("overall_confidence", 0.50)
        num_prov = len(prov) + len(soc_prov)

        match = verdict in expected
        status = "PASS" if match else "FAIL"

        print(f"    Verdict: {verdict.upper()} | Confidence: {conf:.2f} | Provenance Items: {num_prov} | Match: {status}")

        scorecard.append({
            "label": label,
            "ground_truth": gt,
            "verdict": verdict,
            "confidence": conf,
            "num_prov": num_prov,
            "status": status
        })

    print("\n" + "=" * 85)
    print(f"{'Claim':<32} | {'Ground Truth':<25} | {'Verdict':<12} | {'Conf':<6} | {'Prov':<5} | {'Result':<6}")
    print("-" * 85)
    for s in scorecard:
        print(f"{s['label']:<32} | {s['ground_truth']:<25} | {s['verdict']:<12} | {s['confidence']:<6.2f} | {s['num_prov']:<5} | {s['status']:<6}")
    print("=" * 85)

    passed_count = sum(1 for s in scorecard if s["status"] == "PASS")
    print(f"\nBenchmark Score: {passed_count}/{len(scorecard)} correct ({passed_count/len(scorecard)*100:.0f}%)")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
