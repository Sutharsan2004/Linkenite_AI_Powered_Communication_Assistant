import os
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Any

from storage import init_db, insert_email, list_emails, update_email_status, update_ai_response
from email_processing import load_from_csv, filter_support_emails, fetch_imap_emails
from models import classify_sentiment, generate_reply_with_openai, fallback_template_reply
from extraction import extract_info
from priority import compute_priority
from rag import SimpleRAG

import matplotlib.pyplot as plt

load_dotenv()
init_db()

st.set_page_config(page_title="AI-Powered Communication Assistant", layout="wide")

st.title("📬 AI-Powered Communication Assistant")

with st.sidebar:
    st.header("Ingestion Settings")
    data_src = st.selectbox("Source", ["CSV (demo)", "IMAP mailbox"])
    csv_path = st.text_input("CSV path", value="sample_data.csv")
    enable_imap = os.getenv("ENABLE_IMAP", "false").lower() == "true"
    st.caption("IMAP is configured via .env; set ENABLE_IMAP=true to enable.")
    if data_src == "IMAP mailbox" and not enable_imap:
        st.warning("IMAP disabled. Set ENABLE_IMAP=true in .env to enable.")
    if st.button("Ingest Now"):
        if data_src == "CSV (demo)":
            df = load_from_csv(csv_path)
        else:
            if not enable_imap:
                st.error("IMAP not enabled.")
                st.stop()
            df = fetch_imap_emails(
                host=os.getenv("IMAP_HOST","imap.gmail.com"),
                port=int(os.getenv("IMAP_PORT","993")),
                username=os.getenv("IMAP_USERNAME",""),
                password=os.getenv("IMAP_PASSWORD",""),
                folder=os.getenv("IMAP_FOLDER","INBOX"),
                since_days=int(os.getenv("IMAP_SEARCH_SINCE_DAYS","1"))
            )
        df = filter_support_emails(df)
        if df.empty:
            st.info("No eligible support emails found.")
        else:
            st.success(f"Ingested {len(df)} email(s). Processing...")
            rag = SimpleRAG(kb_path="kb")
            for _, row in df.iterrows():
                sender = row.get("sender","")
                subject = row.get("subject","")
                body = row.get("body","")
                sent_date = row.get("sent_date", datetime.utcnow())
                sent_date = pd.to_datetime(sent_date, errors="coerce") or datetime.utcnow()

                sentiment = classify_sentiment((subject + "\n" + body)[:4000])
                priority_label, priority_score = compute_priority(subject, body, sentiment)
                extracted = extract_info(f"{subject}\n{body}")
                # RAG retrieve
                contexts = rag.retrieve(f"{subject}\n{body}", k=4)
                kb_text = "\n\n".join([c[0] for c in contexts])

                # Build prompt
                prompt = f"""
You are a customer support AI. Craft a concise, empathetic reply.
Context from knowledge base (may include policies, product info, troubleshooting):
---
{kb_text}
---

Sender: {sender}
Subject: {subject}
Email body:
{body}

Requirements:
- Professional, friendly tone
- Acknowledge any frustration if applicable
- Reference relevant product/policy info from the context
- Provide next steps and set expectations (SLA if urgent)
- Keep to 8-12 sentences maximum
"""
                ai_text = generate_reply_with_openai(prompt)
                if not ai_text:
                    # Fallback guidance based on extracted topics
                    guidance = "- We'll verify your access and role permissions.\n"
                    if "billing" in " ".join(extracted.get("mentioned_topics", [])):
                        guidance += "- We'll audit the invoice IDs and initiate a refund if applicable within 5 business days.\n"
                    if "api" in " ".join(extracted.get("mentioned_topics", [])):
                        guidance += "- We'll share API/CRM integration details and best practices.\n"
                    if "latency" in " ".join(extracted.get("mentioned_topics", [])):
                        guidance += "- We'll check regional status and suggest retries with backoff if needed.\n"
                    ai_text = fallback_template_reply(
                        customer_name=sender.split("@")[0] if sender else "",
                        subject=subject,
                        body_summary=body[:200].strip().replace("\n"," "),
                        guidance=guidance.strip()
                    )

                rec = {
                    "sender": sender,
                    "subject": subject,
                    "body": body,
                    "sent_date": str(sent_date),
                    "sentiment": sentiment,
                    "priority": priority_label,
                    "priority_score": float(priority_score),
                    "extracted_json": json.dumps(extracted),
                    "ai_response": ai_text,
                    "status": "pending"
                }
                insert_email(rec)
            st.success("Processing complete. See the dashboard below.")

# Main dashboard
col1, col2 = st.columns([2,1])

with col1:
    st.subheader("📥 Incoming Support Emails (prioritized)")
    rows = list_emails(order_by_priority=True)
    if not rows:
        st.info("No emails found yet. Use the sidebar to ingest.")
    else:
        for r in rows:
            with st.expander(f"#{r['id']} | {r['priority']} | {r['subject']}  — from {r['sender']}"):
                st.markdown(f"**Received:** {r['sent_date']}  |  **Sentiment:** {r['sentiment']}  |  **Status:** {r['status']}")
                st.write(r['body'])
                extracted = json.loads(r['extracted_json'] or "{}")
                st.markdown("**Extracted Info**")
                st.json(extracted)
                st.markdown("**AI Draft Reply (editable before sending)**")
                ai_text = st.text_area(f"ai_reply_{r['id']}", value=r['ai_response'], height=220)
                save, resolve = st.columns(2)
                with save:
                    if st.button(f"Save Draft #{r['id']}", key=f"save_{r['id']}"):
                        update_ai_response(r['id'], ai_text)
                        st.success("Draft saved.")
                with resolve:
                    if st.button(f"Mark Resolved #{r['id']}", key=f"resolve_{r['id']}"):
                        update_email_status(r['id'], "resolved")
                        st.success("Marked as resolved.")

with col2:
    st.subheader("📊 Analytics (last 24h snapshot)")
    rows = list_emails(order_by_priority=False)
    if rows:
        df = pd.DataFrame(rows)
        # Basic counts
        total = len(df)
        pending = int((df['status'] == 'pending').sum())
        resolved = int((df['status'] == 'resolved').sum())
        urgent = int((df['priority'] == 'Urgent').sum())
        st.metric("Total emails", total)
        st.metric("Urgent", urgent)
        st.metric("Resolved", resolved)
        st.metric("Pending", pending)

        # Sentiment distribution (matplotlib)
        fig = plt.figure()
        df['sentiment'].value_counts().plot(kind='bar', title='Sentiment Distribution')
        st.pyplot(fig)

        # Priority distribution
        fig2 = plt.figure()
        df['priority'].value_counts().plot(kind='bar', title='Priority Distribution')
        st.pyplot(fig2)
    else:
        st.info("No data yet. Ingest to see analytics.")
