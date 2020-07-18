#! /bin/python
#coding:utf-8
#Date: 2020/07/11

import os
import psutil
from subprocess import PIPE
import traceback

def get_symboltable_readelf(file_name):

    p = psutil.Popen(["readelf","-s",file_name],stdin = PIPE, stdout = PIPE)
    #python3版本需要将byte类型的数据转化为字符串
    symboltable_info = p.stdout.read().decode("utf-8")
    
    return symboltable_info

def parse_raw_output_symboltable(output, sym_type):

    output = output.split("\n")
    #去除开头和结果的空格
    output = list(map(lambda x: x.strip(), output))

    #filter type FILE
    output = list(filter(lambda x: (sym_type in x) & \
                                   ("HIDDEN" not in x), output))
    
    #去除一些系统函数，后续可以继续添加
    output = list(filter(lambda x: 
                                ("str" not in x) & \
                                ("libc" not in x) & \
                                ("mem" not in x) & \
                                ("pthread" not in x ) & \
                                ("sys" not in x) & \
                                ("GI" not in x) & \
                                ("call" not in x) & \
                                ("aeabi" not in x), output))
    #按照空格划分
    output = list(map(lambda x: x.split(" "), output))
    
    #移除空字符串
    def remove_empty(x):
        while "" in x:
            x.remove("")
        return x
    
    output = list(map(remove_empty, output))
    
    #去除一些系统函数   
    output = list(filter(lambda x: ("__" not in x[7]) & \
                        (not x[7].startswith("_L_")) & \

                        ("_IO" not in x[7]) & \
                        ("_Unwind" not in x[7]), output)) 
    return output

def obtain_type_and_name(one_line_table):
    return one_line_table[3],one_line_table[7]
    
def obtain_sym_table(file_name, sym_type):
    symbol_table = parse_raw_output_symboltable(get_symboltable_readelf(file_name),sym_type)
    file_table = list(map(obtain_type_and_name, symbol_table))
    
    return file_table

binary_path = "./elf"

if __name__ == "__main__":
    
    count = 0

    file_table_list = []
    try:
        for one_file in os.listdir(binary_path):
            count += 1
            file_table_list.extend(obtain_sym_table("./elf/" + one_file, "FUNC"))
    
        for one in file_table_list:
            print(one)
    except Exception as e:
        traceback.print_exc()
