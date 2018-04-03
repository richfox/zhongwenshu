#-*-coding:utf-8-*-
#＝＝＝＝＝＝奶粉分析器＝＝＝＝＝＝＝＝
#Python 2.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de


import sys
import xml
import lxml
import openpyxl.workbook
import re
import requests
import json


def search_matched_bracket(str,bracket):
    bpair = []
    open = bracket[0]
    close = bracket[1]
    count = 0
    for pos,c in enumerate(str):
        if c == open:
            count += 1
            if count == 1:
                bpair.append(pos)
        elif c == close:
            count -= 1
            if count == 0:
                bpair.append(pos)
        if count < 0:
            break
    return bpair


def preprocess2(htmlstring):
    try:
        res = htmlstring.decode('utf-8')
    except Exception as error:
        print error
        print 'delete illegal multibyte sequence...'
        pos = re.findall('decodebytesinposition(\d+)-(\d+):illegal',str(error).replace(' ',''))
        if len(pos) != 0:
            htmlstring = htmlstring[0:int(pos[0][0])] + htmlstring[int(pos[0][1]):]
            return preprocess2(htmlstring)
    else:
        return res


def preprocess(htmlstring):
    res = htmlstring.replace('\n','')
    return res


def load_json(jsonstring):
    try:
        res = json.loads(jsonstring)
    except Exception as error:
        print error
        pos = re.findall('Expectingobject:line(\d+)column(\d+)\(char(\d+)\)',str(error).replace(' ',''))
        if pos:
            if jsonstring[int(pos[0][2])] == '}':
                jsonstring += '}' #补齐
            elif jsonstring[int(pos[0][2])] == '"':
                jsonstring += '}' #补齐
            return load_json(jsonstring)
    else:
        return res    


def aptamil():
    print("Analysing aptamil...\n")

    test = True
    htmltext = ''

    if test:
        htmltext = open('searchres.txt','r').read()
        htmltree = lxml.html.document_fromstring(preprocess(htmltext))
    else:
        url = 'https://s.taobao.com/search'
        payload = {'q':'德语版 老友记','ie':'utf-8'}
        htmltext = requests.get(url,params=payload).text
        parser = lxml.html.HTMLParser()
        htmltree = xml.etree.ElementTree.fromstring(preprocess(htmltext),parser)

    #获取script标签里的g_page_config变量，该变量是个json字符串
    scripts = htmltree.xpath('//script')
    for script in scripts:
        if script.text:
            if re.findall('g_page_config',script.text):
                bpair = search_matched_bracket(script.text,'{}')
                jsontexts = []
                if len(bpair)/2:
                    for i in range(len(bpair)/2):
                        jsontexts.append(script.text[bpair[i*2]:bpair[i*2+1]])
                        jsondata = load_json(jsontexts[i])
                        print(jsondata)
                break
    

    print("\nFinished.")