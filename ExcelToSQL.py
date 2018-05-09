#-*-coding:utf-8-*-
#＝＝＝＝＝＝订单导入系统＝＝＝＝＝＝＝＝
#Python 2.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de


import io
import re
import pymysql
import openpyxl.workbook



def ExcelToSQLGBuy(sqls):
    print("excel to SQL start...\n")

    for host,(username,password,dbname,charset) in sqls.items():
        connection = pymysql.connect(host=host,user=username,password=password,db=dbname,charset=charset)
        try:
            #with connection.cursor() as cursor:

            connection.commit()
        finally:
            connection.close()

    print("Finished.")
    