# SEVTParking_Out

## Tạo service
```
sudo nano /etc/systemd/system/myapp.service
```
## Nội dung file myapp.service
```
[Unit]
Description=My Python Script Service
[Service]
StandardOutput=journal
StandardError=journal
User=meg
WorkingDirectory=/home/meg/SEVTParking_Out
ExecStart=/home/meg/myenv/bin/python /home/meg/SEVTParking_Out/Checkout_MODE.py
Restart=always    
RestartSec=4
StartLimitIntervalSec=0
[Install]
WantedBy=multi-user.target
```
## Lưu lại
```
sudo systemctl daemon-reload          # Nạp lại danh sách service
sudo systemctl enable myapp # Tự chạy khi boot
sudo systemctl start myapp  # Chạy ngay
```
## Xem log
```
journalctl -u myapp -f
```
# Tạo môi trường ảo
## Cài venv nếu chưa có
```
sudo apt update
sudo apt install python3-venv -y
```
## Tạo môi trường ảo
```
python3 -m venv myenv --system-site-packages
source myenv/bin/activate
```
## Các thư viện
```
pip install cryptography pycryptodome pymongo python-dateutil pyserial schedule
```
