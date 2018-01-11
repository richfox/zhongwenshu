#-*-coding:utf-8-*-
#＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝访问语法树＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
#Python 2.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de



import sys
import lxml.html
import openpyxl.workbook
import re


class Visitor:
    def __init__(self,file):
        htmlstring = open(file,'r').read()
        htmltree = lxml.html.document_fromstring(self.preprocess(htmlstring))
        self._htmltree = htmltree

    #预处理，比如先删除一些非法字符
    def preprocess(self,htmlstring):
        try:
            res = htmlstring.decode('gb2312')
        except Exception as error:
            print error
            print 'delete illegal multibyte sequence...'
            pos = re.findall('decodebytesinposition(\d+)-(\d+):illegal',str(error).replace(' ',''))
            if len(pos) != 0:
                htmlstring = htmlstring[0:int(pos[0][0])] + htmlstring[int(pos[0][1]):]
                return self.preprocess(htmlstring)
        else:
            return res

    def searchOrderGoods(self):
        basepath = '//*[@id="normalorder"]//*[@class="merch_bord"]//table[@class="tabl_merch"]'
        books = self._htmltree.xpath(basepath + '//*[@class="tab_w1"]/*[@name="productname"]')
        titles = self._htmltree.xpath(basepath + '//*[@class="tab_w1"]/*[@name="productname"]/@title')
        hrefs = self._htmltree.xpath(basepath + '//*[@class="tab_w1"]/*[@name="productname"]/@href')
        prices = self._htmltree.xpath(basepath + '//*[@class="tab_w3"]')
        bonuses = self._htmltree.xpath(basepath + '//*[@class="tab_w2"]')
        amounts = self._htmltree.xpath(basepath + '//*[@class="tab_w6"]')
        sums = self._htmltree.xpath(basepath + '//*[@class="tab_w4"]')

        #换购商品
        subbooks = self._htmltree.xpath(basepath + '//*[@class="tab_w1"]/*[@class="present"]')

        ordernr = self._htmltree.xpath('//*[@id="normalorder"]//div[@id="divorderhead"][@class="order_news"]/p/text()')
        ordertime = self._htmltree.xpath('//*[@id="normalorder"]//div[@id="divorderhead"][@class="order_news"]//span[@class="order_news_hint"]/span')
        others = self._htmltree.xpath('//*[@id="normalorder"]//table[@class="tabl_other"]//span')
        endprice = self._htmltree.xpath('//*[@id="normalorder"]//div[@class="price_total"]/span[1]')
        payment = self._htmltree.xpath('//*[@id="normalorder"]//*[@class="order_detail_frame"]/ul[position()=4]/li')

        wb = openpyxl.Workbook()
        ws = wb.active
        j = 0
        for i,book in enumerate(books):
            #lxml.html.tostring(book,pretty_print=True,encoding='utf-8')

            #预售商品
            res = book.xpath('../span[@class="c_red"]')
            if len(res) != 0: #是预售
                ws.cell(row=i+j+1,column=1,value='[YS] ' + titles[i]).hyperlink = hrefs[i]
            else:
                ws.cell(row=i+j+1,column=1,value=titles[i]).hyperlink = hrefs[i]

            if len(prices[i].xpath('./text()')) != 0: #没有折扣的情况，比如订单35737447378 
                ws.cell(row=i+j+1,column=2,value=prices[i].text)
            else:
                res = prices[i].xpath('./span')
                ws.cell(row=i+j+1,column=2,value=res[0].text)

            ws.cell(row=i+j+1,column=3,value=bonuses[i].text)
            ws.cell(row=i+j+1,column=4,value=amounts[i].text)

            #小计以数字形式保存
            sum = re.findall('\d+.\d+',sums[i].text)[0]
            ws.cell(row=i+j+1,column=5,value=sum)

            #换购商品
            res = books[i].xpath('../br')
            if len(res) != 0: #有换购
                j += 1
                hgtitle = books[i].xpath('../a[2]/@title')
                hghref = books[i].xpath('../a[2]/@href')
                hgprice = prices[i].xpath('./span/text()')
                hgamount = amounts[i].xpath('./text()[2]')
                hgsum = sums[i].xpath('./text()[2]')
                
                ws.cell(row=i+j+1,column=1,value='[HG] ' + hgtitle[0]).hyperlink = hghref[0]
                if len(hgprice) != 0:
                    ws.cell(row=i+j+1,column=2,value=hgprice[0])
                if len(hgamount) != 0:
                    ws.cell(row=i+j+1,column=4,value=hgamount[0])
                if len(hgsum) != 0:
                    ws.cell(row=i+j+1,column=5,value=re.findall('\d+.\d+',hgsum[0])[0])


        lastrow = len(books) + len(subbooks)

        #订单号，下单时间，付款方式
        nr = ''
        for n in ordernr:
            if n.strip(' \n\t'):
                nr = n.strip(' \n\t')
                break
        if len(ordertime) == 0:
            ws.cell(row=lastrow+1,column=1,value=nr+payment[0].text)
        elif len(ordertime) == 1:
            ws.cell(row=lastrow+1,column=1,value=nr+ordertime[0].text+payment[0].text)
        elif len(ordertime) == 2:
            ws.cell(row=lastrow+1,column=1,value=nr+ordertime[0].text+ordertime[1].text+payment[0].text)

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