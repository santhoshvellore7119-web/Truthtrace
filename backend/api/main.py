from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import asyncio

from agents.claim_extractor import ClaimExtractorAgent
from agents.osint_hunter import OSINTHunterAgent
from agents.fact_checker import FactCheckAgent
from agents.narrative_profiler import NarrativeProfilerAgent
from agents.synthesizer import SynthesizerAgent

app = FastAPI(title="TruthTrace API", version="0.1.0")

class AnalyzeRequest(BaseModel):
    claim: Optional[str] = None
    url: Optional[str] = None

class AnalyzeResponse(BaseModel):
    verdict: str
    credibility_score: float
    timeline: list
    patient_zero: dict
    source_tweaking: dict
    narrative_intention: dict
    evidence: list

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_claim(request: AnalyzeRequest):
    """
    Analyze a claim or URL using the multi-agent pipeline.
    """
    if not request.claim and not request.url:
        raise HTTPException(status_code=400, detail="Either claim or url must be provided")

    # Initialize agents
    claim_extractor = ClaimExtractorAgent()
    osint_hunter = OSINTHunterAgent()
    fact_checker = FactCheckAgent()
    narrative_profiler = NarrativeProfilerAgent()
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

    # Step 5: Synthesize results
    synthesizer_input = {
        'claims': claims_data.get('claims', []),
        'provenance': osint_data.get('provenance', []),
        'fact_check_results': fact_check_data.get('fact_check_results', []),
        'narrative_analysis': narrative_data.get('narrative_analysis', {})
    }
    synthesizer_result = await synthesizer.execute(synthesizer_input)
    if not synthesizer_result.success:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {synthesizer_result.error}")

    dossier = synthesizer_result.data

    # Ensure we have all required fields for the response
    response = AnalyzeResponse(
        verdict=dossier.get('verdict', 'UNVERIFIED'),
        credibility_score=dossier.get('credibility_score', 0.0),
        timeline=dossier.get('timeline', []),
        patient_zero=dossier.get('patient_zero', {}),
        source_tweaking=dossier.get('source_tweaking', {}),
        narrative_intention=dossier.get('narrative_intention', {}),
        evidence=dossier.get('evidence', [])
    )

    return response

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)