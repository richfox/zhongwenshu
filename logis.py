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


def import_logis_to_sql(server,logis):
    print("Starting import logis info to database...\n")

    sql = server["mysql"]
    connection = pymysql.connect(sql[0],sql[1],sql[2],sql[3],charset=sql[4])

    #区分测试和主数据库
    rinterTable = ""
    logiscnTable = ""
    logisdeTable = ""
    if sql[3] == 'zhongw_test':
        rinterTable = "zws_test_railway_inter"
        logiscnTable = "zws_test_logis_cn"
        logisdeTable = "zws_test_logis_de"
    elif sql[3] == 'zhongwenshu_db1':
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
                  VALUES (NULL, %s, '', %s, '-1', %s)"
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
                    VALUES (NULL, %s, %s, '', %s, '-1', %s)"
                cursor.execute(sql,(sn,rinterid,timestamp,company))
                logging.info(sql % ("'"+sn+"'",rinterid,"'"+timestamp+"'","'"+company+"'"))

            for sn,company in de_packet.items():
                sql = "INSERT INTO " + logisdeTable + " (`id`, `de_packet_sn`, `railway_id`, `de_log`, `de_time`, `de_status`, `de_company`) \
                    VALUES (NULL, %s, %s, '', %s, '-1', %s)"
                cursor.execute(sql,(sn,rinterid,timestamp,company))
                logging.info(sql % ("'"+sn+"'",rinterid,"'"+timestamp+"'","'"+company+"'"))

        connection.commit()
    finally:
        connection.close()

    print("Finished.")