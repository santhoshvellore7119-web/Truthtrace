"""
Test suite for TruthTrace Phase 0 and Phase 1 implementation.
Validates schemas, vector store clustering, wayback agent, osint hunter, and end-to-end synthesis.
"""
import asyncio
import sys
import os
import unittest
from datetime import datetime

# Set up python path for backend imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from models.schemas import Claim, TimelineEvent, Dossier, Source, Evidence, SubClaim
from utils.vector_store import VectorStore, compute_embedding, cosine_similarity
from agents.wayback_agent import WaybackAgent
from agents.osint_hunter import OSINTHunterAgent
from agents.fact_checker import FactCheckAgent
from agents.synthesizer import SynthesizerAgent
from agents.claim_extractor import ClaimExtractorAgent

class TestTruthTracePhase0And1(unittest.TestCase):

    def test_claim_and_timeline_schemas(self):
        """Verify Claim and TimelineEvent schema creation and validation."""
        c = Claim(
            text="Drinking salt water cures aging",
            extracted_entities=["salt water", "aging"],
            source_url="https://example.com/article",
            source_platform="GDELT",
            timestamp=datetime(2023, 5, 10, 14, 0, 0)
        )
        self.assertEqual(c.text, "Drinking salt water cures aging")
        self.assertTrue(len(c.id) > 0)
        self.assertIsNotNone(c.timestamp)
        self.assertEqual(c.source_platform, "GDELT")

        ev = TimelineEvent(
            source="Reuters",
            timestamp=datetime(2023, 5, 10, 14, 0, 0),
            url="https://reuters.com/factcheck",
            title="Fact Check: Salt water does not cure aging",
            credibility_tier="mainstream"
        )
        self.assertEqual(ev.source, "Reuters")
        self.assertFalse(ev.is_patient_zero_candidate)

    def test_vector_store_and_clustering(self):
        """Verify VectorStore embeddings and claim clustering."""
        vs = VectorStore(collection_name="test_claims")
        c1 = Claim(text="Drinking salt water reverses human biological aging", timestamp=datetime(2023, 1, 1))
        c2 = Claim(text="Salt water consumption cures aging according to study", timestamp=datetime(2023, 1, 5))
        c3 = Claim(text="New Mars rover captures high resolution crater images", timestamp=datetime(2023, 2, 1))

        vs.add_claims([c1, c2, c3])
        
        # Test search
        results = vs.similarity_search("salt water aging cure", top_k=2)
        self.assertGreaterEqual(len(results), 1)

        # Test clustering
        clusters = vs.cluster_claims(similarity_threshold=0.3)
        self.assertGreaterEqual(len(clusters), 1)

    def test_async_agents_and_pipeline(self):
        """Run all async tests in event loop."""
        asyncio.run(self._run_async_tests())

    async def _run_async_tests(self):
        # 1. Test Wayback Agent
        wayback_agent = WaybackAgent()
        res = await wayback_agent.execute({"urls": ["https://www.google.com", "https://invalid-non-existent-domain-12345.xyz"]})
        self.assertTrue(res.success)
        self.assertIn("snapshots", res.data)
        self.assertIn("https://www.google.com", res.data["snapshots"])

        # 2. Test OSINT Hunter
        osint_agent = OSINTHunterAgent()
        res = await osint_agent.execute({"claims": ["Drinking salt water reverses aging"]})
        self.assertTrue(res.success)
        self.assertIn("provenance", res.data)
        self.assertIsInstance(res.data["provenance"], list)

        # 3. Test Fact Checker
        fc_agent = FactCheckAgent()
        res = await fc_agent.execute({"claims": ["Drinking salt water reverses aging"]})
        self.assertTrue(res.success)
        self.assertIn("fact_check_results", res.data)
        self.assertIsInstance(res.data["fact_check_results"], list)

        # 4. Test Synthesizer and timeline
        synthesizer = SynthesizerAgent()
        provenance = [
            {
                "claim": "Drinking salt water reverses aging",
                "platform": "BlogSpot",
                "url": "https://blogspot.com/early_claim",
                "timestamp": "2023-01-01T10:00:00Z",
                "title": "Miracle Salt Water Cure",
                "credibility_tier": "unverified"
            },
            {
                "claim": "Drinking salt water reverses aging",
                "platform": "Reuters Fact Check",
                "url": "https://reuters.com/debunk",
                "timestamp": "2023-01-10T12:00:00Z",
                "title": "Debunked: Salt water cure",
                "credibility_tier": "mainstream"
            }
        ]
        wayback_snapshots = {
            "https://blogspot.com/early_claim": {
                "earliest_timestamp": "2023-01-01T10:00:00Z",
                "earliest_snapshot_url": "https://web.archive.org/web/20230101100000/https://blogspot.com/early_claim"
            }
        }
        fact_check_results = [
            {
                "claim": "Drinking salt water reverses aging",
                "verdict": "false",
                "confidence": 0.90,
                "sources": [{"name": "Reuters", "url": "https://reuters.com/debunk", "rating": "False"}]
            }
        ]

        synth_res = await synthesizer.execute({
            "claims": ["Drinking salt water reverses aging"],
            "provenance": provenance,
            "wayback_snapshots": wayback_snapshots,
            "fact_check_results": fact_check_results
        })
        self.assertTrue(synth_res.success)
        dossier = synth_res.data
        self.assertEqual(dossier["input_claim"], "Drinking salt water reverses aging")
        self.assertEqual(dossier["overall_verdict"], "false")
        self.assertEqual(len(dossier["timeline"]), 2)
        self.assertEqual(dossier["timeline"][0]["source"], "BlogSpot")
        self.assertTrue(dossier["timeline"][0]["is_patient_zero_candidate"])
        self.assertIsNotNone(dossier["patient_zero"])
        self.assertEqual(dossier["patient_zero"]["platform"], "BlogSpot")

        # 5. Full end-to-end pipeline run
        claim_extractor = ClaimExtractorAgent()
        ext_res = await claim_extractor.execute({"claim": "Government plans to ban coffee next month."})
        self.assertTrue(ext_res.success)
        claims = ext_res.data["claims"]

        osint_res = await osint_agent.execute({"claims": claims})
        self.assertTrue(osint_res.success)
        prov = osint_res.data["provenance"]

        urls = [p.get("url") for p in prov if p.get("url")]
        wb_res = await wayback_agent.execute({"urls": urls, "provenance": prov})
        snapshots = wb_res.data.get("snapshots", {})

        fc_res = await fc_agent.execute({"claims": claims, "provenance": prov})
        self.assertTrue(fc_res.success)

        synth_pipeline_res = await synthesizer.execute({
            "claims": claims,
            "provenance": prov,
            "wayback_snapshots": snapshots,
            "fact_check_results": fc_res.data.get("fact_check_results", [])
        })
        self.assertTrue(synth_pipeline_res.success)
        full_dossier = synth_pipeline_res.data
        self.assertIn("timeline", full_dossier)
        self.assertIn("overall_verdict", full_dossier)
        self.assertIn("overall_confidence", full_dossier)

        print("\n==========================================")
        print("  TRUTHTRACE PHASE 0 & 1 TEST RESULTS")
        print("==========================================")
        print(f"Verdict: {full_dossier['overall_verdict'].upper()} (Confidence: {full_dossier['overall_confidence']:.2f})")
        print(f"Timeline Events Discovered: {len(full_dossier['timeline'])}")
        for idx, ev in enumerate(full_dossier['timeline'][:3]):
            print(f"  [{idx+1}] {ev.get('source')} -> {ev.get('title')[:45]}... (TS: {ev.get('timestamp')})")
        if full_dossier.get("patient_zero"):
            print(f"Candidate Patient Zero: {full_dossier['patient_zero']}")
        print("==========================================\n")

if __name__ == "__main__":
    unittest.main()
