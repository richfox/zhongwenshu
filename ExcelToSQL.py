#-*-coding:utf-8-*-
#＝＝＝＝＝＝订单导入系统＝＝＝＝＝＝＝＝
#Python 2.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de


import io
import re
import pymysql
import openpyxl.workbook
import time


#生成22位团购订单号
def generate_tuan_ordernr(jsformnr):
    ymd = time.strftime("%Y%m%d",time.localtime())
    stamp = str(int(time.time()))
    tuan = jsformnr.zfill(4)
    return ymd + stamp + tuan


def ExcelToSQLGBuy(sqls,params):
    print("excel to SQL start...\n")

    #read excel data
    wb = openpyxl.load_workbook('_jsform.xlsx')
    ws = wb.active
    
    orders = {}
    sns = []
    for row,cells in enumerate(ws.rows):
        books = {}
        for col,cell in enumerate(cells):
            if row == 0:
                ddsn = re.findall(u'\[([0-9]+)\]',cell.value.replace(u' ',u''))
                if ddsn:
                    sns.append(ddsn[0])
            else:
                if col == 0:
                    orderid = cell.value
                elif col>0 and col<=len(sns):
                    if cell.value >= 1:
                        books[sns[col-1]] = cell.value
                    
        if row != 0:
            orders[generate_tuan_ordernr(str(orderid))] = books


    for host,(username,password,dbname,charset) in sqls.items():
        connection = pymysql.connect(host=host,user=username,password=password,db=dbname,charset=charset)

        try:
            #区分测试和主数据库
            goodstypetable = ""
            attrtable = ""
            goodsattrtable = ""
            ordertable = ""
            ordergoodstable = ""
            orderactiontable = ""
            if dbname == 'zhongw_test':
                goodstypetable = "ecs_test_goods_type"
                attrtable = "ecs_test_attribute"
                goodsattrtable = "ecs_test_goods_attr"
                ordertable = "ecs_test_order_info"
                ordergoodstable = "ecs_test_order_goods"
                orderactiontable = "ecs_test_order_action"
            elif dbname == 'zhongwenshu_db1':
                goodstypetable = "ecs_goods_type"
                attrtable = "ecs_attribute"
                goodsattrtable = "ecs_goods_attr"
                ordertable = "ecs_order_info"
                ordergoodstable = "ecs_order_goods"
                orderactiontable = "ecs_order_action"
        
            for ordernr,books in orders.items():
                with connection.cursor() as cursor:
                    #找团购商品属性
                    sql = "SELECT `cat_id` FROM " + goodstypetable + " WHERE `cat_name`=%s"
                    cursor.execute(sql,params[u'name'])
                    goodtype = cursor.fetchone()[0]

                    sql = "SELECT `attr_id` FROM " + attrtable + " WHERE `cat_id`=%s"
                    cursor.execute(sql,goodtype)
                    attrid = cursor.fetchone()[0]

                    sql = "SELECT `goods_id` FROM " + goodsattrtable + " WHERE `attr_id`=%s"
                    cursor.execute(sql,attrid)
                    goodids = cursor.fetchall()

                    #生成订单
                    sql = "INSERT INTO " + ordertable + " (`order_id`, `order_sn`, `user_id`, `order_status`, `shipping_status`, `pay_status`, \
                        `consignee`, `country`, `province`, `city`, `district`, `address`, `zipcode`, `tel`, `mobile`, `email`, \
                        `best_time`, `sign_building`, `postscript`, `shipping_id`, `shipping_name`, `pay_id`, `pay_name`, \
                        `how_oos`, `how_surplus`, `pack_name`, `card_name`, `card_message`, `inv_payee`, `inv_content`, `goods_amount`, \
                        `shipping_fee`, `insure_fee`, `pay_fee`, `pack_fee`, `card_fee`, `money_paid`, \
                        `surplus`, `integral`, `integral_money`, `bonus`, `order_amount`, `from_ad`, `referer`, \
                        `add_time`, `confirm_time`, `pay_time`, `shipping_time`, `pack_id`, `card_id`, `bonus_id`, `invoice_no`, \
                        `extension_code`, `extension_id`, `to_buyer`, `pay_note`, `agency_id`, `inv_type`, `tax`, `is_separate`, \
                        `parent_id`, `discount`, `discount7`, `discount19`, `goods_amount7`, `goods_amount19`) \
                        VALUES (NULL, %s, '0', '1', '3', '2', \
                        'Tang Shanqiong', '3409', '0', '0', '0', 'Berliner Str. 40', '38678', '017655505472', '', 'mini_tang@hotmail.com', \
                        '', 'Clausthal-Zellerfeld', '', '12', 'DHL Paket', '4', 'paypal 第一时间到付', \
                        '有货商品先发，缺货商品退款', '', '', '', '', '', '', '114.78', \
                        '0.00', '0.00', '0.00', '0.00', '0.00', '114.78', \
                        '0.00', '0', '0.00', '0.00', '0.00', '0', '本站', \
                        '1524138219', '1524138261', '1524138261', '0', '0', '0', '0', '', \
                        '', '0', '#34', '', '0', '', '0.00', '0', \
                        '0', '0.00', '0.00', '0.00', '0.00', '114.78')"
                    cursor.execute(sql,ordernr)

                    #订单编号
                    sql = "SELECT `order_id` FROM " + ordertable + " WHERE `order_sn`=%s"
                    cursor.execute(sql,ordernr)
                    orderid = cursor.fetchone()[0]
                    print(orderid)


                    goodattr = params[u'attr'] + u':' + u'汉声中国童话（全12册）[102.11] \r\n多商品:从尿布到约会[4.67] \r\n'

                    #订单商品
                    sql = "INSERT INTO " + ordergoodstable + " (`rec_id`, `order_id`, `goods_id`, `goods_name`, \
                        `goods_sn`, `product_id`, `goods_number`, `market_price`, `goods_price`, `goods_attr`, \
                        `send_number`, `is_real`, `extension_code`, `parent_id`, `is_gift`, `goods_attr_id`) \
                        VALUES (NULL, %s, '3738', '4月团', \
                        'TUAN0418', '0', '1', '116.38', '114.78', %s, \
                        '0', '1', '', '0', '0', '23010,23017')" #ecs_goods_attr
                    cursor.execute(sql,orderid,goodattr)

                    #订单状态
                    sql = "INSERT INTO " + orderactiontable + " (`action_id`, `order_id`, `action_user`, \
                        `order_status`, `shipping_status`, `pay_status`, `action_place`, `action_note`, `log_time`) \
                        VALUES (NULL, %s, 'zhongwenshu', \
                        '1', '0', '2', '0', '5ED87113L11792735（paypal 交易号）', '1524138261')"
                    cursor.execute(sql,orderid,orderid)

                connection.commit()
        finally:
            connection.close()

    print("Finished.")
    