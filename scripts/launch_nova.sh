#!/bin/bash

cd /home/noaht/tutoring-robot


/home/noaht/tutoring-robot/env/bin/python main.py > nova_log.txt 2>&1 &


sleep 5

#Launch Chromium Kiosk
chromium-browser --kiosk --app=http://127.0.0.1:5000 --noerrdialogs --disable-infobars --check-for-update-interval=31536000
