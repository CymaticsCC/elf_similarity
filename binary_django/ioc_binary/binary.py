#! /bin/python
#coding:utf-8
#Date:2020/06/22


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
import logging
import ssdeep

def create_binary_from_download():
    download_list = download_record.objects.filter(added_to_binary_table = False)
    logging.info("Start to insert %d binary records." % len(download_list))
    for one in download_list:
        if one.file_info.startswith("ELF"):
            ori_name = one.download_url.split("/")[-1]
            try:
                obj = binary(
                        sha256 = one.file_sha256,
                        binary_ori_name = ori_name,
                        file_path = one.download_path,
                        file_info = one.file_info,
                        download_record_id = one.id,
                        add_date = timezone.now(),
                        download_url = one.download_url,
                        ssdeep_value = ssdeep.hash_from_file(one.download_path)
                    )
                obj.save()
            except Exception as e:
                pass

        one.added_to_binary_table = True
        one.save()
    logging.info("Insert all binary records.")

if __name__ == "__main__":
    create_binary_from_download()

