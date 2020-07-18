#! /bin/python3
#coding:utf-8

import requests
import logging
import traceback

def request_test(url):
    print("hello:")
    print(a)
    try:
        req = requests.get(url)
        return req.content
    except Exception as e:
        print(e)
        #traceback.print_exc()
        #raise e

from multiprocessing.dummy import Pool as ThreadPool

def main():
    url_list = ["http://www.qxq.comx" for i in range(5)] 
    pool = ThreadPool(3)
    pool.map(request_test, url_list)
    pool.close()
    pool.join()
    time.sleep(10)

if __name__ == "__main__":
    main()
    print("I'm fine")
