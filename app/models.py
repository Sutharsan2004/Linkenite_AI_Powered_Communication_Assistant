import os
from typing import Optional
from transformers import pipeline
from openai import OpenAI

# Sentiment pipeline (binary) – simple, fast
_sentiment = None
def get_sentiment_pipeline():
    global _sentiment
    if _sentiment is None:
        _sentiment = pipeline("sentiment-analysis")
    return _sentiment

def classify_sentiment(text: str) -> str:
    pipe = get_sentiment_pipeline()
    try:
        res = pipe(text[:4000])[0]
        # Map to Positive/Negative/Neutral (SST-2 is binary, emulate neutral threshold)
        label = res["label"]  # POSITIVE or NEGATIVE
        score = res["score"]
        if score < 0.7:
            return "Neutral"
        return "Positive" if label.upper().startswith("POS") else "Negative"
    except Exception:
        return "Neutral"

def generate_reply_with_openai(prompt: str, model: Optional[str] = None) -> Optional[str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    try:
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful, empathetic customer support assistant. Keep replies concise and professional."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return None

def fallback_template_reply(customer_name: str, subject: str, body_summary: str, guidance: str) -> str:
    return f"""Hi {customer_name or 'there'},

Thanks for reaching out regarding "{subject}". We understand the importance of this and we’re here to help.

Summary of your issue:
- {body_summary}

What we’ll do next:
{guidance}

If anything is urgent or if we missed context, please reply to this email and we’ll prioritize immediately.

Best regards,
Support Team
"""
