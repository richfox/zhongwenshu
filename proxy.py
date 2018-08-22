#-*-coding:utf-8-*-
#＝＝＝＝＝＝代理设置＝＝＝＝＝＝＝＝
#Python 2.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de
#
#Example: 
#when meet the error: requests.exceptions.ConnectTimeout: HTTPConnectionPool(host='product.dangdang.com', port=80): Max retries exceeded with url: /20771648.html
#requests.get('http://product.dangdang.com/20771648.html',timeout=5,headers=get_http_headers(),proxies=get_http_proxies())


import sys
import random
import requests


USER_AGENTS = ["Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 Version/12.16",
               "Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14",
               "Mozilla/5.0 (Windows NT 6.0; rv:2.0) Gecko/20100101 Firefox/4.0 Opera 12.14",
               "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0) Opera 12.14",
               "Opera/12.80 (Windows NT 5.1; U; en) Presto/2.10.289 Version/12.02",
               "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
               "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36",
               "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36",
               "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36",
               "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2226.0 Safari/537.36",
               "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
               "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0",
               "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0",
               "Mozilla/5.0 (X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/31.0",
               "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20130401 Firefox/31.0",
               "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"]


def get_http_headers():
    return {'User-Agent':random.choice(USER_AGENTS)}

#实时代理IP抓取
#https://proxy.mimvp.com/
#https://www.baibianip.com/api/doc.html
#http://ip.jiangxianli.com/
def get_http_proxies():
    proxies = []
    #todo
    proxies.append({'http':'http://139.224.24.26:8888','https':'http://139.224.24.26:8888'})
    proxies.append({'http':'http://219.141.153.11:8080','https':'http://219.141.153.11:8080'})
    proxies.append({'http':'http://223.93.172.248:3128','https':'http://223.93.172.248:3128'})
    proxies.append({'http':'http://117.27.144.248:8088','https':'http://117.27.144.248:8088'})
    return proxies


def get_html_text_with_proxy(url):
    text = ""
    for proxy in get_http_proxies():
        try:
            res = requests.get(url,timeout=6,headers=get_http_headers(),proxies=proxy)
            if res.ok:
                print(proxy['http'] + " fetched successfully!")
                text = res.text
                break
        except:
            continue
    return text


def get_html_text(url):
    text = ""
    try:
        text = requests.get(url).text
    except requests.exceptions.ConnectTimeout:
        print("timeout, try with another IP...")
        text = get_html_text_with_proxy(url)
    except requests.exceptions.ConnectionError:
        print("connection failed, try with another IP...")
        text = get_html_text_with_proxy(url)
    except:
        print("unexpected error:",sys.exc_info()[0])
    else:
        print(url + " fetched successfully!")
    return text