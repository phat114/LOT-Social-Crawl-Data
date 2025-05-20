import logging
from datetime import timedelta
from typing_extensions import override
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from camoufox import AsyncNewBrowser
from crawlee._utils.context import ensure_context
from crawlee.browsers import PlaywrightBrowserPlugin, PlaywrightBrowserController
from crawlee.crawlers import PlaywrightCrawler
from crawlee.fingerprint_suite import (
    DefaultFingerprintGenerator,
    HeaderGeneratorOptions,
    ScreenOptions,
)
from crawlee.http_clients import HttpxHttpClient
from crawlee.request_loaders import RequestList

from connection import create_connection
from globals import result_queue


def parse_abbreviated_number(s: str) -> int:
    s = s.strip().upper().replace(',', '')
    try:
        if s.endswith('K'):
            return int(float(s[:-1]) * 1_000)
        elif s.endswith('M'):
            return int(float(s[:-1]) * 1_000_000)
        elif s.endswith('B'):
            return int(float(s[:-1]) * 1_000_000_000)
        else:
            return int(float(s))
    except (ValueError, TypeError) as e:
        print(f"⚠️ Lỗi khi chuyển '{s}' thành số: {e}")
        return 0


def is_positive_number(value):
    try:
        number = float(value)
        return number > 0
    except (ValueError, TypeError):
        return False


async def process_queue():
    while True:
        result = await result_queue.get()
        if result is None:
            break  # Kết thúc
        print("📦 Xử lý kết quả:", result)
        await update_data([result])

async def update_data(data):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        ids = [str(d["id"]) for d in data]
        reactions_case = " ".join([f"WHEN {d['id']} THEN {d['likes']}" for d in data])
        comments_case = " ".join([f"WHEN {d['id']} THEN {d['comments']}" for d in data])
        shares_case = " ".join([f"WHEN {d['id']} THEN {d['shares']}" for d in data])
        views_case = " ".join([f"WHEN {d['id']} THEN {d['views']}" for d in data])
        bookmarks_case = " ".join([f"WHEN {d['id']} THEN {d['bookmarks']}" for d in data])
        query = f"""
                    UPDATE nifehub_marketing_process_posts
                    SET
                        likes = CASE id {reactions_case} END,
                        comments = CASE id {comments_case} END,
                        shares = CASE id {shares_case} END,
                        views = CASE id {views_case} END,
                        bookmarks = CASE id {bookmarks_case} END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id IN ({','.join(ids)});
                """
        cursor.execute(query)
        conn.commit()
    except Exception as e:
        print(f"❌ Lỗi UPDATE: {e}")
        logging.error(f"❌ Lỗi UPDATE: {e}", exc_info=True)

    finally:
        cursor.close()
        conn.close()


def append_query_param(url: str, key: str, value: str):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query[key] = [value]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


class CamoufoxPlugin(PlaywrightBrowserPlugin):
    """Example browser plugin that uses Camoufox Browser, but otherwise keeps the functionality of
    PlaywrightBrowserPlugin."""

    @ensure_context
    @override
    async def new_browser(self) -> PlaywrightBrowserController:
        if not self._playwright:
            raise RuntimeError('Playwright browser plugin is not initialized.')
        fingerprint_generator = DefaultFingerprintGenerator(
            header_options=HeaderGeneratorOptions(browsers=['chromium']),
            screen_options=ScreenOptions(min_width=3000),
        )
        browser = await AsyncNewBrowser(
            playwright=self._playwright,
            # executable_path="E:/camoufox/camoufox.exe",
            headless=False
        )
        return PlaywrightBrowserController(
            browser=browser,
            max_open_pages_per_browser=1,  #  Increase, if camoufox can handle it in your usecase.
            # header_generator=None,
            #  This turns off the crawlee header_generation. Camoufox has its own.
            fingerprint_generator=fingerprint_generator,
            # browser_type="chromium",

        )
