import math
import pytest

def test_predict_valid_request(client, valid_healthy_payload):
    """Test /predict endpoint with a valid 15-feature payload returns 200 OK and expected schema."""
    response = client.post("/predict", json=valid_healthy_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "predicted_risk_level" in data
    assert data["predicted_risk_level"] in ["Low", "Medium", "High"]
    assert "probabilities" in data
    assert "calibrated_confidence" in data
    assert isinstance(data["calibrated_confidence"], float)
    assert 0.0 <= data["calibrated_confidence"] <= 1.0
    assert "explanation_sentence" in data

    assert "top_5_shap_factors" in data
    assert len(data["top_5_shap_factors"]) == 5
    assert "health_index" in data
    assert 0.0 <= data["health_index"] <= 100.0
    assert "failure_archetype" in data
    assert "is_escalating" in data
    assert isinstance(data["is_escalating"], bool)

def test_predict_missing_required_fields(client, valid_healthy_payload):
    """Test /predict with missing required fields returns 422 Validation Error."""
    # Test empty payload
    response_empty = client.post("/predict", json={})
    assert response_empty.status_code == 422
    
    # Test missing required week_number field
    incomplete_payload = valid_healthy_payload.copy()
    del incomplete_payload["week_number"]
    response_missing = client.post("/predict", json=incomplete_payload)
    assert response_missing.status_code == 422

def test_predict_probabilities_sum_to_one(client, valid_healthy_payload, valid_critical_payload):
    """Test that risk probabilities always sum to approximately 1.0 across different input payloads."""
    for payload in [valid_healthy_payload, valid_critical_payload]:
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        
        probs = response.json()["probabilities"]
        prob_sum = sum(probs.values())
        assert math.isclose(prob_sum, 1.0, abs_tol=1e-3), f"Probabilities sum to {prob_sum}, expected ~1.0"

def test_predict_known_high_risk_case(client):
    """Regression test: Validates model performance on the known high-risk running benchmark case.
    
    Verifies that this exact payload returns High risk, High probability > 0.9,
    and overdue_tasks_percentage_delta among top 2 SHAP factors by impact.
    """
    known_high_risk_payload = {
        "project_id": "TEST-PROJ-HIGH-001",
        "project_name": "Test Known High Risk Sprint",
        "week_number": 20.0,
        "issue_count": 32.0,
        "task_completion_rate": 42.9,
        "unresolved_issue_percentage": 57.1,
        "overdue_tasks_percentage": 57.1,
        "defect_density": 28.6,
        "critical_bug_count": 3.0,
        "team_size": 4.0,
        "schedule_progress_percentage": 42.9,
        "stale_days_threshold_used": 39.0,
        "issue_count_delta": 8.0,
        "task_completion_rate_delta": -8.5,
        "overdue_tasks_percentage_delta": 14.2,
        "defect_density_delta": 4.2,
        "team_size_delta": -2.0
    }
    
    response = client.post("/predict", json=known_high_risk_payload)
    assert response.status_code == 200
    
    data = response.json()
    
    # 1. Assert predicted risk level is "High"
    assert data["predicted_risk_level"] == "High"
    
    # 2. Assert High-class probability is above 0.9
    assert data["probabilities"]["High"] > 0.9, f"High probability {data['probabilities']['High']} is not > 0.9"
    
    # 3. Assert overdue_tasks_percentage_delta appears among top 2 SHAP factors by absolute impact
    top_5_shap = data["top_5_shap_factors"]
    # Sort top 5 SHAP factors by absolute impact to ensure ranking by absolute magnitude
    sorted_by_abs_impact = sorted(top_5_shap, key=lambda f: abs(f["shap_impact"]), reverse=True)
    top_2_feature_names = [f["feature"] for f in sorted_by_abs_impact[:2]]
    
    assert "overdue_tasks_percentage_delta" in top_2_feature_names, (
        f"Expected 'overdue_tasks_percentage_delta' in top 2 SHAP factors, got {top_2_feature_names}"
    )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])



