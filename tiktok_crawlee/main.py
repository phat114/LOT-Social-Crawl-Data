from apify import Actor
from crawlee.crawlers import PlaywrightCrawler
from crawlee.http_clients import HttpxHttpClient
from .routes import router
from datetime import timedelta

async def main() -> None:
    # This is a demo link. Fetch links from your database.
    links = ['https://www.tiktok.com/@makoto.gif/video/7424601086847192353']
    
    async with Actor:
        crawler = PlaywrightCrawler(
            request_handler=router,
            # headless=True,
            headless=False,
            max_requests_per_crawl=1,
            http_client=HttpxHttpClient(),
            browser_type="firefox",
            browser_new_context_options={"permissions": []},
            request_handler_timeout=timedelta(seconds=120),
        )

        await crawler.run(
            links
        )
