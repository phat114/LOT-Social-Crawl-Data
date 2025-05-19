import mysql.connector
from mysql.connector import Error

def create_connection():
    try:
        connection = mysql.connector.connect(
            host='210.245.111.173',        # Hoặc IP MySQL server
            database='apidemo',
            user='apidemou',
            password='P9ywhu#g0gluVGYR'
        )

        if connection.is_connected():
            print("✅ Kết nối thành công tới MySQL")
            return connection
        return None

    except Error as e:
        print(f"❌ Lỗi kết nối: {e}")
        return None
