"""
Google X-ray Search Service (via Serper.dev)
Uses Serper.dev API to perform site:linkedin.com searches
for discovering companies and their decision makers.
"""

import httpx
import re
import json
from typing import Optional
from config import SERPER_API_KEY

SERPER_URL = "https://google.serper.dev/search"


def _location_matches(snippet: str, description: str, target_location: str) -> bool:
    """
    Check if a company's snippet/description indicates it's actually 
    in the target location, not just mentioning it.
    Returns True if location seems to match, or if we can't determine.
    """
    if not target_location:
        return True  # No location filter, accept all

    # Normalize: lower case and remove spaces/punctuation for a "slug" match
    def normalize(s):
        return re.sub(r'[^a-z0-9]', '', s.lower())

    target_norm = normalize(target_location)
    text = f"{snippet} {description}".lower()
    text_norm = normalize(text)

    # If the normalized target is in the normalized text, it's a strong match
    if target_norm in text_norm:
        return True

    # Check for actual target (with spaces) as a fallback
    target = target_location.lower().strip()
    if target in text:
        return True

    return False


async def xray_search_companies(
    industry: str = "",
    location: str = "",
    company_size: str = "",
    keywords: str = "",
    max_results: int = 10
) -> list[dict]:
    """
    Search for companies on LinkedIn using Google X-ray search via Serper.dev.
    Builds query like: site:linkedin.com/company "AI" "startup" "San Francisco"
    """
    query_parts = ['site:linkedin.com/company']

    if industry:
        query_parts.append(f'"{industry}"')
    if location:
        query_parts.append(f'"{location}"')
    if company_size:
        query_parts.append(f'"{company_size}"')
    if keywords:
        for kw in keywords.split(","):
            kw = kw.strip()
            if kw:
                # Remove strict quotes from keywords to allow for typos and fuzzy matching
                query_parts.append(kw)

    query = " ".join(query_parts)
    companies = []

    # Request more results than needed so we can filter by location
    request_num = min(max_results * 3, 30) if location else min(max_results, 30)

    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json",
        }
        payload = {"q": query}

        # Use Serper's location parameter for geo-targeting
        # Note: We remove this because it requires canonical names (like "New York, New York, United States")
        # and we already include the location in the search query 'q'.
        # if location:
        #     payload["location"] = location

        try:
            resp = await client.post(SERPER_URL, headers=headers, json=payload)
            if resp.status_code != 200:
                print(f"SERPER ERROR {resp.status_code}: {resp.text}")
            resp.raise_for_status()
            data = resp.json()
            # print(f"RECEIVED FROM SERPER: {len(data.get('organic', []))} results")

            for item in data.get("organic", []):
                company = _parse_company_result(item, query)
                if company:
                    # Apply location filter
                    if location and not _location_matches(
                        company.get("description", ""),
                        item.get("title", ""),
                        location
                    ):
                        continue  # Skip companies not actually in this location

                    companies.append(company)
                if len(companies) >= max_results:
                    break

        except httpx.HTTPError as e:
            print(f"[X-ray Search] Error: {e}")

    return companies


async def xray_find_decision_makers(
    company_name: str,
    roles: Optional[list[str]] = None
) -> list[dict]:
    """
    Find decision makers at a specific company using Google X-ray search via Serper.dev.
    Query: site:linkedin.com/in "company_name" ("CEO" OR "CTO" OR "Founder")
    """
    if roles is None:
        roles = ["CEO", "CTO", "Founder", "Co-Founder", "Head of", "VP", "Director", "COO", "CMO", "Hiring Manager"]

    role_query = " OR ".join([f'"{r}"' for r in roles])
    query = f'site:linkedin.com/in "{company_name}" ({role_query})'

    decision_makers = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json",
        }
        payload = {"q": query, "num": 10}

        try:
            resp = await client.post(SERPER_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("organic", []):
                dm = _parse_person_result(item, company_name)
                if dm:
                    decision_makers.append(dm)

        except httpx.HTTPError as e:
            print(f"[X-ray Search] Decision maker search error: {e}")

    return decision_makers


def _parse_company_result(item: dict, search_query: str) -> Optional[dict]:
    """Parse a Serper.dev search result into a company dict."""
    link = item.get("link", "")
    title = item.get("title", "")
    snippet = item.get("snippet", "")

    # Only accept linkedin.com/company URLs
    if "linkedin.com/company" not in link:
        return None

    # Extract company name from title
    name = re.split(r"\s*[\|–\-]\s*LinkedIn", title)[0].strip()
    if not name or name.lower() == "linkedin":
        return None

    # Try to extract location from snippet
    # LinkedIn snippets often have format: "Company. Industry. Location · followers"
    location = ""
    # Pattern 1: "City, State" or "City, Country" near the start
    loc_match = re.search(r"(?:headquartered in|located in|based in)\s+([^.]+)", snippet, re.IGNORECASE)
    if loc_match:
        location = loc_match.group(1).strip()
    else:
        # Pattern 2: LinkedIn format "Description. Industry. City, State"
        loc_match = re.search(r"[·]\s*([A-Za-z\s,]+?)(?:\s*[·]|\s*\d+\s*(?:followers|employees))", snippet)
        if loc_match:
            location = loc_match.group(1).strip()

    # Try to extract employee count
    employee_count = ""
    emp_match = re.search(r"(\d[\d,]*(?:\+)?)\s*(?:employees|followers|seguidores)", snippet, re.IGNORECASE)
    if emp_match:
        employee_count = emp_match.group(1)

    # Try to extract industry from snippet
    industry = ""
    industry_match = re.search(r"Industry:\s*([^·|.]+)", snippet)
    if industry_match:
        industry = industry_match.group(1).strip()

    return {
        "name": name,
        "linkedin_url": link,
        "description": snippet,
        "location": location,
        "employee_count": employee_count,
        "industry": industry,
        "website": "",
        "search_query": search_query,
    }


def _parse_person_result(item: dict, company_name: str) -> Optional[dict]:
    """Parse a Serper.dev search result into a decision maker dict."""
    link = item.get("link", "")
    title = item.get("title", "")
    snippet = item.get("snippet", "")

    if "linkedin.com/in" not in link:
        return None

    # Extract name and title from "John Doe - CEO at Company | LinkedIn"
    name = re.split(r"\s*[\|–\-]\s*LinkedIn", title)[0].strip()

    # Try to parse "Name - Title" format
    person_title = ""
    parts = name.split(" - ", 1)
    if len(parts) == 2:
        name = parts[0].strip()
        person_title = parts[1].strip()

    if not name:
        return None

    # Extract location from snippet
    location = ""
    loc_patterns = [
        r"^([A-Za-z\s,]+(?:Area|Region|Metro))",
        r"(?:Location|Based in)\s*[:·]\s*([^·|.]+)",
        r"Location:\s*([^.·]+)",
    ]
    for pattern in loc_patterns:
        loc_match = re.search(pattern, snippet)
        if loc_match:
            location = loc_match.group(1).strip()
            break

    return {
        "name": name,
        "title": person_title,
        "linkedin_url": link,
        "location": location,
        "snippet": snippet,
    }
