#-*-coding:utf-8-*-
#＝＝＝＝＝＝登书系统＝＝＝＝＝＝＝＝
#Python 2.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de


import pymysql


def SQLimport(sqllist):
    print("Import start...\n")

    for host,(username,password,dbname,charset) in sqllist.items():

        connection = pymysql.connect(host=host,user=username,password=password,db=dbname,charset=charset)
        try:
            with connection.cursor() as cursor:
                sql = "SELECT `user_id`, `email` FROM `ecs_test_users` WHERE `user_name`=%s"
                cursor.execute(sql,'xfu')
                res = cursor.fetchone()
                print(res)
        finally:
            connection.close()

    print("Finished.")