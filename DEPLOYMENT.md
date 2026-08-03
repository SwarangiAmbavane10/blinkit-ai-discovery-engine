# Deployment Guide - Blinkit AI Product Discovery Engine

This document provides step-by-step instructions to deploy the Blinkit AI Product Discovery Engine dashboard to production.

---

## 1. Project Framework & Hosting Platform Analysis

### Detected Framework
- **Framework**: [Streamlit](https://streamlit.io/) (Python web app framework).
- **Frontend Entrypoint**: `app.py`
- **Backend Processing**: `main.py` (ingestion, cleaning, Cosine/TF-IDF retrieval, and Gemini/Groq LLM analysis).

### Hosting Platform Suitability: Vercel vs. Recommended Alternatives

> [!WARNING]
> **Vercel is NOT the appropriate platform for hosting standard Streamlit applications.**
>
> **Why Vercel is incompatible:**
> 1. **Stateless / Serverless Architecture**: Vercel is optimized for static frontends and stateless, short-lived serverless functions. Streamlit, by contrast, requires a persistent Python web server running in the background.
> 2. **WebSocket Support**: Streamlit relies on long-lived WebSocket connections to send UI event messages between the client browser and Python runtime. Vercel serverless functions do not support WebSockets.
> 3. **Execution Time Limits**: Vercel serverless functions have hard execution limits (e.g., 10 to 60 seconds), whereas Streamlit dashboard sessions need to stay open for as long as the user is browsing.
>
> If you deploy this repository directly to Vercel, the build will either fail during runtime resolution or crash instantly because of WebSocket connection failures.

### Recommended Hosting Platforms
Instead of Vercel, we strongly recommend deploying this project on one of the following platforms:
1. **Streamlit Community Cloud** (Recommended & Free): The native hosting solution from Streamlit. It deploys directly from your GitHub repo, automatically manages requirements, and handles live WebSocket state seamlessly.
2. **Render or Railway** (Container/PaaS): Excellent options to host persistent Python background instances. You can run the app directly using the Streamlit CLI or a simple Docker container.

---

## 2. Environment Variables & Secrets Configuration

All configuration is loaded via environment variables (mapped through [settings.py](file:///c:/Users/91911/OneDrive/Desktop/blinkit%20ai%20discovery%20engine/backend/src/discovery_engine/config/settings.py)). When deploying, make sure to add these variables to your hosting provider's dashboard:

### Core Secrets
- `LLM_PROVIDER`: Set to either `gemini` (default) or `groq` to select the LLM client.
- `GEMINI_API_KEY`: Required if `LLM_PROVIDER=gemini`. Your Google AI Studio Gemini API Key.
- `GROQ_API_KEY`: Required if `LLM_PROVIDER=groq`. Your Groq Cloud Console API Key.

### Optional Configurations
- `LOG_LEVEL`: Logging verbosity (e.g., `INFO`, `DEBUG`). Defaults to `INFO`.
- `GEMINI_MODEL`: Gemini model version to use. Defaults to `gemini-1.5-flash`.
- `GROQ_MODEL`: Groq model version to use. Defaults to `llama-3.3-70b-versatile`.
- `PLAY_STORE_APP_ID`: Defaults to `com.grofers.customerapp`.
- `APP_STORE_APP_ID`: Defaults to `1393452285`.
- `CLEANED_DATA_PATH`: Path to the clean CSV database. Defaults to `backend/data/clean_reviews.csv`.

> [!NOTE]
> **Production Read-Only Behavior:**
> The dashboard is pre-populated with a pre-computed clean reviews corpus ([clean_reviews.csv](file:///c:/Users/91911/OneDrive/Desktop/blinkit%20ai%20discovery%20engine/backend/data/clean_reviews.csv)) and a pre-synthesized AI insights report ([report.json](file:///c:/Users/91911/OneDrive/Desktop/blinkit%20ai%20discovery%20engine/analysis/results/report.json)) tracked in Git. 
> 
> Therefore, in production environments with ephemeral storage (like Streamlit Cloud or Render Free), the dashboard will render fully and run **read-only** immediately. Running the live ingestion pipeline via the button on the dashboard is disabled/not recommended in production because any new files written will be lost when the container recycles.

---

## 3. Step-by-Step Deployment Instructions

### Option A: Streamlit Community Cloud (Recommended)

Streamlit Community Cloud is free and provides native support.

1. **Push your code to GitHub**: Ensure all changes are committed and pushed to a repository on your GitHub account.
2. **Sign in to Streamlit**: Go to [share.streamlit.io](https://share.streamlit.io/) and log in using your GitHub account.
3. **Deploy a new app**:
   - Click the **"New app"** button.
   - Select your Repository, Branch (usually `main`), and specify the Main file path as `app.py`.
4. **Configure Secrets**:
   - Click the **"Advanced settings..."** button before deploying or go to Settings in your app console.
   - In the **Secrets** text area, paste your environment variables in TOML format:
     ```toml
     LLM_PROVIDER = "gemini"
     GEMINI_API_KEY = "your-api-key-here"
     ```
5. **Deploy**: Click **"Deploy!"**. Streamlit will provision the server, install Python dependencies from `requirements.txt`, and launch your app.

---

### Option B: Render Deployment (Alternative)

Render allows you to run a persistent web service.

1. **Sign in to Render**: Log in at [dashboard.render.com](https://dashboard.render.com/).
2. **Create a Web Service**:
   - Click **New +** and select **Web Service**.
   - Connect your GitHub repository.
3. **Configure Service Settings**:
   - **Name**: `blinkit-ai-discovery-engine`
   - **Language**: `Python` or `Docker` (Python is simpler).
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
4. **Configure Environment Variables**:
   - Scroll down to the **Environment** section.
   - Click **Add Environment Variable** and add:
     - `LLM_PROVIDER` (e.g., `gemini`)
     - `GEMINI_API_KEY` (your API key)
5. **Deploy**: Click **Create Web Service**. Render will build and expose the app with a public URL.

---

### Option C: Vercel Deployment (Fallback Attempt)

If deployment to Vercel is strictly required, you can attempt to host it using Vercel's Python serverless builder, although dynamic UI interactions will fail.

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```
2. **Create/Verify `vercel.json`**:
   Ensure the following `vercel.json` file exists in the root of the repository:
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "app.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "app.py"
       }
     ]
   }
   ```
3. **Login and Deploy**:
   Open a terminal in the project root and run:
   ```bash
   vercel login
   vercel
   ```
   Follow the prompts to link the project.
4. **Set Environment Variables on Vercel**:
   Go to your Vercel Dashboard, select your project -> **Settings** -> **Environment Variables**, and add `GEMINI_API_KEY` and/or `GROQ_API_KEY`.
5. **Promote to Production**:
   ```bash
   vercel --prod
   ```

*Note: Since Vercel executes `app.py` as a serverless function, it will fail to support the persistent WebSocket server needed for Streamlit. We strongly encourage deploying via **Option A** or **Option B**.*
