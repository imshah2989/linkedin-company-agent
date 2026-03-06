"""Company Routes — CRUD for discovered companies."""

from fastapi import APIRouter, HTTPException, Query

from database import get_companies, get_company, delete_company

router = APIRouter(prefix="/api/companies", tags=["Companies"])


@router.get("")
async def list_companies(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    industry: str = "",
    location: str = "",
    search: str = "",
    campaign: str = "",
):
    """List all discovered companies with filtering and pagination."""
    return get_companies(page=page, limit=limit, search=search, industry=industry, location=location, campaign=campaign)


@router.get("/{company_id}")
async def get_company_detail(company_id: int, campaign: str = "Default"):
    """Get company detail with its decision makers."""
    company = get_company(company_id, campaign=campaign)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.delete("/{company_id}")
async def remove_company(company_id: int, campaign: str = "Default"):
    """Delete a company and all its related data."""
    success = delete_company(company_id, campaign=campaign)
    if not success:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"message": "Company deleted"}
