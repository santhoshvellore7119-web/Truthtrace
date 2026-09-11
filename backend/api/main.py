from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import asyncio
import logging

logger = logging.getLogger(__name__)

from agents.claim_extractor import ClaimExtractorAgent
from agents.osint_hunter import OSINTHunterAgent
from agents.social_hunter import SocialHunterAgent
from agents.wayback_agent import WaybackAgent
from agents.fact_checker import FactCheckAgent
from agents.narrative_profiler import NarrativeProfilerAgent
from agents.red_team_auditor import RedTeamAuditorAgent
from agents.attribution_agent import AttributionAgent
from agents.video_analyst import VideoAnalystAgent
from agents.synthesizer import SynthesizerAgent
from models.schemas import Dossier

app = FastAPI(
    title="TruthTrace Forensic Intelligence API",
    description="Multi-agent forensic pipeline for tracing misinformation narratives back to Patient Zero.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    claim: Optional[str] = None
    url: Optional[str] = None

@app.post("/analyze", response_model=Dossier)
async def analyze_claim(request: AnalyzeRequest):
    """
    Analyze a claim or URL using the comprehensive multi-agent forensic pipeline.
    """
    if not request.claim and not request.url:
        raise HTTPException(status_code=400, detail="Either claim or url must be provided")

    # Initialize all specialized agents
    claim_extractor = ClaimExtractorAgent()
    osint_hunter = OSINTHunterAgent()
    social_hunter = SocialHunterAgent()
    wayback_agent = WaybackAgent()
    fact_checker = FactCheckAgent()
    narrative_profiler = NarrativeProfilerAgent()
    red_team_auditor = RedTeamAuditorAgent()
    attribution_agent = AttributionAgent()
    video_analyst = VideoAnalystAgent()
    synthesizer = SynthesizerAgent()

    # Step 1: Claim Extraction & Normalization
    claim_input = {}
    if request.claim:
        claim_input['claim'] = request.claim
    if request.url:
        claim_input['url'] = request.url

    claim_result = await claim_extractor.execute(claim_input)
    if not claim_result.success:
        raise HTTPException(status_code=500, detail=f"Claim extraction failed: {claim_result.error}")

    claims_data = claim_result.data
    if not claims_data or 'claims' not in claims_data:
        raise HTTPException(status_code=500, detail="No claims extracted")

    claims_list = claims_data.get('claims', [])

    # Step 2: Parallel Web & Social Media Hunting (GDELT, NewsAPI, Reddit, Telegram)
    osint_task = osint_hunter.execute(claims_data)
    social_task = social_hunter.execute(claims_data)

    osint_result, social_result = await asyncio.gather(osint_task, social_task, return_exceptions=True)

    osint_data = osint_result.data if isinstance(osint_result, object) and getattr(osint_result, 'success', False) else {'provenance': [], 'raw_sources': {}}
    social_data = social_result.data if isinstance(social_result, object) and getattr(social_result, 'success', False) else {'social_provenance': []}

    provenance_list = osint_data.get('provenance', [])
    social_provenance_list = social_data.get('social_provenance', [])
    combined_provenance = provenance_list + social_provenance_list

    # Step 3: Historical Archival Snapshots (Wayback CDX API)
    discovered_urls = [p.get('url') for p in combined_provenance if p.get('url')]
    wayback_result = await wayback_agent.execute({'urls': discovered_urls, 'provenance': combined_provenance})
    wayback_snapshots = wayback_result.data.get('snapshots', {}) if getattr(wayback_result, 'success', False) else {}

    # Step 4: Fact Checker & Narrative Profiler in Parallel
    fact_check_input = {
        'claims': claims_list,
        'provenance': combined_provenance,
        'raw_sources': osint_data.get('raw_sources', {})
    }
    narrative_input = {
        'claims': claims_list,
        'fact_check_results': []
    }

    fact_check_result = await fact_checker.execute(fact_check_input)
    fact_check_data = fact_check_result.data if getattr(fact_check_result, 'success', False) else {'fact_check_results': []}

    narrative_input['fact_check_results'] = fact_check_data.get('fact_check_results', [])
    narrative_result = await narrative_profiler.execute(narrative_input)
    narrative_data = narrative_result.data if getattr(narrative_result, 'success', False) else {'narrative_analysis': {}}

    # Step 5: Red-Team Auditing, Attribution & Video Forensics in Parallel
    red_team_audit_input = {
        'provenance': combined_provenance,
        'fact_check_results': fact_check_data.get('fact_check_results', []),
        'narrative_analysis': narrative_data.get('narrative_analysis', {})
    }
    attribution_input = {
        'provenance': provenance_list,
        'social_provenance': social_provenance_list
    }
    video_input = {
        'claims': claims_list,
        'url': request.url,
        'provenance': combined_provenance
    }

    red_team_task = red_team_auditor.execute(red_team_audit_input)
    attribution_task = attribution_agent.execute(attribution_input)
    video_task = video_analyst.execute(video_input)

    red_team_res, attr_res, video_res = await asyncio.gather(
        red_team_task, attribution_task, video_task, return_exceptions=True
    )

    red_team_audit_data = red_team_res.data if isinstance(red_team_res, object) and getattr(red_team_res, 'success', False) else {'red_team_audit': {}}
    attribution_data = attr_res.data if isinstance(attr_res, object) and getattr(attr_res, 'success', False) else {'attribution': {}}
    video_data = video_res.data if isinstance(video_res, object) and getattr(video_res, 'success', False) else {'video_forensics': {}}

    # Step 6: Final Synthesis & Cluster Extraction
    synthesizer_input = {
        'claims': claims_list,
        'provenance': provenance_list,
        'social_provenance': social_provenance_list,
        'wayback_snapshots': wayback_snapshots,
        'fact_check_results': fact_check_data.get('fact_check_results', []),
        'narrative_analysis': narrative_data.get('narrative_analysis', {}),
        'red_team_audit': red_team_audit_data.get('red_team_audit', {}),
        'attribution': attribution_data.get('attribution', {}),
        'video_forensics': video_data.get('video_forensics', {})
    }

    synthesizer_result = await synthesizer.execute(synthesizer_input)
    if not synthesizer_result.success:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {synthesizer_result.error}")

    return synthesizer_result.data

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)