import logging

from googleapiclient.discovery import build
from helper import update_data
import datetime

API_KEY = "AIzaSyBt8MQRZBsi4TMdt3jyOU2PUbRdYitqacM"  # Thay bằng API Key của bạn
youtube = build("youtube", "v3", developerKey=API_KEY)

def handle_crawl(item):
    try:
        video_id = item.get("post_url").split('v=')[-1].split('&')[0] if 'v=' in item.get("post_url") else item.get("post_url").split('/')[
            -1]
        print(video_id)
        request = youtube.videos().list(
            part="statistics,snippet",
            id=video_id
        )
        response = request.execute()
        if not response["items"]:
            print(f"❌ Không tìm thấy video {video_id}")
            logging.error(f"❌ Không tìm thấy video {video_id}", exc_info=True)

            return None

        video = response["items"][0]
        return {
            "platform_post_id": video_id,
            "post_title": video["snippet"]["title"],
            "likes": int(video["statistics"].get("likeCount", 0)),
            "views": int(video["statistics"].get("viewCount", 0)),
            "comments": int(video["statistics"].get("commentCount", 0)),
            "shares": 0,
            "bookmarks": 0,
            "id": item.get("id")
        }
    except Exception as e:
        print(f"❌ Lỗi khi gọi API-youtube cho {item.get('id')}: {e}")
        logging.error(f"❌ Lỗi khi gọi API-youtube cho {item.get('id')}: {e}", exc_info=True)
        return None

async def get_youtube_stats(data):
    try:
        print(data)
        results = []
        for item in data:
            result = handle_crawl(item)
            if result:
                results.append(result)
        return results
    except Exception as e:
        print(f"❌ Lỗi khi lấy thống kê YouTube: {e}")
        logging.error(f"❌ Lỗi khi lấy thống kê YouTube: {e}", exc_info=True)

        return []
