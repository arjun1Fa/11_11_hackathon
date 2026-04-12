import requests
import json

url = 'https://yoirzyoeshlyqxilpygm.supabase.co/rest/v1/'
key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvaXJ6eW9lc2hseXF4aWxweWdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU5MDg0ODksImV4cCI6MjA5MTQ4NDQ4OX0.YVsvtMx4dAIl3PhHLa6MOI1qMmhpXq-XeMuwKLMJOQM'
headers = {'apikey': key, 'Authorization': f'Bearer {key}', 'Prefer': 'count=exact'}

tables = ['customers', 'packages', 'conversations', 'enquiry_events', 'handoff_queue', 'knowledge_base']
for table in tables:
    r = requests.get(url + table + '?select=id&limit=0', headers=headers)
    count = r.headers.get('Content-Range', '?')
    print(f'{table:20s} → {r.status_code}  rows: {count}')
