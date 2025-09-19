from supabase import create_client, Client
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

# --- Supabase connection ---
url = "https://sphrjnrndnreelyvjkar.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNwaHJqbnJuZG5yZWVseXZqa2FyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcwODYwMzEsImV4cCI6MjA3MjY2MjAzMX0.TgXltOAC6iKdvzmkloYaD6MSukBOG-y2SXqdbevSShs"
supabase: Client = create_client(url, key)

# --- Fetch data from Supabase ---
students = supabase.from_("students").select("id, dropout").execute().data
all_features = []

for s in students:
    student_id = s["id"]

    # Attendance %
    attendance = supabase.from_("attendance").select("status").eq("student_id", student_id).execute().data
    total_days = len(attendance)
    present_days = sum(1 for r in attendance if r["status"] == "Present")
    attendance_pct = (present_days / total_days) * 100 if total_days > 0 else 0

    # Average score
    scores = supabase.from_("scores").select("marks").eq("student_id", student_id).execute().data
    avg_score = sum(sc["marks"] for sc in scores) / len(scores) if scores else 0

    # Fees pending (numeric)
    fees = supabase.from_("fees").select("amount_due").eq("student_id", student_id).execute().data
    fees_pending = 1 if any(f["amount_due"] > 0 for f in fees) else 0

    # Backlogs (<40 marks subjects)
    backlogs = sum(1 for sc in scores if sc["marks"] < 40)

    # 🟢 Use real label from DB (instead of synthetic rules)
    dropout = s.get("dropout", 0)  # default to 0 if not set

    # Collect features + label
    all_features.append([attendance_pct, avg_score, fees_pending, backlogs, dropout])

# --- Convert to DataFrame ---
df = pd.DataFrame(all_features, columns=["attendance", "avg_score", "fees_pending", "backlogs", "dropout"])

# --- Train-test split ---
X = df[["attendance", "avg_score", "fees_pending", "backlogs"]]
y = df["dropout"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# --- Train model ---
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# --- Evaluate ---
y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))
print("Sample data being used for training:")
print(df.head(10))
print("Class distribution:", df["dropout"].value_counts())

# --- Save model ---
joblib.dump(model, "dropout_model.pkl")
print("✅ Model retrained and saved as dropout_model.pkl")
