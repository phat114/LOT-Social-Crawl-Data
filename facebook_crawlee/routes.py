from urllib.parse import parse_qs, urlparse, urlencode, urlunparse

from crawlee.router import Router
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext, ParselCrawler

from helper import parse_abbreviated_number
router  = Router[PlaywrightCrawlingContext]()

facebook_reactions = [
    "like",
    "love",
    "care",
    "haha",
    "wow",
    "sad",
    "angry"
]

facebook_crawled = []

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

@router.default_handler
async def default_handler(context: PlaywrightCrawlingContext) -> None:
    try:
        await context.page.mouse.move(200, 300)
        await context.page.mouse.wheel(0, 1000)
        await context.page.wait_for_timeout(2000 )
        # Init giá trị
        title = ''
        total_plays = total_share = total_comment = total_reactions = 0

        # Emulate media nếu có
        if hasattr(context.page, 'emulate_media'):
            try:
                await context.page.emulate_media(
                    color_scheme="dark",
                    reduced_motion="no-preference"
                )
                print("✅ Đã thiết lập emulate_media.")
            except Exception as e:
                print(f"❌ emulate_media lỗi: {e}")
        else:
            await context.page.set_extra_http_headers({"User-Agent": "my-custom-agent"})

        url = context.page.url
        query = parse_qs(urlparse(url).query)
        post_id = query.get("post_id", [None])[0]
        # 📌 1. VIDEO PAGE
        if "videos" in url:
            await context.page.wait_for_selector('div[data-pagelet="WatchPermalinkVideo"]')

            wrap_sel = 'div[data-pagelet="WatchPermalinkVideo"] ~ div > div:last-child'

            reaction_toolbar = await context.page.query_selector(f'{wrap_sel} span[role="toolbar"] ~ div[role="button"]')
            if reaction_toolbar:
                total_reactions = parse_abbreviated_number(await get_deepest_info(reaction_toolbar))

            comment_locator = await context.page.query_selector(f'{wrap_sel} .html-span div[role="button"] span[dir="auto"]')
            if comment_locator:
                total_comment = parse_abbreviated_number(
                    (await get_deepest_info(comment_locator)).replace("comments", "").strip()
                )

                # Plays
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

                if parent_plays_locator:
                    plays_locator = await parent_plays_locator.evaluate_handle('''el => {
                        let sibling = el.nextElementSibling;
                        while (sibling) {
                            if (sibling.tagName === 'SPAN') return sibling;
                            sibling = sibling.nextElementSibling;
                        }
                        return null;
                    }''')
                    if plays_locator:
                        total_plays = parse_abbreviated_number(
                            (await get_deepest_info(plays_locator)).replace("plays", "").strip()
                        )

            title = (await context.page.title()).split('|')[0].strip()

        # 📌 2. EMBED PAGE
        elif "embed_post" in url:
            await context.page.wait_for_selector('div[aria-posinset="1"]')
            wrap_element = await context.page.query_selector('div[aria-posinset="1"] div[data-visualcompletion="ignore-dynamic"]')

            if wrap_element:
                reaction_locator = await wrap_element.query_selector('span[aria-hidden="true"]')
                if reaction_locator:
                    total_reactions = parse_abbreviated_number(await get_deepest_info(reaction_locator))

                comment_locator = await wrap_element.query_selector('div[aria-expanded="true"]')
                if comment_locator:
                    total_comment = parse_abbreviated_number(
                        (await get_deepest_info(comment_locator)).replace("comments", "").strip()
                    )

                    share_locator = await comment_locator.evaluate_handle('''el => {
                        let parent = el.parentElement;
                        while (parent) {
                            if (parent?.tagName === 'DIV') return parent.nextElementSibling;
                            parent = parent.parentElement;
                        }
                        return null;
                    }''')
                    if share_locator:
                        total_share = parse_abbreviated_number(
                            (await get_deepest_info(share_locator)).replace('shares', "").strip()
                        )

                title = await context.page.eval_on_selector(
                    'meta[name="description"]', 'el => el.getAttribute("content")'
                )

        # 📌 3. REELS PAGE
        elif "reel" in url:
            await context.page.wait_for_selector('div[data-pagelet="Reels"]')

            # Like
            like = await context.page.query_selector('div[aria-label="Like"]')
            if like:
                like_next = await like.evaluate_handle('el => el.parentElement.nextSibling')
                if like_next:
                    total_reactions = parse_abbreviated_number(await get_deepest_info(like_next))

            # Comment
            comment = await context.page.query_selector('div[aria-label="Comment"]')
            if comment:
                comment_next = await comment.evaluate_handle('el => el.parentElement.nextSibling')
                if comment_next:
                    total_comment = parse_abbreviated_number(await get_deepest_info(comment_next))

            # Share
            share = await context.page.query_selector('div[aria-label="Share"]')
            if share:
                share_next = await share.evaluate_handle('el => el.parentElement.nextSibling')
                if share_next:
                    total_share = parse_abbreviated_number(await get_deepest_info(share_next))

            title = await context.page.eval_on_selector(
                'link[rel="alternate"][type="application/json+oembed"]', 'el => el.getAttribute("title")'
            )
            if title:
                title= title.split('|')[0].strip()
        # 📌 4. OTHER POSTS
        else:
            await context.page.wait_for_selector('div[role="complementary"]')
            reaction_toolbar = await context.page.query_selector(
                'div[role="complementary"] span[role="toolbar"] ~ span[aria-hidden="true"]'
            )
            if reaction_toolbar:
                total_reactions = parse_abbreviated_number(await get_deepest_info(reaction_toolbar))

            comment_locator = await context.page.query_selector(
                'div[role="complementary"] .html-span div[role="button"] span[dir="auto"]'
            )
            if comment_locator:
                total_comment = parse_abbreviated_number(await get_deepest_info(comment_locator))

        await context.push_data({
            "id": post_id,
            # "post_title": title,
            "likes": total_reactions,
            "comments": total_comment,
            "shares": total_share,
            "views": total_plays,
            "bookmarks": 0,
        })

        # ✅ Xuất kết quả
        print(f"📌 Title: {title}")
        print(f"❤️ Total reactions: {total_reactions}")
        print(f"💬 Total comments: {total_comment}")
        print(f"🔁 Total shares: {total_share}")
        print(f"▶️ Total plays: {total_plays}")
        # await context.enqueue_links()
    except Exception as e:
        print(f"❌ Lỗi xảy ra trong handler: {e}")
