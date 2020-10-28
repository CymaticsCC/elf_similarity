本篇文章讲解内容参考文章[恶意ELF二进制文件相似度比较及可视化](https://www.freebuf.com/articles/system/243764.html)

# ELF_similarity


## ELF自动化下载

当前测试环境是

- 阿里云centos7系统
- Docker version 19.03.8, build afacb8b
- docker-compose version 1.25.4, build 8d51620a

执行以下命令：

1）构造镜像

包括基于python3的django应用镜像和基于mysql的数据库镜像

sh build.sh

2）为了将数据持久化，会创建文件夹挂载到容器上，"mysql_data"，用来存储数据库文件；初次执行时docker会自动创建这个文件夹；用户也可以自己创建，注意保证权限正确

3）启动镜像

docker-compose up 

如果希望后台启动，可以加-d选项


此时访问http://your_ip:8188即可查看Web界面，稍等片刻后，等应用抓取数据并入库后，即可显示所有信息，初次启动要等待数据库初始化。当前在阿里云的centos7 1核2G的服务器上测试，大概五分钟即可完成一次定时任务，目前是每两小时启动一次抓取任务


如果部署不成功，当前目录下的working.log会显示当前工作日志，请协同查看django容器日志与working.log来定位问题。

![阿里云搭建效果](https://github.com/CymaticsCC/elf_similarity/blob/master/pic/%E9%98%BF%E9%87%8C%E4%BA%91%E6%95%88%E6%9E%9C.png)



**注意**：该web应用只是个人研究的一个工具，没有经过任何**性能和安全的测试**，后续在数据量大的情况下，可能越来越慢，请自行修改代码



## neo4j展示ELF的文件及函数共享关系


需要环境

python3

需要第三方库

- psutil
- py2neo 

执行以下步骤：

1）启动图数据库neo4j镜像

docker run -it -d -p 7687:7687 -p 7474:7474 neo4j:3.4

2）登录neo4j的web网页修改密码 访问http://your_ip:7474

3）同步修改elf_neo4j目录下elf_neo4j.py脚本的IP及密码信息

4）将分析的not stripped的ELF放置与相应路径，并在elf_neo4j.py中修改

5）python3 elf_neo4j.py

6）在http://your_ip:7474查看关系

![图数据库文件关系](https://github.com/CymaticsCC/elf_similarity/blob/master/pic/%E5%9B%BE%E6%95%B0%E6%8D%AE%E5%BA%93%E6%96%87%E4%BB%B6%E5%85%B3%E7%B3%BB.png)

