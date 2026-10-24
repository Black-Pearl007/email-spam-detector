from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CREDENTIALS_FILE = ROOT / "credentials.json"   # downloaded from Google Cloud (keep private)
TOKEN_FILE = ROOT / "token.json"               # created after your first sign-in (keep private)
MODEL_DIR = ROOT / "models" / "email-spam-distilbert"  # unzip the Colab model here
DB_PATH = ROOT / "emails.db"

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]  # read-only, cannot modify or delete mail
GMAIL_QUERY = "in:inbox newer_than:2d"
MAX_PER_POLL = 25
POLL_SECONDS = 30
SPAM_THRESHOLD = 0.5
