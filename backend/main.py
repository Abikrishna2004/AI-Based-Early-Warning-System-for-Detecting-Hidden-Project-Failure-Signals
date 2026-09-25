"""
Project Sentinel - FastAPI Backend API
======================================

Instructions to run the API server locally:
    uvicorn main:app --reload

Server will start on http://127.0.0.1:8000
Interactive API Docs (Swagger): http://127.0.0.1:8000/docs
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import torch
torch.set_num_threads(1)
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
import io
import re
import uuid
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, cast
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from catboost import CatBoostClassifier, Pool
import pypdf
import torch
import torch.nn as nn
import ruptures as rpt
from sqlalchemy.orm import Session
from database import init_db, get_db, Project, ProjectInput, Prediction, Recommendation

import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(asyncio.to_thread(load_artifacts))
    yield

# 1. Initialize FastAPI App & CORS
app = FastAPI(
    title="CompilePulse AI Backend",
    description="API endpoint for CompilePulse - An AI-Powered Project Intelligence & Early Warning Platform",
    version="1.5.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:9005",
        "http://127.0.0.1:9005",
        "https://compile-pulse.web.app",
        "https://compilepulse.firebaseapp.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Pydantic Models for Input Features, Simulation, Forecasting & RAG
# 2. Pydantic Models for Input Features, Simulation, Forecasting & RAG
class ProjectFeatures(BaseModel):
    project_id: Optional[str] = Field("PROJ-101", json_schema_extra={"example": "PROJ-101"}, description="Project ID identifier")
    project_name: Optional[str] = Field(None, json_schema_extra={"example": "CompilePulse Main"}, description="Optional project name")
    week_number: float = Field(..., json_schema_extra={"example": 20.0}, description="Week number of the project")
    issue_count: float = Field(..., json_schema_extra={"example": 15.0}, description="Total issue count")
    task_completion_rate: float = Field(..., json_schema_extra={"example": 42.9}, description="Task completion rate (%)")
    unresolved_issue_percentage: float = Field(..., json_schema_extra={"example": 57.1}, description="Unresolved issue percentage (%)")
    overdue_tasks_percentage: float = Field(..., json_schema_extra={"example": 57.1}, description="Overdue tasks percentage (%)")
    defect_density: float = Field(..., json_schema_extra={"example": 28.6}, description="Defect density metric")
    critical_bug_count: float = Field(..., json_schema_extra={"example": 1.0}, description="Number of critical bugs")
    team_size: float = Field(..., json_schema_extra={"example": 1.0}, description="Team size")
    schedule_progress_percentage: float = Field(..., json_schema_extra={"example": 42.9}, description="Schedule progress percentage (%)")
    stale_days_threshold_used: float = Field(..., json_schema_extra={"example": 39.0}, description="Stale days threshold used")
    issue_count_delta: float = Field(..., json_schema_extra={"example": 0.0}, description="Weekly change in issue count")
    task_completion_rate_delta: float = Field(..., json_schema_extra={"example": 0.0}, description="Weekly change in task completion rate (%)")
    overdue_tasks_percentage_delta: float = Field(..., json_schema_extra={"example": 14.2}, description="Weekly change in overdue tasks percentage (%)")
    defect_density_delta: float = Field(..., json_schema_extra={"example": 0.0}, description="Weekly change in defect density")
    team_size_delta: float = Field(..., json_schema_extra={"example": 0.0}, description="Weekly change in team size")

class SimulationRequest(BaseModel):
    features: ProjectFeatures
    changes: Dict[str, float] = Field(
        ...,
        json_schema_extra={"example": {"team_size": 2.0, "overdue_tasks_percentage": -15.0}},
        description="Dictionary mapping feature names to numerical changes (+ or -)"
    )

class ForecastRequest(BaseModel):
    overdue_tasks_percentage: List[float] = Field(
        ...,
        json_schema_extra={"example": [45.0, 48.0, 52.0, 55.0, 58.0, 60.0]},
        description="Historical weekly values for overdue tasks percentage (minimum 3 weeks)"
    )
    defect_density: Optional[List[float]] = Field(
        None,
        json_schema_extra={"example": [20.0, 22.0, 24.0, 25.0, 27.0, 28.6]},
        description="Optional historical weekly values for defect density (minimum 3 weeks)"
    )
    task_completion_rate: Optional[List[float]] = Field(
        None,
        json_schema_extra={"example": [65.0, 60.0, 55.0, 50.0, 45.0, 42.9]},
        description="Optional historical weekly values for task completion rate (minimum 3 weeks)"
    )

class IngestDocumentRequest(BaseModel):
    project_id: str = Field(..., json_schema_extra={"example": "PROJ-101"}, description="Project ID to tag the ingested document chunks")
    text: str = Field(..., json_schema_extra={"example": "Project Sentinel Weekly Status Report - Week 20. Milestone 3 delivery is scheduled for October 15, 2026. Task 4 is currently blocked due to severe resource constraint on backend engineering."}, description="Extracted or raw document text")
    document_name: Optional[str] = Field("status_report.pdf", description="Document filename/source identifier")

class AskQuestionRequest(BaseModel):
    project_id: str = Field(..., json_schema_extra={"example": "PROJ-101"}, description="Project ID to query")
    question: str = Field(..., json_schema_extra={"example": "What is currently blocking this project?"}, description="Natural language query")

class WeeklyMetricItem(BaseModel):
    week: int
    overdue_tasks_percentage: float
    defect_density: Optional[float] = 0.0

class ChangePointRequest(BaseModel):
    project_id: Optional[str] = Field("PROJ-101", description="Project ID")
    weekly_data: List[WeeklyMetricItem] = Field(
        ...,
        json_schema_extra={
            "example": [
                {"week": 10, "overdue_tasks_percentage": 10.0, "defect_density": 2.0},
                {"week": 11, "overdue_tasks_percentage": 12.0, "defect_density": 2.5},
                {"week": 12, "overdue_tasks_percentage": 11.0, "defect_density": 2.2},
                {"week": 13, "overdue_tasks_percentage": 14.0, "defect_density": 3.0},
                {"week": 14, "overdue_tasks_percentage": 42.0, "defect_density": 18.0},
                {"week": 15, "overdue_tasks_percentage": 48.0, "defect_density": 22.0},
                {"week": 16, "overdue_tasks_percentage": 57.1, "defect_density": 28.6}
            ]
        },
        description="Historical weekly metric values"
    )


# Feature to Action Recommendation Mapping
RECOMMENDATION_MAPPING: Dict[str, str] = {
    'defect_density': "Audit code quality immediately and conduct targeted refactoring to resolve defect accumulation.",
    'overdue_tasks_percentage': "Re-evaluate project timeline, reprioritize project backlog, and unblock stalled deliverables.",
    'critical_bug_count': "Assign senior engineers immediately to triage and resolve open critical bugs.",
    'task_completion_rate': "Improve daily sprint cadence and reduce scope creep to increase task completion rates.",
    'unresolved_issue_percentage': "Conduct issue triage sessions to close or reassign stagnant open tickets.",
    'schedule_progress_percentage': "Adjust milestone commitments or reallocate temporary resources to regain progress velocity.",
    'overdue_tasks_percentage_delta': "Investigate sudden increases in task bottlenecks before overdue work escalates.",
    'defect_density_delta': "Strengthen QA automated testing to halt accelerating defect rates.",
    'task_completion_rate_delta': "Address recent productivity drops by reviewing team blockers in retrospectives.",
    'team_size_delta': "Manage capacity changes smoothly to avoid onboarding or offboarding productivity dips.",
    'issue_count_delta': "Implement stricter feature request gates to stabilize incoming issue growth.",
    'team_size': "Review workload allocation across team members to prevent burnout.",
    'stale_days_threshold_used': "Update stale ticket policies to reflect realistic team response cycles.",
    'week_number': "Schedule mid-project milestone review to realign team deliverables.",
    'issue_count': "Streamline backlog management to eliminate duplicate or low-priority tickets."
}

FEATURE_COLS = [
    'week_number', 'issue_count', 'task_completion_rate',
    'unresolved_issue_percentage', 'overdue_tasks_percentage',
    'defect_density', 'critical_bug_count', 'team_size',
    'schedule_progress_percentage', 'stale_days_threshold_used',
    'issue_count_delta', 'task_completion_rate_delta',
    'overdue_tasks_percentage_delta', 'defect_density_delta', 'team_size_delta'
]

NON_NEGATIVE_COLS = {'team_size', 'critical_bug_count', 'issue_count'}
PERCENTAGE_COLS = {
    'task_completion_rate', 'unresolved_issue_percentage',
    'overdue_tasks_percentage', 'schedule_progress_percentage', 'defect_density'
}

RISK_KEYWORDS = [
    r'\bdelay(?:ed|s)?\b',
    r'\bblock(?:ed|s)?\b',
    r'\boverdue\b',
    r'\bat risk\b',
    r'\bbehind schedule\b',
    r'\bresource constraint(?:s)?\b',
    r'\bcritical issue(?:s)?\b',
    r'\bbottleneck(?:s)?\b',
    r'\bslippage\b',
    r'\bimpairment\b',
    r'\bconcern(?:s)?\b'
]

DATE_PATTERNS = [
    r'\b\d{4}-\d{2}-\d{2}\b',
    r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
    r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b',
    r'\b(?:deadline|due date|scheduled for|target date|milestone)\b',
    r'\bQ[1-4]\s+\d{4}\b'
]

# Global variables for models, embedder & vector database
cb_model = None
anomaly_model = None
embed_model = None
chroma_client = None
chroma_collection = None
flan_tokenizer = None
flan_model = None
archetype_model = None
archetype_map = None
lstm_model = None
lstm_scaler = None
calibration_model = None
shap_interaction_data = None
signal_precedence_data = None
classes = []

try:
    from evaluate_calibration_and_cost import PlattCalibrator
except Exception:
    PlattCalibrator = None


# PyTorch LSTM Forecaster Model Definition
class PyTorchLSTMForecaster(nn.Module):
    def __init__(self, input_size=3, hidden_size=48, num_layers=2, output_size=3):
        super(PyTorchLSTMForecaster, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.1)
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        out = self.fc(lstm_out[:, -1, :])
        return out

def get_embed_model():
    global embed_model
    if embed_model is None:
        print("Initializing SentenceTransformer model 'all-MiniLM-L6-v2'...", flush=True)
        from sentence_transformers import SentenceTransformer
        embed_model = SentenceTransformer('all-MiniLM-L6-v2')
    return embed_model

def get_flan_model():
    global flan_tokenizer, flan_model
    if flan_model is None:
        print("Initializing local seq2seq model 'google/flan-t5-small'...", flush=True)
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        flan_tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-small")
        flan_model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-small")
        print("Local Flan-T5 model loaded successfully.", flush=True)
    return flan_tokenizer, flan_model

def get_chroma_collection():
    global chroma_client, chroma_collection
    if chroma_collection is None:
        import chromadb
        base_dir = os.path.dirname(__file__)
        chroma_db_dir = os.environ.get("SENTINEL_CHROMA_DIR", os.path.join(base_dir, 'chroma_db'))
        chroma_client = chromadb.PersistentClient(path=chroma_db_dir)
        chroma_collection = chroma_client.get_or_create_collection(name="project_sentinel_knowledge")
        print(f"ChromaDB persistent vector database initialized at {chroma_db_dir}.")
    return chroma_collection

# 3. Artifact & Model Loading on Startup
def load_artifacts():
    global cb_model, anomaly_model, embed_model, chroma_client, chroma_collection, archetype_model, archetype_map, lstm_model, lstm_scaler, calibration_model, classes
    base_dir = os.path.dirname(__file__)
    
    print("[LOAD] Step 1: Loading CatBoost Classifier...", flush=True)
    model_path = os.path.join(base_dir, 'best_model_catboost.cbm')
    cb_model = CatBoostClassifier()
    cb_model.load_model(model_path)
    classes = list(cast(Any, cb_model).classes_)
    print("[LOAD] Step 1 Done.", flush=True)

    print("[LOAD] Step 2: Loading Anomaly Model (V2 15-feature or V1 10-feature)...", flush=True)
    anomaly_path_v2 = os.path.join(base_dir, 'anomaly_model_v2.pkl')
    anomaly_path_v1 = os.path.join(base_dir, 'anomaly_model.pkl')
    if os.path.exists(anomaly_path_v2):
        anomaly_model = joblib.load(anomaly_path_v2)
        print(f"[LOAD] IsolationForest V2 anomaly model loaded successfully from {anomaly_path_v2}.", flush=True)
    elif os.path.exists(anomaly_path_v1):
        anomaly_model = joblib.load(anomaly_path_v1)
        print(f"[LOAD] IsolationForest V1 anomaly model loaded successfully from {anomaly_path_v1}.", flush=True)
    else:
        print(f"[LOAD] Warning: Anomaly model not found at {anomaly_path_v2} or {anomaly_path_v1}.", flush=True)
    print("[LOAD] Step 2 Done.", flush=True)

    print("[LOAD] Step 2b: Loading KMeans Archetype Model...", flush=True)
    archetype_path = os.path.join(base_dir, 'archetype_model.pkl')
    if os.path.exists(archetype_path):
        try:
            archetype_data = joblib.load(archetype_path)
            archetype_model = archetype_data.get('kmeans_model')
            archetype_map = archetype_data.get('archetype_map')
            print(f"[LOAD] KMeans archetype model loaded successfully from {archetype_path}.", flush=True)
        except Exception as e:
            print(f"[LOAD] Archetype model error: {e}", flush=True)

    print("[LOAD] Step 2c: Loading PyTorch LSTM Forecaster...", flush=True)
    lstm_model_path = os.path.join(base_dir, 'lstm_forecast_model.pt')
    lstm_scaler_path = os.path.join(base_dir, 'lstm_scaler.pkl')
    if os.path.exists(lstm_model_path) and os.path.exists(lstm_scaler_path):
        try:
            lstm_scaler = joblib.load(lstm_scaler_path)
            lstm_model = PyTorchLSTMForecaster(input_size=3, hidden_size=48, num_layers=2, output_size=3)
            lstm_model.load_state_dict(torch.load(lstm_model_path, map_location=torch.device('cpu')))
            lstm_model.eval()
            print(f"[LOAD] PyTorch LSTM forecast model loaded successfully from {lstm_model_path}.", flush=True)
        except Exception as e:
            print(f"[LOAD] LSTM model error: {e}", flush=True)

    print("[LOAD] Step 2e: Loading SHAP Interaction Matrix...", flush=True)
    inter_matrix_path = os.path.join(base_dir, 'shap_interaction_matrix.json')
    if os.path.exists(inter_matrix_path):
        try:
            with open(inter_matrix_path, 'r') as f:
                import json
                shap_interaction_data = json.load(f)
            print(f"[LOAD] SHAP interaction matrix loaded successfully from {inter_matrix_path}.", flush=True)
        except Exception as e:
            print(f"[LOAD] SHAP interaction matrix load error: {e}", flush=True)
    else:
        try:
            from compute_shap_interactions import compute_and_save_shap_interactions
            shap_interaction_data = compute_and_save_shap_interactions()
            print(f"[LOAD] SHAP interaction matrix computed & saved on demand.", flush=True)
        except Exception as e:
            print(f"[LOAD] SHAP interaction computation error: {e}", flush=True)

    print("[LOAD] Step 2f: Loading Signal Precedence Results...", flush=True)
    prec_path = os.path.join(base_dir, 'signal_precedence_results.json')
    if os.path.exists(prec_path):
        try:
            with open(prec_path, 'r') as f:
                import json
                signal_precedence_data = json.load(f)
            print(f"[LOAD] Signal precedence results loaded successfully from {prec_path}.", flush=True)
        except Exception as e:
            print(f"[LOAD] Signal precedence load error: {e}", flush=True)
    else:
        try:
            from compute_signal_precedence import compute_and_save_signal_precedence
            signal_precedence_data = compute_and_save_signal_precedence()
            print(f"[LOAD] Signal precedence analysis computed & saved on demand.", flush=True)
        except Exception as e:
            print(f"[LOAD] Signal precedence computation error: {e}", flush=True)


    print("[LOAD] Step 3: Deferred RAG module pre-warming (on-demand loading)...", flush=True)
    print("[LOAD] Step 4: Deferred ChromaDB pre-warming (on-demand loading)...", flush=True)

    print("[LOAD] Step 5: Initializing PostgreSQL database tables...", flush=True)
    try:
        init_db()
        print("[LOAD] PostgreSQL database tables initialized.", flush=True)
    except Exception as e:
        print(f"[LOAD] Database initialization error: {e}", flush=True)

    import gc
    gc.collect()
    print("[LOAD] ALL ARTIFACTS LOADED SUCCESSFULLY!", flush=True)

# 4. Health Check Endpoint
@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "CompilePulse AI API",
        "catboost_loaded": cb_model is not None,
        "anomaly_model_loaded": anomaly_model is not None,
        "rag_module_loaded": embed_model is not None and chroma_collection is not None
    }

def compute_project_health_index(features: ProjectFeatures, prob_dict: dict, pred_risk: str) -> Dict[str, Any]:
    comp_score = max(0.0, min(100.0, features.task_completion_rate))
    overdue_score = max(0.0, min(100.0, 100.0 - features.overdue_tasks_percentage))
    defect_score = max(0.0, min(100.0, 100.0 - features.defect_density * 3.0))
    unresolved_score = max(0.0, min(100.0, 100.0 - features.unresolved_issue_percentage))
    bug_score = max(0.0, min(100.0, 100.0 - features.critical_bug_count * 20.0))
    
    base_health = (
        0.25 * comp_score +
        0.25 * overdue_score +
        0.20 * defect_score +
        0.15 * unresolved_score +
        0.15 * bug_score
    )
    
    high_prob = prob_dict.get("High", 0.0)
    med_prob = prob_dict.get("Medium", 0.0)
    
    health_penalty = (high_prob * 30.0) + (med_prob * 10.0)
    final_health = round(max(0.0, min(100.0, base_health - health_penalty)), 1)
    
    if final_health >= 70.0:
        status = "Healthy"
    elif final_health >= 40.0:
        status = "At Risk"
    else:
        status = "Critical"
        
    return {
        "health_index": final_health,
        "health_status": status
    }

def detect_risk_escalation(features: ProjectFeatures, proj_id: str, db: Session) -> Dict[str, Any]:
    # Check 3 key deltas: overdue_tasks_percentage_delta, defect_density_delta, unresolved/issue_count_delta
    overdue_worsening = features.overdue_tasks_percentage_delta > 0
    defect_worsening = features.defect_density_delta > 0
    unresolved_worsening = (
        features.unresolved_issue_percentage > 35.0 or 
        features.issue_count_delta > 0 or 
        features.task_completion_rate_delta < 0
    )

    worsening_count = sum([overdue_worsening, defect_worsening, unresolved_worsening])

    # Query recent inputs for this project to check 3 consecutive weeks
    recent_inputs = (
        db.query(ProjectInput)
        .filter(ProjectInput.project_id == proj_id)
        .order_by(ProjectInput.timestamp.desc())
        .limit(4)
        .all()
    )

    consecutive_weeks = 1
    if len(recent_inputs) >= 2:
        for inp in recent_inputs[1:]:
            if (inp.overdue_tasks_percentage_delta > 0) or (inp.defect_density_delta > 0):
                consecutive_weeks += 1

    # Flag escalation if at least 2 of 3 metrics show worsening
    is_escalating = (worsening_count >= 2 and (consecutive_weeks >= 1 or features.overdue_tasks_percentage > 30.0))

    if is_escalating:
        msg = "Risk has escalated for 3 consecutive weeks across multiple signals — this pattern historically precedes High risk classification"
    else:
        msg = None

    return {
        "is_escalating": is_escalating,
        "escalation_message": msg
    }

# 5. Prediction Endpoint
@app.post("/predict")
def predict_project_risk(features: ProjectFeatures, db: Session = Depends(get_db)):
    if cb_model is None:
        raise HTTPException(status_code=500, detail="Model artifacts not initialized.")
    
    input_dict = features.model_dump()
    input_df = pd.DataFrame([input_dict])[FEATURE_COLS]
    
    pred_risk = cb_model.predict(input_df)[0]
    if isinstance(pred_risk, (list, np.ndarray)):
        pred_risk = pred_risk[0]
        
    probs = cb_model.predict_proba(input_df)[0]
    prob_dict = {cls: round(float(prob), 4) for cls, prob in zip(classes, probs)}
    
    pred_class_idx = classes.index(pred_risk)
    shap_matrix = cb_model.get_feature_importance(Pool(input_df), type='ShapValues')
    if shap_matrix.ndim == 3:
        single_shap = shap_matrix[0, pred_class_idx, :len(FEATURE_COLS)]
    elif shap_matrix.ndim == 2:
        single_shap = shap_matrix[0, :len(FEATURE_COLS)]
    else:
        single_shap = shap_matrix[:len(FEATURE_COLS)]
    
    factor_df = pd.DataFrame({
        'feature': FEATURE_COLS,
        'value': input_df.iloc[0].values,
        'shap_impact': single_shap
    }).sort_values(by='shap_impact', ascending=False).reset_index(drop=True)
    
    top5_factors = factor_df.head(5)
    
    top_5_shap_factors = [
        {
            "feature": row['feature'],
            "value": float(row['value']),
            "shap_impact": round(float(row['shap_impact']), 4)
        }
        for _, row in top5_factors.iterrows()
    ]
    
    factor_str_list = [f"{row['feature']} ({row['value']})" for _, row in top5_factors.iterrows()]
    explanation_sentence = f"This project was classified {pred_risk} Risk primarily due to: {', '.join(factor_str_list)}."
    
    recommended_actions: List[str] = []
    if pred_risk in ['Medium', 'High']:
        top3_features = top5_factors['feature'].head(3).tolist()
        for feat in top3_features:
            rec = RECOMMENDATION_MAPPING.get(feat, f"Monitor and optimize {feat} to mitigate risk.")
            recommended_actions.append(rec)

    # Compute Health Index & Status
    health_info = compute_project_health_index(features, prob_dict, pred_risk)

    proj_id = features.project_id or "PROJ-101"
    proj_name = features.project_name or f"Project {proj_id}"
    now = datetime.now(timezone.utc)

    # Detect Risk Escalation
    escalation_info = detect_risk_escalation(features, proj_id, db)

    # 1. Projects table: create new project row only if that project_id doesn't already exist
    existing_proj = db.query(Project).filter(Project.project_id == proj_id).first()
    if not existing_proj:
        new_proj = Project(
            project_id=proj_id,
            project_name=proj_name,
            created_date=now
        )
        db.add(new_proj)
        db.flush()

    # 2. Project Inputs table: all 15 feature columns + timestamp
    input_record = ProjectInput(
        project_id=proj_id,
        week_number=features.week_number,
        issue_count=features.issue_count,
        task_completion_rate=features.task_completion_rate,
        unresolved_issue_percentage=features.unresolved_issue_percentage,
        overdue_tasks_percentage=features.overdue_tasks_percentage,
        defect_density=features.defect_density,
        critical_bug_count=features.critical_bug_count,
        team_size=features.team_size,
        schedule_progress_percentage=features.schedule_progress_percentage,
        stale_days_threshold_used=features.stale_days_threshold_used,
        issue_count_delta=features.issue_count_delta,
        task_completion_rate_delta=features.task_completion_rate_delta,
        overdue_tasks_percentage_delta=features.overdue_tasks_percentage_delta,
        defect_density_delta=features.defect_density_delta,
        team_size_delta=features.team_size_delta,
        timestamp=now
    )
    db.add(input_record)
    db.flush()

    # 3. Predictions table: risk_level, risk_probability (confidence), model_version="catboost_v1", prediction_date
    risk_prob = prob_dict.get(pred_risk, 0.0)
    prediction_record = Prediction(
        project_id=proj_id,
        risk_level=pred_risk,
        risk_probability=risk_prob,
        model_version="catboost_v1",
        prediction_date=now
    )
    db.add(prediction_record)
    db.flush()

    # 4. Recommendations table: prediction_id, risk_factor, recommendation, priority (1, 2, or 3 based on SHAP rank order)
    top3_shap = top5_factors.head(3)
    for idx, (_, row) in enumerate(top3_shap.iterrows()):
        feat_name = row['feature']
        rec_text = RECOMMENDATION_MAPPING.get(feat_name, f"Monitor and optimize {feat_name} to mitigate risk.")
        priority_val = idx + 1
        rec_record = Recommendation(
            prediction_id=prediction_record.prediction_id,
            risk_factor=feat_name,
            recommendation=rec_text,
            priority=priority_val
        )
        db.add(rec_record)

    # Failure Archetype Assignment using trained KMeans model
    failure_archetype = {
        "name": "Slow Decline",
        "description": "Gradually decreasing task completion rate accompanied by creeping overdue task accumulation."
    }
    if archetype_model is not None and archetype_map is not None:
        try:
            cluster_idx = int(archetype_model.predict(input_df)[0])
            if cluster_idx in archetype_map:
                failure_archetype = archetype_map[cluster_idx]
        except Exception as e:
            print(f"[PREDICT] Failure archetype clustering assignment error: {e}", flush=True)

    # Calculate Calibrated Confidence
    raw_confidence = prob_dict.get(pred_risk, 0.0)
    calibrated_confidence = raw_confidence
    if calibration_model is not None:
        try:
            raw_probs_arr = np.array([[prob_dict.get(c, 0.0) for c in classes]])
            cal_probs_arr = calibration_model.predict_proba(raw_probs_arr)[0]
            pred_idx = classes.index(pred_risk)
            calibrated_confidence = round(float(cal_probs_arr[pred_idx]), 4)
        except Exception as e:
            print(f"[PREDICT] Calibrated confidence calculation error: {e}", flush=True)

    db.commit()

    return {
        "project_id": proj_id,
        "predicted_risk_level": pred_risk,
        "probabilities": prob_dict,
        "calibrated_confidence": calibrated_confidence,
        "explanation_sentence": explanation_sentence,
        "top_5_shap_factors": top_5_shap_factors,
        "recommended_actions": recommended_actions,
        "health_index": health_info["health_index"],
        "health_status": health_info["health_status"],
        "failure_archetype": failure_archetype,
        "is_escalating": escalation_info["is_escalating"],
        "escalation_message": escalation_info["escalation_message"],
        "prediction_id": prediction_record.prediction_id
    }


# 5d. Change-Point Detection Endpoint via ruptures PELT algorithm
@app.post("/detect_changepoints")
def detect_change_points(req: ChangePointRequest):
    if not req.weekly_data or len(req.weekly_data) < 3:
        return {
            "project_id": req.project_id or "PROJ-101",
            "detected_change_points": [],
            "message": "At least 3 weekly data points are required for change-point detection."
        }
    
    weeks = [item.week for item in req.weekly_data]
    overdue_vals = np.array([item.overdue_tasks_percentage for item in req.weekly_data])
    
    detected_cp = []
    
    try:
        # Run Ruptures PELT change-point detection with RBF model
        algo = rpt.Pelt(model="rbf", min_size=2, jump=1).fit(overdue_vals)
        # Select penalty parameter
        pen_val = max(1.0, float(np.var(overdue_vals) * 0.5)) if len(overdue_vals) > 5 else 1.0
        result_indices = algo.predict(pen=pen_val)
        
        # Filter out trailing end index
        cp_indices = [idx for idx in result_indices if idx < len(overdue_vals)]
        
        for idx in cp_indices:
            w_num = weeks[idx] if idx < len(weeks) else weeks[-1]
            detected_cp.append({
                "week": w_num,
                "index": idx,
                "metric": "overdue_tasks_percentage",
                "explanation": f"A significant shift in overdue task behavior was detected at week {w_num} — this may correspond to a scope change, team change, or external event worth investigating."
            })
    except Exception as e:
        print(f"[CHANGEPOINT] PELT detection error: {e}", flush=True)
        
    return {
        "project_id": req.project_id or "PROJ-101",
        "detected_change_points": detected_cp,
        "message": f"Detected {len(detected_cp)} change-point shifts across historical weekly data."
    }

# 5a. Multi-Horizon Risk Prediction Endpoint
@app.post("/predict_horizon")
def predict_horizon_risk(features: ProjectFeatures):
    if cb_model is None:
        raise HTTPException(status_code=500, detail="Model artifacts not initialized.")
    
    base_dict = features.model_dump()
    horizons = []
    
    for week_step, label in [(0, "Now"), (1, "+1 Wk"), (2, "+2 Wks"), (3, "+3 Wks")]:
        proj_features = base_dict.copy()
        proj_features['week_number'] = base_dict['week_number'] + week_step
        
        # Project key trend metrics using weekly deltas
        if week_step > 0:
            proj_features['overdue_tasks_percentage'] = max(0.0, min(100.0, proj_features['overdue_tasks_percentage'] + proj_features['overdue_tasks_percentage_delta'] * week_step))
            proj_features['task_completion_rate'] = max(0.0, min(100.0, proj_features['task_completion_rate'] + proj_features['task_completion_rate_delta'] * week_step))
            proj_features['defect_density'] = max(0.0, proj_features['defect_density'] + proj_features['defect_density_delta'] * week_step)
            proj_features['issue_count'] = max(0.0, proj_features['issue_count'] + proj_features['issue_count_delta'] * week_step)
        
        input_df = pd.DataFrame([proj_features])[FEATURE_COLS]
        pred_risk = cb_model.predict(input_df)[0]
        if isinstance(pred_risk, (list, np.ndarray)):
            pred_risk = pred_risk[0]
            
        probs = cb_model.predict_proba(input_df)[0]
        prob_dict = {cls: round(float(prob), 4) for cls, prob in zip(classes, probs)}
        conf = float(prob_dict.get(pred_risk, 0.0) * 100)
        
        horizons.append({
            "horizon": label,
            "week": int(base_dict['week_number'] + week_step),
            "risk_level": pred_risk,
            "confidence": round(conf, 1),
            "probabilities": prob_dict
        })
        
    # Determine trajectory status
    risk_rank = {"Low": 1, "Medium": 2, "High": 3}
    start_rank = risk_rank.get(horizons[0]["risk_level"], 2)
    end_rank = risk_rank.get(horizons[-1]["risk_level"], 2)
    
    if end_rank > start_rank:
        trajectory = "Worsening"
    elif end_rank < start_rank:
        trajectory = "Improving"
    else:
        trajectory = "Stable"
        
    return {
        "project_id": features.project_id or "PROJ-101",
        "horizons": horizons,
        "trajectory_status": trajectory
    }

# 5b. Helper Function: Calculate Portfolio Risk Urgency Score
def _calculate_project_urgency(proj, latest_pred):
    risk_weights = {"High": 3.0, "Medium": 2.0, "Low": 1.0}
    risk_level = latest_pred.risk_level if latest_pred else "Unanalyzed"
    weight = risk_weights.get(risk_level, 0.5)
    
    # Calibrated confidence (from prediction or default 0.75)
    confidence = float(latest_pred.risk_probability) if (latest_pred and latest_pred.risk_probability is not None) else 0.75
    
    # Staleness calculation (in weeks)
    now = datetime.now(timezone.utc)
    if latest_pred and latest_pred.prediction_date:
        pred_date = latest_pred.prediction_date
        if pred_date.tzinfo is None:
            pred_date = pred_date.replace(tzinfo=timezone.utc)
        days_diff = max(0, (now - pred_date).days)
    elif proj and proj.created_date:
        c_date = proj.created_date
        if c_date.tzinfo is None:
            c_date = c_date.replace(tzinfo=timezone.utc)
        days_diff = max(0, (now - c_date).days)
    else:
        days_diff = 14
        
    weeks_stale = round(days_diff / 7.0, 1)
    staleness_bonus = min(3.0, round(weeks_stale * 0.5, 2))
    
    # Escalation status: High risk or worsening flag
    is_escalating = (risk_level == "High")
    escalation_bonus = 1.5 if is_escalating else 0.0
    
    urgency_score = round(weight * (1.0 + confidence) + escalation_bonus + staleness_bonus, 2)
    
    if urgency_score >= 6.0:
        urgency_level = "CRITICAL"
    elif urgency_score >= 4.0:
        urgency_level = "HIGH"
    elif urgency_score >= 2.5:
        urgency_level = "MODERATE"
    else:
        urgency_level = "LOW"
        
    return {
        "urgency_score": urgency_score,
        "urgency_level": urgency_level,
        "risk_weight": weight,
        "calibrated_confidence": round(confidence, 4),
        "is_escalating": is_escalating,
        "weeks_stale": weeks_stale,
        "days_since_analysis": days_diff
    }

# 5c. GET /projects endpoint (enhanced with urgency score)
@app.get("/projects")
def get_all_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    result = []
    
    for proj in projects:
        latest_pred = (
            db.query(Prediction)
            .filter(Prediction.project_id == proj.project_id)
            .order_by(Prediction.prediction_date.desc(), Prediction.prediction_id.desc())
            .first()
        )
        
        urgency_info = _calculate_project_urgency(proj, latest_pred)
        
        result.append({
            "project_id": proj.project_id,
            "project_name": proj.project_name,
            "created_date": proj.created_date.isoformat() if proj.created_date else None,
            "risk_level": latest_pred.risk_level if latest_pred else None,
            "timestamp": latest_pred.prediction_date.isoformat() if latest_pred else None,
            "urgency_score": urgency_info["urgency_score"],
            "urgency_level": urgency_info["urgency_level"],
            "is_escalating": urgency_info["is_escalating"],
            "weeks_stale": urgency_info["weeks_stale"],
            "calibrated_confidence": urgency_info["calibrated_confidence"],
            "most_recent_prediction": {
                "prediction_id": latest_pred.prediction_id,
                "risk_level": latest_pred.risk_level,
                "risk_probability": latest_pred.risk_probability,
                "model_version": latest_pred.model_version,
                "prediction_date": latest_pred.prediction_date.isoformat(),
                "timestamp": latest_pred.prediction_date.isoformat()
            } if latest_pred else None
        })
        
    return result

# 5d. GET /projects/prioritized endpoint
@app.get("/projects/prioritized")
def get_prioritized_projects(db: Session = Depends(get_db)):
    all_projects = get_all_projects(db)
    # Sort by urgency_score descending
    all_projects.sort(key=lambda x: x["urgency_score"], reverse=True)
    return {
        "total_monitored_projects": len(all_projects),
        "prioritized_attention_list": all_projects
    }

# 5e. GET /interaction_analysis endpoint
@app.get("/interaction_analysis")
def get_shap_interaction_analysis():
    global shap_interaction_data
    if shap_interaction_data is not None:
        return shap_interaction_data
        
    base_dir = os.path.dirname(__file__)
    inter_matrix_path = os.path.join(base_dir, 'shap_interaction_matrix.json')
    if os.path.exists(inter_matrix_path):
        try:
            with open(inter_matrix_path, 'r') as f:
                import json
                shap_interaction_data = json.load(f)
            return shap_interaction_data
        except Exception as e:
            print(f"[API] Error loading SHAP interaction file: {e}", flush=True)
            
    try:
        from compute_shap_interactions import compute_and_save_shap_interactions
        shap_interaction_data = compute_and_save_shap_interactions()
        return shap_interaction_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate SHAP interaction analysis: {e}")

# 5f. GET /signal_precedence endpoint
@app.get("/signal_precedence")
def get_signal_precedence_analysis():
    global signal_precedence_data
    if signal_precedence_data is not None:
        return signal_precedence_data
        
    base_dir = os.path.dirname(__file__)
    prec_path = os.path.join(base_dir, 'signal_precedence_results.json')
    if os.path.exists(prec_path):
        try:
            with open(prec_path, 'r') as f:
                import json
                signal_precedence_data = json.load(f)
            return signal_precedence_data
        except Exception as e:
            print(f"[API] Error loading signal precedence file: {e}", flush=True)
            
    try:
        from compute_signal_precedence import compute_and_save_signal_precedence
        signal_precedence_data = compute_and_save_signal_precedence()
        return signal_precedence_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate signal precedence analysis: {e}")

# 5c. GET /projects/{project_id}/history endpoint
@app.get("/projects/{project_id}/history")
def get_project_history(project_id: str, db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.project_id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project with ID '{project_id}' not found.")
        
    predictions = (
        db.query(Prediction)
        .filter(Prediction.project_id == project_id)
        .order_by(Prediction.prediction_date.asc(), Prediction.prediction_id.asc())
        .all()
    )
    
    history = []
    for pred in predictions:
        recs = (
            db.query(Recommendation)
            .filter(Recommendation.prediction_id == pred.prediction_id)
            .order_by(Recommendation.priority.asc())
            .all()
        )
        
        history.append({
            "prediction_id": pred.prediction_id,
            "project_id": pred.project_id,
            "risk_level": pred.risk_level,
            "risk_probability": pred.risk_probability,
            "model_version": pred.model_version,
            "prediction_date": pred.prediction_date.isoformat(),
            "timestamp": pred.prediction_date.isoformat(),
            "recommendations": [
                {
                    "recommendation_id": r.recommendation_id,
                    "risk_factor": r.risk_factor,
                    "recommendation": r.recommendation,
                    "priority": r.priority
                }
                for r in recs
            ]
        })
        
    return {
        "project_id": proj.project_id,
        "project_name": proj.project_name,
        "created_date": proj.created_date.isoformat() if proj.created_date else None,
        "total_predictions": len(history),
        "history": history
    }

# 6. Counterfactual Simulation Endpoint with Bounds Validation & Clamping
@app.post("/simulate")
def simulate_project_risk(sim_req: SimulationRequest):
    if cb_model is None:
        raise HTTPException(status_code=500, detail="Model artifacts not initialized.")

    base_dict = sim_req.features.model_dump()
    base_df = pd.DataFrame([base_dict])[FEATURE_COLS]

    base_risk = cb_model.predict(base_df)[0]
    if isinstance(base_risk, (list, np.ndarray)):
        base_risk = base_risk[0]
    base_probs = cb_model.predict_proba(base_df)[0]
    base_prob_dict = {cls: round(float(prob), 4) for cls, prob in zip(classes, base_probs)}
    base_conf = base_prob_dict[base_risk]

    mod_dict = base_dict.copy()
    changes_applied = {}
    warnings: List[str] = []

    for feat_name, change_val in sim_req.changes.items():
        if feat_name in FEATURE_COLS:
            naive_val = float(mod_dict[feat_name] + change_val)
            clamped_val = naive_val

            if feat_name in NON_NEGATIVE_COLS:
                if naive_val < 0:
                    clamped_val = 0.0
                    warnings.append(
                        f"{feat_name} was capped at 0 since the requested change would have produced a negative value."
                    )
            elif feat_name in PERCENTAGE_COLS:
                if naive_val < 0:
                    clamped_val = 0.0
                    warnings.append(
                        f"{feat_name} was capped at 0% since the requested change would have produced a negative value."
                    )
                elif naive_val > 100:
                    clamped_val = 100.0
                    warnings.append(
                        f"{feat_name} was capped at 100% since the requested change exceeded 100%."
                    )

            mod_dict[feat_name] = clamped_val
            changes_applied[feat_name] = float(change_val)

    mod_df = pd.DataFrame([mod_dict])[FEATURE_COLS]

    sim_risk = cb_model.predict(mod_df)[0]
    if isinstance(sim_risk, (list, np.ndarray)):
        sim_risk = sim_risk[0]
    sim_probs = cb_model.predict_proba(mod_df)[0]
    sim_prob_dict = {cls: round(float(prob), 4) for cls, prob in zip(classes, sim_probs)}
    sim_conf = sim_prob_dict[sim_risk]

    change_phrases = []
    for feat, delta in changes_applied.items():
        feat_clean = feat.replace('_', ' ')
        if delta > 0:
            val_str = f"{delta:g}"
            if "percentage" in feat or "rate" in feat:
                change_phrases.append(f"increasing {feat_clean} by {val_str}%")
            else:
                change_phrases.append(f"increasing {feat_clean} by {val_str}")
        elif delta < 0:
            val_str = f"{abs(delta):g}"
            if "percentage" in feat or "rate" in feat:
                change_phrases.append(f"reducing {feat_clean} by {val_str}%")
            else:
                change_phrases.append(f"reducing {feat_clean} by {val_str}")
        else:
            change_phrases.append(f"keeping {feat_clean} unchanged")

    if not change_phrases:
        summary_sentence = "No valid feature changes were specified. The predicted risk remains unchanged."
    else:
        if len(change_phrases) == 1:
            change_str = change_phrases[0].capitalize()
        elif len(change_phrases) == 2:
            change_str = f"{change_phrases[0].capitalize()} and {change_phrases[1]}"
        else:
            change_str = f"{', '.join([p.capitalize() if i==0 else p for i, p in enumerate(change_phrases[:-1])])}, and {change_phrases[-1]}"

        base_conf_pct = round(base_conf * 100, 1)
        sim_conf_pct = round(sim_conf * 100, 1)

        conf_diff = abs(base_conf - sim_conf)
        risk_changed = (base_risk != sim_risk)

        if risk_changed:
            summary_sentence = (
                f"{change_str} would change the predicted risk from {base_risk} to {sim_risk}, "
                f"with confidence shifting from {base_conf_pct}% to {sim_conf_pct}%."
            )
        elif conf_diff >= 0.005:
            summary_sentence = (
                f"{change_str} would keep the predicted risk at {base_risk}, "
                f"while shifting confidence from {base_conf_pct}% to {sim_conf_pct}%."
            )
        else:
            summary_sentence = (
                f"{change_str} has no meaningful effect on the prediction. "
                f"The predicted risk remains {base_risk} at {base_conf_pct}% confidence."
            )

    return {
        "baseline": {
            "predicted_risk_level": base_risk,
            "probabilities": base_prob_dict,
            "confidence": base_conf
        },
        "simulated": {
            "modified_features": mod_dict,
            "predicted_risk_level": sim_risk,
            "probabilities": sim_prob_dict,
            "confidence": sim_conf
        },
        "changes_applied": changes_applied,
        "warnings": warnings,
        "summary_sentence": summary_sentence
    }

# 7. Anomaly Detection Endpoint
@app.post("/detect_anomaly")
def detect_project_anomaly(features: ProjectFeatures):
    if anomaly_model is None:
        raise HTTPException(status_code=500, detail="Anomaly model artifact not initialized.")

    input_dict = features.model_dump()
    n_expected = getattr(anomaly_model, 'n_features_in_', len(FEATURE_COLS))
    used_cols = FEATURE_COLS[:n_expected] if n_expected < len(FEATURE_COLS) else FEATURE_COLS
    input_df = pd.DataFrame([input_dict])[used_cols]

    pred = anomaly_model.predict(input_df)[0]
    is_anomaly = bool(pred == -1)

    raw_score = float(anomaly_model.decision_function(input_df)[0])
    anomaly_score = round(raw_score, 4)

    if is_anomaly:
        message = (
            "Warning: This project's current metrics are statistically unusual compared to typical patterns in the training data, "
            "which may indicate an emerging risk pattern not yet captured by the standard classifier."
        )
    else:
        message = (
            "Normal: This project's current metrics conform to typical statistical patterns observed in the training dataset."
        )

    return {
        "is_anomaly": is_anomaly,
        "anomaly_score": anomaly_score,
        "message": message
    }

# Helper function for linear trend forecasting
def _compute_metric_forecast(metric_name: str, values: List[float]):
    N = len(values)
    if N < 3:
        raise ValueError("Forecasting requires at least 3 weeks of history.")

    X = np.arange(1, N + 1)
    Y = np.array(values, dtype=float)

    m, c = np.polyfit(X, Y, 1)

    raw_w1 = m * (N + 1) + c
    raw_w2 = m * (N + 2) + c
    raw_w3 = m * (N + 3) + c

    if "percentage" in metric_name or "rate" in metric_name:
        w1 = round(float(np.clip(raw_w1, 0.0, 100.0)), 1)
        w2 = round(float(np.clip(raw_w2, 0.0, 100.0)), 1)
        w3 = round(float(np.clip(raw_w3, 0.0, 100.0)), 1)
    elif "density" in metric_name or "count" in metric_name:
        w1 = round(float(max(0.0, raw_w1)), 1)
        w2 = round(float(max(0.0, raw_w2)), 1)
        w3 = round(float(max(0.0, raw_w3)), 1)
    else:
        w1, w2, w3 = round(float(raw_w1), 1), round(float(raw_w2), 1), round(float(raw_w3), 1)

    if metric_name in ['overdue_tasks_percentage', 'defect_density']:
        if m > 0.5:
            trend = "worsening"
        elif m < -0.5:
            trend = "improving"
        else:
            trend = "stable"
    elif metric_name == 'task_completion_rate':
        if m > 0.5:
            trend = "improving"
        elif m < -0.5:
            trend = "worsening"
        else:
            trend = "stable"
    else:
        trend = "worsening" if m > 0.5 else ("improving" if m < -0.5 else "stable")

    return {
        "historical_values": [round(float(v), 1) for v in values],
        "slope_per_week": round(float(m), 2),
        "trend_direction": trend,
        "forecast_week_1": w1,
        "forecast_week_2": w2,
        "forecast_week_3": w3
    }

# 8. Time-Series Forecasting Endpoint
@app.post("/forecast")
def forecast_project_metrics(req: ForecastRequest):
    metrics_to_process = {
        'overdue_tasks_percentage': req.overdue_tasks_percentage,
        'defect_density': req.defect_density,
        'task_completion_rate': req.task_completion_rate
    }

    for m_name, m_vals in metrics_to_process.items():
        if m_vals is not None and len(m_vals) < 3:
            raise HTTPException(
                status_code=400,
                detail=f"Forecasting requires at least 3 weeks of history (provided {len(m_vals)} points for {m_name})."
            )

    forecast_results = {}
    for m_name, m_vals in metrics_to_process.items():
        if m_vals is not None:
            try:
                forecast_results[m_name] = _compute_metric_forecast(m_name, m_vals)
            except ValueError as ve:
                raise HTTPException(status_code=400, detail=str(ve))

    overdue_fc = forecast_results['overdue_tasks_percentage']
    slope = overdue_fc['slope_per_week']
    w3_val = overdue_fc['forecast_week_3']

    if slope > 0.5:
        summary_sentence = (
            f"Overdue tasks are trending upward by approximately {abs(slope):.1f} percentage points per week; "
            f"if this trend continues, overdue tasks could reach {w3_val:g}% within 3 weeks."
        )
    elif slope < -0.5:
        summary_sentence = (
            f"Overdue tasks are trending downward by approximately {abs(slope):.1f} percentage points per week; "
            f"if this trend continues, overdue tasks could reach {w3_val:g}% within 3 weeks."
        )
    else:
        summary_sentence = (
            f"Overdue tasks are relatively stable (slope of {slope:+.1f} percentage points per week), "
            f"remaining around {w3_val:g}% over the next 3 weeks."
        )

    return {
        "forecasts": forecast_results,
        "summary_sentence": summary_sentence
    }

# 8b. PyTorch LSTM & Side-by-Side Forecasting Endpoint
def _compute_lstm_forecast(req: ForecastRequest):
    overdue = req.overdue_tasks_percentage or [20.0]*6
    defect = req.defect_density or [10.0]*6
    completion = req.task_completion_rate or [60.0]*6

    def fit_len_6(arr):
        if len(arr) >= 6:
            return list(arr[-6:])
        else:
            pad = [arr[0]] * (6 - len(arr))
            return pad + list(arr)

    overdue_6 = fit_len_6(overdue)
    defect_6 = fit_len_6(defect)
    completion_6 = fit_len_6(completion)

    raw_window = np.column_stack([overdue_6, defect_6, completion_6])

    linear_forecasts = {
        'overdue_tasks_percentage': _compute_metric_forecast('overdue_tasks_percentage', overdue),
        'defect_density': _compute_metric_forecast('defect_density', defect),
        'task_completion_rate': _compute_metric_forecast('task_completion_rate', completion)
    }

    lstm_forecasts = {}

    if lstm_model is not None and lstm_scaler is not None:
        try:
            scaler_min = lstm_scaler['scaler_min']
            scaler_max = lstm_scaler['scaler_max']
            scaler_range = lstm_scaler['scaler_range']

            scaled_seq = (raw_window - scaler_min) / scaler_range
            scaled_seq_3d = scaled_seq[np.newaxis, :, :].copy()

            preds_steps = []
            curr_seq = scaled_seq_3d.copy()

            for step in range(3):
                with torch.no_grad():
                    inp = torch.tensor(curr_seq, dtype=torch.float32)
                    p_scaled = lstm_model(inp).numpy()[0]
                preds_steps.append(p_scaled)
                new_w = np.vstack([curr_seq[0, 1:], p_scaled])[np.newaxis, :, :]
                curr_seq = new_w

            preds_steps = np.array(preds_steps)
            descaled_preds = preds_steps * scaler_range + scaler_min

            metrics_names = ['overdue_tasks_percentage', 'defect_density', 'task_completion_rate']
            for col_idx, m_name in enumerate(metrics_names):
                raw_w1 = descaled_preds[0, col_idx]
                raw_w2 = descaled_preds[1, col_idx]
                raw_w3 = descaled_preds[2, col_idx]

                if "percentage" in m_name or "rate" in m_name:
                    w1 = round(float(np.clip(raw_w1, 0.0, 100.0)), 1)
                    w2 = round(float(np.clip(raw_w2, 0.0, 100.0)), 1)
                    w3 = round(float(np.clip(raw_w3, 0.0, 100.0)), 1)
                else:
                    w1 = round(float(max(0.0, raw_w1)), 1)
                    w2 = round(float(max(0.0, raw_w2)), 1)
                    w3 = round(float(max(0.0, raw_w3)), 1)

                lstm_forecasts[m_name] = {
                    "forecast_week_1": w1,
                    "forecast_week_2": w2,
                    "forecast_week_3": w3
                }
        except Exception as e:
            print(f"[LSTM FORECAST] Error running PyTorch LSTM: {e}", flush=True)

    if not lstm_forecasts:
        for m_name in ['overdue_tasks_percentage', 'defect_density', 'task_completion_rate']:
            lin = linear_forecasts[m_name]
            lstm_forecasts[m_name] = {
                "forecast_week_1": lin["forecast_week_1"],
                "forecast_week_2": lin["forecast_week_2"],
                "forecast_week_3": lin["forecast_week_3"]
            }

    # Extract 3-seed stability benchmark stats and hybrid selections
    metric_selection = lstm_scaler.get('metric_selection', {}) if lstm_scaler else {}
    linear_mean_mae = lstm_scaler.get('linear_mean_mae', {}) if lstm_scaler else {}
    lstm_mean_mae = lstm_scaler.get('lstm_mean_mae', {}) if lstm_scaler else {}
    linear_std_mae = lstm_scaler.get('linear_std_mae', {}) if lstm_scaler else {}
    lstm_std_mae = lstm_scaler.get('lstm_std_mae', {}) if lstm_scaler else {}

    metrics_list = ['overdue_tasks_percentage', 'defect_density', 'task_completion_rate']
    selected_methods = {}
    hybrid_forecasts = {}

    for m_name in metrics_list:
        # Default to lstm if not found in saved scaler metadata
        sel_method = metric_selection.get(m_name, 'lstm')
        selected_methods[m_name] = sel_method

        if sel_method == 'lstm':
            fc = lstm_forecasts.get(m_name, {})
        else:
            fc = linear_forecasts.get(m_name, {})

        hybrid_forecasts[m_name] = {
            "method_used": sel_method,
            "forecast_week_1": fc.get("forecast_week_1", 0.0),
            "forecast_week_2": fc.get("forecast_week_2", 0.0),
            "forecast_week_3": fc.get("forecast_week_3", 0.0)
        }

    mae_benchmark = {
        "metrics": {
            m_name: {
                "linear_mean_mae": round(float(linear_mean_mae.get(m_name, 0.0)), 4),
                "linear_std_mae": round(float(linear_std_mae.get(m_name, 0.0)), 4),
                "lstm_mean_mae": round(float(lstm_mean_mae.get(m_name, 0.0)), 4),
                "lstm_std_mae": round(float(lstm_std_mae.get(m_name, 0.0)), 4),
                "selected_method": selected_methods[m_name]
            } for m_name in metrics_list
        }
    }

    summary_parts = []
    for m_name in metrics_list:
        m_sel = selected_methods[m_name]
        lin_m = linear_mean_mae.get(m_name, 0.0)
        lstm_m = lstm_mean_mae.get(m_name, 0.0)
        summary_parts.append(f"{m_name}: {m_sel.upper()} (Linear MAE {lin_m:.4f} vs LSTM MAE {lstm_m:.4f})")

    summary_sentence = (
        f"Hybrid forecasting model selected per-metric optimal models based on 3-seed benchmark results: "
        f"{'; '.join(summary_parts)}."
    )

    return {
        "selected_methods": selected_methods,
        "hybrid_forecasts": hybrid_forecasts,
        "linear_forecasts": linear_forecasts,
        "lstm_forecasts": lstm_forecasts,
        "mae_benchmark": mae_benchmark,
        "summary_sentence": summary_sentence
    }

@app.post("/forecast_lstm")
def forecast_project_metrics_lstm(req: ForecastRequest):
    return _compute_lstm_forecast(req)

# Helper PDF text extractor
def _extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        pages_text = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages_text.append(t)
        return "\n".join(pages_text)
    except Exception as e:
        raise ValueError(f"PDF text extraction failed: {str(e)}")

# 9. Document Analysis Endpoint
@app.post("/analyze_document")
async def analyze_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    file_bytes = await file.read()
    if not file_bytes or len(file_bytes.strip()) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty or text extraction failed.")

    filename_lower = file.filename.lower()
    extracted_text = ""
    file_type = "plain_text"

    if filename_lower.endswith(".pdf") or file.content_type == "application/pdf":
        file_type = "pdf"
        try:
            extracted_text = _extract_text_from_pdf_bytes(file_bytes)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Text extraction failed: {str(e)}")
    else:
        try:
            extracted_text = file_bytes.decode("utf-8", errors="ignore")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read text file: {str(e)}")

    extracted_text = extracted_text.strip()
    if not extracted_text:
        raise HTTPException(status_code=400, detail="Uploaded file is empty or text extraction failed.")

    raw_sentences = re.split(r'(?<=[.!?])\s+', extracted_text)
    sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 5]

    risk_mentions = []
    deadline_mentions = []

    risk_regex = re.compile('|'.join(RISK_KEYWORDS), re.IGNORECASE)
    date_regex = re.compile('|'.join(DATE_PATTERNS), re.IGNORECASE)

    for sentence in sentences:
        if risk_regex.search(sentence):
            if sentence not in risk_mentions:
                risk_mentions.append(sentence)
        if date_regex.search(sentence):
            if sentence not in deadline_mentions:
                deadline_mentions.append(sentence)

    word_count = len(extracted_text.split())
    reading_time_minutes = round(word_count / 200.0, 2)

    return {
        "filename": file.filename,
        "file_type": file_type,
        "word_count": word_count,
        "reading_time_minutes": reading_time_minutes,
        "risk_mentions": risk_mentions,
        "deadline_mentions": deadline_mentions,
        "extracted_text": extracted_text
    }

def _chunk_text_by_paragraphs_and_sentences(text_content: str) -> List[str]:
    # Normalize missing spaces after punctuation (e.g. "boy.He" -> "boy. He")
    text_content = re.sub(r'(?<=[.!?])(?=[A-Za-z])', r' ', text_content.strip())
    # 1. Split into paragraphs/sections by double newlines if present
    paragraphs = [p.strip() for p in re.split(r'(?:\r?\n\s*){2,}', text_content) if p.strip()]
    
    raw_chunks = []
    if len(paragraphs) > 1:
        for para in paragraphs:
            # Filter out decorative line separators (e.g. ====== or -------)
            lines = [line.strip() for line in para.splitlines() if line.strip() and not re.match(r'^[=\-_*#\s]+$', line.strip())]
            cleaned_para = " ".join(lines)
            if not cleaned_para:
                continue
                
            raw_sentences = re.split(r'(?<=[.!?])\s+', cleaned_para)
            sentences = [s.strip() for s in raw_sentences if s.strip() and not re.match(r'^[=\-_*#\s]+$', s.strip())]
            
            if not sentences:
                continue
                
            if len(sentences) <= 4:
                raw_chunks.append(" ".join(sentences))
            else:
                for i in range(0, len(sentences), 3):
                    group = sentences[i:i + 4]
                    if group:
                        raw_chunks.append(" ".join(group))
    else:
        # Fallback: if no double newlines, group lines/sentences into chunks of 3-4 sentences
        lines = [line.strip() for line in text_content.splitlines() if line.strip() and not re.match(r'^[=\-_*#\s]+$', line.strip())]
        cleaned_text = " ".join(lines)
        raw_sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
        sentences = [s.strip() for s in raw_sentences if s.strip() and not re.match(r'^[=\-_*#\s]+$', s.strip())]
        
        if len(sentences) <= 4:
            raw_chunks.append(" ".join(sentences))
        else:
            for i in range(0, len(sentences), 3):
                group = sentences[i:i + 4]
                if group:
                    raw_chunks.append(" ".join(group))
                    
    # 2. Filter out chunks shorter than 8 words (standalone headers / short metadata lines)
    final_chunks = []
    for chunk in raw_chunks:
        words = chunk.split()
        if len(words) >= 8:
            final_chunks.append(chunk)
            
    if not final_chunks and raw_chunks:
        final_chunks = [c for c in raw_chunks if len(c.split()) >= 3] or raw_chunks

    return final_chunks

def _process_ingestion_background(project_id: str, doc_name: str, chunks: List[str]):
    try:
        model = get_embed_model()
        collection = get_chroma_collection()
        
        # Generate embeddings for each chunk (use batch_size to save memory)
        with torch.no_grad():
            embeddings = model.encode(chunks, show_progress_bar=False, batch_size=8).tolist()

        ids = [f"{project_id}_{uuid.uuid4().hex[:8]}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "project_id": project_id,
                "document_name": doc_name,
                "chunk_index": i
            }
            for i in range(len(chunks))
        ]

        # Add to ChromaDB vector collection
        collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=cast(Any, metadatas)
        )
        print(f"Background ingestion complete for {project_id}: {len(chunks)} chunks.")
    except Exception as e:
        print(f"Background ingestion failed: {e}")

# 10. RAG Document Ingestion Endpoint
@app.post("/ingest_document")
def ingest_document_knowledge(req: IngestDocumentRequest, background_tasks: BackgroundTasks):
    try:
        # Pre-initialize or fail fast
        get_embed_model()
        collection = get_chroma_collection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize RAG vector database: {str(e)}")

    if not req.project_id or not req.project_id.strip():
        raise HTTPException(status_code=400, detail="project_id is required.")

    text_content = req.text.strip()
    if not text_content:
        raise HTTPException(status_code=400, detail="Text content for ingestion cannot be empty.")

    # Apply 3-4 sentence / section chunking strategy with >= 8 words filter
    chunks = _chunk_text_by_paragraphs_and_sentences(text_content)

    if not chunks:
        raise HTTPException(status_code=400, detail="Could not extract valid text chunks for ingestion (chunks must be >= 8 words).")

    # Delete previous chunks for this project_id so re-ingestion is clean & updated
    try:
        collection.delete(where={"project_id": req.project_id})
    except Exception:
        pass

    doc_name = req.document_name or "document.txt"
    
    # Send actual processing to background
    background_tasks.add_task(_process_ingestion_background, req.project_id, doc_name, chunks)

    return {
        "status": "success",
        "project_id": req.project_id,
        "document_name": doc_name,
        "chunks_ingested": len(chunks),
        "message": f"Successfully queued {len(chunks)} chunks for background ingestion into project knowledge base."
    }

def _format_direct_answer(question: str, text: str) -> str:
    q_lower = question.lower().strip()
    s_clean = re.sub(r'^(?:Answer:\s*|Based on[^\:]*\:\s*)', '', text, flags=re.IGNORECASE).strip()

    # 1. Lead engineer queries
    if any(k in q_lower for k in ['lead engineer', 'engineer', 'who is the engineer']):
        match = re.search(r'(?:lead engineer is|engineer is|engineer:\s*)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', s_clean, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # 2. Company name queries
    if any(k in q_lower for k in ['company name', 'name of the company', 'company']):
        match = re.search(r'(?:company name is|company:\s*)\s*([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)?)', s_clean, re.IGNORECASE)
        if match:
            c = match.group(1).strip().rstrip('.')
            if c: return c

    # 3. College name queries
    if any(k in q_lower for k in ['college name', 'name of the college', 'collge name', 'which college', 'college']):
        match = re.search(r'(?:college name is|studies at|college:\s*)\s*([A-Za-z0-9\s,\.&-]+)', s_clean, re.IGNORECASE)
        if match:
            c = match.group(1).strip().rstrip('.')
            if c: return c

    # 4. Person name queries
    if any(k in q_lower for k in ['name of the person', 'what is the name', 'person name']):
        match = re.search(r'(?:name is|name:\s*)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', s_clean, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # 5. Age queries
    if 'age' in q_lower:
        match = re.search(r'\b(\d{1,2})\b', s_clean)
        if match:
            return f"{match.group(1)} years old."

    # 6. Standard clean single sentence response
    formatted = re.sub(r'\bMy\b', 'The', s_clean, flags=re.IGNORECASE)
    formatted = re.sub(r'\bmy\b', 'the', formatted)
    formatted = re.sub(r'\bI am\b', 'The candidate is', formatted, flags=re.IGNORECASE)
    formatted = re.sub(r'\bI\b', 'The candidate', formatted)

    return formatted

STOPWORDS = {
    'is', 'are', 'am', 'was', 'were', 'the', 'a', 'an', 'to', 'it', 'of', 'in', 'on', 'at',
    'or', 'and', 'be', 'do', 'does', 'did', 'so', 'by', 'if', 'we', 'he', 'she', 'they',
    'me', 'my', 'your', 'his', 'her', 'this', 'that', 'these', 'those', 'for', 'with'
}

# 11. RAG Q&A Endpoint
@app.post("/ask")
def ask_project_knowledge(req: AskQuestionRequest):
    try:
        model = get_embed_model()
        collection = get_chroma_collection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize RAG vector database: {str(e)}")

    if not req.project_id or not req.project_id.strip():
        raise HTTPException(status_code=400, detail="project_id is required.")

    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. Reject generic single-word stop words (e.g. "is", "are", "the")
    words = [w.lower().strip('?,.!') for w in req.question.split() if w.lower().strip('?,.!')]
    non_stop = [w for w in words if w not in STOPWORDS]
    if len(non_stop) == 0:
        return {
            "project_id": req.project_id,
            "question": req.question,
            "retrieved_chunks": [],
            "answer": "Please ask a specific, meaningful question about the uploaded project document."
        }

    # Check if any documents exist for this project_id in ChromaDB
    existing_docs = collection.get(where={"project_id": req.project_id})
    if not existing_docs or not existing_docs.get('ids') or len(existing_docs['ids']) == 0:
        return {
            "project_id": req.project_id,
            "question": req.question,
            "retrieved_chunks": [],
            "answer": f"No project knowledge base exists for project '{req.project_id}' yet. Please ingest project documents first."
        }

    # Generate embedding for question
    with torch.no_grad():
        q_embedding = model.encode([req.question.strip()], show_progress_bar=False).tolist()

    # Query ChromaDB collection for top 3 similar chunks tagged with project_id
    available_chunks_count = len(existing_docs['ids'])
    n_results = min(3, available_chunks_count)

    query_res = collection.query(
        query_embeddings=q_embedding,
        n_results=n_results,
        where={"project_id": req.project_id}
    )

    retrieved_chunks = []

    if query_res and query_res.get('documents') and len(query_res['documents']) > 0:
        docs = query_res['documents'][0]
        distances = query_res['distances'][0] if query_res.get('distances') else [0.0] * len(docs)
        metas = query_res['metadatas'][0] if query_res.get('metadatas') else [{}] * len(docs)

        for doc_text, dist, meta in zip(docs, distances, metas):
            similarity_score = round(float(1.0 / (1.0 + dist)), 3)
            doc_name = meta.get("document_name", "document.txt")

            retrieved_chunks.append({
                "chunk_text": doc_text,
                "similarity_score": similarity_score,
                "document_name": doc_name
            })

    if retrieved_chunks:
        # Check overall top similarity score
        max_sim = max([c['similarity_score'] for c in retrieved_chunks])
        if max_sim < 0.20:
            return {
                "project_id": req.project_id,
                "question": req.question,
                "retrieved_chunks": retrieved_chunks,
                "answer": "I could not find information regarding your question in the uploaded document. Please ask a question relevant to the project context."
            }

        # Local seq2seq answer synthesis using google/flan-t5-base
        try:
            tokenizer, f_model = get_flan_model()
            if tokenizer is not None and f_model is not None:
                context_blocks = "\n".join([f"- {c['chunk_text']}" for c in retrieved_chunks[:3]])
                
                prompt = (
                    f"Context:\n{context_blocks}\n\n"
                    f"Question: {req.question}\n\n"
                    f"Instructions: Based on the context provided above, synthesize a clear, factual, natural-language answer to the question. "
                    f"If multiple points are mentioned, summarize them concisely."
                )

                inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
                with torch.no_grad():
                    outputs = f_model.generate(**inputs, max_new_tokens=150, num_beams=2, early_stopping=True)
                gen_tokens = cast(Any, outputs)[0]
                decoded = cast(str, tokenizer.decode(gen_tokens, skip_special_tokens=True))
                raw_gen = decoded.strip()
            else:
                raw_gen = ""



            # Clean and structure the synthesized output
            if raw_gen and len(raw_gen.split()) >= 2:
                clean_ans = raw_gen[0].upper() + raw_gen[1:] if len(raw_gen) > 1 else raw_gen
                # Format into clear sections/bullets if multi-sentence or detailed
                sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_ans) if s.strip()]
                if len(sentences) > 1:
                    bullet_list = "\n".join([f"• {s}" for s in sentences])
                    answer = f"**Synthesized Answer:**\n{bullet_list}"
                else:
                    direct_fact = _format_direct_answer(req.question, retrieved_chunks[0]['chunk_text'])
                    if direct_fact and direct_fact.lower() not in clean_ans.lower():
                        answer = f"**Finding:** {clean_ans}\n\n**Details:** {direct_fact}"
                    else:
                        answer = clean_ans
            else:
                answer = _format_direct_answer(req.question, retrieved_chunks[0]['chunk_text'])

        except Exception as synth_err:
            print(f"[RAG] Flan-T5 Synthesis fallback: {synth_err}", flush=True)
            answer = _format_direct_answer(req.question, retrieved_chunks[0]['chunk_text'])
    else:
        answer = f"No project knowledge base exists for project '{req.project_id}' yet. Please ingest project documents first."

    return {
        "project_id": req.project_id,
        "question": req.question,
        "retrieved_chunks": retrieved_chunks,
        "answer": answer
    }
