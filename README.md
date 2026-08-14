# TruthTrace: Disinformation & Narrative Intelligence Engine

TruthTrace is a full-stack automated investigative tool designed to ingest any news claim, headline, article body, or URL and perform deep forensic verification across the web, news archives, and social media platforms to determine veracity, map the earliest origin ("Patient Zero"), detect source alteration/tweaks, and expose the underlying narrative/motive.

## Features

- **Multi-Vector Web & News Investigation**: Cross-references against fact-checking registries (Snopes, Reuters Fact Check, AP Fact Check, PolitiFact, etc.), global web indices, alternative media, blogs, forums, and the Wayback Machine.
- **Social Media Provenance & "Patient Zero" Tracking**: Searches across social platforms (X/Twitter, Reddit, Telegram, YouTube, Facebook) to locate the earliest known timestamp and profile the originating account.
- **Forensic Anomaly & Source Tweaking Analysis**: Identifies if source material was selectively edited, mistranslated, taken out of context, or altered. Provides side-by-side comparison of original vs. claimed statements.
- **Narrative & Disinformation Agenda Deconstruction**: Identifies the core narrative/agenda being propagated, analyzes emotional hooks, target demographic, and plausible intent/motive.
- **Structured Output Report**: Generates a comprehensive dossier with verdict, credibility score, timeline, patient zero profile, source tweaking breakdown, narrative intention matrix, and evidence sources.
- **Modern Web Interface**: Built with Next.js 14, TypeScript, and Tailwind CSS for a responsive, attractive dashboard.
- **Command Line Interface**: Full CLI tool for terminal-based analysis with rich output formatting.
- **Modular Agent-Based Architecture**: Uses a multi-agent pipeline (Claim Extractor, OSINT Hunter, Fact Checker, Narrative Profiler, Synthesizer) for scalable and maintainable analysis.
- **Free Model Fallback**: When no paid API keys are available, the system automatically falls back to high-quality free/open-source LLMs (e.g., HuggingFace's FLAN-T5) to ensure functionality for all users.

## Architecture

```
TruthTrace/
├── backend/              # Python/FastAPI backend
│   ├── api/              # API endpoints
│   ├── agents/           # AI agents for analysis pipeline
│   ├── scrapers/         # Web and social media scrapers
│   ├── models/           # Data models and schemas
│   ├── utils/            # Utility functions (including LLM manager)
│   └── utils/llm.py      # LLM abstraction with free fallback
├── frontend/             # Next.js 14 web application
│   ├── src/app/          # Application pages and routes
│   └── public/           # Static assets
���└── cli/                  # Command Line Interface
    └── src/              # CLI source code
```

### Backend Agents

1. **Claim Extractor**: Breaks down input text into atomic, testable sub-claims (uses LLM if available, else regex fallback).
2. **OSINT Hunter**: Hunts for provenance across web and social media platforms.
3. **Fact Checker**: Cross-references claims with fact-checking registries and archives.
4. **Narrative Profiler**: Analyzes narrative, intent, and psychological drivers (uses LLM if available, else rule-based fallback).
5. **Synthesizer**: Combines results from all agents into a structured dossier (uses LLM for reasoning if available, else rule-based).

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 18+ (for frontend)
- API keys for search services and LLMs (optional for basic functionality; system works with free models)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd TruthTrace
   ```

2. **Backend Setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env to add your API keys (optional)
   # If you leave API keys blank, the system will use free models automatically
   ```

3. **Frontend Setup**:
   ```bash
   cd ../frontend
   npm install
   # No .env needed for frontend as it communicates with backend via relative paths
   ```

4. **CLI Setup**:
   ```bash
   cd ../cli/src
   pip install -r ../../cli/requirements.txt
   cp .env.example .env
   # Edit .env to set API_BASE_URL if needed (default: http://localhost:8000)
   ```

### Environment Variables

#### Backend (`backend/.env`)
- `TAVILY_API_KEY`: For web search (primary)
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`: For Reddit API
- `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`: For X/Twitter API
- `OPENAI_API_KEY`: For OpenAI LLM (optional; if absent, free models used)
- `HF_API_KEY`: For HuggingFace Inference API (optional; increases rate limits)
- Other API keys as needed for additional services

#### CLI (`cli/src/.env`)
- `API_BASE_URL`: URL of the backend API (defaults to `http://localhost:8000`)

### Free Model Usage

If no OpenAI or other paid LLM API keys are provided, TruthTrace automatically uses:
- **Local transformers**: `google/flan-t5-small` (or similar) via the �� 🤗 Transformers library
- **HuggingFace Inference API**: If `HF_API_KEY` is set, uses free models like `google/flan-t5-xl`
- **Rule-based fallback**: For components where LLMs are less suited (e.g., simple claim extraction)

This ensures that users without API credits can still run the system and obtain meaningful analysis, albeit potentially with slightly less nuanced reasoning compared to state-of-the-art paid models.

## Usage

### Web Interface

1. Navigate to `http://localhost:3000` (or your configured port)
2. Enter a news claim, headline, article body, or URL in the input form
3. Click "Analyze Claim" to start the investigation
4. View the structured results including:
   - Verdict and credibility score
   - Timeline of dissemination
   - Patient zero and origin profile
   - Source tweaking analysis (original vs. claimed)
   - Narrative and intention matrix
   - Evidence and sources
5. Export the report as PDF or share it

### Command Line Interface

```bash
# Basic claim analysis
python -m truthtrace.cli.src.truthtrace_cli check "The moon landing was faked in a Hollywood studio."

# URL analysis
python -m truthtrace.cli.src.truthtrace_cli check --url "https://example.com/suspicious-article"

# Save results to JSON file
python -m truthtrace.cli.src.truthtrace_cli check "Claim to analyze" --output analysis.json

# Check API health
python -m truthtrace.cli.src.truthtrace_cli health
```

## API Endpoints

### Analyze Claim
- **URL**: `POST /api/analyze`
- **Body**: 
  ```json
  {
    "claim": "string (optional)",
    "url": "string (optional)"
  }
  ```
- **Response**: Structured analysis result

### Health Check
- **URL**: `GET /health`
- **Response**: `{"status": "ok"}`

## Project Structure

```
TruthTrace/
├── README.md
├── backend/
│   ├── api/
│   │   └── main.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── claim_extractor.py
│   │   ├── osint_hunter.py
│   │   ├── fact_checker.py
│   │   ├── narrative_profiler.py
│   │   └── synthesizer.py
│   ├── scrapers/
│   ├── models/
│   ├── utils/
│   │   └── llm.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   └── app/
│   │       ├── page.tsx          # Home page with analysis dashboard
│   │       ├── layout.tsx
│   │       ├── globals.css
│   │       ├── about/page.tsx
│   │       └── cli/page.tsx
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.js
├── cli/
│   ├── src/
│   │   ├── truthtrace_cli.py
│   │   └── .env.example
│   └── requirements.txt
���└── .gitignore
```

## Customization and Extensibility

### Adding New Search Sources

1. Create a new scraper in `backend/scrapers/`
2. Add the search function to the OSINT Hunter agent
3. Update the agent's execute method to include the new source

### Adding New LLMs

1. The agent base class (via `backend/utils/llm.py`) is designed to work with any LLM
2. Update the LLM manager to use a different LLM client
3. Modify the prompt engineering as needed for the new model

### Changing the Analysis Pipeline

1. Modify the agent execution order in the backend API
2. Add new agents by inheriting from `BaseAgent`
3. Update the data flow between agents in the API endpoint

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by the need for tools to combat misinformation in the digital age
- Built using modern web technologies and AI agent frameworks
- Thanks to all the open-source projects that make this possible