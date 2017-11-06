#-*-coding:utf-8-*-
#＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝访问语法树＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
#Python 2.7
#author: Xiang Fu



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
        basepath = '//*[@id="normalorder"]//table[@class="tabl_merch"]'
        books = self._htmltree.xpath(basepath + '//*[@name="productname"]')
        titles = self._htmltree.xpath(basepath + '//*[@name="productname"]/@title')
        hrefs = self._htmltree.xpath(basepath + '//*[@name="productname"]/@href')
        prices = self._htmltree.xpath(basepath + '//*[@class="tab_w3"]')
        bonuses = self._htmltree.xpath(basepath + '//*[@class="tab_w2"]')
        amounts = self._htmltree.xpath(basepath + '//*[@class="tab_w6"]')
        sums = self._htmltree.xpath(basepath + '//*[@class="tab_w4"]')

        ordernr = self._htmltree.xpath('//*[@id="normalorder"]//div[@id="divorderhead"][@class="order_news"]/p/text()')
        ordertime = self._htmltree.xpath('//*[@id="normalorder"]//div[@id="divorderhead"][@class="order_news"]//span[@class="order_news_hint"]/span')
        others = self._htmltree.xpath('//*[@id="normalorder"]//table[@class="tabl_other"]//span')
        endprice = self._htmltree.xpath('//*[@id="normalorder"]//div[@class="price_total"]/span[1]')

        wb = openpyxl.Workbook()
        ws = wb.active
        for i,book in enumerate(books):
            #lxml.html.tostring(book,pretty_print=True,encoding='utf-8')

            ws.cell(row=i+1,column=1,value=titles[i]).hyperlink = hrefs[i]
            res = prices[i].xpath('./span')
            if len(res) == 0: #没有折扣
                ws.cell(row=i+1,column=2,value=prices[i].text)
            else:
                ws.cell(row=i+1,column=2,value=res[0].text)
            ws.cell(row=i+1,column=3,value=bonuses[i].text)
            ws.cell(row=i+1,column=4,value=amounts[i].text)
            ws.cell(row=i+1,column=5,value=sums[i].text)

        lastrow = i+1

        #订单号，下单时间
        for nr in ordernr:
            if nr.strip(' \n\t'):
                nr = nr.strip(' \n\t')
                break
        if len(ordertime) == 0:
            ws.cell(row=lastrow+1,column=1,value=nr)
        elif len(ordertime) == 1:
            ws.cell(row=lastrow+1,column=1,value=nr+ordertime[0].text)
        elif len(ordertime) == 2:
            ws.cell(row=lastrow+1,column=1,value=nr+ordertime[0].text+ordertime[1].text)

        #最终价
        ws.cell(row=lastrow+1,column=6,value=endprice[0].text)

        for i,elem in enumerate(others):
            if i == 0:
                ws.cell(row=lastrow+1,column=5,value=others[0].text)
            else:
                ws.cell(row=lastrow+1+i-1,column=3,value=others[i].text)
        
        wb.save('_books.xlsx')
        



def visitorStart(file):
    print("Starting visitor...\n")
    visitor = Visitor(file)
    visitor.searchOrderGoods()
    print("\nFinished.")