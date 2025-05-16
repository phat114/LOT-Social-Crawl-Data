from crawlee.crawlers import PlaywrightCrawlingContext
from crawlee.router import Router
# from mysql.connector import Error
import mysql.connector
from mysql.connector import Error

MYSQL_CONFIG = {
    'host': '',
    'database': '',
    'user': '',
    'password': ''
}

router = Router[PlaywrightCrawlingContext]()

@router.default_handler
async def default_handler(context: PlaywrightCrawlingContext) -> None:
    """Default request handler."""
    log = context.log
    page = context.page

    connection = mysql.connector.connect(
        host="",
        user="",
        password="",
        database=""
    )

    cursor = connection.cursor()

    try:
        await page.wait_for_selector('span[data-e2e="browse-username"]', timeout=10000)

        # Dom to get social info
        social_name = 'tiktok'
        social_url = context.request.url
        social_unique_id = context.request.url.split('/')[-1]

        # Dom to get author name
        author = await page.locator('span[data-e2e="browse-username"]').inner_text() or 'N/A'

        # Dom to get publish time
        time_text = await page.locator('span[data-e2e="browse-username"] ~ span[data-e2e="browser-nickname"] > span:last-child').inner_text()
        publish_time = time_text.strip() or 'N/A'

        # Dom to get description
        description_elements = await page.locator('span[data-e2e="new-desc-span"]').all()
        description = 'N/A'
        for element in description_elements:
            text = await element.inner_text()
            if text.strip():  # Chỉ lấy nội dung không rỗng
                description = text.strip()
                break

        # Dom to get like, share, comment, bookmark
        like = await page.locator('strong[data-e2e="like-count"]').inner_text() or 'N/A'
        share = await page.locator('strong[data-e2e="share-count"]').inner_text() or 'N/A'
        comment = await page.locator('strong[data-e2e="comment-count"]').inner_text() or 'N/A'
        bookmark = await page.locator('strong[data-e2e="undefined-count"]').inner_text() or 'N/A'
        try:
            sql_tracking = """INSERT INTO tracking_history 
            (`social_name`, `social_url`, `social_unique_id`, `author`, `publish_time`, `description`, `like`, `share`, `comment`, `bookmark`, crawl_date)
            VALUES (%s, %s , %s, %s, %s, %s, %s, %s, %s, %s, CURDATE())"""
            
            cursor.execute(sql_tracking, (social_name, social_url, social_unique_id, author, publish_time, description, like, share, comment, bookmark,))
            log_id = cursor.lastrowid

            # Check if record exists in real_time_data
            sql_check = """SELECT COUNT(*) FROM real_time_data 
                WHERE social_name = %s AND social_unique_id = %s"""
            cursor.execute(sql_check, (social_name, social_unique_id))
            record_exists = cursor.fetchone()[0] > 0

            if record_exists:
                # Update existing record in real_time_data
                sql_update = """UPDATE real_time_data 
                    SET social_url = %s, author = %s, publish_time = %s, description = %s, 
                        `like` = %s, `share` = %s, `comment` = %s, `bookmark` = %s, `log_id` = %s, last_update_at = CURDATE()
                    WHERE social_name = %s AND social_unique_id = %s"""
                cursor.execute(sql_update, (social_url, author, publish_time, description, like, share, comment, bookmark, log_id, social_name, social_unique_id))
                log.info(f"Updated record in real_time_data for {social_name}/{social_unique_id}")
            else:
                # Insert new record into real_time_data
                sql_insert = """INSERT INTO real_time_data 
                    (`social_name`, `social_url`, `social_unique_id`, `author`, `publish_time`, `description`, `like`, `share`, `comment`, `bookmark`, `log_id`, `last_update_at`)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURDATE())"""
                cursor.execute(sql_insert, (social_name, social_url, social_unique_id, author, publish_time, description, like, share, comment, bookmark, log_id,))
                log.info(f"Inserted new record into real_time_data for {social_name}/{social_unique_id}")

            connection.commit()
        except Error as e:
            context.log.error(f'MySQL error: {e}')
            sql_error = """INSERT INTO tracking_history 
                    (`social_url`, `status`, `error_message`, `crawl_date`)
                    VALUES (%s, %s, %s, CURDATE())"""
            cursor.execute(sql_error, (context.request.url, 0, str(e)))
            connection.commit()
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

        # Log kết quả

    except Exception as e:
        log.error(f'Error scraping {context.request.url}: {e}')
        try:
            sql_error = """INSERT INTO tracking_history 
                (`social_url`, `status`, `error_message`, `crawl_date`)
                VALUES (%s, %s, %s, CURDATE())"""
            cursor.execute(sql_error, (context.request.url, 0, str(e)))
            connection.commit()
        except Error as db_err:
            log.error(f'MySQL error while logging error: {db_err}')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()