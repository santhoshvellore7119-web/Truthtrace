#!/usr/bin/env python
"""
Test script to verify evidence validation in SubClaim model.
"""
from backend.models.schemas import SubClaim, Evidence, Source
from pydantic import ValidationError
import datetime

def test_evidence_validation():
    print("Testing evidence validation in SubClaim model...")

    # Test 1: SubClaim with verdict "unverified" should allow empty evidence
    try:
        unverified_claim = SubClaim(
            text="This is an unverified claim",
            verdict="unverified",
            verdict_confidence=0.5,
            evidence=[]
        )
        print("[PASS] Unverified claim with empty evidence")
    except ValidationError as e:
        print(f"[FAIL] Unverified claim with empty evidence: {e}")
        return False

    # Test 2: SubClaim with verdict "true" should require evidence
    try:
        true_claim_no_evidence = SubClaim(
            text="This is a true claim",
            verdict="true",
            verdict_confidence=0.9,
            evidence=[]
        )
        print("[FAIL] True claim without evidence: should have raised ValidationError")
        return False
    except ValidationError as e:
        if "SubClaim must have at least one evidence unless verdict is 'unverified'" in str(e):
            print("[PASS] True claim without evidence correctly rejected")
        else:
            print(f"[FAIL] True claim without evidence: Wrong error: {e}")
            return False

    # Test 3: SubClaim with verdict "false" should require evidence
    try:
        false_claim_no_evidence = SubClaim(
            text="This is a false claim",
            verdict="false",
            verdict_confidence=0.8,
            evidence=[]
        )
        print("[FAIL] False claim without evidence: should have raised ValidationError")
        return False
    except ValidationError as e:
        if "SubClaim must have at least one evidence unless verdict is 'unverified'" in str(e):
            print("[PASS] False claim without evidence correctly rejected")
        else:
            print(f"[FAIL] False claim without evidence: Wrong error: {e}")
            return False

    # Test 4: SubClaim with verdict "misleading" should require evidence
    try:
        misleading_claim_no_evidence = SubClaim(
            text="This is a misleading claim",
            verdict="misleading",
            verdict_confidence=0.3,
            evidence=[]
        )
        print("[FAIL] Misleading claim without evidence: should have raised ValidationError")
        return False
    except ValidationError as e:
        if "SubClaim must have at least one evidence unless verdict is 'unverified'" in str(e):
            print("[PASS] Misleading claim without evidence correctly rejected")
        else:
            print(f"[FAIL] Misleading claim without evidence: Wrong error: {e}")
            return False

    # Test 5: SubClaim with proper evidence should be accepted
    try:
        # Create a mock source and evidence
        source = Source(
            url="https://example.com/fact-check",
            domain="example.com",
            credibility_tier="unverified",
            content_hash="abc123"
        )
        evidence = Evidence(
            source=source,
            excerpt="This is an excerpt from the source",
            retrieved_via="fact_check",
            confidence=0.8
        )

        verified_claim = SubClaim(
            text="This is a verified claim",
            verdict="true",
            verdict_confidence=0.9,
            evidence=[evidence]
        )
        print("[PASS] Verified claim with evidence")
    except ValidationError as e:
        print(f"[FAIL] Verified claim with evidence: {e}")
        return False

    print("\nAll evidence validation tests passed!")
    return True

if __name__ == "__main__":
    success = test_evidence_validation()
    exit(0 if success else 1)