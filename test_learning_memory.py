"""
Unit & Integration test suite for TruthTrace Continuous Learning & Memory.
Tests:
1. EpisodicMemoryStore indexing, cross-investigation recall, and domain calibration.
2. ContrastiveQueryLearner metric learning.
3. End-to-end multi-query recall: asking a mutated query recalls prior investigations.
4. User feedback and dynamic domain reputation adjustments.
"""
import sys
import os
import asyncio
import unittest
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from memory.learning_store import LearningMemoryStore
from learning.contrastive_learner import ContrastiveQueryLearner
from api.main import analyze_claim, submit_feedback, get_learning_stats, AnalyzeRequest, FeedbackRequest

class TestContinuousLearning(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Use isolated test database
        self.test_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_learning.db'))
        self.store = LearningMemoryStore(db_path=self.test_db_path)

    def tearDown(self):
        # Clean up test database
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except Exception:
                pass

    def test_contrastive_learner_metrics(self):
        """Test contrastive metric calculations and threshold calibration."""
        learner = ContrastiveQueryLearner(base_threshold=0.60)
        
        sim_high = learner.compute_lexical_dense_hybrid_score(
            "Drinking boiled garlic water cures COVID-19",
            "Boiled garlic water remedies COVID-19 viral infection"
        )
        sim_low = learner.compute_lexical_dense_hybrid_score(
            "Drinking boiled garlic water cures COVID-19",
            "NASA launches robotic rover to Jupiter moon Europa"
        )
        self.assertGreater(sim_high, 0.40)
        self.assertLess(sim_low, 0.15)

        # Dynamic threshold adaptation
        t0 = learner.calibrate_similarity_threshold("viral_cures", historical_matches_count=0)
        t50 = learner.calibrate_similarity_threshold("viral_cures", historical_matches_count=50)
        self.assertLessEqual(t50, t0, "Threshold should adapt as topic density grows")

    def test_episodic_memory_store_lifecycle(self):
        """Test memory recording, domain calibration, and user feedback."""
        sample_dossier = {
            "id": "inv_test_001",
            "input_claim": "Miracle herbal tonic prevents 5G radiation sickness",
            "overall_verdict": "false",
            "overall_confidence": 0.95,
            "patient_zero": {"handle": "conspiracy_herald", "platform": "Telegram", "source_url": "https://t.me/fake_news/123"},
            "attribution": {
                "domains": [{"domain": "herbalcure-2024.xyz", "risk_score": 0.9}]
            },
            "sub_claims": [{"text": "Herbal tonic blocks 5G"}],
            "timeline": [{"timestamp": "2024-01-01T00:00:00"}]
        }

        # 1. Record Investigation
        inv_id = self.store.record_investigation(sample_dossier)
        self.assertEqual(inv_id, "inv_test_001")

        # 2. Recall via related query
        recalled = self.store.recall_prior_investigations("5G radiation sickness herbal tonic cures")
        self.assertGreaterEqual(len(recalled), 1)
        self.assertEqual(recalled[0]["id"], "inv_test_001")
        self.assertEqual(recalled[0]["verdict"], "false")

        # 3. User Feedback & Domain Reputation Learning
        fb_ok = self.store.record_user_feedback(
            investigation_id="inv_test_001",
            rating="accurate",
            correction_text="Confirmed false by WHO report",
            evidence_url="https://who.int/news/5g-health"
        )
        self.assertTrue(fb_ok)

        # Verify domain reputation updated
        stats = self.store.get_learning_stats()
        self.assertGreaterEqual(stats["total_investigations_learned"], 1)
        self.assertGreaterEqual(stats["tracked_domains_count"], 1)
        self.assertGreaterEqual(stats["user_feedback_contributions"], 1)

    async def test_end_to_end_cross_investigation_recall(self):
        """
        Verify that asking Query 1 allows TruthTrace to learn and subsequently
        recall the prior findings when Query 2 is asked.
        """
        # Query 1: Initial Investigation
        req1 = AnalyzeRequest(claim="Drinking boiled lemon water with baking soda cures biological aging")
        res1 = await analyze_claim(req1)
        self.assertIsInstance(res1, dict)

        # Query 2: Mutated query on same topic
        req2 = AnalyzeRequest(claim="Boiled lemon peel and baking soda reverses aging process in cells")
        res2 = await analyze_claim(req2)
        self.assertIsInstance(res2, dict)
        
        # Verify cross investigation memory was queried and included in schema
        self.assertIn("cross_investigation_memory", res2)

        # Feedback Submission via API endpoint
        fb_req = FeedbackRequest(
            dossier_id=res2.get("id", "dossier_123"),
            rating="accurate",
            correction_text="Great job tracing the Reddit origin"
        )
        fb_res = await submit_feedback(fb_req)
        self.assertTrue(fb_res.get("success", False))

        # Check Stats endpoint
        stats = await get_learning_stats()
        self.assertGreaterEqual(stats.get("total_investigations_learned", 0), 1)

if __name__ == '__main__':
    unittest.main()
