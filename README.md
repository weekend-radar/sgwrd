# SG Weekend & Free Activities Radar

An automated, zero-server dashboard that crawls public Singapore Telegram channels for weekend activities, pop-ups, exhibitions, and freebies, and publishes them to a searchable webpage via **GitHub Actions** and **GitHub Pages**.

## How It Works
1. **Source List (`channels.json`):** Stores the list of public Telegram channel handles to monitor.
2. **Scraper (`scraper.py`):** Fetches the public web preview (`https://t.me/s/<channel>`) for each channel, parses structured details (dates, times, locations, links), tags freebies and weekend events, and outputs `events.json`.
3. **Automation (`.github/workflows/crawl.yml`):** Runs daily at **8:15 AM SGT (00:15 UTC)** (and on demand via manual trigger) to commit fresh results to `events.json`.
4. **Frontend (`index.html`):** Static dashboard hosted on GitHub Pages that loads `events.json` with instant keyword, channel, category, and freebie filters.

## Quick Setup
1. **Run Initial Crawl:** Go to the **Actions** tab $\rightarrow$ **Crawl Telegram Weekend Activities** $\rightarrow$ click **Run workflow** to generate `events.json`.
2. **Enable GitHub Pages:** Go to **Settings** $\rightarrow$ **Pages** $\rightarrow$ set **Source** to **Deploy from a branch**, select `main` and `/ (root)`, and click **Save**.
3. **Add More Channels:** Edit `channels.json` and add any public Telegram channel username (without `@`).
