import os
import json
import logging
from typing import List, Dict, Any
import httpx

logger = logging.getLogger("PipelineLogger")

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.1-8b-instant"

def extract_insights_from_reviews(reviews: List[Dict[str, Any]], output_path: str = "data/synthesized_needs.json") -> List[Dict[str, Any]]:
    """
    Takes cleaned reviews, calls Groq API in batches to parse user insights as structured JSON,
    and exports the results to local file.
    """
    logger.info("Initializing AI Processing Layer: Extracting User Insights...")
    groq_api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", DEFAULT_MODEL)

    synthesized_data = []

    if not groq_api_key or groq_api_key.startswith("YOUR_"):
        logger.warning("GROQ_API_KEY is not configured or is a placeholder. Using mock inference engine.")
        # Perform mock heuristics mapping to avoid remote call
        for idx, rev in enumerate(reviews):
            insights = get_mock_insights_for_text(rev.get("cleaned_text", ""))
            merged = {**rev, **insights}
            synthesized_data.append(merged)
    else:
        logger.info(f"Using Groq API with model={model} to analyze {len(reviews)} reviews...")
        
        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json"
        }

        system_prompt = (
            "You are an AI Product Analyst. Analyze the customer review text and return a JSON object with EXACTLY the following keys:\n"
            "- sentiment: (POSITIVE, NEGATIVE, or NEUTRAL)\n"
            "- frustration_level: (High, Medium, or Low)\n"
            "- intent: (A short description of what the user was trying to achieve)\n"
            "- user_segment: (Routine Buyer, Premium Explorer, or Health Conscious/Premium Seeker)\n"
            "- unmet_need: (Specific need or feature missing/broken)\n"
            "- root_cause: (Why the category exploration or purchase failed)\n"
            "Return ONLY the raw JSON object, no Markdown syntax, no backticks, no text wrapping."
        )

        with httpx.Client(headers=headers, timeout=20.0) as client:
            for idx, rev in enumerate(reviews):
                logger.info(f"Analyzing review {idx + 1}/{len(reviews)} (id={rev.get('review_id')})...")
                
                try:
                    payload = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": rev.get("original_text")}
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.1
                    }
                    
                    response = client.post(GROQ_ENDPOINT, json=payload)
                    
                    if response.status_code == 200:
                        content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "{}")
                        insights = json.loads(content)
                        merged = {**rev, **insights}
                        synthesized_data.append(merged)
                    else:
                        logger.warning(f"Groq API returned error status {response.status_code}: {response.text}. Using fallback mapping.")
                        insights = get_mock_insights_for_text(rev.get("cleaned_text", ""))
                        merged = {**rev, **insights}
                        synthesized_data.append(merged)
                        
                except Exception as e:
                    logger.error(f"Error processing review index {idx} with Groq: {e}. Using fallback.")
                    insights = get_mock_insights_for_text(rev.get("cleaned_text", ""))
                    merged = {**rev, **insights}
                    synthesized_data.append(merged)

    # Save to synthesized needs JSON
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(synthesized_data, f, indent=2)
        logger.info(f"Saved synthesized AI insights to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to save synthesized needs: {e}")
        raise e

    return synthesized_data

def get_mock_insights_for_text(text: str) -> Dict[str, Any]:
    """Helper that uses simple heuristics to generate logical mock metadata for reviews."""
    text_lower = text.lower()
    
    # Defaults
    sentiment = "NEUTRAL"
    frustration = "Low"
    intent = " replenishment of groceries"
    segment = "Routine Buyer"
    unmet_need = "Variety and navigation incentives"
    root_cause = "Habitual immediate checkouts limit category exploration"

    if any(k in text_lower for k in ["bad", "stale", "rotten", "bruised", "worse", "crap"]):
        sentiment = "NEGATIVE"
        frustration = "High"
        intent = "purchase fresh foods with trust"
        segment = "Health Conscious/Premium Seeker"
        unmet_need = "Reliable quality control and verification tags"
        root_cause = "Trust deficit due to receiving near-expiry/rotten items"
    elif any(k in text_lower for k in ["browse", "explore", "search", "filter", "find"]):
        sentiment = "NEGATIVE"
        frustration = "Medium"
        intent = "discover new premium product categories"
        segment = "Premium Explorer"
        unmet_need = "Intuitive recommendation boards and robust filter structures"
        root_cause = "App design optimization prioritizes speed checkout over discovery"
    elif any(k in text_lower for k in ["good", "love", "amazing", "fast", "speed"]):
        sentiment = "POSITIVE"
        frustration = "Low"
        intent = "rapid ordering of daily staples"
        segment = "Routine Buyer"
        unmet_need = "Enhanced repeat order automation"
        root_cause = "Excellent speed/convenience infrastructure"

    return {
        "sentiment": sentiment,
        "frustration_level": frustration,
        "intent": intent,
        "user_segment": segment,
        "unmet_need": unmet_need,
        "root_cause": root_cause
    }
