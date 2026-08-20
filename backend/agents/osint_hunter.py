from .base_agent import BaseAgent, AgentResult
from typing import Dict, Any, List
import datetime
import sys
import os
import logging
from urllib.parse import urlparse, parse_qs
import hashlib

# Add the backend directory to the path to import snapshotter and cost tracker
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'evidence'))
from snapshot import snapshotter

# Import cost tracker for observability
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
from observability.cost_tracker import cost_tracker

logger = logging.getLogger(__name__)

# Try to import additional libraries for enhanced OSINT capabilities
try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False
    logger.warning("yt-dlp not installed. Video platform support will be limited.")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("Requests not installed. HTTP capabilities will be limited.")

class OSINTHunterAgent(BaseAgent):
    """Hunts for provenance across web, social media, video platforms, and hidden sources."""

    def __init__(self):
        super().__init__("OSINTHunter")
        self.session = None
        if REQUESTS_AVAILABLE:
            import requests
            self.session = requests.Session()
            # Set a realistic user agent
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Input: {'claims': List[str]}
        Output: {'provenance': List[Dict]} with comprehensive snapshot URLs and metadata
        """
        try:
            claims = input_data.get('claims', [])
            if not claims:
                return AgentResult(success=False, error="No claims to hunt")

            provenance = []
            for i, claim in enumerate(claims):
                # Enhanced provenance hunting with multiple source types
                claim_provenance = await self._hunt_comprehensive_provenance(claim, i)
                provenance.extend(claim_provenance)

            return AgentResult(
                success=True,
                data={'provenance': provenance}
            )
        except Exception as e:
            logger.error(f"OSINT hunter error: {e}")
            return AgentResult(success=False, error=str(e))

    async def _hunt_comprehensive_provenance(self, claim: str, claim_index: int) -> List[Dict]:
        """Hunt for provenance across multiple source types with forensic-level detail."""
        provenance_entries = []

        # 1. Surface web & social media (enhanced)
        surface_web_results = await self._hunt_surface_web(claim, claim_index)
        provenance_entries.extend(surface_web_results)

        # 2. Video platforms
        video_results = await self._hunt_video_platforms(claim, claim_index)
        provenance_entries.extend(video_results)

        # 3. Spread/content amplification tracking
        spread_results = await self._hunt_spread_patterns(claim, claim_index)
        provenance_entries.extend(spread_results)

        # 4. Hidden/deep web sources (placeholder for demonstration)
        hidden_results = await self._hunt_hidden_sources(claim, claim_index)
        provenance_entries.extend(hidden_results)

        # 5. Historical/archival sources
        historical_results = await self._hunt_historical_sources(claim, claim_index)
        provenance_entries.extend(historical_results)

        return provenance_entries

    async def _hunt_surface_web(self, claim: str, claim_index: int) -> List[Dict]:
        """Enhanced surface web and social media hunting."""
        # In a real implementation, this would use search APIs, social media APIs, etc.
        # For now, we'll return enhanced mock data that shows the structure

        platforms = [
            {'name': 'Twitter/X', 'url_pattern': 'https://twitter.com/search?q={}', 'icon': '🐦'},
            {'name': 'Reddit', 'url_pattern': 'https://www.reddit.com/search/?q={}', 'icon': '👽'},
            {'name': 'Facebook', 'url_pattern': 'https://www.facebook.com/search/posts/?q={}', 'icon': '📘'},
            {'name': 'Instagram', 'url_pattern': 'https://www.instagram.com/explore/tags/{}', 'icon': '📸'},
            {'name': 'TikTok', 'url_pattern': 'https://www.tiktok.com/search?q={}', 'icon': '🎵'},
            {'name': 'LinkedIn', 'url_pattern': 'https://www.linkedin.com/search/results/content/?keywords={}', 'icon': '💼'},
            {'name': 'Telegram', 'url_pattern': 'https://t.me/s/{}', 'icon': '💬'},
            {'name': '4chan', 'url_pattern': 'https://archive.4plebs.org/_/search/?q={}', 'icon': '💣'},
        ]

        results = []
        for platform in platforms:
            # Simulate finding content on this platform
            earliest_mention = {
                'timestamp': (datetime.datetime.now() - datetime.timedelta(days=2+claim_index)).isoformat(),
                'platform': platform['name'],
                'handle': f'{platform["name"].lower()}_user_{claim_index}',
                'url': platform['url_pattern'].format(claim.replace(' ', '+')[:50]),
                'content_type': 'text_post',
                'engagement': {
                    'likes': 10 + claim_index * 5,
                    'shares': 5 + claim_index * 2,
                    'comments': 3 + claim_index
                },
                'geotag': None,  # Would be populated if available
                'language_detected': 'en'
            }

            # Add snapshot URL for earliest mention
            earliest_mention['snapshot_url'] = snapshotter.snapshot(earliest_mention['url'])

            # Amplification events (where content went viral or was shared by influential accounts)
            amplification_events = []
            for amp_index in range(2):  # Simulate 2 amplification events
                event_time = datetime.datetime.now() - datetime.timedelta(hours=6+amp_index*3, days=claim_index)
                amplification_events.append({
                    'timestamp': event_time.isoformat(),
                    'platform': platform['name'],
                    'event_type': 'amplification',
                    'amplifier_type': 'influencer' if amp_index == 0 else 'news_outlet',
                    'amplifier_handle': f'amplifier_{amp_index}_{claim_index}',
                    'amplifier_followers': 10000 * (amp_index + 1),
                    'url': f"https://{platform['name'].lower()}.com/post/amp{amp_index}_{claim_index}",
                    'reach_estimate': 50000 + amp_index * 100000,
                    'added_context': f"Amplified with commentary: {['Breaking:', 'Update:', 'Analysis:'][amp_index]} {claim[:30]}..."
                })
                # Add snapshot URL for amplification event
                amplification_events[amp_index]['snapshot_url'] = snapshotter.snapshot(amplification_events[amp_index]['url'])

            results.append({
                'claim': claim,
                'source_type': 'surface_web_social',
                'platform': platform['name'],
                'earliest_mention': earliest_mention,
                'amplification_events': amplification_events,
                'total_estimated_reach': sum(event.get('reach_estimate', 0) for event in amplification_events),
                'first_seen_platform': platform['name'],
                'initial_virality_score': self._calculate_virality_score(earliest_mention, amplification_events)
            })

        return results

    async def _hunt_video_platforms(self, claim: str, claim_index: int) -> List[Dict]:
        """Hunt for video content related to the claim across platforms."""
        if not YT_DLP_AVAILABLE:
            logger.warning("yt-dlp not available, skipping video platform search")
            return []

        video_platforms = [
            {'name': 'YouTube', 'url_pattern': 'https://www.youtube.com/results?search_query={}', 'icon': '▶️'},
            {'name': 'Vimeo', 'url_pattern': 'https://vimeo.com/search?q={}', 'icon': '🎥'},
            {'name': 'Dailymotion', 'url_pattern': 'https://www.dailymotion.com/search/{}', 'icon': '📺'},
            {'name': 'TikTok', 'url_pattern': 'https://www.tiktok.com/search?q={}', 'icon': '🎵'},  # Also in social but video-focused
            {'name': 'Twitch', 'url_pattern': 'https://www.twitch.tv/search?term={}', 'icon': '🟣'},
        ]

        results = []
        for platform in video_platforms:
            # Simulate finding video content
            video_results = []
            for video_index in range(2):  # Simulate 2 videos found
                video_id = f"vid{platform['name'].lower()}{claim_index}{video_index}"
                video_url = f"https://{platform['name'].lower()}.com/watch?v={video_id}" if platform['name'] != 'YouTube' else f"https://www.youtube.com/watch?v={video_id}"

                # Try to get actual video metadata if possible (in real implementation)
                video_metadata = await self._extract_video_metadata(video_url, platform['name'])

                video_entry = {
                    'timestamp': (datetime.datetime.now() - datetime.timedelta(days=1+video_index, hours=claim_index*2)).isoformat(),
                    'platform': platform['name'],
                    'channel_name': f"{platform['name']}_Channel_{claim_index}",
                    'channel_verified': video_index == 0,  # First video from verified channel
                    'channel_subscribers': 50000 + video_index * 25000,
                    'video_title': f"{['Exposing:', 'Investigation:', 'Analysis:'][video_index]} {claim}",
                    'video_description': f"A detailed video examination of the claim: '{claim}'. This video explores various angles and presents evidence.",
                    'duration_seconds': 300 + video_index * 180,  # 5-8 minutes
                    'view_count': 1000 + video_index * 5000,
                    'like_count': 50 + video_index * 200,
                    'dislike_count': 5 + video_index * 20,
                    'comment_count': 10 + video_index * 50,
                    'upload_location': None,  # Would be populated if available
                    'language': 'en',
                    'tags': [claim.split()[0] if claim.split() else 'topic', 'investigation', 'news'],
                    'url': video_url,
                    'content_type': 'video',
                    'transcript_available': video_index == 0,  # First video has transcript
                    'automatic_captions': True,
                }

                # Add snapshot URL for video page (would snapshot the video page, not the video itself)
                video_entry['snapshot_url'] = snapshotter.snapshot(video_entry['url'])

                # If we have transcript available, we might also snapshot or store key portions
                if video_entry['transcript_available']:
                    # In a real implementation, we might extract and store transcript snippets
                    video_entry['transcript_snippet'] = f"This video examines the claim '{claim}' and presents evidence from multiple sources..."

                video_results.append(video_entry)

            if video_results:  # Only add if we found videos
                results.append({
                    'claim': claim,
                    'source_type': 'video_platform',
                    'platform': platform['name'],
                    'videos': video_results,
                    'total_views': sum(v['view_count'] for v in video_results),
                    'total_engagement': sum(v['like_count'] + v['comment_count'] for v in video_results),
                    'earliest_video_date': min(v['timestamp'] for v in video_results),
                    'geographic_distribution': self._estimate_geographic_distribution(video_results)
                })

        return results

    async def _extract_video_metadata(self, video_url: str, platform: str) -> Dict[str, Any]:
        """Extract metadata from video URL using available tools."""
        # In a real implementation with yt-dlp, we would extract actual metadata
        # For now, return empty dict as placeholder
        if not YT_DLP_AVAILABLE:
            return {}

        try:
            # This would be implemented with yt-dlp in a real scenario
            # For demonstration, we'll just return basic info
            parsed_url = urlparse(video_url)
            video_id = parse_qs(parsed_url.query).get('v', ['unknown'])[0] if 'youtube.com' in parsed_url.netloc else 'unknown'
            return {
                'video_id': video_id,
                'platform': platform,
                'extraction_method': 'yt_dlp_placeholder'
            }
        except Exception as e:
            logger.debug(f"Could not extract metadata from {video_url}: {e}")
            return {}

    async def _hunt_spread_patterns(self, claim: str, claim_index: int) -> List[Dict]:
        """Hunt for how the claim spread across networks and platforms."""
        # This would analyze propagation patterns, network graphs, etc.
        # For demonstration, we'll return enhanced mock data

        # Simulate tracking how the claim spread from origin to various communities
        origin_communities = [
            {'name': 'Alternative Health Forum', 'type': 'forum', 'risk_score': 0.8},
            {'name': 'Political Discussion Board', 'type': 'forum', 'risk_score': 0.6},
            {'name': 'Science Enthusiasts Group', 'type': 'social_group', 'risk_score': 0.2},
            {'name': 'Mainstream News Commentary', 'type': 'news_site', 'risk_score': 0.3},
        ]

        spread_waves = []
        base_time = datetime.datetime.now() - datetime.timedelta(days=3)

        for wave_index, community in enumerate(origin_communities):
            wave_time = base_time + datetime.timedelta(hours=wave_index*4)

            # Simulate how it spread from this community to others
            secondary_spread = []
            for target_wave in range(wave_index + 1, min(wave_index + 3, len(origin_communities))):
                target_community = origin_communities[target_wave]
                spread_time = wave_time + datetime.timedelta(hours=2+(target_wave-wave_index)*3)

                secondary_spread.append({
                    'source_community': community['name'],
                    'target_community': target_community['name'],
                    'spread_timestamp': spread_time.isoformat(),
                    'spread_mechanism': ['cross_posting', 'referral_link', 'quote_tweet', 'screenshot_share'][
                        (target_wave - wave_index) % 4
                    ],
                    'amplification_factor': 1.5 + (target_wave - wave_index) * 0.3,
                    'context_modification': f"Adapted for {target_community['name']} audience"
                })

            spread_waves.append({
                'wave_number': wave_index + 1,
                'origin_community': community['name'],
                'community_type': community['type'],
                'initial_timestamp': wave_time.isoformat(),
                'initial_engagement': {
                    'views': 100 + wave_index * 50,
                    'interactions': 20 + wave_index * 10,
                    'shares': 5 + wave_index * 3
                },
                'risk_assessment': community['risk_score'],
                'secondary_spread': secondary_spread,
                'meso_level_spread': True  # Indicates spread between communities
            })

        return [{
            'claim': claim,
            'source_type': 'spread_analysis',
            'analysis_type': 'network_propagation',
            'origin_identified': True,
            'patient_zero_community': origin_communities[0]['name'] if origin_communities else 'Unknown',
            'spread_waves': spread_waves,
            'total_hops': sum(len(wave['secondary_spread']) for wave in spread_waves),
            'geographic_spread_pattern': self._analyze_geographic_spread(spread_waves),
            'temporal_virality_curve': self._generate_virality_curve(spread_waves),
            'network_resilience_score': self._calculate_network_resilience(spread_waves)
        }]

    async def _hunt_hidden_sources(self, claim: str, claim_index: int) -> List[Dict]:
        """Hunt for hidden/deep web sources (placeholder for demonstration)."""
        # In a real implementation, this might involve:
        # - Tor/onion site search (with proper safeguards)
        # - Private forum monitoring
        # - Encrypted channel analysis
        # - Pastebin/dumpsite monitoring
        # - Dark web marketplace observation
        # - Leaked data repository scanning

        # For demonstration, we'll return structured placeholder data
        hidden_platforms = [
            {'name': 'Pastebin/Text Storage Sites', 'risk_level': 'medium', 'content_types': ['logs', 'configs', 'pastes']},
            {'name': 'Internet Archives & Wayback Machine Variants', 'risk_level': 'low', 'content_types': ['historical_pages', 'removed_content']},
            {'name': 'Academic Repository Preprints', 'risk_level': 'low', 'content_types': ['papers', 'datasets', 'supplementary_materials']},
            {'name': 'Government/NGO Document Repositories', 'risk_level': 'low', 'content_types': ['reports', 'datasets', 'meeting_minutes']},
            {'name': 'Special Interest Forums (Requires Registration)', 'risk_level': 'medium', 'content_types': ['discussions', 'manuals', 'guides']},
            # Note: Actual dark web/Tor search would require special handling and ethical considerations
        ]

        results = []
        for platform in hidden_platforms:
            # Simulate finding something in this hidden source
            found_items = []
            for item_index in range(1 if platform['risk_level'] == 'low' else 2):  # More items from lower risk sources
                item_time = datetime.datetime.now() - datetime.timedelta(days=1+item_index, hours=claim_index)

                found_items.append({
                    'discovery_timestamp': item_time.isoformat(),
                    'platform': platform['name'],
                    'content_type': platform['content_types'][item_index % len(platform['content_types'])],
                    'content_hash': hashlib.sha256(f"{claim}_{platform['name']}_{item_index}".encode()).hexdigest()[:16],
                    'access_method': ['direct_link', 'api', 'scraping', 'search'][item_index % 4],
                    'content_snippet': f"Content related to '{claim}' found in {platform['name']}...",
                    'source_reliability': self._assess_source_reliability(platform['name']),
                    'corroboration_level': ['none', 'weak', 'moderate', 'strong'][item_index % 4],
                    'potential_biases': self._identify_potential_biases(platform['name'])
                })

                # Add snapshot URL if applicable (for web-accessible hidden sources)
                if 'archive' in platform['name'].lower() or 'wayback' in platform['name'].lower():
                    found_items[item_index]['snapshot_url'] = snapshotter.snapshot(
                        f"https://example.com/hidden/{platform['name'].lower().replace(' ', '_')}/{item_index}"
                    )

            if found_items:
                results.append({
                    'claim': claim,
                    'source_type': 'hidden_deep_web',
                    'platform_category': platform['name'],
                    'risk_level': platform['risk_level'],
                    'items_found': found_items,
                    'total_items': len(found_items),
                    'date_range': {
                        'earliest': min(item['discovery_timestamp'] for item in found_items),
                        'latest': max(item['discovery_timestamp'] for item in found_items)
                    },
                    'access_difficulty': self._assess_access_difficulty(platform['name']),
                    'legal_considerations': self._get_legal_considerations(platform['name'])
                })

        return results

    async def _hunt_historical_sources(self, claim: str, claim_index: int) -> List[Dict]:
        """Hunt for historical mentions and similar past claims."""
        # This would check historical databases, news archives, etc.
        historical_periods = [
            {'period': 'Recent (last 30 days)', 'days_back': 30, 'sources': ['news', 'social_media', 'blogs']},
            {'period': 'Months (2-6 months ago)', 'days_back': 180, 'sources': ['news_archives', 'academic_journals']},
            {'period': 'Yearly (6-18 months ago)', 'days_back': 540, 'sources': ['historical_news', 'books', 'reports']},
            {'period': 'Historical (pre-digital era)', 'days_back': 3650, 'sources': ['newspaper_archives', 'microfilm', 'library_collections']}
        ]

        results = []
        for period in historical_periods:
            # Simulate finding historical mentions
            mentions_found = []
            for mention_index in range(2):  # Simulate 2 mentions per period
                mention_date = datetime.datetime.now() - datetime.timedelta(
                    days=period['days_back'] - (mention_index * 30)
                )

                mentions_found.append({
                    'mention_date': mention_date.isoformat(),
                    'source_type': period['sources'][mention_index % len(period['sources'])],
                    'source_name': f"Historical Source {mention_index + 1} for {period['period']}",
                    'content_snippet': f"Historical discussion of similar themes to: '{claim[:50]}...'",
                    'context_notes': f"This appears in the context of {['recent events', 'ongoing debates', 'cyclical discussions', 'historical patterns'][mention_index % 4]}",
                    'similarity_score': 0.6 + mention_index * 0.2,  # How similar to current claim
                    'verification_status': ['unverified', 'partially_verified', 'verified', 'contradicted'][mention_index % 4],
                    'access_url': f"https://historical-archive.example.com/{period['period'].lower().replace(' ', '_')}/{mention_index}",
                })

                # Add snapshot for accessible historical sources
                if 'archive' in mentions_found[mention_index]['access_url']:
                    mentions_found[mention_index]['snapshot_url'] = snapshotter.snapshot(
                        mentions_found[mention_index]['access_url']
                    )

            if mentions_found:
                results.append({
                    'claim': claim,
                    'source_type': 'historical_analysis',
                    'time_period': period['period'],
                    'days_back': period['days_back'],
                    'mentions_found': mentions_found,
                    'total_mentions': len(mentions_found),
                    'earliest_mention': min(m['mention_date'] for m in mentions_found),
                    'latest_mention': max(m['mention_date'] for m in mentions_found),
                    'trend_analysis': self._analyze_historical_trend(mentions_found),
                    'recurrence_pattern': self._identify_recurrence_pattern(mentions_found),
                    'historical_veracity_rate': self._calculate_historical_veracity(mentions_found)
                })

        return results

    # Helper methods for analysis
    def _calculate_virality_score(self, earliest_mention: Dict, amplification_events: List[Dict]) -> float:
        """Calculate a virality score based on engagement metrics."""
        base_score = earliest_mention.get('engagement', {}).get('likes', 0) * 0.1
        base_score += earliest_mention.get('engagement', {}).get('shares', 0) * 0.3
        base_score += earliest_mention.get('engagement', {}).get('comments', 0) * 0.2

        amp_score = sum(event.get('reach_estimate', 0) for event in amplification_events) * 0.01
        return min(base_score + amp_score, 100.0)  # Cap at 100

    def _estimate_geographic_distribution(self, video_results: List[Dict]) -> Dict[str, float]:
        """Estimate geographic distribution of video views."""
        # In reality, this would come from analytics
        return {
            'North America': 0.35,
            'Europe': 0.25,
            'Asia': 0.25,
            'Other': 0.15
        }

    def _assess_source_reliability(self, platform_name: str) -> float:
        """Assess reliability of a source platform."""
        reliability_scores = {
            'Academic Repository Preprints': 0.8,
            'Government/NGO Document Repositories': 0.75,
            'Internet Archives & Wayback Machine Variants': 0.7,
            'Pastebin/Text Storage Sites': 0.4,
            'Special Interest Forums (Requires Registration)': 0.5
        }
        return reliability_scores.get(platform_name, 0.5)

    def _identify_potential_biases(self, platform_name: str) -> List[str]:
        """Identify potential biases in a source platform."""
        bias_map = {
            'Academic Repository Preprints': ['publication_bias', 'funding_source_bias'],
            'Government/NGO Document Repositories': ['institutional_bias', 'agenda_bias'],
            'Internet Archives & Wayback Machine Variants': ['selection_bias', 'digital_divide_bias'],
            'Pastebin/Text Storage Sites': ['self_selection_bias', 'anonymity_bias'],
            'Special Interest Forums (Requires Registration)': ['homophily_bias', 'echo_chamber_bias']
        }
        return bias_map.get(platform_name, ['unknown_bias'])

    def _assess_access_difficulty(self, platform_name: str) -> str:
        """Assess how difficult it is to access a platform."""
        difficulty_map = {
            'Academic Repository Preprints': 'medium',  # May require institutional access,
            'Government/NGO Document Repositories': 'low',  # Usually public
            'Internet Archives & Wayback Machine Variants': 'low',  # Publicly accessible
            'Pastebin/Text Storage Sites': 'low',  # Usually public
            'Special Interest Forums (Requires Registration)': 'high',  # Requires registration, possibly vetting
        }
        return difficulty_map.get(platform_name, 'unknown')

    def _get_legal_considerations(self, platform_name: str) -> List[str]:
        """Get legal considerations for accessing a platform."""
        considerations_map = {
            'Academic Repository Preprints': ['copyright', 'data_use_agreements'],
            'Government/NGO Document Repositories': ['public_domain', 'foia_restrictions'],
            'Internet Archives & Wayback Machine Variants': ['copyright', 'terms_of_service'],
            'Pastebin/Text Storage Sites': ['copyright', 'privacy', 'terms_of_service'],
            'Special Interest Forums (Requires Registration)': ['terms_of_service', 'privacy', 'consent']
        }
        return considerations_map.get(platform_name, ['general_legal_compliance'])

    def _analyze_geographic_spread(self, spread_waves: List[Dict]) -> Dict[str, Any]:
        """Analyze geographic patterns in spread."""
        return {
            'primary_hemisphere': 'Northern',
            'urban_rural_ratio': '2:1 urban:rural',
            'cross_border_spread': True,
            'language_barriers_overcome': ['English to Spanish', 'English to French']
        }

    def _generate_virality_curve(self, spread_waves: List[Dict]) -> List[Dict]:
        """Generate a temporal virality curve."""
        curve = []
        base_time = datetime.datetime.now() - datetime.timedelta(days=3)

        for i, wave in enumerate(spread_waves):
            point_time = base_time + datetime.timedelta(hours=i*6)
            curve.append({
                'timestamp': point_time.isoformat(),
                'intensity_score': len(wave.get('secondary_spread', [])) * 10 + 20,
                'reach_estimate': sum(
                    event.get('amplification_factor', 1) * 1000
                    for event in wave.get('secondary_spread', [])
                )
            })
        return curve

    def _calculate_network_resilience(self, spread_waves: List[Dict]) -> float:
        """Calculate how resistant the network is to containment efforts."""
        # Higher score = more resistant to takedown/deplatforming
        base_resilience = 0.3
        for wave in spread_waves:
            base_resilience += len(wave.get('secondary_spread', [])) * 0.1
            base_resilience += wave.get('risk_assessment', 0.5) * 0.2
        return min(base_resilience, 1.0)

    def _analyze_historical_trend(self, mentions: List[Dict]) -> Dict[str, Any]:
        """Analyze historical trends in mentions."""
        if not mentions:
            return {'trend': 'insufficient_data'}

        # Sort by date
        sorted_mentions = sorted(mentions, key=lambda x: x['mention_date'])

        # Calculate frequency over time
        return {
            'trend': 'increasing' if len(mentions) > 1 else 'stable',
            'frequency_per_month': len(mentions) / max(1, (datetime.datetime.now() - datetime.datetime.fromisoformat(sorted_mentions[0]['mention_date'])).days / 30),
            'peek_period': sorted_mentions[-1]['mention_date'] if mentions else None,
            'decay_pattern': None  # Would be calculated with more data
        }

    def _identify_recurrence_pattern(self, mentions: List[Dict]) -> str:
        """Identify if the claim follows a recurrence pattern."""
        if len(mentions) < 2:
            return 'insufficient_data_for_pattern'

        # Simple check for periodicity (would be more sophisticated in reality)
        return 'aperiodic_occasional'  # Placeholder

    def _calculate_historical_veracity(self, mentions: List[Dict]) -> float:
        """Calculate historical accuracy rate of similar claims."""
        if not mentions:
            return 0.5  # Neutral assumption

        veracity_map = {
            'unverified': 0.0,
            'partially_verified': 0.5,
            'verified': 1.0,
            'contradicted': 0.0
        }

        total_veracity = sum(veracity_map.get(m.get('verification_status', 'unverified'), 0.0) for m in mentions)
        return total_veracity / len(mentions)