"""
Synthesizer Agent for TruthTrace.
Synthesizes findings from OSINT Hunter, Social Hunter, Wayback CDX, Fact Checker,
Narrative Profiler, Red-Team Auditor, Attribution Agent, and Video Analyst
into an authoritative, chronologically sorted forensic Dossier.
"""
from .base_agent import BaseAgent, AgentResult
from typing import Dict, Any, List, Optional
import logging
import uuid
from datetime import datetime
from urllib.parse import urlparse

from models.schemas import (
    Dossier, SubClaim, Evidence, Source, OriginatingAccount,
    SourceTweak, NarrativeProfile, RedTeamAudit, TimelineEvent, Claim,
    ClaimCluster, AttributionReport, VideoForensics
)
from utils.vector_store import vector_store

logger = logging.getLogger(__name__)

class SynthesizerAgent(BaseAgent):
    """
    Synthesizes results from all upstream forensic agents into an authoritative Dossier.
    """
    def __init__(self):
        super().__init__("Synthesizer")

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Input: {
            'claims': List[str],
            'provenance': List[Dict],
            'social_provenance': Optional[List[Dict]],
            'fact_check_results': List[Dict],
            'wayback_snapshots': Optional[Dict[str, Dict]],
            'narrative_analysis': Optional[Dict],
            'red_team_audit': Optional[Dict],
            'attribution': Optional[Dict],
            'video_forensics': Optional[Dict],
            'video_analysis': Optional[List[Dict]]
        }
        Output: Dossier serialized as dict
        """
        try:
            claims = input_data.get('claims', [])
            if not claims and 'claim' in input_data:
                claims = [input_data['claim']]

            if not claims:
                return AgentResult(success=False, error="No claims to synthesize")

            provenance = input_data.get('provenance', [])
            social_provenance = input_data.get('social_provenance', [])
            combined_provenance = provenance + social_provenance

            fact_check_results = input_data.get('fact_check_results', [])
            wayback_snapshots = input_data.get('wayback_snapshots', {})
            narrative_analysis = input_data.get('narrative_analysis', {})
            red_team_audit = input_data.get('red_team_audit', {})
            attribution_dict = input_data.get('attribution', {})
            video_forensics_dict = input_data.get('video_forensics', {})

            # 1. Build canonical Claims corpus & register in VectorStore
            claims_corpus = self._build_claims_corpus(claims, combined_provenance)
            vector_store.add_claims(claims_corpus)

            # 2. Perform Semantic Clustering & find cluster Patient-Zero candidates
            clusters = vector_store.cluster_claims(similarity_threshold=0.20)

            # 3. Build sorted chronological timeline
            timeline = self._build_timeline(combined_provenance, wayback_snapshots)

            # 4. Determine overall verdict & confidence
            verdict, confidence = self._determine_overall_verdict(fact_check_results, red_team_audit)

            # 5. Extract Patient Zero candidate from earliest timeline event or cluster
            patient_zero = self._extract_patient_zero(timeline, combined_provenance, clusters)

            # 6. Build SubClaims and Evidence
            sub_claims = self._build_sub_claims(claims, fact_check_results, combined_provenance, wayback_snapshots, verdict, confidence)

            # 7. Build Narrative Profile
            narrative_profile = NarrativeProfile(
                core_narrative=narrative_analysis.get('core_narrative', f"Analysis of claim: {claims[0]}"),
                emotional_hooks=narrative_analysis.get('emotional_hooks', []),
                target_demographic=narrative_analysis.get('target_demographic', 'General Public'),
                plausible_intent=narrative_analysis.get('plausible_intent', 'Information sharing / virality'),
                coordinated_cluster_id=narrative_analysis.get('coordinated_cluster_id')
            )

            # 8. Build Red Team Audit
            red_team_audit_obj = RedTeamAudit(
                flags=red_team_audit.get('flags', []),
                source_credibility_concerns=red_team_audit.get('source_credibility_concerns', []),
                confidence_adjustment=red_team_audit.get('confidence_adjustment', 0.0)
            )

            # 9. Build Attribution Report
            attribution_obj = None
            if attribution_dict:
                try:
                    attribution_obj = AttributionReport.model_validate(attribution_dict)
                except Exception as e:
                    logger.debug(f"Attribution parsing error: {e}")

            # 10. Build Video Forensics Report
            video_forensics_obj = None
            if video_forensics_dict:
                try:
                    video_forensics_obj = VideoForensics.model_validate(video_forensics_dict)
                except Exception as e:
                    logger.debug(f"Video forensics parsing error: {e}")

            # 11. Assemble full Dossier
            dossier = Dossier(
                id=str(uuid.uuid4())[:16],
                input_claim=claims[0],
                language="en",
                sub_claims=sub_claims,
                patient_zero=patient_zero,
                timeline=timeline,
                claims_corpus=claims_corpus,
                clusters=clusters,
                attribution=attribution_obj,
                video_forensics=video_forensics_obj,
                source_tweaks=[],
                narrative=narrative_profile,
                red_team_audit=red_team_audit_obj,
                overall_verdict=verdict,
                overall_confidence=confidence,
                generated_at=datetime.now()
            )

            return AgentResult(success=True, data=dossier.model_dump())

        except Exception as e:
            logger.error(f"Synthesizer error: {e}", exc_info=True)
            return AgentResult(success=False, error=str(e))

    def _build_claims_corpus(self, claims: List[str], provenance: List[Dict]) -> List[Claim]:
        """Convert input claims and provenance items into canonical Claim objects."""
        corpus = []
        for claim_text in claims:
            corpus.append(Claim(
                text=claim_text,
                source_platform="Input Claim",
                timestamp=datetime.now()
            ))

        for prov in provenance:
            if isinstance(prov, dict):
                title = prov.get('title') or prov.get('claim')
                if title:
                    ts = self._parse_datetime(prov.get('timestamp'))
                    corpus.append(Claim(
                        text=title,
                        source_url=prov.get('url'),
                        source_platform=prov.get('platform') or prov.get('source_type'),
                        timestamp=ts,
                        metadata=prov
                    ))
        return corpus

    def _build_timeline(self, provenance: List[Dict], wayback_snapshots: Dict[str, Dict]) -> List[TimelineEvent]:
        """Build sorted ascending chronological timeline of discovered mentions."""
        events = []
        for prov in provenance:
            if not isinstance(prov, dict):
                continue

            url = prov.get('url') or prov.get('earliest_mention', {}).get('url')
            title = prov.get('title') or prov.get('claim', 'Mention')
            source_name = prov.get('platform') or prov.get('source_type') or 'Web Source'
            ts = self._parse_datetime(prov.get('timestamp') or prov.get('earliest_mention', {}).get('timestamp'))

            # Check Wayback CDX timestamp for this URL
            earliest_cdx_ts = None
            if url and url in wayback_snapshots:
                cdx_record = wayback_snapshots[url]
                if cdx_record.get('earliest_timestamp'):
                    earliest_cdx_ts = self._parse_datetime(cdx_record['earliest_timestamp'])

            tier = prov.get('credibility_tier') or 'unverified'
            if tier not in ["registry", "primary", "mainstream", "unverified", "known_low_credibility"]:
                tier = "unverified"

            events.append(TimelineEvent(
                source=source_name,
                timestamp=ts,
                url=url,
                title=title,
                snippet=prov.get('raw_metadata', {}).get('description') or title,
                earliest_cdx_timestamp=earliest_cdx_ts,
                credibility_tier=tier,
                metadata=prov
            ))

        # Sort ascending by timestamp (use earliest_cdx_timestamp if earlier)
        def event_sort_key(ev: TimelineEvent):
            t1 = ev.earliest_cdx_timestamp
            t2 = ev.timestamp
            if t1 and t1.tzinfo:
                t1 = t1.replace(tzinfo=None)
            if t2 and t2.tzinfo:
                t2 = t2.replace(tzinfo=None)
            if t1 and t2:
                return min(t1, t2)
            return t1 or t2 or datetime.max

        events.sort(key=event_sort_key)

        # Mark the very first valid chronological event as the candidate patient zero
        if events:
            events[0].is_patient_zero_candidate = True

        return events

    def _extract_patient_zero(self, timeline: List[TimelineEvent], provenance: List[Dict], clusters: List[ClaimCluster]) -> Optional[OriginatingAccount]:
        """Identify candidate Patient Zero from the earliest timeline event or cluster."""
        if not timeline:
            return None

        earliest = timeline[0]
        platform = earliest.source
        handle = "unknown"

        # Check if handle is present in metadata, earliest_mention, or URL
        if earliest.metadata and 'handle' in earliest.metadata:
            handle = earliest.metadata['handle']
        elif earliest.metadata and 'earliest_mention' in earliest.metadata:
            handle = earliest.metadata['earliest_mention'].get('handle', 'unknown')
        elif earliest.url:
            domain = urlparse(earliest.url).netloc
            handle = domain or platform

        first_seen = earliest.earliest_cdx_timestamp or earliest.timestamp or datetime.now()
        if first_seen and first_seen.tzinfo:
            first_seen = first_seen.replace(tzinfo=None)

        return OriginatingAccount(
            platform=platform,
            handle=handle,
            first_seen_at=first_seen,
            prior_flagged_claims=0
        )

    def _determine_overall_verdict(self, fact_check_results: List[Dict], red_team_audit: Dict) -> tuple[str, float]:
        """Compute overall verdict and confidence."""
        if fact_check_results:
            first_fc = fact_check_results[0]
            verdict = first_fc.get('verdict', 'unverified').lower()
            confidence = float(first_fc.get('confidence', 0.60))
        else:
            verdict = "unverified"
            confidence = 0.50

        # Adjust for red-team audit if provided
        adj = float(red_team_audit.get('confidence_adjustment', 0.0))
        final_conf = max(0.1, min(0.99, confidence + adj))

        valid_verdicts = ["true", "false", "misleading", "unverified", "satire", "opinion"]
        if verdict not in valid_verdicts:
            verdict = "unverified"

        return verdict, final_conf

    def _build_sub_claims(self, claims: List[str], fact_check_results: List[Dict], 
                          provenance: List[Dict], wayback_snapshots: Dict, 
                          verdict: str, confidence: float) -> List[SubClaim]:
        """Construct SubClaim objects with linked Evidence items."""
        sub_claims = []
        for claim_text in claims:
            evidence_items = []

            for prov in provenance:
                url = prov.get('url') or ''
                domain = prov.get('domain') or urlparse(url).netloc or 'unknown'
                tier = prov.get('credibility_tier')
                if tier not in ["registry", "primary", "mainstream", "unverified", "known_low_credibility"]:
                    tier = "unverified"

                snapshot_url = None
                if url in wayback_snapshots:
                    snapshot_url = wayback_snapshots[url].get('earliest_snapshot_url')

                src = Source(
                    url=url or f"https://example.com/claim/{uuid.uuid4().hex[:8]}",
                    domain=domain,
                    snapshot_url=snapshot_url,
                    credibility_tier=tier
                )

                evidence_items.append(Evidence(
                    source=src,
                    excerpt=prov.get('title') or f"Discovered mention of: {claim_text}",
                    retrieved_via=prov.get('source_type') or 'osint_hunter',
                    confidence=0.85
                ))

            sub_claim = SubClaim(
                text=claim_text,
                verdict=verdict,
                verdict_confidence=confidence,
                evidence=evidence_items,
                unverified_inference=(verdict == "unverified" and len(evidence_items) == 0)
            )
            sub_claims.append(sub_claim)

        return sub_claims

    def _parse_datetime(self, val: Any) -> Optional[datetime]:
        """Safely parse various datetime strings and normalize to offset-naive UTC."""
        if isinstance(val, datetime):
            return val.replace(tzinfo=None) if val.tzinfo else val
        if not val or not isinstance(val, str):
            return None
        try:
            dt = datetime.fromisoformat(val.replace('Z', '+00:00'))
            return dt.replace(tzinfo=None) if dt.tzinfo else dt
        except Exception:
            try:
                dt = datetime.strptime(val[:19], "%Y-%m-%dT%H:%M:%S")
                return dt
            except Exception:
                return None