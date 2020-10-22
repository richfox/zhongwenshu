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
import xml
import lxml
import openpyxl.workbook
import Visitor


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
            logging.info("----------------------------------------------------------------") #分割线
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


def get_logis_labels():
    res = {}
    jsonstring = open(".\\Globconfig.json",'rb').read()
    allinfo = json.loads(jsonstring)
    for config in allinfo["configurations"]:
        if "label" in config:
            for label in config["label"]:
                res[label["code"]] = label["name"]
            break
    return res


def get_logis_companies():
    res = {}
    jsonstring = open(".\\Globconfig.json",'rb').read()
    allinfo = json.loads(jsonstring)
    for config in allinfo["configurations"]:
        if "logisCompany" in config:
            for company in config["logisCompany"]:
                res[company["name"]] = company["code"]
            break
    return res


def get_logis_company_headers():
    res = {}
    jsonstring = open(".\\Globconfig.json",'rb').read()
    allinfo = json.loads(jsonstring)
    for config in allinfo["configurations"]:
        if "logisCompanyHeader" in config:
            for company in config["logisCompanyHeader"]:
                res[company["header"]] = company["attr"]
            break
    return res



#
#以下若干函数物流表达式解析，不支持括号，和logis.php一致
#
def split_logis_expr(expr):
    return re.split('[+]',expr.strip()) #+为表达式分隔符

def split_logis_expr_and_token(expr):
    res = {}
    ids = split_logis_expr(expr)
    for id in ids:
        if id.strip():
            sn = ['']
            company =['']
            notes = [[]]
            split_token(id.strip(),sn,company,notes)
            res[sn[0]] = (company[0],notes[0])
    return res


def split_token(token,sn,company,notes):
    pattern = '[:]' #半角冒号为表达式说明符
    if re.search(pattern,token.strip()):
        tokens = re.split(pattern,token.strip())
        token = tokens[0]
        notes[0] = tokens[1:]

    matches = re.split('([a-zA-Z0-9\-]+)',token.strip())
    matches = list(filter(None,matches)) #去除空字符串
    if len(matches) == 1:
        matches[0] = [matches[0]]
        get_main_sn(matches[0])
        sn[0] = matches[0][0]
    else:
        matches[1] = [matches[1]]
        get_main_sn(matches[1])
        sn[0] = matches[1][0]
        company[0] = get_company_code(matches[0])

    if not company[0]:
        company[0] = split_company_header_code(sn)


def get_main_sn(sn):
    pattern = '[\-]' #-符号代表的子单号
    if re.search(pattern,sn[0].strip()):
        sns = re.split(pattern,sn[0].strip())
        sn[0] = sns[0]


def get_company_code(company):
    code = ""
    for n,c in get_logis_companies().items():
        if re.search(n,company):
            code = c
            break
    return code


def split_company_header_code(sn):
    company = ""
    hsize = []
    for h,attr in get_logis_company_headers().items():
        hsize.append(len(h))
    hsize = list(set(hsize))

    for size in hsize:
        header = ""
        if (len(sn[0]) > size):
            header = sn[0][0:size]
            code = get_company_header_code(header)
            if code:
                company = code[0]
                if code[1] == 0:
                    sn[0] = sn[0][size:]
                break
    return company


def get_company_header_code(header):
    res = []
    for h,attr in get_logis_company_headers().items():
        if (h == header.upper()):
            res = attr
            break
    return res
#
#以上若干函数物和logis.php一致
#


def generate_logis_expression_from_html(htmltree):
    expression = ""
    for code,(en,cn,pattern) in Visitor.get_transports_info().items():
        nodes = htmltree.xpath('//div[@id="' + code + '" or @id="' + en + '"]/div[@class="descrip"]//span/text()')
        for i,node in enumerate(nodes):
            if i == 0:
                if expression:
                    expression += " + "
                expression += "%" + code + "("
            expression += node
            if i < len(nodes) - 1:
                expression += " + "
            else:
                expression += ")"
    return expression


def has_special_label(notes):
    if notes:
        for note in notes:
            for code,name in get_logis_labels().items():
                if note.lower() == code.lower():
                    return True
    return False


def get_customer_forecast(htmltree):
    forecast = []
    for code,(en,cn,pattern) in Visitor.get_transports_info().items():
        if code == 'r':
            nodes = htmltree.xpath('//div[@id="' + code + '" or @id="' + en + '"]/div[@class="descrip"]//span/text()')
            for i,node in enumerate(nodes):
                forecast.append(split_logis_expr_and_token(node))
    return forecast


def generate_manifest_expression(data):
    expression = ''
    for i,(sn,company,notes) in enumerate(data):
        expression += get_company_name(company) + sn
        if notes:
            for note in notes:
                expression += ":" + note.strip()
        if i < len(data)-1:
            expression += ' + '
    return expression


def get_company_name(code):
    name = ""
    for n,c in get_logis_companies().items():
        if code.strip().lower() == c:
            name = n
            break
    return name


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
        logiscnTable = "zws_test_logis_cn"
    elif mysql[3] == 'zhongwenshu_db1':
        orderInfoTable = "ecs_order_info"
        orderGoodsTable = "ecs_order_goods"
        goodsTable = "ecs_goods"
        logiscnTable = "zws_logis_cn"

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
    template = ""
    sns = []
    regex = ""
    res = []

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
            #log
            LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
            logging.basicConfig(filename='mylogis.log',level=logging.DEBUG,format=LOG_FORMAT)
            logging.info("----------------------------------------------------------------") #分割线

            for sn in sns:
                orderinfos = {}
                if regex == "1":
                    sql = "SELECT `order_id`,`order_sn`,`best_time`,`money_paid` FROM " + orderInfoTable + " WHERE `order_sn` REGEXP %s AND `order_id` \
                        in (SELECT `order_id` FROM " + orderGoodsTable + " WHERE `goods_id` = %s);"
                    cursor.execute(sql,(sn,template))
                    logging.info(sql % ("'"+sn+"'","'"+template+"'"))
                    orderinfos = cursor.fetchall()
                elif regex == "0":
                    sql = "SELECT `order_id`,`order_sn`,`best_time`,`money_paid` FROM " + orderInfoTable + " WHERE `order_sn` = %s AND `order_id` \
                        in (SELECT `order_id` FROM " + orderGoodsTable + " WHERE `goods_id` = %s);"
                    cursor.execute(sql,(sn,template))
                    logging.info(sql % ("'"+sn+"'","'"+template+"'"))
                    orderinfos = cursor.fetchall()

                for (orderid,ordersn,wchat,paid) in orderinfos:
                    sql = "SELECT `goods_id` FROM " + orderGoodsTable + " WHERE order_id = %s;"
                    cursor.execute(sql,orderid)
                    logging.info(sql % ("'"+str(orderid)+"'"))
                    goodsids = cursor.fetchall()

                    validitem = {}
                    found = False
                    for goodsid in goodsids:
                        sql = "SELECT `cat_id`,`goods_name`,`goods_desc` FROM " + goodsTable + " WHERE goods_id = %s;"
                        cursor.execute(sql,goodsid[0])
                        logging.info(sql % ("'"+str(goodsid[0])+"'"))
                        (catid,goodsname,goodsdesc) = cursor.fetchone()
                        if catid == 82: #82表示订购分类
                            if not(re.match(r".*template.*",goodsname,re.IGNORECASE)): #非模板商品
                                found = True
                                validitem["ordersn"] = ordersn
                                validitem["logisgoodid"] = goodsid[0]
                                validitem["wchat"] = wchat
                                validitem["paid"] = paid

                                parser = lxml.html.HTMLParser()
                                htmltree = xml.etree.ElementTree.fromstring(goodsdesc,parser)
                                validitem["expression"] = generate_logis_expression_from_html(htmltree)
                                
                                manifest = []
                                for forecast in get_customer_forecast(htmltree):
                                    for cnsn,(company,notes) in forecast.items():
                                        sql = "SELECT * FROM " + logiscnTable + " WHERE cn_packet_sn REGEXP %s;"
                                        cursor.execute(sql,cnsn)
                                        logging.info(sql % ("'"+cnsn+"'"))
                                        #未录入的而且没有特定标记的加入交接单
                                        if not cursor.fetchone():
                                            if not has_special_label(notes):
                                                manifest.append((cnsn,company,notes))

                                validitem["manifest"] = generate_manifest_expression(manifest)

                                break

                    if found == True:
                        res.append(validitem)
    finally:
        connection.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    i = 0
    for item in res:
        if i == 0:
            ws.cell(row=1,column=1,value="订单号")
            ws.cell(row=1,column=2,value="国内物流单号")
            ws.cell(row=1,column=3,value="国内物流单号2")
            ws.cell(row=1,column=4,value="用户")
            ws.cell(row=1,column=5,value="支付")
            ws.cell(row=1,column=6,value="重量")
            ws.cell(row=1,column=7,value="备注")
            ws.cell(row=1,column=8,value="交接单")
            i = 1
        ws.cell(row=i+1,column=1,value=item["ordersn"])
        ws.cell(row=i+1,column=2,value=item["expression"])
        ws.cell(row=i+1,column=4,value=item["wchat"])
        ws.cell(row=i+1,column=5,value=item["paid"])
        ws.cell(row=i+1,column=8,value=item["manifest"])
        i += 1
    wb.save("_manifest.xlsx")
    os.system("start _manifest.xlsx")

    print("Finished.")