import argparse
import csv
import json
import re
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


DEFAULT_URL = (
    "https://www.threads.com/search?q=%E7%84%A1%E4%BA%BA%E9%A7%95%E9%A7%9B"
    "&serp_type=default"
)
PROFILE_DIR = Path(__file__).resolve().parent / ".threads_browser_profile"
OUTPUT_FIELDS = [
    "post_url",
    "author",
    "text",
    "published_at",
    "likes",
    "reply_count",
    "reposts",
    "quotes",
    "media_urls",
    "replies",
]


def first_match(pattern, text):
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1) if match else ""


def extract_post(article):
    links = article.locator("a[href*='/post/']")
    post_url = ""
    if links.count():
        post_url = links.first.get_attribute("href") or ""

    text = " ".join(article.inner_text().split())
    time_element = article.locator("time").first
    published_at = ""
    if time_element.count():
        published_at = (
            time_element.get_attribute("datetime")
            or time_element.inner_text()
            or ""
        )

    author = ""
    for author_link in article.locator("a[href^='/@']").all():
        candidate = author_link.inner_text().strip()
        if candidate:
            author = candidate
            break

    media_urls = []
    for selector in ("img[src]", "video[src]", "video source[src]"):
        for element in article.locator(selector).all():
            source = element.get_attribute("src")
            if source and source not in media_urls:
                media_urls.append(source)

    metrics = re.findall(r"\d[\d,.]*(?:\s*萬)?", text.split("翻譯", 1)[-1])[:4]
    metrics += [""] * (4 - len(metrics))

    return {
        "post_url": post_url,
        "author": author,
        "text": text,
        "published_at": published_at,
        "likes": metrics[0],
        "reply_count": metrics[1],
        "reposts": metrics[2],
        "quotes": metrics[3],
        "media_urls": media_urls,
        "replies": [],
    }


def find_post_container(post_link):
    candidates = []
    for ancestor in post_link.locator("xpath=ancestor::div").all():
        if ancestor.locator("a[href*='/post/']").count() != 1:
            continue
        text_length = len(ancestor.inner_text().strip())
        if 80 <= text_length <= 2_000:
            candidates.append((text_length, ancestor))
    return max(candidates, key=lambda item: item[0])[1] if candidates else post_link


def scrape_replies(page, post_url, limit=25):
    page.goto(post_url, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(2_000)
    replies = {}
    for _ in range(10):
        for reply_link in page.locator("a[href*='/post/']").all():
            href = reply_link.get_attribute("href") or ""
            reply_url = (
                "https://www.threads.com" + href
                if href.startswith("/")
                else href
            )
            if not reply_url or reply_url == post_url or reply_url in replies:
                continue
            reply = extract_post(find_post_container(reply_link))
            reply["post_url"] = reply_url
            replies[reply_url] = reply
            if len(replies) >= limit:
                return list(replies.values())
        page.mouse.wheel(0, 2_000)
        page.wait_for_timeout(1_000)
    return list(replies.values())


def scrape_threads(url, limit=25, reply_limit=25, login=False, cdp_url=None):
    with sync_playwright() as playwright:
        owns_context = not cdp_url
        if cdp_url:
            browser = playwright.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]
        else:
            context = playwright.chromium.launch_persistent_context(
                str(PROFILE_DIR),
                channel="chrome",
                headless=False,
                viewport={"width": 1440, "height": 1000},
            )
        page = context.pages[0] if context.pages else context.new_page()
        if login:
            page.goto("https://www.threads.com/", wait_until="domcontentloaded")
            input("請在開啟的瀏覽器完成 Threads 登入，完成後回到終端機按 Enter：")
            if owns_context:
                context.close()
            return []
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(3_000)

        posts = {}
        for _ in range(20):
            for post_link in page.locator("a[href*='/post/']").all():
                post = extract_post(find_post_container(post_link))
                if post["post_url"]:
                    if post["post_url"].startswith("/"):
                        post["post_url"] = "https://www.threads.com" + post["post_url"]
                    posts[post["post_url"]] = post
                    if len(posts) >= limit:
                        break
            if len(posts) >= limit:
                break
            page.mouse.wheel(0, 2_500)
            page.wait_for_timeout(1_500)

        for post in posts.values():
            post["replies"] = scrape_replies(page, post["post_url"], reply_limit)

        if owns_context:
            context.close()
        return list(posts.values())[:limit]


def save_posts(posts):
    output_dir = Path(__file__).resolve().parent
    json_path = output_dir / "threads_posts.json"
    csv_path = output_dir / "threads_posts.csv"

    json_path.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for post in posts:
            row = post.copy()
            row["media_urls"] = "\n".join(row["media_urls"])
            row["replies"] = json.dumps(row["replies"], ensure_ascii=False)
            writer.writerow(row)
    return csv_path, json_path


def main():
    parser = argparse.ArgumentParser(description="抓取公開 Threads 貼文")
    parser.add_argument("url", nargs="?", default=DEFAULT_URL)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--reply-limit", type=int, default=25)
    parser.add_argument("--login", action="store_true", help="開啟瀏覽器供首次手動登入")
    parser.add_argument("--cdp-url", help="連接已用 remote debugging 啟動的 Chrome，例如 http://127.0.0.1:9222")
    args = parser.parse_args()

    if not args.url.startswith(("https://www.threads.com/", "https://threads.net/")):
        parser.error("網址必須是公開的 threads.com 或 threads.net 網址")
    if args.limit < 1:
        parser.error("--limit 必須大於 0")
    if args.reply_limit < 1:
        parser.error("--reply-limit 必須大於 0")

    if args.login:
        scrape_threads(args.url, args.limit, args.reply_limit, login=True)
        print(f"登入狀態已保存至：{PROFILE_DIR}")
        return

    try:
        posts = scrape_threads(args.url, args.limit, args.reply_limit, cdp_url=args.cdp_url)
    except PlaywrightTimeoutError as error:
        raise SystemExit(f"載入 Threads 逾時，請確認網址與網路連線：{error}") from error

    if not posts:
        raise SystemExit("沒有抓到公開貼文；頁面可能要求登入，或 Threads 已更新頁面結構。")

    csv_path, json_path = save_posts(posts)
    print(f"抓到 {len(posts)} 篇貼文")
    print(f"CSV:  {csv_path}")
    print(f"JSON: {json_path}")


if __name__ == "__main__":
    main()