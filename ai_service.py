import json
import re
import httpx
from .config import OPENAI_API_KEY, OPENAI_MODEL

CATEGORIES = [
    "Royalty & Payments", "ISBN & Metadata Issues", "Printing & Quality",
    "Distribution & Availability", "Book Status & Production Updates", "General Inquiry"
]
KB = '''
BookLeaf Publishing operates in India and the US. Publishing packages include Standard Free and Bestseller Breakthrough.
Royalty: author receives 80% of net profit; net profit is MRP minus printing cost, platform commission and shipping.
Royalties are calculated quarterly and paid within 45 days after quarter end. Minimum payout is ₹1,000; smaller balances roll over.
Payouts use the bank account linked in the author dashboard. Detailed platform-wise breakdown is available in the dashboard.
ISBN: BookLeaf assigns a unique ISBN under its publisher imprint. Author-owned imprint ISBNs must be obtained independently.
Duplicate or wrong ISBN is high priority and should be escalated to production with a 48-hour follow-up.
Printing: normal turnaround is 5–7 business days from order confirmation. Verified misprints, binding defects or color inconsistency qualify for free reprint; request photos.
Distribution: listings include Amazon India, Flipkart, Amazon US, Amazon UK and BookLeaf Store. Listings typically go live 7–10 business days after publication. Stock sync can take 24–48 hours.
Production stages: Manuscript Received, Editing (if opted), Cover Design, Typesetting, Proofreading, ISBN Assignment, Printing, Distribution Setup, Published & Live.
Tone: empathetic, professional, specific, honest; own BookLeaf errors; give a clear next step and do not invent facts or dates.
'''

def fallback_classify(text: str):
    t = text.lower()
    if any(w in t for w in ["royalt", "payment", "payout", "paid", "bank", "earning"]):
        cat = "Royalty & Payments"
    elif any(w in t for w in ["isbn", "metadata", "description", "author bio", "book title"]):
        cat = "ISBN & Metadata Issues"
    elif any(w in t for w in ["print", "binding", "blurry", "misprint", "quality", "pages"]):
        cat = "Printing & Quality"
    elif any(w in t for w in ["amazon", "unavailable", "distribution", "listing", "stock"]):
        cat = "Distribution & Availability"
    elif any(w in t for w in ["production", "typesetting", "cover", "proofread", "publication", "status", "delay"]):
        cat = "Book Status & Production Updates"
    else:
        cat = "General Inquiry"
    urgent = any(w in t for w in ["wrong isbn", "duplicate isbn", "six months", "6 months", "overdue", "not received", "defective", "misprint", "urgent"])
    high = any(w in t for w in ["royalty", "payment", "isbn", "quality", "defect", "unavailable"])
    priority = "Critical" if any(w in t for w in ["legal", "fraud", "safety", "critical"]) else ("High" if urgent or high else ("Low" if any(w in t for w in ["bio", "update my bio", "minor change"]) else "Medium"))
    return {"category": cat, "priority": priority, "rationale": "Rule-based fallback classification; admin should verify before sending."}

async def _llm_json(prompt: str):
    if not OPENAI_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={"model": OPENAI_MODEL, "temperature": 0.2, "response_format": {"type": "json_object"},
                      "messages": [{"role":"system","content":"You are a careful BookLeaf support assistant. Use only supplied facts. Never invent dates, statuses, payments or actions. Return valid JSON."},
                                   {"role":"user","content":prompt}]}
            )
            r.raise_for_status()
            return json.loads(r.json()["choices"][0]["message"]["content"])
    except Exception:
        return None

async def classify(subject: str, description: str):
    fallback = fallback_classify(subject + " " + description)
    result = await _llm_json(
        f"Classify this ticket. category must be one of {CATEGORIES}; priority one of Critical, High, Medium, Low. Return JSON keys category, priority, rationale.\\nSubject: {subject}\\nDescription: {description}"
    )
    if result and result.get("category") in CATEGORIES and result.get("priority") in ["Critical","High","Medium","Low"]:
        return result
    return fallback

async def draft_reply(subject: str, description: str, book_context: str = ""):
    fallback = (
        "Hello,\\n\\nThank you for reaching out. I understand your concern and am sorry for the inconvenience. "
        "Our team will review the details of your query against your book and account records. "
        "We will follow up with the relevant update as soon as the review is complete.\\n\\n"
        "Next step: please share any relevant supporting details in this ticket, and our team will investigate.\\n\\n"
        "Regards,\\nBookLeaf Author Support"
    )
    result = await _llm_json(
        f"Draft a concise empathetic BookLeaf support response. Use the policy below and only the verified context. Do not claim an action has already been taken. If information is missing, say it will be checked. End with a clear next step. Return JSON with a single string key named draft.\nPOLICY:\n{KB}\nBOOK CONTEXT:\n{book_context}\nSUBJECT: {subject}\nQUERY: {description}"
    )
    if result and isinstance(result.get("draft"), str) and len(result["draft"]) > 20:
        return result["draft"]
    return fallback
