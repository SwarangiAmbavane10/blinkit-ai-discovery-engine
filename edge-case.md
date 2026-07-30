# AI Product Discovery Engine — Edge Cases

**Organization:** Blinkit  
**Document Type:** Edge Case & Failure Mode Specification  
**Version:** 1.0  
**Last Updated:** July 2026  
**Sources:** `architecture.md`, `context.md`, `implementation-plan.md`

---

## Purpose

This document defines how the Blinkit AI Product Discovery Engine behaves when data, search, AI synthesis, or infrastructure deviates from the happy path. Each edge case specifies **detection**, **system response**, **stakeholder output**, and **mitigation** so engineering, analytics, and business teams handle failures consistently.

---

## Edge Case Index

| ID | Category | Severity | Primary Layer |
|----|----------|----------|---------------|
| EC-01 | No reviews | High | Ingestion / Retrieval |
| EC-02 | Conflicting reviews | Medium | Retrieval / Insight Engine |
| EC-03 | Spam | Medium | Review Cleaning |
| EC-04 | Duplicate reviews | Low | Review Cleaning |
| EC-05 | Mixed language reviews | Medium | Review Cleaning / Retrieval |
| EC-06 | Very long reviews | Low | Embedding / Retrieval |
| EC-07 | Fake reviews | High | Review Cleaning / Validation |
| EC-08 | Hallucination prevention | Critical | LLM Integration / Validation |
| EC-09 | Rate limiting | High | Collection / LLM Integration |
| EC-10 | Empty search | Medium | Retrieval / Dashboard |
| EC-11 | Low confidence insights | Medium | Insight Engine / Dashboard |
| EC-12 | Deployment failures | Critical | Deployment |

---

## EC-01 — No Reviews

### Scenario

No new or historical reviews exist for a given source, time window, category filter, or query context. Common triggers:

- First run before initial collection completes
- Connector failure across all sources
- Overly narrow filters (e.g., RQ + category + segment + 30-day window with zero matches)
- Blinkit app temporarily delisted or API outage
- New market/city with no vocal user feedback yet

### Detection

| Signal | Location |
|--------|----------|
| `record_count = 0` on ingestion run | Collection runner manifest |
| Empty raw store directory for run ID | Object storage |
| `source_documents` count = 0 for filter | PostgreSQL |
| Retrieval returns 0 candidates | Retrieval Layer |
| Evidence bundle `items.length = 0` | Bundle builder |

### System Behavior

1. **Ingestion:** Complete run with status `SUCCESS_EMPTY` (not `FAILURE`); log warning with source and date range.
2. **Cleaning:** Skip pipeline stages; emit cleaning report with `accepted: 0`.
3. **Embedding:** No-op; log "nothing to embed."
4. **Retrieval:** Do **not** call Gemini; return structured empty bundle.
5. **Synthesis:** Block analysis run; set status `SKIPPED_NO_EVIDENCE`.
6. **Dashboard:** Show empty state UI; do not render insight cards from prior unrelated data.

### Stakeholder Output

```
Status: Insufficient evidence
Message: No user feedback matched your filters for [source / category / date range].
Recommendation: Widen recency window, remove segment filter, or wait for next ingestion cycle.
Last successful ingestion: [timestamp]
```

Monthly report section for affected RQ:

> *Insufficient new evidence this cycle. Prior period answer retained (version N, dated YYYY-MM-DD).*

### Mitigation

| Action | Owner |
|--------|-------|
| Verify connector credentials and app IDs | Engineering |
| Widen default recency window (90 → 180 days) | Product / Analytics |
| Seed Google Form survey for first-party input | Growth / Research |
| Alert if `SUCCESS_EMPTY` for 3 consecutive scheduled runs | Ops |

### Related Components

`CollectionRunner`, `CleaningPipeline`, `RetrievalRouter`, `AnalysisTriggerService`, Dashboard empty states

---

## EC-02 — Conflicting Reviews

### Scenario

Users express opposing views on the same theme or category—for example:

- Play Store: *"Great variety, love discovering new snacks"*
- Reddit: *"Blinkit has no variety compared to Zepto"*
- Same source, different time periods (pre vs. post UI redesign)

Conflicts are **expected**, not errors. The system must surface them, not resolve them by averaging.

### Detection

| Signal | Location |
|--------|----------|
| Sentiment divergence on same theme tag | Enrichment records |
| `ContradictionStrategy` retrieves opposing docs | Retrieval Layer |
| Gemini flags contradiction in output | Insight Generator |
| Confidence calibrator caps at Medium | Validation Layer |

### System Behavior

1. **Retrieval:** `ContradictionStrategy` explicitly fetches opposing-sentiment documents for contested themes.
2. **Synthesis:** Prompt instructs model to report both sides with source attribution—not pick a winner.
3. **Insight output:** Include `contradiction: true` and `conflict_summary` field.
4. **Persistence:** Write entry to `contradiction_log` with both document IDs.
5. **Confidence:** Cap at **Medium** regardless of mention count until human review.
6. **Dashboard:** Contradiction badge + side-by-side evidence view.

### Stakeholder Output

**Insight card example:**

```
Theme: Catalog variety perception
Confidence: Medium (conflicting evidence)
Summary: Android reviewers frequently praise snack selection; Reddit threads 
         in r/india compare Blinkit unfavorably to Zepto for variety.
Evidence A [Play Store]: "..." (n=12, mostly positive)
Evidence B [Reddit]: "..." (n=8, mostly negative)
Suggested action: Segment by platform and city; investigate assortment by region.
```

### Mitigation

| Action | When |
|--------|------|
| Segment conflict by source type, city, app version | Always |
| Time-box analysis (post-redesign only) | UI change detected |
| Human analyst review queue | High-impact contradictions affecting roadmap |
| Do not auto-merge into single narrative | Never |

### Related Components

`ContradictionStrategy`, `ContradictionScanWorkflow`, `contradiction_log`, `ConfidenceCalibrator`, Dashboard contradiction view

---

## EC-03 — Spam

### Scenario

Low-quality or malicious content enters the corpus:

- Generic bot text: *"Great app!!! Download now!!!"*
- Promo / referral spam
- Unrelated content (crypto, unrelated apps)
- Copy-paste identical text across many accounts
- Review bombing during outages (repeated *"worst app ever"* with no substance)

### Detection

| Signal | Rule |
|--------|------|
| Text length < 10 chars after normalize | `IngestValidator` reject |
| High repetition ratio | Same token repeated >40% of words |
| URL / referral pattern density | >2 promotional URLs |
| Gibberish score | Character entropy or language model perplexity threshold |
| Burst detection | >50 identical `content_hash` in 24h |
| Off-topic keywords | Blocklist: crypto, casino, unrelated app names |
| Star rating mismatch | 5-star + negative-only keywords (optional heuristic) |

### System Behavior

1. **Ingest validate:** Reject record; reason code `SPAM_REJECTED`.
2. **Do not embed or index** rejected spam.
3. **Log** rejected count in cleaning run report (not shown in dashboard source browser).
4. **Burst alert:** If rejection rate >30% in one run, flag ops for possible review bombing.
5. **Soft quarantine (optional):** Borderline cases stored with `quality_flag: suspected_spam` excluded from retrieval by default.

### Stakeholder Output

Spam is **not surfaced** to business stakeholders. Ops dashboard metric only:

```
Ingestion run X: 1,240 accepted, 87 rejected (spam), 12 rejected (PII)
Alert: Rejection rate 6.5% (within normal range)
```

### Mitigation

| Action | Detail |
|--------|--------|
| Maintain blocklist / allowlist | Update quarterly |
| Weight by helpfulness (Play Store) | Prefer reviews with helpful votes |
| Exclude outage windows | Configurable date blacklist during known incidents |
| Never include spam in insight evidence | Hard rule |

### Related Components

`IngestValidator`, `PreEnricher`, `CleaningPipeline`, `RetrievalRouter` (quality filter)

---

## EC-04 — Duplicate Reviews

### Scenario

Same review appears multiple times due to:

- Re-ingestion of unchanged records
- Cross-posted Reddit content
- User edits review (new text, same or different source ID)
- Export overlap between manual CSV and API fetch
- Identical text, different `source_id` (rare)

### Detection

| Signal | Rule |
|--------|------|
| Same `(source_type, source_id)` | `Deduplicator` — skip insert |
| Same `content_hash` (SHA-256 of normalized text) | Flag as content duplicate |
| Fuzzy text match >95% | Secondary dedup for cross-source |
| Reddit cross-post | Same URL or `crosspost_parent_id` |

### System Behavior

1. **Primary dedup:** Upsert on `(source_type, source_id)` — idempotent re-ingest.
2. **Content hash:** If `source_id` new but hash exists:
   - Link as `duplicate_of: original_document_id`
   - Do **not** double-count in theme frequency or evidence bundles
3. **User edit:** If same `source_id`, new hash → update document; re-embed; preserve version history.
4. **Retrieval:** Collapse duplicates in bundle; keep highest recency / rating representative.
5. **Aggregation:** Theme counts use distinct `content_hash`, not raw row count.

### Stakeholder Output

Insight evidence shows one representative quote; metadata notes:

```
Mention count: 14 (11 unique voices, 3 duplicate copies excluded)
```

### Mitigation

| Action | Detail |
|--------|--------|
| Idempotent ingestion runs | Required |
| Version document on edit | Audit trail |
| Dedup before embedding | Avoid redundant vector storage |
| Report unique vs. total mentions | Transparency in insight cards |

### Related Components

`Deduplicator`, `DocumentRepository`, `BundleBuilder`, `ThemeAggregator`

---

## EC-05 — Mixed Language Reviews

### Scenario

India-specific feedback often mixes languages:

- Hindi-English (Hinglish): *"Blinkit se sirf milk order karta hu, variety nahi hai"*
- Tamil / Telugu / Bengali with English product names
- English reviews with Hindi category terms
- Transliterated text without native script

Phase 1 default is **English-first** per `context.md`.

### Detection

| Signal | Location |
|--------|----------|
| `LanguageDetector` output | `en`, `hi`, `mixed`, `ta`, etc. |
| Non-Latin script ratio | Character class analysis |
| Code-switching heuristic | Multiple languages in single document |

### System Behavior

1. **Ingest:** Store `language_tag` on `source_documents` and enrichment records.
2. **English-only mode (default):**
   - **Include** Hinglish and predominantly English mixed text
   - **Include** but tag `confidence_penalty: language` for non-English majority
   - **Exclude from synthesis** (optional config) if `<20%` Latin script and no discovery keywords matched
3. **Embedding:** Embed full text regardless; semantic search partially works on mixed language.
4. **Retrieval:** Apply language filter when stakeholder selects language scope.
5. **Synthesis:** Prompt includes caveat: *"Evidence may underrepresent non-English speakers."*
6. **Dashboard:** Filter by language tag; bias disclosure in report footer.

### Stakeholder Output

Report footer (always when non-English excluded or penalized):

```
Language coverage: 78% English-primary, 14% Hinglish, 8% excluded (non-English majority).
Insight confidence may underrepresent regional-language users.
```

Insight card with mixed-language source:

```
Evidence [Play Store, hi-en]: "..." 
(Original; summary in English)
```

### Mitigation

| Phase | Action |
|-------|--------|
| Phase 1 | English + Hinglish; tag and disclose |
| Phase 2 | Hindi translation pass (Gemini translate → analyze → cite original) |
| Phase 3 | Multilingual embeddings; language-specific retrieval |

### Related Components

`LanguageDetector`, `Normalizer`, `RetrievalRouter`, `PromptBuilder`, `ConfidenceCalibrator`

---

## EC-06 — Very Long Reviews

### Scenario

Long-form content exceeds embedding or token limits:

- Reddit threads (2,000+ words)
- Google Form free-text responses
- Copy-pasted rants or story-format reviews
- Multi-topic posts covering delivery + discovery + pricing

Architecture specifies: chunk at **512 tokens**, **64-token overlap** for Reddit; single chunk for short reviews.

### Detection

| Signal | Threshold |
|--------|-----------|
| Token count > 512 | Trigger chunking |
| Token count > 8,000 | Flag `very_long`; cap chunks processed |
| Multiple topics detected | Optional multi-theme split via Flash tagging |

### System Behavior

1. **Chunking:** Split into overlapping chunks; each gets own `chunk_id`, shared `document_id`.
2. **Embedding:** Embed each chunk separately; store in `document_chunks`.
3. **Retrieval:** Return chunk-level matches; `BundleBuilder` dedupes by parent `document_id` (keep highest-scoring chunk).
4. **Excerpt:** Show 300-char excerpt from best-matching chunk; link to full document in Source Browser.
5. **Token budget:** When assembling evidence for Gemini, include top 1–2 chunks per long doc, not all chunks.
6. **Synthesis:** Prompt notes *"Long source truncated; see document_id for full text."*

### Stakeholder Output

Source Browser shows full text with chunk highlights. Insight cards show concise excerpt only.

### Edge-within-edge

| Sub-case | Behavior |
|----------|----------|
| Long but low relevance | Reranker deprioritizes; may exclude from bundle |
| Long Reddit thread, one relevant sentence | Semantic chunk retrieves correct paragraph |
| Form response > limit | Truncate tail with `[truncated]` marker; log warning |

### Related Components

`Chunker`, `EmbeddingPipeline`, `BundleBuilder`, `TokenBudget`, Source Browser

---

## EC-07 — Fake Reviews

### Scenario

Reviews that are not genuine user feedback:

- Paid / incentivized app store reviews (generic praise)
- Competitor sabotage (coordinated 1-star campaigns)
- Bot farms (timing clusters, identical phrasing)
- Astroturfing on Reddit (new accounts, promotional tone)
- Synthetic form responses (duplicate IP, straight-line answers)

Distinct from **spam** (EC-03): fake reviews may be grammatically coherent and topically relevant but **inauthentic**.

### Detection

| Signal | Heuristic |
|--------|-----------|
| Temporal burst | >20 reviews same hour, same star rating |
| Account age (Reddit) | Account <7 days + promotional content |
| Template similarity | Cluster of reviews with >90% structural similarity |
| Form straight-lining | Same answer pattern across all questions |
| Rating-text mismatch | 5 stars + exclusively negative discovery language |
| Helpfulness zero (Play) | Low engagement on extreme ratings |
| IP / device fingerprint (forms) | Duplicate submissions |

### System Behavior

1. **Score, don't silently drop (default):** Assign `authenticity_score: 0.0–1.0`.
2. **Threshold policy:**
   - `< 0.3` → exclude from retrieval and synthesis
   - `0.3–0.6` → include with `low_authenticity` flag; cap insight confidence at Medium
   - `> 0.6` → normal processing
3. **Review bombing window:** Ops-configurable blackout dates excluded from trend detection.
4. **Never accuse publicly:** Internal flag only; stakeholder copy says *"coordinated feedback pattern detected"* not *"fake reviews."*
5. **Audit:** Store authenticity signals in enrichment metadata for analyst review.

### Stakeholder Output

When coordinated campaign affects a theme:

```
Theme: Delivery speed complaints (Jan 12–13 spike)
Confidence: Medium
Note: Cluster of 34 similar 1-star reviews detected in 6-hour window, 
      possibly coordinated. Excluded from mention count; included in 
      contradiction log for transparency.
Unique mention count: 8 (excluding coordinated cluster)
```

### Mitigation

| Action | Detail |
|--------|--------|
| Cross-validate with Reddit + Forms | Single-source bursts discounted |
| Human analyst confirmation before roadmap action | Required for high-impact claims |
| Do not base legal or PR responses solely on AI flags | Policy |

### Related Components

`PreEnricher`, `IngestValidator`, `ThemeAggregator`, `TrendDetector`, `contradiction_log`

---

## EC-08 — Hallucination Prevention

### Scenario

Gemini generates content not grounded in retrieved evidence:

- Fabricated user quotes
- Invented `document_id` citations
- Overgeneralization (*"All users hate produce"*) from 2 mentions
- False category or segment attribution
- Confident recommendations with no supporting evidence

**Critical edge case.** Primary trust risk for the engine.

### Detection & Prevention (Defense in Depth)

| Layer | Control |
|-------|---------|
| **Prompt** | Negative constraints: *"Use only provided evidence; never invent quotes or IDs"* |
| **Structured output** | Require `citations: [{document_id, quote}]` per claim |
| **Retrieval** | No synthesis without non-empty Evidence Bundle |
| **GroundingValidator** | Every `document_id` must exist in bundle |
| **Quote fidelity** | Fuzzy match ≥85% between cited quote and source text |
| **Fabrication block** | Reject if direct quote not in any bundle document |
| **Citation rate** | Reject if >20% citations fail verification |
| **Confidence calibrator** | Downgrade overconfident outputs |
| **Human quarantine** | Failed validation → Analyst Review Queue |

### System Behavior

```
Gemini response
    → CitationExtractor
    → GroundingValidator
        → FAIL: Quarantine + reason GROUNDING_FAILURE
        → PASS: SchemaValidator → BusinessRulesValidator → Publish
```

**Auto-repair (once):** Re-prompt with explicit list of valid `document_id`s and instruction to remove unverified claims.

**Never publish** insights that fail grounding after one repair attempt.

### Stakeholder Output

Published insights always include clickable evidence links. Quarantined insights visible only to Analysts:

```
Quarantine ID: Q-1042
Reason: Citation document_id abc-123 not in evidence bundle
Action: [Regenerate] [Edit manually] [Reject]
```

### Hallucination Anti-Patterns Blocked

| Anti-pattern | Validator rule |
|--------------|----------------|
| Uncited direct quote | `Fabrication block` |
| Generic "users want better UX" | `BusinessRulesValidator` |
| High confidence, 1 source | `ConfidenceCalibrator` |
| Claim about MAC % or order data | Out of scope — reject |
| Competitor pricing facts | Reject unless in user quote |

### Metrics & Targets

| Metric | Target |
|--------|--------|
| Grounding pass rate (after 1 retry) | ≥95% |
| High-confidence precision (human audit) | ≥90% |
| Quarantine rate | <10% |

### Related Components

`PromptBuilder`, `GroundingValidator`, `CitationExtractor`, `ProvenanceLinker`, `QuarantineService`, `ValidationPipeline`

---

## EC-09 — Rate Limiting

### Scenario

External APIs throttle or reject requests due to volume:

| API | Typical limit trigger |
|-----|----------------------|
| Google Play scraper / API | IP-based throttling |
| App Store Connect | Daily quota |
| Reddit (PRAW) | 60 requests/minute OAuth |
| Google Sheets / Forms | 100 requests/100 seconds/user |
| Gemini (Vertex AI) | RPM / TPM quotas |
| Embedding API | Batch size and QPS limits |

### Detection

| Signal | HTTP / SDK code |
|--------|-----------------|
| Rate limited | 429 Too Many Requests |
| Quota exceeded | 403 / RESOURCE_EXHAUSTED |
| Server overload | 503 Service Unavailable |
| Token bucket empty | Internal `RateLimiter` block |

### System Behavior

#### Collection Layer

1. `RetryPolicy`: exponential backoff (1s, 2s, 4s, 8s, max 5 attempts).
2. Per-connector rate budget in config.
3. Failed records → `DeadLetterQueue` after max retries.
4. Partial run status: `PARTIAL_SUCCESS` with error breakdown.

#### Gemini / Embedding Layer

1. `RateLimiter`: token bucket per minute (configurable RPM/TPM).
2. Queue excess requests; do not drop silently.
3. `RetryHandler`: 3 retries with jitter on 429/503.
4. **Synthesis:** Fail loud — alert ops; do not substitute with ungrounded fallback text.
5. **Tagging (Flash):** Acceptable to defer batch to next schedule slot.

#### Dashboard / API Layer

1. Rate limit ad-hoc analysis triggers: max 5 per analyst per hour.
2. Return `429` with `Retry-After` header.

### Stakeholder Output

Dashboard when synthesis queued:

```
Analysis run AR-8821: Queued (API rate limit)
Estimated completion: ~15 minutes
You will be notified when ready.
```

Ingestion ops alert:

```
ALERT: Play Store connector rate limited. Run PARTIAL_SUCCESS. 
847/1000 records fetched. Retry scheduled in 30 minutes.
```

### Mitigation

| Action | Detail |
|--------|--------|
| Stagger source schedules | Play 02:00, Reddit 03:00, App Store 04:00 UTC |
| Batch embedding in off-peak windows | Composer DAG |
| Request quota increase (Vertex AI) | Production onboarding |
| Cache retrieval bundles | Reduce repeat Gemini calls |
| Circuit breaker | Pause connector 15 min after 5 consecutive 429s |

### Related Components

`RetryPolicy`, `RateLimiter`, `RetryHandler`, `DeadLetterQueue`, `CollectionRunner`, `AnalysisTriggerService`

---

## EC-10 — Empty Search

### Scenario

User or system search returns zero results:

- Dashboard Source Browser: query *"organic pet food discovery"*
- Retrieval: no documents match RQ + category + segment + recency filters
- Semantic search below similarity threshold
- Filters too restrictive (all 4 dimensions applied)
- Typo or taxonomy mismatch (*"snacks"* vs. internal *"Munchies"*)

Distinct from **EC-01 No Reviews** (corpus empty globally) — here the **corpus exists** but **query matches nothing**.

### Detection

| Signal | Location |
|--------|----------|
| `candidates.length = 0` after all strategies | RetrievalRouter |
| Semantic max score < threshold (e.g., 0.65) | SemanticStrategy |
| FTS no matches | FTSStrategy |
| Cross-source balancer cannot fill bundle | BundleBuilder |

### System Behavior

1. **Relaxation cascade** (automatic, logged):

   ```
   Step 1: Original query
   Step 2: Drop segment filter
   Step 3: Widen recency 180 → 365 days
   Step 4: Drop category filter (keep RQ)
   Step 5: Lower semantic threshold 0.65 → 0.55
   Step 6: Return empty with suggestions
   ```

2. **Do not call Gemini** if bundle still empty after relaxation (unless analyst forces with override — Admin only).

3. **Suggest:** Alternate keywords, related L1 categories from taxonomy, nearest semantic neighbors (if score 0.55–0.65).

4. **Cache negative results** briefly (5 min) to avoid repeat API cost.

### Stakeholder Output

**Dashboard empty search:**

```
No results for "organic pet food discovery"

Suggestions:
• Try broader term: "pet" or "Pet Care"
• Remove segment filter: mission_shopper
• Widen date range to 12 months
• Related category in taxonomy: Pet (L1)

Nearest themes (partial match): deal_discovery (0.58), assortment_gap (0.56)
[Run suggested search]
```

**API response:**

```json
{
  "status": "empty",
  "bundle_id": null,
  "relaxation_steps_applied": ["drop_segment", "widen_recency"],
  "suggestions": ["pet", "Pet Care"],
  "nearest_neighbors": []
}
```

### Mitigation

| Action | Detail |
|--------|--------|
| Taxonomy synonym map | "snacks" → "Munchies" L1 |
| Did-you-mean on FTS | PostgreSQL trigram |
| Default dashboard filters | Broader than ad-hoc |
| Log empty searches | Product insight for taxonomy gaps |

### Related Components

`RetrievalRouter`, `FTSStrategy`, `TaxonomyRepository`, Dashboard Source Browser, `AnalysisTriggerService`

---

## EC-11 — Low Confidence Insights

### Scenario

Insights that meet minimum publish rules but carry **Low** or downgraded **Medium** confidence:

- Single source type only
- ≤2 independent mentions
- Stale data majority (>180 days)
- Contradictory evidence present
- Mixed-language penalty applied
- Low authenticity score on underlying reviews
- Segment inferred, not stated in form data

Per `context.md`, Low confidence is valid output — not a failure — but must be labeled and handled differently.

### Detection

| Rule | Confidence impact |
|------|-------------------|
| `<2 source types` | Cannot be High |
| `<3 mentions` | Cannot be High |
| Contradiction detected | Cap at Medium |
| Majority evidence >180d | Add `stale_data` flag |
| `authenticity_score < 0.6` | Cap at Medium |
| Single viral Reddit thread | Likely Low — flag `single_thread_risk` |

### System Behavior

1. **Publish** Low/Medium insights to dashboard (transparency over silence).
2. **Exclude** Low confidence from Executive Overview top-5 auto-selection (configurable).
3. **Exclude** Low from opportunity backlog **ranking** top tier; show in separate "Emerging signals" section.
4. **Do not** use Low confidence insights as sole input for monthly report executive summary.
5. **Badge** all Low/Medium cards with confidence + rationale tooltip.
6. **Analyst action:** "Promote to research" button triggers Google Form follow-up survey design (manual, out of system).

### Stakeholder Output

**Low confidence insight card:**

```
Theme: Premium organic produce interest
Confidence: Low
Rationale: 2 mentions, single source (Reddit), both from same thread, 
           data >200 days old.

Summary: Two users in r/bangalore mentioned wanting organic produce on Blinkit.
         Insufficient evidence to generalize.

Recommended action: Monitor; consider targeted survey before merchandising bet.
Action owner: Merchandising (research needed)
[View evidence] [Add to watchlist]
```

**Monthly report handling:**

> *3 emerging low-confidence signals included in appendix; not counted in top-5 themes.*

### Mitigation

| Action | When |
|--------|------|
| Widen collection | Persistent Low on important theme |
| Targeted Google Form | Validate segment hypothesis |
| Wait for triangulation | Do not escalate to leadership deck |
| Human promote | Analyst confirms → manual confidence override with audit note |

### Related Components

`ConfidenceCalibrator`, `BusinessRulesValidator`, `ThemeAggregator`, Dashboard `ConfidenceBadge`, Executive Overview filters

---

## EC-12 — Deployment Failures

### Scenario

Infrastructure or release failures in staging or production:

- Cloud Run service fails health check after deploy
- Database migration (`alembic upgrade`) fails mid-way
- Terraform apply partial state
- Secret Manager rotation breaks Gemini credentials
- Cloud SQL connection pool exhaustion
- Composer DAG fails silently
- Frontend/backend version mismatch (API contract break)
- Docker image build failure in CI/CD
- Rollback required after smoke test failure

### Detection

| Signal | Tool |
|--------|------|
| `/health` returns non-200 | Smoke test script |
| Cloud Run revision not serving traffic | GCP console / Monitoring |
| Migration error | Alembic exit code ≠ 0 |
| Error rate spike | Cloud Monitoring alert |
| Gemini auth failure | Structured log `AUTH_ERROR` |
| E2E Playwright failure | CI pipeline |

### System Behavior

#### Deploy Pipeline (Fail-Safe)

```
CI pass → Build image → Deploy staging → Smoke test
    → FAIL: Block prod promotion; keep previous revision
    → PASS: Manual approval → Deploy prod → Smoke test
        → FAIL: Auto-rollback to previous Cloud Run revision
        → PASS: Notify ops; mark release healthy
```

#### Component-Specific Failures

| Failure | Response |
|---------|----------|
| **Migration fails** | Do not route traffic to new revision; run `alembic downgrade -1`; alert DBA |
| **Backend up, DB down** | Return `503` with `database_unavailable`; dashboard shows maintenance banner |
| **Gemini unavailable** | Retrieval and browse still work; synthesis returns `503` with retry guidance |
| **Redis down** | Degrade to uncached retrieval; log warning; no user-facing error |
| **Ingestion DAG fails** | Previous corpus retained; alert ops; dashboard shows "Data last updated X days ago" |
| **Partial Terraform** | Do not destroy; `terraform apply` fix-forward; state lock enforced |

#### Data Integrity Rules During Failure

- Never deploy insight generator without successful migration
- Never delete `source_documents` on rollback
- Analysis runs in progress: mark `FAILED_DEPLOY` not lost; retryable

### Stakeholder Output

**Dashboard maintenance banner:**

```
Service notice: Insight generation temporarily unavailable (estimated 30 min).
Browse existing insights and source data remain available.
Last data refresh: 2026-07-28 02:00 IST
Incident: INC-2044 [View status]
```

**Ops runbook trigger:** `docs/runbooks/deployment_checklist.md`

### Rollback Procedure

1. Route 100% traffic to previous Cloud Run revision (`N-1`).
2. If migration applied: assess forward-fix vs. downgrade (DBA decision).
3. Verify smoke tests on `N-1`.
4. Post-incident: root cause in `analysis_runs` equivalent for deploys (release log).

### Recovery Targets

| Component | RTO | RPO |
|-----------|-----|-----|
| Cloud Run API | 15 min (rollback) | 0 |
| Cloud SQL | 4 hours | 1 hour |
| Vector index rebuild | 8 hours | 24 hours |
| Full pipeline operational | 4 hours | Last successful ingestion |

### Mitigation

| Action | Detail |
|--------|--------|
| Blue/green Cloud Run deploy | Required for prod |
| Migration test on staging clone | Pre-prod gate |
| Feature flags for synthesis | Disable LLM without full rollback |
| Synthetic monitoring every 5 min | `/health`, `/api/v1/insights?limit=1` |
| DR drill quarterly | Cloud SQL PITR restore |

### Related Components

Terraform modules, GitHub Actions workflows, `SmokeTestRunner`, Cloud Monitoring alerts, runbooks, Cloud Run revision management

---

## Cross-Cutting Decision Matrix

When multiple edge cases overlap, apply rules in this order:

| Priority | Rule |
|----------|------|
| 1 | **Safety & compliance** — PII, auth failures, hallucination → block publish |
| 2 | **Data integrity** — Dedup, fake cluster exclusion, grounding |
| 3 | **Transparency** — Contradictions surfaced, confidence labeled |
| 4 | **Availability** — Degrade gracefully (browse without synthesis) |
| 5 | **Completeness** — Relaxation cascade for empty search |

**Example:** Conflicting + low authenticity + single source → **Low confidence**, contradiction logged, coordinated cluster excluded, publish to "Emerging signals" only.

---

## Monitoring & Alerts Summary

| Edge Case | Alert Condition | Severity |
|-----------|-----------------|----------|
| EC-01 No reviews | 3 consecutive `SUCCESS_EMPTY` ingestion runs | Warning |
| EC-02 Conflicting | No alert (expected); log to contradiction_log | Info |
| EC-03 Spam | Rejection rate >30% in single run | Warning |
| EC-04 Duplicate | Dedup rate >50% (possible connector bug) | Warning |
| EC-05 Mixed language | >40% excluded for language in run | Info |
| EC-06 Very long | Chunk count >20 per document | Info |
| EC-07 Fake | Authenticity exclusion >15% of run | Warning |
| EC-08 Hallucination | Grounding fail rate >10% | Critical |
| EC-09 Rate limiting | 5 consecutive 429s on any connector | Warning |
| EC-10 Empty search | >100 empty searches/day (taxonomy gap signal) | Info |
| EC-11 Low confidence | >60% of new insights Low in cycle | Info |
| EC-12 Deployment | Smoke test fail or error rate >5% | Critical |

---

## Testing Requirements

Each edge case must have corresponding tests (see `implementation-plan.md`):

| Edge Case | Test Type | Fixture |
|-----------|-----------|---------|
| EC-01 | Integration | Empty corpus DB |
| EC-02 | Unit + Integration | Opposing sentiment fixture pair |
| EC-03 | Unit | Spam text samples |
| EC-04 | Unit | Duplicate source_id + hash fixtures |
| EC-05 | Unit | Hinglish + Hindi-only samples |
| EC-06 | Unit | 10K-token Reddit post |
| EC-07 | Unit | Burst + template cluster fixture |
| EC-08 | Integration | Gemini mock with bad citations |
| EC-09 | Unit | Mock 429 responses |
| EC-10 | Integration | Seeded DB + zero-match query |
| EC-11 | Unit | Confidence calibrator scenarios |
| EC-12 | Manual + CI | Failed smoke test rollback drill |

---

## Document Relationships

| Document | Role |
|----------|------|
| `context.md` | Confidence rules, triangulation, output quality |
| `architecture.md` | Validation layer, retrieval, deployment design |
| `implementation-plan.md` | Phase ownership of edge case handlers |
| `edge-case.md` (this file) | Failure modes and behavioral specification |

---

*Edge cases are operational requirements, not exceptions. The engine must fail visibly, label uncertainty honestly, and never trade trust for completeness.*
