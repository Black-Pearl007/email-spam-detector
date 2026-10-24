"""Polls Gmail, classifies new mail, stores results.

Run:  python -m src.fetcher          (loop forever)
      python -m src.fetcher --once   (single pass)
"""
import argparse
import time

from . import db
from .classifier import SpamClassifier
from .config import GMAIL_QUERY, MAX_PER_POLL, MODEL_DIR, POLL_SECONDS, SPAM_THRESHOLD
from .email_parser import parse_message
from .gmail_client import get_message, get_service, list_message_ids


def poll_once(service, clf):
    seen = db.seen_ids()
    new = [i for i in list_message_ids(service, GMAIL_QUERY, MAX_PER_POLL) if i not in seen]
    for msg_id in new:
        parsed = parse_message(get_message(service, msg_id))
        result = clf.predict(parsed["subject"], parsed["text"])
        db.save(parsed, result)
        print(f"[{result['label'].upper():4}] {result['spam_prob']:.2f}  {parsed['sender'][:35]:35}  {parsed['subject'][:50]}")
    return len(new)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    if not MODEL_DIR.exists():
        raise SystemExit(f"Model not found at {MODEL_DIR}. Unzip the model saved from Colab there.")

    db.init()
    clf = SpamClassifier(MODEL_DIR, SPAM_THRESHOLD)
    service = get_service()
    print("Connected to Gmail (read-only). Watching for new mail...")

    while True:
        poll_once(service, clf)
        if args.once:
            break
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
