import os
import sys
import json
import csv
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# Dynamically add the backend/src directory to sys.path to resolve discovery_engine imports cleanly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_SRC = os.path.join(BASE_DIR, "backend", "src")
if BACKEND_SRC not in sys.path:
    sys.path.insert(0, BACKEND_SRC)

try:
    from discovery_engine.config.settings import settings
    from discovery_engine.retrieval.engine import RetrievalEngine
except ImportError as ie:
    # Fallback to local import helper just in case path resolver behaves differently on Vercel
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "src")))
    from discovery_engine.config.settings import settings
    from discovery_engine.retrieval.engine import RetrievalEngine

app = FastAPI(
    title="Blinkit AI Product Discovery Engine API",
    description="Serverless API exposing the ingestion pipeline, data corpus, search, and AI-synthesized product insights",
    version="1.0.0"
)

# Enable CORS for easy cross-origin querying (e.g., from dashboards or external services)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Absolute Paths
CLEAN_CSV_PATH = os.path.join(BASE_DIR, "backend", "data", "clean_reviews.csv")
REPORT_JSON_PATH = os.path.join(BASE_DIR, "analysis", "results", "report.json")

# Fallback paths inside the workspace in case Vercel references the root directory
ALTERNATIVE_CLEAN_CSV_PATH = os.path.join(BASE_DIR, "blinkit_reviews_clean.csv")
ALTERNATIVE_DISCOVERY_CSV_PATH = os.path.join(BASE_DIR, "blinkit_discovery_reviews.csv")

def get_corpus_path() -> str:
    """Helper to check and return the active corpus file path."""
    if os.path.exists(CLEAN_CSV_PATH):
        return CLEAN_CSV_PATH
    elif os.path.exists(ALTERNATIVE_DISCOVERY_CSV_PATH):
        return ALTERNATIVE_DISCOVERY_CSV_PATH
    elif os.path.exists(ALTERNATIVE_CLEAN_CSV_PATH):
        return ALTERNATIVE_CLEAN_CSV_PATH
    return CLEAN_CSV_PATH

@app.get("/api/status", tags=["Status"])
def read_status():
    """Returns the API service health and current settings configuration (excluding secrets)."""
    return {
        "status": "online",
        "framework": "FastAPI",
        "provider": settings.LLM_PROVIDER,
        "models": {
            "gemini": settings.GEMINI_MODEL,
            "groq": settings.GROQ_MODEL
        },
        "limits": {
            "play_store": settings.PLAY_STORE_FETCH_LIMIT,
            "app_store": settings.APP_STORE_FETCH_LIMIT,
            "reddit": settings.REDDIT_FETCH_LIMIT
        },
        "corpus_loaded": os.path.exists(get_corpus_path()),
        "report_compiled": os.path.exists(REPORT_JSON_PATH)
    }

@app.get("/api/report", tags=["Analysis Report"])
def read_report():
    """Reads and returns the precompiled AI Product Insights report."""
    if not os.path.exists(REPORT_JSON_PATH):
        raise HTTPException(
            status_code=404, 
            detail="AI analysis report is not yet generated. Please trigger pipeline run first."
        )
    try:
        with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse report file: {str(e)}")

@app.get("/api/reviews", tags=["Data Corpus"])
def read_reviews(
    source_type: Optional[str] = Query(None, description="Filter by source (play_store, app_store, reddit, google_form)"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment (POSITIVE, NEGATIVE, NEUTRAL)"),
    limit: int = Query(50, ge=1, le=200, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """Returns a list of cleaned, deduplicated canonical reviews from the corpus database."""
    csv_path = get_corpus_path()
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Reviews corpus file not found. Ingest data first.")

    reviews = []
    try:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Map source to lowercase snake_case
                src = str(row.get("source_type", "")).lower() or str(row.get("source", "")).lower()
                src = src.replace(" ", "_").replace("google_forms", "google_form")

                row_sentiment = str(row.get("sentiment", "")).upper()
                if not row_sentiment and row.get("rating"):
                    try:
                        val = float(row.get("rating"))
                        row_sentiment = "POSITIVE" if val >= 4 else ("NEGATIVE" if val <= 2 else "NEUTRAL")
                    except Exception:
                        row_sentiment = "NEUTRAL"

                # Apply Filters
                if source_type and src != source_type.lower():
                    continue
                if sentiment and row_sentiment != sentiment.upper():
                    continue

                reviews.append({
                    "review_id": row.get("review_id", ""),
                    "source_type": src,
                    "original_text": row.get("original_text") or row.get("review_text", ""),
                    "cleaned_text": row.get("cleaned_text", ""),
                    "rating": row.get("rating", ""),
                    "timestamp": row.get("timestamp") or row.get("date", ""),
                    "sentiment": row_sentiment,
                    "review_url": row.get("review_url", "")
                })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading corpus CSV: {str(e)}")

    total_count = len(reviews)
    paginated_reviews = reviews[offset:offset + limit]

    return {
        "total": total_count,
        "offset": offset,
        "limit": limit,
        "count": len(paginated_reviews),
        "results": paginated_reviews
    }

@app.get("/api/query", tags=["Search / Retrieval"])
def query_retrieval(
    q: str = Query(..., description="Query terms to search reviews for relevance (e.g. 'freshness', 'premium')"),
    top_k: int = Query(10, ge=1, le=50, description="Max matching items to retrieve")
):
    """Queries the TF-IDF Cosine similarity engine and returns the top-k most relevant reviews."""
    csv_path = get_corpus_path()
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Reviews corpus file not found. Cannot perform search.")

    try:
        retriever = RetrievalEngine()
        retriever.load_corpus(csv_path)
        top_reviews = retriever.retrieve(query=q, top_k=top_k)
        return {
            "query": q,
            "count": len(top_reviews),
            "results": top_reviews
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving matching documents: {str(e)}")

@app.post("/api/run", tags=["Pipeline Execution"])
def run_pipeline():
    """
    Triggers the data ingestion, validation, and AI synthesis analysis pipeline dynamically.
    WARNING: Running this in serverless containers may encounter execution time constraints or temporary file writes.
    """
    try:
        # Dynamically load and reload main to trigger run cleanly
        import importlib
        if "main" in sys.modules:
            importlib.reload(sys.modules["main"])
        else:
            import main
        
        main.main()
        return {
            "success": True,
            "message": "Ingestion and synthesis analysis pipeline executed successfully.",
            "report_path": os.path.relpath(REPORT_JSON_PATH)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")

# Fallback root path router
@app.get("/", include_in_schema=False)
def read_root():
    return {
        "message": "Blinkit AI Product Discovery Engine API is online.",
        "docs_url": "/docs",
        "status_url": "/api/status"
    }
