# TruthTrace — Master Build Prompt
### The complete brief for turning TruthTrace from a working prototype into a real, defensible, best-in-class narrative-intelligence platform.

> **How to use this document:** Paste this whole file into Claude Code (or a similarly capable coding agent) as the standing project brief at the start of a session, e.g. `claude "Read TRUTHTRACE_MASTER_BUILD_PROMPT.md in full before doing anything. Then propose a working plan for Phase 1 and start implementing."` Keep this file in the repo root (`/TRUTHTRACE_MASTER_BUILD_PROMPT.md`) and re-point the agent at it whenever you start a new session, so nothing gets lost between sessions. Work through the phases in order — do not let the agent skip ahead to polish/UI before the evidence and persistence layers are real.

---

## 0. Mission statement (read this first, every time)

You are not building a demo. You are not building "an LLM that summarizes whether something is true." You are building **verifiable investigative infrastructure**: a system whose outputs a skeptical journalist, researcher, or fact-checker could actually stand behind in public, because every claim it makes traces back to an inspectable piece of evidence with a timestamp and a source.

If at any point you (the coding agent) are about to have an LLM assert something as fact without attaching the evidence it came from, stop and fix the architecture instead. **The evidence graph is the product. The narrative and verdict are just a view on top of it.**

Optimize, in order of priority:
1. **Trustworthiness of output** (every claim traceable, every source graded, nothing silently hallucinated)
2. **Resilience** (platforms rate-limit and block scrapers constantly — degrade gracefully, never fail silently)
3. **Regional-language capability** (Tamil-first, then Hindi) — this is the actual market differentiator, not a stretch feature
4. **Everything else** (UI polish, speed, extra integrations)

---

## 1. Product thesis — what makes this different from every other fact-checker

Read this and internalize it before writing code. Most "AI fact-checkers" (Full Fact, Logically, generic GPT-wrapper tools) answer "is this true?" with an opaque score. That is not defensible and not differentiated. TruthTrace answers three harder, more valuable questions:

1. **Where did this actually start, and who benefits?** (Patient Zero + motive/narrative analysis — provenance, not just truth value)
2. **What exactly was changed between the original source and the version being spread?** (Source-tweaking diff — this is the single most novel and hardest-to-fake feature; protect and prioritize it)
3. **Is this part of a coordinated pattern, or an isolated claim?** (Cross-claim graph memory — nobody else at this scale does claim-level coordination detection)

The regional-language angle (Tamil first) is not a translation nice-to-have — it is a genuine open market. English-language disinformation is saturated with tooling; Tamil/Indian-regional-language disinformation (WhatsApp forwards, YouTube shorts, Facebook reposts around Indian politics and finance) is under-tooled and high-volume. Build the pipeline so Tamil is a first-class citizen, not a translate-then-analyze bolt-on — translation loses idiom, sarcasm, and culturally-loaded framing that IS the disinformation signal.

---

## 2. Non-negotiable design principles

- **Every claim in a dossier must carry a `source_ref` pointing to a stored `Evidence` object.** No `Evidence` object, no claim in the final report. If an agent can't back a statement with evidence, it must mark it as `unverified_inference` and visually/structurally separate it from sourced claims.
- **No feature ships without a degraded-mode fallback.** X/Twitter API dies → fall back to Nitter mirrors → fall back to Wayback/Google cache → fall back to "provenance unknown, here's why." Never let one blocked API silently zero out a whole section of the report.
- **Every external call (scraper, LLM, search API) must be logged with cost, latency, and success/failure**, from day one. You cannot productionize what you cannot observe.
- **LLM outputs that will be shown as findings must be JSON-schema-validated** (use Pydantic / Zod) before they touch the response. Never pass raw LLM text into the final report — parse, validate, re-serialize.
- **Assume adversarial input.** Someone will feed this tool a claim specifically engineered to make the Narrative Profiler produce a flattering or misleading read. Build the red-team/self-skepticism agent (Section 6.6) from Phase 1, not as a later add-on.
- **Everything must run in "free mode."** If a contributor or user has zero API keys, the system must still produce a real (if less rich) analysis using local models + free-tier search + public archives. This is already a stated goal — do not regress it while adding features.

---

## 3. Target architecture (end state)

```
TruthTrace/
├── backend/
│   ├── api/                      # FastAPI routes
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── claim_extractor.py
│   │   ├── osint_hunter.py
│   │   ├── fact_checker.py
│   │   ├── narrative_profiler.py
│   │   ├── red_team_auditor.py   # NEW — self-skepticism pass
│   │   └── synthesizer.py
│   ├── evidence/
│   │   ├── graph_store.py        # Postgres + pgvector persistence
│   │   ├── schemas.py            # Claim, Evidence, Source, Account, Dossier
│   │   └── snapshot.py           # Wayback/archive.today snapshotting
│   ├── scrapers/
│   │   ├── web_search.py         # Tavily/Serper + fallback chain
│   │   ├── social/
│   │   │   ├── reddit.py
│   │   │   ├── twitter_x.py
│   │   │   ├── telegram.py
│   │   │   ├── youtube.py
│   │   │   └── fallback_cache.py # Google cache + Wayback fallback
│   │   └── factcheck_registries.py # Snopes, PolitiFact, AP, Reuters, BOOM (India), Alt News
│   ├── i18n/
│   │   ├── tamil_pipeline.py     # Tamil-first NLP: extraction, translation-aware analysis
│   │   └── lang_detect.py
│   ├── graph_intel/
│   │   ├── clustering.py         # coordinated-narrative detection across stored claims
│   │   └── account_scoring.py    # repeat-offender account credibility tracking
│   ├── utils/llm.py              # existing LLM abstraction w/ free fallback — extend, don't replace
│   ├── observability/
│   │   ├── logging.py
│   │   └── cost_tracker.py
│   └── tests/
├── frontend/                     # Next.js 14 — dashboard + evidence graph viewer
├── extension/                    # NEW — Phase 5 browser extension (Manifest V3)
├── cli/
└── docs/
    ├── ARCHITECTURE.md
    ├── AGENT_SPECS.md
    └── EVALUATION.md
```

---

## 4. Core data model (implement this before touching any agent logic)

Use Pydantic v2 models on the backend, mirrored as TypeScript types on the frontend. This schema IS the evidence graph — get it right first.

```python
class Source(BaseModel):
    id: str
    url: str
    domain: str
    fetched_at: datetime
    snapshot_url: str | None       # Wayback/archive.today permalink, captured at fetch time
    credibility_tier: Literal["registry", "primary", "mainstream", "unverified", "known_low_credibility"]
    content_hash: str              # for detecting later edits to the same URL

class Evidence(BaseModel):
    id: str
    source: Source
    excerpt: str                   # the exact supporting text, verbatim, with position offsets
    retrieved_via: str             # which scraper/tool found this
    confidence: float              # 0-1, how well this excerpt supports the linked claim

class SubClaim(BaseModel):
    id: str
    text: str
    atomic: bool                   # true if this is a single testable assertion
    verdict: Literal["true","false","misleading","unverified","satire","opinion"]
    verdict_confidence: float
    evidence: list[Evidence]       # MUST be non-empty unless verdict == "unverified"
    unverified_inference: bool     # true if this came from LLM reasoning without direct evidence

class OriginatingAccount(BaseModel):
    platform: str
    handle: str
    first_seen_at: datetime | None
    follower_count: int | None
    prior_flagged_claims: int      # pulled from graph_intel — repeat-offender signal

class SourceTweak(BaseModel):
    original_text: str
    altered_text: str
    tweak_type: Literal["mistranslation","out_of_context","selective_edit","fabrication","satire_stripped"]
    diff_span: tuple[int, int]

class NarrativeProfile(BaseModel):
    core_narrative: str
    emotional_hooks: list[str]
    target_demographic: str
    plausible_intent: str
    coordinated_cluster_id: str | None   # links to graph_intel clustering output

class RedTeamAudit(BaseModel):
    flags: list[str]               # e.g. "narrative profiler may be pattern-matching on tone, not substance"
    source_credibility_concerns: list[str]
    confidence_adjustment: float   # applied to final dossier confidence

class Dossier(BaseModel):
    id: str
    input_claim: str
    language: str
    sub_claims: list[SubClaim]
    patient_zero: OriginatingAccount | None
    source_tweaks: list[SourceTweak]
    narrative: NarrativeProfile
    red_team_audit: RedTeamAudit
    overall_verdict: str
    overall_confidence: float
    generated_at: datetime
```

Store every `Dossier`, `Evidence`, and `Source` permanently in Postgres (pgvector extension for embedding-based similarity search across claims — this powers the coordination-clustering feature in Phase 3). Never discard evidence after generating the report; it's the asset that compounds in value over time.

---

## 5. Backend agent specifications

For each agent below: implement (a) the LLM-available path, (b) the free/local-model path, (c) the zero-LLM rule-based fallback, in that priority order, matching the existing `utils/llm.py` fallback pattern. Every agent must catch and log its own failures and return a partial result rather than throwing — a broken OSINT Hunter should never take down the whole pipeline.

### 5.1 Claim Extractor
- Input: raw text / URL. Output: `list[SubClaim]` (verdict/evidence unfilled at this stage).
- Must split compound claims into atomic, independently-checkable units.
- Must detect and tag: satire, opinion, rhetorical question (these get a different pipeline than factual assertions — don't try to "fact check" an opinion).
- Language detection happens here — route Tamil (and later Hindi) input into `i18n/tamil_pipeline.py` rather than translating first and losing signal.

### 5.2 OSINT Hunter
- Input: sub-claims. Output: candidate `Source` + `Evidence` objects, plus `OriginatingAccount` if a social origin is found.
- Implement the **fallback chain** explicitly: primary API → alternate API/mirror → Wayback Machine CDX API → Google cache → "provenance unknown" with a logged reason. This chain must be visible in code as an actual ordered list, testable in isolation.
- Every scraper module needs its own rate-limit handling and exponential backoff — a 429 from Reddit must not crash the pipeline.
- Snapshot every source at fetch time (`evidence/snapshot.py`) so later edits to the live page can't erase the evidence trail — this is a core trust guarantee, implement it early.

### 5.3 Fact Checker
- Cross-references sub-claims against fact-check registries (Snopes, Reuters Fact Check, AP, PolitiFact, and — important for your market — **BOOM Live** and **Alt News**, the two most credible Indian fact-checking registries, which the current build doesn't list at all).
- Produces the `SourceTweak` diff: original wording vs. claimed wording, with the specific span that changed and a `tweak_type` classification. This is your most defensible, hardest-to-replicate feature — invest disproportionate engineering effort here, including good test coverage with real historical examples of misquotes/mistranslations.

### 5.4 Narrative Profiler
- Produces `NarrativeProfile`. Must explicitly separate **descriptive** analysis (what emotional levers are used, what demographic is targeted) from **speculative** analysis (claimed intent/motive) — speculative fields must be clearly flagged as inference, never presented with false certainty.

### 5.5 Red-Team Auditor (NEW — build this in Phase 1, not later)
- Takes the outputs of 5.2–5.4 and actively tries to break them: are the "evidence" sources themselves low-credibility? Is the Narrative Profiler pattern-matching on tone/style rather than substantive claims? Is the Patient Zero attribution actually just "first result returned by search," not genuinely earliest?
- Produces `RedTeamAudit`, which downgrades `overall_confidence` when it finds weaknesses. This agent's entire job is to keep the system honest about its own limits — treat it as a hard requirement for shipping, not a polish item.

### 5.6 Synthesizer
- Combines everything into the `Dossier`. Enforce the rule from Section 2: no `SubClaim` may have a non-`unverified` verdict without at least one linked `Evidence` object. Validate this programmatically, not just by prompting the LLM to behave.

---

## 6. Cross-claim intelligence layer (`graph_intel/`) — Phase 3

This is the part of the system that gets more valuable with every claim it processes, and is the actual long-term moat:

- **`clustering.py`**: embed every processed claim (via pgvector) and cluster by narrative similarity + timing proximity to detect coordinated pushes — e.g. "these 40 claims across 3 platforms share phrasing and appeared within 6 hours of each other."
- **`account_scoring.py`**: track every `OriginatingAccount` encountered across all dossiers; surface "this account has originated N previously-debunked claims" as a first-class signal in future reports on the same account.

Do not build this before the evidence/persistence layer (Section 4) is solid — it depends entirely on having real stored history to work with.

---

## 7. Regional-language pipeline (Tamil-first) — Phase 2

- Build `i18n/tamil_pipeline.py` to do claim extraction and narrative analysis **natively in Tamil**, not via machine-translate-then-analyze. Machine translation strips sarcasm, idiom, and culturally loaded phrasing — which is often exactly where the disinformation signal lives.
- Source the fact-check registry list for Indian-language misinformation specifically (BOOM, Alt News, Vishvas News, Factly) and prioritize these over English-only registries when the input is Tamil.
- Validate against real Tamil political/financial misinformation examples — build a small labeled test set (you have direct access to this domain through your own research work; use it to seed evaluation data, never to leak into production behavior — keep eval data clearly separated).

---

## 8. API contract additions

Extend the existing `/api/analyze` and `/health` endpoints with:

```
GET  /api/dossier/{id}                  # fetch a stored dossier by id, with full evidence graph
GET  /api/dossier/{id}/evidence-graph   # graph-shaped response (nodes/edges) for the frontend visualizer
GET  /api/accounts/{platform}/{handle}  # account credibility history
GET  /api/clusters/{cluster_id}         # coordinated-narrative cluster detail
POST /api/analyze                       # existing — extend response to always include full Dossier schema
GET  /health                            # existing — extend to report per-scraper/per-LLM health, not just "ok"
```

Every response must validate against the Pydantic schemas in Section 4 before leaving the API layer — reject/log, never silently pass through malformed data.

---

## 9. Frontend requirements (Next.js)

- Replace the flat "credibility score + text report" view with an **evidence graph visualizer**: claim nodes connected to their evidence nodes, color-coded by credibility tier, so a user can literally click into "why was this marked false" and see the source, snapshot link, and excerpt.
- Add a **source-tweak diff view**: side-by-side original vs. altered text with the changed span highlighted — this is your signature feature, give it real visual craft, not an afterthought table.
- Add an **account history view** once Section 6 exists: "this account has been flagged in N prior dossiers."
- Keep the existing CLI-parity page, but make sure every capability added to the backend surfaces somewhere in the UI — don't let backend features go dark because nobody wired up a view.

---

## 10. Browser extension — Phase 5 (distribution strategy)

Nobody proactively visits a fact-checking website. Build a Manifest V3 extension (`extension/`) that lets a user highlight any text on any page and get an inline TruthTrace verdict without leaving the page. This is the actual growth lever for the whole project — treat it as a real phase with its own milestone, not a stretch goal.

---

## 11. Security, cost, and observability requirements (apply from Phase 1 onward)

- Rate-limit the public API per-IP and per-key from day one; a free public demo without this will get cost-bombed.
- Log every external call (LLM + scraper + search API) with latency, cost estimate, and success/failure to `observability/cost_tracker.py`. Surface a simple `/api/stats` or admin view of daily spend.
- Never log or persist raw API keys; validate `.env` loading fails loudly (not silently falls back to "no key") when a key is malformed.
- Add basic input sanitization on the `/api/analyze` endpoint — this tool will attract adversarial and abusive input by its very nature; treat every input as hostile.

---

## 12. Testing strategy

- Unit tests per agent using recorded/mocked scraper responses (never hit live APIs in CI).
- Golden-set integration tests: 15–20 real historical claims (mix of true, false, misleading, satire, and at least 5 in Tamil) with known correct verdicts — run the full pipeline against these on every PR and fail the build if accuracy regresses.
- Explicit tests for the fallback chains (Section 5.2) — simulate each API being down and assert the system degrades instead of crashing.
- Explicit tests asserting the "no claim without evidence" invariant from Section 2 at the schema-validation layer.

---

## 13. Build phases and acceptance criteria

**Phase 1 — Trust infrastructure (do this first, no exceptions)**
- Implement the full data model (Section 4), Postgres persistence, source snapshotting, and the Red-Team Auditor.
- Acceptance: every dossier produced end-to-end has zero claims without linked evidence, and every source has a snapshot URL.

**Phase 2 — Regional language**
- Tamil-first claim extraction and fact-checking, sourcing Indian fact-check registries.
- Acceptance: golden-set Tamil claims produce correct verdicts with native-language evidence excerpts, not translated ones.

**Phase 3 — Cross-claim graph intelligence**
- pgvector clustering + account scoring, live in the API and surfaced in the frontend.
- Acceptance: feeding two related coordinated claims produces a linked `cluster_id` and the account view shows prior-flag history.

**Phase 4 — Adversarial hardening**
- Expand Red-Team Auditor coverage; add source-credibility scoring for fact-checkers themselves; add hostile-input test suite.
- Acceptance: golden-set includes adversarially-phrased claims and the system correctly flags its own uncertainty rather than confidently misjudging them.

**Phase 5 — Distribution**
- Ship the browser extension.
- Acceptance: a real user can highlight text on an arbitrary news site and get a verdict inline, backed by the full API.

Do not let polish or new integrations jump the queue ahead of Phase 1 and Phase 2 — they are the actual differentiators; everything else is table stakes.

---

## 14. Working agreement for the coding agent

- Work in small, reviewable commits, one logical change per commit, clear messages (`feat(evidence): add source snapshotting via Wayback CDX API`).
- After each phase, update `docs/ARCHITECTURE.md` and `docs/AGENT_SPECS.md` to reflect what was actually built (not just what was planned) — keep docs and code from drifting apart.
- Before marking any phase "done," run the golden-set integration tests and report the pass rate honestly — do not claim completion without running them.
- If a design choice in this document turns out to be impractical once you're in the code, flag it explicitly and propose an alternative rather than silently deviating.

---

## 15. Definition of "best in the market"

Not: prettiest UI, most integrations, fastest response time.
Actually: **the only tool in this space where every claim is traceable to inspectable evidence, that natively handles Tamil/Indian-regional-language disinformation, and that gets measurably smarter with every claim it processes because it remembers.** If the finished system can do those three things, it is legitimately differentiated — build toward that, not toward feature parity with existing English-only fact-checkers.