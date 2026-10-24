import base64
import re
from email.utils import parseaddr

from bs4 import BeautifulSoup

URL_RE = re.compile(r"https?://[^\s\"'<>)]+", re.I)
SHORTENERS = {"bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd", "cutt.ly", "rebrand.ly"}


def _decode(data: str) -> str:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")


def _walk(part, out):
    for p in part.get("parts", []) or []:
        _walk(p, out)
    body = part.get("body", {})
    mime = part.get("mimeType", "")
    if body.get("data"):
        if mime == "text/plain":
            out["plain"].append(_decode(body["data"]))
        elif mime == "text/html":
            out["html"].append(_decode(body["data"]))
    if part.get("filename"):
        out["attachments"].append(part["filename"])


def _html_to_text(html: str):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    links = [a["href"] for a in soup.find_all("a", href=True) if a["href"].startswith("http")]
    return soup.get_text(" ", strip=True), links


def _domain(addr: str) -> str:
    return addr.split("@")[-1].lower() if "@" in addr else ""


def parse_message(msg: dict) -> dict:
    payload = msg.get("payload", {})
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}

    out = {"plain": [], "html": [], "attachments": []}
    _walk(payload, out)

    links = []
    if out["plain"]:
        text = "\n".join(out["plain"])
    else:
        text, links = _html_to_text("\n".join(out["html"]))
    links += URL_RE.findall(text)
    links = list(dict.fromkeys(links))

    from_name, from_addr = parseaddr(headers.get("from", ""))
    _, reply_addr = parseaddr(headers.get("reply-to", ""))
    auth = headers.get("authentication-results", "").lower()

    sender_domain = _domain(from_addr)
    link_domains = {re.sub(r"^https?://([^/:?#]+).*", r"\1", l).lower() for l in links}

    return {
        "id": msg["id"],
        "sender": from_addr or headers.get("from", ""),
        "sender_name": from_name,
        "subject": headers.get("subject", "(no subject)"),
        "date": headers.get("date", ""),
        "snippet": msg.get("snippet", ""),
        "text": text.strip(),
        "links": links,
        "flags": {
            "auth_fail": any(f"{k}=fail" in auth for k in ("spf", "dkim", "dmarc")),
            "reply_to_mismatch": bool(reply_addr) and _domain(reply_addr) != sender_domain,
            "shortened_link": bool(link_domains & SHORTENERS),
            "has_attachment": bool(out["attachments"]),
            "many_links": len(links) > 10,
        },
    }
