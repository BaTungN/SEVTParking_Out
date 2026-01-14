from pymongo import MongoClient
from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo
from datetime import timezone
import json
class MongoDB:
    _instance = None  # Singleton instance
    def __new__(cls, uri="mongodb://sevtadm:Sevt%21202%23@117.7.228.184:35002/?authSource=admin", db_name="CarParkingControl", timeout_ms=2000):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = MongoClient(
                uri,
                serverSelectionTimeoutMS=timeout_ms,
                connectTimeoutMS=timeout_ms,
                socketTimeoutMS=timeout_ms  # Thoiw gian cho thao tac docghi
            )  # Kết nối đến MongoDB
            cls._instance.db = cls._instance.client[db_name]  # Chọn

        return cls._instance
    def get_collection(self, collection_name):
        self.db.command("ping")
        return self.db[collection_name]  # Trả về collection
    # def get_date_time(self):
    #     server_status = self.client.admin.command("hello")
    #     mongo_time = server_status["localTime"]
    #     vn_tz=ZoneInfo("Asia/Ho_Chi_Minh")
    #     server_time=mongo_time.astimezone(tz=vn_tz)
    #     return server_time.replace(tzinfo=None)

if __name__ == '__main__':
    from pymongo import MongoClient

    client = MongoClient("mongodb://sevtadm:Sevt%21202%23@117.7.228.184:35002/?authSource=admin")

    try:
        client.admin.command("ping")
        print("✅ Kết nối MongoDB thành công!")
    except Exception as e:
        print("❌ Kết nối thất bại:", e)