from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse


def index(request):
    context = {}
    template = loader.get_template('app/index.html')
    return HttpResponse(template.render(context, request))


def gentella_html(request):
    context = {}
    # The template to be loaded as per gentelella.
    # All resource paths for gentelella end in .html.

    # Pick out the html file name from the url. And load that template.
    load_template = request.path.split('/')[-1]
    template = loader.get_template('app/' + load_template)
    return HttpResponse(template.render(context, request))

import json
from .models import download_record
from .models import ioc_urls_record
from .models import binary
from .models import ioc_urls_work_log
from .models import ssdeep_compare

import random

def json_test(request):
    
    com_res = ssdeep_compare.objects.all().order_by("-ssdeep_res")[:1500]

    link_json = {}
    
    all_node = list(map(lambda x:x.left_file, com_res))
    all_node.extend(list(map(lambda x:x.right_file,com_res)))
    all_node = list(set(all_node))
    
    all_type = binary.objects.values("file_info").distinct()
    type_list = list(map(lambda x: x['file_info'], all_type)) 
    type_list = set((map(lambda x: x.split(",")[1][1:], type_list)))
    
    link_json['sample_count'] = len(all_node)
    link_json['type_count'] = len(type_list)

    link_json['categories'] = [{"name":value} for value in type_list]
    def get_node_category(type_list, node_file_info):
        node_file_info = node_file_info.split(",")[1].strip(" ")
        for index,one in enumerate(type_list):
            if one == node_file_info:
                return index

    def get_node_info(sha256):
        node_info = {}
        binary_obj = binary.objects.filter(sha256 = sha256 )[0]
        node_info['name'] = binary_obj.binary_ori_name
        node_info['value'] = 1
        node_info['category'] = get_node_category(type_list, binary_obj.file_info)
        return node_info

    link_json['nodes'] = []
    for one in all_node:
        link_json['nodes'].append(get_node_info(one))


    link_json['links'] = []
    for one in com_res:
        link = {}
        if one.ssdeep_res > 0:
            link['source'] = all_node.index(one.left_file)
            link['target'] = all_node.index(one.right_file)
            link_json['links'].append(link)
        
    return HttpResponse(json.dumps(link_json))


def binaries(request):

    context = {}



    binary_list = binary.objects.all().order_by('file_info')

    if len(binary_list) == 0:
        pass
    else:
        return_doc = ""

        for one in binary_list:
            return_doc += '''
<tr>
    <td>{file_name}</td>
    <td>ELF</td>
    <td>{file_info}</td>
    <td>{sha256}</td>
    <td>{download_url}</td>
    <td>{download_date}</td>
</tr>'''.format(
            file_info = one.file_info,
            file_name = one.binary_ori_name,
            sha256 = one.sha256,
            download_url = one.download_url,
            download_date = one.add_date.strftime("%Y-%m-%d %H:%M:%S"))
        context['binaries_info'] = return_doc

    load_template = request.path.split('/')[-1]
    template = loader.get_template('app/' + load_template)
    return HttpResponse(template.render(context, request))

def urls_info(request):
    context = {}

    url_list = ioc_urls_record.objects.filter(status = True)[:200]
    if len(url_list) == 0:
        pass
    else:
        return_doc = ""
        for one in url_list:
            return_doc += '''<tr>
                                <td>{url}</td>
                                <td>{date}</td>
                                <td>{status}</td>
                             </tr>
                          '''.format(
                        url = one.url,
                        date = one.add_date.strftime("%Y-%m-%d %H:%M:%S"),
                        status = "True" if one.status else "False"
                        )
        context["urls_info"] = return_doc

    load_template = request.path.split('/')[-1]
    template = loader.get_template('app/' + load_template)
    return HttpResponse(template.render(context, request))


def binary_urls(request):
    context = {}
    
    #获取url列表并填充
    url_list = ioc_urls_record.objects.filter(status = True)[:200]
    
    url_count = ioc_urls_record.objects.values("url").distinct().count()
    url_alive = ioc_urls_record.objects.filter(status = True).values("url").distinct().count()
    url_dead = url_count - url_alive
    context["total_url_count"] = str(url_count)
    context["alive_url_count"] = str(url_alive)
    context["dead_url_count"] = str(url_dead)

    binary_list = download_record.objects.values("file_sha256").distinct().count()
    context["download_binary_count"] = str(binary_list)


    tasks_list = ioc_urls_work_log.objects.all().order_by("-work_date")[:5]
    
    if len(tasks_list) == 0:
        pass
    else:
        return_doc = ""
        for one in tasks_list:
            return_doc += '''
<tr>
    <td>{work_time}</td>
    <td>{work_res}</td>
    <td>{url_count}</td>
    <td>{work_stats}</td>
</tr>'''.format(
        work_time = one.work_date.strftime("%Y-%m-%d %H:%M:%S"),
        work_res = "成功" if one.work_succ_flag else "失败",
        url_count = one.url_count,
        work_stats = one.work_stats
    )
        context["tasks_info"] = return_doc



    if len(url_list) == 0:
        pass
    else:
        return_doc = ""

        for one in url_list:
            return_doc += '''<tr>
                                <td>{url}</td>
                                <td>{date}</td>
                                <td>{status}</td>
                             </tr>
                          '''.format(
                        url = one.url,
                            date = one.add_date.strftime("%Y-%m-%d %H:%M:%S"),
                            status = "True" if one.status else "False"
                        )
        context["ioc_urls"] = return_doc
    
    url_list = ioc_urls_record.objects.filter(status = True)[:20]
    if len(url_list) == 0:
        pass
    else:
        return_doc = ""
        for one in url_list:
            return_doc += '''<tr>
                            <td>{url}</td>
                            <td>{date}</td>
                            <td>{status}</td>
                         </tr>
                      '''.format(
                    url = one.url,
                    date = one.add_date.strftime("%Y-%m-%d %H:%M:%S"),
                    status = "True" if one.status else "False"
                    )
        context["urls_info"] = return_doc

    binary_list = binary.objects.all().order_by('file_info')[:20]

    if len(binary_list) == 0:
        pass
    else:
        return_doc = ""

        for one in binary_list:
            return_doc += '''
<tr>
    <td><a href="/static/binary/{md5}">{file_name}</a></td>
    <td>ELF</td>
    <td>{file_info}</td>
    <td>{md5}</td>
    <td>{download_url}</td>
    <td>{download_date}</td>
</tr>'''.format(
            file_info = one.file_info,
            file_name = one.binary_ori_name,
            md5 = one.sha256,
            download_url = one.download_url,
            download_date = one.add_date.strftime("%Y-%m-%d %H:%M:%S"))
        context['binaries_info'] = return_doc

    load_template = request.path.split('/')[-1]
    if load_template == "":
        load_template = "data_stats.html"
    template = loader.get_template('app/' + load_template)
    return HttpResponse(template.render(context, request))
