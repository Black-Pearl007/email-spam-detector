"""Live dashboard.  Run:  streamlit run app.py   (while `python -m src.fetcher` runs in another terminal)"""
import json

import pandas as pd
import streamlit as st

from src import db
from src.config import SPAM_THRESHOLD

st.set_page_config(page_title="Live Email Spam Detector", layout="wide")
st.title("Live Email Spam Detector")

db.init()
threshold = st.sidebar.slider("Spam threshold", 0.05, 0.99, SPAM_THRESHOLD, 0.05)
refresh = st.sidebar.number_input("Auto-refresh (seconds)", 5, 120, 10)
st.sidebar.caption("Higher threshold = fewer real emails wrongly flagged, but more spam gets through.")


@st.fragment(run_every=int(refresh))
def dashboard():
    rows = db.recent()
    if not rows:
        st.info("No emails yet. Start the fetcher:  python -m src.fetcher")
        return

    df = pd.DataFrame(rows)
    df["is_spam"] = df["spam_prob"] >= threshold
    c1, c2, c3 = st.columns(3)
    c1.metric("Emails scanned", len(df))
    c2.metric("Flagged as spam", int(df["is_spam"].sum()))
    c3.metric("Latest", df["processed_at"].iloc[0])

    view = st.radio("Show", ["All", "Spam only", "Not spam"], horizontal=True)
    if view == "Spam only":
        df = df[df["is_spam"]]
    elif view == "Not spam":
        df = df[~df["is_spam"]]

    for _, r in df.iterrows():
        icon = "🔴" if r["is_spam"] else "🟢"
        with st.expander(f"{icon} {r['spam_prob']:.0%}  |  {r['subject'][:70]}  |  {r['sender']}"):
            st.progress(float(r["spam_prob"]))
            st.write(r["snippet"])
            flags = [k.replace("_", " ") for k, v in json.loads(r["flags"]).items() if v]
            if flags:
                st.warning("Suspicious signals: " + ", ".join(flags))
            links = json.loads(r["links"])
            if links:
                st.caption("Links (do not click): " + "  ".join(links[:5]))
            b1, b2, _ = st.columns([1, 1, 6])
            if b1.button("Correct", key=f"ok_{r['id']}"):
                db.set_feedback(r["id"], "correct")
            if b2.button("Wrong", key=f"bad_{r['id']}"):
                db.set_feedback(r["id"], "wrong")
            if r["feedback"]:
                st.caption(f"Feedback saved: {r['feedback']}")


dashboard()
