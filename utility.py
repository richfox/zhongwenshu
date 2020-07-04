#-*-coding:utf-8-*-
#＝＝＝＝＝＝＝＝＝＝＝＝＝＝
#Python 3.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de


import io
import re
import xml.etree.ElementTree
import lxml.html
import lxml.etree
import json
import sys
import requests
import proxy

def get_html_text(url,cookies=None):
    htmltext = ""
    try:
        htmltext = requests.get(url,headers=proxy.get_http_headers(),cookies=cookies).text
    except requests.exceptions.ConnectTimeout:
        print("timeout, try with another IP...")
        htmltext = proxy.get_html_text_with_proxy(url,cookies=cookies)
    except requests.exceptions.ConnectionError:
        print("connection failed, try with another IP...")
        htmltext = proxy.get_html_text_with_proxy(url,cookies=cookies)
    except requests.exceptions.InvalidURL:
        print("invalid url")
    except:
        print("unexpected error: {0} {1}".format(sys.exc_info()[0],"try with another IP..."))
        htmltext = proxy.get_html_text_with_proxy(url,cookies=cookies)
    else:
        print(url + " fetched successfully!")
    return htmltext

def get_html_byte(url):
    bytes = b""
    try:
        bytes = requests.get(url,headers=proxy.get_http_headers()).content
    except requests.exceptions.ConnectTimeout:
        print("timeout, try with another IP...")
        bytes = proxy.get_html_byte_with_proxy(url)
    except requests.exceptions.ConnectionError:
        print("connection failed, try with another IP...")
        bytes = proxy.get_html_byte_with_proxy(url)
    except requests.exceptions.InvalidURL:
        print("invalid url")
    except:
        print("unexpected error: {0} {1}".format(sys.exc_info()[0],"try with another IP..."))
        bytes = proxy.get_html_byte_with_proxy(url)
    else:
        print(url + " fetched successfully!")
    return bytes

def post_html_text(url):
    htmltext = ""
    try:
        htmltext = requests.post(url,headers=proxy.get_http_headers()).text
    except requests.exceptions.ConnectTimeout:
        print("timeout, try with another IP...")
        htmltext = proxy.post_html_text_with_proxy(url)
    except requests.exceptions.ConnectionError:
        print("connection failed, try with another IP...")
        htmltext = proxy.post_html_text_with_proxy(url)
    except requests.exceptions.InvalidURL:
        print("invalid url")
    except:
        print("unexpected error: {0} {1}".format(sys.exc_info()[0],"try with another IP..."))
        htmltext = proxy.post_html_text_with_proxy(url)
    else:
        print(url + " fetched successfully!")
    return htmltext

def post_html_byte(url):
    bytes = b""
    try:
        bytes = requests.post(url,headers=proxy.get_http_headers()).content
    except requests.exceptions.ConnectTimeout:
        print("timeout, try with another IP...")
        bytes = proxy.post_html_byte_with_proxy(url)
    except requests.exceptions.ConnectionError:
        print("connection failed, try with another IP...")
        bytes = proxy.post_html_byte_with_proxy(url)
    except requests.exceptions.InvalidURL:
        print("invalid url")
    except:
        print("unexpected error: {0} {1}".format(sys.exc_info()[0],"try with another IP..."))
        bytes = proxy.post_html_byte_with_proxy(url)
    else:
        print(url + " fetched successfully!")
    return bytes


def get_html_tree(text):
    parser = lxml.html.HTMLParser()
    htmltree = xml.etree.ElementTree.fromstring(text,parser)

    return htmltree


#语法分析html，返回语法树
def parser_html(url):
    htmltext = get_html_text(url)
    if not htmltext:
        raise Exception("html text is empty!")

    return get_html_tree(htmltext)


#在text中start位置开始找到第一个，字符串charset中的任何一个字符
#类似std::string.find_first_of()
def find_first_of(text,charset,start):
    pos = -1
    while start < len(text):
        if text[start] in charset:
            pos = start
            break
        start += 1
    return pos


#找到匹配的括号
#bpair输入格式{'(':')'}
def search_close_bracket(text,posopen,bpair):
    posclose = -1
    openstack = []
    start = posopen + 1

    charopen = list(bpair.keys())[0]
    charclose = bpair[charopen]
    charset = charopen + charclose
    pos = find_first_of(text,charset,start)
    while pos != -1:
        if text[pos] == charopen:
            openstack.append(charopen)
        elif text[pos] == charclose:
            if len(openstack) == 0:
                posclose = pos
                break
            else:
                openstack.pop()
        start = pos + 1
        pos = find_first_of(text,charset,start)

    return posclose
