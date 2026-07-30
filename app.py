import os
import sys
import json
import csv
import pandas as pd
import altair as alt
import streamlit as st

# Set up page configurations
st.set_page_config(
    page_title="Blinkit AI Discovery Engine Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dynamically add the backend/src directory to sys.path to resolve imports cleanly
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_SRC = os.path.join(BASE_DIR, "backend", "src")
if BACKEND_SRC not in sys.path:
    sys.path.insert(0, BACKEND_SRC)

# File Paths
CLEAN_CSV_PATH = os.path.join(BASE_DIR, "backend", "data", "clean_reviews.csv")
REPORT_JSON_PATH = os.path.join(BASE_DIR, "analysis", "results", "report.json")

# ---------------------------------------------------------
# Helper Functions to Load and Process Data
# ---------------------------------------------------------
@st.cache_data
def load_clean_reviews(file_path):
    """Loads cleaned reviews data from CSV, mapping columns to support blinkit_reviews_clean.csv or blinkit_discovery_reviews.csv."""
    discovery_path = os.path.join(BASE_DIR, "blinkit_discovery_reviews.csv")
    root_clean_path = os.path.join(BASE_DIR, "blinkit_reviews_clean.csv")
    if os.path.exists(discovery_path):
        file_path = discovery_path
    elif os.path.exists(root_clean_path):
        file_path = root_clean_path

    if not os.path.exists(file_path):
        return None
        
    df = pd.read_csv(file_path)
    
    # Map blinkit_reviews_clean.csv format to expected app.py schema
    if "source" in df.columns and "review_text" in df.columns:
        # Standardize source strings to snake_case codes
        df["source_type"] = df["source"].str.lower().str.replace(" ", "_")
        df["source_type"] = df["source_type"].replace("google_forms", "google_form")
        
        # Rename date & review_text
        df["timestamp"] = df["date"]
        df["original_text"] = df["review_text"]
        
        # Generate unique review IDs using text hash
        if "review_id" not in df.columns:
            import hashlib
            df["review_id"] = df["original_text"].apply(
                lambda x: hashlib.md5(str(x).encode("utf-8")).hexdigest()[:8]
            )
            
        # Ensure review_url is present
        if "review_url" not in df.columns:
            def get_fallback_url(row):
                src = str(row.get("source_type", ""))
                if "play" in src:
                    return "https://play.google.com/store/apps/details?id=com.grofers.customerapp"
                elif "app" in src:
                    return "https://apps.apple.com/in/app/blinkit-groceries-more/id1393452285"
                elif "reddit" in src:
                    return "https://www.reddit.com/r/india/"
                else:
                    return "https://play.google.com/store/apps/details?id=com.grofers.customerapp"
            df["review_url"] = df.apply(get_fallback_url, axis=1)
            
        # Parse missing sentiments
        if "sentiment" not in df.columns:
            def parse_sentiment(r):
                try:
                    val = float(r)
                    if val >= 4:
                        return "POSITIVE"
                    elif val <= 2:
                        return "NEGATIVE"
                    else:
                        return "NEUTRAL"
                except Exception:
                    return "NEUTRAL"
            df["sentiment"] = df["rating"].apply(parse_sentiment)
            
    return df


def load_analysis_report(file_path):
    """Loads Phase 5 report from JSON."""
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_backend_pipeline():
    """Triggers the backend pipeline using main.py directly."""
    try:
        import importlib
        if "main" in sys.modules:
            importlib.reload(sys.modules["main"])
        else:
            import main
        main.main()
        st.cache_data.clear() # Clear streamlit cache
        return True
    except Exception as e:
        st.error(f"Failed to execute backend: {e}")
        return False

# ---------------------------------------------------------
# UI Header and Bootstrapping Check
# ---------------------------------------------------------
st.sidebar.image("blinkit_logo.svg", width=120)
st.sidebar.title("Discovery Engine")
st.sidebar.caption("AI-powered Growth Analytics")

df_reviews = load_clean_reviews(CLEAN_CSV_PATH)
report_data = load_analysis_report(REPORT_JSON_PATH)

def render_view_evidence(cited_ids, df_reviews):
    """Renders a collapsible evidence list of matching cited reviews."""
    if not cited_ids:
        st.write("*(No specific reviews cited by the AI)*")
        return
        
    # Standardize cited IDs
    clean_ids = [str(cid).strip().lower() for cid in cited_ids]
    
    # Filter reviews matching the IDs
    matches = df_reviews[df_reviews["review_id"].astype(str).str.lower().isin(clean_ids)]
    
    if matches.empty:
        st.write("*(No matching reviews found in corpus for these cited IDs)*")
        return
        
    st.markdown("**View Evidence:**")
    for _, row in matches.iterrows():
        # Setup source name
        src_clean = str(row['source_type']).replace("_", " ").title()
        
        # Rating display
        rating_val = row.get('rating')
        rating_str = f"⭐ {int(rating_val)}" if pd.notna(rating_val) and str(rating_val).strip() != "" else "No Rating"
        
        # Clickable source link
        url = row.get('review_url', 'https://play.google.com/store/apps/details?id=com.grofers.customerapp')
        
        # Render clean card style block
        st.markdown(
            f"""
            <div style="background-color: #f8f9fa; border-left: 5px solid #ff9900; padding: 12px; margin-bottom: 12px; border-radius: 4px;">
                <strong>[{src_clean}]</strong> ID: <code>{row['review_id']}</code> | Rating: <strong>{rating_str}</strong> | 
                <a href="{url}" target="_blank">View Original Source</a>
                <p style="margin-top: 6px; font-style: italic; font-size: 14px;">"{row['original_text']}"</p>
                <small style="color: gray;">Click the link above to view the original review.</small>
            </div>
            """,
            unsafe_allow_html=True
        )

# Bootstrapping trigger if files are missing
if df_reviews is None or report_data is None:
    st.warning("⚠️ No local data or analysis report found! The backend pipeline needs to run to collect and clean reviews.")
    if st.button("🚀 Run Backend Data & AI Ingestion Pipeline"):
        with st.spinner("Executing pipeline (Ingesting, cleaning, and querying Gemini)..."):
            success = run_backend_pipeline()
            if success:
                st.success("Ingestion pipeline completed successfully! Reloading page...")
                st.rerun()
    st.stop()

# ---------------------------------------------------------
# Sidebar Filter & Navigation
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("Navigation")
page = st.sidebar.radio(
    "Select view",
    ["📊 Overview Dashboard", "🎭 User Sentiment Analysis", "🚨 Customer Pain Points", "👥 User Segmentation", "💡 AI Opportunity Generator", "🔍 AI Research Copilot"]
)

st.sidebar.markdown("---")
# Quick source stats filter
st.sidebar.subheader("Feedback Sources Active")
sources_present = df_reviews["source_type"].unique() if df_reviews is not None else []
for src in sources_present:
    src_clean = src.replace("_", " ").title()
    count = len(df_reviews[df_reviews["source_type"] == src])
    st.sidebar.write(f"✓ **{src_clean}** ({count} items)")

# ---------------------------------------------------------
# Page 1: Overview Dashboard
# ---------------------------------------------------------
if page == "📊 Overview Dashboard":
    st.title("📊 Discovery Engine Overview")
    st.markdown("This dashboard presents key analytics on category exploration barriers across Blinkit customer reviews.")

    # Metric Cards
    m1, m2, m3, m4, m5 = st.columns(5)
    total_count = len(df_reviews)
    m1.metric(label="Total Reviews Analyzed", value=total_count)
    
    play_count = len(df_reviews[df_reviews["source_type"] == "play_store"])
    m2.metric(label="Play Store Reviews", value=play_count)
    
    app_count = len(df_reviews[df_reviews["source_type"] == "app_store"])
    m3.metric(label="App Store Reviews", value=app_count)
    
    reddit_count = len(df_reviews[df_reviews["source_type"] == "reddit"])
    m4.metric(label="Reddit Mentions", value=reddit_count)
    
    form_count = len(df_reviews[df_reviews["source_type"] == "google_form"])
    m5.metric(label="Google Form Responses", value=form_count)

    st.markdown("---")

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Data Sources Distribution")
        # Build Altair Bar Chart for Sources
        source_df = df_reviews["source_type"].value_counts().reset_index()
        source_df.columns = ["Source", "Count"]
        source_df["Source"] = source_df["Source"].str.replace("_", " ").str.title()
        
        chart = alt.Chart(source_df).mark_bar(color="#f4c430").encode(
            x=alt.X("Count:Q", title="Number of reviews"),
            y=alt.Y("Source:N", sort="-x", title="Source Channel"),
            tooltip=["Source", "Count"]
        ).properties(height=250)
        
        st.altair_chart(chart, use_container_width=True)

    with c2:
        st.subheader("Overall Sentiment Summary")
        # Build Altair Pie/Donut Chart for Sentiments
        sentiment_df = df_reviews["sentiment"].value_counts().reset_index()
        sentiment_df.columns = ["Sentiment", "Count"]
        
        sentiment_colors = {
            "POSITIVE": "#2ecc71",
            "NEUTRAL": "#95a5a6",
            "NEGATIVE": "#e74c3c"
        }
        
        donut_chart = alt.Chart(sentiment_df).mark_arc(innerRadius=50).encode(
            theta=alt.Theta("Count:Q", title="Reviews count"),
            color=alt.Color("Sentiment:N", 
                            scale=alt.Scale(domain=list(sentiment_colors.keys()), range=list(sentiment_colors.values())),
                            title="Sentiment"),
            tooltip=["Sentiment", "Count"]
        ).properties(height=250)
        
        st.altair_chart(donut_chart, use_container_width=True)

    st.markdown("---")
    st.subheader("Latest Feedback Excerpts")
    # Show last 5 cleaned reviews
    st.dataframe(
        df_reviews[["review_id", "source_type", "original_text", "sentiment", "timestamp"]]
        .rename(columns={"review_id": "ID", "source_type": "Source", "original_text": "Review Text", "sentiment": "Sentiment", "timestamp": "Date"})
        .head(5),
        use_container_width=True
    )

# ---------------------------------------------------------
# Page 2: User Sentiment Analysis
# ---------------------------------------------------------
elif page == "🎭 User Sentiment Analysis":
    st.title("🎭 User Sentiment & Topic Distribution")
    st.markdown("Deep dive into user sentiments, star ratings, and common keywords.")

    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("Star Rating Distribution (Google Play & App Store)")
        # Filter reviews with integer ratings
        rating_df = df_reviews[df_reviews["rating"].notna()].copy()
        rating_df["rating"] = rating_df["rating"].astype(int)
        
        if not rating_df.empty:
            rating_counts = rating_df["rating"].value_counts().reset_index()
            rating_counts.columns = ["Rating", "Count"]
            
            rating_chart = alt.Chart(rating_counts).mark_bar(color="#ff9900").encode(
                x=alt.X("Rating:O", title="Star Rating (1-5)"),
                y=alt.Y("Count:Q", title="Number of Reviews"),
                tooltip=["Rating", "Count"]
            ).properties(height=300)
            st.altair_chart(rating_chart, use_container_width=True)
        else:
            st.info("No numerical star ratings available to display.")

    with c2:
        st.subheader("Extracts: Active Themes")
        # Pull theme names from JSON report
        theme_names = []
        for cluster in report_data.get("theme_clustering", []):
            for t in cluster.get("themes", []):
                theme_names.append((t.get("theme_name"), t.get("frequency", 0)))
                
        if theme_names:
            st.write("Identified issues weighted by mention count:")
            for tn, freq in sorted(theme_names, key=lambda x: x[1], reverse=True):
                st.info(f"📍 **{tn}** — Mentions: **{freq}**")
        else:
            st.write("No theme metadata found in the AI report.")

    st.markdown("---")
    st.subheader("Common Keywords in Cleaned Corpus")
    # Simple keyword cloud helper using word splits
    all_cleaned_words = " ".join(df_reviews["cleaned_text"].dropna().tolist()).split()
    word_freq = {}
    for w in all_cleaned_words:
        if len(w) > 3: # Skip very short terms
            word_freq[w] = word_freq.get(w, 0) + 1
            
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:15]
    cols = st.columns(5)
    for idx, (word, count) in enumerate(sorted_words):
        cols[idx % 5].metric(label=f"Keyword #{idx+1}", value=word, delta=f"{count} occurrences", delta_color="off")

# ---------------------------------------------------------
# Page 3: Customer Pain Points
# ---------------------------------------------------------
elif page == "🚨 Customer Pain Points":
    st.title("🚨 Customer Pain Points & Issues")
    st.markdown("The primary category discovery friction points extracted from user feedback.")

    theme_clusters = report_data.get("theme_clustering", [])
    
    if theme_clusters:
        for idx, cluster in enumerate(theme_clusters):
            st.subheader(f"🔴 Cluster {idx+1}: {cluster.get('cluster_name')}")
            st.caption(cluster.get("description", ""))
            
            for theme in cluster.get("themes", []):
                st.markdown(f"##### Theme: **{theme.get('theme_name')}** (Frequency: {theme.get('frequency', 'N/A')})")
                
                # Show pain points
                st.write("**Specific Pain Points:**")
                for pp in theme.get("pain_points", []):
                    st.write(f"- 🔴 {pp}")
                
                # Show representative quotes in expander
                with st.expander("💬 View Supporting User Quotes from Reviews"):
                    for quote in theme.get("representative_quotes", []):
                        st.markdown(f"> *\"{quote}\"*")
                
                # Show evidence block
                render_view_evidence(theme.get("cited_review_ids", []), df_reviews)
            st.markdown("---")
    else:
        st.info("No theme clustering report is available yet.")

    # Search & Filter Tool
    st.subheader("🔍 Review Finder Tool")
    search_query = st.text_input("Enter keyword to filter reviews (e.g., 'freshness', 'vegetables', 'recommendation'):")
    if search_query:
        matches = df_reviews[df_reviews["cleaned_text"].str.contains(search_query.lower(), na=False)]
        st.write(f"Found **{len(matches)}** reviews containing '{search_query}':")
        for idx, row in matches.head(10).iterrows():
            st.markdown(f"**[{row['source_type'].upper()}] (Rating: {row['rating']})**")
            st.markdown(f"> *\"{row['original_text']}\"*")
            st.markdown("---")

# ---------------------------------------------------------
# Page 4: User Segmentation
# ---------------------------------------------------------
elif page == "👥 User Segmentation":
    st.title("👥 User Segmentation Exploration")
    st.markdown("AI-generated customer personas based on category exploration likelihood.")

    segments = report_data.get("user_segments", [])
    
    if segments:
        seg_cols = st.columns(len(segments))
        for idx, seg in enumerate(segments):
            with seg_cols[idx]:
                st.subheader(seg.get("segment_name"))
                
                # Setup color based on likelihood
                likelihood = seg.get("exploration_likelihood", "Medium")
                color = "green" if likelihood == "High" else "orange" if likelihood == "Medium" else "red"
                
                st.markdown(f"Exploration Likelihood: :**{color}**[{likelihood}]")
                st.markdown(f"**Characteristics:**\n{seg.get('characteristics')}")
                
                st.markdown("**Primary Barriers:**")
                for bar in seg.get("primary_barriers", []):
                    st.markdown(f"- ⚠️ {bar}")
    else:
        # Default fallback presentation
        st.subheader("Default Personas")
        c1, c2 = st.columns(2)
        with c1:
            st.info("🧩 **Routine Buyer** (Likelihood: Low) \n\n **Characteristics:** Orders same bread and milk. \n\n **Barriers:** Habit inertia, Buy Again UX.")
        with c2:
            st.success("🧩 **New Product Explorer** (Likelihood: High) \n\n **Characteristics:** Searches premium items. \n\n **Barriers:** Assortment visibility gap.")

# ---------------------------------------------------------
# Page 5: AI Opportunity Generator
# ---------------------------------------------------------
elif page == "💡 AI Opportunity Generator":
    st.title("💡 AI Opportunity & Product Generator")
    st.markdown("Structured recommendations and product opportunity backlog matching the Blinkit Growth Case Study.")

    # 1. Jobs-To-Be-Done (JTBD)
    st.subheader("🎯 Jobs-To-Be-Done (JTBD) Hypotheses")
    jtbds = report_data.get("jtbd", [])
    if jtbds:
        for idx, jtbd in enumerate(jtbds):
            st.info(
                f"**Job #{idx+1}**\n\n"
                f"- **When:** {jtbd.get('situation')}\n"
                f"- **I want to:** {jtbd.get('motivation')}\n"
                f"- **So that:** {jtbd.get('expected_outcome')}"
            )
    else:
        st.write("No JTBD list found in report.")

    st.markdown("---")

    # 2. Opportunities Table
    st.subheader("📋 Opportunity Backlog")
    opportunities = report_data.get("opportunities", [])
    if opportunities:
        opp_table = []
        for opp in opportunities:
            opp_table.append({
                "Opportunity": opp.get("opportunity_name"),
                "Description": opp.get("description"),
                "Target Segment": opp.get("target_segment"),
                "Impact": opp.get("business_impact"),
                "Effort Tier": opp.get("effort_tier")
            })
        st.table(pd.DataFrame(opp_table))
        
        # Display supporting quotes and clickable evidence reviews
        st.subheader("💬 Opportunity Evidence Citations")
        for opp in opportunities:
            st.markdown(f"###### Supporting Quotes for *{opp.get('opportunity_name')}*:")
            for ev in opp.get("evidence", []):
                st.markdown(f"> *\"{ev}\"*")
            # Render evidence reviews card
            render_view_evidence(opp.get("cited_review_ids", []), df_reviews)
            st.write("")
    else:
        st.write("No Opportunities backlog found in report.")

    st.markdown("---")

    # 3. Root Cause Analysis
    st.subheader("🌲 Root Cause Trees")
    root_causes = report_data.get("root_cause_analysis", [])
    if root_causes:
        for rc in root_causes:
            st.error(f"**Symptom:** {rc.get('symptom')}")
            st.warning(f"  └── **Intermediate Cause:** {rc.get('intermediate_cause')}")
            st.success(f"    └── **Systemic Root Cause:** {rc.get('root_cause')}")
            st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.write("No Root Cause trees found in report.")

    # Calibration Summary
    st.markdown("---")
    overall = report_data.get("overall_analysis", {})
    st.subheader("Calibration & Confidence Summary")
    st.markdown(f"**Engine Confidence Rating:** :blue[{overall.get('confidence_score', 'N/A')}]")
    st.markdown(f"**Calibration Details:** {overall.get('confidence_rationale', '')}")

# ---------------------------------------------------------
# Page 6: AI Research Copilot
# ---------------------------------------------------------
elif page == "🔍 AI Research Copilot":
    st.title("🔍 AI Research Copilot")
    st.markdown("Ask custom research questions to the AI Discovery Engine. The engine will retrieve the most relevant reviews from the filtered corpus and perform real-time structured analysis backed by concrete evidence.")

    custom_question = st.text_input(
        "Enter your research question:",
        value="Why don't users explore categories?",
        placeholder="e.g., Why don't users try fresh organic milk? or Why do users switch to Zepto?"
    )

    if st.button("🚀 Analyze & Generate Insights"):
        if not custom_question.strip():
            st.warning("Please enter a valid research question.")
        else:
            with st.spinner("Retrieving relevant reviews and invoking AI synthesis..."):
                try:
                    # 1. Initialize retrieval engine
                    from discovery_engine.retrieval.engine import RetrievalEngine
                    from discovery_engine.llm.prompt_builder import PromptBuilder
                    from discovery_engine.llm.client import GeminiClient
                    
                    retriever = RetrievalEngine()
                    # Use absolute path for safety
                    discovery_path = os.path.join(BASE_DIR, "blinkit_discovery_reviews.csv")
                    retriever.load_corpus(discovery_path)
                    
                    # 2. Retrieve top 20 reviews
                    top_reviews = retriever.retrieve(query=custom_question, top_k=20)
                    
                    if not top_reviews:
                        st.error("No reviews could be retrieved for this question.")
                    else:
                        st.success(f"Retrieved **{len(top_reviews)}** supporting reviews from corpus!")
                        
                        # 3. Build Prompt
                        business_goal = "Increase the percentage of Monthly Active Customers (MAC) who purchase from at least one new category every month."
                        prompt = PromptBuilder.build_synthesis_prompt(
                            business_goal=business_goal,
                            question=custom_question,
                            reviews=top_reviews
                        )
                        
                        # 4. Call Gemini/Groq client
                        client = GeminiClient()
                        analysis_result = client.generate_content(prompt, json_mode=True)
                        
                        if "error" in analysis_result:
                            st.error(f"Failed to generate insights: {analysis_result['error']}")
                            if "raw_output" in analysis_result:
                                st.code(analysis_result["raw_output"])
                        else:
                            st.balloons()
                            st.markdown("### 📊 Analysis Results")
                            
                            # Concise AI-generated answer/confidence summary
                            overall = analysis_result.get("overall_analysis", {})
                            st.subheader("Calibration & Confidence Summary")
                            st.markdown(f"**Engine Confidence Rating:** :blue[{overall.get('confidence_score', 'N/A')}]")
                            st.markdown(f"**Calibration Details:** {overall.get('confidence_rationale', '')}")
                            
                            st.markdown("---")
                            
                            # Render Theme Clustering
                            st.subheader("🚨 Identified Customer Pain Points & Themes")
                            theme_clusters = analysis_result.get("theme_clustering", [])
                            if theme_clusters:
                                for idx, cluster in enumerate(theme_clusters):
                                    st.markdown(f"#### Cluster {idx+1}: {cluster.get('cluster_name')}")
                                    st.caption(cluster.get("description", ""))
                                    for theme in cluster.get("themes", []):
                                        st.markdown(f"##### Theme: **{theme.get('theme_name')}** (Frequency: {theme.get('frequency', 'N/A')})")
                                        for pp in theme.get("pain_points", []):
                                            st.write(f"- 🔴 {pp}")
                                        with st.expander("💬 View Supporting Quotes"):
                                            for q in theme.get("representative_quotes", []):
                                                st.markdown(f"> *\"{q}\"*")
                                        render_view_evidence(theme.get("cited_review_ids", []), df_reviews)
                                        st.write("")
                            else:
                                st.info("No theme clusters generated for this query.")
                                
                            st.markdown("---")
                            
                            # Render Opportunities
                            st.subheader("💡 Opportunity Backlog")
                            opportunities = analysis_result.get("opportunities", [])
                            if opportunities:
                                opp_table = []
                                for opp in opportunities:
                                    opp_table.append({
                                        "Opportunity": opp.get("opportunity_name"),
                                        "Description": opp.get("description"),
                                        "Target Segment": opp.get("target_segment"),
                                        "Impact": opp.get("business_impact"),
                                        "Effort Tier": opp.get("effort_tier")
                                    })
                                st.table(pd.DataFrame(opp_table))
                                
                                for opp in opportunities:
                                    st.markdown(f"###### Supporting Quotes for *{opp.get('opportunity_name')}*:")
                                    for ev in opp.get("evidence", []):
                                        st.markdown(f"> *\"{ev}\"*")
                                    render_view_evidence(opp.get("cited_review_ids", []), df_reviews)
                                    st.write("")
                            else:
                                st.info("No opportunity backlog generated for this query.")
                                
                            st.markdown("---")
                            
                            # JTBD
                            st.subheader("🎯 Jobs-To-Be-Done (JTBD) Hypotheses")
                            jtbds = analysis_result.get("jtbd", [])
                            if jtbds:
                                for idx, jtbd in enumerate(jtbds):
                                    st.info(
                                        f"**Job #{idx+1}**\n\n"
                                        f"- **When:** {jtbd.get('situation')}\n"
                                        f"- **I want to:** {jtbd.get('motivation')}\n"
                                        f"- **So that:** {jtbd.get('expected_outcome')}"
                                    )
                                    
                            # Root Cause
                            st.subheader("🌲 Root Cause Trees")
                            root_causes = analysis_result.get("root_cause_analysis", [])
                            if root_causes:
                                for rc in root_causes:
                                    st.error(f"**Symptom:** {rc.get('symptom')}")
                                    st.warning(f"  └── **Intermediate Cause:** {rc.get('intermediate_cause')}")
                                    st.success(f"    └── **Systemic Root Cause:** {rc.get('root_cause')}")
                                    st.write("")
                                    
                except Exception as ex:
                    st.error(f"An error occurred during analysis: {ex}")
