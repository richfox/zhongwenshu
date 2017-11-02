#-*-coding:utf-8-*-
#＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝访问语法树＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
#Python 2.7



import sys
import lxml.html
import openpyxl.workbook
import re


class Visitor:
    def __init__(self,file):
        htmlstring = open(file,'r').read()
        htmltree = lxml.html.document_fromstring(htmlstring.decode('gb2312'))
        self._htmltree = htmltree

    def searchOrderGoods(self):
        basepath = '//*[@id="normalorder"]//table//*[@name="productname"]'
        books = self._htmltree.xpath(basepath)
        titles = self._htmltree.xpath(basepath+'/@title')

        wb = openpyxl.Workbook()
        ws = wb.active
        for i,title in enumerate(titles):
            #lxml.html.tostring(book,pretty_print=True,encoding='utf-8')
            col = 'A'
            row = str(i+1)
            cell = col + row
            ws[cell] = title
        wb.save('_books.xlsx')
        



def visitorStart(file):
    print("Starting visitor...\n")
    visitor = Visitor(file)
    visitor.searchOrderGoods()
    print("\nFinished.")