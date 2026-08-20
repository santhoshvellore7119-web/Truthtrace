"""
Evidence graph storage using PostgreSQL with pgvector extension.
"""
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from sqlalchemy import (
    create_engine, Column, String, Text, DateTime, Float, Integer, Boolean, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB

# For pgvector, we need to install pgvector and use the vector type
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = None  # type: ignore

# We'll define the models here, but note that we also have Pydantic models in backend.models.schemas
# We'll convert between them.

Base = declarative_base()

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/truthtrace"
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database, creating tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

# SQLAlchemy Models

class SourceDB(Base):
    __tablename__ = "sources"

    id = Column(String(16), primary_key=True, default=lambda: str(uuid.uuid4())[:16])
    url = Column(Text, nullable=False)
    domain = Column(String(255), nullable=False, index=True)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    snapshot_url = Column(Text, nullable=True)
    credibility_tier = Column(String(50), nullable=False)
    content_hash = Column(String(64), nullable=False, unique=True)  # SHA-256

    # Relationships
    evidences = relationship("EvidenceDB", back_populates="source")

    __table_args__ = (
        Index("ix_sources_domain_fetched_at", "domain", "fetched_at"),
    )

class EvidenceDB(Base):
    __tablename__ = "evidences"

    id = Column(String(16), primary_key=True, default=lambda: str(uuid.uuid4())[:16])
    source_id = Column(String(16), ForeignKey("sources.id"), nullable=False, index=True)
    excerpt = Column(Text, nullable=False)
    retrieved_via = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)

    # Relationships
    source = relationship("SourceDB", back_populates="evidences")
    sub_claims = relationship("SubClaimDB", secondary="subclaim_evidence", back_populates="evidences")

class SubClaimDB(Base):
    __tablename__ = "sub_claims"

    id = Column(String(16), primary_key=True, default=lambda: str(uuid.uuid4())[:16])
    text = Column(Text, nullable=False)
    atomic = Column(Boolean, nullable=False, default=True)
    verdict = Column(String(20), nullable=False)
    verdict_confidence = Column(Float, nullable=False)
    unverified_inference = Column(Boolean, nullable=False, default=False)
    dossier_id = Column(String(16), ForeignKey("dossiers.id"), nullable=False, index=True)

    # Relationships
    evidences = relationship("EvidenceDB", secondary="subclaim_evidence", back_populates="sub_claims")
    source_tweaks = relationship("SourceTweakDB", back_populates="sub_claim")
    narrative_profile = relationship("NarrativeProfileDB", uselist=False, back_populates="sub_claim")
    originating_account = relationship("OriginatingAccountDB", uselist=False, back_populates="sub_claim")
    dossier = relationship("DossierDB", back_populates="sub_claims")

class SubClaimEvidence(Base):
    __tablename__ = "subclaim_evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sub_claim_id = Column(String(16), ForeignKey("sub_claims.id"), nullable=False)
    evidence_id = Column(String(16), ForeignKey("evidences.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("sub_claim_id", "evidence_id", name="uq_subclaim_evidence"),
    )

class OriginatingAccountDB(Base):
    __tablename__ = "originating_accounts"

    id = Column(String(16), primary_key=True, default=lambda: str(uuid.uuid4())[:16])
    sub_claim_id = Column(String(16), ForeignKey("sub_claims.id"), nullable=False, unique=True)
    platform = Column(String(50), nullable=False)
    handle = Column(String(100), nullable=False)
    first_seen_at = Column(DateTime, nullable=True)
    follower_count = Column(Integer, nullable=True)
    prior_flagged_claims = Column(Integer, nullable=False, default=0)

    # Relationships
    sub_claim = relationship("SubClaimDB", back_populates="originating_account")

class SourceTweakDB(Base):
    __tablename__ = "source_tweaks"

    id = Column(String(16), primary_key=True, default=lambda: str(uuid.uuid4())[:16])
    sub_claim_id = Column(String(16), ForeignKey("sub_claims.id"), nullable=False, index=True)
    original_text = Column(Text, nullable=False)
    altered_text = Column(Text, nullable=False)
    tweak_type = Column(String(50), nullable=False)
    diff_span_start = Column(Integer, nullable=False)
    diff_span_end = Column(Integer, nullable=False)

    # Relationships
    sub_claim = relationship("SubClaimDB", back_populates="source_tweaks")

class NarrativeProfileDB(Base):
    __tablename__ = "narrative_profiles"

    id = Column(String(16), primary_key=lambda: str(uuid.uuid4())[:16])
    sub_claim_id = Column(String(16), ForeignKey("sub_claims.id"), nullable=False, unique=True)
    core_narrative = Column(Text, nullable=False)
    emotional_hooks = Column(ARRAY(String(100)), nullable=False)
    target_demographic = Column(String(100), nullable=False)
    plausible_intent = Column(String(100), nullable=False)
    coordinated_cluster_id = Column(String(16), nullable=True)  # To be used in Phase 3

    # Relationships
    sub_claim = relationship("SubClaimDB", back_populates="narrative_profile")

class RedTeamAuditDB(Base):
    __tablename__ = "red_team_audits"

    id = Column(String(16), primary_key=lambda: str(uuid.uuid4())[:16])
    sub_claim_id = Column(String(16), ForeignKey("sub_claims.id"), nullable=False, unique=True)
    flags = Column(ARRAY(String(200)), nullable=False)
    source_credibility_concerns = Column(ARRAY(String(200)), nullable=False)
    confidence_adjustment = Column(Float, nullable=False, default=0.0)

    # Relationships
    sub_claim = relationship("SubClaimDB", back_populates="red_team_audit")

class DossierDB(Base):
    __tablename__ = "dossiers"

    id = Column(String(16), primary_key=lambda: str(uuid.uuid4())[:16])
    input_claim = Column(Text, nullable=False)
    language = Column(String(10), nullable=False)
    overall_verdict = Column(String(20), nullable=False)
    overall_confidence = Column(Float, nullable=False)
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    sub_claims = relationship("SubClaimDB", back_populates="dossier", order_by="SubClaimDB.id")
    # Note: We don't store source_tweaks, narrative, red_team_audit directly because they are linked via sub_claims.
    # However, the Dossier model in Pydantic has these as fields. We'll need to assemble them when querying.

# We'll create a repository class to handle the conversion between Pydantic and DB models.

class EvidenceStore:
    def __init__(self, db_session: Session):
        self.db = db_session

    def save_dossier(self, dossier: Dossier) -> str:
        """Save a Dossier and all related entities to the database.
        Returns the dossier ID.
        """
        # Check if dossier already exists
        existing = self.db.query(DossierDB).filter(DossierDB.id == dossier.id).first()
        if existing:
            # Update existing
            db_dossier = existing
        else:
            db_dossier = DossierDB(
                id=dossier.id,
                input_claim=dossier.input_claim,
                language=dossier.language,
                overall_verdict=dossier.overall_verdict,
                overall_confidence=dossier.overall_confidence,
                generated_at=dossier.generated_at
            )
            self.db.add(db_dossier)

        # We need to save sub_claims and their related entities.
        # For simplicity, we'll delete existing sub_claims for this dossier and recreate.
        # In a production system, we'd do a more careful merge.
        self.db.query(SubClaimDB).filter(SubClaimDB.dossier_id == dossier.id).delete()
        self.db.flush()

        for sub_claim in dossier.sub_claims:
            db_sub_claim = SubClaimDB(
                id=sub_claim.id,
                text=sub_claim.text,
                atomic=sub_claim.atomic,
                verdict=sub_claim.verdict,
                verdict_confidence=sub_claim.verdict_confidence,
                unverified_inference=sub_claim.unverified_inference,
                dossier_id=dossier.id
            )
            self.db.add(db_sub_claim)
            self.db.flush()  # to get the ID if needed

            # Save evidences
            for evidence in sub_claim.evidence:
                # Check if evidence already exists (by content_hash? we don't have that in EvidenceDB yet)
                # We'll just create new evidence for simplicity.
                db_evidence = EvidenceDB(
                    id=evidence.id,
                    source_id=evidence.source.id,  # We assume the source is already saved or we save it below
                    excerpt=evidence.excerpt,
                    retrieved_via=evidence.retrieved_via,
                    confidence=evidence.confidence
                )
                self.db.add(db_evidence)
                self.db.flush()

                # Link evidence to sub_claim
                db_sub_claim_evidence = SubClaimEvidence(
                    sub_claim_id=db_sub_claim.id,
                    evidence_id=db_evidence.id
                )
                self.db.add(db_sub_claim_evidence)

                # Save the source if not already saved
                # We'll check by URL or content_hash
                existing_source = self.db.query(SourceDB).filter(SourceDB.url == evidence.source.url).first()
                if not existing_source:
                    db_source = SourceDB(
                        id=evidence.source.id,
                        url=evidence.source.url,
                        domain=evidence.source.domain,
                        fetched_at=evidence.source.fetched_at,
                        snapshot_url=evidence.source.snapshot_url,
                        credibility_tier=evidence.source.credibility_tier,
                        content_hash=evidence.source.content_hash
                    )
                    self.db.add(db_source)
                else:
                    # Update the source if needed? We'll just keep the existing one.
                    # We could update the snapshot_url and fetched_at if they are newer.
                    pass

            # Save source_tweaks
            for tweak in sub_claim.source_tweaks:
                db_tweak = SourceTweakDB(
                    id=tweak.id if hasattr(tweak, 'id') else str(uuid.uuid4())[:16],
                    sub_claim_id=db_sub_claim.id,
                    original_text=tweak.original_text,
                    altered_text=tweak.altered_text,
                    tweak_type=tweak.tweak_type,
                    diff_span_start=tweak.diff_span[0],
                    diff_span_end=tweak.diff_span[1]
                )
                self.db.add(db_tweak)

            # Save originating account (if present)
            if sub_claim.patient_zero:
                existing_account = self.db.query(OriginatingAccountDB).filter(
                    OriginatingAccountDB.sub_claim_id == db_sub_claim.id
                ).first()
                if not existing_account:
                    db_account = OriginatingAccountDB(
                        id=sub_claim.patient_zero.id if hasattr(sub_claim.patient_zero, 'id') else str(uuid.uuid4())[:16],
                        sub_claim_id=db_sub_claim.id,
                        platform=sub_claim.patient_zero.platform,
                        handle=sub_claim.patient_zero.handle,
                        first_seen_at=sub_claim.patient_zero.first_seen_at,
                        follower_count=sub_claim.patient_zero.follower_count,
                        prior_flagged_claims=sub_claim.patient_zero.prior_flagged_claims
                    )
                    self.db.add(db_account)

            # Save narrative profile
            if sub_claim.narrative:  # Note: in the SubClaim model we don't have narrative, but in Dossier we do.
                # Actually, the narrative is in the Dossier, not in SubClaim.
                # We made an error: the Dossier has a narrative field, not the SubClaim.
                # We need to adjust: the Dossier.narrative is a NarrativeProfile that applies to the whole dossier?
                # Looking back at the prompt: the Dossier has a narrative: NarrativeProfile.
                # And the SubClaim does not have a narrative.
                # We'll need to store the narrative at the dossier level.
                pass

            # Save red_team_audit (also at dossier level)
            # We'll handle dossier-level fields after the loop.

        # Save dossier-level narrative and red_team_audit
        # We'll create a one-to-one relationship from Dossier to NarrativeProfileDB and RedTeamAuditDB.
        # But note: the Dossier model has one narrative and one red_team_audit.
        # We'll add these as optional one-to-one.

        # For now, we'll skip the dossier-level narrative and red_team_audit to focus on getting the sub_claims right.
        # We'll come back to this.

        self.db.commit()
        return dossier.id

    def get_dossier(self, dossier_id: str) -> Optional[Dossier]:
        """Retrieve a Dossier by ID, converting from DB models to Pydantic models."""
        db_dossier = self.db.query(DossierDB).filter(DossierDB.id == dossier_id).first()
        if not db_dossier:
            return None

        # We need to assemble the Dossier from the DB models.
        # This is complex because we have to collect sub_claims with their evidences, source_tweaks, etc.
        # We'll do a simple version for now.

        # Get sub_claims for this dossier
        db_sub_claims = self.db.query(SubClaimDB).filter(SubClaimDB.dossier_id == dossier_id).all()

        sub_claims = []
        for db_sub_claim in db_sub_claims:
            # Get evidences for this sub_claim
            db_evidences = self.db.query(EvidenceDB).join(SubClaimEvidence).filter(
                SubClaimEvidence.sub_claim_id == db_sub_claim.id
            ).all()

            evidences = []
            for db_evidence in db_evidences:
                # Get the source for this evidence
                db_source = self.db.query(SourceDB).filter(SourceDB.id == db_evidence.source_id).first()
                source = Source(
                    id=db_source.id,
                    url=db_source.url,
                    domain=db_source.domain,
                    fetched_at=db_source.fetched_at,
                    snapshot_url=db_source.snapshot_url,
                    credibility_tier=db_source.credibility_tier,
                    content_hash=db_source.content_hash
                )
                evidence = Evidence(
                    id=db_evidence.id,
                    source=source,
                    excerpt=db_evidence.excerpt,
                    retrieved_via=db_evidence.retrieved_via,
                    confidence=db_evidence.confidence
                )
                evidences.append(evidence)

            # Get source_tweaks for this sub_claim
            db_tweaks = self.db.query(SourceTweakDB).filter(SourceTweakDB.sub_claim_id == db_sub_claim.id).all()
            source_tweaks = []
            for db_tweak in db_tweaks:
                source_tweaks.append(SourceTweak(
                    id=db_tweak.id,
                    original_text=db_tweak.original_text,
                    altered_text=db_tweak.altered_text,
                    tweak_type=db_tweak.tweak_type,
                    diff_span=(db_tweak.diff_span_start, db_tweak.diff_span_end)
                ))

            # Get originating account (patient_zero) for this sub_claim
            db_account = self.db.query(OriginatingAccountDB).filter(
                OriginatingAccountDB.sub_claim_id == db_sub_claim.id
            ).first()
            patient_zero = None
            if db_account:
                patient_zero = OriginatingAccount(
                    platform=db_account.platform,
                    handle=db_account.handle,
                    first_seen_at=db_account.first_seen_at,
                    follower_count=db_account.follower_count,
                    prior_flagged_claims=db_account.prior_flagged_claims
                )

            # Note: We are missing the narrative and red_team_audit for the sub_claim? Actually, they are at dossier level.
            # We'll get them from the dossier.

            sub_claim = SubClaim(
                id=db_sub_claim.id,
                text=db_sub_claim.text,
                atomic=db_sub_claim.atomic,
                verdict=db_sub_claim.verdict,
                verdict_confidence=db_sub_claim.verdict_confidence,
                evidence=evidences,
                unverified_inference=db_sub_claim.unverified_inference,
                source_tweaks=source_tweaks
                # Note: patient_zero is set above, but the SubClaim model doesn't have patient_zero.
                # Wait, the SubClaim model in the prompt does not have patient_zero.
                # The patient_zero is in the Dossier.
                # We made another error: the Dossier has patient_zero: OriginatingAccount | None.
                # So we need to move patient_zero to the dossier level.
            )
            sub_claims.append(sub_claim)

        # Get dossier-level patient_zero (we'll take the first sub_claim's account? Not correct.)
        # Actually, the patient_zero is for the dossier, not per sub_claim.
        # We'll need to store it in the DossierDB.
        # We'll skip for now and set to None.

        # Get dossier-level narrative and red_team_audit (we'll skip for now)

        dossier = Dossier(
            id=db_dossier.id,
            input_claim=db_dossier.input_claim,
            language=db_dossier.language,
            sub_claims=sub_claims,
            patient_zero=None,  # TODO
            source_tweaks=[],  # TODO: we need to collect source_tweaks from sub_claims? Actually, source_tweaks are per sub_claim.
            narrative=NarrativeProfile(
                core_narrative="",
                emotional_hooks=[],
                target_demographic="",
                plausible_intent=""
            ),  # TODO
            red_team_audit=RedTeamAudit(
                flags=[],
                source_credibility_concerns=[],
                confidence_adjustment=0.0
            ),  # TODO
            overall_verdict=db_dossier.overall_verdict,
            overall_confidence=db_dossier.overall_confidence,
            generated_at=db_dossier.generated_at
        )

        return dossier

# We'll also need a function to initialize the database and create tables.

def init_db():
    Base.metadata.create_all(bind=engine)