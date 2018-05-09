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
    
    rows = ws.rows
    for row in rows:
        for i,cell in enumerate(row):
            cell.value

    for host,(username,password,dbname,charset) in sqls.items():
        connection = pymysql.connect(host=host,user=username,password=password,db=dbname,charset=charset)
        try:
            #with connection.cursor() as cursor:

            connection.commit()
        finally:
            connection.close()

    print("Finished.")
    