# Project Sentinel - Backend Integration Test Suite

This directory contains the automated integration test suite for the Project Sentinel FastAPI backend API.

## 📋 Prerequisites & Installation

Ensure `pytest` and `httpx` are installed in your Python environment:

```bash
pip install -r backend/requirements.txt
```

---

## 🚀 Running the Test Suite

From the project root directory (`final_year_project/`), run:

```bash
pytest tests/ -v
```

### Useful Options:
- **Run a specific test file**:
  ```bash
  pytest tests/test_predict.py -v
  ```
- **Run a specific test function**:
  ```bash
  pytest tests/test_predict.py -k "test_predict_valid_request" -v
  ```
- **Show stdout print statements**:
  ```bash
  pytest tests/ -v -s
  ```

---

## 🧪 Test Files Overview

| File | Tested Endpoints & Functionality |
| :--- | :--- |
| [`conftest.py`](file:///c:/Users/ACER/Desktop/final_year_project/tests/conftest.py) | Session-scoped model pre-warming fixture & isolated test database setup |
| [`test_predict.py`](file:///c:/Users/ACER/Desktop/final_year_project/tests/test_predict.py) | `/predict` (200 OK schema, 422 validation, probability sum ≈ 1.0) |
| [`test_simulate.py`](file:///c:/Users/ACER/Desktop/final_year_project/tests/test_simulate.py) | `/simulate` (bounds clamping <0% or >100%, warning generation, comparison summary) |
| [`test_forecast.py`](file:///c:/Users/ACER/Desktop/final_year_project/tests/test_forecast.py) | `/forecast` & `/forecast_lstm` (insufficient history 400 error, 6-point forecast sequence) |
| [`test_document_rag.py`](file:///c:/Users/ACER/Desktop/final_year_project/tests/test_document_rag.py) | `/analyze_document`, `/ingest_document`, `/ask` (document extraction, RAG Q&A, empty KB safety) |
| [`test_anomaly.py`](file:///c:/Users/ACER/Desktop/final_year_project/tests/test_anomaly.py) | `/detect_anomaly` (boolean status & float anomaly score) |
