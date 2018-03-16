#-*-coding:utf-8-*-
#＝＝＝＝＝＝奶粉分析器＝＝＝＝＝＝＝＝
#Python 2.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de


import sys
import lxml.html
import openpyxl.workbook
import re


def preprocess(htmlstring):
    try:
        res = htmlstring.decode('utf-8')
    except Exception as error:
        print error
        print 'delete illegal multibyte sequence...'
        pos = re.findall('decodebytesinposition(\d+)-(\d+):illegal',str(error).replace(' ',''))
        if len(pos) != 0:
            htmlstring = htmlstring[0:int(pos[0][0])] + htmlstring[int(pos[0][1]):]
            return preprocess(htmlstring)
    else:
        return res

def aptamil():
    print("Analysing aptamil...\n")
    htmlstring = open('test.html','r').read()
    htmltree = lxml.html.document_fromstring(preprocess(htmlstring))

    products = htmltree.xpath('//*[@id="mainsrp-itemlist"]/div/div/div[1]/*[@data-category="auctions"]')
    print(products)

    print("\nFinished.")