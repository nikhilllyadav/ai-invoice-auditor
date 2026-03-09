import os
import json
from rich import print
REPORTS_DIR = os.path.join("data", "reports")

def load_reports():
    reports = []
    if os.path.exists(REPORTS_DIR):
        files = sorted([f for f in os.listdir(REPORTS_DIR) if f.endswith(".json")])
        for file in files:
            try:
                with open(os.path.join(REPORTS_DIR, file)) as f:
                    data = json.load(f)
                    data["_filename"] = file 
                    reports.append(data)
            except: continue
    return reports

reports = load_reports()
print(reports)
