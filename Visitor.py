#-*-coding:utf-8-*-
#＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝访问语法树＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
#Python 2.7



import sys
import lxml.html



class Visitor:
    def __init__(self,file):
        htmltree = lxml.html.parse(file)
        print(lxml.html.tostring(htmltree,pretty_print=True))
        self._htmltree = htmltree

    def searchOrderGoods(self):
        res = self._htmltree.xpath('//*[@id="normalorder"]//table//*[@name="productname"]')
        print(lxml.html.tostring(res[0],pretty_print=True))
        



def visitorStart(file):
    print("Starting visitor...\n")
    visitor = Visitor(file)
    visitor.searchOrderGoods()
    print("\nFinished.")