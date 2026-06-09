#!/usr/bin/env python3
import os, re, json, html, calendar, pathlib, requests, feedparser

FEEDS = {
    "Webex App":            "https://status.webex.com/Webex_App.rss",
    "Webex Calling":        "https://status.webex.com/Webex_Calling.rss",
    "Webex Contact Center": "https://status.webex.com/Webex_Contact_Center.rss",
}
TOKEN = os.environ["WEBEX_BOT_TOKEN"]
ROOM  = os.environ["WEBEX_ROOM_ID"]
STATE = pathlib.Path(os.environ.get("STATE_FILE", "seen.json"))
DEBUG = os.environ.get("DEBUG") == "1"          # DEBUG=1 prints parse results, posts nothing

STATUSES       = ("resolved","monitoring","identified","investigating",
                  "scheduled","in progress","verifying","completed","postmortem")
MAINT_STATUSES = {"scheduled","in progress","verifying","completed"}
EMOJI          = {"investigating":"🚨","identified":"🚨","monitoring":"👀","resolved":"✅"}

STATUS_RE = re.compile(r"(?i)\b(" + "|".join(STATUSES) + r")\b\s*-\s*")
TS_RE     = re.compile(r"[A-Z][a-z]{2}\s+\d{1,2},\s+\d{2}:\d{2}\s+UTC")

def strip_html(s):
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"[ \t]{2,}", " ", html.unescape(s)).strip()

def latest_update(summary_html):
    """(timestamp, status, body) for the newest update only, or None."""
    text = strip_html(summary_html)
    m = STATUS_RE.search(text)                  # first status keyword = newest update
    if not m:
        return None
    status = m.group(1).lower()
    rest   = text[m.end():]
    ts     = TS_RE.search(rest)                 # body ends at the first timestamp
    body   = rest[:ts.start()].strip() if ts else rest.strip()
    stamp  = ts.group(0) if ts else ""
    return stamp, status, body

def regions(summary_html):
    pre = strip_html(summary_html)
    cut = STATUS_RE.search(pre)                 # regions live in the preamble, before updates
    if cut:
        pre = pre[:cut.start()]
    m = re.search(r"Regions:\s*(.+?)\s*(?:Change\s*#|Component\s+Status|$)", pre)
    return m.group(1).strip(" ,-") if m else ""

def item_ts(e):
    t = e.get("updated_parsed") or e.get("published_parsed")
    return calendar.timegm(t) if t else 0

seen      = set(json.loads(STATE.read_text())) if STATE.exists() else set()
updated   = set(seen)
first_run = not STATE.exists()

for service, url in FEEDS.items():
    for e in feedparser.parse(url).entries:
        guid = e.get("id") or e.get("link")
        uid  = f"{service}:{guid}:{item_ts(e)}"
        if uid in seen and not DEBUG:
            continue
        updated.add(uid)

        upd      = latest_update(e.get("summary", ""))
        status   = upd[1] if upd else ""
        title    = e.get("title", "")
        is_maint = "maintenance" in title.lower() or status in MAINT_STATUSES

        if DEBUG:
            tag = "MAINT(skip)" if is_maint else "POST"
            if upd:
                print(f"[{service}] {tag} {title}\n  status={status!r} stamp={upd[0]!r}\n  body={upd[>
            else:
                print(f"[{service}] {tag} {title}\n  (no status parsed)\n")
            continue

        # Can comment out 'or first_run' + delete seed.json to post to room
        if is_maint or first_run:
            continue

        stamp, status, body = upd
        lines = [f"{EMOJI.get(status,'🔔')} **{service} — {status.title()}**", "", f"**{title}**"]
        reg = regions(e.get("summary", ""))
        if reg:
            lines.append(f"Regions: {reg}")
        # Add e.link to be able to view  Inc
        lines += ["", body, "", f"_{stamp}_", f"[View Incident]({e.link})"]
        requests.post("https://webexapis.com/v1/messages",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={"roomId": ROOM, "markdown": "\n".join(lines)}, timeout=20).raise_for_status()

if not DEBUG:
    STATE.write_text(json.dumps(sorted(updated)))
