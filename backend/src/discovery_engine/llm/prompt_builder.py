import json
from typing import List, Dict, Any

class PromptBuilder:
    """Builder class to compile LLM synthesis prompts for the discovery engine."""

    @staticmethod
    def build_synthesis_prompt(
        business_goal: str,
        question: str,
        reviews: List[Dict[str, Any]]
    ) -> str:
        """
        Builds the detailed synthesis prompt containing the goal, question,
        evidence reviews list, and the target output JSON schema.
        """
        # Format the reviews list as text
        reviews_formatted = []
        for i, rev in enumerate(reviews):
            reviews_formatted.append(
                f"REVIEW #{i+1}:\n"
                f"- Review ID: {rev['review_id']}\n"
                f"- Source: {rev['source_type']}\n"
                f"- Date: {rev['timestamp']}\n"
                f"- Rating: {rev['rating'] if rev['rating'] else 'None'}\n"
                f"- Sentiment: {rev['sentiment']}\n"
                f"- Text: \"{rev['original_text']}\"\n"
            )
        reviews_block = "\n".join(reviews_formatted)

        prompt = f"""
You are a senior Business Intelligence Analyst for Blinkit, a leading quick commerce platform in India.
Your task is to analyze user feedback to explain why users are not exploring new categories and to generate actionable business insights.

### 1. Business Context & Goal
- **Business Goal**: {business_goal}
- **Research Question**: {question}

### 2. Evidence Corpus (Top 20 retrieved reviews)
Below are the top 20 reviews most relevant to the research question:
---
{reviews_block}
---

### 3. Required Output Schema
You must perform the analysis based strictly on the provided reviews and return a JSON object matching the schema below.
Ensure you represent the data accurately. Do not fabricate any quotes or IDs.

JSON Schema format to return:
{{
  "theme_clustering": [
    {{
      "cluster_name": "Name of the theme cluster (e.g. UX friction, Quality concerns)",
      "description": "Short explanation of the cluster",
      "themes": [
        {{
          "theme_name": "Specific feedback theme name",
          "frequency": 3, // integer count of reviews supporting this theme
          "pain_points": ["specific pain point 1", "specific pain point 2"],
          "representative_quotes": ["quoted text from supporting reviews"],
          "cited_review_ids": ["Review ID 1", "Review ID 2"] // EXACT Review IDs from the evidence corpus that support this theme
        }}
      ]
    }}
  ],
  "root_cause_analysis": [
    {{
      "symptom": "What is the symptom seen in the feedback?",
      "intermediate_cause": "What immediately causes this symptom?",
      "root_cause": "What is the systemic root cause (UX, Psychology, Merchandising, Supply)?"
    }}
  ],
  "jtbd": [
    {{
      "situation": "When [user situation]...",
      "motivation": "I want to [motivation/action]...",
      "expected_outcome": "So that [outcome/value]..."
    }}
  ],
  "user_segments": [
    {{
      "segment_name": "Name of segment (e.g. Habitual Reorderer, Health Conscious)",
      "characteristics": "Description of traits",
      "exploration_likelihood": "High | Medium | Low",
      "primary_barriers": ["barrier 1", "barrier 2"]
    }}
  ],
  "opportunities": [
    {{
      "opportunity_name": "Name of proposed opportunity/intervention",
      "description": "What should the team do?",
      "target_segment": "Which segment does this target?",
      "business_impact": "High | Medium | Low",
      "effort_tier": "Quick win | Structural bet",
      "evidence": ["Citations/quotes from reviews supporting this opportunity"],
      "cited_review_ids": ["Review ID 1", "Review ID 2"] // EXACT Review IDs from the evidence corpus that support this opportunity
    }}
  ],
  "overall_analysis": {{
    "confidence_score": "High | Medium | Low",
    "confidence_rationale": "Why did you choose this confidence score? (mention evidence density, contradictions)"
  }}
}}

### 4. Constraints
- Return **JSON output ONLY**. Do not wrap the JSON in extra markdown format descriptions or conversational text. Return only the parsable JSON string.
- If a section cannot be determined, return an empty array instead of omitting the key.
- Cite the actual text from the reviews in the `representative_quotes` and `evidence` fields.
"""
        return prompt.strip()
