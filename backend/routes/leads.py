"""Lead Routes — Pipeline management for B2B outreach."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from database import add_lead, get_leads, update_lead, delete_lead, get_lead_stats, get_decision_maker

router = APIRouter(prefix="/api/leads", tags=["Leads"])


class CreateLeadRequest(BaseModel):
    decision_maker_id: int
    notes: str = ""
    campaign: str = "Default"


class UpdateLeadRequest(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    score: Optional[float] = None


@router.get("")
async def list_leads(status: str = "", campaign: str = ""):
    """List all leads with optional status filter."""
    return get_leads(status=status, campaign=campaign)


@router.post("")
async def create_lead(req: CreateLeadRequest):
    """Create a new lead from a decision maker."""
    dm = get_decision_maker(req.decision_maker_id, campaign=req.campaign)
    if not dm:
        raise HTTPException(status_code=404, detail="Decision maker not found")

    result = add_lead(req.decision_maker_id, req.notes, campaign=req.campaign)
    if result.get("existing"):
        return {"id": result["id"], "message": "Lead already exists", "status": result.get("status", "new")}

    return {"id": result["id"], "status": result.get("status", "new"), "message": "Lead created successfully"}


@router.patch("/{lead_id}")
async def patch_lead(lead_id: int, req: UpdateLeadRequest, campaign: str = "Default"):
    """Update lead status, notes, or score."""
    data = {}
    if req.status:
        valid_statuses = ["new", "contacted", "replied", "meeting", "negotiation", "closed_won", "closed_lost"]
        if req.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status: {req.status}")
        data["status"] = req.status
    if req.notes is not None:
        data["notes"] = req.notes
    if req.score is not None:
        data["score"] = req.score

    result = update_lead(lead_id, data, campaign=campaign)
    if not result:
        raise HTTPException(status_code=404, detail="Lead not found")

    return {"id": lead_id, "status": result.get("status"), "message": "Lead updated"}


@router.delete("/{lead_id}")
async def remove_lead(lead_id: int, campaign: str = "Default"):
    """Delete a lead."""
    success = delete_lead(lead_id, campaign=campaign)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Lead deleted"}


@router.get("/stats")
async def lead_statistics(campaign: str = ""):
    """Get pipeline statistics."""
    return get_lead_stats(campaign=campaign)
