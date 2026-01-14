import os
import json
import time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Đường dẫn file lưu trữ dữ liệu tạm thời
log_file_path = '/path/to/local_log.json'





def check_mongo_connection(server_ip, port=27017, replica_set='rs0'):
    """
    Kiểm tra kết nối tới MongoDB server.
    Args:
        server_ip: IP hoặc hostname của MongoDB server.
        port: Cổng MongoDB, mặc định là 27017.
        replica_set: Tên replica set, nếu có.
    """
    try:
        # Kết nối tới MongoDB server
        client = MongoClient(f"mongodb://{server_ip}:{port}/", serverSelectionTimeoutMS=5000)

        # Gọi server_info() để kiểm tra kết nối, nếu không thể kết nối sẽ ném ra lỗi
        client.server_info()
        print("MongoDB server is reachable!")
        return True
    except ConnectionFailure:
        print(f"Could not connect to MongoDB server at {server_ip}:{port}.")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def sync_logs(server_ip):
    """
    Đồng bộ dữ liệu từ file JSON lên MongoDB khi có kết nối.
    """
    if check_mongo_connection(server_ip):
        # Kiểm tra nếu có dữ liệu chưa đồng bộ
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as file:
                logs = json.load(file)

            if logs:
                # Kết nối MongoDB
                client = MongoClient(f"mongodb://{server_ip}:27017/")
                db = client["vehicle_parking"]
                collection = db["logs"]

                # Gửi dữ liệu lên MongoDB
                collection.insert_many(logs)
                print(f"{len(logs)} logs đã được đồng bộ lên server.")

                # Sau khi đồng bộ xong, xóa file local
                os.remove(log_file_path)
            else:
                print("No logs to sync.")
        else:
            print(f"Log file {log_file_path} does not exist.")
    else:
        print("Unable to connect to MongoDB server or network issue.")


def periodic_sync(server_ip):
    """
    Kiểm tra kết nối và đồng bộ dữ liệu định kỳ mỗi phút.
    """
    while True:
        sync_logs(server_ip)
        time.sleep(60)  # Kiểm tra và đồng bộ mỗi phút


# Ví dụ sử dụng
if __name__ == "__main__":
    server_ip = "117.7.228.184"  # Địa chỉ IP của MongoDB server
    print("Starting periodic synchronization...")
    periodic_sync(server_ip)
