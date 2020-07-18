#! /bin/python3
#coding:utf-8
#2020/07/14


import os
import os.path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), './'))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from utils import setting_logging_module
setting_logging_module()

from ioc_binary_downloader import Ioc_Downloader
from ioc_url_recorder import IocUrl_Worker
from binary import create_binary_from_download
from ssdeep_compare import add_ssdeep_record

import time
import logging

def daily_binary_work():
    start_time = time.time()
    logging.info("Start doing the crontab job.")
    while True:
       if IocUrl_Worker().insert_ioc_records_daily():
           break
       else:
           time.sleep(3)

    Ioc_Downloader().work()
    create_binary_from_download()
    add_ssdeep_record() 
    end_time = time.time()
    logging.info("Ended the crontab job using %.2f s." % (end_time - start_time))

if __name__ == "__main__":
    daily_binary_work()
