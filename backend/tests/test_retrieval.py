import os
import csv
from discovery_engine.retrieval.engine import RetrievalEngine

def test_retrieval_engine(tmp_path):
    csv_file = tmp_path / "clean_reviews.csv"
    
    headers = ["review_id", "source_type", "source_id", "original_text", "cleaned_text", "rating", "timestamp", "sentiment", "content_hash"]
    rows = [
        ["doc_1", "play_store", "gp_1", "I hate vegetables quality, rotten tomatoes", "hate vegetables quality rotten tomatoes", "1", "2026-07-28T09:00:00Z", "NEGATIVE", "hash1"],
        ["doc_2", "reddit", "sub_1", "Speed of check out is good, I always reorder milk", "speed check good always reorder milk", "4", "2026-07-27T10:00:00Z", "POSITIVE", "hash2"],
        ["doc_3", "play_store", "gp_2", "Why is it hard to explore gourmet categories?", "hard explore gourmet categories", "3", "2026-07-26T11:00:00Z", "NEUTRAL", "hash3"]
    ]
    
    with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
        
    engine = RetrievalEngine()
    engine.load_corpus(str(csv_file))
    
    # Query matching doc_3 and doc_1
    results = engine.retrieve(query="Why don't users explore categories?", top_k=2)
    
    # doc_3 contains 'explore' and 'categories'
    assert len(results) >= 1
    assert results[0]["review_id"] == "doc_3"
    assert results[0]["sentiment"] == "NEUTRAL"
    assert results[0]["source_type"] == "play_store"
    assert results[0]["rating"] == "3"
    assert "timestamp" in results[0]
