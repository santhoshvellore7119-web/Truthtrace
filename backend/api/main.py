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
from agents.fact_checker import FactCheckAgent
from agents.narrative_profiler import NarrativeProfilerAgent
from agents.red_team_auditor import RedTeamAuditorAgent
from agents.video_analyst import VideoAnalystAgent
from agents.synthesizer import SynthesizerAgent
from models.schemas import Dossier

app = FastAPI(title="TruthTrace API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    claim: Optional[str] = None
    url: Optional[str] = None

@app.post("/analyze", response_model=Dossier)
async def analyze_claim(request: AnalyzeRequest):
    """
    Analyze a claim or URL using the multi-agent pipeline with forensic video analysis.
    """
    if not request.claim and not request.url:
        raise HTTPException(status_code=400, detail="Either claim or url must be provided")

    # Initialize agents
    claim_extractor = ClaimExtractorAgent()
    osint_hunter = OSINTHunterAgent()
    fact_checker = FactCheckAgent()
    narrative_profiler = NarrativeProfilerAgent()
    red_team_auditor = RedTeamAuditorAgent()
    video_analyst = VideoAnalystAgent()
    synthesizer = SynthesizerAgent()

    # Step 1: Extract claims
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

    # Step 2: Hunt for provenance
    osint_result = await osint_hunter.execute(claims_data)
    if not osint_result.success:
        # Continue with empty provenance rather than failing
        osint_data = {'provenance': []}
    else:
        osint_data = osint_result.data

    # Step 3: Fact check
    fact_check_input = {
        'claims': claims_data.get('claims', []),
        'provenance': osint_data.get('provenance', [])
    }
    fact_check_result = await fact_checker.execute(fact_check_input)
    if not fact_check_result.success:
        fact_check_data = {'fact_check_results': []}
    else:
        fact_check_data = fact_check_result.data

    # Step 4: Narrative profiling
    narrative_input = {
        'claims': claims_data.get('claims', []),
        'fact_check_results': fact_check_data.get('fact_check_results', [])
    }
    narrative_result = await narrative_profiler.execute(narrative_input)
    if not narrative_result.success:
        narrative_data = {'narrative_analysis': {}}
    else:
        narrative_data = narrative_result.data

    # Step 4.5: Red-Team Auditing
    red_team_audit_input = {
        'provenance': osint_data.get('provenance', []),
        'fact_check_results': fact_check_data.get('fact_check_results', []),
        'narrative_analysis': narrative_data.get('narrative_analysis', {})
    }
    red_team_audit_result = await red_team_auditor.execute(red_team_audit_input)
    if not red_team_audit_result.success:
        # Continue with empty audit rather than failing
        red_team_audit_data = {'red_team_audit': {}}
    else:
        red_team_audit_data = red_team_audit_result.data

    # Step 5: Video Forensic Analysis (NEW)
    # Only run video analysis if we have claims that might benefit from video content
    video_analysis_data = {'video_analysis': []}
    try:
        # In a full implementation, we might intelligently decide when to run video analysis
        # For now, we'll run it on all analyses to demonstrate the capability
        video_input = {
            'claims': claims_data.get('claims', []),
            # We could also pass specific video URLs if we had them from OSINT hunting
        }
        video_result = await video_analyst.execute(video_input)
        if video_result.success:
            video_analysis_data = video_result.data
        else:
            logger.warning(f"Video analysis failed: {video_result.error}")
            video_analysis_data = {'video_analysis': []}
    except Exception as e:
        logger.warning(f"Video analysis error: {e}")
        video_analysis_data = {'video_analysis': []}

    # Step 6: Synthesize results
    synthesizer_input = {
        'claims': claims_data.get('claims', []),
        'provenance': osint_data.get('provenance', []),
        'fact_check_results': fact_check_data.get('fact_check_results', []),
        'narrative_analysis': narrative_data.get('narrative_analysis', {}),
        'red_team_audit': red_team_audit_data.get('red_team_audit', {}),
        'video_analysis': video_analysis_data.get('video_analysis', [])
    }
    synthesizer_result = await synthesizer.execute(synthesizer_input)
    if not synthesizer_result.success:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {synthesizer_result.error}")

    dossier = synthesizer_result.data
    return dossier

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)