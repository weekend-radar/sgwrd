import json
import re
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup


def load_channels() -> list[str]:
    with open("channels.json", "r", encoding="utf-8") as f:
        return json.load(f)


def extract_photo_url(wrap) -> str:
    # Check CSS background-image on .tgme_widget_message_photo_wrap
    photo_wrap = wrap.select_one(".tgme_widget_message_photo_wrap")
    if photo_wrap:
        style = photo_wrap.get("style", "")
        match = re.search(r"background-image\s*:\s*url\(['\"]?(.*?)['\"]?\)", style, re.IGNORECASE)
        if match:
            return match.group(1)

    # Fallback: check for an <img> inside photo/media containers
    img = wrap.select_one(".tgme_widget_message_photo img, .tgme_widget_message_photo_wrap img")
    if img and img.get("src"):
        return img["src"]

    return ""


def parse_post(wrap, channel: str) -> dict | None:
    msg_el = wrap.select_one(".tgme_widget_message_text")
    if not msg_el:
        return None

    for br in msg_el.find_all("br"):
        br.replace_with("\n")

    raw_text = msg_el.get_text()
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return None

    post_attr = wrap.get("data-post", "")
    post_url = f"https://t.me/{post_attr}" if post_attr else f"https://t.me/s/{channel}"

    time_el = wrap.select_one("time[datetime]")
    posted_at = time_el["datetime"] if time_el else ""

    headline = lines[0]
    category = "General"
    cat_match = re.match(r"^\[([^\]]+)\]\s*(.*)", headline)
    if cat_match:
        category = cat_match.group(1).strip()
        headline = cat_match.group(2).strip()

    date_info = ""
    time_info = ""
    location = ""
    external_link = ""
    bullets = []

    clock_icons = (
        "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚", "🕛",
        "🕣", "🕤", "🕥", "🕦", "🕧"
    )

    for line in lines[1:]:
        if line.startswith("📆"):
            date_info = line.lstrip("📆").strip()
        elif line[0] in clock_icons:
            time_info = line[1:].strip()
        elif line.startswith("📍"):
            location = line.lstrip("📍").strip()
        elif line.startswith("👉"):
            for a in msg_el.find_all("a", href=True):
                if "t.me/" not in a["href"] and not a["href"].startswith("?"):
                    external_link = a["href"]
                    break
        elif not line.startswith((f"@{channel}", "#")):
            bullets.append(line)

    full_lower = raw_text.lower()
    is_free = any(
        w in full_lower
        for w in ["free entry", "free admission", "freebies", "free gift", "complimentary", "free "]
    )
    is_weekend = any(
        w in full_lower
        for w in ["weekend", "sat", "sun", "fri - sun", "daily"]
    )

    return {
        "source": f"@{channel}",
        "category": category,
        "title": headline,
        "image": extract_photo_url(wrap),
        "bullets": bullets,
        "date": date_info,
        "time": time_info,
        "location": location,
        "is_free": is_free,
        "is_weekend": is_weekend,
        "post_url": post_url,
        "external_link": external_link,
        "posted_at": posted_at,
    }


def scrape_channel(channel: str) -> list[dict]:
    url = f"https://t.me/s/{channel}"
    resp = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    wraps = soup.select(".tgme_widget_message_wrap .tgme_widget_message")

    posts = []
    for wrap in reversed(wraps):
        parsed = parse_post(wrap, channel)
        if parsed:
            posts.append(parsed)
    return posts


def main():
    channels = load_channels()
    all_events = []

    for ch in channels:
        try:
            all_events.extend(scrape_channel(ch))
        except Exception as exc:
            print(f"Warning: failed @{ch}: {exc}")

    all_events.sort(key=lambda x: x.get("posted_at", ""), reverse=True)

    payload = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "events": all_events,
    }

    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(all_events)} posts across {len(channels)} channel(s).")


if __name__ == "__main__":
    main()
