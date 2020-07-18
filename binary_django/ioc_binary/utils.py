#! /bin/python3
#coding:utf-8
#Date:2020/07/13


import os.path
base_path = os.path.dirname(os.path.abspath(__file__))

import logging
def setting_logging_module(level = logging.INFO):

    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%m/%d/%Y %H:%M:%S"
    
    logging.basicConfig(filename = os.path.join(base_path, "working.log"),level = level, format = LOG_FORMAT, datefmt = DATE_FORMAT)

