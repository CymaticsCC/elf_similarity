#! /bin/bash

python3 manage.py makemigrations && python3 manage.py migrate

cd ioc_binary/
python3 daily_work.py & 
cd ../
service cron start
python3 manage.py crontab add
python3 manage.py runserver 0.0.0.0:8188 
