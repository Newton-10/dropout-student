import random
from datetime import datetime, timedelta
from supabase import create_client

# --- Supabase connection ---
url = "https://sphrjnrndnreelyvjkar.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNwaHJqbnJuZG5yZWVseXZqa2FyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcwODYwMzEsImV4cCI6MjA3MjY2MjAzMX0.TgXltOAC6iKdvzmkloYaD6MSukBOG-y2SXqdbevSShs"
supabase = create_client(url, key)

# Subjects for scores
subjects = ["Math", "Physics", "Chemistry", "CS"]

# Term for fees
term = "2025-Sem1"

# --- Generate 100 students ---
for i in range(1, 101):
    # Generate student info
    name = f"Student {i}"
    email = f"student{i}@college.edu"
    phone = f"9000000{i:03d}"
    mentor_id = random.choice([1, 2])

    # Features for dropout logic
    attendance_pct = random.randint(20, 100)
    avg_score = random.randint(20, 95)
    fees_pending_flag = random.choice([0, 1])
    backlogs = random.randint(0, 5)

    # Dropout label
    dropout = 1 if (attendance_pct < 60 or avg_score < 40 or fees_pending_flag == 1) else 0

    # Insert into students table
    student_insert = supabase.table("students").insert({
        "name": name,
        "email": email,
        "phone": phone,
        "mentor_id": mentor_id,
        "dropout": dropout
    }).execute()

    student_id = student_insert.data[0]["id"]  # Get new student ID

    # --- Attendance (last 30 days) ---
    start_date = datetime(2025, 8, 1)
    for d in range(30):
        date = start_date + timedelta(days=d)
        status = "Present" if random.randint(1, 100) <= attendance_pct else "Absent"
        supabase.table("attendance").insert({
            "student_id": student_id,
            "date": date.strftime("%Y-%m-%d"),
            "status": status
        }).execute()

    # --- Scores ---
    for subj in subjects:
        marks = random.randint(20, 95)
        supabase.table("scores").insert({
            "student_id": student_id,
            "subject": subj,
            "marks": marks,
            "exam_date": "2025-08-10"
        }).execute()

    # --- Fees ---
    amount_due = random.choice([0, 1000, 2000]) if fees_pending_flag else 0
    status = "Paid" if amount_due == 0 else "Unpaid"
    supabase.table("fees").insert({
        "student_id": student_id,
        "term": term,
        "amount_due": amount_due,
        "status": status
    }).execute()

print("✅ 100 students + attendance + scores + fees inserted into Supabase!")
