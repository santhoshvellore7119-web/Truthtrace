"""
Comprehensive test suite for TruthTrace Phases 2 through 6.
Tests Semantic Clustering, Social Ingestion, Attribution, Video Forensics, and complete pipeline.
"""
import asyncio
import sys
import os
import unittest
from datetime import datetime, timezone

# Set up python path for backend imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from models.schemas import Claim, ClaimCluster, AttributionReport, VideoForensics, Dossier
from utils.vector_store import VectorStore
from agents.social_hunter import SocialHunterAgent
from agents.attribution_agent import AttributionAgent
from agents.video_analyst import VideoAnalystAgent
from agents.osint_hunter import OSINTHunterAgent
from agents.wayback_agent import WaybackAgent
from agents.fact_checker import FactCheckAgent
from agents.synthesizer import SynthesizerAgent
from agents.claim_extractor import ClaimExtractorAgent

class TestTruthTracePhases2To6(unittest.TestCase):

    def test_semantic_clustering_phase2(self):
        """Phase 2: Verify dense embeddings and semantic claim clustering with Patient Zero extraction."""
        vs = VectorStore(collection_name="test_phase2_clustering")
        c1 = Claim(
            text="5G mobile towers cause acute respiratory illness and suppress human immunity",
            source_platform="Reddit",
            source_url="https://reddit.com/r/conspiracy/early_5g_post",
            timestamp=datetime(2023, 1, 1, tzinfo=timezone.utc)
        )
        c2 = Claim(
            text="Cellular 5G towers suppress biological immunity causing illness",
            source_platform="BlogSpot",
            source_url="https://altnews.xyz/5g_report",
            timestamp=datetime(2023, 1, 10, tzinfo=timezone.utc)
        )
        c3 = Claim(
            text="NASA James Webb telescope captures deepest infrared galaxy field",
            source_platform="NASA.gov",
            source_url="https://nasa.gov/jwst_deep_field",
            timestamp=datetime(2023, 3, 1, tzinfo=timezone.utc)
        )

        vs.add_claims([c1, c2, c3])
        clusters = vs.cluster_claims(similarity_threshold=0.25)
        
        self.assertGreaterEqual(len(clusters), 1)
        # Find the 5G cluster
        g5_clusters = [cl for cl in clusters if "5g" in cl.label.lower() or any("5g" in c.text.lower() for c in cl.claims)]
        self.assertGreaterEqual(len(g5_clusters), 1)
        target_cluster = g5_clusters[0]
        self.assertGreaterEqual(target_cluster.claim_count, 2)
        self.assertEqual(target_cluster.patient_zero_source, "https://reddit.com/r/conspiracy/early_5g_post")

    def test_async_phases_3_to_6(self):
        """Run async tests for Social Ingestion, Attribution, Video Forensics, and Synthesis."""
        asyncio.run(self._run_async_tests())

    async def _run_async_tests(self):
        # 1. Phase 3: Social Ingestion
        social_agent = SocialHunterAgent()
        soc_res = await social_agent.execute({"claims": ["Drinking salt water reverses aging"]})
        self.assertTrue(soc_res.success)
        self.assertIn("social_provenance", soc_res.data)
        self.assertGreater(len(soc_res.data["social_provenance"]), 0)

        # 2. Phase 4: Attribution Agent (WHOIS & Coordination)
        attr_agent = AttributionAgent()
        sample_prov = [
            {"url": "https://www.reuters.com/factcheck", "platform": "Reuters", "handle": "reuters"},
            {"url": "https://break-news.xyz/viral", "platform": "Twitter", "handle": "anon1"},
            {"url": "https://break-news.xyz/copy", "platform": "Telegram", "handle": "anon2"},
        ]
        attr_res = await attr_agent.execute({"provenance": sample_prov, "social_provenance": []})
        self.assertTrue(attr_res.success)
        attr_data = attr_res.data["attribution"]
        self.assertIn("domains", attr_data)
        self.assertIn("coordination", attr_data)

        # 3. Phase 5: Video Forensics
        video_agent = VideoAnalystAgent()
        vid_res = await video_agent.execute({
            "claims": ["Breaking 2026 military intercept footage"],
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        })
        self.assertTrue(vid_res.success)
        self.assertIn("video_forensics", vid_res.data)

        # 4. Full End-to-End Multi-Agent Pipeline (Phases 0 through 6)
        claim_extractor = ClaimExtractorAgent()
        osint_hunter = OSINTHunterAgent()
        wayback_agent = WaybackAgent()
        fact_checker = FactCheckAgent()
        synthesizer = SynthesizerAgent()

        claim_text = "Drinking boiled lemon water with baking soda cures biological aging."
        ext_res = await claim_extractor.execute({"claim": claim_text})
        claims = ext_res.data["claims"]

        # Parallel OSINT & Social Ingestion
        osint_task = osint_hunter.execute({"claims": claims})
        social_task = social_agent.execute({"claims": claims})
        osint_res, social_res = await asyncio.gather(osint_task, social_task)

        prov = osint_res.data.get("provenance", [])
        soc_prov = social_res.data.get("social_provenance", [])
        combined_prov = prov + soc_prov

        # Wayback CDX
        urls = [p.get("url") for p in combined_prov if p.get("url")]
        wb_res = await wayback_agent.execute({"urls": urls, "provenance": combined_prov})
        snapshots = wb_res.data.get("snapshots", {})

        # Fact Check & Attribution & Video
        fc_res = await fact_checker.execute({"claims": claims, "provenance": combined_prov})
        attr_pipeline_res = await attr_agent.execute({"provenance": prov, "social_provenance": soc_prov})
        vid_pipeline_res = await video_agent.execute({"claims": claims, "provenance": combined_prov})

        # Synthesize into complete Dossier
        synth_res = await synthesizer.execute({
            "claims": claims,
            "provenance": prov,
            "social_provenance": soc_prov,
            "wayback_snapshots": snapshots,
            "fact_check_results": fc_res.data.get("fact_check_results", []),
            "attribution": attr_pipeline_res.data.get("attribution", {}),
            "video_forensics": vid_pipeline_res.data.get("video_forensics", {})
        })

        self.assertTrue(synth_res.success)
        dossier = synth_res.data

        self.assertIn("timeline", dossier)
        self.assertIn("clusters", dossier)
        self.assertIn("attribution", dossier)
        self.assertIn("video_forensics", dossier)
        self.assertIn("patient_zero", dossier)

        print("\n===========================================================")
        print("     TRUTHTRACE PHASES 0 THROUGH 6 PIPELINE VERIFIED")
        print("===========================================================")
        print(f"Claim Investigated: {dossier['input_claim']}")
        print(f"Verdict: {dossier['overall_verdict'].upper()} (Confidence: {dossier['overall_confidence']:.2f})")
        print(f"Clusters Formed: {len(dossier['clusters'])}")
        print(f"Attribution Summary: {dossier['attribution']['summary']}")
        if dossier.get("patient_zero"):
            print(f"Patient Zero Origin: @{dossier['patient_zero']['handle']} on {dossier['patient_zero']['platform']}")
        print(f"Timeline Events: {len(dossier['timeline'])}")
        print("===========================================================\n")

if __name__ == "__main__":
    unittest.main()
