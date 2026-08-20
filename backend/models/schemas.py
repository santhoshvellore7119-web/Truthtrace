from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime
import hashlib

class Source(BaseModel):
    id: str = Field(default_factory=lambda: hashlib.sha256(datetime.now().isoformat().encode()).hexdigest()[:16])
    url: str
    domain: str
    fetched_at: datetime = Field(default_factory=datetime.now)
    snapshot_url: Optional[str] = None  # Wayback/archive.today permalink, captured at fetch time
    credibility_tier: Literal["registry", "primary", "mainstream", "unverified", "known_low_credibility"]
    content_hash: str  # for detecting later edits to the same URL

    @validator('content_hash', always=True)
    def set_content_hash(cls, v, values):
        # In a real implementation, this would be computed from the content.
        # For now, we'll use a placeholder.
        if not v:
            return hashlib.sha256(values.get('url', '').encode()).hexdigest()
        return v

class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: hashlib.sha256(datetime.now().isoformat().encode()).hexdigest()[:16])
    source: Source
    excerpt: str = Field(..., min_length=1)  # the exact supporting text, verbatim, with position offsets
    retrieved_via: str  # which scraper/tool found this
    confidence: float = Field(..., ge=0.0, le=1.0)  # 0-1, how well this excerpt supports the linked claim

class SubClaim(BaseModel):
    id: str = Field(default_factory=lambda: hashlib.sha256(datetime.now().isoformat().encode()).hexdigest()[:16])
    text: str = Field(..., min_length=1)
    atomic: bool = True  # true if this is a single testable assertion
    verdict: Literal["true", "false", "misleading", "unverified", "satire", "opinion"]
    verdict_confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: List[Evidence] = Field(default_factory=list)
    unverified_inference: bool = False  # true if this came from LLM reasoning without direct evidence

    @validator('evidence')
    def check_evidence_if_not_unverified(cls, v, values):
        if values.get('verdict') != "unverified" and not v:
            raise ValueError("SubClaim must have at least one evidence unless verdict is 'unverified'")
        return v

class OriginatingAccount(BaseModel):
    platform: str
    handle: str
    first_seen_at: Optional[datetime] = None
    follower_count: Optional[int] = None
    prior_flagged_claims: int = 0  # pulled from graph_intel — repeat-offender signal

class SourceTweak(BaseModel):
    original_text: str = Field(..., min_length=1)
    altered_text: str = Field(..., min_length=1)
    tweak_type: Literal["mistranslation", "out_of_context", "selective_edit", "fabrication", "satire_stripped"]
    diff_span: tuple[int, int]  # start and end indices in the altered text

class NarrativeProfile(BaseModel):
    core_narrative: str = Field(..., min_length=1)
    emotional_hooks: List[str] = Field(default_factory=list)
    target_demographic: str = Field(..., min_length=1)
    plausible_intent: str = Field(..., min_length=1)
    coordinated_cluster_id: Optional[str] = None  # links to graph_intel clustering output

class RedTeamAudit(BaseModel):
    flags: List[str] = Field(default_factory=list)  # e.g. "narrative profiler may be pattern-matching on tone, not substance"
    source_credibility_concerns: List[str] = Field(default_factory=list)
    confidence_adjustment: float = Field(default=0.0, ge=-1.0, le=1.0)  # applied to final dossier confidence

class Dossier(BaseModel):
    id: str = Field(default_factory=lambda: hashlib.sha256(datetime.now().isoformat().encode()).hexdigest()[:16])
    input_claim: str = Field(..., min_length=1)
    language: str = Field(..., min_length=2)  # e.g., "en", "ta"
    sub_claims: List[SubClaim] = Field(default_factory=list)
    patient_zero: Optional[OriginatingAccount] = None
    source_tweaks: List[SourceTweak] = Field(default_factory=list)
    narrative: NarrativeProfile
    red_team_audit: RedTeamAudit = Field(default_factory=RedTeamAudit)
    overall_verdict: Literal["true", "false", "misleading", "unverified", "satire", "opinion"]
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    generated_at: datetime = Field(default_factory=datetime.now)

    @validator('sub_claims')
    def check_subclaims_evidence(cls, v):
        for subclaim in v:
            if subclaim.verdict != "unverified" and not subclaim.evidence:
                raise ValueError(f"SubClaim '{subclaim.text}' must have evidence unless verdict is 'unverified'")
        return v