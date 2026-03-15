"""
GitLab Handbook & Direction Pages Scraper
==========================================

Recursively scrapes all sub-pages under GitLab's Handbook and Direction
sections, extracts clean text content, and saves results to a JSON file.

Usage:
    pip install -r requirements.txt
    python scrape_gitlab.py

Output:
    gitlab_data.json — list of {"url": "...", "content": "..."} entries
"""

import json
import logging
import re
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

# ─── Configuration ───────────────────────────────────────────────────────────

MAX_PAGES = 3000          # Maximum number of pages to scrape
MAX_DEPTH = 5             # Maximum link depth from seed URLs
CONCURRENCY = 10          # Number of parallel HTTP workers
DELAY = 0.5               # Seconds to wait between requests per worker
REQUEST_TIMEOUT = 30      # HTTP request timeout in seconds
CHECKPOINT_INTERVAL = 50  # Save progress every N pages
OUTPUT_FILE = "gitlab_data.json"
CHECKPOINT_FILE = "gitlab_data_checkpoint.json"

# Seed URLs to start crawling from
SEED_URLS = [
    "https://handbook.gitlab.com/handbook/",
    "https://about.gitlab.com/direction/",
]

# URL scope — only follow links matching these prefixes
ALLOWED_PREFIXES = [
    "https://handbook.gitlab.com/handbook/",
    "https://about.gitlab.com/direction/",
]

# Tags/classes to remove before extracting text (nav, footer, sidebars, etc.)
ELEMENTS_TO_REMOVE = [
    "nav", "footer", "header",
    {"class_": re.compile(r"(sidebar|nav|menu|footer|header|breadcrumb|toc|"
                          r"table-of-contents|edit-page|page-meta|"
                          r"cookie|banner|alert|modal)", re.I)},
    {"id": re.compile(r"(sidebar|nav|menu|footer|header|breadcrumb|toc|"
                      r"table-of-contents)", re.I)},
    {"role": re.compile(r"(navigation|banner|contentinfo)", re.I)},
    "script", "style", "noscript", "iframe",
]

# Minimum content length to keep a page (skip near-empty pages)
MIN_CONTENT_LENGTH = 100

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("scraper")

# ─── HTTP Session ────────────────────────────────────────────────────────────

session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
})


# ─── Helpers ─────────────────────────────────────────────────────────────────

def is_allowed_url(url: str) -> bool:
    """Check if URL falls within allowed prefixes."""
    return any(url.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def normalize_url(url: str) -> str:
    """Remove fragment, trailing whitespace, and ensure trailing slash for dirs."""
    url, _ = urldefrag(url)
    url = url.strip()
    # Remove query parameters to avoid duplicate pages
    parsed = urlparse(url)
    url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    # Ensure paths without extensions get a trailing slash
    if not parsed.path.split("/")[-1].count("."):
        if not url.endswith("/"):
            url += "/"
    return url


def clean_text(text: str) -> str:
    """Clean extracted text by collapsing whitespace and removing blank lines."""
    # Replace multiple spaces/tabs with single space
    text = re.sub(r"[ \t]+", " ", text)
    # Split into lines, strip each, remove empty ones
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    # Rejoin and collapse multiple newlines
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_content(html: str, url: str) -> str | None:
    """Extract main text content from HTML, stripping boilerplate elements."""
    soup = BeautifulSoup(html, "lxml")

    # Remove unwanted elements
    for selector in ELEMENTS_TO_REMOVE:
        if isinstance(selector, str):
            for el in soup.find_all(selector):
                el.decompose()
        elif isinstance(selector, dict):
            for el in soup.find_all(**selector):
                el.decompose()

    # Try to find the main content area
    main_content = (
        soup.find("main")
        or soup.find("article")
        or soup.find(attrs={"role": "main"})
        or soup.find("div", class_=re.compile(r"(content|main|article|page)", re.I))
        or soup.find("div", id=re.compile(r"(content|main|article|page)", re.I))
    )

    if main_content:
        text = main_content.get_text(separator="\n")
    else:
        # Fallback: use body
        body = soup.find("body")
        text = body.get_text(separator="\n") if body else soup.get_text(separator="\n")

    text = clean_text(text)

    if len(text) < MIN_CONTENT_LENGTH:
        log.debug(f"Skipping {url} — too short ({len(text)} chars)")
        return None

    return text


def extract_links(html: str, base_url: str) -> list[str]:
    """Extract all valid, in-scope links from an HTML page."""
    soup = BeautifulSoup(html, "lxml")
    links = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()

        # Skip non-HTTP links
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue

        # Resolve relative URLs
        full_url = urljoin(base_url, href)
        full_url = normalize_url(full_url)

        # Skip file downloads and non-page resources
        parsed = urlparse(full_url)
        ext = parsed.path.rsplit(".", 1)[-1].lower() if "." in parsed.path.split("/")[-1] else ""
        if ext in ("pdf", "png", "jpg", "jpeg", "gif", "svg", "ico", "css", "js",
                    "zip", "tar", "gz", "mp4", "webm", "xml", "json", "yaml", "yml",
                    "woff", "woff2", "ttf", "eot"):
            continue

        if is_allowed_url(full_url):
            links.append(full_url)

    return links


def fetch_page(url: str) -> tuple[str, str | None, list[str]]:
    """
    Fetch a single page. Returns (url, content_text_or_None, list_of_links).
    """
    try:
        time.sleep(DELAY)  # Rate limiting
        response = session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)

        # Handle non-HTML responses
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            log.debug(f"Skipping non-HTML: {url} ({content_type})")
            return url, None, []

        if response.status_code != 200:
            log.warning(f"HTTP {response.status_code}: {url}")
            return url, None, []

        html = response.text
        content = extract_content(html, url)
        links = extract_links(html, url)

        return url, content, links

    except requests.RequestException as e:
        log.warning(f"Request failed: {url} — {e}")
        return url, None, []
    except Exception as e:
        log.error(f"Unexpected error for {url}: {e}")
        return url, None, []


def save_results(results: list[dict], filepath: str) -> None:
    """Save scraped data to a JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    log.info(f"Saved {len(results)} pages to {filepath}")


# ─── Main Crawler ────────────────────────────────────────────────────────────

def crawl():
    """
    BFS crawler that discovers and scrapes pages starting from seed URLs.
    Uses a thread pool for concurrent HTTP requests.
    """
    log.info("=" * 60)
    log.info("GitLab Handbook & Direction Scraper")
    log.info("=" * 60)
    log.info(f"Config: MAX_PAGES={MAX_PAGES}, MAX_DEPTH={MAX_DEPTH}, "
             f"CONCURRENCY={CONCURRENCY}, DELAY={DELAY}s")
    log.info(f"Seeds: {SEED_URLS}")
    log.info("")

    # BFS queue: (url, depth)
    queue = deque()
    visited = set()
    results = []

    # Initialize with seed URLs
    for seed in SEED_URLS:
        normalized = normalize_url(seed)
        queue.append((normalized, 0))
        visited.add(normalized)

    pages_scraped = 0
    pages_with_content = 0
    errors = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        while queue and pages_scraped < MAX_PAGES:
            # Submit a batch of URLs from the queue
            batch_size = min(CONCURRENCY * 2, len(queue), MAX_PAGES - pages_scraped)
            futures = {}

            for _ in range(batch_size):
                if not queue:
                    break
                url, depth = queue.popleft()
                future = executor.submit(fetch_page, url)
                futures[future] = (url, depth)

            # Process completed futures
            for future in as_completed(futures):
                url, depth = futures[future]
                pages_scraped += 1

                try:
                    fetched_url, content, links = future.result()

                    if content:
                        results.append({
                            "url": fetched_url,
                            "content": content,
                        })
                        pages_with_content += 1

                    # Discover new links (if within depth limit)
                    if depth < MAX_DEPTH:
                        new_links = 0
                        for link in links:
                            if link not in visited and pages_scraped + len(queue) < MAX_PAGES * 2:
                                visited.add(link)
                                queue.append((link, depth + 1))
                                new_links += 1

                    elapsed = time.time() - start_time
                    rate = pages_scraped / elapsed if elapsed > 0 else 0
                    log.info(
                        f"[{pages_scraped:>4}/{MAX_PAGES}] "
                        f"✓ {pages_with_content} pages | "
                        f"Queue: {len(queue):>5} | "
                        f"Rate: {rate:.1f} pg/s | "
                        f"{url[:80]}"
                    )

                except Exception as e:
                    errors += 1
                    log.error(f"Error processing {url}: {e}")

                # Checkpoint save
                if pages_scraped % CHECKPOINT_INTERVAL == 0 and results:
                    save_results(results, CHECKPOINT_FILE)

    # ─── Final Summary ───────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    log.info("")
    log.info("=" * 60)
    log.info("SCRAPING COMPLETE")
    log.info("=" * 60)
    log.info(f"Pages visited:      {pages_scraped}")
    log.info(f"Pages with content: {pages_with_content}")
    log.info(f"Pages skipped:      {pages_scraped - pages_with_content - errors}")
    log.info(f"Errors:             {errors}")
    log.info(f"Total time:         {elapsed:.1f}s")
    log.info(f"Avg rate:           {pages_scraped / elapsed:.1f} pages/sec")
    log.info("")

    # Save final output
    if results:
        save_results(results, OUTPUT_FILE)
        log.info(f"✅ Output saved to: {OUTPUT_FILE}")

        # Print sample
        log.info("")
        log.info("─── Sample Entry ───")
        sample = results[0]
        log.info(f"URL: {sample['url']}")
        log.info(f"Content preview: {sample['content'][:300]}...")
    else:
        log.warning("No content was scraped. Check your network connection and URLs.")

    return results


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    crawl()
