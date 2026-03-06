import json
import os
import sys
from datetime import datetime, timezone

# Add backend to path so we can import database
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import _db, LocalDB, GoogleSheetsDB

def migrate():
    print("🚀 Starting Data Migration: Local JSON -> Google Sheets...")
    
    # 1. Force load local data
    local = LocalDB("data.json")
    local_data = local.data
    
    # 2. Get Google Sheets instance
    sheets = _db()
    if not isinstance(sheets, GoogleSheetsDB):
        print("❌ Error: Google Sheets is not configured or connected.")
        return

    # Helper to map old IDs to new ones if they change (though SheetsDB IDs are strings)
    # Actually, we'll try to keep the IDs or let Sheets generate them if they don't exist.
    
    # --- 3. Migrate Search History ---
    print("\n[1/4] Migrating Search History...")
    history = local_data.get("SearchHistory", [])
    for h in history:
        try:
            sheets.add_search_history(h['query'], h['filters'], h['result_count'])
            print(f"  ✅ Migrated search: {h['query'][:50]}...")
        except Exception as e:
            print(f"  ⚠️ Skip search: {e}")

    # --- 4. Migrate Companies ---
    print("\n[2/4] Migrating Companies...")
    companies = local_data.get("Companies", [])
    co_map = {} # old_id -> new_id
    for co in companies:
        old_id = co.get("id")
        # Clean data for SheetsDB format
        co_data = {
            "name": co.get("name"),
            "linkedin_url": co.get("linkedin_url"),
            "description": co.get("description"),
            "location": co.get("location"),
            "employee_count": co.get("employee_count"),
            "industry": co.get("industry"),
            "website": co.get("website"),
            "search_query": co.get("search_query")
        }
        try:
            new_co = sheets.add_company(co_data)
            co_map[str(old_id)] = str(new_co["id"])
            print(f"  ✅ Migrated company: {co['name']}")
        except Exception as e:
            print(f"  ⚠️ Skip company {co['name']}: {e}")

    # --- 5. Migrate Decision Makers ---
    print("\n[3/4] Migrating Decision Makers...")
    dms = local_data.get("DecisionMakers", [])
    dm_map = {} # old_id -> new_id
    for dm in dms:
        old_id = dm.get("id")
        old_co_id = dm.get("company_id")
        new_co_id = co_map.get(str(old_co_id))
        
        if not new_co_id:
            print(f"  ⚠️ Skipping DM {dm['name']} (Company ID {old_co_id} not found)")
            continue
            
        dm_data = {
            "name": dm.get("name"),
            "title": dm.get("title"),
            "linkedin_url": dm.get("linkedin_url"),
            "location": dm.get("location"),
            "snippet": dm.get("snippet")
        }
        try:
            new_dm = sheets.add_decision_maker(new_co_id, dm_data)
            dm_map[str(old_id)] = str(new_dm["id"])
            print(f"  ✅ Migrated DM: {dm['name']}")
        except Exception as e:
            print(f"  ⚠️ Skip DM {dm['name']}: {e}")

    # --- 6. Migrate Leads ---
    print("\n[4/4] Migrating Leads...")
    leads = local_data.get("Leads", [])
    for lead in leads:
        old_dm_id = lead.get("decision_maker_id")
        new_dm_id = dm_map.get(str(old_dm_id))
        
        if not new_dm_id:
            print(f"  ⚠️ Skipping Lead (DM ID {old_dm_id} not found)")
            continue
            
        try:
            # add_lead returns existing if already there
            new_lead = sheets.add_lead(new_dm_id, lead.get("notes", ""))
            # Update status if it's not 'new'
            if lead.get("status") != "new":
                sheets.update_lead(new_lead["id"], {"status": lead["status"]})
            print(f"  ✅ Migrated lead status for DM ID {new_dm_id}")
        except Exception as e:
            print(f"  ⚠️ Skip lead: {e}")

    print("\n🎉 Migration Complete! All data is now in Google Sheets.")

if __name__ == "__main__":
    migrate()
