#-*-coding:utf-8-*-
#＝＝＝＝＝＝登书系统＝＝＝＝＝＝＝＝
#Python 2.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de

import io
import re
import pymysql
import requests
import xml
import lxml



def SpiderToSQL(sqls):
    print("Spider to SQL start...\n")

    for host,(username,password,dbname,charset,urls) in sqls.items():
        connection = pymysql.connect(host=host,user=username,password=password,db=dbname,charset=charset)
        try:
            for url,tag in urls.items():
                htmltext = requests.get(url).text
                parser = lxml.html.HTMLParser()
                htmltree = xml.etree.ElementTree.fromstring(htmltext,parser)
                #res = lxml.html.tostring(htmltree,pretty_print=True)
                #print(res)

                
        finally:
            connection.close()

    print("Finished.")