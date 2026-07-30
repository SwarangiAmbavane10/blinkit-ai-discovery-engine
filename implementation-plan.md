# AI Product Discovery Engine — Implementation Plan

**Organization:** Blinkit  
**Document Type:** Implementation Plan  
**Version:** 1.0  
**Last Updated:** July 2026  
**Source:** `architecture.md`

---

## Overview

This plan breaks implementation into **seven sequential phases**. Each phase delivers testable artifacts before the next begins. Phases map to `architecture.md` layers as follows:

| Implementation Phase | Architecture Components |
|---------------------|-------------------------|
| Phase 1 — Review Collection | Source connectors, raw export storage |
| Phase 2 — Review Cleaning | Normalizer, dedup, PII, enrichment, repository, ingest validation |
| Phase 3 — Review Retrieval | Embeddings, vector index, retrieval router, evidence bundles |
| Phase 4 — LLM Integration | Prompt Builder, Gemini Gateway, model routing |
| Phase 5 — Insight Engine | Insight Generator, Validation Layer, provenance linking |
| Phase 6 — Dashboard | Next.js frontend, Dashboard API, exports |
| Phase 7 — Deployment | GCP infra, CI/CD, observability, production hardening |

### Recommended Project Layout

```
blinkit-ai-discovery-engine/
├── backend/
│   ├── src/discovery_engine/
│   ├── tests/
│   ├── alembic/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   └── package.json
├── prompts/
├── schemas/
├── infra/terraform/
├── dags/
├── docker/
├── docs/
└── scripts/
```

### Phase Dependency Graph

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7
                              ↗___________↗
                         (Phase 4 needs Phase 3 bundles;
                          Phase 5 needs Phase 4 responses)
```

---

## Phase 1 — Review Collection

Acquire raw user feedback from Google Play, Apple App Store, Reddit, and Google Forms. Persist raw exports for audit and downstream cleaning.

### Objectives

1. Implement four source connectors with a shared interface
2. Extract required fields per source per `architecture.md` §4.2
3. Support batch runs (Play, App Store, Reddit) and event-style loads (Google Forms CSV/webhook)
4. Persist raw payloads to object storage with ingestion run lineage
5. Handle retries, rate limits, and idempotent source IDs at collection time
6. Provide CLI entry points for manual and scheduled collection

### Files

| Path | Purpose |
|------|---------|
| `backend/pyproject.toml` | Python project; dependencies: `httpx`, `praw`, `google-play-scraper`, `pydantic`, `python-dotenv` |
| `backend/src/discovery_engine/__init__.py` | Package root |
| `backend/src/discovery_engine/config/settings.py` | Env-based config: API keys, app IDs, subreddit list |
| `backend/src/discovery_engine/config/constants.py` | Source type enums, Blinkit app identifiers |
| `backend/src/discovery_engine/collection/base_connector.py` | Abstract connector interface |
| `backend/src/discovery_engine/collection/play_store_connector.py` | Google Play review fetcher |
| `backend/src/discovery_engine/collection/app_store_connector.py` | App Store Connect / export reader |
| `backend/src/discovery_engine/collection/reddit_connector.py` | Reddit API (PRAW) crawler |
| `backend/src/discovery_engine/collection/google_form_connector.py` | Sheets API / CSV / webhook parser |
| `backend/src/discovery_engine/collection/models/raw_record.py` | Pydantic model for unnormalized source records |
| `backend/src/discovery_engine/collection/models/ingestion_run.py` | Run metadata: run_id, source, started_at, status |
| `backend/src/discovery_engine/collection/runner/collection_runner.py` | Orchestrates connector execution |
| `backend/src/discovery_engine/collection/runner/retry_policy.py` | Exponential backoff, max retries |
| `backend/src/discovery_engine/storage/raw_store.py` | Local/GCS raw JSON export writer |
| `backend/src/discovery_engine/storage/dead_letter_queue.py` | Failed record queue |
| `backend/src/discovery_engine/cli/collect.py` | CLI: `collect --source play_store --since 2026-01-01` |
| `backend/tests/collection/test_play_store_connector.py` | Unit tests with mocked responses |
| `backend/tests/collection/test_reddit_connector.py` | Unit tests with mocked PRAW |
| `backend/tests/collection/test_google_form_connector.py` | CSV fixture tests |
| `backend/tests/collection/test_collection_runner.py` | Runner orchestration tests |
| `backend/tests/fixtures/raw/play_store_sample.json` | Sample raw Play Store payload |
| `backend/tests/fixtures/raw/reddit_sample.json` | Sample Reddit thread |
| `backend/tests/fixtures/raw/google_form_sample.csv` | Sample form export |
| `docker/docker-compose.dev.yml` | Local dev services stub (MinIO optional for GCS emulation) |
| `.env.example` | Template for Reddit, App Store, GCS credentials |
| `scripts/run_collection.sh` | Shell wrapper for batch collection |

### Classes

| Class | Responsibility |
|-------|----------------|
| `BaseConnector` | Abstract: `fetch(since: datetime) -> list[RawRecord]`, `source_type` property |
| `PlayStoreConnector` | Fetches Blinkit Play Store reviews via public API/scraper |
| `AppStoreConnector` | Fetches iOS reviews via App Store Connect or CSV import |
| `RedditConnector` | Crawls configured subreddits/keywords for Blinkit mentions |
| `GoogleFormConnector` | Reads form responses from Sheets API, CSV, or webhook payload |
| `RawRecord` | Pydantic model: `source_type`, `source_id`, `payload: dict`, `fetched_at` |
| `IngestionRun` | Tracks run lifecycle: `run_id`, `connector_version`, `record_count`, `status` |
| `CollectionRunner` | Instantiates connector, applies retry policy, writes to raw store |
| `RetryPolicy` | Configurable backoff for transient API failures |
| `RawStore` | Writes `{run_id}/{source_type}/{source_id}.json` to local path or GCS |
| `DeadLetterQueue` | Persists records that fail after max retries |

### Outputs

| Output | Description |
|--------|-------------|
| Raw JSON files | One file per source record in `raw/{run_id}/` |
| `IngestionRun` manifest | JSON summary: counts, errors, duration, connector versions |
| Dead-letter records | Failed fetches with error reason for ops review |
| Collection logs | Structured JSON logs: source, run_id, record_count, latency |
| CLI exit codes | `0` success, `1` partial failure, `2` fatal error |

### Testing

| Test Type | Scope | Pass Criteria |
|-----------|-------|---------------|
| **Unit** | Each connector with mocked HTTP/PRAW | Required fields extracted; empty response handled |
| **Unit** | `RetryPolicy` | Retries on 429/503; stops after max attempts |
| **Unit** | `RawStore` | Writes idempotent paths; overwrites same `source_id` in same run |
| **Integration** | `CollectionRunner` + fixture files | End-to-end write of ≥10 fixture records to temp dir |
| **Contract** | Raw record shape vs. Phase 2 input | `RawRecord.payload` consumable by normalizer |
| **Manual** | Live Play Store fetch (optional, gated) | ≥1 real review returned for Blinkit app ID |
| **Regression** | Snapshot of normalized field mapping doc | Field mapping table matches architecture §4.2 |

**Test commands:**

```bash
cd backend && pytest tests/collection/ -v
cd backend && pytest tests/collection/ --cov=discovery_engine.collection --cov-report=term-missing
```

---

## Phase 2 — Review Cleaning

Transform raw records into Canonical Review Documents (CRDs), deduplicate, redact PII, apply rule-based pre-enrichment, validate, and persist to PostgreSQL.

### Objectives

1. Normalize all four source types to unified CRD schema (`architecture.md` §4.3)
2. Deduplicate by `(source_type, source_id)` and content hash
3. Redact PII (email, phone, address patterns)
4. Apply rule-based discovery signal tagging and category mention extraction
5. Validate ingest schema and reject poison records
6. Provision PostgreSQL schema, migrations, and repository write layer
7. Generate `tsvector` full-text index columns for Phase 3 fallback search

### Files

| Path | Purpose |
|------|---------|
| `backend/src/discovery_engine/cleaning/normalizer.py` | Source-specific → CRD mapping |
| `backend/src/discovery_engine/cleaning/normalizers/play_store_normalizer.py` | Play Store field mapping |
| `backend/src/discovery_engine/cleaning/normalizers/app_store_normalizer.py` | App Store field mapping |
| `backend/src/discovery_engine/cleaning/normalizers/reddit_normalizer.py` | Reddit post/comment mapping |
| `backend/src/discovery_engine/cleaning/normalizers/google_form_normalizer.py` | Form Q&A flattening to text |
| `backend/src/discovery_engine/cleaning/deduplicator.py` | Hash + source-id dedup logic |
| `backend/src/discovery_engine/cleaning/pii_redactor.py` | Regex-based PII removal |
| `backend/src/discovery_engine/cleaning/text_utils.py` | Encoding cleanup, whitespace, emoji handling |
| `backend/src/discovery_engine/cleaning/language_detector.py` | Language tag (en, hi, etc.) |
| `backend/src/discovery_engine/cleaning/pre_enricher.py` | Keyword discovery signal scanner |
| `backend/src/discovery_engine/cleaning/category_extractor.py` | Raw category term extraction |
| `backend/src/discovery_engine/cleaning/pipeline/cleaning_pipeline.py` | Stage orchestrator |
| `backend/src/discovery_engine/domain/models/source_document.py` | CRD Pydantic/SQLAlchemy model |
| `backend/src/discovery_engine/domain/models/enrichment_record.py` | Pre-enrichment tags model |
| `backend/src/discovery_engine/domain/models/taxonomy_mapping.py` | L1/L2 category mapping model |
| `backend/src/discovery_engine/validation/ingest_validator.py` | Schema, allowlist, text quality checks |
| `backend/src/discovery_engine/repository/document_repository.py` | CRUD for `source_documents` |
| `backend/src/discovery_engine/repository/enrichment_repository.py` | CRUD for `enrichment_records` |
| `backend/src/discovery_engine/repository/taxonomy_repository.py` | Category taxonomy CRUD |
| `backend/src/discovery_engine/db/session.py` | SQLAlchemy async session factory |
| `backend/src/discovery_engine/db/base.py` | Declarative base |
| `backend/alembic/versions/001_create_source_documents.py` | Initial migration |
| `backend/alembic/versions/002_create_enrichment_taxonomy.py` | Enrichment + taxonomy tables |
| `backend/alembic/versions/003_add_fts_tsvector.py` | Full-text search column + GIN index |
| `backend/data/taxonomy/blinkit_categories_l1.json` | Seed L1 category taxonomy |
| `backend/data/rules/discovery_keywords.json` | Discovery signal keyword list |
| `backend/src/discovery_engine/cli/clean.py` | CLI: `clean --run-id {uuid}` |
| `backend/tests/cleaning/test_normalizers.py` | Per-source normalization |
| `backend/tests/cleaning/test_deduplicator.py` | Dedup scenarios |
| `backend/tests/cleaning/test_pii_redactor.py` | PII patterns removed |
| `backend/tests/cleaning/test_pre_enricher.py` | Keyword tagging accuracy |
| `backend/tests/cleaning/test_cleaning_pipeline.py` | End-to-end pipeline |
| `backend/tests/validation/test_ingest_validator.py` | Validation rules |
| `backend/tests/repository/test_document_repository.py` | DB integration (testcontainers) |
| `docker/docker-compose.dev.yml` | Add PostgreSQL 15 service |
| `schemas/crd.schema.json` | JSON Schema for CRD (shared with validation) |

### Classes

| Class | Responsibility |
|-------|----------------|
| `PlayStoreNormalizer` | Maps Play Store raw → `SourceDocument` |
| `AppStoreNormalizer` | Maps App Store raw → `SourceDocument` |
| `RedditNormalizer` | Merges title + body; sets subreddit metadata |
| `GoogleFormNormalizer` | Flattens Q&A pairs into searchable text + metadata |
| `Normalizer` (facade) | Routes raw record to source-specific normalizer |
| `Deduplicator` | `is_duplicate(source_type, source_id, content_hash) -> bool` |
| `PIIRedactor` | `redact(text: str) -> str` |
| `LanguageDetector` | Returns ISO language code |
| `PreEnricher` | Applies discovery keyword rules; sets signal density score |
| `CategoryExtractor` | Extracts raw category mentions from text |
| `CleaningPipeline` | Runs: normalize → dedup → PII → language → pre-enrich → validate → persist |
| `SourceDocument` | ORM/Pydantic CRD entity |
| `EnrichmentRecord` | Pre-enrichment tags: signals, raw categories, language |
| `TaxonomyMapping` | Maps raw terms → Blinkit L1/L2 |
| `IngestValidator` | Validates CRD schema, source allowlist, min text length |
| `DocumentRepository` | Upsert documents; query by source, date, hash |
| `EnrichmentRepository` | Persist/retrieve enrichment records linked to documents |
| `TaxonomyRepository` | Load and resolve category mappings |

### Outputs

| Output | Description |
|--------|-------------|
| `source_documents` rows | Clean CRDs in PostgreSQL |
| `enrichment_records` rows | Pre-enrichment tags per document |
| `taxonomy_mappings` seed data | Blinkit L1 categories loaded |
| Cleaning run report | Accepted/rejected/skipped counts per run |
| Rejected record log | Validation failures with reason codes |
| `tsvector` index | Full-text search ready on `source_documents.text` |

### Testing

| Test Type | Scope | Pass Criteria |
|-----------|-------|---------------|
| **Unit** | Each normalizer with fixtures | All CRD required fields populated correctly |
| **Unit** | `Deduplicator` | Same `source_id` skipped; changed content hash updates |
| **Unit** | `PIIRedactor` | Email/phone stripped; review text preserved |
| **Unit** | `PreEnricher` | Discovery keywords flag `signal_density > 0` |
| **Unit** | `IngestValidator` | Rejects <10 chars, unknown source, missing fields |
| **Integration** | `CleaningPipeline` + PostgreSQL testcontainer | Raw fixtures → CRDs in DB |
| **Integration** | Idempotent re-run | Second clean of same run produces 0 duplicates |
| **Performance** | 1,000 document batch | Completes in <60s on dev hardware |
| **Data quality** | Sample audit (manual) | 50 random CRDs human-reviewed for normalization accuracy ≥95% |

**Test commands:**

```bash
docker compose -f docker/docker-compose.dev.yml up -d postgres
cd backend && alembic upgrade head
cd backend && pytest tests/cleaning/ tests/validation/ tests/repository/ -v
cd backend && python -m discovery_engine.cli.clean --run-id test-fixture-run
```

---

## Phase 3 — Review Retrieval

Embed cleaned documents, index vectors in pgvector, and implement hybrid retrieval that assembles Evidence Bundles for downstream LLM synthesis.

### Objectives

1. Chunk long documents (Reddit) per architecture §5.3
2. Generate embeddings via Google `text-embedding-004`
3. Store vectors in pgvector with metadata filters
4. Implement semantic, metadata, and full-text retrieval strategies
5. Cross-source balance and re-rank to produce Evidence Bundles
6. Cache hot bundles in Redis (optional in dev; required in prod)
7. Expose retrieval via internal Python API and FastAPI endpoint

### Files

| Path | Purpose |
|------|---------|
| `backend/src/discovery_engine/embedding/chunker.py` | Token-based chunking (512/64 overlap) |
| `backend/src/discovery_engine/embedding/embedder.py` | Google embedding API client |
| `backend/src/discovery_engine/embedding/embedding_pipeline.py` | Batch embed new/updated documents |
| `backend/src/discovery_engine/embedding/models/document_chunk.py` | Chunk entity with `chunk_id`, `document_id`, `text` |
| `backend/alembic/versions/004_enable_pgvector.py` | pgvector extension + embedding column |
| `backend/alembic/versions/005_create_document_chunks.py` | Chunks table with vector index |
| `backend/src/discovery_engine/retrieval/models/query_context.py` | QueryContext Pydantic model |
| `backend/src/discovery_engine/retrieval/models/evidence_bundle.py` | EvidenceBundle + EvidenceItem models |
| `backend/src/discovery_engine/retrieval/strategies/semantic_strategy.py` | Vector KNN search |
| `backend/src/discovery_engine/retrieval/strategies/metadata_strategy.py` | SQL filter by RQ, category, recency |
| `backend/src/discovery_engine/retrieval/strategies/fts_strategy.py` | PostgreSQL tsvector search |
| `backend/src/discovery_engine/retrieval/strategies/contradiction_strategy.py` | Opposing sentiment fetch |
| `backend/src/discovery_engine/retrieval/cross_source_balancer.py` | Enforce ≥N source types |
| `backend/src/discovery_engine/retrieval/reranker.py` | Weighted composite scoring |
| `backend/src/discovery_engine/retrieval/retrieval_router.py` | Routes query to strategies |
| `backend/src/discovery_engine/retrieval/bundle_builder.py` | Assembles final EvidenceBundle |
| `backend/src/discovery_engine/retrieval/cache/bundle_cache.py` | Redis get/set with TTL |
| `backend/src/discovery_engine/repository/chunk_repository.py` | Chunk + vector persistence |
| `backend/src/discovery_engine/repository/bundle_repository.py` | Persist bundles for audit |
| `backend/src/discovery_engine/api/routes/retrieval.py` | `POST /api/v1/retrieve` |
| `backend/src/discovery_engine/api/main.py` | FastAPI app entry |
| `backend/src/discovery_engine/cli/embed.py` | CLI: `embed --since 2026-01-01` |
| `backend/tests/embedding/test_chunker.py` | Chunk boundaries |
| `backend/tests/embedding/test_embedding_pipeline.py` | Mock embedder batch |
| `backend/tests/retrieval/test_semantic_strategy.py` | KNN with test vectors |
| `backend/tests/retrieval/test_cross_source_balancer.py` | Source diversity enforcement |
| `backend/tests/retrieval/test_reranker.py` | Score ordering |
| `backend/tests/retrieval/test_bundle_builder.py` | Bundle shape + metadata |
| `backend/tests/retrieval/test_retrieval_router.py` | End-to-end retrieval integration |
| `docker/docker-compose.dev.yml` | Add Redis service |
| `schemas/query_context.schema.json` | QueryContext JSON Schema |
| `schemas/evidence_bundle.schema.json` | EvidenceBundle JSON Schema |

### Classes

| Class | Responsibility |
|-------|----------------|
| `Chunker` | Splits long text; single chunk for short reviews |
| `DocumentChunk` | Chunk model with embedding vector reference |
| `Embedder` | Calls Google embedding API; batch support |
| `EmbeddingPipeline` | Finds unembedded docs → chunk → embed → persist |
| `QueryContext` | RQ, themes, categories, segments, filters, limits |
| `EvidenceItem` | `document_id`, excerpt, source_tag, timestamp, score |
| `EvidenceBundle` | Items list + metadata (source distribution, bundle_id) |
| `SemanticStrategy` | pgvector cosine similarity search |
| `MetadataStrategy` | SQL filters on enrichment tags + recency |
| `FTSStrategy` | `tsvector` keyword fallback |
| `ContradictionStrategy` | Retrieves opposing-sentiment docs for same theme |
| `CrossSourceBalancer` | Ensures minimum source type diversity |
| `Reranker` | Weighted scoring: relevance, recency, diversity, signals |
| `RetrievalRouter` | Selects and merges strategy results |
| `BundleBuilder` | Final assembly, excerpt truncation (300 chars), metadata |
| `BundleCache` | Redis cache keyed by query context hash |
| `ChunkRepository` | Vector insert/query |
| `BundleRepository` | Audit persistence of bundles |

### Outputs

| Output | Description |
|--------|-------------|
| `document_chunks` rows | Text chunks with embedding vectors |
| `EvidenceBundle` JSON | Ranked documents ready for Prompt Builder |
| Bundle audit records | Stored bundles linked to future `analysis_runs` |
| Embedding pipeline report | Documents embedded, failures, token usage |
| `POST /api/v1/retrieve` response | API-accessible bundle for Phase 4+ integration |
| Cache entries | Redis keys for repeated RQ queries |

### Testing

| Test Type | Scope | Pass Criteria |
|-----------|-------|---------------|
| **Unit** | `Chunker` | 600-token Reddit post → 2+ chunks with overlap |
| **Unit** | `Reranker` | Recency boost moves newer doc above older |
| **Unit** | `CrossSourceBalancer` | Inserts second source type when only one present |
| **Integration** | `EmbeddingPipeline` + mock embedder | Chunks persisted with 768/3072-dim vectors |
| **Integration** | `RetrievalRouter` + seeded DB | QueryContext RQ2 → bundle with ≥5 items |
| **Integration** | Cross-source rule | Bundle with `min_sources=2` has ≥2 source types when data exists |
| **API** | `POST /api/v1/retrieve` | Returns 200 + valid EvidenceBundle schema |
| **Performance** | Retrieval latency | p95 <500ms for 10K document corpus (dev) |
| **Quality** | Manual relevance check | Top-10 results relevant to 5 test queries (≥7/10 rated relevant) |

**Test commands:**

```bash
cd backend && pytest tests/embedding/ tests/retrieval/ -v
cd backend && python -m discovery_engine.cli.embed --all
curl -X POST http://localhost:8000/api/v1/retrieve -H "Content-Type: application/json" -d @tests/fixtures/query_rq2.json
```

---

## Phase 4 — LLM Integration

Implement Prompt Builder and Gemini Gateway with model routing, structured JSON output, retry/rate-limit handling, and analysis run audit logging.

### Objectives

1. Load versioned prompt templates from `prompts/` registry
2. Inject `context.md` grounding, evidence bundles, and output JSON schemas
3. Route tasks to Gemini Flash (tagging) vs. Pro (synthesis)
4. Enforce structured output via `response_schema`
5. Record `analysis_runs` with prompt hash, model version, token usage
6. Implement retry, rate limiting, and token budget caps
7. Support multi-pass monthly report orchestration (shell only; full report in Phase 5)

### Files

| Path | Purpose |
|------|---------|
| `prompts/v1/system_instruction.txt` | Base system role from context.md |
| `prompts/v1/tpl_rq_synthesis.txt` | RQ synthesis task template |
| `prompts/v1/tpl_insight_card.txt` | Insight card template |
| `prompts/v1/tpl_segment_profile.txt` | Segment profile template |
| `prompts/v1/tpl_root_cause.txt` | Root-cause tree template |
| `prompts/v1/tpl_opportunity.txt` | Opportunity backlog template |
| `prompts/v1/tpl_monthly_report_pass_a.txt` | Per-RQ mini-synthesis |
| `prompts/v1/tpl_monthly_report_pass_b.txt` | Contradiction consolidation |
| `prompts/v1/tpl_monthly_report_pass_c.txt` | Executive narrative |
| `prompts/v1/negative_constraints.txt` | Shared anti-patterns block |
| `schemas/insight_card.schema.json` | Insight card JSON Schema |
| `schemas/segment_profile.schema.json` | Segment profile JSON Schema |
| `schemas/opportunity_item.schema.json` | Opportunity backlog JSON Schema |
| `schemas/root_cause_tree.schema.json` | Root-cause tree JSON Schema |
| `schemas/monthly_report.schema.json` | Monthly report JSON Schema |
| `backend/src/discovery_engine/llm/models/prompt_package.py` | PromptPackage dataclass |
| `backend/src/discovery_engine/llm/models/gemini_request.py` | Request model |
| `backend/src/discovery_engine/llm/models/gemini_response.py` | Response + TokenUsage model |
| `backend/src/discovery_engine/llm/prompt/template_registry.py` | Load/version templates |
| `backend/src/discovery_engine/llm/prompt/context_loader.py` | Load context.md excerpts |
| `backend/src/discovery_engine/llm/prompt/evidence_formatter.py` | Format bundle as numbered excerpts |
| `backend/src/discovery_engine/llm/prompt/prompt_builder.py` | Assemble PromptPackage |
| `backend/src/discovery_engine/llm/prompt/prompt_hasher.py` | SHA256 of final prompt for audit |
| `backend/src/discovery_engine/llm/gemini/gemini_client.py` | google-genai SDK wrapper |
| `backend/src/discovery_engine/llm/gemini/model_router.py` | Flash vs. Pro routing |
| `backend/src/discovery_engine/llm/gemini/rate_limiter.py` | Token bucket rate limit |
| `backend/src/discovery_engine/llm/gemini/retry_handler.py` | 429/503 retry with jitter |
| `backend/src/discovery_engine/llm/gemini/response_parser.py` | Parse JSON; handle malformed output |
| `backend/src/discovery_engine/llm/gemini/token_budget.py` | Truncate evidence to fit budget |
| `backend/src/discovery_engine/llm/orchestration/multi_pass_runner.py` | Monthly report pass A/B/C |
| `backend/src/discovery_engine/repository/analysis_run_repository.py` | Persist analysis runs |
| `backend/alembic/versions/006_create_analysis_runs.py` | Analysis runs table |
| `backend/src/discovery_engine/api/routes/synthesis.py` | `POST /api/v1/synthesize` |
| `backend/src/discovery_engine/cli/synthesize.py` | CLI: `synthesize --rq RQ2 --template tpl_rq_synthesis` |
| `backend/tests/llm/test_prompt_builder.py` | Template rendering |
| `backend/tests/llm/test_evidence_formatter.py` | Source tags + document IDs |
| `backend/tests/llm/test_model_router.py` | Task → model mapping |
| `backend/tests/llm/test_response_parser.py` | Valid/invalid JSON handling |
| `backend/tests/llm/test_gemini_client.py` | Mock SDK responses |
| `backend/tests/llm/test_multi_pass_runner.py` | Pass orchestration order |
| `backend/tests/fixtures/evidence/sample_bundle.json` | Sample EvidenceBundle |

### Classes

| Class | Responsibility |
|-------|----------------|
| `TemplateRegistry` | Loads templates by ID and version from `prompts/` |
| `ContextLoader` | Reads static business context from docs |
| `EvidenceFormatter` | Formats bundle items: `[Play Store] doc_id: "excerpt"` |
| `PromptBuilder` | Builds `PromptPackage` from template + bundle + schema |
| `PromptHasher` | Computes reproducible prompt hash |
| `PromptPackage` | `system_instruction`, `contents`, `response_schema`, `template_id` |
| `GeminiClient` | Executes API call; returns `GeminiResponse` |
| `ModelRouter` | Maps task type → model name + temperature |
| `RateLimiter` | Token bucket per minute |
| `RetryHandler` | Exponential backoff on transient errors |
| `ResponseParser` | Extracts and validates JSON from model response |
| `TokenBudget` | Truncates evidence list to max input tokens |
| `MultiPassRunner` | Sequences Pass A → B → C for monthly reports |
| `GeminiRequest` / `GeminiResponse` | Request/response dataclasses with usage metadata |
| `AnalysisRunRepository` | Stores run audit trail |

### Outputs

| Output | Description |
|--------|-------------|
| `PromptPackage` | Complete prompt ready for Gemini |
| `GeminiResponse` | Parsed JSON + raw text + token usage |
| `analysis_runs` rows | Audit: prompt_hash, model, bundle_id, latency, status |
| Synthesis API response | Structured JSON matching artifact schema |
| Error/retry logs | Failed calls with retry count and final status |
| CLI synthesis JSON file | `--output insight_rq2.json` for local dev |

### Testing

| Test Type | Scope | Pass Criteria |
|-----------|-------|---------------|
| **Unit** | `PromptBuilder` | All sections present; evidence IDs match bundle |
| **Unit** | `ModelRouter` | Tagging → Flash; synthesis → Pro |
| **Unit** | `ResponseParser` | Parses valid JSON; raises on invalid |
| **Unit** | `TokenBudget` | Truncates to budget; preserves highest-ranked evidence |
| **Unit** | `RetryHandler` | Retries 429; fails after 3 attempts |
| **Integration** | `GeminiClient` with mock | Full request/response cycle recorded |
| **Integration** | `POST /api/v1/synthesize` | Returns schema-valid insight card JSON |
| **Live (gated)** | Real Gemini call | 1 insight card generated; tokens logged |
| **Audit** | `AnalysisRunRepository` | prompt_hash stable for identical inputs |
| **Regression** | Prompt snapshots | Template changes detected in CI |

**Test commands:**

```bash
cd backend && pytest tests/llm/ -v
cd backend && python -m discovery_engine.cli.synthesize --rq RQ2 --output /tmp/rq2.json
# Gated live test:
GEMINI_LIVE=1 pytest tests/llm/test_gemini_live.py -v
```

---

## Phase 5 — Insight Engine

Transform Gemini responses into persisted insight artifacts with provenance linking, aggregation, confidence calibration, and multi-stage validation before publish.

### Objectives

1. Parse Gemini JSON into typed insight artifacts (cards, profiles, opportunities, reports, Q&A)
2. Link every claim to source `document_id` via provenance linker
3. Run 5-stage validation pipeline (grounding → schema → business rules → confidence)
4. Quarantine failed artifacts for analyst review
5. Implement aggregation: theme merge, trend detection, opportunity ranking
6. Persist insights, evidence links, and contradiction log
7. Orchestrate workflows: WF-THEME-DISCOVER, WF-RQ-UPDATE, WF-MONTHLY-REPORT

### Files

| Path | Purpose |
|------|---------|
| `backend/src/discovery_engine/insights/models/insight_card.py` | Thematic insight card model |
| `backend/src/discovery_engine/insights/models/segment_profile.py` | Segment exploration profile |
| `backend/src/discovery_engine/insights/models/barrier_map.py` | Barrier map nodes |
| `backend/src/discovery_engine/insights/models/discovery_pathway.py` | Pathway map model |
| `backend/src/discovery_engine/insights/models/root_cause_tree.py` | Root-cause tree model |
| `backend/src/discovery_engine/insights/models/opportunity_item.py` | Opportunity backlog item |
| `backend/src/discovery_engine/insights/models/monthly_report.py` | Monthly report model |
| `backend/src/discovery_engine/insights/models/qa_entry.py` | Q&A repository entry |
| `backend/src/discovery_engine/insights/parsers/artifact_parser.py` | Gemini JSON → typed models |
| `backend/src/discovery_engine/insights/normalizers/artifact_normalizer.py` | Enum cleanup, field defaults |
| `backend/src/discovery_engine/insights/linkers/provenance_linker.py` | Citation → evidence_links |
| `backend/src/discovery_engine/insights/linkers/citation_extractor.py` | Extract document_id refs from text |
| `backend/src/discovery_engine/insights/aggregators/theme_aggregator.py` | Merge themes within 7-day window |
| `backend/src/discovery_engine/insights/aggregators/trend_detector.py` | new/rising/stable/declining |
| `backend/src/discovery_engine/insights/aggregators/opportunity_ranker.py` | Impact tier scoring |
| `backend/src/discovery_engine/insights/workflows/base_workflow.py` | Abstract workflow |
| `backend/src/discovery_engine/insights/workflows/theme_discover_workflow.py` | WF-THEME-DISCOVER |
| `backend/src/discovery_engine/insights/workflows/rq_update_workflow.py` | WF-RQ-UPDATE |
| `backend/src/discovery_engine/insights/workflows/segment_build_workflow.py` | WF-SEGMENT-BUILD |
| `backend/src/discovery_engine/insights/workflows/monthly_report_workflow.py` | WF-MONTHLY-REPORT |
| `backend/src/discovery_engine/insights/workflows/contradiction_scan_workflow.py` | WF-CONTRADICTION-SCAN |
| `backend/src/discovery_engine/insights/generators/insight_generator.py` | Main orchestrator |
| `backend/src/discovery_engine/validation/grounding_validator.py` | Citation existence + quote fidelity |
| `backend/src/discovery_engine/validation/schema_validator.py` | JSON Schema + Pydantic |
| `backend/src/discovery_engine/validation/business_rules_validator.py` | RQ mapping, actionability |
| `backend/src/discovery_engine/validation/confidence_calibrator.py` | Deterministic confidence override |
| `backend/src/discovery_engine/validation/validation_pipeline.py` | 5-stage orchestrator |
| `backend/src/discovery_engine/validation/quarantine_service.py` | Failed artifact queue |
| `backend/alembic/versions/007_create_insight_artifacts.py` | Insight tables |
| `backend/alembic/versions/008_create_evidence_links.py` | Provenance graph |
| `backend/alembic/versions/009_create_contradiction_log.py` | Contradiction log |
| `backend/src/discovery_engine/repository/insight_repository.py` | Insight CRUD + versioning |
| `backend/src/discovery_engine/repository/evidence_link_repository.py` | Provenance links |
| `backend/src/discovery_engine/repository/quarantine_repository.py` | Quarantine queue |
| `backend/src/discovery_engine/api/routes/insights.py` | `GET/POST /api/v1/insights` |
| `backend/src/discovery_engine/api/routes/quarantine.py` | Analyst quarantine endpoints |
| `backend/src/discovery_engine/cli/generate_insights.py` | CLI workflow runner |
| `backend/tests/insights/test_artifact_parser.py` | Parse all artifact types |
| `backend/tests/insights/test_provenance_linker.py` | Citation verification |
| `backend/tests/insights/test_theme_aggregator.py` | Theme merge logic |
| `backend/tests/insights/test_trend_detector.py` | Trend labels |
| `backend/tests/validation/test_grounding_validator.py` | Fabrication detection |
| `backend/tests/validation/test_business_rules_validator.py` | High-confidence rules |
| `backend/tests/validation/test_confidence_calibrator.py` | Downgrade scenarios |
| `backend/tests/validation/test_validation_pipeline.py` | End-to-end pass/fail |
| `backend/tests/insights/test_monthly_report_workflow.py` | Multi-pass integration |

### Classes

| Class | Responsibility |
|-------|----------------|
| `ArtifactParser` | Deserializes Gemini JSON to typed insight models |
| `ArtifactNormalizer` | Normalizes enums, defaults, empty lists |
| `CitationExtractor` | Finds `document_id` references in claims and quotes |
| `ProvenanceLinker` | Verifies citations; writes `evidence_links` |
| `ThemeAggregator` | Merges duplicate themes; increments evidence count |
| `TrendDetector` | Compares 30/90-day frequency → trend label |
| `OpportunityRanker` | Scores and ranks opportunity backlog items |
| `InsightGenerator` | Coordinates parse → link → validate → persist |
| `GroundingValidator` | Citation exists; fuzzy quote match ≥85% |
| `SchemaValidator` | Pydantic + JSON Schema validation |
| `BusinessRulesValidator` | RQ mapping, High-confidence cross-source rule |
| `ConfidenceCalibrator` | Downgrades overconfident insights |
| `ValidationPipeline` | Runs all validators; returns pass/fail + reasons |
| `QuarantineService` | Routes failures to analyst queue |
| `ThemeDiscoverWorkflow` | Retrieval → synthesize → validate → publish cards |
| `RQUpdateWorkflow` | Updates Q&A repository entry for one RQ |
| `MonthlyReportWorkflow` | Multi-pass synthesis + consolidation |
| `ContradictionScanWorkflow` | Detects and logs conflicting themes |
| `InsightRepository` | Versioned insight persistence |
| `EvidenceLinkRepository` | Provenance graph CRUD |
| `QuarantineRepository` | Quarantine queue storage |

### Outputs

| Output | Description |
|--------|-------------|
| `insight_artifacts` rows | Published insight cards, profiles, reports (JSONB) |
| `evidence_links` rows | insight_id ↔ document_id provenance graph |
| `contradiction_log` rows | Conflicting themes with source pointers |
| Q&A repository entries | Versioned RQ1–RQ7 answers |
| Quarantine queue items | Failed artifacts with validation reasons |
| Monthly Discovery Intelligence Report | Full structured report artifact |
| Validation metrics | Pass rate, quarantine rate per run |

### Testing

| Test Type | Scope | Pass Criteria |
|-----------|-------|---------------|
| **Unit** | `ProvenanceLinker` | Rejects insight when >20% citations invalid |
| **Unit** | `GroundingValidator` | Catches fabricated quote not in bundle |
| **Unit** | `ConfidenceCalibrator` | High → Medium when single source type |
| **Unit** | `BusinessRulesValidator` | Rejects opportunity without action_owner |
| **Unit** | `ThemeAggregator` | Same theme within 7 days merges, not duplicates |
| **Integration** | `ValidationPipeline` | Valid fixture passes; invalid fixture quarantined |
| **Integration** | `ThemeDiscoverWorkflow` | End-to-end: bundle → Gemini mock → published insight |
| **Integration** | `MonthlyReportWorkflow` | 3-pass mock produces complete report artifact |
| **Quality** | Human audit sample | 20 insights reviewed; ≥90% grounding accuracy |
| **Metrics** | Quarantine rate | <10% on golden test corpus |

**Test commands:**

```bash
cd backend && pytest tests/insights/ tests/validation/ -v
cd backend && python -m discovery_engine.cli.generate_insights --workflow theme_discover
cd backend && python -m discovery_engine.cli.generate_insights --workflow monthly_report
```

---

## Phase 6 — Dashboard

Deliver stakeholder-facing web application and Dashboard API for browsing insights, drilling into evidence, triggering ad-hoc analysis, and exporting reports.

### Objectives

1. Build Next.js dashboard with views defined in `architecture.md` §11.2
2. Implement FastAPI query, export, and analysis-trigger endpoints
3. Enable evidence drill-down from insight → source documents
4. Implement RBAC (Viewer, Analyst, Admin, Executive)
5. Support CSV/PDF/JSON export of opportunities and reports
6. Build Analyst Quarantine Queue UI for Phase 5 failures
7. Wire ad-hoc analysis: UI → retrieve → synthesize → validate → display

### Files

| Path | Purpose |
|------|---------|
| **Frontend** | |
| `frontend/package.json` | Next.js 14, TypeScript, Tailwind, shadcn/ui |
| `frontend/tsconfig.json` | TypeScript config |
| `frontend/src/app/layout.tsx` | Root layout + nav |
| `frontend/src/app/page.tsx` | Executive Overview |
| `frontend/src/app/rq/page.tsx` | RQ Explorer (RQ1–RQ7) |
| `frontend/src/app/rq/[id]/page.tsx` | Single RQ detail + version history |
| `frontend/src/app/themes/page.tsx` | Theme Trends |
| `frontend/src/app/segments/page.tsx` | Segment Profiles |
| `frontend/src/app/segments/[id]/page.tsx` | Segment detail |
| `frontend/src/app/opportunities/page.tsx` | Opportunity Backlog |
| `frontend/src/app/barriers/page.tsx` | Barrier & Pathway Maps |
| `frontend/src/app/sources/page.tsx` | Source Browser |
| `frontend/src/app/reports/page.tsx` | Report Archive |
| `frontend/src/app/reports/[id]/page.tsx` | Report viewer |
| `frontend/src/app/quarantine/page.tsx` | Analyst Review Queue |
| `frontend/src/app/analysis/new/page.tsx` | Ad-hoc analysis trigger |
| `frontend/src/components/insight/InsightCard.tsx` | Insight card display |
| `frontend/src/components/insight/EvidencePanel.tsx` | Drill-down source quotes |
| `frontend/src/components/insight/ConfidenceBadge.tsx` | High/Medium/Low badge |
| `frontend/src/components/charts/ThemeTrendChart.tsx` | Theme frequency sparkline |
| `frontend/src/components/charts/SourceDistributionChart.tsx` | Source mix chart |
| `frontend/src/components/opportunity/OpportunityTable.tsx` | Sortable/filterable table |
| `frontend/src/components/layout/Sidebar.tsx` | Navigation sidebar |
| `frontend/src/lib/api/client.ts` | Typed API client |
| `frontend/src/lib/api/types.ts` | Shared TS types from schemas |
| `frontend/src/lib/auth/session.ts` | Auth session helpers |
| `frontend/src/hooks/useInsights.ts` | Data fetching hooks |
| `frontend/src/hooks/useAnalysisRun.ts` | Poll analysis run status |
| **Backend API** | |
| `backend/src/discovery_engine/api/routes/dashboard/insights.py` | List/filter insights |
| `backend/src/discovery_engine/api/routes/dashboard/documents.py` | Source browser |
| `backend/src/discovery_engine/api/routes/dashboard/reports.py` | Report archive |
| `backend/src/discovery_engine/api/routes/dashboard/opportunities.py` | Opportunity backlog |
| `backend/src/discovery_engine/api/routes/dashboard/analysis.py` | Trigger ad-hoc run |
| `backend/src/discovery_engine/api/routes/dashboard/exports.py` | CSV/PDF/JSON export |
| `backend/src/discovery_engine/api/routes/dashboard/quarantine.py` | Quarantine management |
| `backend/src/discovery_engine/api/services/query_service.py` | Complex insight queries |
| `backend/src/discovery_engine/api/services/export_service.py` | PDF/CSV generation |
| `backend/src/discovery_engine/api/services/analysis_trigger_service.py` | Async analysis enqueue |
| `backend/src/discovery_engine/api/middleware/auth.py` | OAuth/JWT validation |
| `backend/src/discovery_engine/api/middleware/rbac.py` | Role-based access |
| `backend/src/discovery_engine/api/deps.py` | FastAPI dependencies |
| **Tests** | |
| `frontend/src/components/insight/__tests__/InsightCard.test.tsx` | Component tests |
| `frontend/e2e/dashboard.spec.ts` | Playwright E2E |
| `backend/tests/api/test_dashboard_insights.py` | API integration |
| `backend/tests/api/test_exports.py` | Export format validation |
| `backend/tests/api/test_rbac.py` | Role permission tests |
| `backend/tests/api/test_analysis_trigger.py` | Ad-hoc run flow |

### Classes

| Class | Module | Responsibility |
|-------|--------|----------------|
| `QueryService` | backend | Paginated insight queries with filters |
| `ExportService` | backend | Generates CSV, PDF, JSON exports |
| `AnalysisTriggerService` | backend | Enqueues retrieve → synthesize → validate pipeline |
| `AuthMiddleware` | backend | Validates OAuth/JWT tokens |
| `RBACMiddleware` | backend | Enforces role permissions per route |
| `InsightCard` | frontend | Renders insight with confidence + RQ badge |
| `EvidencePanel` | frontend | Shows linked source documents |
| `OpportunityTable` | frontend | Filterable backlog table |
| `ThemeTrendChart` | frontend | Theme frequency visualization |
| `ApiClient` | frontend | Typed HTTP client for backend API |

### Outputs

| Output | Description |
|--------|-------------|
| Executive Overview page | Top themes, trends, contradiction alerts |
| RQ Explorer | Searchable RQ1–RQ7 answers with evidence counts |
| Segment Profiles | Exploration likelihood, barriers, verbatim examples |
| Opportunity Backlog | Ranked, filterable, CSV-exportable |
| Source Browser | Full-text search over CRDs (no PII) |
| Report Archive | Monthly reports with PDF download |
| Analyst Quarantine Queue | Review/approve/reject failed insights |
| Ad-hoc analysis UI | Trigger and poll analysis runs |
| OpenAPI spec | Auto-generated at `/docs` |

### Testing

| Test Type | Scope | Pass Criteria |
|-----------|-------|---------------|
| **Component** | `InsightCard`, `EvidencePanel` | Renders all required fields; drill-down loads sources |
| **API** | Dashboard insight routes | 200 + pagination; filters by RQ, confidence |
| **API** | `ExportService` | CSV/PDF valid format; correct row count |
| **API** | `RBACMiddleware` | Viewer cannot access quarantine; Analyst can |
| **Integration** | Ad-hoc analysis trigger | UI → API → workflow → result displayed |
| **E2E** | Playwright golden path | Login → RQ Explorer → evidence drill-down → export CSV |
| **Accessibility** | axe-core scan | No critical a11y violations on main pages |
| **Performance** | Dashboard load | LCP <2.5s on staging with 1K insights |
| **Security** | PII scan | Source browser never renders redacted PII patterns |

**Test commands:**

```bash
cd backend && pytest tests/api/ -v
cd frontend && npm test
cd frontend && npx playwright test
```

---

## Phase 7 — Deployment

Provision GCP infrastructure, containerize services, establish CI/CD, observability, and production hardening per `architecture.md` §12.

### Objectives

1. Define Terraform modules for VPC, Cloud SQL, Cloud Run, GCS, Secret Manager, Redis
2. Containerize backend services and frontend
3. Configure Cloud Composer DAGs for scheduled ingestion and monthly reports
4. Set up GitHub Actions CI/CD with staging → production promotion
5. Implement Cloud Monitoring dashboards, alerts, and structured logging
6. Configure Secret Manager, IAM least-privilege, private Cloud SQL
7. Document runbooks, DR procedures, and smoke tests
8. Execute production cutover checklist

### Files

| Path | Purpose |
|------|---------|
| **Infrastructure** | |
| `infra/terraform/main.tf` | Root module |
| `infra/terraform/variables.tf` | Environment variables |
| `infra/terraform/outputs.tf` | Endpoints, connection strings |
| `infra/terraform/modules/vpc/main.tf` | VPC, subnets, private services access |
| `infra/terraform/modules/cloud_sql/main.tf` | PostgreSQL 15 + pgvector HA |
| `infra/terraform/modules/cloud_run/main.tf` | Cloud Run services |
| `infra/terraform/modules/gcs/main.tf` | Raw exports + report buckets |
| `infra/terraform/modules/redis/main.tf` | Memorystore Redis |
| `infra/terraform/modules/secret_manager/main.tf` | Secrets provisioning |
| `infra/terraform/modules/iam/main.tf` | Service accounts + bindings |
| `infra/terraform/environments/dev.tfvars` | Dev environment values |
| `infra/terraform/environments/staging.tfvars` | Staging values |
| `infra/terraform/environments/prod.tfvars` | Production values |
| **Docker** | |
| `docker/Dockerfile.backend` | Backend multi-stage build |
| `docker/Dockerfile.frontend` | Next.js production build |
| `docker/docker-compose.prod.yml` | Local prod-like stack |
| **CI/CD** | |
| `.github/workflows/ci.yml` | Lint, test, build on PR |
| `.github/workflows/deploy-staging.yml` | Deploy to staging on merge to main |
| `.github/workflows/deploy-prod.yml` | Manual approval → production |
| **Orchestration** | |
| `dags/ingestion_dag.py` | Daily Play/App Store/Reddit collection + clean |
| `dags/embedding_dag.py` | Post-ingestion embedding job |
| `dags/monthly_report_dag.py` | Monthly WF-MONTHLY-REPORT |
| `dags/form_ingest_dag.py` | Google Form CSV poll |
| **Observability** | |
| `infra/monitoring/dashboards/pipeline.json` | Cloud Monitoring dashboard |
| `infra/monitoring/alerts/ingestion_failure.yaml` | Alert policies |
| `infra/monitoring/alerts/gemini_rate_limit.yaml` | Gemini 429 alert |
| `backend/src/discovery_engine/observability/logging.py` | Structured JSON logging |
| `backend/src/discovery_engine/observability/metrics.py` | Custom metrics emitter |
| `backend/src/discovery_engine/observability/tracing.py` | Cloud Trace integration |
| **Runbooks** | |
| `docs/runbooks/ingestion_failure.md` | Ingestion ops runbook |
| `docs/runbooks/gemini_outage.md` | LLM fallback runbook |
| `docs/runbooks/database_recovery.md` | DR procedure |
| `docs/runbooks/deployment_checklist.md` | Pre/post deploy checklist |
| **Scripts** | |
| `scripts/smoke_test.sh` | Post-deploy health checks |
| `scripts/db_migrate.sh` | Alembic migrate in Cloud Run job |
| `scripts/seed_taxonomy.sh` | Production taxonomy seed |

### Classes / Components

| Component | Responsibility |
|-----------|----------------|
| `Terraform VPC module` | Private network for Cloud SQL + Cloud Run |
| `Terraform Cloud SQL module` | HA PostgreSQL with pgvector, backups, PITR |
| `Terraform Cloud Run module` | API, retrieval, synthesis services |
| `Terraform GCS module` | Raw + export buckets with lifecycle rules |
| `Terraform IAM module` | Per-service service accounts |
| `PipelineDashboard` | Cloud Monitoring: ingestion lag, retrieval p95, validation fail rate |
| `StructuredLogger` | JSON logs with run_id, trace_id, service name |
| `MetricsEmitter` | Custom counters: documents_ingested, insights_published, gemini_tokens |
| `TraceMiddleware` | FastAPI Cloud Trace propagation |
| `IngestionDAG` | Airflow: collect → clean → embed |
| `MonthlyReportDAG` | Airflow: retrieve → multi-pass → publish |
| `SmokeTestRunner` | HTTP checks: /health, /api/v1/insights, DB connectivity |

### Outputs

| Output | Description |
|--------|-------------|
| GCP staging environment | Fully wired dev/staging stack |
| GCP production environment | HA Cloud SQL, Cloud Run, Composer, GCS |
| Container images | Backend + frontend in Artifact Registry |
| CI/CD pipelines | Automated test + deploy workflows |
| Cloud Monitoring dashboards | Pipeline health visibility |
| Alert policies | Ingestion failure, Gemini 429, validation spike |
| Composer DAGs | Scheduled ingestion + monthly report |
| Runbooks | Ops documentation for on-call |
| Deployment checklist | Signed-off production cutover |
| Smoke test report | Post-deploy pass/fail |

### Testing

| Test Type | Scope | Pass Criteria |
|-----------|-------|---------------|
| **Terraform** | `terraform validate` + plan | No errors; plan matches expected resources |
| **Container** | Docker build | Images build <5 min; non-root user |
| **CI** | GitHub Actions on PR | Lint + unit tests pass |
| **Deploy staging** | Full pipeline | All Cloud Run services healthy |
| **Smoke** | `scripts/smoke_test.sh` | All endpoints 200; DB migration current |
| **Load** | k6 retrieval endpoint | p95 <500ms at 50 RPS on staging |
| **DR drill** | Cloud SQL PITR restore | Restore to test instance <4 hours |
| **Security** | IAM audit | No overly permissive roles; secrets not in env vars |
| **Observability** | Trigger test alert | Ingestion failure alert fires within 5 min |
| **E2E prod-like** | Staging full cycle | Collect → clean → embed → synthesize → dashboard |

**Test commands:**

```bash
cd infra/terraform && terraform validate && terraform plan -var-file=environments/staging.tfvars
docker build -f docker/Dockerfile.backend -t discovery-backend .
docker build -f docker/Dockerfile.frontend -t discovery-frontend .
./scripts/smoke_test.sh https://staging-discovery.blinkit.internal
```

---

## Cross-Phase Milestones

| Milestone | Phase | Date (suggested) | Gate Criteria |
|-----------|-------|------------------|---------------|
| M1 — Raw data flowing | Phase 1 | Week 2 | 4 sources collect to raw store |
| M2 — Clean corpus ready | Phase 2 | Week 4 | ≥1,000 CRDs in PostgreSQL |
| M3 — Retrieval live | Phase 3 | Week 6 | Evidence bundles via API |
| M4 — First AI insight | Phase 4 + 5 | Week 8 | 1 validated insight card published |
| M5 — Dashboard alpha | Phase 6 | Week 10 | Stakeholders browse insights |
| M6 — Production launch | Phase 7 | Week 12 | Staging smoke pass; prod cutover |

---

## Shared Dependencies Across Phases

| Dependency | Introduced | Used By |
|------------|------------|---------|
| PostgreSQL 15 + pgvector | Phase 2 | Phases 3–7 |
| Redis | Phase 3 | Phases 3–7 |
| Google embedding API | Phase 3 | Phases 3–7 |
| Gemini API (Vertex AI) | Phase 4 | Phases 4–7 |
| `context.md` / `problemStatement.md` | Phase 4 | Phases 4–6 |
| JSON Schemas in `schemas/` | Phase 2, 4 | Phases 4–6 |
| FastAPI app shell | Phase 3 | Phases 3–7 |

---

## Risk Register (Implementation)

| Risk | Phase | Mitigation |
|------|-------|------------|
| Reddit/Play Store rate limits | 1 | Retry policy; cache; stagger schedules |
| Embedding cost at scale | 3 | Batch embed; skip unchanged content hashes |
| Gemini JSON malformation | 4 | ResponseParser + one repair retry |
| Citation fabrication | 5 | GroundingValidator; quarantine queue |
| Dashboard scope creep | 6 | MVP views first; defer barrier map viz to v1.1 |
| Terraform state drift | 7 | Remote state in GCS; plan-only on PR |

---

## Document Relationships

| Document | Role |
|----------|------|
| `problemStatement.md` | Business problem and scope |
| `context.md` | AI operating rules and output specs |
| `architecture.md` | Solution design |
| `implementation-plan.md` (this file) | Phased build plan with files, classes, tests |

---

*Execute phases sequentially unless noted. Do not start Phase 4 without Phase 3 retrieval API returning valid Evidence Bundles. Do not deploy Phase 7 production until Phase 6 staging E2E passes.*
