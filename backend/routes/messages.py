"""Message Routes — AI-powered outreach message generation and tracking."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from database import add_message, get_messages, update_message, get_leads, get_decision_maker, get_company
from services.ai_generator import generate_message

router = APIRouter(prefix="/api/messages", tags=["Messages"])


class GenerateMessageRequest(BaseModel):
    lead_id: int
    message_type: str = "connection_request"
    sender_context: str = "We help companies automate their business processes using AI agents."
    campaign: str = "Default"


class UpdateMessageRequest(BaseModel):
    content: Optional[str] = None
    status: Optional[str] = None


@router.post("/generate")
async def generate_outreach_message(req: GenerateMessageRequest):
    """Generate a personalized outreach message for a lead using Cerebras AI."""
    # Find the lead in the correct campaign
    all_leads = get_leads(campaign=req.campaign)
    lead = None
    for l in all_leads:
        if str(l.get("id")) == str(req.lead_id):
            lead = l
            break

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    dm = lead.get("decision_maker", {})
    company = dm.get("company", {}) or {}

    # Get previous message if follow-up
    previous_message = ""
    if req.message_type == "follow_up":
        msgs = get_messages(req.lead_id, campaign=req.campaign)
        if msgs:
            previous_message = msgs[0].get("content", "")

    result = await generate_message(
        message_type=req.message_type,
        company_name=company.get("name", ""),
        industry=company.get("industry", ""),
        company_description="",
        company_location="",
        employee_count="",
        person_name=dm.get("name", ""),
        person_title=dm.get("title", ""),
        sender_context=req.sender_context,
        previous_message=previous_message,
    )

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["message"])

    # Save to Google Sheets in the correct campaign
    saved = add_message(req.lead_id, req.message_type, result["message"], campaign=req.campaign)

    return {
        "id": saved.get("id"),
        "content": result["message"],
        "subject": result.get("subject", ""),
        "type": result["type"],
        "status": "draft",
        "tokens_used": result.get("tokens_used", 0),
    }


@router.get("/{lead_id}")
async def get_lead_messages(lead_id: int, campaign: str = "Default"):
    """Get all messages for a lead."""
    return get_messages(lead_id, campaign=campaign)


@router.patch("/{message_id}")
async def patch_message(message_id: int, req: UpdateMessageRequest, campaign: str = "Default"):
    """Update a message content or status."""
    data = {}
    if req.content is not None:
        data["content"] = req.content
    if req.status:
        valid = ["draft", "sent", "replied"]
        if req.status not in valid:
            raise HTTPException(status_code=400, detail=f"Invalid status: {req.status}")
        data["status"] = req.status

    result = update_message(message_id, data, campaign=campaign)
    if not result:
        raise HTTPException(status_code=404, detail="Message not found")

    return {"id": message_id, "message": "Message updated"}
