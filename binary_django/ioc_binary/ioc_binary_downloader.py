#! /bin/python
#coding:utf-8
#Date:2020/07/13

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
from app.models import ioc_urls_record

download_file_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../') + "app/static/binary/")

import time
import hashlib
import socket
socket.setdefaulttimeout(2)

import requests
from requests.exceptions import ConnectionError,Timeout
import magic

from multiprocessing.dummy import Pool as ThreadPool
import threading 
import logging
from queue import Queue
from utils import setting_logging_module

class Ioc_Downloader(object):

    def __init__(self):
        self.threads_num = 128
        self.bulk_size = 128
        self.succ_download = 0
        self.done_count = 0
        self.count_flag = True
        self.db_working = True
        self.record_insert_queue = Queue(1024)

    def get_file_info(self,file_name):
        """
        利用file命令获取指定文件的文件信息
        param file_name: 文件名, str
        return file_info:文件信息
        """
        #这里暂时只关注二进制和shell类型文件
        file_info = magic.from_file(file_name)
        return file_info

    def show_status(self, url_count):
        while self.count_flag:
            logging.info("There are %.2f tasks have been done.[binary_download]" % (self.done_count / url_count))
            time.sleep(5)

    def download_write_to_db(self,queue,bulk_size):
        
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
                    
                    one_object = download_record(**one)
                    object_list.append(one_object)
                    
                    #批量插入数据
                    if len(object_list) >= bulk_size:
                        download_record.objects.bulk_create(object_list)
                        object_list.clear()
                
                #发生异常后，将表中的数据先插入
                except Exception as e:
                    if len(object_list) > 0:
                        download_record.objects.bulk_create(object_list)
                        object_list.clear()
        

        if len(object_list) > 0:
            download_record.objects.bulk_create(object_list)
            object_list.clear()
        
        return



    def filter_some_type(self, file_info):
        """
        过滤某些类型的文件
        param file_info:文件信息,dic
        return: 是否要过滤掉
        """
        
    
        filter_type_str = [
                "data",
                "empty", #空
                "Mach-O",   #mac
                "Zip archive data", #apk
        ]
                           
        if len(list(filter(lambda x: file_info.startswith(x), filter_type_str))) > 0:
            return False

        if "HTML" in file_info:
            return False

        return True
    
    def calc_sha256(self,content):
        """
        计算文件的sha256
        param content:文件内容
        return: sha256
        """
        hash_obj = hashlib.sha256()
        hash_obj.update(content)
        return hash_obj.hexdigest()

    def download_file(self, url):
        """
        按照url下载文件
        param url: 文件url，str
        return: (是否下载成功，文件内容)
        """
        try:
            req = requests.get(url,timeout = (5,5))

        except (ConnectionError,Timeout) as e:
            return (False,None)

        except Exception as e:
            return (False,None)

        if not req.ok:
            return (False,None)
        if len(req.content) == 0:
            return (False,None)

        return (True, req.content)

    def download_one_binary(self, arg):
        
        """
        下载二进制，并更新url状态
        """

        start_time = time.time()
        url, url_record_id = arg
        try:
            if self._download_one_binary(url,url_record_id):
                self.succ_download += 1
                ioc_urls_record.objects.filter(id = url_record_id).update(is_download = True)
            else:
                ioc_urls_record.objects.filter(id = url_record_id).update(status = False)
            self.done_count += 1
            end_time = time.time()
        except Exception as e:
            logging.error("Some error happend when download_one_binary", exc_info = True)
            return

        logging.debug("Url: %s using %.2f s." %(url,end_time - start_time))


    def _download_one_binary(self, url, url_record_id):
        """
        下载一个软件，并进行一些辅助工作，例如获取文件信息，插入日志等
        param url:文件url
        param url_record_id: 对应的ioc_url_record的id
        """
        
        download_res, download_content = self.download_file(url)

        if not download_res:
            return False

        file_hash = self.calc_sha256(download_content)
        file_path = os.path.join(download_file_dir, file_hash)


        #获取文件信息，并进行过滤，如果不满足条件则删除生成的文件
        with open(file_path, "wb") as f:
            f.write(download_content)
        
        file_info  = self.get_file_info(file_path)
        if not self.filter_some_type(file_info):
            try:
                os.remove(file_path)
            except Exception as e:
                pass
            return False

        record = {
            "file_sha256": file_hash,
            "download_url":url,
            "download_url_id":url_record_id,
            "file_info": file_info,
            "download_path":file_path,
        }   
        while True:
            try:
                self.record_insert_queue.put(record)
                break
            except Exception as e:
                continue

        return True

    def url_list_gen(self, db_query_set):
        """
        url_list生成器
        """
        for one in db_query_set:
            yield (one.url,one.id)

    def work(self):

        url_list = ioc_urls_record.objects.filter(status = True, is_download = False).all() 
        if len(url_list) == 0:
            logging.info("There is no binaries have to download.")
            sys.exit(1)
        logging.info("start to download %d binary." % len(url_list))

        start_time = time.time()

        thread_write_to_db = threading.Thread(target = self.download_write_to_db, \
                                            args = (self.record_insert_queue, self.bulk_size))
        thread_write_to_db.start()
        
        pool = ThreadPool(self.threads_num)
        logging.info("open %d threads to work." % self.threads_num)

        thread_status = threading.Thread(target = self.show_status, args = (len(url_list),))
        thread_status.start()

        pool.map(self.download_one_binary, self.url_list_gen(url_list))
        pool.close()
        pool.join()
        
        self.record_insert_queue.join()
        self.db_working = False
        self.count_flag = False
        end_time = time.time()
        logging.info("download binaries %d successfully using %.2f s." % (self.succ_download, end_time - start_time))
         
    
if __name__ == "__main__":
    Ioc_Downloader().work()
