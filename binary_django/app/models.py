from __future__ import unicode_literals

from django.db import models

# Create your models here.

class ioc_urls_record(models.Model):
    '''
        这个数据模型指每天爬虫去某些数据源得到的信息，每天都在更新
    '''
    url = models.TextField()
    is_download = models.BooleanField(default = False)
    add_date = models.DateTimeField(auto_now_add = True)
    source = models.TextField()
    status = models.BooleanField()
    
    def __str__(self):
        return "%s from %s added on %s" % (self.url, self.source, self.add_date.strftime("%Y-%m-%d %H:%M:%S"))


class ioc_urls_work_log(models.Model):
    url_count = models.IntegerField()
    work_date = models.DateTimeField(auto_now_add = True)
    work_succ_flag = models.BooleanField(default = False)
    work_stats = models.TextField()


class ioc_urls(models.Model):
    '''
        这个模型是完全去重记录的
    '''
    url_sha256 = models.CharField(max_length = 255,primary_key = True)
    url = models.TextField()
    status = models.BooleanField()
    source = models.TextField()
    first_add_date = models.DateTimeField(auto_now_add = True)
    status_check_date = models.DateTimeField(auto_now = True)
    up_days = models.IntegerField(default = 1)

    def __str__(self):
        return "url %s from %s" % (self.url,self.source)

class download_record(models.Model):
    file_sha256 = models.TextField()
    download_url = models.TextField()
    download_url_id = models.IntegerField()
    download_date = models.DateTimeField(auto_now_add = True)
    download_path = models.TextField()
    file_info = models.TextField(default = "")
    added_to_binary_table = models.BooleanField(default = False)


class binary(models.Model):
    sha256 = models.CharField(max_length = 64,primary_key =True) 
    binary_ori_name = models.TextField()
    file_path = models.TextField()
    file_info = models.TextField()

    add_from_url = models.BooleanField(default = True)
    download_url = models.TextField()
    download_record_id = models.IntegerField()
    add_from_file = models.BooleanField(default = False)
    add_date = models.DateTimeField(auto_now_add = True)

    ssdeep_value = models.TextField()

    def __str__(self):
        info = ""
        if self.add_from_url:
            info = "%s downloaded from %s" % (self.binary_ori_name, self.download_url)
        else:
            info = "%s uploaded by self" % self.binary_ori_name
        return info

class ssdeep_compare(models.Model):
    left_file = models.CharField(max_length = 64)
    right_file = models.CharField(max_length = 64)
    ssdeep_res = models.IntegerField()

    class Meta:
        unique_together = (("left_file","right_file"),)
