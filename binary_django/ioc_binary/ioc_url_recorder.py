#! /bin/python
#coding:utf-8
#2020/07/13 
#Version1.0

#单独使用模块的内容，必须采用设置环境变量
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../')) 
os.environ.setdefault("DJANGO_SETTINGS_MODULE","binary_compare.settings")

#然后启动这个django环境
import django
django.setup()

#引入即可
from app.models import ioc_urls_record
from app.models import ioc_urls_work_log

import sys
import time
import threading
from multiprocessing.dummy import Pool as ThreadPool

import socket
socket.setdefaulttimeout(2)

import requests
from requests.exceptions import ConnectionError,Timeout

import psutil
from subprocess import PIPE

from url_loader.loader import Osint_Loader, URLhaus_Loader
from queue import Queue
import logging


from utils import setting_logging_module


class IocUrl_Worker(object):

    def __init__(self):
        self.all_url_count = 0
        self.url_list = []
        self.done_url_count = 0
        self.data_insert_queue = Queue(1024)
        self.db_working = True
        self.count_flag = True
        self.threads_num = 128
        self.bulk_size = 256
    
    def work(self):
        pass

    def show_status(self, url_count):
        while self.count_flag:
            logging.info("There are %.2f tasks have been done.[url_staus_check]" % (self.done_url_count / url_count))
            time.sleep(5)

    def check_link_status_by_head(self,link):
        """
        使用head方法检查某个link是否可联通
        param link: 具体的link, str
        return: ret_value, int,0为异常，1为成功
        """
        try:
            res = requests.head(link,timeout = (3,3))
            if res.status_code == 200:
                return 1    
            return 0
        except (ConnectionError,Timeout) as e:
            return 0
        except Exception as e:
            return 0
        
        return 0

    def thread_check_url_status(self,url_info):
        """
        检查url状态的线程函数
        param url_info:url信息(url_source,link)，tuple
        return:None
        """

        url_source, link = url_info
        
        exists_status = 0
        try:
            if self.check_link_status_by_head(link):
                exists_status = 1
        except Exception as e:
            logging.error("Failed to check %s.[check_url_status]" % link, exc_info = True)
        
        while True:
            try:
                self.data_insert_queue.put((url_source, link,True if exists_status else False))
                break
            except Exception as e:
                continue

        self.done_url_count += 1
        return 


    def obtain_url_list(self):
        """
        获取URL列表
        return: url_list 从某ioc网站上获取的url列表, list
        """
    
        load_url_start_time = time.time()
        logging.info("start up loaders.")
        
        #当前使用两个loader，在初始化过程中会请求网址中的信息，如果失败则报告异常
        url_loader_class_list = [URLhaus_Loader,Osint_Loader]
        url_loader_list = []

        with open("url_loader/index.html", "r") as f:
            data = f.read()

        for one in url_loader_class_list:
            try:
                tmp_loader = one()
                url_loader_list.append(tmp_loader)
                logging.info("Obtain loader %s success." % one.url_source)
            except Exception as e:
                logging.warning("Obtain loader %s failed." % one.url_source)
                continue

        url_count = 0
        source_list = list(map(lambda x: x.url_source, url_loader_class_list))
        loader_count_list = [0 for i in range(len(url_loader_class_list))]

        load_url_end_time = time.time()
        time_used = load_url_end_time - load_url_start_time
        logging.info("Obtain all loader using %.2fs." % time_used)
    
        url_list = []
        for index,tmp_loader in enumerate(url_loader_list):
            tmp_list = tmp_loader.return_url_list()
            loader_count_list[index] = len(tmp_list)
            url_list.extend(list(map(lambda x: (tmp_loader.url_source, x), tmp_loader.return_url_list())))
        
        stats_list = zip(source_list, loader_count_list)

        stats_str = ",".join(list(map(lambda x: "source:%s count:%d" % (x[0],x[1]), stats_list)))

        if len(url_loader_list) == 0:
            ioc_urls_work_log.objects.create(url_count = 0,work_succ_flag = False, work_stats = stats_str)
            logging.error("Obtain all loader failed.Please check your network.")
            return []
        
        url_count = len(url_list)
        ioc_urls_work_log.objects.create(url_count = url_count,work_succ_flag = True, work_stats = stats_str)
        logging.info( "Working res->" + stats_str)

        return url_list

    def write_to_database(self,queue,bulk_size):
        
        """
        将数据批量写入数据库的线程
            
        :param queue: 队列，从该队列中取出要插入的数据
        :param bulk_size: 块大小，每次批量插入数据库的数据数量
        :return: None
        
        """
        
        #批量插入数据库的对象列表
        object_list = []
    
        while self.db_working:
            if not queue.empty():
                try:
                    one = queue.get(timeout = 3)
                    queue.task_done()
                    
                    url_source, url, status = one
                    one_object = ioc_urls_record(url = url, status = status, source = url_source)
                    object_list.append(one_object)
                    
                    #批量插入数据
                    if len(object_list) >= buil_size:
                        ioc_urls_record.objects.bulk_create(object_list)
                        object_list.clear()
                
                #发生异常后，将表中的数据先插入
                except Exception as e:
                    if len(object_list) > 0:
                        ioc_urls_record.objects.bulk_create(object_list)
                        object_list.clear()
    
        if len(object_list) > 0:
            ioc_urls_record.objects.bulk_create(object_list)
            object_list.clear()
        
        return
    
    def insert_ioc_records_daily(self):
    
        #获取url列表
        self.url_list = self.obtain_url_list()
        self.url_count = len(self.url_list)
        if self.url_count == 0:
            return False
        logging.info("Get %d urls to check" % self.url_count)
    
        #启动写入数据库的线程
        thread_write_to_db = threading.Thread(target = self.write_to_database, args = (self.data_insert_queue, self.bulk_size))
        thread_write_to_db.start()
    
        start_time = time.time()
    
        #探测URL状态的线程池
        logging.info("open %d threads working." % self.threads_num)
        pool = ThreadPool(self.threads_num)

        #进度条的线程
        thread_status = threading.Thread(target = self.show_status, args = (self.url_count,))
        thread_status.start()

        pool.map(self.thread_check_url_status, self.url_list)

        pool.close()
        pool.join()
        
        #关闭进度条的线程
        self.count_flag = False
        end_time = time.time()
        
        #等待数据库线程结束
        self.data_insert_queue.join()
        time.sleep(1)
        self.db_working = False
    
        logging.info("All %d urls have been checked using %.2f s." % (self.url_count, end_time - start_time))
        return True
    
if __name__ == "__main__":
    setting_logging_module()
    IocUrl_Worker().insert_ioc_records_daily()
