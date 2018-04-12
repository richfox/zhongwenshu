#-*-coding:utf-8-*-
#＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝网页爬取图片＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
#Python 2.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de

import sys
import webbrowser
import xml.etree.ElementTree

# 正则
import re
# 操作系统功能
import os
# 网络交互
import requests
# XPath
import lxml.etree

import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)




#辅助函数
def remove_noise(section):
    res = section
    for each in re.findall(u'<.*?>',section,re.S):
        res = res.replace(each,u'').replace(u'\r\n',u'')
    return res


#爬虫类
class Spider:
    def __init__(self,url):
        # 获取网页源代码
        self._html = requests.get(url).text
        self._title = u""
        self._page = u""

    def getHtml(self):
        return self._html

    def getTitle(self):
        return self._title

    def getPage(self):
        return self._page

    #找图片
    def searchPicture(self):
        # 正则
        regX = '<img alt=\"\" src=\".*.jpg\" title=\"\" id=\"modalBigImg\">'

        #找到第一张大图
        elem_url = re.findall(regX,self._html,re.S)
        for each in elem_url:
            print(each)
            pic_url = re.findall('http://.*.jpg',each,re.S)
            webbrowser.open(pic_url[0])

        #找到共有几张图
        #问号表示非贪婪匹配
        regX = '<ul id=\"mask-small-list-slider\">.*?</ul>'
        elem_url = re.findall(regX,self._html,re.S)
        numPicture = 0
        for each in elem_url:
            pic_url = re.findall('data-imghref=\"http://.*?.jpg\"',each,re.S)
            for pic in pic_url:
                print(re.findall('http://.*.jpg',pic)[0])
                numPicture += 1
        print("Here is " + str(numPicture) + " pictures!\n")

    #找书籍信息
    def searchAttr(self):
        _title = re.findall(u'<h1 title=.*?>.*?</h1>',self._html,re.S)[0]
        print(u"title:" + remove_noise(_title))
        subtitle = re.findall(u'<h2>.*?</h2>',self._html,re.S)[0]
        print(u'subtitle:' + remove_noise(subtitle))
        author = re.findall(u'<span class=\"t1\" id=\"author\" dd_name=\"\u4f5c\u8005\".*?</span>',self._html,re.S)[0]
        print(u'author:' + remove_noise(author))
        press = re.findall(u'<span class=\"t1\" dd_name=\"\u51fa\u7248\u793e\".*?</span>',self._html,re.S)[0]
        print(u'press:' + remove_noise(press))
        presstime = re.findall(u'<span class=\"t1\">\u51fa\u7248\u65f6\u95f4.*?</span>',self._html,re.S)[0]
        print(u'press time:' + remove_noise(presstime))
        _page = re.findall(u'<li>\u9875 \u6570.*?</li>',self._html,re.S)[0]
        print(u'page:' + remove_noise(_page))
        word = re.findall(u'<li>\u5b57 \u6570.*?</li>',self._html,re.S)[0]
        print(u'word:' + remove_noise(word))
        size = re.findall(u'<li>\u5f00 \u672c.*?</li>',self._html,re.S)[0]
        print(u'size:' + remove_noise(size))
        paper = re.findall(u'<li>\u7eb8 \u5f20.*?</li>',self._html,re.S)[0]
        print(u'paper:' + remove_noise(paper))
        packing = re.findall(u'<li>\u5305 \u88c5.*?</li>',self._html,re.S)[0]
        print(u'packing' + remove_noise(packing))
        isbn = re.findall(u'<li>\u56fd\u9645\u6807\u51c6\u4e66\u53f7.*?</li>',self._html,re.S)[0]
        print(u'ISBN:' + remove_noise(isbn))
        classification = re.findall(u'<li class=\"clearfix fenlei\" dd_name=\"\u8be6\u60c5\u6240\u5c5e\u5206\u7c7b\".*?>.*?</li>',self._html,re.S)[0]
        print(u'classification:' + remove_noise(classification))
        print("")

    #找订单信息
    def searchOrder(self):
        htmltree = lxml.etree.HTML(self._html)
        print(lxml.etree.tostring(htmltree,pretty_print=True))





def spiderStart(urllist):
    print("Starting spider...\n")
    for url, tag in urllist.items():
        spider = Spider(url)
        if tag == 0:
            spider.searchPicture()
            spider.searchAttr()
        elif tag == 1:
            spider.searchOrder()
    print("\nFinished.")


def spider_picture(url):
    spider = Spider(url)
    spider.searchPicture()
