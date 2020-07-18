#! /bin/python3
#coding:utf-8
#2020/07/12

import requests
from requests.exceptions import ConnectionError,Timeout
import abc

class Url_Loader(metaclass = abc.ABCMeta):

    def __init__(self, data):
        self.data = None
        self.urls = []

        if data is not None:
            self.data = data
        else:
            self.download_ioc_html(self.url)
        
        self.work()

    def download_ioc_html(self, url):
        try:
            response = requests.get(url, timeout = (5,5))
        except Exception as e:
            raise e

        self.data = response.text
        self.data.replace("\r\n","\n")

    def work(self):
        self.parse_html_to_lines()
        self.filter_html_line()
        self.obtain_urls()
        self.filter_url()
        self.filter_url_black()

    def filter_url_black(self):
        self.urls = list(filter(lambda x: "bolizarsospos.com" not in x, self.urls))


    def parse_html_to_lines(self):
        data = self.data.split("\n")[self.start_line:]
        data = list(filter(lambda x: len(x) > 0, data))
        self.data = data

    def obtain_urls(self):
        self.urls = list(map(self.parse_one_line, self.data))
    
    def return_url_list(self):
        return self.urls

    @abc.abstractmethod
    def parse_one_line(self,x):
        pass
    
    @abc.abstractmethod
    def filter_html_line(self):
        pass

    @abc.abstractmethod
    def filter_url(self):
        pass

    def __str__(self):
        if len(self.urls) > 0:
            return "\n".join(self.urls)
        else:
            return "There is no url in this loader"

class Osint_Loader(Url_Loader):
    
    url = "https://osint.digitalside.it/Threat-Intel/lists/latesturls.txt"
    url_source = "osint"
    start_line = 11

    filter_tuple = (".bat",".cab",".txt",".zip",".exe",".doc",".apk",".png",".jpg", ".dll", ".jar", ".php")
    def __init__(self, data = None):
        Url_Loader.__init__(self, data)

    def filter_html_line(self):
        pass

    def filter_url(self):
        self.urls = list(filter(lambda x: ( "Mozi.m" not in x ) & \
                                          ( not x.endswith(".i")) & \
                                          ( not x.endswith("/")) & \
                                          ( x[-4:]  not in self.filter_tuple ), self.urls))

    def parse_one_line(self,one_line):
        return one_line

class URLhaus_Loader(Url_Loader):

    url = "https://urlhaus.abuse.ch/downloads/csv_online/"
    start_line = 9
    url_source = "urlhaus"
    
    def __init__(self,data = None):
        Url_Loader.__init__(self,data)

    def filter_html_line(self):
        self.data = list(filter(lambda x: ( "elf" in x ), self.data))

    def filter_url(self):
        #当前规则，过滤elf类型的二进制
        self.urls = list(filter(lambda x: ( not x.endswith("/")) & \
                                          ( not x.endswith(".i")) & \
                                          ( not x.endswith(".exe")) & \
                                          ( "Mozi.m" not in x) , self.urls))
    
    def parse_one_line(self,one_line):
        url = one_line.split("\"")[5]
        return url

def loader_test():

    data = None 
    with open("latext.txt", "r") as f:
       data = f.read()

    test_url = Osint_Loader(data)
    print(test_url)


if __name__ == "__main__":
    loader_test()
