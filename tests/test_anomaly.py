import pytest

def test_detect_anomaly_valid_input(client, valid_healthy_payload, valid_critical_payload):
    """Test /detect_anomaly returns a boolean and float score for a valid input payload."""
    for payload in [valid_healthy_payload, valid_critical_payload]:
        response = client.post("/detect_anomaly", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "is_anomaly" in data
        assert isinstance(data["is_anomaly"], bool)
        assert "anomaly_score" in data
        assert isinstance(data["anomaly_score"], float)
        assert "message" in data
        assert isinstance(data["message"], str)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])


