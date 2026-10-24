#!/usr/bin/env python3
"""Print feed items not seen before and newer than MAX_AGE_DAYS. Playbook: agents/news-watch.md."""
import concurrent.futures, email.utils, pathlib, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

SEEN = pathlib.Path(__file__).parent / "seen.txt"
MAX_AGE_DAYS = 3
A = "{http://www.w3.org/2005/Atom}"

def gnews(q, gl="US"):
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": q + " when:2d", "hl": "en-US", "gl": gl, "ceid": f"{gl}:en"})

# One entry per watch-list topic: a Google News query (gnews("<query>", "<country code>")) or any RSS/Atom URL.
FEEDS = {
    # Daily item: AI and agents
    "claude-code-releases": "https://github.com/anthropics/claude-code/releases.atom",
    "ai-agents": gnews('"AI agents" OR "coding agent" OR OpenAI OR Anthropic OR "Google DeepMind" (launches OR releases OR announces)'),
}

def fetch(name, url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
    except Exception as e:
        return name, [], str(e)
    out = []
    for it in root.iter():
        if it.tag == "item":
            title, link, date = it.findtext("title"), it.findtext("link"), it.findtext("pubDate")
        elif it.tag == A + "entry":
            title, date = it.findtext(A + "title"), it.findtext(A + "updated")
            link = (it.find(A + "link") if it.find(A + "link") is not None else {}).get("href")
        else:
            continue
        out.append(((title or "").strip(), (link or "").strip(), date or ""))
    return name, out, None

def age_days(date):
    try:
        ts = email.utils.parsedate_to_datetime(date).timestamp()
    except Exception:
        try:
            ts = time.mktime(time.strptime(date[:19], "%Y-%m-%dT%H:%M:%S"))
        except Exception:
            return 0
    return (time.time() - ts) / 86400

seen = set(SEEN.read_text().split("\n")) if SEEN.exists() else set()
new = []
with concurrent.futures.ThreadPoolExecutor(8) as ex:
    for name, items, err in ex.map(lambda kv: fetch(*kv), FEEDS.items()):
        if err:
            print(f"! {name}: {err}", file=sys.stderr)
        for title, link, date in items:
            if link and link not in seen and age_days(date) <= MAX_AGE_DAYS:
                seen.add(link)
                new.append(link)
                print(f"[{name}] {title} | {date[:16]} | {link}")
with SEEN.open("a") as f:
    f.writelines(l + "\n" for l in new)
