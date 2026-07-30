from discovery_engine.llm.prompt_builder import PromptBuilder

def test_prompt_builder_synthesis():
    business_goal = "Increase exploration"
    question = "Why don't users explore?"
    reviews = [
        {
            "review_id": "doc_1",
            "source_type": "play_store",
            "timestamp": "2026-07-28T09:00:00Z",
            "rating": 1,
            "sentiment": "NEGATIVE",
            "original_text": "Worst quality tomatoes"
        }
    ]
    
    prompt = PromptBuilder.build_synthesis_prompt(business_goal, question, reviews)
    
    assert "Increase exploration" in prompt
    assert "Why don't users explore?" in prompt
    assert "doc_1" in prompt
    assert "play_store" in prompt
    assert "Worst quality tomatoes" in prompt
    assert "JSON Schema format to return:" in prompt
