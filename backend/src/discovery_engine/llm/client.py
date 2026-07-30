import httpx
import json
from typing import Dict, Any, Optional
from discovery_engine.config.settings import settings
from discovery_engine.utils.logging import logger

class GeminiClient:
    """Lightweight REST client wrapper routing to Google Gemini API or Groq API based on settings."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.provider = settings.LLM_PROVIDER
        
        if self.provider == "groq":
            self.api_key = api_key or settings.GROQ_API_KEY
            self.model = model or settings.GROQ_MODEL
        else:
            # Default to gemini
            self.api_key = api_key or settings.GEMINI_API_KEY
            self.model = model or settings.GEMINI_MODEL

    def generate_content(self, prompt: str, json_mode: bool = True) -> Dict[str, Any]:
        """
        Calls the configured LLM API (Gemini or Groq) with the given prompt.
        If json_mode is True, requests structured JSON response.
        """
        if not self.api_key:
            logger.warning(f"{self.provider.upper()}_API_KEY is not configured. Falling back to mock Phase 5 structured JSON.")
            return self._get_mock_phase_5_analysis()

        if self.provider == "groq":
            return self._generate_groq_content(prompt, json_mode)
        else:
            return self._generate_gemini_content(prompt, json_mode)

    def _generate_gemini_content(self, prompt: str, json_mode: bool = True) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }

        # Build payload
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {}
        }

        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        try:
            logger.info(f"Invoking Gemini model={self.model} via REST API...")
            response = httpx.post(url, headers=headers, json=payload, timeout=60.0)
            
            if response.status_code != 200:
                logger.error(f"Gemini API returned status {response.status_code}: {response.text}")
                logger.warning("Falling back to mock Phase 5 structured JSON due to API error.")
                return self._get_mock_phase_5_analysis()

            res_data = response.json()
            # Extract text content from response structure
            candidates = res_data.get("candidates", [])
            if not candidates:
                logger.warning("No candidates returned from Gemini. Returning mock fallback.")
                return self._get_mock_phase_5_analysis()
                
            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return self._parse_json_or_text(text, json_mode)

        except Exception as e:
            logger.error(f"Error calling Gemini REST API: {e}. Falling back to mock analysis.")
            return self._get_mock_phase_5_analysis()

    def _generate_groq_content(self, prompt: str, json_mode: bool = True) -> Dict[str, Any]:
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Build payload for Groq (OpenAI-compatible)
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            logger.info(f"Invoking Groq model={self.model} via REST API...")
            response = httpx.post(url, headers=headers, json=payload, timeout=60.0)
            
            if response.status_code != 200:
                logger.error(f"Groq API returned status {response.status_code}: {response.text}")
                logger.warning("Falling back to mock Phase 5 structured JSON due to API error.")
                return self._get_mock_phase_5_analysis()

            res_data = response.json()
            choices = res_data.get("choices", [])
            if not choices:
                logger.warning("No choices returned from Groq. Returning mock fallback.")
                return self._get_mock_phase_5_analysis()
                
            text = choices[0].get("message", {}).get("content", "")
            return self._parse_json_or_text(text, json_mode)

        except Exception as e:
            logger.error(f"Error calling Groq REST API: {e}. Falling back to mock analysis.")
            return self._get_mock_phase_5_analysis()

    def _parse_json_or_text(self, text: str, json_mode: bool) -> Dict[str, Any]:
        if json_mode:
            # Parse output string as JSON
            try:
                # Strip out markdown json markers if the model included them
                cleaned_text = text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                return json.loads(cleaned_text)
            except json.JSONDecodeError as je:
                logger.error(f"Failed to parse model output as JSON: {je}. Output was: {text}")
                return {"error": "JSON_PARSE_ERROR", "raw_output": text}
        else:
            return {"text": text}

    def _get_mock_phase_5_analysis(self) -> Dict[str, Any]:
        """Returns mock detailed analysis matching the Phase 5 schema constraints."""
        return {
            "theme_clustering": [
                {
                    "cluster_name": "UX Friction & Speed Optimization",
                    "description": "Friction in the purchase journey caused by layouts optimized for repeat purchases.",
                    "themes": [
                        {
                            "theme_name": "Habit/Repeat Purchase Screen Lock-in",
                            "frequency": 8,
                            "pain_points": [
                                "App layout defaults to Buy Again or repeat list, burying other category links.",
                                "Lack of discovery prompts on the main checkout path."
                            ],
                            "representative_quotes": [
                                "The app layout only prompts me to reorder the same stuff, making it hard to see other options.",
                                "I always order bread and milk... But the layout only prompts me to reorder, not browse."
                            ]
                        }
                    ]
                },
                {
                    "cluster_name": "Quality Concerns & Trust Deficit",
                    "description": "Hesitancy to try perishable or sensitive categories due to freshness concerns.",
                    "themes": [
                        {
                            "theme_name": "Fresh Produce Freshness Issues",
                            "frequency": 7,
                            "pain_points": [
                                "Rotten or bruised vegetables delivered in past orders, eroding trust.",
                                "Hesitancy to try fresh meats or produce."
                            ],
                            "representative_quotes": [
                                "I prefer going to the local market for vegetables because of quality concerns.",
                                "The last three times I ordered tomatoes and bananas, they were bruised or stale."
                            ]
                        }
                    ]
                }
            ],
            "root_cause_analysis": [
                {
                    "symptom": "Users checkout repeat items in under 30 seconds but rarely click adjacent categories.",
                    "intermediate_cause": "The homepage and reorder sections dominate the visible viewport, leaving other categories below the fold.",
                    "root_cause": "The UX design is structurally optimized for speed and reorder metrics, suppressing category exploration."
                },
                {
                    "symptom": "High drop-off on fresh produce trial.",
                    "intermediate_cause": "Lack of quality guarantees and previous negative experiences with rotten items.",
                    "root_cause": "Sourcing and last-mile cold chain storage issues leading to quality decay, coupled with low consumer trust."
                }
            ],
            "jtbd": [
                {
                    "situation": "When I need staples in a hurry",
                    "motivation": "I want to checkout instantly with zero friction",
                    "expected_outcome": "So I can get my day started without delays."
                },
                {
                    "situation": "When I am looking to cook a special recipe and need premium spices or fresh herbs",
                    "motivation": "I want to trust that Blinkit has fresh stock and clear curation",
                    "expected_outcome": "So I can confidently order everything in one basket instead of going to a specialty store."
                }
            ],
            "user_segments": [
                {
                    "segment_name": "Habitual Reorderer",
                    "characteristics": "High frequency, buys same 5-10 staples, checkout is extremely fast.",
                    "exploration_likelihood": "Low",
                    "primary_barriers": [
                        "Inertia of 'Buy Again' buttons",
                        "UX ignores exploration interest"
                    ]
                },
                {
                    "segment_name": "Health-Conscious / Premium Seeker",
                    "characteristics": "Willing to spend on organic produce, premium teas, or healthy snacks.",
                    "exploration_likelihood": "High",
                    "primary_barriers": [
                        "Assortment visibility gaps",
                        "Quality trust deficit on fresh items"
                    ]
                }
            ],
            "opportunities": [
                {
                    "opportunity_name": "Co-Purchase Cross-Sell Nudges",
                    "description": "Bundle organic options or recipe-based adjacent items directly in the cart/checkout flow.",
                    "target_segment": "Habitual Reorderer",
                    "business_impact": "High",
                    "effort_tier": "Quick win",
                    "evidence": [
                        "I bought organic soap once and now my whole home page is only soap. Why don't they recommend organic snacks?"
                    ]
                },
                {
                    "opportunity_name": "Quality Guarantees on Fresh Produce",
                    "description": "Introduce visible 'quality stamps' or freshness ratings on L1 landing pages for Fruits & Vegetables.",
                    "target_segment": "Health-Conscious / Premium Seeker",
                    "business_impact": "High",
                    "effort_tier": "Structural bet",
                    "evidence": [
                        "I prefer going to the local market for vegetables because of quality concerns.",
                        " tomatoes and bananas, they were bruised or stale."
                    ]
                }
            ],
            "overall_analysis": {
                "confidence_score": "High",
                "confidence_rationale": "Clustered across 20 mock records from Play Store, App Store, and Reddit showing highly consistent quality and UX friction complaints."
            }
        }
