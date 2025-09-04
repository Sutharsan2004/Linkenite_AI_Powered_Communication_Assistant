import re
from typing import Dict, Any, List

EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
PHONE_REGEX = r"(?:\+?\d{1,3}[- ]?)?(?:\(?\d{2,4}\)?[- ]?)?\d{3,4}[- ]?\d{4}"
PRODUCT_KEYWORDS = ["dashboard", "api", "crm", "billing", "latency", "orders"]

def extract_info(text: str) -> Dict[str, Any]:
    emails = re.findall(EMAIL_REGEX, text, flags=re.IGNORECASE)
    phones = re.findall(PHONE_REGEX, text)
    lower = text.lower()
    mentioned = [k for k in PRODUCT_KEYWORDS if k in lower]
    sentiment_indicators = {
        "negative": any(w in lower for w in ["cannot", "can't", "error", "critical", "discrepancy", "billed twice", "latency", "forbidden"]),
        "positive": any(w in lower for w in ["thank you", "appreciate", "great", "awesome"])
    }
    return {
        "emails_found": list(set(emails)),
        "phones_found": list(set(phones)),
        "mentioned_topics": mentioned,
        "sentiment_indicators": sentiment_indicators
    }
