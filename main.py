import asyncio
import json
from datetime import datetime

from connection import create_connection
from facebook_crawlee.main import main as crawlee_facebook
from tiktok_crawlee.main import main as crawlee_tiktok



def convert_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()  # hoặc .strftime("%Y-%m-%d %H:%M:%S")
    return obj


async def handle_crawling(platform,data):
    print(f"Crawling {platform}...")
    match platform:
        case "facebook":
            await  crawlee_facebook(data)
            return None
        case "tiktok":
            await  crawlee_tiktok(data)
            return None
        case "youtube":
            return platform
        case _:
            return []


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
                await handle_crawling(platform, platform_map[platform])

            with open("backup/posts_data.jsonl", "w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False, indent=2)
            print("✅ Đã ghi dữ liệu ra file posts_data.json")
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"❌ Lỗi: {e}")
