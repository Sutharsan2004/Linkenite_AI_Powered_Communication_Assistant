import os
import re
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, timedelta
from imapclient import IMAPClient

FILTER_TERMS = ["support", "query", "request", "help"]

def load_from_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Normalize columns
    df.columns = [c.strip().lower() for c in df.columns]
    # Parse date if possible
    if "sent_date" in df.columns:
        try:
            df["sent_date"] = pd.to_datetime(df["sent_date"], infer_datetime_format=True, dayfirst=True)
        except Exception:
            pass
    return df

def filter_support_emails(df: pd.DataFrame) -> pd.DataFrame:
    def eligible(subj):
        if not isinstance(subj, str):
            return False
        s = subj.lower()
        return any(term in s for term in FILTER_TERMS)
    return df[df["subject"].apply(eligible)].copy()

def fetch_imap_emails(host: str, port: int, username: str, password: str, folder: str = "INBOX", since_days: int = 1) -> pd.DataFrame:
    msgs = []
    with IMAPClient(host, port=port, ssl=True) as server:
        server.login(username, password)
        server.select_folder(folder)
        since_date = (datetime.utcnow() - timedelta(days=since_days)).date()
        uids = server.search(['SINCE', since_date.strftime("%d-%b-%Y")])
        for uid, data in server.fetch(uids, ['ENVELOPE', 'RFC822.TEXT']).items():
            env = data.get(b'ENVELOPE')
            if not env:
                continue
            sender_addr = None
            if env.from_ and len(env.from_) > 0:
                addr = env.from_[0]
                sender_addr = f"{addr.mailbox.decode() if addr.mailbox else ''}@{addr.host.decode() if addr.host else ''}"
            subject = (env.subject or b'').decode(errors="ignore")
            date = env.date
            body = (data.get(b'RFC822.TEXT') or b'').decode(errors="ignore")
            msgs.append({
                "sender": sender_addr,
                "subject": subject,
                "body": body,
                "sent_date": date
            })
    return pd.DataFrame(msgs)
