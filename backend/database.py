"""
Database Layer with Google Sheets & Local Fallback
Prioritizes Google Sheets if configured, otherwise falls back to a local JSON file.
Maintains a consistent functional API for the application.
"""

import gspread
import json
import os
from datetime import datetime, timezone
from google.oauth2.service_account import Credentials
from config import GOOGLE_SHEET_ID, GOOGLE_SERVICE_ACCOUNT_FILE

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# ── Google Sheets Implementation ──────────────────────────────────────
class GoogleSheetsDB:
    def __init__(self, sheet_id, creds_file, creds_json=None):
        self.sheet_id = sheet_id
        if creds_json:
            # Use raw JSON from env var
            try:
                info = json.loads(creds_json)
                self.creds = Credentials.from_service_account_info(info, scopes=SCOPES)
            except Exception as e:
                print(f"❌ Failed to load GOOGLE_SERVICE_ACCOUNT_JSON: {e}")
                raise e
        else:
            # Fallback to local file
            creds_path = os.path.join(os.path.dirname(__file__), creds_file) if not os.path.isabs(creds_file) else creds_file
            self.creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
            
        self.client = gspread.authorize(self.creds)
        self.db = self.client.open_by_key(self.sheet_id)
        
        # Standard headers for primary tabs
        self.comp_headers = ["id", "name", "linkedin_url", "description", "location", "employee_count", "industry", "website", "search_query", "created_at"]
        self.dm_headers = ["id", "company_id", "name", "title", "linkedin_url", "location", "snippet", "created_at"]
        self.lead_headers = ["id", "decision_maker_id", "status", "notes", "score", "created_at", "updated_at"]
        self.msg_headers = ["id", "lead_id", "message_type", "content", "status", "created_at"]

    def _sheet_name(self, base_name, campaign):
        # Default/empty campaign uses the base name (cleanest)
        if not campaign or campaign.lower() == "default":
            return base_name
        return f"[{campaign}] {base_name}"

    def _get_sheet(self, name, headers, campaign="Default"):
        full_name = self._sheet_name(name, campaign)
        try:
            sheet = self.db.worksheet(full_name)
            # Ensure all headers exist
            existing = sheet.row_values(1)
            missing = [h for h in headers if h not in existing]
            if missing:
                for h in missing:
                    sheet.update_cell(1, len(existing) + 1, h)
                    existing.append(h)
            return sheet
        except gspread.exceptions.WorksheetNotFound:
            sheet = self.db.add_worksheet(title=full_name, rows="1000", cols=str(len(headers)))
            sheet.append_row(headers)
            # Make headers bold
            sheet.format("A1:Z1", {"textFormat": {"bold": True}})
            return sheet

    def _next_id(self, sheet):
        records = sheet.get_all_records()
        return max([int(r.get("id", 0)) for r in records if str(r.get("id")).isdigit()], default=0) + 1

    def init_db(self):
        # Ensure Default tabs exist
        self._get_sheet("Companies", self.comp_headers)
        self._get_sheet("DecisionMakers", self.dm_headers)
        self._get_sheet("Leads", self.lead_headers)
        self._get_sheet("Messages", self.msg_headers)
        self._get_sheet("SearchHistory", ["id", "query", "filters", "result_count", "created_at"])
        print("✅ Google Sheets Database Initialized")

    def add_company(self, data):
        campaign = data.get("campaign", "Default")
        sheet = self._get_sheet("Companies", self.comp_headers, campaign)
        records = sheet.get_all_records()
        
        # Check if exists in this campaign's tab
        for r in records:
            if r.get("linkedin_url") == data.get("linkedin_url"):
                return r
                
        new_id = str(self._next_id(sheet))
        data["id"] = new_id
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        
        row = [
            data.get("id"), data.get("name"), data.get("linkedin_url"), data.get("description"),
            data.get("location"), data.get("employee_count"), data.get("industry"),
            data.get("website"), data.get("search_query"), data.get("created_at")
        ]
        sheet.append_row(row)
        return data

    def get_companies(self, page=1, limit=20, search="", industry="", location="", campaign="Default"):
        sheet = self._get_sheet("Companies", self.comp_headers, campaign)
        recs = sheet.get_all_records()
        
        if search:
            search = search.lower()
            recs = [r for r in recs if search in str(r.get("name", "")).lower()]
            
        total = len(recs)
        recs = sorted(recs, key=lambda x: int(x['id']) if str(x.get('id', '')).isdigit() else 0, reverse=True)
        
        start = (page - 1) * limit
        page_recs = recs[start:start + limit]
        
        # Count decision makers
        dm_sheet = self._get_sheet("DecisionMakers", self.dm_headers, campaign)
        dms = dm_sheet.get_all_records()
        for r in page_recs:
            r["decision_makers_count"] = sum(1 for dm in dms if str(dm.get("company_id")) == str(r.get("id")))
            
        return {"total": total, "companies": page_recs}

    def get_company(self, id, campaign="Default"):
        sheet = self._get_sheet("Companies", self.comp_headers, campaign)
        for r in sheet.get_all_records():
            if str(r.get("id")) == str(id):
                dm_sheet = self._get_sheet("DecisionMakers", self.dm_headers, campaign)
                dms = dm_sheet.get_all_records()
                r["decision_makers"] = [dm for dm in dms if str(dm.get("company_id")) == str(id)]
                return r
        return None

    def delete_company(self, id, campaign="Default"):
        sheet = self._get_sheet("Companies", self.comp_headers, campaign)
        records = sheet.get_all_records()
        for i, r in enumerate(records):
            if str(r.get("id")) == str(id):
                sheet.delete_rows(i + 2) 
                return True
        return False

    def add_decision_maker(self, company_id, data, campaign="Default"):
        sheet = self._get_sheet("DecisionMakers", self.dm_headers, campaign)
        records = sheet.get_all_records()
        
        for r in records:
            if r.get("linkedin_url") == data.get("linkedin_url") and str(r.get("company_id")) == str(company_id):
                return r
                
        new_id = str(self._next_id(sheet))
        data["id"] = new_id
        data["company_id"] = str(company_id)
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        
        row = [
            data.get("id"), data.get("company_id"), data.get("name"), data.get("title"),
            data.get("linkedin_url"), data.get("location"), data.get("snippet"), data.get("created_at")
        ]
        sheet.append_row(row)
        return data

    def get_decision_maker(self, id, campaign="Default"):
        sheet = self._get_sheet("DecisionMakers", self.dm_headers, campaign)
        for r in sheet.get_all_records():
            if str(r.get("id")) == str(id):
                return r
        return None

    def add_lead(self, decision_maker_id, notes="", campaign="Default"):
        sheet = self._get_sheet("Leads", self.lead_headers, campaign)
        records = sheet.get_all_records()
        
        for r in records:
            if str(r.get("decision_maker_id")) == str(decision_maker_id):
                return {**r, "existing": True}
                
        new_id = str(self._next_id(sheet))
        now = datetime.now(timezone.utc).isoformat()
        
        row = [new_id, str(decision_maker_id), "new", notes, 0, now, now]
        sheet.append_row(row)
        
        return {
            "id": new_id,
            "decision_maker_id": str(decision_maker_id),
            "status": "new",
            "notes": notes,
            "score": 0,
            "created_at": now,
            "updated_at": now
        }

    def get_leads(self, status="", campaign="Default"):
        leads = self._get_sheet("Leads", self.lead_headers, campaign).get_all_records()
        dms = {str(d['id']): d for d in self._get_sheet("DecisionMakers", self.dm_headers, campaign).get_all_records()}
        cos = {str(c['id']): c for c in self._get_sheet("Companies", self.comp_headers, campaign).get_all_records()}
        msgs = self._get_sheet("Messages", self.msg_headers, campaign).get_all_records()
        
        enriched = []
        for r in leads:
            if status and str(r.get('status')) != status: continue
            
            dm = dms.get(str(r.get('decision_maker_id')), {})
            company = cos.get(str(dm.get('company_id')), {})
            
            msg_count = sum(1 for m in msgs if str(m.get('lead_id')) == str(r.get('id')))
            
            enriched.append({
                **r,
                "decision_maker": {**dm, "company": company},
                "messages_count": msg_count
            })
            
        return sorted(enriched, key=lambda x: int(x['id']) if str(x.get('id','')).isdigit() else 0, reverse=True)

    def update_lead(self, id, data, campaign="Default"):
        sheet = self._get_sheet("Leads", self.lead_headers, campaign)
        records = sheet.get_all_records()
        headers = sheet.row_values(1)
        
        for i, r in enumerate(records):
            if str(r.get("id")) == str(id):
                row_num = i + 2
                now = datetime.now(timezone.utc).isoformat()
                
                if "status" in data:
                    col = headers.index("status") + 1
                    sheet.update_cell(row_num, col, data["status"])
                if "notes" in data:
                    col = headers.index("notes") + 1
                    sheet.update_cell(row_num, col, data["notes"])
                
                col = headers.index("updated_at") + 1
                sheet.update_cell(row_num, col, now)
                
                return {**r, **data, "updated_at": now}
        return None

    def delete_lead(self, id, campaign="Default"):
        sheet = self._get_sheet("Leads", self.lead_headers, campaign)
        for i, r in enumerate(sheet.get_all_records()):
            if str(r.get("id")) == str(id):
                sheet.delete_rows(i + 2)
                return True
        return False

    def get_lead_stats(self, campaign="Default"):
        leads = self._get_sheet("Leads", self.lead_headers, campaign).get_all_records()
        cos_count = len(self._get_sheet("Companies", self.comp_headers, campaign).get_all_records())
        dms_count = len(self._get_sheet("DecisionMakers", self.dm_headers, campaign).get_all_records())
        
        total = len(leads)
        by_status = {s: sum(1 for r in leads if r.get("status") == s) 
                    for s in ["new", "contacted", "replied", "meeting", "negotiation", "closed_won", "closed_lost"]}
        
        return {
            "total_leads": total,
            "total_companies": cos_count,
            "total_decision_makers": dms_count,
            "by_status": by_status,
            "conversion_rate": round(by_status['closed_won']/total*100 if total > 0 else 0, 1)
        }

    def add_message(self, lead_id, message_type, content, campaign="Default"):
        sheet = self._get_sheet("Messages", self.msg_headers, campaign)
        new_id = str(self._next_id(sheet))
        now = datetime.now(timezone.utc).isoformat()
        
        row = [new_id, str(lead_id), message_type, content, "draft", now]
        sheet.append_row(row)
        
        return {
            "id": new_id, "lead_id": str(lead_id), "message_type": message_type,
            "content": content, "status": "draft", "created_at": now
        }

    def get_messages(self, lead_id, campaign="Default"):
        msgs = self._get_sheet("Messages", self.msg_headers, campaign).get_all_records()
        filtered = [r for r in msgs if str(r.get('lead_id')) == str(lead_id)]
        return sorted(filtered, key=lambda x: int(x['id']) if str(x.get('id','')).isdigit() else 0, reverse=True)

    def update_message(self, id, data, campaign="Default"):
        sheet = self._get_sheet("Messages", self.msg_headers, campaign)
        records = sheet.get_all_records()
        headers = sheet.row_values(1)
        
        for i, r in enumerate(records):
            if str(r.get("id")) == str(id):
                row_num = i + 2
                if "status" in data:
                    col = headers.index("status") + 1
                    sheet.update_cell(row_num, col, data["status"])
                if "content" in data:
                    col = headers.index("content") + 1
                    sheet.update_cell(row_num, col, data["content"])
                return {**r, **data}
        return None

    def add_search_history(self, query, filters, result_count):
        sheet = self.db.worksheet("SearchHistory")
        new_id = str(self._next_id(sheet))
        now = datetime.now(timezone.utc).isoformat()
        
        row = [new_id, query, json.dumps(filters), result_count, now]
        sheet.append_row(row)

    def get_search_history(self, limit=20):
        recs = self.db.worksheet("SearchHistory").get_all_records()
        for r in recs:
            if isinstance(r.get("filters"), str):
                try: r["filters"] = json.loads(r["filters"])
                except: pass
        
        sorted_recs = sorted(recs, key=lambda x: int(x.get('id', 0)) if str(x.get('id','')).isdigit() else 0, reverse=True)
        return sorted_recs[:limit]


# ── Local DB Implementation ───────────────────────────────────────────
class LocalDB:
    def __init__(self, filename="data.json"):
        self.filename = os.path.join(os.path.dirname(__file__), filename) if not os.path.isabs(filename) else filename
        self.data = self._load()
    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f: return json.load(f)
            except: pass
        return {"Companies": [], "DecisionMakers": [], "Leads": [], "Messages": [], "SearchHistory": []}
    def _save(self):
        with open(self.filename, 'w') as f: json.dump(self.data, f, indent=2)
    def _next_id(self, table):
        items = self.data.get(table, [])
        return max([int(i.get("id", 0)) for i in items if str(i.get("id")).isdigit()], default=0) + 1
    def init_db(self): print("✅ Local Database Initialized")
    def add_company(self, data):
        # Check if exists IN THIS CAMPAIGN
        current_campaign = data.get("campaign", "Default")
        for r in self.data["Companies"]:
            if r.get("linkedin_url") == data.get("linkedin_url") and r.get("campaign") == current_campaign: return r
        data["id"] = str(self._next_id("Companies"))
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        data["campaign"] = data.get("campaign", "Default")
        self.data["Companies"].append(data); self._save(); return data
    def get_companies(self, page=1, limit=20, search="", industry="", location="", campaign=""):
        recs = self.data["Companies"]
        if search: recs = [r for r in recs if search.lower() in r.get("name","").lower()]
        if campaign: recs = [r for r in recs if r.get("campaign") == campaign]
        total = len(recs); recs = sorted(recs, key=lambda x: int(x['id']), reverse=True); start = (page-1)*limit
        page_recs = recs[start:start+limit]
        for r in page_recs: r["decision_makers_count"] = sum(1 for dm in self.data["DecisionMakers"] if str(dm.get("company_id")) == str(r.get("id")))
        return {"total": total, "companies": page_recs}
    def get_company(self, id, campaign="Default"):
        for r in self.data["Companies"]:
            if str(r.get("id")) == str(id):
                r["decision_makers"] = [dm for dm in self.data["DecisionMakers"] if str(dm.get("company_id")) == str(id)]
                return r
        return None
    def delete_company(self, id, campaign="Default"):
        self.data["Companies"] = [r for r in self.data["Companies"] if str(r.get("id")) != str(id)]
        self.data["DecisionMakers"] = [r for r in self.data["DecisionMakers"] if str(r.get("company_id")) != str(id)]
        self._save(); return True
    def add_decision_maker(self, company_id, data, campaign="Default"):
        for r in self.data["DecisionMakers"]:
            if r.get("linkedin_url") == data.get("linkedin_url") and str(r.get("company_id")) == str(company_id): return r
        data["id"] = str(self._next_id("DecisionMakers"))
        data["company_id"] = str(company_id)
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        self.data["DecisionMakers"].append(data); self._save(); return data
    def get_decision_maker(self, id, campaign="Default"):
        for r in self.data["DecisionMakers"]:
            if str(r.get("id")) == str(id): return r
        return None
    def add_lead(self, decision_maker_id, notes="", campaign="Default"):
        for r in self.data["Leads"]:
            if str(r.get("decision_maker_id")) == str(decision_maker_id): return {**r, "existing": True}
        row = {"id": str(self._next_id("Leads")), "decision_maker_id": str(decision_maker_id), "status": "new", "notes": notes, "score": 0, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()}
        self.data["Leads"].append(row); self._save(); return row
    def get_leads(self, status="", campaign="Default"):
        recs = self.data["Leads"]; dms = {str(d['id']): d for d in self.data["DecisionMakers"]}; cos = {str(c['id']): c for c in self.data["Companies"]}
        enriched = [{**r, "decision_maker": {**dms.get(str(r['decision_maker_id']), {}), "company": cos.get(str(dms.get(str(r['decision_maker_id']), {}).get('company_id')), {})}, "messages_count": 0} for r in recs if (not status or r['status'] == status) and (not campaign or cos.get(str(dms.get(str(r['decision_maker_id']), {}).get('company_id')), {}).get('campaign') == campaign)]
        return sorted(enriched, key=lambda x: int(x['id']), reverse=True)
    def update_lead(self, id, data, campaign="Default"):
        for r in self.data["Leads"]:
            if str(r['id']) == str(id):
                if "status" in data: r["status"] = data["status"]
                if "notes" in data: r["notes"] = data["notes"]
                r["updated_at"] = datetime.now(timezone.utc).isoformat(); self._save(); return r
        return None
    def delete_lead(self, id, campaign="Default"):
        self.data["Leads"] = [r for r in self.data["Leads"] if str(r['id']) != str(id)]; self._save(); return True
    def get_lead_stats(self, campaign="Default"):
        cos = [c for c in self.data["Companies"] if not campaign or c.get("campaign") == campaign]
        co_ids = {str(c["id"]) for c in cos}
        dms = [d for d in self.data["DecisionMakers"] if str(d.get("company_id")) in co_ids]
        dm_ids = {str(d["id"]) for d in dms}
        leads = [l for l in self.data["Leads"] if str(l.get("decision_maker_id")) in dm_ids]
        total = len(leads)
        by_status = {s: sum(1 for r in leads if r.get("status") == s) for s in ["new", "contacted", "replied", "meeting", "negotiation", "closed_won", "closed_lost"]}
        return {"total_leads": total, "total_companies": len(cos), "total_decision_makers": len(dms), "by_status": by_status, "conversion_rate": round(by_status['closed_won']/total*100 if total > 0 else 0, 1)}
    def add_message(self, lead_id, message_type, content, campaign="Default"):
        row = {"id": str(self._next_id("Messages")), "lead_id": str(lead_id), "message_type": message_type, "content": content, "status": "draft", "created_at": datetime.now(timezone.utc).isoformat()}
        self.data["Messages"].append(row); self._save(); return row
    def get_messages(self, lead_id, campaign="Default"):
        return sorted([r for r in self.data["Messages"] if str(r['lead_id']) == str(lead_id)], key=lambda x: int(x['id']), reverse=True)
    def update_message(self, id, data, campaign="Default"):
        for r in self.data["Messages"]:
            if str(r['id']) == str(id):
                if "status" in data: r["status"] = data["status"]
                if "notes" in data: r["notes"] = data["notes"]
                self._save(); return r
        return None
    def add_search_history(self, query, filters, result_count):
        self.data["SearchHistory"].append({"id": str(self._next_id("SearchHistory")), "query": query, "filters": filters, "result_count": result_count, "created_at": datetime.now(timezone.utc).isoformat()}); self._save()
    def get_search_history(self, limit=20): return sorted(self.data["SearchHistory"], key=lambda x: int(x.get('id', 0)), reverse=True)[:limit]

from config import GOOGLE_SHEET_ID, GOOGLE_SERVICE_ACCOUNT_FILE, GOOGLE_SERVICE_ACCOUNT_JSON

# ── Factory ───────────────────────────────────────────────────────────
_db_instance = None
def _db():
    global _db_instance
    if not _db_instance: 
        # Check for Sheet ID
        if not GOOGLE_SHEET_ID:
            print("⚠️ GOOGLE_SHEET_ID not found, falling back to LocalDB")
            _db_instance = LocalDB()
            return _db_instance

        # Try Service Account JSON (Raw string from Env)
        if GOOGLE_SERVICE_ACCOUNT_JSON:
            try:
                _db_instance = GoogleSheetsDB(GOOGLE_SHEET_ID, GOOGLE_SERVICE_ACCOUNT_FILE, GOOGLE_SERVICE_ACCOUNT_JSON)
                return _db_instance
            except Exception as e:
                print(f"⚠️ Failed to connect to Google Sheets via JSON ENV: {e}")

        # Try Service Account File
        creds_path = os.path.join(os.path.dirname(__file__), GOOGLE_SERVICE_ACCOUNT_FILE)
        if os.path.exists(creds_path):
            try:
                _db_instance = GoogleSheetsDB(GOOGLE_SHEET_ID, GOOGLE_SERVICE_ACCOUNT_FILE)
                return _db_instance
            except Exception as e:
                print(f"⚠️ Failed to connect to Google Sheets via file: {e}")

        # Fallback
        print("⚠️ No valid Google Sheets configuration found, using LocalDB")
        _db_instance = LocalDB()
        
    return _db_instance

# Functional API for Routes
def init_db(): return _db().init_db()
def add_company(data): return _db().add_company(data)
def get_companies(page=1, limit=20, search="", industry="", location="", campaign="Default"): return _db().get_companies(page, limit, search, industry, location, campaign)
def get_company(id, campaign="Default"): return _db().get_company(id, campaign)
def delete_company(id, campaign="Default"): return _db().delete_company(id, campaign)
def add_decision_maker(company_id, data, campaign="Default"): return _db().add_decision_maker(company_id, data, campaign)
def get_decision_maker(id, campaign="Default"): return _db().get_decision_maker(id, campaign)
def add_lead(decision_maker_id, notes="", campaign="Default"): return _db().add_lead(decision_maker_id, notes, campaign)
def get_leads(status="", campaign="Default"): return _db().get_leads(status, campaign)
def update_lead(id, data, campaign="Default"): return _db().update_lead(id, data, campaign)
def delete_lead(id, campaign="Default"): return _db().delete_lead(id, campaign)
def get_lead_stats(campaign="Default"): return _db().get_lead_stats(campaign)
def add_message(lead_id, message_type, content, campaign="Default"): return _db().add_message(lead_id, message_type, content, campaign)
def get_messages(lead_id, campaign="Default"): return _db().get_messages(lead_id, campaign)
def update_message(id, data, campaign="Default"): return _db().update_message(id, data, campaign)
def add_search_history(query, filters, result_count): return _db().add_search_history(query, filters, result_count)
def get_search_history(limit=20): return _db().get_search_history(limit)
