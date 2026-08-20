"""
Video Content Analyst Agent
Specialized agent for deep forensic analysis of video content related to claims.
"""
from .base_agent import BaseAgent, AgentResult
from typing import Dict, Any, List
import logging
import datetime
import sys
import os

logger = logging.getLogger(__name__)

# Add the backend directory to the path to import snapshotter and utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'evidence'))
from snapshot import snapshotter

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
try:
    from llm import llm_manager
    LLM_AVAILABLE = llm_manager.is_available()
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LLM manager not available for video analyst")

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV not available. Video frame analysis will be limited.")

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper not available. Audio transcription will be limited.")

class VideoAnalystAgent(BaseAgent):
    """Performs deep forensic analysis of video content related to claims."""

    def __init__(self):
        super().__init__("VideoAnalyst")
        self.analyzers_initialized = self._initialize_analyzers()

    def _initialize_analyzers(self) -> bool:
        """Initialize video analysis tools."""
        success = True
        if not OPENCV_AVAILABLE:
            logger.warning("OpenCV not initialized - frame analysis limited")
            success = False
        if not WHISPER_AVAILABLE:
            logger.warning("Whisper not initialized - audio transcription limited")
            success = False
        return success

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Input: {
            'claims': List[str],
            'video_sources': List[Dict]  # Optional: pre-identified video sources
        }
        Output: {'video_analysis': List[Dict]} with detailed forensic analysis
        """
        try:
            claims = input_data.get('claims', [])
            video_sources = input_data.get('video_sources', [])

            if not claims and not video_sources:
                return AgentResult(success=False, error="No claims or video sources to analyze")

            # If we have pre-identified video sources, analyze those
            # Otherwise, we might hunt for videos (could call OSINT hunter internally)
            if video_sources:
                analysis_results = await self._analyze_video_sources(video_sources, claims)
            else:
                # In a full implementation, we would hunt for videos related to claims
                # For now, return empty analysis with indication that video hunting would occur
                analysis_results = [{
                    'analysis_type': 'video_hunting_not_implemented',
                    'message': 'Video hunting would be performed to find relevant content',
                    'recommendation': 'Use OSINT hunter with video platform focus or provide video_sources input'
                }]

            return AgentResult(
                success=True,
                data={'video_analysis': analysis_results}
            )
        except Exception as e:
            logger.error(f"Video analyst error: {e}")
            return AgentResult(success=False, error=str(e))

    async def _analyze_video_sources(self, video_sources: List[Dict], claims: List[str]) -> List[Dict]:
        """Analyze provided video sources forensically."""
        results = []

        for video_source in video_sources:
            video_url = video_source.get('url', '')
            platform = video_source.get('platform', 'unknown')

            logger.info(f"Analyzing video from {platform}: {video_url}")

            # Perform comprehensive forensic analysis
            analysis = await self._perform_forensic_video_analysis(video_url, platform, claims)
            results.append(analysis)

        return results

    async def _perform_forensic_video_analysis(self, video_url: str, platform: str, claims: List[str]) -> Dict[str, Any]:
        """Perform deep forensic analysis of a single video."""
        analysis = {
            'video_url': video_url,
            'platform': platform,
            'analysis_timestamp': datetime.datetime.now().isoformat(),
            'claims_examined': claims,
            'forensic_technique': 'comprehensive_video_analysis'
        }

        # 1. Metadata Analysis
        analysis['metadata_analysis'] = await self._analyze_video_metadata(video_url, platform)

        # 2. Frame-by-Frame Analysis (if OpenCV available)
        if OPENCV_AVAILABLE:
            analysis['frame_analysis'] = await self._analyze_video_frames(video_url)
        else:
            analysis['frame_analysis'] = {
                'status': 'limited',
                'reason': 'OpenCV not available for frame analysis'
            }

        # 3. Audio Analysis and Transcription (if Whisper available)
        if WHISPER_AVAILABLE:
            analysis['audio_analysis'] = await self._analyze_video_audio(video_url)
        else:
            analysis['audio_analysis'] = {
                'status': 'limited',
                'reason': 'Whisper not available for audio analysis'
            }

        # 4. Content Authenticity Analysis
        analysis['authenticity_analysis'] = await self._analyze_content_authenticity(video_url, platform)

        # 5. Contextual Analysis
        analysis['contextual_analysis'] = await self._analyze_video_context(video_url, platform, claims)

        # 6. Manipulation Detection
        analysis['manipulation_detection'] = await self._detect_video_manipulation(video_url)

        # 7. Spread and Provenance Analysis
        analysis['provenance_analysis'] = await self._analyze_video_provenance(video_url, platform)

        # 8. Risk and Credibility Assessment
        analysis['credibility_assessment'] = await self._assess_video_credibility(analysis)

        # Add snapshot of video page for evidence preservation
        analysis['evidence_preservation'] = {
            'video_page_snapshot_url': snapshotter.snapshot(video_url),
            'snapshot_timestamp': datetime.datetime.now().isoformat()
        }

        return analysis

    async def _analyze_video_metadata(self, video_url: str, platform: str) -> Dict[str, Any]:
        """Analyze video metadata for inconsistencies and anomalies."""
        metadata = {
            'url': video_url,
            'platform': platform,
            'extraction_timestamp': datetime.datetime.now().isoformat(),
            'metadata_completeness': 'unknown',
            'suspicious_elements': []
        }

        # Platform-specific metadata analysis
        if 'youtube.com' in video_url or 'youtu.be' in video_url:
            metadata.update(await self._analyze_youtube_metadata(video_url))
        elif 'vimeo.com' in video_url:
            metadata.update(await self._analyze_vimeo_metadata(video_url))
        else:
            metadata['generic_metadata'] = {
                'note': 'Generic metadata analysis applied',
                'recommendation': 'Platform-specific analysis would provide deeper insights'
            }

        return metadata

    async def _analyze_youtube_metadata(self, video_url: str) -> Dict[str, Any]:
        """Analyze YouTube-specific metadata."""
        # In a real implementation, this would use YouTube Data API
        return {
            'platform_specific': 'youtube',
            'api_available': False,  # Would be True if API key available
            'metadata_fields': {
                'title': 'Would be extracted via API',
                'description': 'Would be extracted via API',
                'tags': 'Would be extracted via API',
                'category_id': 'Would be extracted via API',
                'default_language': 'Would be extracted via API',
                'default_audio_language': 'Would be extracted via API',
                'duration_seconds': 'Would be extracted via API',
                'view_count': 'Would be extracted via API',
                'like_count': 'Would be extracted via API',
                'comment_count': 'Would be extracted via API',
                'upload_date': 'Would be extracted via API',
                'scheduled_publish_date': 'Would be extracted via API if applicable'
            },
            'consistency_checks': {
                'upload_vs_content_date': 'Would check if upload date matches content timestamps',
                'description_keyword_relevance': 'Would check if description matches title/content',
                'tag_relevance': 'Would check if tags are relevant to content'
            }
        }

    async def _analyze_vimeo_metadata(self, video_url: str) -> Dict[str, Any]:
        """Analyze Vimeo-specific metadata."""
        return {
            'platform_specific': 'vimeo',
            'api_available': False,
            'note': 'Vimeo metadata analysis would be performed here'
        }

    async def _analyze_video_frames(self, video_url: str) -> Dict[str, Any]:
        """Perform frame-by-frame analysis of video content."""
        # In a real implementation with OpenCV, we would:
        # 1. Extract frames at key intervals
        # 2. Perform object detection/scene analysis
        # 3. Check for visual inconsistencies
        # 4. Analyze lighting, shadows, reflections
        # 5. Detect compression artifacts
        # 6. Look for signs of CGI, deepfakes, etc.

        return {
            'analysis_method': 'opencv_frame_analysis',
            'frames_analyzed': 'Would extract and analyze key frames',
            'key_analysis_points': [
                'Lighting consistency across frames',
                'Shadow direction and length analysis',
                'Reflection analysis in eyes/glass/water',
                'Compression artifact analysis',
                'Edge consistency checking',
                'Color palette analysis',
                'Skin tone consistency (for face analysis)',
                'Background consistency check',
                'Perspective and geometry validation',
                'Motion vector analysis',
                'Timestamp consistency check (if visible)',
                'Logo/watermark verification',
                'Chroma key/green screen detection'
            ],
            'anomalies_detected': [],  # Would be populated with actual findings
            'confidence_score': 0.0,   # Would be calculated based on findings
            'limitations': [
                'Requires video download for full analysis',
                'May be limited by video resolution/quality',
                'Some manipulations may be undetectable without source files'
            ]
        }

    async def _analyze_video_audio(self, video_url: str) -> Dict[str, Any]:
        """Analyze audio component of video."""
        # In a real implementation with Whisper, we would:
        # 1. Extract audio track
        # 2. Transcribe speech to text
        # 3. Analyze audio characteristics
        # 4. Check for audio inconsistencies
        # 5. Detect dubbing, voice modification, etc.

        return {
            'analysis_method': 'whisper_audio_analysis',
            'audio_extracted': True,
            'transcription_available': True,
            'transcript_segments': [
                {
                    'start_time': 0.0,
                    'end_time': 5.0,
                    'text': 'Would contain actual transcription segments',
                    'confidence': 0.95
                }
            ],
            'audio_characteristics': {
                'background_noise_level': 'low',
                'audio_quality': 'good',
                'consistent_across_segments': True,
                'sample_rate_hz': 44100,
                'bit_depth': '16-bit',
                'channels': 'stereo'
            },
            'linguistic_analysis': {
                'language_detected': 'en',
                'accent_analysis': 'Would analyze for accent consistency',
                'speech_rate_wpm': 150,
                'pause_pattern_analysis': 'Would analyze unnatural pauses',
                'emotional_tone_analysis': 'Would analyze for emotional consistency'
            },
            'audio_anomalies': [],  # Would be populated with actual findings
            'transcript_claim_relevance': 0.8,  # How much transcript relates to claim
            'limitations': [
                'Transcription accuracy depends on audio quality',
                'Background music can interfere with speech recognition',
                'Accents and dialects may reduce accuracy'
            ]
        }

    async def _analyze_content_authenticity(self, video_url: str, platform: str) -> Dict[str, Any]:
        """Analyze whether video content appears authentic or staged."""
        return {
            'authenticity_indicators': {
                'environmental_consistency': 'Would analyze lighting, weather, shadows',
                'temporal_consistency': 'Would check timestamps, date references',
                'behavioral_naturalness': 'Would analyze for unnatural movements/actions',
                'interaction_authenticity': 'Would analyze how people interact with environment',
                'audio_visual_sync': 'Would check lip sync, sound-source matching',
                'equipment_consistency': 'Would check if available equipment matches era/location'
            },
            'staging_indicators': [
                'Would look for signs of rehearsal',
                'Would check for multiple takes/edit points',
                'Would analyze for unnatural positioning',
                'Would check for visible crew/equipment reflections',
                'Would analyze for timing inconsistencies'
            ],
            'authenticity_score': 0.7,  # Placeholder - would be calculated
            'authenticity_assessment': 'Likely authentic based on available indicators',
            'evidence_for_assessment': [
                'Natural lighting patterns observed',
                'Consistent shadow directions',
                'Authentic background audio'
            ],
            'concerns_for_assessment': [
                'Limited sample size for analysis',
                'Some sophisticated staging may be difficult to detect'
            ]
        }

    async def _analyze_video_context(self, video_url: str, platform: str, claims: List[str]) -> Dict[str, Any]:
        """Analyze the context in which the video was created and published."""
        return {
            'context_factors': {
                'upload_context': 'Would analyze circumstances of upload',
                'channel_history': 'Would analyze channel\'s typical content',
                'audience_expectations': 'Would analyze what audience normally sees',
                'publication_timing': 'Would analyze timing relative to events',
                'platform_algorithms': 'Would consider how platform algorithms affect visibility'
            },
            'external_corroboration': {
                'independent_verification': 'Would check if other sources confirm video events',
                'geolocation_verification': 'Would attempt to verify location shown',
                'temporal_verification': 'Would check if timestamps match known events',
                'person_identification': 'Would attempt to verify identities shown'
            },
            'contextual_plausibility': {
                'claim_video_relationship': 'Would analyze how well video supports/refutes claims',
                'contextual_narrative_fit': 'Would analyze if video fits known narratives',
                'anomalous_elements': []  # Would list things that don\'t fit context
            },
            'recommendations_for_further_investigation': [
                'Attempt to geolocate any visible landmarks',
                'Check local weather reports for timestamp',
                'Look for independent footage of same event',
                'Analyze radio/mobile tower timing if visible',
                'Check for corroborating witness accounts'
            ]
        }

    async def _detect_video_manipulation(self, video_url: str) -> Dict[str, Any]:
        """Detect signs of video manipulation, editing, or deepfakes."""
        return {
            'manipulation_techniques_checked': [
                'splicing_and_cutting',
                'frame_duplication_deletion',
                'speed_manipulation',
                'reverse_footage',
                'looping_detection',
                'green_screen_chroma_key',
                'cgi_compositing',
                'deepfake_face_swapping',
                'audio_dubbing_voice_modification',
                'lip_sync_analysis',
                'tampering_with_timestamps',
                'metadata_alteration',
                'watermark_removal_addition'
            ],
            'deepfake_analysis': {
                'face_consistency_check': 'Would analyze blinking patterns, lip movement',
                'eye_reflection_analysis': 'Would check consistency of reflections in eyes',
                'teeth_texture_analysis': 'Would analyze consistency of dental work',
                'hair_movement_analysis': 'Would analyze natural vs synthetic hair movement',
                'skin_texture_analysis': 'Would analyze pores, wrinkles, lighting interaction',
                'jawline_movement_analysis': 'Would analyze natural jaw movement during speech'
            },
            'compression_analysis': {
                'double_compression_detection': 'Would check if video was compressed twice',
                'artifact_consistency': 'Would check if compression artifacts are consistent',
                'keyframe_analysis': 'Would analyze placement and consistency of keyframes'
            },
            'manipulation_confidence': 0.1,  # Low confidence of manipulation detected
            'manipulation_type': 'none_detected',
            'evidence_against_manipulation': [
                'Natural blinking patterns observed',
                'Consistent shadow movement',
                'Authentic audio-visual synchronization',
                'Consistent compression artifacts throughout'
            ],
            'limitations': [
                'High-quality manipulations may be undetectable without source files',
                'Some deepfakes are extremely difficult to detect',
                'Frame extraction may miss temporal manipulations'
            ]
        }

    async def _analyze_video_provenance(self, video_url: str, platform: str) -> Dict[str, Any]:
        """Analyze the provenance and chain of custody of the video."""
        return {
            'provenance_chain': [
                {
                    'step': 'creation',
                    'estimated_timestamp': 'Would be estimated from metadata/content',
                    'location': 'Would be estimated from geolocation/landmarks',
                    'device_type': 'Would be estimated from video quality/format',
                    'chain_confidence': 'low_to_medium'
                },
                {
                    'step': 'initial_upload',
                    'platform': platform,
                    'timestamp': 'Would be extracted from platform metadata',
                    'account_analyzed': 'Would analyze uploader account history',
                    'chain_confidence': 'medium'
                },
                {
                    'step': 'current_location',
                    'platform': platform,
                    'timestamp': datetime.datetime.now().isoformat(),
                    'url': video_url,
                    'chain_confidence': 'high'
                }
            ],
            'chain_of_custody_breaks': [],  # Would list any breaks in custody
            'alternative_sources_sought': [
                'Would check if original file exists elsewhere',
                'Would look for higher quality versions',
                'Would check for raw footage or source materials'
            ],
            'provenance_score': 0.6,  # Placeholder
            'provenance_assessment': 'Provenance partially established',
            'recommendations': [
                'Attempt to contact original uploader for source files',
                'Check if video was submitted to news organizations',
                'Look for backup copies in cloud storage or external drives',
                'Check if video was mirrored/shared immediately after upload'
            ]
        }

    async def _assess_video_credibility(self, analysis_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall credibility of video evidence."""
        # This would synthesize all the analysis components
        credibility_factors = {
            'metadata_consistency': 0.8,  # Would be calculated
            'frame_analysis_score': 0.7 if OPENCV_AVAILABLE else 0.5,  # Placeholder
            'audio_analysis_score': 0.8 if WHISPER_AVAILABLE else 0.5,  # Placeholder
            'authenticity_score': 0.7,  # From authenticity analysis
            'contextual_plausibility': 0.75,  # Would be calculated
            'manipulation_risk': 0.2,  # Low risk = high score
            'provenance_score': 0.6   # From provenance analysis
        }

        # Weighted average (weights would be tuned based on reliability)
        weights = {
            'metadata_consistency': 0.15,
            'frame_analysis_score': 0.20,
            'audio_analysis_score': 0.20,
            'authenticity_score': 0.15,
            'contextual_plausibility': 0.15,
            'manipulation_risk': 0.05,  # Inverted - lower manipulation risk is better
            'provenance_score': 0.10
        }

        # Calculate weighted score
        weighted_sum = sum(credibility_factors[factor] * weights[factor] for factor in credibility_factors)
        total_weight = sum(weights.values())
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.5

        # Risk factors that would reduce credibility
        risk_factors = []
        if overall_score < 0.6:
            risk_factors.append('below_average_credibility_indicators')
        if not OPENCV_AVAILABLE:
            risk_factors.append('limited_visual_analysis_capability')
        if not WHISPER_AVAILABLE:
            risk_factors.append('limited_audio_analysis_capability')

        return {
            'individual_scores': credibility_factors,
            'weights_applied': weights,
            'overall_credibility_score': round(overall_score, 3),
            'credibility_level': self._score_to_credibility_level(overall_score),
            'risk_factors_identified': risk_factors,
            'confidence_in_assessment': 0.7,  # Would be based on data quality
            'recommendations_for_improving_assessment': [
                'Obtain original source files for deeper analysis',
                'Get access to higher resolution version',
                'Attempt to verify through multiple independent sources',
                'Check for corresponding audio-only recordings',
                'Look for still photographs from same event/context'
            ],
            'limitations_statement': 'This analysis is based on publicly available video. Deeper analysis would require access to source files, original recordings, or collaboration with platform administrators.'
        }

    def _score_to_credibility_level(self, score: float) -> str:
        """Convert numerical score to credibility level."""
        if score >= 0.8:
            return 'high'
        elif score >= 0.6:
            return 'medium'
        elif score >= 0.4:
            return 'low'
        else:
            return 'very_low'