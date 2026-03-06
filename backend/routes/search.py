"""Search Routes — Company discovery via Google X-ray search."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from database import add_company, add_decision_maker, add_search_history, get_search_history, get_company
from services.xray_search import xray_search_companies, xray_find_decision_makers

router = APIRouter(prefix="/api/search", tags=["Search"])


class CompanySearchRequest(BaseModel):
    industry: str = ""
    location: str = ""
    company_size: str = ""
    keywords: str = ""
    max_results: int = 10
    campaign: str = "Default"


class DecisionMakerSearchRequest(BaseModel):
    roles: Optional[list[str]] = None
    campaign: str = "Default"


@router.post("/companies")
async def search_companies(req: CompanySearchRequest):
    """Search for companies using Google X-ray search on LinkedIn."""
    results = await xray_search_companies(
        industry=req.industry,
        location=req.location,
        company_size=req.company_size,
        keywords=req.keywords,
        max_results=req.max_results,
    )

    saved = []
    for r in results:
        r["campaign"] = req.campaign
        company = add_company(r)
        saved.append(company)

    add_search_history(
        query=f"industry={req.industry} location={req.location} keywords={req.keywords}",
        filters=req.model_dump(),
        result_count=len(saved),
    )

    return {
        "count": len(saved),
        "companies": saved,
    }


@router.post("/decision-makers/{company_id}")
async def search_decision_makers(
    company_id: int,
    req: DecisionMakerSearchRequest = DecisionMakerSearchRequest(),
):
    """Find decision makers at a specific company."""
    company = get_company(company_id, campaign=req.campaign)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    results = await xray_find_decision_makers(company["name"], roles=req.roles)

    saved = []
    for r in results:
        dm = add_decision_maker(company_id, r, campaign=req.campaign)
        saved.append(dm)

    return {
        "company": company["name"],
        "count": len(saved),
        "decision_makers": saved,
    }


@router.get("/history")
async def get_history():
    """Get past search history."""
    return get_search_history(limit=20)
