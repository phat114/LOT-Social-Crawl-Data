from crawlee.crawlers import PlaywrightCrawlingContext
from crawlee.router import Router
from crawlee.storages import Dataset
import re

router = Router[PlaywrightCrawlingContext]()
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

@router.default_handler
async def default_handler(context: PlaywrightCrawlingContext) -> None:
    context.log.info(f'default_handler is processing {context.request.url}')

    reaction_arr = []
    reaction_toolbar = await context.page.query_selector(f'span[role="toolbar"] ~ span[aria-hidden="true"]')
    # lấy số reaction

    total_reactions = await get_deepest_info(reaction_toolbar)
    print(f"Tổng số reaction: {total_reactions}")

    # lấy số comment
    comment_locator = await context.page.query_selector(f'div[role="complementary"] .html-span div[role="button"] span[dir="auto"]')
    total_comment = await get_deepest_info(comment_locator)
    print(f"Tổng số comment: {total_comment}")

    for x in facebook_reactions:
        reaction_locator = await context.page.query_selector(f'div[aria-label*="{x.capitalize()}"]')
        if reaction_locator:
            reaction_aria = await reaction_locator.get_attribute('aria-label')
            if reaction_aria:
                # Remove label text and extract integer
                reaction = int(
                    reaction_aria.replace(f'{x.capitalize()}:', '').replace("people", '').strip()
                )
                print(reaction)

                reaction_arr.append({x: reaction})
            else:
                print(f"Aria-label not found for {x}")
                reaction_arr.append({x: 0})
        else:
            print(f"Reaction element not found for {x}")
            reaction_arr.append({x: 0})

    print(reaction_arr)


# thử nghiệm
#
# @router.default_handler
# async def default_handler(context: PlaywrightCrawlingContext) -> None:
#     # This is a fallback route which will handle the start URL.
#     context.log.info(f'default_handler is processing {context.request.url}')
#
#     await context.page.wait_for_selector('.collection-block-item')
#
#     await context.enqueue_links(
#         selector='.collection-block-item',
#         label='CATEGORY',
#     )
#
#
# @router.handler('CATEGORY')
# async def category_handler(context: PlaywrightCrawlingContext) -> None:
#     # This replaces the context.request.label == CATEGORY branch of the if clause.
#     context.log.info(f'category_handler is processing {context.request.url}')
#
#     await context.page.wait_for_selector('.product-item > a')
#
#     await context.enqueue_links(
#         selector='.product-item > a',
#         label='DETAIL',
#     )
#
#     next_button = await context.page.query_selector('a.pagination__next')
#     if next_button:
#         await context.enqueue_links(
#             selector='a.pagination__next',
#             label='CATEGORY',
#         )
#
#
# @router.handler('DETAIL')
# async def detail_handler(context: PlaywrightCrawlingContext) -> None:
#     # This replaces the context.request.label == DETAIL branch of the if clause.
#     context.log.info(f'detail_handler is processing {context.request.url}')
#
#     url_part = context.request.url.split('/').pop()
#     manufacturer = url_part.split('-')[0]
#
#     title = await context.page.locator('.product-meta h1').text_content()
#
#     sku = await context.page.locator('span.product-meta__sku-number').text_content()
#
#     price_element = context.page.locator('span.price', has_text='$').first
#     current_price_string = await price_element.text_content() or ''
#     raw_price = current_price_string.split('$')[1]
#     price = float(raw_price.replace(',', ''))
#
#     in_stock_element = context.page.locator(
#         selector='span.product-form__inventory',
#         has_text='In stock',
#     ).first
#     in_stock = await in_stock_element.count() > 0
#     data = {
#         'manufacturer': manufacturer,
#         'title': title,
#         'sku': sku,
#         'price': price,
#         'in_stock': in_stock,
#     }
#
#     await context.push_data(data)
