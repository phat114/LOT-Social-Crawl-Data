from apify import Actor
from crawlee.crawlers import PlaywrightCrawler
from crawlee.http_clients import HttpxHttpClient
from .routes import router
from datetime import timedelta
from crawlee import ConcurrencySettings, Request
import sys


async def main() -> None:
    """The crawler entry point."""
    # Kiểm tra xem có URL được truyền vào không
    if len(sys.argv) < 2:
        print("Vui lòng cung cấp URL TikTok.")
        print("Ví dụ: uv run python -m tiktok_crawlee 'https://www.tiktok.com/@championsleague/video/7190381560057646342'")
        return

    # Lấy URL từ command line
    tiktok_url = sys.argv[1]

    # Kiểm tra xem URL có phải là URL TikTok hợp lệ không
    if not tiktok_url.startswith("https://www.tiktok.com/"):
        print("URL không hợp lệ. Vui lòng cung cấp một URL TikTok hợp lệ.")
        return
    
    async with Actor:
        crawler = PlaywrightCrawler(
            # proxy_
            request_handler=router,
            # headless=True,
            headless=False,
            max_requests_per_crawl=1,
            http_client=HttpxHttpClient(),
            # max_items=20,
            # max_tasks_per_minute=50,
            browser_type="firefox",
            browser_new_context_options={"permissions": []},
            request_handler_timeout=timedelta(seconds=500),
        )


        await crawler.run(
            [tiktok_url]
        )
