#!/usr/bin/env python3
import time, sys, os, re, json, html, calendar, pathlib, requests, feedparser
# Poll RSS feeds every 2 min
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "120"))

# WebEx Status Feeds
FEEDS = {
    "Webex App - Commercial":            "https://status.webex.com/Webex_App.rss",
    "Webex Calling - Commercial":        "https://status.webex.com/Webex_Calling.rss",
    "Webex Contact Center - Commercial": "https://status.webex.com/Webex_Contact_Center.rss",
    # Future -  could add government feeds, but I don't have a need for it at this point
    # Add any you'd like
}
TOKEN = os.environ["WEBEX_BOT_TOKEN"]
INC_ROOM  = os.environ["INC_NOTIFICATION_WEBEX_ROOM_ID"] # WebEx cloud incident notifications
SEC_ROOM = os.environ["CRIT_SEC_NOTIFICATION_WEBEX_ROOM_ID"] # Critical security notifications webex space
INC_STATE = pathlib.Path(os.environ.get("INC_STATE_FILE", "inc_seen.json"))
DEBUG = os.environ.get("DEBUG") == "1"          # DEBUG=1 prints parse results, posts nothing

STATUSES       = ("resolved","monitoring","identified","investigating",
                  "scheduled","in progress","verifying","completed","postmortem")
MAINT_STATUSES = {"scheduled","in progress","verifying","completed"}
EMOJI          = {"investigating":"🚨","identified":"🚨","monitoring":"👀","resolved":"✅"}

STATUS_RE = re.compile(r"(?i)\b(" + "|".join(STATUSES) + r")\b\s*-\s*")
TS_RE     = re.compile(r"[A-Z][a-z]{2}\s+\d{1,2},\s+\d{2}:\d{2}\s+UTC")

# Added this feature after WebEx Incident code was implemented
# ── Cisco PSIRT security advisories ─────────────────────────
# The advisory feed already carries the rating inline ("Security Impact Rating: Critical")
# and names the product in the title, so we filter straight from the XML — no API needed.
SEC_FEED  = os.environ.get("CISCO_FEED_URL",
    "https://sec.cloudapps.cisco.com/security/center/psirtrss20/CiscoSecurityAdvisory.xml")
SEC_STATE = pathlib.Path(os.environ.get("SEC_STATE_FILE", "sec_seen.json"))

CISCO_RATING = "critical"                                  # only post this Security Impact Rating
COLLAB_KEYWORDS = {                                        # tune to definition of "collaboration"
    "webex", "unified communications manager", "unified cm", "cucm",
    "unity connection", "im and presence", "expressway", "telepresence",
    "jabber", "finesse", "contact center",
    "uccx", "Cisco Unified Contact Center Enterprise", "pcce", "emergency responder",
}
SIR_RE = re.compile(r"Security Impact Rating:\s*(\w+)", re.I)


# ── Helpers ─────────────────────────────────────────────────
def strip_html(s):
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"[ \t]{2,}", " ", html.unescape(s)).strip()

def item_ts(e):
    t = e.get("updated_parsed") or e.get("published_parsed")
    return calendar.timegm(t) if t else 0

def post(room, markdown):
    requests.post("https://webexapis.com/v1/messages",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"roomId": room, "markdown": markdown}, timeout=20).raise_for_status()

def load_seen(path):
    return set(json.loads(path.read_text())) if path.exists() else set()

# ── Webex status incidents ──────────────────────────────────
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

def poll_webex_status_feed():
    seen      = set(json.loads(INC_STATE.read_text())) if INC_STATE.exists() else set()
    updated   = set(seen)
    first_run = not INC_STATE.exists()

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
                    print(f"[{service}] {tag} {title}  status={status!r}")
                    # print(f"[{service}] {tag} {title}\n  status={status!r} stamp={upd[0]!r}\n  body={upd[2][:160]!r}\n")
                else:
                    print(f"[{service}] {tag} {title}\n  (no status parsed)\n")
                continue

            # Can comment out 'or first_run' + delete inc_seen.json to post to room
            if is_maint or first_run:
                continue

            stamp, status, body = upd
            lines = [f"{EMOJI.get(status,'🔔')} **{service} — {status.title()}**", "", f"**{title}**"]
            reg = regions(e.get("summary", ""))
            if reg:
                lines.append(f"Regions: {reg}")
            # Add e.link to be able to view  Inc
            lines += ["", body, "", f"_{stamp}_", f"[View Incident]({e.link})"]
            post(INC_ROOM, "\n".join(lines))
            '''
                requests.post("https://webexapis.com/v1/messages",
                headers={"Authorization": f"Bearer {TOKEN}"},
                json={"roomId": INC_ROOM, "markdown": "\n".join(lines)}, timeout=20).raise_for_status()
            '''
    
    # Save the updated set of seen items, so it's not repeated
    if not DEBUG:
        INC_STATE.write_text(json.dumps(sorted(updated)))

# ── Cisco PSIRT advisories ──────────────────────────────────
def cisco_rating(e):
    """Security Impact Rating from the advisory text, lowercased (e.g. 'critical')."""
    m = SIR_RE.search(strip_html(e.get("summary", "")))
    return m.group(1).lower() if m else ""

def is_collab(e):
    text = (e.get("title", "") + " " + strip_html(e.get("summary", ""))).lower()
    return any(k in text for k in COLLAB_KEYWORDS)

def poll_cisco_advisories():
    if not SEC_ROOM:
        return                                  # not configured -> skip silently
    seen      = load_seen(SEC_STATE)
    updated   = set(seen)
    first_run = not SEC_STATE.exists()

    for e in feedparser.parse(SEC_FEED).entries:
        guid = e.get("id") or e.get("link")
        uid  = f"cisco:{guid}:{item_ts(e)}"     # re-post only when an advisory is revised
        if uid in seen and not DEBUG:           # already seen, skip
            continue
        # Check if any previous seen entry has the same guid (i.e. the advisory was revised)
        revised = any(s.startswith(f"cisco:{guid}:") for s in seen)
        updated.add(uid)

        rating = cisco_rating(e)
        match  = rating == CISCO_RATING and is_collab(e)

        if DEBUG:
            print(f"[Cisco PSIRT] {'POST' if match else 'skip'} "
                  f"rating={rating!r} collab={is_collab(e)}  {e.get('title','')} [View Advisory]({e.link})")
            continue

        if not match or first_run:              # seed silently on first run
            continue

        # add "Revised" to title if this advisory was previously seen
        tag = "🔄 (Revised) " if revised else ""
        lines = [
            f"**{tag} 🔴 Critical Cisco Security Advisory - (Collaboration)**", "",
            f"**{e.get('title','')}**",
            f"Security Impact Rating: {rating.title()}", "",
            f"_{e.get('published','')}_",
            f"[View Advisory]({e.link})",
        ]
        post(SEC_ROOM, "\n".join(lines))

    if not DEBUG:
        SEC_STATE.write_text(json.dumps(sorted(updated)))

if __name__ == "__main__":
    if DEBUG or "--once" in sys.argv:
        poll_webex_status_feed()
        poll_cisco_advisories( )
    else:
        print(f"Webex Inc Bot running; polling every {POLL_SECONDS}s", flush=True)
        while True:
            try:
                poll_webex_status_feed()
                poll_cisco_advisories()
            except Exception as ex:
                print(f"poll error: {ex}", file=sys.stderr, flush=True)
            time.sleep(POLL_SECONDS)
