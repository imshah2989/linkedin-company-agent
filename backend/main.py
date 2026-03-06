"""
LinkedIn Companies Approach Agent — FastAPI Backend
Main application entry point with CORS, routers, and Google Sheets initialization.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routes.search import router as search_router
from routes.companies import router as companies_router
from routes.leads import router as leads_router
from routes.messages import router as messages_router

app = FastAPI(
    title="LinkedIn Company Agent API",
    description="AI-powered B2B lead generation agent using Google X-ray search, Cerebras AI, and Google Sheets",
    version="1.0.0",
)

# ── CORS ───────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "https://*.vercel.app"  # Support Vercel production and preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────
app.include_router(search_router)
app.include_router(companies_router)
app.include_router(leads_router)
app.include_router(messages_router)


# ── Startup ────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    try:
        init_db()
        print("✅ Google Sheets database initialized")
    except Exception as e:
        print(f"⚠️ Google Sheets init warning: {e}")
        print("  Make sure GOOGLE_SHEET_ID and service_account.json are configured in .env")
    print("🚀 LinkedIn Company Agent API is running")


@app.get("/")
async def root():
    return {
        "name": "LinkedIn Company Agent API",
        "version": "1.0.0",
        "database": "Google Sheets",
        "ai": "Cerebras (free tier)",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/api/campaigns")
async def get_campaigns():
    from database import get_all_campaigns
    return {"campaigns": get_all_campaigns()}

@app.get("/health")
async def health():
    return {"status": "healthy"}
