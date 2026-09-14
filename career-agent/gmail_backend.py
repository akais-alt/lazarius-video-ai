import os
import base64
from email.message import EmailMessage
from email.utils import parseaddr
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify", "https://www.googleapis.com/auth/gmail.send"]

def gmail_service():
    client_id = os.environ.get("GMAIL_CLIENT_ID")
    client_secret = os.environ.get("GMAIL_CLIENT_SECRET")
    refresh_token = os.environ.get("GMAIL_REFRESH_TOKEN")
    if not all([client_id, client_secret, refresh_token]):
        return None
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=GMAIL_SCOPES,
    )
    return build("gmail", "v1", credentials=creds, cache_discovery=False)

def _attachment(filename, content_b64):
    data = base64.b64decode(content_b64)
    return filename, data

def send_gmail(to, subject, body):
    service = gmail_service()
    if not service or not to:
        return False
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    sender = os.environ.get("GMAIL_USER_EMAIL")
    if sender:
        msg["From"] = sender
    msg.set_content(body)
    for env_name, filename in [
        ("CV_BASE64", "CV_Siaka_Kamagate.pdf"),
        ("LETTER_BASE64", "Lettre_Motivation_Siaka_Kamagate.pdf"),
    ]:
        raw = os.environ.get(env_name)
        if raw:
            name, data = _attachment(filename, raw)
            msg.add_attachment(data, maintype="application", subtype="pdf", filename=name)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return True

def read_inbox(max_results=20):
    service = gmail_service()
    if not service:
        return []
    result = service.users().messages().list(userId="me", q="in:anywhere newer_than:2d", maxResults=max_results).execute()
    messages = []
    for item in result.get("messages", []):
        m = service.users().messages().get(userId="me", id=item["id"], format="metadata", metadataHeaders=["From", "Subject", "Date"]).execute()
        headers = {h["name"].lower(): h["value"] for h in m.get("payload", {}).get("headers", [])}
        messages.append({
            "id": item["id"],
            "sender": parseaddr(headers.get("from", ""))[1],
            "subject": headers.get("subject", ""),
            "received_at": headers.get("date", ""),
            "snippet": m.get("snippet", ""),
        })
    return messages
