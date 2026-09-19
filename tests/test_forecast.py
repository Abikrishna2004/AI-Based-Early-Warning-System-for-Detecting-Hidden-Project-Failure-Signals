import pytest

def test_forecast_insufficient_history(client):
    """Test /forecast triggers a 400 Bad Request error when fewer than 3 historical points are provided."""
    payload = {
        "overdue_tasks_percentage": [10.0, 15.0]  # Only 2 points
    }
    
    response = client.post("/forecast", json=payload)
    assert response.status_code == 400
    
    data = response.json()
    assert "detail" in data
    assert "at least 3 weeks" in data["detail"].lower()

def test_forecast_valid_sequence(client):
    """Test /forecast with a valid sequence returns linear trend forecasts for weeks 1, 2, and 3."""
    payload = {
        "overdue_tasks_percentage": [10.0, 12.0, 15.0, 18.0, 22.0, 25.0],
        "defect_density": [2.0, 2.5, 3.0, 3.8, 4.5, 5.0],
        "task_completion_rate": [80.0, 75.0, 70.0, 65.0, 60.0, 55.0]
    }
    
    response = client.post("/forecast", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "forecasts" in data
    assert "overdue_tasks_percentage" in data["forecasts"]
    
    fc = data["forecasts"]["overdue_tasks_percentage"]
    assert "forecast_week_1" in fc
    assert "forecast_week_2" in fc
    assert "forecast_week_3" in fc
    assert fc["forecast_week_1"] > 0.0

def test_forecast_lstm_valid_sequence(client):
    """Test /forecast_lstm with a valid sequence returns hybrid & LSTM forecasts for weeks 1, 2, and 3."""
    payload = {
        "overdue_tasks_percentage": [10.0, 12.0, 15.0, 18.0, 22.0, 25.0],
        "defect_density": [2.0, 2.5, 3.0, 3.8, 4.5, 5.0],
        "task_completion_rate": [80.0, 75.0, 70.0, 65.0, 60.0, 55.0]
    }
    
    response = client.post("/forecast_lstm", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "hybrid_forecasts" in data
    assert "lstm_forecasts" in data
    assert "linear_forecasts" in data
    
    hybrid_overdue = data["hybrid_forecasts"]["overdue_tasks_percentage"]
    assert "forecast_week_1" in hybrid_overdue
    assert "forecast_week_2" in hybrid_overdue
    assert "forecast_week_3" in hybrid_overdue

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

