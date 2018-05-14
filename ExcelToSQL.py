#-*-coding:utf-8-*-
#＝＝＝＝＝＝订单导入系统＝＝＝＝＝＝＝＝
#Python 2.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de


import io
import re
import pymysql
import openpyxl.workbook



def ExcelToSQLGBuy(sqls,params):
    print("excel to SQL start...\n")

    #read excel data
    wb = openpyxl.load_workbook('_jsform.xlsx')
    ws = wb.active
    
    orders = {}
    books = []
    for row,cells in enumerate(ws.rows):
        booknums = []
        for col,cell in enumerate(cells):
            if row == 0:
                ddsn = re.findall(u'\[([0-9]+)\]',cell.value.replace(u' ',u''))
                if ddsn:
                    books.append(ddsn[0])
            else:
                if col == 0:
                    orderid = cell.value
                elif col>0 and col<=len(books):
                    booknums.append(cell.value)
                    
        if row != 0:
            orders[orderid] = booknums


    for host,(username,password,dbname,charset) in sqls.items():
        connection = pymysql.connect(host=host,user=username,password=password,db=dbname,charset=charset)
        try:
            #with connection.cursor() as cursor:

            connection.commit()
        finally:
            connection.close()

    print("Finished.")
    