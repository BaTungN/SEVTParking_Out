import threading
import traceback
import logging
from datetime import datetime, timedelta,timezone
from datetime import timezone, timedelta, timedelta as td
import serial
import time
from ExtensionCls.MongoDB import MongoDB
from ExtensionCls.IsCheckTime import IsCheckTime
import json,base64
import atexit
import RPi.GPIO as GPIO
import os
from Tesncryption.AsymmetricEncryption import AsymmetricEncryption,AESUtil
import hashlib
gpio_pins = [17, 18, 27, 22, 23, 24, 25]
gpio_on=False
# def cleanup_gpio():
#     print("Chương trình kết thúc, cleanup GPIO...")
#     GPIO.cleanup()

# atexit.register(cleanup_gpio)
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)  # PHẢI GỌI DÒNG NÀY TRƯỚC
GPIO.setwarnings(False)

for pin in gpio_pins:
    GPIO.setup(pin, GPIO.OUT)
def on_pin():
    global gpio_on
    # GPIO.setmode(GPIO.BCM)  # PHẢI GỌI DÒNG NÀY TRƯỚC
    # GPIO.setwarnings(False)
    # for pin in gpio_pins:
    #     GPIO.setup(pin, GPIO.OUT)
    logging.info(">>>> BARRIER OPEN")
    gpio_on=True
    for pin in gpio_pins:
        GPIO.output(pin, GPIO.HIGH)

def off_pin():
    global gpio_on
    logging.info(">>>> BARRIER CLOSE")
    # gpio_on=False
    # GPIO.setmode(GPIO.BCM)  # PHẢI GỌI DÒNG NÀY TRƯỚC
    # GPIO.setwarnings(False)
    # for pin in gpio_pins:
    #     GPIO.setup(pin, GPIO.OUT)

    for pin in gpio_pins:
        GPIO.output(pin, GPIO.LOW)
entrylog_file="backup_entry.json"
config_file="configs.json"
database_file="database.json"
# with open('/home/meg/UHF_RFID_CHECK/ExtensionCls/configs.json', 'r', encoding='utf-8') as file:
with open(config_file, 'r', encoding='utf-8') as file:
    configs = json.load(file)
port_name = configs['port']
baudrate = configs['baudrate']
_name_parking = configs['name_parking']
ServerUri = configs['server']['uri']
DBname = configs['server']['db_name']
# log_filename = "Logs/Car_parking.log"
log_filename = "Car_parking.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)
in_ok = "NO"
out_ok = "NO"
data_send = ""

def load_aes_key_iv():
    with open('/home/meg/SEVTParking_Out/Keys/aes_key_iv.json') as f:
        data = json.load(f)
    key = base64.b64decode(data['key'])
    return key
# �?c public key t? file
with open("/home/meg/SEVTParking_Out/Keys/public_key.pem", "r") as f:
    public_key = f.read()

# �?c private key t? file
with open("/home/meg/SEVTParking_Out/Keys/private_key.pem", "r") as f:
    private_key = f.read()
def hash_sha256(data: str) -> bytes:
    return hashlib.sha256(data.encode('utf-8')).digest()
key_aes= load_aes_key_iv()
aesUtil = AESUtil(key=key_aes)


class ControlCar:
    NameParking = 'A'
    connected = True

    def __init__(self, nameparking, checktime_set):
        self.NameParking = nameparking
        self.ModulCheck = IsCheckTime(self.NameParking)
        self.checktime_set = checktime_set
        try:
            MongoDBServer = MongoDB(uri=ServerUri, db_name=DBname)
            # from ExtensionCls.Logs import DBLogs
            # datetimeee = MongoDBServer.get_date_time()
            # newtime_os = datetimeee.strftime("%Y-%m-%d %H:%M:%S")
            # print(newtime_os)
            # os.system("sudo date -s '{}'".format(newtime_os))
            self.vehicles = MongoDBServer.get_collection("EmployeeParking")
            self.entry_logs = MongoDBServer.get_collection("EntryLogs")
            self.parking_status = MongoDBServer.get_collection("ParkingStatus")
            self.connected = True
            print("connected")

        except Exception as e:
            self.open_barrier()
            
            logging.error("KHONG THE KET NOI VOI SERVER: {}".format(e))
    def open_barrier(self):
        on_pin()
        # self.ImportLog=ImportLogs(nameparking)
    # ============= THEM DU LIEU RA =======================
    def insert_checkout(self, id_card=None, state=None, checkout_time=None):
        state_insert=True
        try:
            logs = self.entry_logs.find({
                "id_card.sha": hash_sha256(id_card),
                "name_parking": self.NameParking,
                #"status_in":"valid",
                #"checkout_time": None
                }
                ).sort({"checkin_time": -1})
            listt = list(logs)
          
            if not bool(listt):
                print("Xe khong co log vao bai!")
                return False
            log = listt[0]
            if log.get("checkout_time") is not None:
                checkout_time_log=log["checkout_time"]
                if checkout_time_log.tzinfo is None:
                    checkout_time_log = checkout_time_log.replace(tzinfo=timezone.utc)
                delta = checkout_time - checkout_time_log
                if delta < timedelta(hours=10):
                    self.entry_logs.update_one(
                        {"id_card.sha": log["id_card"]["sha"],
                        "name_parking": self.NameParking,
                        #"status_in":"valid",
                        "checkin_time": log["checkin_time"]},
                        {"$set": {"checkout_time": checkout_time}},
                        upsert=False
                    )
                    logging.info("****___UPDATE___****")
                else:
                    return False
            else:
                self.entry_logs.update_one(
                    {"id_card.sha": log["id_card"]["sha"],
                    "name_parking": self.NameParking,
                    #"status_in":"valid",
                    "checkin_time": log["checkin_time"]},
                    {"$set": {"checkout_time": checkout_time}},
                    upsert=False
                )
            if state is not None:
                self.vehicles.update_one(
                    {"id_card.sha": log["id_card"]["sha"],
                    "name_parking": self.NameParking},
                    {"$set": {
                        "checkin_status": state
                    }}, upsert=False)
            # count = self.vehicles.count_documents({
            #     "name_parking": self.NameParking,
            #     "car_parked": True
            # })
            # count = self.entry_logs.count_documents(
            #     {
            #         "name_parking": self.NameParking,
            #         "checkin_time":{'$ne':None},
            #         "checkout_time": None
            #     }
            # )
            try:
                # pipeline = [
                #     {
                #         "$match": {
                #             "name_parking": self.NameParking,
                #             "checkin_time": {"$ne": None},
                #             "checkout_time": None,
                #             "status_in": "valid"
                #         }
                #     },
                #     {"$sort": {"checkin_time": -1}},
                #     {
                #         "$group": {
                #             "_id": "$id_card.sha",
                #             "latest_log": {"$first": "$$ROOT"}
                #         }
                #     },
                #     {"$count": "total"}
                # ]
                pipeline = [
                    {
                        "$match": {
                            "name_parking": self.NameParking,
                            "status_in": "valid"
                        }
                    },
                    {"$sort": {"checkin_time": -1}},
                    {
                        "$group": {
                            "_id": "$id_card.sha",
                            "latest_log": {"$first": "$$ROOT"}
                        }
                    },
                    {
                        "$match": {
                            "latest_log.checkin_time": {"$ne": None},
                            "latest_log.checkout_time": None
                        }
                    },
                    {"$count": "total"}
                ]
                result_pip = list(self.entry_logs.aggregate(pipeline))
                count = result_pip[0]["total"] if result_pip else 0
                logging.info("========****count: {} ****========".format(count))
            except Exception as e:
                print(" {}".format(e))
            self.parking_status.update_one(
                {"name_parking": self.NameParking},
                {"$set": {"occupied_slots": count}}
            )
            return True
        except Exception as e:
            logging.error("Insert fail: "+e)
            return False

    # ============= KIEM TRA XE CO LOG HAY CHUA =======================
    def is_exist_in(self, id_card_check):
        try:
            check = self.entry_logs.find_one({"id_card.sha": hash_sha256(id_card_check)})
            if check:
                return True
            return False
        except Exception as e:
            logging.error("CHECK EXITS LOGS:{}".format(e))
            return False
    # **********************************************************
    # ============= KIEM TRA SLOT BAI XE =======================
    # ***********************************************************
    def is_parking_available(self):
        try:
            status = self.parking_status.find_one({"name_parking": self.NameParking})
            return status["occupied_slots"] < status["total_slots"], status["total_slots"] - status["occupied_slots"]
        except Exception as e:
            return False,0
    # ============= LUU DU LIEU =======================
    def save_data(self, id_card, checkin_time, checkout_time, state=None):
        try:
            self.entry_logs.insert_one({
                "id_card": {
                    "aes": aesUtil.encrypt(id_card),
                    "sha": hash_sha256(id_card)
                },
                "name_parking": self.NameParking,
                "checkin_time": checkin_time,
                "checkout_time": checkout_time,
                "status_in":"nocheckin"
            })
            if state is not None:
                self.vehicles.update_one(
                    {"id_card.sha": hash_sha256(id_card)},
                    {"$set": {
                        "checkin_status": state
                    }}, upsert=True)
            try:
                # pipeline = [
                #     {
                #         "$match": {
                #             "name_parking": self.NameParking,
                #             "checkin_time": {"$ne": None},
                #             "checkout_time": None,
                #             "status_in":"valid"
                #         }
                #     },
                #     {"$sort": {"checkin_time": -1}},
                #     {
                #         "$group": {
                #             "_id": "$id_card.sha",
                #             "latest_log": {"$first": "$$ROOT"}
                #         }
                #     },
                #     {"$count": "total"}
                # ]
                pipeline = [
                    {
                        "$match": {
                            "name_parking": self.NameParking,
                            "status_in": "valid"
                        }
                    },
                    {"$sort": {"checkin_time": -1}},
                    {
                        "$group": {
                            "_id": "$id_card.sha",
                            "latest_log": {"$first": "$$ROOT"}
                        }
                    },
                    {
                        "$match": {
                            "latest_log.checkin_time": {"$ne": None},
                            "latest_log.checkout_time": None
                        }
                    },
                    {"$count": "total"}
                ]
                result_pip = list(self.entry_logs.aggregate(pipeline))
                count = result_pip[0]["total"] if result_pip else 0
                logging.info("========****count: {} ****========".format(count))
            except Exception as e:
                print(" {}".format(e))
            self.parking_status.update_one(
                {"name_parking": self.NameParking},
                {"$set": {"occupied_slots": count}}
            )
            return True
        except Exception as e:
            return False


    # ============= XE RA =======================
    def checkout_car(self, id_car_check):

        global out_ok
        is_parking_available, slots = self.is_parking_available()
        datetimee = datetime.now(timezone.utc)
        vehicle = None
        try:
            if vehicle is None:
                _id_car_check=id_car_check[-8:]
                
                vehicle = self.vehicles.find_one({"id_card.sha": hash_sha256(_id_car_check),"type_card.sha": hash_sha256("epass"), "name_parking": self.NameParking})
                if vehicle:
                    id_car_check=_id_car_check
                    
        except:
            self.open_barrier()
            logging.error("KHONG THE KET NOI SERVER!")
        try:
            if vehicle is None:
                vehicle = self.vehicles.find_one({"id_card.sha": hash_sha256(id_car_check), "name_parking": self.NameParking})
        except Exception as e:
            self.open_barrier()
            logging.error("KHONG THE KET NOI SERVER!{}".format(e))

        if not vehicle:
            _insert_checkout=self.insert_checkout(id_card=id_car_check, checkout_time=datetimee)
            if _insert_checkout:
                logging.info("ID: {} Thoi gian ra:{}".format(id_car_check, datetimee))
            else:
                try:
                    self.save_data(id_card=id_car_check, checkin_time=None, checkout_time=datetimee)
                except Exception as e:
                    logging.info("{}".format(e))
            logging.info("Xe khong ton tai trong he thong!")
            return

        # Kiem tra han su dung bai xe
        # expiry = self.ModulCheck.is_expiry_available(vehicle["start_date"], datetime_now=datetimee, months=6)
        # temp = "OK"
        # if expiry <= td(0):
        #     logging.warning("Xe het han su dung bai: {}".format(expiry * (-1)))
        # else:
        #     logging.info("Xe con han su dung bai: {}".format(expiry))
        # Kiem tra xe ra bai

        self.open_barrier()
        insert_checkout=self.insert_checkout(id_card=id_car_check, state=False, checkout_time=datetimee)
        if insert_checkout:
            out_ok = "OUTOK"
            logging.info("ID:{} Thoi gian ra:{}".format(id_car_check, datetimee))
        else:
            self.save_data(id_card=id_car_check, checkin_time=None, checkout_time=datetimee)
            logging.warning("KHONG CO GIO VAO")


def thread_checkout(com, baudrate):
    global out_ok, data_send,gpio_on
    id_in_temp = "-1"
    # ser_rfid = serial.Serial(port=com, baudrate=baudrate, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
    #                          bytesize=serial.EIGHTBITS, timeout=1)
    reset_second = time.time()
 
    ser_rfid=None
    try:
        off_pin()
        ser_rfid = serial.Serial(port=com, baudrate=baudrate, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                                bytesize=serial.EIGHTBITS, timeout=1)
    except Exception as e:
        ser_rfid=None
        on_pin()
        logging.error("KHONG THE KET NOI CONG COM: {}".format(e))
    while True:
        if ser_rfid is not None:
            data_bytes = ser_rfid.read(18)
            data = data_bytes[4:-2].hex().lower()
            
            
            # data = ser_rfid.readline().decode('utf-8').strip()
            # if len(data)>1 and len(data)<24:999999999999999999999
            #     logging.info("========****DATA RAW: {} ****========".format(data))
            
            if data!="" and data != None :
                if len(data) == 24:
                    
                    
                    if data != id_in_temp:
                        
                        if gpio_on==False:
                             on_pin()
                        logging.info("ID nhan duoc: {}".format(data))
                        checkout = ControlCar(nameparking=_name_parking, checktime_set=45)
                        checkout.checkout_car(data)
                        id_in_temp = data
                        time.sleep(0.5)
                        if gpio_on==True:
                            gpio_on=False
                            off_pin()
                            # id_in_temp=""
            
            if time.time() - reset_second > 20:
                id_in_temp = ""
                reset_second = time.time()

#======================== TEST Chuong trinh ============================
#====================================================================
current_tag=None
last_seen=0
last_action=0
timeout=1
timedelay_btw=2
state="IDLE"
isSerial = False
def main():
    try:
        while True:
            global current_tag,last_seen,last_action,timeout,state,isSerial
            ser_rfid=None
            try:
                ser_rfid = serial.Serial(port=port_name, baudrate=baudrate, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                                    bytesize=serial.EIGHTBITS, timeout=1)
                off_pin()
                logging.info(">>>>SERIAL OK")
                isSerial=False
            except Exception as e:
                if isSerial ==False:
                    logging.error(">>>> Serial: {}".format(e))
                    isSerial=True
                    on_pin()
                ser_rfid=None
                    
                
            if ser_rfid is not None:
                try:
                    while True:
                        now = time.time()
                        data_bytes = ser_rfid.read(18)
                        tag = data_bytes[4:-2].hex().lower()
                        #tag=ser_rfid.readline().decode().strip()
                        print(tag)
                        if state =="IDLE":
                            if tag and len(tag)==24 and tag.startswith("341"):
                                current_tag=tag
                                #on_pin()
                                logging.info("========================= ID nhan duoc: {} ============================".format(tag))
                                try:
                                    checkout = ControlCar(nameparking=_name_parking, checktime_set=45)
                                    checkout.checkout_car(tag)
                                except:
                                    check=False
                                    logging.info(">>>>===Step 1 OFFLINE")
                                    with open("cache_collection.json", "r", encoding="utf-8") as f:
                                        offline_data = json.load(f, object_hook=json_util.object_hook)
                                    for off in offline_data:
                                        if off["id_card"]["sha"]== hash_sha256(tag[-8:]) and off["name_parking"] ==_name_parking and off["type_card"]["sha"] == hash_sha256("epass"):
                                            check=True
                                            on_pin()
                                    if check==False:
                                        for off in offline_data:
                                            if off["id_card"]["sha"] == hash_sha256(tag) and off["name_parking"] ==_name_parking and off["type_card"]["sha"] == hash_sha256("vetc"):
                                                check=True
                                                on_pin()
                                state ="CARD_HELD"
                                last_seen = now
                                print("step1")
                        elif state =="CARD_HELD":
                            if tag == current_tag:
                                last_seen=now
                                last_action = now
                                print("step2")
                            elif not tag and now - last_seen > timeout:
                                off_pin()
                                current_tag=None
                                state ="IDLE" 
                                print("step3")
                            elif tag and len(tag)==24 and tag.startswith("341") and tag != current_tag and now  -last_action>timedelay_btw:
                                #on_pin()
                                logging.info("======================== ID nhan duoc: {} ==============================".format(tag))
                                try:
                                    checkout = ControlCar(nameparking=_name_parking, checktime_set=45)
                                    checkout.checkout_car(tag)
                                except:
                                    check=False
                                    logging.info(">>>>===Step 1 OFFLINE")
                                    with open("cache_collection.json", "r", encoding="utf-8") as f:
                                        offline_data = json.load(f, object_hook=json_util.object_hook)
                                    for off in offline_data:
                                        if off["id_card"]["sha"]== hash_sha256(tag[-8:]) and off["name_parking"] ==_name_parking and off["type_card"]["sha"] == hash_sha256("epass"):
                                            check=True
                                            on_pin()
                                    if check==False:
                                        for off in offline_data:
                                            if off["id_card"]["sha"] == hash_sha256(tag) and off["name_parking"] ==_name_parking and off["type_card"]["sha"] == hash_sha256("vetc"):
                                                check=True
                                                on_pin()
                                print("step4")
                                current_tag=tag
                                last_seen=now
                                last_action=now
                        time.sleep(0)

                except Exception as e:
                    logging.error("LOI XU LY CHECKOUT: {}".format(e))
    except Exception as ex:
        print("FAIL COM")
#====================================================================================
#====================================================================================
#==========================      AUTO BACKUP      ===================================
#====================================================================================
def backup_collection():
    MONGO_URI = configs['server']['uri']
    DB_NAME = configs['server']['db_name']
    BACKUP_FILE = "./backup.json"   
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        vehicles = db["EmployeeParking"]
        data = list(vehicles.find({}))

        tmp_file = "cache_collection.json.tmp"

        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, default=json_util.default, ensure_ascii=False)

        os.replace(tmp_file, "cache_collection.json")

        print(f"? Backup OK [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")

    except Exception as e:
        print(f"? Backup loii: {e}")
schedule.every().day.at("00:05").do(backup_collection)
schedule.every().day.at("17:05").do(backup_collection)
# ===== LOOP CH?Y N?N =====
def backup():
    logging.info("Backup Start")
    while True:
        schedule.run_pending()
        time.sleep(1)
#====================================================================================
def _main():
    thread = threading.Thread(target=thread_checkout, args=(port_name,baudrate))
    thread.start()
    thread2 = threading.Thread(target=backup)
    thread2.start()
if __name__ == '__main__':
    # main_oneway("/dev/ttyUSB0", 57600)
    main()
