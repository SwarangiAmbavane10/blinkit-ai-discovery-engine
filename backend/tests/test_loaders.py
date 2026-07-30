import os
import csv
import pytest
from discovery_engine.loaders.csv_loader import CSVReviewLoader

def test_csv_loader_mapping(tmp_path):
    # Create a temporary CSV file with dynamic columns
    csv_file = tmp_path / "test_feedback.csv"
    
    headers = ["Submission Date", "User Comment", "Stars Awarded", "Reference ID"]
    rows = [
        ["2026-07-28T09:00:00Z", "Very bad quality produce", "1", "ref_001"],
        ["2026-07-27T10:00:00Z", "Highly recommend this app!", "5", "ref_002"]
    ]
    
    with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
        
    loader = CSVReviewLoader(file_path=str(csv_file))
    records = loader.fetch_raw()
    
    assert len(records) == 2
    assert records[0].source_id == "ref_001"
    assert records[0].payload["text"] == "Very bad quality produce"
    assert records[0].payload["rating"] == "1"
    assert records[0].payload["timestamp"] == "2026-07-28T09:00:00Z"
    
    assert records[1].source_id == "ref_002"
    assert records[1].payload["text"] == "Highly recommend this app!"
    assert records[1].payload["rating"] == "5"
    assert records[1].payload["timestamp"] == "2026-07-27T10:00:00Z"
