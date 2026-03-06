"""
AI Message Generator Service
Uses Cerebras Cloud SDK (free tier: 1M tokens/day) for generating
personalized LinkedIn outreach messages.
"""

from cerebras.cloud.sdk import Cerebras
from config import CEREBRAS_API_KEY

client = Cerebras(api_key=CEREBRAS_API_KEY)

# ── Prompt Templates ──────────────────────────────────

CONNECTION_REQUEST_PROMPT = """You are a professional B2B sales outreach expert. Write a short, personalized LinkedIn connection request message (max 300 characters for LinkedIn limit).

Company Info:
- Company: {company_name}
- Industry: {industry}
- Description: {company_description}
- Location: {company_location}

Decision Maker:
- Name: {person_name}
- Title: {person_title}

Sender's Context: {sender_context}

Rules:
1. Start with "Hi {first_name}," 
2. Reference something specific about their company
3. Be genuine, not salesy
4. End with a soft CTA (e.g., "Would love to connect")
5. Keep under 300 characters
6. No emojis, no links
"""

FOLLOW_UP_PROMPT = """You are a professional B2B sales outreach expert. Write a personalized LinkedIn follow-up message.

Company Info:
- Company: {company_name}
- Industry: {industry}
- Description: {company_description}

Decision Maker:
- Name: {person_name}
- Title: {person_title}

Previous Message: {previous_message}

Sender's Context: {sender_context}

Rules:
1. Reference the previous connection
2. Add value (share an insight, case study hint, or relevant question)
3. Keep it conversational, 2-3 sentences max
4. End with a specific question or CTA
5. No emojis, no links
"""

INMAIL_PROMPT = """You are a professional B2B sales outreach expert. Write a compelling LinkedIn InMail message.

Company Info:
- Company: {company_name}
- Industry: {industry}
- Description: {company_description}
- Location: {company_location}
- Size: {employee_count}

Decision Maker:
- Name: {person_name}
- Title: {person_title}

Sender's Context: {sender_context}

Rules:
1. Write a compelling subject line (first line, prefix with "Subject: ")
2. Open with something relevant to their role/company
3. Explain value proposition in 2-3 sentences
4. Include a clear CTA (e.g., "Would a 15-min call work?")
5. Keep professional but warm
6. Total body: 4-6 sentences max
"""


async def generate_message(
    message_type: str,
    company_name: str,
    industry: str = "",
    company_description: str = "",
    company_location: str = "",
    employee_count: str = "",
    person_name: str = "",
    person_title: str = "",
    sender_context: str = "We help companies automate their business processes using AI agents.",
    previous_message: str = "",
) -> dict:
    """Generate a personalized outreach message using Cerebras AI."""

    first_name = person_name.split()[0] if person_name else "there"

    template_map = {
        "connection_request": CONNECTION_REQUEST_PROMPT,
        "follow_up": FOLLOW_UP_PROMPT,
        "inmail": INMAIL_PROMPT,
    }

    template = template_map.get(message_type, CONNECTION_REQUEST_PROMPT)

    prompt = template.format(
        company_name=company_name,
        industry=industry,
        company_description=company_description,
        company_location=company_location,
        employee_count=employee_count,
        person_name=person_name,
        person_title=person_title,
        first_name=first_name,
        sender_context=sender_context,
        previous_message=previous_message,
    )

    try:
        response = client.chat.completions.create(
            model="llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": "You are a professional B2B outreach message writer. Write concise, personalized messages."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )

        content = response.choices[0].message.content.strip()

        # Parse subject for InMail
        subject = ""
        if message_type == "inmail" and content.startswith("Subject:"):
            lines = content.split("\n", 1)
            subject = lines[0].replace("Subject:", "").strip()
            content = lines[1].strip() if len(lines) > 1 else content

        return {
            "message": content,
            "subject": subject,
            "type": message_type,
            "tokens_used": response.usage.total_tokens if response.usage else 0,
        }

    except Exception as e:
        return {
            "message": f"Error generating message: {str(e)}",
            "subject": "",
            "type": message_type,
            "tokens_used": 0,
            "error": True,
        }
