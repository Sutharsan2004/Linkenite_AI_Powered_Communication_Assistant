# AI-Powered Communication Assistant (Hackathon Round 1)

End-to-end solution to ingest support emails, prioritize, extract key info, draft AI responses with RAG, and visualize everything on a dashboard.

Demo Video - https://drive.google.com/drive/folders/1Fv6i13Pd7Ak_XWYcSbFWat89k54a89XE?usp=drive_link

## 🧩 Features
- **Email Retrieval**: CSV demo or IMAP (Gmail/Outlook) via .env.
- **Filtering**: Subject contains "Support", "Query", "Request", "Help".
- **Categorization**: Sentiment (Positive/Negative/Neutral) + Priority (Urgent/Not urgent).
- **Priority Queue**: Urgent items bubble to the top using a heuristic score.
- **Information Extraction**: Emails, phone numbers, topics, sentiment indicators.
- **RAG + LLM Draft Replies**: Retrieves KB context (FAISS + sentence-transformers) and generates replies via OpenAI. Falls back to a rule-based template if no API key.
- **Dashboard**: Streamlit UI with list view, editable AI drafts, status updates, and analytics (counts + bar charts).
- **Storage**: SQLite (`aica.db`).

## 🗂 Project Structure
```
aica-assistant/
├── app/
│   ├── app.py                 # Streamlit app
│   ├── storage.py             # SQLite helpers
│   ├── email_processing.py    # CSV/IMAP ingestion + filtering
│   ├── models.py              # Sentiment + LLM helpers
│   ├── extraction.py          # Info extraction (emails/phones/topics)
│   ├── priority.py            # Priority scoring
│   └── rag.py                 # FAISS-based retriever
├── kb/
│   ├── products.md
│   └── policies.md
├── sample_data.csv
├── requirements.txt
├── .env.sample
└── README.md
```

## 🚀 Quick Start
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt

# Optional: create .env from sample
cp .env.sample .env
# add your OPENAI_API_KEY to enable LLM replies (fallback works without)

# Run
streamlit run app/app.py
```

