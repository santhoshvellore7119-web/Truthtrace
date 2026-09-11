from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
import hashlib
import uuid

class Claim(BaseModel):
    """
    Canonical Claim object across the entire TruthTrace pipeline.
    Every agent downstream reads and writes this shape.
    """
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    text: str = Field(..., min_length=1)
    extracted_entities: List[str] = Field(default_factory=list)
    source_url: Optional[str] = None
    timestamp: Optional[datetime] = None
    embedding: Optional[List[float]] = None
    cluster_id: Optional[str] = None
    source_platform: Optional[str] = None  # GDELT, NewsAPI, GoogleFactCheck, Reddit, Telegram, YouTube, etc.
    credibility_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TimelineEvent(BaseModel):
    """
    An event along the provenance timeline sorted in ascending chronological order.
    """
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    source: str = Field(..., min_length=1)
    timestamp: Optional[datetime] = None
    url: Optional[str] = None
    title: Optional[str] = None
    snippet: Optional[str] = None
    earliest_cdx_timestamp: Optional[datetime] = None
    is_patient_zero_candidate: bool = False
    cluster_id: Optional[str] = None
    credibility_tier: Optional[Literal["registry", "primary", "mainstream", "unverified", "known_low_credibility"]] = "unverified"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ClaimCluster(BaseModel):
    """
    Semantic cluster of near-duplicate and reworded claim variants.
    """
    cluster_id: str
    label: str
    claim_count: int = 0
    earliest_timestamp: Optional[datetime] = None
    patient_zero_source: Optional[str] = None
    claims: List[Claim] = Field(default_factory=list)

class DomainAttribution(BaseModel):
    """
    WHOIS domain metadata, registration age, and MBFC / IFCN registry ratings.
    """
    domain: str
    registration_date: Optional[datetime] = None
    domain_age_days: Optional[int] = None
    is_freshly_registered: bool = False  # True if < 90 days old
    mbfc_rating: Optional[str] = None  # e.g. "Fact-Checked Registry", "Conspiracy/Pseudomedicine", "Mainstream"
    is_ifcn_signatory: bool = False
    credibility_tier: str = "unverified"

class CoordinationSignal(BaseModel):
    """
    Account coordination signal detecting synchronized posting across accounts.
    """
    detected: bool = False
    coordination_score: float = 0.0  # 0.0 - 1.0
    account_count: int = 0
    time_window_minutes: int = 0
    matched_phrase: str = ""
    details: str = ""

class AttributionReport(BaseModel):
    """
    Aggregated organizational and network attribution report.
    """
    domains: List[DomainAttribution] = Field(default_factory=list)
    coordination: Optional[CoordinationSignal] = None
    summary: str = ""

class VideoForensics(BaseModel):
    """
    Forensic analysis of video content (YouTube metadata, Whisper transcript, keyframe recycling).
    """
    video_url: Optional[str] = None
    channel_name: Optional[str] = None
    published_at: Optional[datetime] = None
    view_count: Optional[int] = None
    transcript_excerpt: Optional[str] = None
    is_recycled_footage: bool = False
    recycling_confidence: float = 0.0
    keyframe_matches: List[str] = Field(default_factory=list)
    verdict_notes: str = ""

class Source(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    url: str
    domain: str
    fetched_at: datetime = Field(default_factory=datetime.now)
    snapshot_url: Optional[str] = None
    credibility_tier: Literal["registry", "primary", "mainstream", "unverified", "known_low_credibility"] = "unverified"
    content_hash: str = ""

    @validator('content_hash', pre=True, always=True)
    def set_content_hash(cls, v, values):
        if not v:
            url = values.get('url', '')
            return hashlib.sha256(url.encode()).hexdigest()
        return v

class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    source: Source
    excerpt: str = Field(..., min_length=1)
    retrieved_via: str
    confidence: float = Field(..., ge=0.0, le=1.0)

class SubClaim(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    text: str = Field(..., min_length=1)
    atomic: bool = True
    verdict: Literal["true", "false", "misleading", "unverified", "satire", "opinion"]
    verdict_confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: List[Evidence] = Field(default_factory=list)
    unverified_inference: bool = False


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
    prior_flagged_claims: int = 0
    account_age_days: Optional[int] = None
    coordination_score: Optional[float] = None

class SourceTweak(BaseModel):
    original_text: str = Field(..., min_length=1)
    altered_text: str = Field(..., min_length=1)
    tweak_type: Literal["mistranslation", "out_of_context", "selective_edit", "fabrication", "satire_stripped"]
    diff_span: tuple[int, int]

class NarrativeProfile(BaseModel):
    core_narrative: str = Field(..., min_length=1)
    emotional_hooks: List[str] = Field(default_factory=list)
    target_demographic: str = Field(..., min_length=1)
    plausible_intent: str = Field(..., min_length=1)
    coordinated_cluster_id: Optional[str] = None

class RedTeamAudit(BaseModel):
    flags: List[str] = Field(default_factory=list)
    source_credibility_concerns: List[str] = Field(default_factory=list)
    confidence_adjustment: float = Field(default=0.0, ge=-1.0, le=1.0)

class Dossier(BaseModel):
    id: str = Field(default_factory=lambda: hashlib.sha256(datetime.now().isoformat().encode()).hexdigest()[:16])
    input_claim: str = Field(..., min_length=1)
    language: str = Field(default="en", min_length=2)
    sub_claims: List[SubClaim] = Field(default_factory=list)
    patient_zero: Optional[OriginatingAccount] = None
    timeline: List[TimelineEvent] = Field(default_factory=list)
    claims_corpus: List[Claim] = Field(default_factory=list)
    clusters: List[ClaimCluster] = Field(default_factory=list)
    attribution: Optional[AttributionReport] = None
    video_forensics: Optional[VideoForensics] = None
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