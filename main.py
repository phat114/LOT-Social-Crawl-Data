import asyncio
import json
from datetime import datetime, timedelta

from crawlee.crawlers import PlaywrightCrawler

from connection import create_connection
from helper import append_query_param, update_data

from facebook_crawlee.routes import router as facebook_router
from tiktok_crawlee.routes import router as tiktok_router
from crawlee.http_clients import HttpxHttpClient
from crawlee.request_loaders import RequestList

def convert_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()  # hoặc .strftime("%Y-%m-%d %H:%M:%S")
    return obj


async def handle_crawling(platform, data):
    try:
        if platform == "facebook":
            router = facebook_router
        elif platform == "tiktok":
            router = tiktok_router
        else:
            router = tiktok_router

        # async with Actor:
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
            browser_type="chromium",
            browser_new_context_options={"permissions": []},
            request_handler_timeout=timedelta(seconds=120),
            request_manager=request_manager
        )

        await crawler.run()
        # crawler_data = await crawler.get_data()
        # print(crawler_data, 'tiktok_crawlee')
        # items = crawler_data.items
        # await update_data(items)
    except Exception as e:
        print(f"❌ Lỗi: {e}")


async def main():
    conn = create_connection()

    if conn:
        try:
            cursor = conn.cursor(dictionary=True)  # Trả về dict tự động
            cursor.execute("SELECT * FROM nifehub_marketing_process_posts")
            rows = cursor.fetchall()  # rows là list[dict]
            # Ghi vào file JSON
            # Chuyển datetime -> string cho từng dict
            platform_map = {"facebook": [], "tiktok": [], "youtube": []}
            for row in rows:
                # Convert datetime fields
                for key, value in row.items():
                    if isinstance(value, datetime):
                        row[key] = value.strftime("%Y-%m-%d %H:%M:%S")

                platform = row.get("platform")
                if platform in platform_map:
                    platform_map[platform].append(row)
            for platform in platform_map:
                print(f"\n🚀 Crawling {platform.upper()}...")
                await handle_crawling(platform, platform_map[platform])
                print(f"✅ DONE: {platform.upper()}\n")

            with open("backup/posts_data.jsonl", "w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False, indent=2)
            print("✅ Đã ghi dữ liệu ra file posts_data.json")
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"❌ Lỗi: {e}")
