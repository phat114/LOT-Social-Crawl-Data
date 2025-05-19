from apify import Actor
from crawlee.crawlers import PlaywrightCrawler
from crawlee.http_clients import HttpxHttpClient
from crawlee.request_loaders import RequestList

from helper import update_data, append_query_param
from .routes import router
from datetime import timedelta

async def main(data) -> None:
    # This is a demo link. Fetch links from your database.

    async with Actor:
        urls = [
            append_query_param(i["post_url"], "post_id", str(i["id"]))
            for i in data
        ]
        # async with Actor:
        # proxy_configuration = ProxyConfiguration(
        #     proxy_urls=[
        #         # "http://1003ge0i4m:1003ge0i4m@157.15.109.145:44589",
        # )
        request_list = RequestList(urls)
        request_manager = await request_list.to_tandem()
        crawler = PlaywrightCrawler(
            request_handler=router,
            # headless=True,
            headless=False,
            max_requests_per_crawl=1,
            http_client=HttpxHttpClient(),
            browser_type="firefox",
            browser_new_context_options={"permissions": []},
            request_handler_timeout=timedelta(seconds=120),
            request_manager=request_manager
        )


        await crawler.run()
        crawler_data = await crawler.get_data()
        print(crawler_data,'tiktok_crawlee')
        items = crawler_data.items
        await update_data(items)
