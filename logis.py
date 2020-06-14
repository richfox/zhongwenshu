#-*-coding:utf-8-*-
# 中德物流
#Python 3.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de

import sys
import os
import hashlib
import json
import time
import utility
import pymysql
import logging
import re
import openpyxl.workbook


def import_logis_to_sql(server,logis):
    print("Starting import logis info to database...\n")

    mysql = server["mysql"]
    connection = pymysql.connect(mysql[0],mysql[1],mysql[2],mysql[3],charset=mysql[4])

    #区分测试和主数据库
    rinterTable = ""
    logiscnTable = ""
    logisdeTable = ""
    if mysql[3] == 'zhongw_test':
        rinterTable = "zws_test_railway_inter"
        logiscnTable = "zws_test_logis_cn"
        logisdeTable = "zws_test_logis_de"
    elif mysql[3] == 'zhongwenshu_db1':
        rinterTable = "zws_railway_inter"
        logiscnTable = "zws_logis_cn"
        logisdeTable = "zws_logis_de"

    try:
        railway_sn = ""
        inter_company = ""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
        cn_packet = {}
        de_packet = {}

        for area,info in logis.items():
            if area == "inter":
                for k,v in info.items():
                    inter_company = k
                    railway_sn = v
            elif area == "cn":
                for k,v in info.items():
                    for sn in v:
                        cn_packet[sn] = k
            elif area == "de":
                for k,v in info.items():
                    for sn in v:
                        de_packet[sn] = k


        #先写入国际段物流信息，因为国际段主键是作为其他表的外键
        #再写入国内段和德国段物流信息，可以不分先后
        with connection.cursor() as cursor:
            sql = "INSERT INTO " + rinterTable + " (`id`, `railway_sn`, `inter_log`, `inter_time`, `inter_status`, `inter_company`) \
                  VALUES (NULL, %s, '', %s, '-1', %s);"
            cursor.execute(sql,(railway_sn,timestamp,inter_company))

            #log
            LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
            logging.basicConfig(filename='mylogis.log',level=logging.DEBUG,format=LOG_FORMAT)
            logging.info(sql % ("'"+railway_sn+"'","'"+timestamp+"'","'"+inter_company+"'"))

            sql = "SELECT `id` FROM " + rinterTable + " WHERE `railway_sn`=%s"
            cursor.execute(sql,railway_sn)
            rinterid = cursor.fetchone()[0]
            print("inter id : " + str(rinterid))

            for sn,company in cn_packet.items():
                sql = "INSERT INTO " + logiscnTable + " (`id`, `cn_packet_sn`, `railway_id`, `cn_log`, `cn_time`, `cn_status`, `cn_company`) \
                    VALUES (NULL, %s, %s, '', %s, '-1', %s);"
                cursor.execute(sql,(sn,rinterid,timestamp,company))
                logging.info(sql % ("'"+sn+"'",rinterid,"'"+timestamp+"'","'"+company+"'"))

            for sn,company in de_packet.items():
                sql = "INSERT INTO " + logisdeTable + " (`id`, `de_packet_sn`, `railway_id`, `de_log`, `de_time`, `de_status`, `de_company`) \
                    VALUES (NULL, %s, %s, '', %s, '-1', %s);"
                cursor.execute(sql,(sn,rinterid,timestamp,company))
                logging.info(sql % ("'"+sn+"'",rinterid,"'"+timestamp+"'","'"+company+"'"))

        connection.commit()
    finally:
        connection.close()

    print("Finished.")




def generate_logis_expression_from_sql(server,logis):
    print("Starting generate logis expression from database...\n")

    mysql = server["mysql"]
    connection = pymysql.connect(mysql[0],mysql[1],mysql[2],mysql[3],charset=mysql[4])

    #区分测试和主数据库
    orderInfoTable = ""
    orderGoodsTable = ""
    if mysql[3] == 'zhongw_test':
        orderInfoTable = "ecs_test_order_info"
        orderGoodsTable = "ecs_test_order_goods"
        goodsTable = "ecs_test_goods"
    elif mysql[3] == 'zhongwenshu_db1':
        orderInfoTable = "ecs_order_info"
        orderGoodsTable = "ecs_order_goods"
        goodsTable = "ecs_goods"

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
    template = ""
    sns = []
    regex = ""
    res = {}

    for template,v in logis.items():
        for regex,orders in v.items():
            if regex == "1":
                for order in orders:
                    sns.append("^" + order + ".*$")
            elif regex == "0":
                for order in orders:
                    sns.append(order)
    try:
        with connection.cursor() as cursor:
            for sn in sns:
                if regex == "1":
                    sql = "SELECT `order_id`,`order_sn` FROM " + orderInfoTable + " WHERE `order_sn` REGEXP %s AND `order_status`=1 AND `order_id` \
                        in (SELECT `order_id` FROM " + orderGoodsTable + " WHERE `goods_id` = %s);"
                    cursor.execute(sql,(sn,template))
                    orderids = cursor.fetchall()

                    for (orderid,ordersn) in orderids:
                        sql = "SELECT `goods_id` FROM " + orderGoodsTable + " WHERE order_id = %s;"
                        cursor.execute(sql,orderid)
                        goodsids = cursor.fetchall()

                        found = False
                        for goodsid in goodsids:
                            sql = "SELECT `cat_id`,`goods_name` FROM " + goodsTable + " WHERE goods_id = %s;"
                            cursor.execute(sql,goodsid[0])
                            (catid,goodsname) = cursor.fetchone()
                            if catid == 82: #82表示订购分类
                                if not(re.match(r".*template.*",goodsname,re.IGNORECASE)): #非模板商品
                                    found = True
                                    res[ordersn] = goodsid[0]
                                    break
                
    finally:
        connection.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    i = 0
    for k,v in res.items():
        ws.cell(row=i+1,column=1,value=k)
        i += 1
    wb.save("_manifest.xlsx")
    os.system("start _manifest.xlsx")

    print("Finished.")