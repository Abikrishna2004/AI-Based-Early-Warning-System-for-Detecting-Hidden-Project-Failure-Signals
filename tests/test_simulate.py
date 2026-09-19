import pytest

def test_simulate_bounds_clamping(client, valid_critical_payload):
    """Test /simulate bounds-clamping logic for percentage metrics exceeding 100% or going below 0%."""
    payload = {
        "features": valid_critical_payload,
        "changes": {
            "overdue_tasks_percentage": 60.0,   # 57.1 + 60.0 = 117.1% -> clamped to 100.0%
            "task_completion_rate": -60.0       # 42.9 - 60.0 = -17.1% -> clamped to 0.0%
        }
    }
    
    response = client.post("/simulate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "warnings" in data
    assert len(data["warnings"]) >= 2
    
    # Verify warning strings mention capping/clamping
    warning_text = " ".join(data["warnings"]).lower()
    assert "capped at 100%" in warning_text or "exceeded 100%" in warning_text
    assert "capped at 0%" in warning_text or "negative" in warning_text
    
    # Verify modified features reflect clamped values
    mod = data["simulated"]["modified_features"]
    assert mod["overdue_tasks_percentage"] == 100.0
    assert mod["task_completion_rate"] == 0.0

def test_simulate_summary_sentence(client, valid_critical_payload):
    """Test /simulate returns baseline vs simulated comparison and a clear summary sentence."""
    payload = {
        "features": valid_critical_payload,
        "changes": {
            "overdue_tasks_percentage": -40.0,
            "critical_bug_count": -3.0
        }
    }
    
    response = client.post("/simulate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "baseline" in data
    assert "simulated" in data
    assert "summary_sentence" in data
    assert isinstance(data["summary_sentence"], str)
    assert len(data["summary_sentence"]) > 10
    
    # Verify summary sentence contains expected descriptive terms
    summary = data["summary_sentence"].lower()
    assert "predicted risk" in summary or "confidence" in summary

if __name__ == "__main__":
    pytest.main([__file__, "-v"])


