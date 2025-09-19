from fastapi import FastAPI
import joblib
from pydantic import BaseModel
from supabase import create_client, Client
from sklearn.ensemble import RandomForestClassifier
import numpy as np
from sklearn.metrics import accuracy_score
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load trained model
model = joblib.load("dropout_model.pkl")

# Supabase credentials
url = "https://sphrjnrndnreelyvjkar.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNwaHJqbnJuZG5yZWVseXZqa2FyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcwODYwMzEsImV4cCI6MjA3MjY2MjAzMX0.TgXltOAC6iKdvzmkloYaD6MSukBOG-y2SXqdbevSShs"
supabase: Client = create_client(url, key)

# Define input format
class StudentData(BaseModel):
    attendance: int
    scores: int
    fees_pending: int
    backlogs: int

# Create FastAPI app
app = FastAPI(title="Student Dropout Prediction API")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/predict-risk")
def predict_risk(student: StudentData):
    features = [[
        student.attendance,
        student.scores,
        student.fees_pending,
        student.backlogs
    ]]
    prediction = model.predict(features)[0]
    return {"dropout_risk": "At Risk" if prediction == 1 else "Safe"}

@app.get("/predict-from-db/{student_id}")
def predict_from_db(student_id: int):
    # 1. Attendance %
    attendance = supabase.from_("attendance").select("status").eq("student_id", student_id).execute()
    records = attendance.data
    if not records:
        return {"student_id": student_id, "risk": "No Data"}

    total_days = len(records)
    present_days = sum(1 for r in records if r["status"] == "Present")
    attendance_pct = (present_days / total_days) * 100

    # 2. Average score
    scores = supabase.from_("scores").select("marks").eq("student_id", student_id).execute()
    scores_data = scores.data
    avg_score = sum(s["marks"] for s in scores_data) / len(scores_data) if scores_data else 0

    # 3. Fees pending (convert to numeric for ML model)
    fees = supabase.from_("fees").select("amount_due").eq("student_id", student_id).execute()
    fees_data = fees.data
    fees_pending = 1 if any(f["amount_due"] > 0 for f in fees_data) else 0

    # 4. Backlogs (count subjects with <40 marks)
    backlogs = sum(1 for s in scores_data if s["marks"] < 40)

    # 🔥 Use ML model
    features = [[attendance_pct, avg_score, fees_pending, backlogs]]
    prediction = model.predict(features)[0]

    risk = "At Risk" if prediction == 1 else "Safe"

    return {
        "student_id": student_id,
        "attendance_pct": attendance_pct,
        "avg_score": avg_score,
        "fees_pending": fees_pending,
        "backlogs": backlogs,
        "risk": risk
    }



# 🔥 New retrain endpoint
@app.post("/retrain")
def retrain_model():
    global model

    # 1. Get all unique student_ids
    students = supabase.from_("students").select("id").execute()
    if not students.data:
        return {"message": "No students found to train on."}

    X, y = [], []

    for student in students.data:
        sid = student["id"]

        # Attendance
        attendance = supabase.from_("attendance").select("status").eq("student_id", sid).execute()
        records = attendance.data
        if not records:
            continue
        total_days = len(records)
        present_days = sum(1 for r in records if r["status"] == "Present")
        attendance_pct = (present_days / total_days) * 100

        # Scores
        scores = supabase.from_("scores").select("marks").eq("student_id", sid).execute()
        scores_data = scores.data
        avg_score = sum(s["marks"] for s in scores_data) / len(scores_data) if scores_data else 0

        # Fees
        fees = supabase.from_("fees").select("amount_due").eq("student_id", sid).execute()
        fees_data = fees.data
        fees_pending = 1 if any(f["amount_due"] > 0 for f in fees_data) else 0

        # Backlogs
        backlogs = sum(1 for s in scores_data if s["marks"] < 40)

        # Label (ground truth) - assume "dropouts" table has status=1 for at risk
        label_data = supabase.from_("dropouts").select("status").eq("student_id", sid).execute()
        if not label_data.data:
            continue
        label = label_data.data[0]["status"]  # 1 = At Risk, 0 = Safe

        # Append training data
        X.append([attendance_pct, avg_score, fees_pending, backlogs])
        y.append(label)

    if not X:
        return {"message": "Not enough data to retrain."}

    # 2. Train model
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X, y)

    # 3. Evaluate accuracy
    y_pred = clf.predict(X)
    acc = accuracy_score(y, y_pred)

    # 4. Save & reload model
    joblib.dump(clf, "dropout_model.pkl")
    model = clf

    return {
        "message": "Model retrained successfully",
        "samples": len(X),
        "accuracy": round(acc, 2)
    }


