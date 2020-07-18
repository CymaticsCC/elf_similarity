#! /bin/python
#coding:utf-8
#Date:2020/06/20


#单独使用模块的内容，必须采用设置环境变量
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../')) 
os.environ.setdefault("DJANGO_SETTINGS_MODULE","binary_compare.settings")

#然后启动这个django环境
import django
django.setup()

#引入即可
from app.models import download_record
from app.models import binary
from django.utils import timezone
from app.models import ssdeep_compare

import threading
import time


import ssdeep
from django.db.utils import IntegrityError

from multiprocessing.dummy import Pool as ThreadPoll

from queue import Queue
added_count = 0
data_queue = Queue(10240)
def add_one_ssdeep_thread(args):
    global data_queue
    global added_count
    added_count += 1
    left_file, right_file, left_value, right_value = args
    record = {
        "left_file":left_file,
        "right_file":right_file,
        "ssdeep_res":ssdeep.compare(left_value,right_value),
    }
    while True:
        try:
            data_queue.put(record)
            break
        except Exception as e:
            logging.error("Some error",exc_info =True)
            continue
    return         


db_working = True
def ssdeep_bulk_write_to_db(data_queue, bulk_size):

    object_list = []
    while db_working:
        if not data_queue.empty():
            try:
                one = data_queue.get(timeout = 3)
                data_queue.task_done()
                one_object = ssdeep_compare(**one)
                object_list.append(one_object)
                if len(object_list) >= bulk_size:
                    try:
                        ssdeep_compare.objects.bulk_create(object_list)
                    except IntegrityError as e:
                        pass
                    finally:
                        object_list.clear()
            except Exception as e:
                logging.error("????",exc_info = True)
                if len(object_list) > 0:
                    try:
                        ssdeep_compare.objects.bulk_create(object_list)
                    except IntegrityError as e:
                        pass
                    finally:
                        object_list.clear()

    if len(object_list) > 0:
        try:
            ssdeep_compare.objects.bulk_create(object_list)
        except IntegrityError as e:
            pass
        finally:
            object_list.clear()

    return

all_count = 1

def binary_ssdeep_list():
    global all_count
    binary_list = binary.objects.all()
    count = len(binary_list)

    all_count = count * ( count - 1) / 2

    for i in range(count):
        for j in range(i + 1, count):
            yield (binary_list[i].sha256, binary_list[j].sha256,binary_list[i].ssdeep_value,binary_list[j].ssdeep_value)
import logging

status_count_flag = False
def show_status():
    global added_count 
    global status_count_flag
    while not status_count_flag:
        logging.info("There are %.2f tasks have been done.[ss_deep_insert]" % (added_count / all_count))
        time.sleep(5)

def add_ssdeep_record():
    
    logging.info("Start insert ssdeep compare value")
    global status_count_flag
    global data_queue
    global db_working
    start_time = time.time()
    t = threading.Thread(target = show_status)
    t.start()
    bulk_size = 1024
    t_write_db = threading.Thread(target = ssdeep_bulk_write_to_db,args = (data_queue, bulk_size))
    t_write_db.start()

    pool = ThreadPoll(127)
    pool.map(add_one_ssdeep_thread, binary_ssdeep_list())
    pool.close()
    pool.join()
    time.sleep(10)

    data_queue.join()
    db_working = False
    status_count_flag = True

    end_time = time.time()
    
    logging.info("Insert all ssdeep compare value using %.2f s." % (end_time - start_time))

if __name__ == "__main__":
    add_ssdeep_record()   
