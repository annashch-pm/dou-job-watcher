import os
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

RSS_URL = "https://jobs.dou.ua/vacancies/feeds/?category=Project%20Manager"
SEEN_FILE = "seen_jobs.json"

EXCLUDE_WORDS = [
    "junior",
    "trainee",
    "intern",
    "internship",
]


def get_jobs():
    req = urllib.request.Request(
        RSS_URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    jobs = []

    for item in root.findall(".//item"):
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()

        if title and link:
            jobs.append({
                "title": title,
                "link": link
            })

    return jobs


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()

    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f))


def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, ensure_ascii=False, indent=2)


def should_send(job):
    title = job["title"].lower()
    return not any(word in title for word in EXCLUDE_WORDS)


def send_telegram(job):
    message = (
        f"🆕 New DOU vacancy\n\n"
        f"{job['title']}\n\n"
        f"{job['link']}"
    )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": message,
        "disable_web_page_preview": "false"
    }).encode()

    with urllib.request.urlopen(url, data=data, timeout=30) as response:
        response.read()


jobs = get_jobs()
seen = load_seen()

if not seen:
    save_seen({job["link"] for job in jobs})
    print(f"First run: saved {len(jobs)} existing vacancies.")
    raise SystemExit


new_jobs = [job for job in jobs if job["link"] not in seen]

sent = 0
excluded = 0

for job in reversed(new_jobs):
    if should_send(job):
        send_telegram(job)
        sent += 1
        print(f"Sent: {job['title']}")
    else:
        excluded += 1
        print(f"Excluded: {job['title']}")

    seen.add(job["link"])


save_seen(seen)

print(
    f"Found {len(new_jobs)} new vacancies. "
    f"Sent {sent}. Excluded {excluded}."
)
