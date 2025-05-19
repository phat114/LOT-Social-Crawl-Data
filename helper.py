from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from connection import create_connection

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

async def update_data(data):
    conn = create_connection()
    cursor = conn.cursor()
    try:

        ids = [x["id"] for x in data]
        reactions_case = " ".join([f"WHEN {d['id']} THEN {d['likes']}" for d in data])
        comments_case = " ".join([f"WHEN {d['id']} THEN {d['comments']}" for d in data])
        shares_case  = " ".join([f"WHEN {d['id']} THEN {d['shares']}" for d in data])
        views_case  = " ".join([f"WHEN {d['id']} THEN {d['views']}" for d in data])
        bookmarks_case  = " ".join([f"WHEN {d['id']} THEN {d['bookmarks']}" for d in data])

        query = (f"""
            UPDATE nifehub_marketing_process_posts
            SET
                likes = CASE id {reactions_case} END,
                comments = CASE id {comments_case} END,
                shares = CASE id {shares_case} END,
                views = CASE id {views_case} END,
                bookmarks = CASE id {bookmarks_case} END
            WHERE id IN ({','.join(str(i) for i in ids)});
        """)

        cursor.execute(query)
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"❌ Lỗi UPDATE: {e}")

def append_query_param(url: str, key: str, value: str):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query[key] = [value]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))
