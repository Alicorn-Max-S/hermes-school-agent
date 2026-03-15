---
name: webscraping
description: Extract content from web pages using a cost-efficient tiered approach — free tools first (curl, Python requests, BeautifulSoup, trafilatura), escalating to Firecrawl only when necessary.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [webscraping, scraping, extraction, free, firecrawl, research, web]
    related_skills: [duckduckgo-search, arxiv, domain-intel]
    fallback_for_toolsets: []
prerequisites:
  commands: [curl, python3]
---

# Web Scraping

Extract content from web pages using a **cost-efficient tiered approach**. Free tools handle the majority of scraping tasks. Firecrawl is reserved for pages that resist free methods.

## Decision Flowchart

```
URL to scrape
  │
  ├─ Static page, public content?
  │    └─ YES → Tier 1: curl + trafilatura/BeautifulSoup (FREE)
  │
  ├─ Tier 1 returned empty/garbage?
  │    └─ YES → Tier 2: Python requests + headers + readability (FREE)
  │
  ├─ Tier 2 failed? (JS-rendered, anti-bot, login wall)
  │    └─ YES → Tier 3: Firecrawl scrape (PAID — single page)
  │
  └─ Need to crawl multiple pages from a domain?
       └─ YES → Tier 3: Firecrawl crawl with limit + filters (PAID — minimize pages)
```

**Rule of thumb:** Always start at Tier 1. Only escalate when the previous tier produces empty, broken, or incomplete content.

---

## How to Detect When to Escalate Tiers

After attempting a free scrape (Tier 1 or 2), inspect the result for these signals before deciding to escalate:

### Signs you need to move from Tier 1 to Tier 2

| Signal | What You See | Why |
|--------|-------------|-----|
| **Empty or near-empty output** | `trafilatura.extract()` returns `None` or `< 100 chars` | Page may need custom headers or specific element targeting |
| **Boilerplate only** | Output is just nav links, footer text, cookie banners | trafilatura's content detection missed the main body |
| **Encoding garbage** | `Ã©`, `â€™`, mojibake characters | Need `resp.encoding = resp.apparent_encoding` in requests |
| **403 / 406 response** | HTTP error from curl/trafilatura | Site requires browser-like headers or cookies |

### Signs you need to move from Tier 2 to Tier 3 (Firecrawl)

| Signal | What You See | Why |
|--------|-------------|-----|
| **"Enable JavaScript" message** | Body contains text like "Please enable JavaScript", "This app requires JS", or `<noscript>` content only | Page is a JavaScript SPA/framework (React, Vue, Angular, Next.js) |
| **Empty `<body>` with JS bundles** | HTML has `<script src="app.bundle.js">` but `<div id="root"></div>` is empty | Content is rendered client-side, not in server HTML |
| **Dashboard / web app UI** | URL points to a dashboard, admin panel, or interactive tool (Grafana, Retool, Notion, Figma) | These are fully JS-rendered applications |
| **Cloudflare / anti-bot challenge** | Response contains "Checking your browser", "cf-browser-verification", 403 with challenge page | Anti-bot protection requires a real browser environment |
| **CAPTCHA page** | Response contains CAPTCHA HTML instead of content | Bot detection triggered |
| **Infinite scroll / lazy load** | Only first few items appear, rest require scrolling | Content loaded dynamically via JS |
| **Login wall / paywall** | Redirect to login page or "Subscribe to read" overlay | Firecrawl may handle some; others need authentication |

### Quick detection snippet

Run this after a Tier 2 attempt to check if Firecrawl is needed:

```python
def needs_firecrawl(html: str) -> tuple[bool, str]:
    """Check if HTML content suggests JS rendering is required."""
    html_lower = html.lower()
    checks = [
        ("please enable javascript" in html_lower, "JS required message detected"),
        ("this app requires javascript" in html_lower, "JS required message detected"),
        ('<div id="root"></div>' in html or '<div id="app"></div>' in html, "Empty SPA root element"),
        ("cf-browser-verification" in html_lower, "Cloudflare challenge detected"),
        ("checking your browser" in html_lower, "Anti-bot challenge detected"),
        (len(html.strip()) < 500 and "<script" in html_lower, "Minimal HTML with JS bundles"),
        ('<noscript>' in html_lower and len(html) < 2000, "Noscript-only content"),
    ]
    for condition, reason in checks:
        if condition:
            return True, reason
    return False, ""

# Usage after Tier 2:
resp = requests.get(url, headers=headers, timeout=15)
should_escalate, reason = needs_firecrawl(resp.text)
if should_escalate:
    print(f"Escalating to Firecrawl: {reason}")
    # Proceed to Tier 3
```

---

## Tier 1: curl + trafilatura (Free)

Best for: blogs, news articles, documentation, wikis, static sites.

### Quick extract with curl + trafilatura

```python
import trafilatura

# Download and extract main content (strips nav, ads, boilerplate)
downloaded = trafilatura.fetch_url("https://example.com/article")
text = trafilatura.extract(downloaded)
print(text)
```

### With metadata

```python
import trafilatura

downloaded = trafilatura.fetch_url("https://example.com/article")
result = trafilatura.extract(downloaded, include_comments=False, include_tables=True,
                              output_format="json", with_metadata=True)
print(result)
```

### Output as markdown

```python
import trafilatura

downloaded = trafilatura.fetch_url("https://example.com/article")
text = trafilatura.extract(downloaded, output_format="txt", include_links=True, include_tables=True)
print(text)
```

### curl fallback (no Python dependencies)

```bash
# Fetch raw HTML
curl -sL -A "Mozilla/5.0 (compatible; HermesBot/1.0)" "https://example.com/article" -o /tmp/page.html

# Quick text extraction with Python stdlib
python3 -c "
import html, re, sys
with open('/tmp/page.html') as f:
    content = f.read()
# Remove scripts, styles, and tags
for tag in ['script', 'style', 'nav', 'footer', 'header']:
    content = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', content, flags=re.DOTALL|re.IGNORECASE)
content = re.sub(r'<[^>]+>', ' ', content)
content = html.unescape(content)
content = re.sub(r'\s+', ' ', content).strip()
print(content[:5000])
"
```

### Install trafilatura (one-time)

```bash
pip install trafilatura
```

---

## Tier 2: Python requests + BeautifulSoup (Free)

Best for: pages needing custom headers, cookie handling, specific element extraction, or when trafilatura misses content.

### Targeted element extraction

```python
import requests
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
resp = requests.get("https://example.com/page", headers=headers, timeout=15)
soup = BeautifulSoup(resp.text, "html.parser")

# Remove noise
for tag in soup(["script", "style", "nav", "footer", "aside"]):
    tag.decompose()

# Extract main content area
main = soup.find("main") or soup.find("article") or soup.find("div", class_="content") or soup.body
text = main.get_text(separator="\n", strip=True)
print(text[:5000])
```

### Extract structured data (tables)

```python
import requests
from bs4 import BeautifulSoup

resp = requests.get("https://example.com/data", headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
soup = BeautifulSoup(resp.text, "html.parser")

for table in soup.find_all("table"):
    rows = table.find_all("tr")
    for row in rows:
        cells = [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
        print(" | ".join(cells))
    print()
```

### Extract all links from a page

```python
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

url = "https://example.com"
resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
soup = BeautifulSoup(resp.text, "html.parser")

links = []
for a in soup.find_all("a", href=True):
    full_url = urljoin(url, a["href"])
    links.append({"text": a.get_text(strip=True), "url": full_url})
    print(f"{a.get_text(strip=True)}: {full_url}")
```

### Install BeautifulSoup (one-time)

```bash
pip install requests beautifulsoup4
```

---

## Tier 3: Firecrawl (Paid — Use Sparingly)

Use **only** when Tiers 1-2 fail due to: JavaScript rendering, anti-bot protection, CAPTCHAs, login walls, or when you need structured multi-page crawling.

**Requires:** `FIRECRAWL_API_KEY` environment variable (or self-hosted via `FIRECRAWL_API_URL`).

### Single page scrape

```python
# Using the built-in web_extract tool (preferred — handles summarization automatically)
web_extract(urls=["https://example.com/js-heavy-page"])
```

### Single page scrape (direct API — when you need raw content)

```python
from firecrawl import Firecrawl
import os

client = Firecrawl(api_key=os.getenv("FIRECRAWL_API_KEY"))
result = client.scrape(url="https://example.com/js-heavy-page", formats=["markdown"])

print(result.markdown[:3000])
```

### Multi-page crawl (cost-conscious)

```python
# Using the built-in web_crawl tool
# IMPORTANT: Always set a limit to control costs. NEVER exceed 10.
web_crawl("example.com", "Extract pricing information", limit=3)
```

### Crawl Limit Guidelines

**The limit must ALWAYS be 10 or less.** Choose the smallest limit that gets the job done:

| Task Type | Recommended Limit | Rationale |
|-----------|-------------------|-----------|
| **Single fact lookup** (pricing, contact info, one answer) | `limit=1` to `limit=2` | You only need 1-2 pages |
| **Specific section** (API docs for one endpoint, single tutorial) | `limit=3` to `limit=5` | A few pages cover a focused topic |
| **Broad topic survey** (entire API reference, full docs section) | `limit=5` to `limit=8` | Enough to capture most of a section |
| **Maximum coverage** (comprehensive site audit, full docs) | `limit=10` | Hard ceiling — never go higher |

**If you need more than 10 pages**, break the task into multiple targeted crawls with filters:
```python
# Instead of limit=20 across a whole site, do two focused crawls:
web_crawl("docs.example.com", "API authentication", limit=5, include_paths=["/auth/*"])
web_crawl("docs.example.com", "API endpoints", limit=5, include_paths=["/api/*"])
```

### When Firecrawl Limit is Reached

**IMPORTANT: If a Firecrawl crawl completes and you did not get enough content to fulfill the user's request, you MUST ask the user before re-running or increasing the limit.** Do not silently re-run Firecrawl — each run costs credits.

Tell the user:
1. How many pages were crawled and what was found
2. What is still missing
3. Ask if they want to run another crawl (with a specific new limit and/or adjusted filters)

Example:
> "I crawled 5 pages from docs.example.com and found the authentication docs, but the rate-limiting section wasn't included. Would you like me to run another crawl targeting `/api/rate-limits/*` with limit=3?"

### Cost optimization tips for Firecrawl

| Strategy | How | Savings |
|----------|-----|---------|
| **Set low limits** | `limit=3` to `limit=5` on crawls | Prevents runaway costs |
| **Use URL filters** | `include_paths=["/docs/*"]` | Scrape only relevant pages |
| **Exclude paths** | `exclude_paths=["/blog/*", "/archive/*"]` | Skip irrelevant sections |
| **Scrape, don't crawl** | Use `web_extract` for known URLs | 1 credit vs N credits |
| **Cache results** | Save output to file, reuse later | Avoid duplicate scrapes |
| **Self-host** | Set `FIRECRAWL_API_URL` | Zero API cost (server cost only) |
| **Ask before retry** | Confirm with user before re-crawling | Prevents wasted credits |

### Firecrawl via built-in tools (recommended)

The Hermes agent provides three built-in tools that wrap Firecrawl with LLM-powered summarization:

| Tool | Use Case | Example |
|------|----------|---------|
| `web_search` | Find URLs by topic | `web_search("python FastAPI deployment")` |
| `web_extract` | Get content from known URLs | `web_extract(urls=["https://..."])` |
| `web_crawl` | Crawl a site with instructions | `web_crawl("docs.example.com", "Find API reference", limit=5)` |

These tools automatically:
- Summarize content via LLM to reduce token usage
- Clean base64 images
- Handle retries and error reporting

---

## When to Use Each Tier

| Scenario | Tier | Tool | Cost |
|----------|------|------|------|
| Blog post / news article | 1 | trafilatura | Free |
| Documentation page | 1 | trafilatura or curl | Free |
| Wiki / static HTML | 1 | curl + Python | Free |
| Page with specific CSS selectors needed | 2 | BeautifulSoup | Free |
| Table/structured data extraction | 2 | BeautifulSoup | Free |
| Page behind cookie/session | 2 | requests with session | Free |
| JavaScript-rendered SPA | 3 | Firecrawl scrape | Paid |
| Anti-bot / Cloudflare protected | 3 | Firecrawl scrape | Paid |
| Crawl entire docs site | 3 | Firecrawl crawl + limit | Paid |
| PDF extraction from URL | 3 | Firecrawl scrape | Paid |

---

## Complete Workflow Example

```python
import trafilatura
import requests
from bs4 import BeautifulSoup

def scrape_url(url: str) -> str:
    """Scrape a URL using tiered approach: free first, Firecrawl as fallback."""

    # --- Tier 1: trafilatura (free) ---
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_tables=True, include_links=True)
            if text and len(text.strip()) > 100:
                return text
    except Exception:
        pass

    # --- Tier 2: requests + BeautifulSoup (free) ---
    try:
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        main = soup.find("main") or soup.find("article") or soup.body
        if main:
            text = main.get_text(separator="\n", strip=True)
            if len(text.strip()) > 100:
                return text
    except Exception:
        pass

    # --- Tier 3: Firecrawl (paid fallback) ---
    # Only reaches here if free methods failed
    return web_extract(urls=[url])

url = "https://example.com/target-page"
content = scrape_url(url)
print(content[:3000])
```

---

## Batch Scraping (Multiple URLs)

```python
import trafilatura

urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3",
]

results = {}
firecrawl_fallback = []

for url in urls:
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        text = trafilatura.extract(downloaded)
        if text and len(text.strip()) > 100:
            results[url] = text
            continue
    # Mark for Firecrawl fallback
    firecrawl_fallback.append(url)

# Only send failures to Firecrawl (saves money)
if firecrawl_fallback:
    fc_result = web_extract(urls=firecrawl_fallback)
    # Parse and merge fc_result into results

print(f"Free: {len(results)}, Firecrawl: {len(firecrawl_fallback)}")
```

---

## Saving Scraped Content

```python
import json, os, hashlib
from datetime import datetime

def save_scrape(url: str, content: str, output_dir: str = "./scraped"):
    """Save scraped content to a JSON file for reuse."""
    os.makedirs(output_dir, exist_ok=True)
    url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
    filename = f"{output_dir}/{url_hash}.json"
    data = {
        "url": url,
        "content": content,
        "scraped_at": datetime.now().isoformat(),
    }
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    return filename

def load_scrape(url: str, output_dir: str = "./scraped", max_age_hours: int = 24):
    """Load cached scrape if it exists and is fresh enough."""
    url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
    filename = f"{output_dir}/{url_hash}.json"
    if not os.path.exists(filename):
        return None
    with open(filename) as f:
        data = json.load(f)
    scraped_at = datetime.fromisoformat(data["scraped_at"])
    age_hours = (datetime.now() - scraped_at).total_seconds() / 3600
    if age_hours > max_age_hours:
        return None  # Stale cache
    return data["content"]
```

---

## Limitations

- **trafilatura** works best on article-style pages. It may miss content on SPAs, dashboards, or heavily interactive pages.
- **BeautifulSoup** cannot execute JavaScript. JS-rendered content will appear empty.
- **Firecrawl** costs credits per page scraped/crawled. Always set limits on crawls.
- **Rate limiting**: Add `time.sleep(1)` between requests when scraping multiple pages from the same domain to avoid being blocked.
- **robots.txt**: Respect site policies. Check `https://example.com/robots.txt` before scraping.

## Pitfalls

- **Don't jump to Firecrawl first.** Most public pages work fine with curl or trafilatura. Try free tools before spending credits. Check the "How to Detect When to Escalate Tiers" section to confirm escalation is warranted.
- **Don't crawl without limits.** Always pass `limit=` when using `web_crawl`. The limit must be **10 or less** — no exceptions.
- **Don't silently re-run Firecrawl.** If a crawl didn't return enough content, **ask the user** before running another one. Each run costs credits. Explain what was found and what's missing.
- **Don't forget User-Agent headers.** Some sites block requests without a browser-like User-Agent. Always set one in Tier 2.
- **Don't scrape the same URL twice.** Cache results to disk (see Saving Scraped Content above) to avoid redundant Firecrawl calls.
- **Don't ignore encoding.** Use `resp.encoding = resp.apparent_encoding` with requests if you see garbled text.
- **Don't parse HTML with regex for complex extraction.** Use BeautifulSoup — regex on HTML is fragile and error-prone.
- **Don't guess if a page needs Firecrawl.** Run the `needs_firecrawl()` detection check (see above) after Tier 2 fails — don't assume based on the URL alone.
