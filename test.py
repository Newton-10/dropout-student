# test.py
from supabase import create_client, Client

url = "https://sphrjnrndnreelyvjkar.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNwaHJqbnJuZG5yZWVseXZqa2FyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcwODYwMzEsImV4cCI6MjA3MjY2MjAzMX0.TgXltOAC6iKdvzmkloYaD6MSukBOG-y2SXqdbevSShs"
supabase: Client = create_client(url, key)

response = supabase.from_("students").select("*").limit(1).execute()
print(response)
