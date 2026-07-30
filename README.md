# Blinkit AI Product Discovery Engine

This project defines and implements an **AI-powered Product Discovery Engine** for the Blinkit quick commerce growth case study. The engine analyzes qualitative user feedback from multiple channels to explain why category exploration stalls for Monthly Active Customers (MAC) and surfaces product improvement opportunities.

---

## Folder Layout

```
blinkit-ai-discovery-engine/
├── backend/
│   ├── data/
│   │   ├── raw/                      # Raw JSON connector feeds (Phases 1-2)
│   │   ├── dlq/                      # Dead Letter Queue files
│   │   ├── google_form_responses.csv # Mock survey response CSV source
│   │   └── clean_reviews.csv         # Cleaned, normalized, and deduplicated CSV database
│   ├── src/
│   │   └── discovery_engine/
│   │       ├── config/               # Settings loading (constants & settings)
│   │       ├── models/               # Pydantic schemas (RawRecord, CanonicalReview, IngestionRun)
│   │       ├── utils/                # Logging setup
│   │       ├── validation/           # Rating verification and PII Redactor
│   │       ├── loaders/              # Connectors (Play Store, App Store, Reddit, CSV)
│   │       ├── cleaning/             # Cleaner and CSV exporter modules
│   │       ├── retrieval/            # Cosine similarity/TF-IDF text retriever
│   │       └── llm/                  # Prompt builder and Gemini REST API Client
│   └── tests/                        # Unit test suite for validation, cleaning, and search
├── analysis/
│   └── results/
│       └── report.json               # Synthesized JSON output report (Phase 5 analysis)
├── app.py                            # Streamlit frontend application entry point
├── main.py                           # Central backend application runner
├── query_and_analyze.py                   # Script to test backend pipeline integration
├── requirements_frontend.txt         # Frontend package requirements
├── .env                              # Environment variable configurations
└── README.md                         # Project documentation
```

---

## 1. How to Install Dependencies

Make sure you have Python 3.11+ installed. To install all dependencies for both the backend and frontend, run the following:

```bash
# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
pip install -r requirements_frontend.txt
```

---

## 2. How to Run the Backend Ingestion Pipeline

To run the raw review collection, validation, cleaning, retrieval, and LLM synthesis, execute the central runner:

```bash
python main.py
```

### Backend Configurations
Create or update the `.env` file in the workspace root or `backend/` directory to configure API keys:
```env
# Application Config
LOG_LEVEL=INFO

# Storage Config
RAW_STORE_DIR=./backend/data/raw
DEAD_LETTER_QUEUE_DIR=./backend/data/dlq
CLEANED_DATA_PATH=backend/data/clean_reviews.csv

# Google Gemini Config
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-1.5-flash
```

*Note: If no `GEMINI_API_KEY` is provided, the engine will gracefully fall back to generating high-quality mock analysis matching the Phase 5 schema.*

---

## 3. How to Run the Frontend Dashboard

To launch the interactive PM growth dashboard, run the following command in the project root folder:

```bash
streamlit run app.py
```

Streamlit will boot up local server and automatically open the application in your browser (usually at `http://localhost:8501`).

### Dashboard Features
- **Overview Dashboard**: Track metrics (Total reviews, Play Store counts, Reddit mentions, Google Forms responses) and view charts showing distribution by channel and overall sentiment.
- **Sentiment & Topic Analysis**: Star rating distribution chart, active theme indicators, and common keywords from the cleaned review corpus.
- **Customer Pain Points**: Explores specific pain point clusters and themes, lists the issues, prints supporting quotes, and includes an interactive keyword query tool.
- **User Segmentation**: Displays behavioral segments (Routine Buyers, New Product Explorers, Health Conscious/Premium Seekers) with details on exploration barriers and likelihood.
- **Opportunity Generator**: Structured opportunities table (matching L1 categories and targets), Jobs-to-be-Done (JTBD) hypotheses, and root-cause symptom-cause trees.
