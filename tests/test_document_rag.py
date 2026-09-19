import pytest

def test_analyze_document(client):
    """Test /analyze_document text extraction and risk keyword detection."""
    sample_text = (
        "Project Sentinel Weekly Status Report - Week 14. "
        "Milestone 3 delivery is currently delayed and at risk due to critical resource constraints on backend engineering. "
        "The target due date is October 15, 2026."
    )
    files = {
        "file": ("status_report.txt", sample_text.encode("utf-8"), "text/plain")
    }
    
    response = client.post("/analyze_document", files=files)
    assert response.status_code == 200
    
    data = response.json()
    assert data["filename"] == "status_report.txt"
    assert data["word_count"] > 10
    assert "risk_mentions" in data
    assert len(data["risk_mentions"]) >= 1
    assert "delayed" in data["risk_mentions"][0].lower() or "at risk" in data["risk_mentions"][0].lower()
    assert "deadline_mentions" in data

def test_ask_no_knowledge_base(client):
    """Test asking a question for a project_id with no ingested documents returns 'no knowledge base' message without crashing."""
    payload = {
        "project_id": "PROJ-UNINGESTED-999",
        "question": "What is the current delivery status?"
    }
    
    response = client.post("/ask", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["project_id"] == "PROJ-UNINGESTED-999"
    assert data["retrieved_chunks"] == []
    assert "no project knowledge base exists" in data["answer"].lower()

def test_ingest_and_ask_flow(client):
    """Test end-to-end RAG ingestion and Q&A retrieval flow."""
    test_proj_id = "PROJ-TEST-RAG-101"
    document_text = (
        "Project Sentinel Release Notes - Phase 2. "
        "The lead engineer for backend development is Sarah Jenkins. "
        "Sprint 4 completion rate reached 92% after resolving critical database query performance bottlenecks."
    )
    
    # 1. Ingest Document
    ingest_payload = {
        "project_id": test_proj_id,
        "text": document_text,
        "document_name": "release_notes.txt"
    }
    ingest_res = client.post("/ingest_document", json=ingest_payload)
    assert ingest_res.status_code == 200
    assert ingest_res.json()["status"] == "success"
    assert ingest_res.json()["chunks_ingested"] >= 1
    
    # 2. Ask Question
    ask_payload = {
        "project_id": test_proj_id,
        "question": "Who is the lead engineer for backend development?"
    }
    ask_res = client.post("/ask", json=ask_payload)
    assert ask_res.status_code == 200
    
    ask_data = ask_res.json()
    assert len(ask_data["retrieved_chunks"]) >= 1
    assert "answer" in ask_data
    assert "sarah jenkins" in ask_data["answer"].lower() or "sarah" in ask_data["retrieved_chunks"][0]["chunk_text"].lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

