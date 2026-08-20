from .base_agent import BaseAgent, AgentResult
from typing import Dict, Any, List
import sys
import os

# Add the backend directory to the path to import snapshotter
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'evidence'))
from snapshot import snapshotter

class FactCheckAgent(BaseAgent):
    """Cross-references claims with fact-checking registries and archives."""

    def __init__(self):
        super().__init__("FactChecker")

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Input: {'claims': List[str], 'provenance': List[Dict]}
        Output: {'fact_check_results': List[Dict]} with snapshot URLs added
        """
        try:
            claims = input_data.get('claims', [])
            provenance = input_data.get('provenance', [])
            if not claims:
                return AgentResult(success=False, error="No claims to check")

            results = []
            for claim in claims:
                # Mock fact-check result
                sources = [
                    {'name': 'Snopes', 'url': 'https://snopes.com/fact-check/example', 'rating': 'Mixture'},
                    {'name': 'Reuters Fact Check', 'url': 'https://www.reuters.com/fact-check/example', 'rating': 'False'}
                ]

                # Add snapshot URLs for sources
                for source in sources:
                    source['snapshot_url'] = snapshotter.snapshot(source['url'])

                archival_snapshots = [
                    {'timestamp': '2026-08-10T08:00:00Z', 'url': 'https://web.archive.org/web/20260810080000/https://example.com/original'}
                ]

                # Add snapshot URLs for archival snapshots
                for snapshot in archival_snapshots:
                    snapshot['snapshot_url'] = snapshotter.snapshot(snapshot['url'])

                results.append({
                    'claim': claim,
                    'verdict': 'MISLEADING',
                    'confidence': 0.78,
                    'sources': sources,
                    'archival_snapshots': archival_snapshots
                })

            return AgentResult(
                success=True,
                data={'fact_check_results': results}
            )
        except Exception as e:
            return AgentResult(success=False, error=str(e))