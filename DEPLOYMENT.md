# Deployment Guide - Blinkit AI Product Discovery Engine Serverless API

This document provides step-by-step instructions to test and deploy the Blinkit AI Product Discovery Engine backend as a **Serverless FastAPI API** on Vercel.

---

## 1. Project Framework & Vercel Suitability

### Detected Framework & Architecture
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python ASGI web framework).
- **Entrypoint**: [api/index.py](file:///c:/Users/91911/OneDrive/Desktop/blinkit%20ai%20discovery%20engine/api/index.py).
- **Platform Capability**: Fully compatible with Vercel's Python serverless runtime builder (`@vercel/python`).

### Supported API Endpoints
When deployed, the service exposes the following serverless endpoints:
* `GET /`: Health status message and link to documentation.
* `GET /api/status`: Service details, environment stats, configurations, and data corpus/report file existence flags.
* `GET /api/report`: Reads and returns the precompiled AI Product Insights JSON report ([report.json](file:///c:/Users/91911/OneDrive/Desktop/blinkit%20ai%20discovery%20engine/analysis/results/report.json)).
* `GET /api/reviews`: Returns reviews loaded from the CSV database ([clean_reviews.csv](file:///c:/Users/91911/OneDrive/Desktop/blinkit%20ai%20discovery%20engine/backend/data/clean_reviews.csv)), with optional parameters for pagination (`limit`, `offset`) and filtering (`source_type`, `sentiment`).
* `GET /api/query`: Performs semantic/TF-IDF similarity searches on the corpus using the backend's `RetrievalEngine` (`q` query string and `top_k` count).
* `POST /api/run`: Triggers the dynamic reviews scraping, cleaning, and LLM analysis pipeline (invokes `main.main()`).

---

## 2. Environment Variables & Secrets Configuration

Paste the following variables in your Vercel Dashboard under **Settings -> Environment Variables** or define them in your local `.env` file:

### Core Secrets
- `LLM_PROVIDER`: Set to either `gemini` (default) or `groq`.
- `GEMINI_API_KEY`: Required if `LLM_PROVIDER=gemini`. Your Google AI Studio Gemini API Key.
- `GROQ_API_KEY`: Required if `LLM_PROVIDER=groq`. Your Groq Cloud Console API Key.

### Optional Configs
- `LOG_LEVEL`: Logging level (e.g. `INFO`, `DEBUG`). Defaults to `INFO`.
- `GEMINI_MODEL`: Gemini model version to use. Defaults to `gemini-1.5-flash`.
- `GROQ_MODEL`: Groq model version to use. Defaults to `llama-3.3-70b-versatile`.
- `PLAY_STORE_APP_ID`: Defaults to `com.grofers.customerapp`.
- `APP_STORE_APP_ID`: Defaults to `1393452285`.

---

## 3. Local Verification & Testing

Verify imports and execution flow locally before deploying to Vercel:

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Start the local ASGI web server**:
   ```bash
   uvicorn api.index:app --reload
   ```
3. **Inspect and Test**:
   - Access the interactive OpenAPI documentation: `http://127.0.0.1:8000/docs`
   - Test health check: `http://127.0.0.1:8000/api/status`
   - Test retrieval search: `http://127.0.0.1:8000/api/query?q=premium&top_k=3`
   - Test corpus reviews: `http://127.0.0.1:8000/api/reviews?limit=5`

---

## 4. Vercel Deployment Instructions

### Option A: Deployment via Vercel CLI (Recommended)

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```
2. **Authenticate**:
   ```bash
   vercel login
   ```
3. **Configure Routing**:
   Ensure `vercel.json` exists in the root directory:
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "api/index.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "api/index.py"
       }
     ]
   }
   ```
4. **Deploy**:
   ```bash
   vercel
   ```
   Follow the prompts to link to your Vercel account.
5. **Set Environment Variables on Vercel**:
   Go to your project settings in the Vercel Web Console and add your secrets (`GEMINI_API_KEY`, etc.).
6. **Promote to Production**:
   ```bash
   vercel --prod
   ```

### Option B: Deployment via Vercel GitHub Integration

1. Push your repository to GitHub.
2. In the Vercel dashboard, click **"Add New"** -> **"Project"**.
3. Import your GitHub repository.
4. Vercel will automatically discover the `vercel.json` and detect the Python configuration.
5. Expand the **Environment Variables** section and paste your keys.
6. Click **"Deploy"**. Vercel will run `pip install`, build your functions, and expose the API.
