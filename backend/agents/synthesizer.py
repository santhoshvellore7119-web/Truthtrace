from .base_agent import BaseAgent, AgentResult
from utils.llm import get_llm_prompt
from typing import Dict, Any, List
import logging
import json
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Import the Pydantic models from the models module
try:
    from ..models.schemas import (
        Dossier, SubClaim, Evidence, Source, OriginatingAccount,
        SourceTweak, NarrativeProfile, RedTeamAudit
    )
except ImportError:
    # Fallback for when the models module is not available (e.g., during testing)
    # We'll define minimal versions here, but ideally we should have the models.
    from pydantic import BaseModel, Field
    from typing import List, Optional, Literal
    from datetime import datetime
    import hashlib

    class Source(BaseModel):
        id: str = Field(default_factory=lambda: hashlib.sha256(datetime.now().isoformat().encode()).hexdigest()[:16])
        url: str
        domain: str
        fetched_at: datetime = Field(default_factory=datetime.now)
        snapshot_url: Optional[str] = None
        credibility_tier: Literal["registry", "primary", "mainstream", "unverified", "known_low_credibility"]
        content_hash: str

    class Evidence(BaseModel):
        id: str = Field(default_factory=lambda: hashlib.sha256(datetime.now().isoformat().encode()).hexdigest()[:16])
        source: Source
        excerpt: str = Field(..., min_length=1)
        retrieved_via: str
        confidence: float = Field(..., ge=0.0, le=1.0)

    class SubClaim(BaseModel):
        id: str = Field(default_factory=lambda: hashlib.sha256(datetime.now().isoformat().encode()).hexdigest()[:16])
        text: str = Field(..., min_length=1)
        atomic: bool = True
        verdict: Literal["true", "false", "misleading", "unverified", "satire", "opinion"]
        verdict_confidence: float = Field(..., ge=0.0, le=1.0)
        evidence: List[Evidence] = Field(default_factory=list)
        unverified_inference: bool = False

    class OriginatingAccount(BaseModel):
        platform: str
        handle: str
        first_seen_at: Optional[datetime] = None
        follower_count: Optional[int] = None
        prior_flagged_claims: int = 0

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
        language: str = Field(..., min_length=2)
        sub_claims: List[SubClaim] = Field(default_factory=list)
        patient_zero: Optional[OriginatingAccount] = None
        source_tweaks: List[SourceTweak] = Field(default_factory=list)
        narrative: NarrativeProfile
        red_team_audit: RedTeamAudit = Field(default_factory=RedTeamAudit)
        overall_verdict: Literal["true", "false", "misleading", "unverified", "satire", "opinion"]
        overall_confidence: float = Field(..., ge=0.0, le=1.0)
        generated_at: datetime = Field(default_factory=datetime.now)

class SynthesizerAgent(BaseAgent):
    """Synthesizes results from all agents into a structured dossier using LLM or fallback."""

    def __init__(self):
        super().__init__("Synthesizer")

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Input: {
            'claims': List[str],
            'provenance': List[Dict],
            'fact_check_results': List[Dict],
            'narrative_analysis': Dict,
            'red_team_audit': Dict,   # optional, from RedTeamAuditor
            'video_analysis': List[Dict]  # optional, from VideoAnalyst
        }
        Output: Dossier object as dict
        """
        try:
            claims = input_data.get('claims', [])
            provenance = input_data.get('provenance', [])
            fact_check_results = input_data.get('fact_check_results', [])
            narrative_analysis = input_data.get('narrative_analysis', {})
            video_analysis = input_data.get('video_analysis', [])

            if not claims:
                return AgentResult(success=False, error="No claims to synthesize")

            # Try LLM-based synthesis if available
            from utils.llm import llm_manager
            raw_dossier = None
            if llm_manager.is_available():
                # Prepare a concise summary for LLM
                claims_text = " ".join(claims[:2])  # first claim(s)
                fc_summary = ""
                if fact_check_results:
                    fc_items = []
                    for fc in fact_check_results[:3]:
                        fc_items.append(f"Verdict: {fc.get('verdict', 'unknown')}, Confidence: {fc.get('confidence', 0):.2f}")
                    fc_summary = "; ".join(fc_items)
                narrative_summary = ""
                if narrative_analysis:
                    narrative_summary = f"Core narrative: {narrative_analysis.get('core_narrative', 'unknown')}; Intent: {narrative_analysis.get('plausible_intent', 'unknown')}"
                video_summary = ""
                if video_analysis:
                    video_count = len(video_analysis)
                    video_summary = f"Video analysis available: {video_count} video(s) analyzed forensically"

                prompt = f"""You are an AI misinformation analyst. Given the following information, produce a structured JSON assessment.

                Claim: {claims_text}
                Fact-check summaries: {fc_summary}
                Narrative analysis: {narrative_summary}
                Video analysis: {video_summary}

                Provide a JSON object with:
                - verdict: one of ["CONFIRMED", "MOSTLY TRUE", "MISLEADING", "OUT OF CONTEXT", "FABRICATED", "SATIRE", "UNVERIFIED"]
                - credibility_score: float 0-100 (higher means more credible)
                - timeline: list of objects with timestamp and event (you can infer plausible timeline)
                - patient_zero: object with entity, handle, platform, account_created, bio, network_affiliations (if unknown, use null/empty)
                - source_tweaking: object with original_statement, claimed_statement, alterations (list)
                - narrative_intention: object with core_narrative, emotional_hooks (list), target_demographic, plausible_intent
                - evidence: list of objects with source, url, timestamp, type

                Use the provided info as much as possible; if unknown, indicate with empty strings or null.
                Respond with valid JSON only."""
                try:
                    llm_response = get_llm_prompt(prompt, max_tokens=1024, temperature=0.3)
                    # Extract JSON
                    import re
                    json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                    if json_match:
                        raw_dossier = json.loads(json_match.group())
                        # Ensure all required fields exist (provide defaults if missing)
                        required_defaults = {
                            'verdict': 'UNVERIFIED',
                            'credibility_score': 50.0,
                            'timeline': [],
                            'patient_zero': {},
                            'source_tweaking': {'original_statement': '', 'claimed_statement': '', 'alterations': []},
                            'narrative_intention': {'core_narrative': '', 'emotional_hooks': [], 'target_demographic': '', 'plausible_intent': ''},
                            'evidence': []
                        }
                    for key, default in required_defaults.items():
                        if key not in raw_dossier:
                            raw_dossier[key] = default
                        elif isinstance(default, dict) and isinstance(raw_dossier[key], dict):
                            # merge sub-dicts
                            for subkey, subdefault in default.items():
                                if subkey not in raw_dossier[key]:
                                    raw_dossier[key][subkey] = subdefault
                        elif isinstance(default, list) and isinstance(raw_dossier[key], list):
                            # ensure list
                            pass
                    logger.info("Generated dossier using LLM")
                except Exception as e:
                    logger.warning(f"LLM synthesis failed: {e}, falling back to rule-based")
                    raw_dossier = None  # We'll fall back to rule-based below

            # If LLM failed or not available, use rule-based synthesis
            if raw_dossier is None:
                # Fallback: rule-based synthesis (same as before but cleaned up)
                # For simplicity, we'll use the first claim's data if there are multiple
                primary_claim = claims[0] if claims else ""

                # Determine overall verdict based on fact check results
                verdict = self._determine_verdict(fact_check_results)
                credibility_score = self._calculate_credibility_score(fact_check_results)

                # Apply video analysis credibility adjustment if available
                if video_analysis:
                    video_credibility_adjustment = self._calculate_video_credibility_adjustment(video_analysis)
                    credibility_score = max(0.0, min(100.0, credibility_score + video_credibility_adjustment))

                # Build timeline from provenance (simplified)
                timeline = self._build_timeline(provenance)

                # Extract patient zero from provenance (first mention)
                patient_zero = self._extract_patient_zero(provenance)

                # Build source tweaking analysis (simplified)
                source_tweaking = self._build_source_tweaking(claims, fact_check_results)

                # Narrative intention is directly from narrative_analysis
                narrative_intention = narrative_analysis

                # Gather evidence from fact check results, provenance, and video analysis
                evidence = self._gather_evidence(fact_check_results, provenance, video_analysis)

                # Construct the final dossier
                raw_dossier = {
                    'verdict': verdict,
                    'credibility_score': credibility_score,
                    'timeline': timeline,
                    'patient_zero': patient_zero,
                    'source_tweaking': source_tweaking,
                    'narrative_intention': narrative_intention,
                    'evidence': evidence
                }

                logger.info("Generated dossier using rule-based fallback")

            # Apply red team audit confidence adjustment
            red_team_audit = input_data.get('red_team_audit', {})
            if red_team_audit:
                confidence_adjustment = red_team_audit.get('confidence_adjustment', 0.0)
                if 'credibility_score' in raw_dossier:
                    raw_dossier['credibility_score'] = max(0.0, min(100.0, raw_dossier['credibility_score'] + (confidence_adjustment * 100)))

            # Convert the raw_dossier to a Dossier object
            logger.info(f"About to call _build_dossier with red_team_audit type: {type(red_team_audit)}")
            logger.info(f"red_team_audit value: {red_team_audit}")
            dossier = self._build_dossier(raw_dossier, claims, provenance, fact_check_results, narrative_analysis, red_team_audit, video_analysis)

            logger.info("Generated dossier")
            # Return the dossier as a dictionary to match AgentResult's data field type
            data = dossier.model_dump()
            return AgentResult(success=True, data=data)
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return AgentResult(success=False, error=str(e))

    def _determine_verdict(self, fact_check_results: List[Dict]) -> str:
        """Determine overall verdict from fact check results."""
        if not fact_check_results:
            return "UNVERIFIED"

        # Simple aggregation: if any fact check says fabricated, lean towards that
        # In reality, this would be more sophisticated
        verdicts = [result.get('verdict', '').upper() for result in fact_check_results]
        if any(v == 'FABRICATED' for v in verdicts):
            return "FABRICATED"
        elif any(v == 'MISLEADING' for v in verdicts):
            return "MISLEADING"
        elif any(v == 'OUT OF CONTEXT' for v in verdicts):
            return "OUT OF CONTEXT"
        elif any(v == 'SATIRE' for v in verdicts):
            return "SATIRE"
        elif any(v in ['CONFIRMED', 'MOSTLY TRUE'] for v in verdicts):
            return "CONFIRMED"
        else:
            return "UNVERIFIED"

    def _calculate_credibility_score(self, fact_check_results: List[Dict]) -> float:
        """Calculate credibility score from fact check results."""
        if not fact_check_results:
            return 50.0  # Neutral when no data

        # Simple average of confidence scores (inverted for credibility)
        scores = []
        for result in fact_check_results:
            confidence = result.get('confidence', 0.5)
            verdict = result.get('verdict', '').upper()
            # If verdict indicates false, credibility is low; if true, high
            if verdict in ['FABRICATED', 'MISLEADING', 'OUT OF CONTEXT']:
                scores.append((1 - confidence) * 100)  # Invert and scale to 0-100
            else:
                scores.append(confidence * 100)

        return sum(scores) / len(scores) if scores else 50.0

    def _calculate_video_credibility_adjustment(self, video_analysis: List[Dict]) -> float:
        """Calculate credibility adjustment based on video analysis results."""
        if not video_analysis:
            return 0.0

        total_adjustment = 0.0
        video_count = len(video_analysis)

        for video in video_analysis:
            # Extract credibility score from video analysis if available
            credibility_assessment = video.get('credibility_assessment', {})
            if isinstance(credibility_assessment, dict):
                video_score = credibility_assessment.get('overall_credibility_score', 0.5)
                # Convert 0-1 score to -50 to +50 adjustment (where 0.5 = neutral)
                adjustment = (video_score - 0.5) * 100  # -50 to +50 range
                total_adjustment += adjustment
                logger.debug(f"Video credibility adjustment: {adjustment} (video score: {video_score})")

        # Average the adjustment across all videos
        average_adjustment = total_adjustment / video_count if video_count > 0 else 0.0
        # Limit the adjustment to prevent overcorrection
        return max(-25.0, min(25.0, average_adjustment))

    def _build_timeline(self, provenance: List[Dict]) -> List[Dict]:
        """Build timeline from provenance data."""
        timeline = []
        for prov in provenance:
            if not isinstance(prov, dict):
                continue

            # Add earliest mention
            if 'earliest_mention' in prov and isinstance(prov['earliest_mention'], dict):
                mention = prov['earliest_mention']
                timeline.append({
                    'timestamp': mention.get('timestamp', ''),
                    'event': f"First appearance on {mention.get('platform', 'unknown')} by {mention.get('handle', 'unknown user')}"
                })
            # Add amplification events
            amplification_events = prov.get('amplification_events', [])
            if isinstance(amplification_events, list):
                for event in amplification_events:
                    if isinstance(event, dict):
                        timeline.append({
                            'timestamp': event.get('timestamp', ''),
                            'event': f"Amplified on {event.get('platform', 'unknown')} in {event.get('community', 'unknown community')}"
                        })
            # Add video analysis events if available
            video_analysis = prov.get('video_analysis', [])
            if isinstance(video_analysis, list):
                for video_event in video_analysis:
                    if isinstance(video_event, dict):
                        timeline.append({
                            'timestamp': video_event.get('timestamp', ''),
                            'event': f"Video forensic analysis: {video_event.get('platform', 'unknown')} content examined"
                        })
        # Sort by timestamp (empty strings will sort to the beginning)
        timeline.sort(key=lambda x: x['timestamp'])
        return timeline

    def _extract_patient_zero(self, provenance: List[Dict]) -> Dict:
        """Extract patient zero (earliest mention) from provenance."""
        if not provenance:
            return {}

        # Find the earliest mention across all provenance
        earliest = None
        earliest_time = None

        for prov in provenance:
            if not isinstance(prov, dict):
                continue
            if 'earliest_mention' in prov and isinstance(prov['earliest_mention'], dict):
                mention = prov['earliest_mention']
                timestamp = mention.get('timestamp', '')
                if timestamp and (earliest_time is None or timestamp < earliest_time):
                    earliest_time = timestamp
                    earliest = mention

        if earliest:
            # Return only the fields we can actually use for OriginatingAccount
            # We'll handle the datetime conversion in _build_dossier
            return {
                'handle': earliest.get('handle', 'unknown'),
                'platform': earliest.get('platform', 'unknown'),
                'first_seen_at_str': earliest.get('timestamp', '')  # String timestamp to be parsed later
            }
        return {}

    def _build_source_tweaking(self, claims: List[str], fact_check_results: List[Dict]) -> Dict:
        """Build source tweaking analysis."""
        # Simplified: if we have fact check results, we can note alterations
        # In a real implementation, we would compare the claim to the original source
        if not fact_check_results:
            return {
                'original_statement': 'No original source found for comparison.',
                'claimed_statement': claims[0] if claims else '',
                'alterations': ['Unable to verify against original source']
            }

        # Use the first fact check result for simplicity
        fact_check = fact_check_results[0]
        original = fact_check.get('original_statement', 'Original statement not available.')
        claimed = claims[0] if claims else ''
        alterations = fact_check.get('alterations', ['No specific alterations noted'])

        return {
            'original_statement': original,
            'claimed_statement': claimed,
            'alterations': alterations
        }

    def _gather_evidence(self, fact_check_results: List[Dict], provenance: List[Dict], video_analysis: List[Dict] = None) -> List[Dict]:
        """Gather evidence from fact check results, provenance, and video analysis."""
        evidence = []
        video_analysis = video_analysis or []

        # Add fact check sources
        for result in fact_check_results:
            if not isinstance(result, dict):
                continue
            sources = result.get('sources', [])
            if isinstance(sources, list):
                for source in sources:
                    if isinstance(source, dict):
                        evidence.append({
                            'source': source.get('name', 'Unknown'),
                            'url': source.get('url', ''),
                            'timestamp': source.get('timestamp', ''),
                            'snapshot_url': source.get('snapshot_url'),  # May be None
                            'type': 'fact_check'
                        })
            # Add archival snapshots
            archival_snapshots = result.get('archival_snapshots', [])
            if isinstance(archival_snapshots, list):
                for snapshot in archival_snapshots:
                    if isinstance(snapshot, dict):
                        evidence.append({
                            'source': 'Wayback Machine',
                            'url': snapshot.get('url', ''),
                            'timestamp': snapshot.get('timestamp', ''),
                            'snapshot_url': snapshot.get('snapshot_url'),  # May be None
                            'type': 'archival'
                        })

        # Add provenance URLs as evidence
        for prov in provenance:
            if not isinstance(prov, dict):
                continue
            if 'earliest_mention' in prov and isinstance(prov['earliest_mention'], dict):
                mention = prov['earliest_mention']
                evidence.append({
                    'source': f"Provenance ({mention.get('platform', 'unknown')})",
                    'url': mention.get('url', ''),
                    'timestamp': mention.get('timestamp', ''),
                    'snapshot_url': mention.get('snapshot_url'),  # May be None
                    'type': 'provenance'
                })
            # Also check amplification events for evidence
            amplification_events = prov.get('amplification_events', [])
            if isinstance(amplification_events, list):
                for event in amplification_events:
                    if isinstance(event, dict):
                        evidence.append({
                            'source': f"Provenance ({event.get('platform', 'unknown')})",
                            'url': event.get('url', ''),
                            'timestamp': event.get('timestamp', ''),
                            'snapshot_url': event.get('snapshot_url'),  # May be None
                            'type': 'provenance'
                        })

        # Add video analysis as evidence
        for video in video_analysis:
            # Add the video page itself as evidence
            video_url = video.get('video_url', '')
            if video_url:
                evidence.append({
                    'source': f"Video ({video.get('platform', 'unknown')})",
                    'url': video_url,
                    'timestamp': video.get('analysis_timestamp', ''),
                    'snapshot_url': video.get('evidence_preservation', {}).get('video_page_snapshot_url'),
                    'type': 'video_forensic_analysis',
                    'credibility_score': video.get('credibility_assessment', {}).get('overall_credibility_score', 0.5)
                })

            # Add specific findings from video analysis as evidence if they have relevant data
            authenticity = video.get('authenticity_analysis', {})
            if authenticity and isinstance(authenticity, dict):
                evidence.append({
                    'source': f"Video Authenticity Analysis ({video.get('platform', 'unknown')})",
                    'url': video.get('video_url', ''),
                    'timestamp': video.get('analysis_timestamp', ''),
                    'snapshot_url': video.get('evidence_preservation', {}).get('video_page_snapshot_url'),
                    'type': 'video_authenticity',
                    'credibility_score': authenticity.get('authenticity_score', 0.5)
                })

            manipulation = video.get('manipulation_detection', {})
            if manipulation and isinstance(manipulation, dict):
                evidence.append({
                    'source': f"Video Manipulation Check ({video.get('platform', 'unknown')})",
                    'url': video.get('video_url', ''),
                    'timestamp': video.get('analysis_timestamp', ''),
                    'snapshot_url': video.get('evidence_preservation', {}).get('video_page_snapshot_url'),
                    'type': 'video_manipulation_analysis',
                    'credibility_score': 1.0 - manipulation.get('manipulation_confidence', 0.0)  # Invert - lower manipulation confidence is better
                })

        return evidence

    def _build_dossier(self, raw_dossier: Dict[str, Any], claims: List[str], provenance: List[Dict],
                       fact_check_results: List[Dict], narrative_analysis: Dict[str, Any],
                       red_team_audit: Dict[str, Any], video_analysis: List[Dict] = None) -> Dossier:
        """Convert raw_dossier and input data to a Dossier object."""
        video_analysis = video_analysis or []

        # Generate an ID for the dossier
        dossier_id = str(uuid.uuid4())

        # Input claim: use the first claim or concatenate if multiple? We'll use the first.
        input_claim = claims[0] if claims else ""

        # Language: we don't have language detection, default to 'en'
        language = "en"

        # Build sub_claims: we'll create one sub_claim for the first claim.
        # In a more advanced version, we would split claims and map evidence to each.
        sub_claims = []
        if claims:
            # Use the first claim for the sub_claim text
            claim_text = claims[0]
            # Map the verdict from raw_dossier to the SubClaim verdict literal
            verdict_str = raw_dossier.get('verdict', 'UNVERIFIED').upper()
            # We need to map the verdict string to the literal allowed in SubClaim.
            # The SubClaim verdict literal is: "true", "false", "misleading", "unverified", "satire", "opinion"
            # We'll map the raw_dossier verdict to one of these.
            verdict_mapping = {
                "CONFIRMED": "true",
                "MOSTLY TRUE": "true",
                "MISLEADING": "misleading",
                "OUT OF CONTEXT": "misleading",  # treat as misleading
                "FABRICATED": "false",
                "SATIRE": "satire",
                "UNVERIFIED": "unverified"
            }
            sub_claim_verdict = verdict_mapping.get(verdict_str, "unverified")
            # The verdict_confidence: we have credibility_score in raw_dossier (0-100)
            # We'll use that as the confidence for the sub_claim (convert to 0-1)
            credibility_score = raw_dossier.get('credibility_score', 50.0)
            verdict_confidence = credibility_score / 100.0
            # Build evidence list for the sub_claim
            evidence_list = []
            for ev in raw_dossier.get('evidence', []):
                # Create a Source object from the URL
                url = ev.get('url', '')
                # Extract domain from URL
                domain = ""
                if url:
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        domain = parsed.netloc
                    except Exception:
                        domain = ""
                source = Source(
                    url=url,
                    domain=domain,
                    snapshot_url=ev.get('snapshot_url'),  # Add snapshot URL if available
                    credibility_tier="unverified",  # placeholder
                    content_hash=""  # placeholder
                )
                # The Evidence model requires an excerpt and retrieved_via.
                # We'll set excerpt to a placeholder and retrieved_via to the type.
                evidence = Evidence(
                    source=source,
                    excerpt="Evidence excerpt not available in the current prototype.",
                    retrieved_via=ev.get('type', 'unknown'),
                    confidence=0.8  # placeholder confidence
                )
                evidence_list.append(evidence)

            # Determine if the sub_claim has unverified_inference
            # According to the Dossier model, a SubClaim must have evidence unless verdict is unverified.
            unverified_inference = (sub_claim_verdict == "unverified") and (not evidence_list)

            sub_claim = SubClaim(
                text=claim_text,
                verdict=sub_claim_verdict,  # type: ignore
                verdict_confidence=verdict_confidence,
                evidence=evidence_list,
                unverified_inference=unverified_inference
            )
            sub_claims.append(sub_claim)

        # Build patient_zero (OriginatingAccount) from the raw_dossier's patient_zero
        patient_zero_dict = raw_dossier.get('patient_zero', {})
        patient_zero = None
        if patient_zero_dict:
            # Parse the first_seen_at_str to datetime if it's a valid ISO format string
            first_seen_at = None
            first_seen_at_str = patient_zero_dict.get('first_seen_at_str', '')
            if first_seen_at_str:
                try:
                    first_seen_at = datetime.fromisoformat(first_seen_at_str.replace('Z', '+00:00'))
                except ValueError:
                    # If parsing fails, leave as None
                    pass

            patient_zero = OriginatingAccount(
                platform=patient_zero_dict.get('platform', 'unknown'),
                handle=patient_zero_dict.get('handle', 'unknown'),
                first_seen_at=first_seen_at,
                follower_count=None,  # we don't have this
                prior_flagged_claims=0  # we don't have this
            )

        # Build source_tweaks from the raw_dossier's source_tweaking
        source_tweaks = []
        source_tweaking = raw_dossier.get('source_tweaking', {})
        if source_tweaking:
            original_text = source_tweaking.get('original_statement', '')
            altered_text = source_tweaking.get('claimed_statement', '')
            alterations = source_tweaking.get('alterations', [])
            # We'll create one SourceTweak for the pair (original_text, altered_text)
            # We'll set the diff_span to (0, len(altered_text)) as a placeholder.
            if original_text and altered_text:
                source_tweak = SourceTweak(
                    original_text=original_text,
                    altered_text=altered_text,
                    tweak_type="selective_edit",  # placeholder
                    diff_span=(0, len(altered_text))
                )
                source_tweaks.append(source_tweak)
            # Note: we are not handling multiple alterations for simplicity.

        # Build narrative from the raw_dossier's narrative_intention
        narrative_intention = raw_dossier.get('narrative_intention', {})
        narrative = NarrativeProfile(
            core_narrative=narrative_intention.get('core_narrative', ''),
            emotional_hooks=narrative_intention.get('emotional_hooks', []),
            target_demographic=narrative_intention.get('target_demographic', ''),
            plausible_intent=narrative_intention.get('plausible_intent', '')
        )

        # Build red_team_audit from the input red_team_audit
        red_team_audit_obj = RedTeamAudit(
            flags=red_team_audit.get('flags', []),
            source_credibility_concerns=red_team_audit.get('source_credibility_concerns', []),
            confidence_adjustment=red_team_audit.get('confidence_adjustment', 0.0)
        )

        # Build the Dossier
        dossier = Dossier(
            id=dossier_id,
            input_claim=input_claim,
            language=language,
            sub_claims=sub_claims,
            patient_zero=patient_zero,
            source_tweaks=source_tweaks,
            narrative=narrative,
            red_team_audit=red_team_audit_obj,
            overall_verdict=sub_claim_verdict,  # type: ignore
            overall_confidence=verdict_confidence,
            generated_at=datetime.now()
        )

        return dossier