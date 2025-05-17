from camoufox import AsyncNewBrowser
from crawlee._utils.context import ensure_context
from typing_extensions import override
from crawlee.browsers import (
    BrowserPool,
    PlaywrightBrowserController,
    PlaywrightBrowserPlugin,
)
from crawlee.fingerprint_suite import (
    DefaultFingerprintGenerator,
    HeaderGeneratorOptions,
    ScreenOptions,
)
from crawlee.router import Router
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

crawler_router  = Router[PlaywrightCrawlingContext]()

facebook_reactions = [
    "like",
    "love",
    "care",
    "haha",
    "wow",
    "sad",
    "angry"
]


async def get_deepest_info(locator):
    if locator is None:
        return ''
    try:
        # Kiểm tra xem locator có method evaluate_handle không
        if not hasattr(locator, 'evaluate_handle'):
            return ''

        deepest = await locator.evaluate_handle('''
                el => {
                    let current = el;
                    while (current.querySelector("span")) {
                        current = current.querySelector("span");
                    }
                    return current;
                }
            ''')
        return await deepest.inner_text()
    except Exception as e:
        print(f"⚠️ Lỗi trong get_deepest_info: {e}")
        return ''
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

@crawler_router.default_handler
async def default_handler(context: PlaywrightCrawlingContext) -> None:
    try:
        print(dir(context.page))

        # Kiểm tra xem context.page có phương thức emulate_media không
        if hasattr(context.page, 'emulate_media'):
            try:
                # Thiết lập các thuộc tính hợp lệ
                await context.page.emulate_media(
                    color_scheme="dark",  # Chế độ màu tối
                    reduced_motion="no-preference"  # Không giảm chuyển động
                )
                print("Đã thiết lập emulate_media.")
            except Exception as e:
                # In lỗi nếu có bất kỳ sự cố nào khi thiết lập emulate_media
                print(f"❌ Lỗi khi gọi emulate_media: {e}")
        else:
            # Nếu không có phương thức emulate_media, sử dụng headers tùy chỉnh
            await context.page.set_extra_http_headers({"User-Agent": "my-custom-agent"})
            print("❌ Phương thức set_emulated_media không tồn tại trên context.page.")
        reaction_arr = []
        title = ''
        total_plays = 0
        total_share = 0
        print(context.page.url.find("embed_post"),context.page.url)
        if(context.page.url.find("videos") != -1):
            #lấy reaction
            reaction_toolbar = await context.page.query_selector(f'div[data-pagelet="WatchPermalinkVideo"] ~ div > div:last-child span[role="toolbar"] ~ div[role="button"]')
            total_reactions = await get_deepest_info(reaction_toolbar)
            total_reactions = parse_abbreviated_number(total_reactions)

            # lấy số comment
            comment_locator = await context.page.query_selector(f'div[data-pagelet="WatchPermalinkVideo"] ~ div > div:last-child .html-span div[role="button"] span[dir="auto"]')
            total_comment = await get_deepest_info(comment_locator)
            total_comment = parse_abbreviated_number(total_comment.replace("comments", "").strip())

            #lấy lượt xem
            parent_plays_locator = await comment_locator.evaluate_handle('''el => {
                let parent = el;
                let count = 0;
                while (parent && count < 3) {
                    parent = parent.parentElement;
                    if (parent?.tagName === 'DIV') count++;
                    if (count === 2) return parent;
                }
                return null;
            }''')
            plays_locator = await parent_plays_locator.evaluate_handle('''el => {
                    let sibling = el.nextElementSibling;
                    while (sibling) {
                        if (sibling.tagName === 'SPAN') return sibling;
                        sibling = sibling.nextElementSibling;
                    }
                    return null;
                }''')
            total_plays = await get_deepest_info(plays_locator)
            total_plays = parse_abbreviated_number(total_plays.replace("plays", "").strip())

            #lấy title
            title = await context.page.title()
            if title:
                title = title.split('|')[0].strip()
        elif (context.page.url.find("embed_post") != -1 ):
            wrap_element = await context.page.query_selector('div[aria-posinset="1"] div[data-visualcompletion="ignore-dynamic"]')
            if(wrap_element):
                reaction_locator = await wrap_element.query_selector('span[aria-hidden="true"]')
                total_reactions = await get_deepest_info(reaction_locator)
                total_reactions = parse_abbreviated_number(total_reactions)
                comment_locator = await wrap_element.query_selector('div[aria-expanded="true"]')
                total_comment = await get_deepest_info(comment_locator)
                total_comment = parse_abbreviated_number(total_comment.replace("comments", "").strip())
                share_locator = await comment_locator.evaluate_handle('''el => {
                let parent = el;
                let count = 0;
                while (parent && count < 3) {
                    parent = parent.parentElement;
                    if (parent?.tagName === 'DIV') count++;
                    if (count === 2) return parent.nextElementSibling;
                }
                return null;
            }''')
                total_share = await get_deepest_info(share_locator)
                total_share = parse_abbreviated_number(total_share.replace('shares', "").strip())
        else:
            reaction_toolbar = await context.page.query_selector(f'div[role="complementary"] span[role="toolbar"] ~ span[aria-hidden="true"]')
            # lấy số reaction

            total_reactions = await get_deepest_info(reaction_toolbar)

            # lấy số comment
            comment_locator = await context.page.query_selector(f'div[role="complementary"] .html-span div[role="button"] span[dir="auto"]')
            total_comment = await get_deepest_info(comment_locator)

        # for x in facebook_reactions:
        #     reaction_locator = await context.page.query_selector(f'div[aria-label*="{x.capitalize()}"]')
        #     if reaction_locator:
        #         reaction_aria = await reaction_locator.get_attribute('aria-label')
        #         if reaction_aria:
        #             # Remove label text and extract integer
        #             reaction = int(
        #                 parse_abbreviated_number(reaction_aria.replace(f'{x.capitalize()}:', '').replace("people", '').strip())
        #             )
        #             print(reaction)
        #
        #             reaction_arr.append({x: reaction})
        #         else:
        #             print(f"Aria-label not found for {x}")
        #             reaction_arr.append({x: 0})
        #     else:
        #         print(f"Reaction element not found for {x}")
        #         reaction_arr.append({x: 0})
        print(f"Tổng số reaction: {total_reactions}")
        print(f"Tổng số comment: {total_comment}")
        print(f"Tổng số play: {total_plays}")
        print(f"title: {title}")
        print(f"Tổng số share: {total_share}")
    except Exception as e:
        print(f"❌ Lỗi xảy ra trong handler: {e}")

async def main() -> None:
    # async with Actor:
    # proxy_configuration = ProxyConfiguration(
    #     proxy_urls=[
    #         # "http://1003ge0i4m:1003ge0i4m@157.15.109.145:44589",
    # )
    crawler = PlaywrightCrawler(
        # proxy_configuration = proxy_configuration,
        max_requests_per_crawl=1,
        # Provide our router instance to the crawler.
        request_handler=crawler_router,
        browser_pool=BrowserPool(plugins=[CamoufoxPlugin()]),
        # browser_type = "chromium",
        # headless=False,
        # fingerprint_generator = fingerprint_generator
    )
    await crawler.run(['https://www.facebook.com/maohievan/posts/1978863362556695?ref=embed_post'])
    # await crawler.run(['https://www.facebook.com/photo/?fbid=4184754011769858&set=a.1378621109049843'])
