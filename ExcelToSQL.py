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

#提取当当编号
def get_ddsn(name):
    ddsn = ""
    res = re.findall(u'\[([0-9]+)\]',name.replace(u' ',u''))
    if res:
        ddsn = res[0]
    return ddsn
    

def ExcelToSQLGBuy(sqls,params):
    print("excel to SQL start...\n")

    #read excel data
    wb = openpyxl.load_workbook('_jsform.xlsx')
    ws = wb.active
    
    orders = {}
    sns = []
    orderinfos = [[]]
    endcol = -1 #这列以及这列之后都是jsform保留字段
    for row,cells in enumerate(ws.rows):
        orderbooks = {}
        for col,cell in enumerate(cells):
            if row == 0:
                ddsn = get_ddsn(cell.value)
                if ddsn:
                    sns.append(ddsn)
                else:
                    if cell.value == u'在线支付状态':
                        endcol = col
                    orderinfos[0].append(cell.value)
            else:
                if col == 0:
                    orderid = cell.value
                    orderinfos.append([])
                    orderinfos[row].append(cell.value)
                elif col>0 and col<=len(sns):
                    if cell.value >= 1:
                        orderbooks[sns[col-1]] = cell.value
                else:
                    if col <= endcol:
                        orderinfos[row].append(cell.value)
                    
        if row != 0:
            orders[generate_tuan_ordernr(str(orderid))] = orderbooks


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
                goodstable = "ecs_test_goods"
                ordertable = "ecs_test_order_info"
                ordergoodstable = "ecs_test_order_goods"
                orderactiontable = "ecs_test_order_action"
            elif dbname == 'zhongwenshu_db1':
                goodstypetable = "ecs_goods_type"
                attrtable = "ecs_attribute"
                goodsattrtable = "ecs_goods_attr"
                goodstable = "ecs_goods"
                ordertable = "ecs_order_info"
                ordergoodstable = "ecs_order_goods"
                orderactiontable = "ecs_order_action"
        
            for ordernr,books in orders.items():
                with connection.cursor() as cursor:
                    #找团购大类
                    sql = "SELECT `cat_id` FROM " + goodstypetable + " WHERE `cat_name`=%s"
                    res = cursor.execute(sql,params[u'name'])
                    if res:
                        goodtype = cursor._rows[0][0]
                        print goodtype
                    else:
                        raise Exception, "this goodtype %s for groupbuy is not jet inserted in database!" %params[u'name']

                    #找团购大类的属性
                    sql = "SELECT `attr_id` FROM " + attrtable + " WHERE `cat_id`=%s"
                    cursor.execute(sql,goodtype)
                    attrids = ""
                    for i,row in enumerate(cursor._rows):
                        attrids += str(row[0]) + " "
                    print attrids
                    attrid = cursor._rows[i][0]

                    #找团购商品
                    sql = "SELECT `goods_attr_id`,`goods_id` FROM " + goodsattrtable + " WHERE `attr_id`=%s"
                    cursor.execute(sql,attrid)
                    goodids = ""
                    for i,row in enumerate(cursor._rows):
                        goodids += str(row) + " "
                    print goodids
                    goodid = cursor._rows[i][1]

                    #找商品sn号
                    sql = "SELECT `goods_sn` FROM " + goodstable + " WHERE `goods_id`=%s"
                    res = cursor.execute(sql,goodid)
                    if res:
                        goodsn = cursor._rows[0][0]

                    #找当当编号
                    ddsns = {}
                    sql = "SELECT `goods_attr_id`,`attr_value`,`attr_price` FROM " + goodsattrtable + " WHERE `attr_id`=%s AND `goods_id`=%s"
                    cursor.execute(sql,(attrid,goodid))
                    for i,row in enumerate(cursor._rows):
                        ddsns[get_ddsn(row[1])] = (row[0],row[1],row[2])

                    #生成订单商品属性
                    goodsattr = ""
                    goodsattrid = ""
                    goodsattrprice = 0.00
                    for sn,num in books.items():
                        if num == 1:
                            goodsattr += params[u'attr'] + u':' + ddsns[sn][1] + u'[' + ddsns[sn][2] + u']' + u'\r\n'
                            goodsattrid += str(ddsns[sn][0]) + u','
                            goodsattrprice += float(ddsns[sn][2])

                    if goodsattrid:
                        goodsattrid = goodsattrid[0:-1]

                    baseprice = float(params[u'dhl_de']) + float(params[u'packing'])
                    goodsprice = format(baseprice + goodsattrprice,'.2f')

                    raise Exception


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

                    
                    #订单商品
                    sql = "INSERT INTO " + ordergoodstable + " (`rec_id`, `order_id`, `goods_id`, `goods_name`, \
                        `goods_sn`, `product_id`, `goods_number`, `market_price`, `goods_price`, `goods_attr`, \
                        `send_number`, `is_real`, `extension_code`, `parent_id`, `is_gift`, `goods_attr_id`) \
                        VALUES (NULL, %s, %s, %s, \
                        %s, '0', '1', %s, %s, %s, \
                        '0', '1', '', '0', '0', %s)"
                    cursor.execute(sql,(orderid,goodid,params[u'goodsname'],goodsn,goodsprice,goodsprice,goodsattr,goodsattrid))

                    #订单状态
                    sql = "INSERT INTO " + orderactiontable + " (`action_id`, `order_id`, `action_user`, \
                        `order_status`, `shipping_status`, `pay_status`, `action_place`, `action_note`, `log_time`) \
                        VALUES (NULL, %s, 'zhongwenshu', \
                        '1', '0', '2', '0', '5ED87113L11792735（paypal 交易号）', '1524138261')"
                    cursor.execute(sql,(orderid,orderid))

                connection.commit()
        finally:
            connection.close()

    print("Finished.")
    