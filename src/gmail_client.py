from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import CREDENTIALS_FILE, TOKEN_FILE, SCOPES


def get_service():
    """Sign in via the browser the first time; reuse token.json afterwards."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    "credentials.json not found. See the 'Gmail setup' section in README.md."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def list_message_ids(service, query, max_results):
    resp = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    return [m["id"] for m in resp.get("messages", [])]


def get_message(service, msg_id):
    return service.users().messages().get(userId="me", id=msg_id, format="full").execute()
