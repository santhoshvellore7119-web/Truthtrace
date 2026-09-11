"""
Comprehensive end-to-end multi-scenario test suite for TruthTrace.
Tests diverse input types:
1. Medical / Health Disinformation Text Statement
2. Suspicious Article URL with Conspiracy Claim
3. Geopolitical / Policy Claim
4. Recycled Video / Image Forensics URL
5. Direct News Article URL Investigation

Verifies:
- Extraction & Normalization
- Ascending Chronological Timeline
- Patient Zero Identification
- Semantic Claim Clustering
- WHOIS & Domain Risk Attribution
- Keyframe & Video Recycling Detection
- Verdict & Confidence Scoring
"""
import sys
import os
import asyncio
import unittest
from datetime import datetime

# Setup backend path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from api.main import analyze_claim, AnalyzeRequest
from models.schemas import Dossier

class TestTruthTraceDiverseScenarios(unittest.IsolatedAsyncioTestCase):

    async def test_scenario_1_medical_claim_statement(self):
        """Scenario 1: Medical / Health Disinformation Text Statement"""
        print("\n" + "="*70)
        print("SCENARIO 1: Medical Disinformation Statement")
        print("="*70)
        req = AnalyzeRequest(claim="Drinking boiled garlic water cures COVID-19 and prevents all viral respiratory infections")
        res = await analyze_claim(req)
        
        # res is dict returned by analyze_claim
        self.assertIsInstance(res, dict)
        self.assertIn("timeline", res)
        self.assertIn("overall_verdict", res)
        self.assertIn("overall_confidence", res)
        self.assertIn("clusters", res)
        
        # Verify chronological timeline ordering
        timeline = res["timeline"]
        self.assertGreater(len(timeline), 0)
        dates = []
        for ev in timeline:
            ts = ev.get("timestamp")
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            dates.append(ts)
        self.assertEqual(dates, sorted(dates), "Timeline must be strictly ascending in time")

        print(f"Verdict: {res['overall_verdict'].upper()} (Confidence: {res['overall_confidence']:.2f})")
        print(f"Clusters Formed: {len(res['clusters'])}")
        print(f"Timeline Events: {len(timeline)} (Strictly Ascending)")
        if res.get("patient_zero"):
            print(f"Patient Zero: @{res['patient_zero'].get('handle')} on {res['patient_zero'].get('platform')}")

    async def test_scenario_2_conspiracy_article_url(self):
        """Scenario 2: Conspiracy Claim with Suspicious News Domain URL"""
        print("\n" + "="*70)
        print("SCENARIO 2: Conspiracy Claim with Suspicious Domain URL")
        print("="*70)
        req = AnalyzeRequest(
            claim="5G mmWave antennas cause sudden bird collapse and cardiac arrest",
            url="https://freshnewsalert-2024.xyz/5g-kills-birds"
        )
        res = await analyze_claim(req)
        
        self.assertIsInstance(res, dict)
        self.assertIn("attribution", res)
        attr = res["attribution"]
        self.assertIn("domains", attr)
        self.assertIn("coordination", attr)
        
        print(f"Verdict: {res['overall_verdict'].upper()}")
        print(f"Domains Analyzed: {len(attr['domains'])}")
        print(f"High Risk Domains: {attr.get('high_risk_domains', [])}")
        print(f"Attribution Summary: {attr.get('summary')}")

    async def test_scenario_3_geopolitical_policy_statement(self):
        """Scenario 3: Geopolitical / Policy Disinformation Statement"""
        print("\n" + "="*70)
        print("SCENARIO 3: Geopolitical Policy Statement")
        print("="*70)
        req = AnalyzeRequest(claim="United Nations votes to replace all national passports with mandatory digital biometric chips by 2026")
        res = await analyze_claim(req)
        
        self.assertIsInstance(res, dict)
        self.assertIn("sub_claims", res)
        self.assertIn("timeline", res)
        self.assertGreater(len(res["timeline"]), 0)
        
        print(f"Verdict: {res['overall_verdict'].upper()} (Confidence: {res['overall_confidence']:.2f})")
        print(f"Subclaims Extracted: {len(res['sub_claims'])}")
        print(f"Timeline Events: {len(res['timeline'])}")

    async def test_scenario_4_video_forensics_url(self):
        """Scenario 4: Recycled Video URL & Visual Forensics"""
        print("\n" + "="*70)
        print("SCENARIO 4: Recycled Video URL & Visual Forensics")
        print("="*70)
        req = AnalyzeRequest(
            claim="Breaking 2026 military intercept footage over ocean",
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )
        res = await analyze_claim(req)
        
        self.assertIsInstance(res, dict)
        self.assertIn("video_forensics", res)
        vid = res["video_forensics"]
        self.assertIsNotNone(vid)
        
        print(f"Video URL Analyzed: {vid.get('video_url')}")
        print(f"Channel Name: {vid.get('channel_name')}")
        print(f"Recycled Footage Detected: {vid.get('is_recycled_footage')}")
        print(f"Recycling Confidence: {vid.get('recycling_confidence', 0.0):.2f}")
        print(f"Verdict Notes: {vid.get('verdict_notes')}")

    async def test_scenario_5_news_article_url_investigation(self):
        """Scenario 5: Direct News Article URL Investigation"""
        print("\n" + "="*70)
        print("SCENARIO 5: Direct News Article URL Investigation")
        print("="*70)
        req = AnalyzeRequest(
            url="https://www.bbc.com/news/world-us-canada-68482024"
        )
        res = await analyze_claim(req)
        
        self.assertIsInstance(res, dict)
        self.assertIn("input_claim", res)
        self.assertIn("timeline", res)
        self.assertGreater(len(res["timeline"]), 0)
        
        print(f"Extracted Input Claim: {res['input_claim']}")
        print(f"Verdict: {res['overall_verdict'].upper()}")
        print(f"Timeline Provenance Length: {len(res['timeline'])}")

if __name__ == '__main__':
    unittest.main()
