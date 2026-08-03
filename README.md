# Blinkit AI Growth: 5-Layer Automated AI Data Pipeline

A production-ready, automated AI Data Pipeline that aggregates customer reviews from multiple channels (app stores, social platforms, blogs), cleans and normalizes the data streams, extracts structured user segment pain points via LLM synthesis, generates dense vector embeddings, and indexes them into a Pinecone Vector Database.

---

## 🚀 Pipeline Architecture

The system is structured as a **5-layer automated pipeline** designed to run on a cron schedule or via manual triggers:

```text
  [ Social & App Scrapers ] (Play Store, App Store, Reddit, Twitter, Medium RSS)
               │
               ▼
     [ Ingestion Layer ]   (Clean, sanitize, normalize schema & deduplicate via MD5) -> raw_reviews_dump.json
               │
               ▼
    [ AI Insight Synthesis ] (Structured JSON: sentiment, unmet need, segment via Groq Llama 3.1) -> synthesized_needs.json
               │
               ▼
   [ Vector Embedding Gen ] (Generate 384D dense vectors via sentence-transformers all-MiniLM-L6-v2)
               │
               ▼
    [ Vector Storage Index ] (Create index and batch-upsert vectors + metadata to Pinecone DB)
```

### Component Breakdown
1. **WORKFLOW ORCHESTRATOR**: A Github Actions weekly cron schedule that configures virtual environments, pulls dependencies, injects secrets, and coordinates execution.
2. **SCRAPING LAYER**: Modular scraper scripts for Play Store, App Store, Reddit public API feeds, Twitter v2 searches, and Medium tag feeds. Supports complete mock fallback logic for credentials-free sandboxes.
3. **INGESTION LAYER**: Text preprocessing module (normalizes character encodings, strips HTML markup, normalizes spaces) and handles MD5 content hashing deduplication.
4. **AI PROCESSING LAYER**: Multi-threaded parallel inference caller targeting Groq API endpoints using `llama-3.1-8b-instant` to parse JSON metadata attributes, paired with a local `sentence-transformers` model to map semantic embeddings.
5. **STORAGE LAYER**: Database router that creates serverless Pinecone indexes and pushes vector sets alongside text payloads.

---

## 📂 Folder Layout

```text
blinkit-ai-discovery-engine/
├── .github/workflows/
│   └── pipeline.yml         # GitHub Actions Weekly Cron Orchestrator
├── data/
│   ├── raw_reviews_dump.json    # Layer 3 cleaned and deduplicated reviews
│   └── synthesized_needs.json   # Layer 4 AI insights enriched reviews
├── src/
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── play_store.py    # Play Store reviews scraper
│   │   ├── app_store.py     # App Store reviews scraper
│   │   ├── reddit.py        # Reddit credentials-free JSON and PRAW searcher
│   │   ├── twitter.py       # Twitter/X API search client
│   │   └── medium.py        # Medium RSS tag XML feed parser
│   ├── ingest.py            # Aggregate streams, clean, and deduplicate
│   ├── process_insights.py  # Structured JSON insight extraction using Groq
│   ├── generate_embeddings.py # 384D semantic vector embedding mapper
│   └── upsert_pinecone.py   # Pinecone index management and batch indexing
├── main.py                  # End-to-end pipeline coordinator
├── requirements.txt         # Package dependencies
└── README.md                # System documentation
```

---

## ⚙️ Environment Variables Config

Create or update the `.env` file in the project root directory:

```env
# Application Config
LOG_LEVEL=INFO

# Groq Config
GROQ_API_KEY=YOUR_GROQ_API_KEY
GROQ_MODEL=llama-3.1-8b-instant

# Pinecone Config
PINECONE_API_KEY=YOUR_PINECONE_API_KEY
PINECONE_INDEX_NAME=blinkit-ai-discovery

# Optional Social Credentials (Scrapers fall back to public feeds/mocks if omitted)
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
TWITTER_BEARER_TOKEN=
```

---

## 🛠️ Local Execution & Verification

Follow these steps to run the pipeline on your local machine:

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Execute Ingestion & AI Pipeline**:
   ```bash
   python main.py
   ```
   *Note: If no API keys are provided in the `.env` file, the pipeline will automatically utilize mock heuristics engines to run completely end-to-end and index simulated vectors into Pinecone (dry-run mode).*

3. **Output Files to Inspect**:
   - `data/raw_reviews_dump.json`: Verify that reviews have been cleaned, formatted, and deduplicated.
   - `data/synthesized_needs.json`: Verify that sentiment, segments, frustration levels, and unmet needs have been populated as JSON fields.

---

## ⏰ GitHub Actions Automations

The workflow `.github/workflows/pipeline.yml` is scheduled to run:
* **Cron Time**: Every Monday at 7:00 AM IST (`30 1 * * 1` UTC).
* **Manual execution**: Can be triggered anytime via **Workflow Dispatch** under the Github Actions tab.

To activate, add the repository secrets on GitHub:
* `GROQ_API_KEY`
* `PINECONE_API_KEY`
* `PINECONE_INDEX_NAME`
