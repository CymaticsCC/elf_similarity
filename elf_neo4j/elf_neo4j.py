#! /bin/python3
#coding:utf-8
#2020/07/11 

from py2neo import Graph, Node, Relationship
import traceback
import sys
#修改为你的IP
your_ip = ""
username = "neo4j"
#修改为你的密码
password = "your_password"
#修改为存放要分析的ELF的文件夹名字
binary_path = "./yakuza/"

try:
	graph = Graph("http://"+ your_ip + ":7474",username = username, password = password)
	#删除所有节点
	#graph.delete_all()
except Exception as e:
	traceback.print_exc()
	print("Some error happened when load graph db.")
	sys.exit(1)


import psutil
from subprocess import PIPE
import collections
import os

from  elf_relations import obtain_sym_table

file_list = []
file_arch_list = []
file_attr_list = []
func_attr_list = []


def get_file_arch(file_name):

    #这里暂时只关注二进制和shell类型文件
    p = psutil.Popen(["file",file_name], stdin = PIPE, stdout=PIPE,stderr = PIPE)
    file_info = str(p.stdout.read())
    file_info = file_info.split(":")[1][1:-3]
    return file_info.split(",")[1][1:]

for one in os.listdir(binary_path):
    file_list.append(one)
    file_attr_list.extend(obtain_sym_table(binary_path + one,"FILE"))
    func_attr_list.extend(obtain_sym_table(binary_path + one,"FUNC"))
    file_arch_list.append(get_file_arch(binary_path + one))


file_attr_list = list(set(file_attr_list))
func_attr_list = list(set(func_attr_list))


file_node_list = []
file_attr_node_list = []
func_attr_node_list = []



for index,one in  enumerate(file_list):
    arch = file_arch_list[index]
    file_node_list.append(Node(arch,name = one))

    
for one in file_attr_list:
    file_attr_node_list.append(Node("FILE table",name = one[1]))

for one in func_attr_list:
    func_attr_node_list.append(Node("FUNC table", name = one[1]))

print("Last %d items in file_attr_list" % len(file_attr_list))
print("Last %d items in func_attr_list" % len(func_attr_list))

file_count = 0

for index,one in enumerate(file_list):
    file_count += 1
    file_table = obtain_sym_table(binary_path + one, "FILE")

    for one_attr in file_table:
        try:
            attr_node = file_attr_node_list[file_attr_list.index(one_attr)]
        except ValueError as e: 
            continue
        file_node = file_node_list[index]
        r = Relationship(file_node, "file", attr_node)
        s = file_node | attr_node | r
        graph.create(s)

    func_table = obtain_sym_table(binary_path + one, "FUNC")
    
    for one_attr in func_table:
        try:
            attr_node = func_attr_node_list[func_attr_list.index(one_attr)]
        except ValueError as e: 
            continue
        file_node = file_node_list[index]
        r = Relationship(file_node, "func", attr_node)
        s = file_node | attr_node | r
        graph.create(s)

print("Insert %d elf file node" % file_count)
