import gspread
import os
import json
import sys
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GOOGLE_SHEET_ID, GOOGLE_SERVICE_ACCOUNT_FILE
from database import LocalDB

load_dotenv()

def migrate_sheets():
    print("Migrating Google Sheets...")
    creds_path = os.path.join(os.path.dirname(__file__), GOOGLE_SERVICE_ACCOUNT_FILE)
    creds = Credentials.from_service_account_file(creds_path, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    client = gspread.authorize(creds)
    db = client.open_by_key(GOOGLE_SHEET_ID)
    
    try:
        sheet = db.worksheet("Companies")
        headers = sheet.row_values(1)
        if "campaign" not in headers:
            # Add to end
            col_index = len(headers) + 1
            sheet.update_cell(1, col_index, "campaign")
            # Fill existing with 'Default'
            records = sheet.get_all_records()
            for i, r in enumerate(records):
                sheet.update_cell(i + 2, col_index, "Default")
            print("Added 'campaign' column to Sheets.")
        else:
            print("'campaign' column already exists in Sheets.")
    except Exception as e:
        print(f"Error migrating sheets: {e}")

def migrate_local():
    print("Migrating Local JSON...")
    db = LocalDB()
    updated = False
    for c in db.data.get("Companies", []):
        if "campaign" not in c:
            c["campaign"] = "Default"
            updated = True
    if updated:
        db._save()
        print("Added 'campaign' to Local JSON.")
    else:
        print("'campaign' already exists or no companies in Local JSON.")

if __name__ == "__main__":
    migrate_sheets()
    migrate_local()
