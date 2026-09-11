# TruthTrace: Disinformation & Narrative Intelligence Engine

TruthTrace is an automated, multi-agent forensic verification system designed to ingest news claims, viral headlines, articles, or URLs and perform end-to-end provenance investigation. It uncovers veracity, isolates earliest origin candidates ("Patient Zero"), constructs chronological propagation timelines via the Wayback CDX API, decodes underlying narrative agendas, and learns continuously from investigative feedback.

---

## Key Capabilities

- **Live Multi-Vector OSINT & Fact-Checking**: Parallel querying across DuckDuckGo Lite, Wikipedia OpenSearch, GDELT 2.0 Doc API, Google Fact Check Tools API, and NewsAPI without synthetic fallback URLs.
- **Chronological Provenance & Wayback Archival Tracing**: Resolves earliest web timestamps and archive.org snapshots to reconstruct the exact diffusion timeline.
- **"Patient Zero" Origin Discovery**: Semantic clustering and timestamp sorting isolate the earliest publisher, social account, or domain that catalyzed the claim.
- **Dynamic Narrative & Motive Profiling**: Decodes core narratives, emotional hooks, target demographics, and plausible intentions using content-aware NLP and LLM orchestration.
- **Media Manipulation & Video Forensics**: Keyframe analysis, transcript extraction, and recycled/out-of-context footage detection.
- **WHOIS & Network Attribution**: IFCN/MBFC credibility cross-referencing and astroturf burst pattern detection.
- **Continuous Episodic Learning Memory (Phase 6)**: Vector-backed feedback storage and contrastive metric learning that recalls historical investigations to refine future confidence scoring.
- **Cross-Platform Flutter Frontend**: Responsive UI for Mobile (Android/iOS), Desktop (macOS/Windows/Linux), and Web.
- **Forensic CLI Interface**: Rich terminal UI with styled Dossier panels, timelines, and origin breakdowns.

---

## Architecture (Phases 0 — 6)

```
TruthTrace/
├── backend/                  # Python FastAPI Backend
│   ├── api/                  # FastAPI router (/analyze, /feedback, /metrics)
│   ├── agents/               # Autonomous forensic agents
│   │   ├── claim_extractor.py    # Atomic claim decomposition
│   │   ├── osint_hunter.py       # Live DDG Lite, GDELT, Wikipedia & NewsAPI
│   │   ├── social_hunter.py      # Reddit & public Telegram ingestion
│   │   ├── wayback_agent.py      # Wayback CDX earliest snapshot locator
│   │   ├── fact_checker.py       # Verified registry and evidence evaluator
│   │   ├── narrative_profiler.py # Content-aware narrative & motive profiler
│   │   ├── red_team_auditor.py   # Adversarial self-check & confidence auditor
│   │   ├── attribution_agent.py  # WHOIS, IFCN registry & coordination detector
│   │   ├── video_analyst.py      # Temporal video recycling & YouTube analyst
│   │   └── synthesizer.py        # Dossier assembler & cluster engine
│   ├── learning/             # Contrastive metric learner & loss functions
│   ├── memory/               # Episodic learning store (JSONL / Vector memory)
│   ├── models/schemas.py     # Pydantic v2 schemas for Claim, SubClaim, Dossier
│   └── utils/                # Vector store, LLM abstractions, and helpers
├── flutter_frontend/         # Flutter Cross-Platform Application
│   ├── lib/                  # Screens, models, state providers, and widgets
│   └── pubspec.yaml          # Flutter dependencies
├── cli/                      # Command Line Interface
│   └── src/truthtrace_cli.py # Rich terminal dossier viewer
└── test_phases_2_to_6.py     # End-to-end integration test suite
```

---

## Getting Started

### Prerequisites

- **Python 3.10+**
- **Flutter SDK 3.19+**
- **Git**

---

### Backend Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create and activate a virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment (optional - system works keyless out of the box)
cp .env.example .env

# 5. Start the FastAPI backend
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### Flutter App Setup

```bash
# 1. Navigate to flutter_frontend
cd flutter_frontend

# 2. Get packages
flutter pub get

# 3. Run on your desired platform:
flutter run -d chrome       # Run in Browser
flutter run -d windows      # Run as Windows Desktop App
flutter run -d macos        # Run as macOS Desktop App
flutter run                 # Run on connected Mobile Emulator / Device
```

---

### CLI Usage

```bash
# Verify API health
python cli/src/truthtrace_cli.py health

# Analyze a claim
python cli/src/truthtrace_cli.py check "A viral Frontline magazine cover shows that a massive Vijay wave has emerged in Tamil Nadu"

# Analyze a URL and save output
python cli/src/truthtrace_cli.py check --url "https://example.com/article" --output dossier.json
```

---

## API Reference

### `POST /analyze`
Analyzes an input claim or URL through the complete multi-agent pipeline.

**Request**:
```json
{
  "claim": "Claim string to verify",
  "url": "Optional URL"
}
```

**Response**: Comprehensive `Dossier` object including `overall_verdict`, `overall_confidence`, `patient_zero`, `timeline`, `narrative`, `sub_claims`, `attribution`, `clusters`, and `cross_investigation_memory`.

---

### `POST /feedback`
Submits user feedback (e.g., accurate / inaccurate / correction) to update the Episodic Learning Store.

---

## Running Tests

```bash
# Run full Phase 0-6 end-to-end integration test suite
python test_phases_2_to_6.py

# Run Episodic Learning Store & Metric Learner tests
python test_learning_memory.py
```

---

## License

MIT License. Developed for open forensic journalism and anti-disinformation research.