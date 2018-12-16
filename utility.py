#-*-coding:utf-8-*-
#＝＝＝＝＝＝＝＝＝＝＝＝＝＝
#Python 2.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de


import io
import re
import xml.etree.ElementTree
import lxml.html
import json
import sys
import requests
import proxy

def get_html_text(url):
    htmltext = ""
    try:
        htmltext = requests.get(url).text
    except requests.exceptions.ConnectTimeout:
        print("timeout, try with another IP...")
        htmltext = proxy.get_html_text_with_proxy(url)
    except requests.exceptions.ConnectionError:
        print("connection failed, try with another IP...")
        htmltext = proxy.get_html_text_with_proxy(url)
    except requests.exceptions.InvalidURL:
        print("invalid url")
    except:
        print("unexpected error: {0} {1}".format(sys.exc_info()[0],"try with another IP..."))
        htmltext = proxy.get_html_text_with_proxy(url)
    else:
        print(url + " fetched successfully!")
    return htmltext


def parser_html(url):
    htmltext = get_html_text(url)
    if not htmltext:
        raise Exception("html text is empty!")

    parser = lxml.html.HTMLParser()
    htmltree = xml.etree.ElementTree.fromstring(htmltext,parser)

    return htmltree
