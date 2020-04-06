#-*-coding:utf-8-*-
#＝＝＝＝＝＝订单导入系统＝＝＝＝＝＝＝＝
#Python 3.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de


import io
import re
import pymysql
import openpyxl.workbook
import time



#国家定义在表ecs_region中
countrys = {u'.*Deutschland.*|.*德国.*':3409,
            u'.*Frankreich.*|.*法国.*':3410,
            u'.*Belgien.*|.*比利时.*':3411,
            u'.*Italien.*|.*意大利.*':3412,
            u'.*Niederlande.*|.*荷兰.*':3413,
            u'.*Spanien.*|.*西班牙.*':3414,
            u'.*Tschechien.*|.*捷克.*':3415,
            u'.*Luxemburg.*|.*卢森堡.*':3416,
            u'.*Dänemark.*|.*丹麦.*':3417,
            u'.*Finnland.*|.*芬兰.*':3418,
            u'.*Island.*|.*冰岛.*':3419,
            u'.*Schweden.*|.*瑞典.*':3420,
            u'.*Schweiz.*|.*瑞士.*':3421,
            u'.*Lettland.*|.*拉脱维亚.*':3422,
            u'.*Österreich.*|.*奥地利.*':3423,
            u'.*Polen.*|.*波兰.*':3424,
            u'.*Kroatien.*|.*克罗地亚.*':3425,
            u'.*Portugal.*|.*葡萄牙.*':3426,
            u'.*Ungarn.*|.*匈牙利.*':3427,
            u'.*Griechenland.*|.*希腊.*':3428,
            u'.*Bulgarien.*|.*保加利亚.*':3429,
            u'.*Slowakei.*|.*斯洛伐克.*':3430,
            u'.*Serbien.*|.*塞尔维亚.*':3431,
            u'.*Albanien.*|.*阿尔巴尼亚.*':3432,
            u'.*Großbritannien.*|.*英国.*':3433,
            u'.*Slowenien.*|.*斯洛文尼亚.*':3434,
            u'.*Irland.*|.*爱尔兰.*':3435,
            u'.*Estland.*|.*爱沙尼亚.*':3436,
            u'.*Litauen.*|.*立陶宛.*':3437,
            u'.*Norwegen.*|.*挪威.*':3438,
            u'.*Rumänien.*|.*罗马尼亚.*':3439,
            u'.*Malta.*|.*马耳他.*':3441,
            u'.*Taiwan.*|.*台湾.*':3443,
            u'.*China.*|.*中国.*':3444,
            u'.*Türkei.*|.*土耳其.*':3445}



#生成20位团购订单号
def generate_tuan_ordernr(jsformnr):
    ymd = time.strftime("%Y%m%d",time.localtime())
    stamp = str(int(time.time()))
    tuan = jsformnr.zfill(2)
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
    orderinfos = []
    orderheads = {}
    endcol = -1 #这列以及这列之后都是jsform保留字段
    for row,cells in enumerate(ws.rows):
        orderbooks = {}
        for col,cell in enumerate(cells):
            if row == 0:
                ddsn = get_ddsn(cell.value)
                if ddsn:
                    sns.append(ddsn)
                else:
                    if re.match(u'.*id.*',cell.value,re.I):
                        orderheads[u'id'] = col
                    elif re.match(u'.*德国境内邮费.*',cell.value):
                        orderheads[u'dhl'] = col
                    elif re.match(u'.*欧洲境内邮费补差.*',cell.value):
                        orderheads[u'diff'] = col
                    elif re.match(u'.*打包费.*',cell.value):
                        orderheads[u'packer'] = col
                    elif re.match(u'.*wechat.*|.*微信.*',cell.value,re.I):
                        orderheads[u'wechat'] = col
                    elif re.match(u'.*email.*|.*电子邮件.*',cell.value,re.I):
                        orderheads[u'email'] = col
                    elif re.match(u'.*name.*|.*姓名.*',cell.value,re.I):
                        orderheads[u'name'] = col
                    elif re.match(u'.*telephone.*|.*电话.*',cell.value,re.I):
                        orderheads[u'tel'] = col
                    elif re.match(u'.*详细地址.*',cell.value,re.I):
                        orderheads[u'address'] = col
                    elif re.match(u'.*postcode.*|.*邮编.*',cell.value,re.I):
                        orderheads[u'postcode'] = col
                    elif re.match(u'.*city.*|.*城市.*',cell.value,re.I):
                        orderheads[u'city'] = col
                    elif re.match(u'.*country.*|.*国家.*',cell.value,re.I):
                        orderheads[u'country'] = col
                    elif re.match(u'.*comment.*|.*留言.*',cell.value,re.I):
                        orderheads[u'comment'] = col
                    elif re.match(u'.*金额.*',cell.value,re.I):
                        orderheads[u'amount'] = col
                    elif cell.value == u'在线支付状态':
                        orderheads[u'pay'] = col
                        endcol = col
            else:
                if col == 0:
                    orderid = cell.value
                    orderinfos.append([])
                    orderinfos[row-1].append(cell.value)
                elif col>0 and col<=len(sns):
                    if cell.value >= 1:
                        orderbooks[sns[col-1]] = cell.value
                    orderinfos[row-1].append(cell.value)
                else:
                    if col <= endcol:
                        orderinfos[row-1].append(cell.value)
                    
        if row != 0:
            orders[generate_tuan_ordernr(str(orderid))] = (orderbooks,orderinfos[row-1])


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
            shippingareatable = ""
            if dbname == 'zhongw_test':
                goodstypetable = "ecs_test_goods_type"
                attrtable = "ecs_test_attribute"
                goodsattrtable = "ecs_test_goods_attr"
                goodstable = "ecs_test_goods"
                ordertable = "ecs_test_order_info"
                ordergoodstable = "ecs_test_order_goods"
                orderactiontable = "ecs_test_order_action"
                areatable = "ecs_test_area_region"
                shippingareatable = "ecs_test_shipping_area"
                shippingtable = "ecs_test_shipping"
                paymenttable = "ecs_test_payment"
            elif dbname == 'zhongwenshu_db1':
                goodstypetable = "ecs_goods_type"
                attrtable = "ecs_attribute"
                goodsattrtable = "ecs_goods_attr"
                goodstable = "ecs_goods"
                ordertable = "ecs_order_info"
                ordergoodstable = "ecs_order_goods"
                orderactiontable = "ecs_order_action"
                areatable = "ecs_area_region"
                shippingareatable = "ecs_shipping_area"
                shippingtable = "ecs_shipping"
                paymenttable = "ecs_payment"
        
            for ordernr,(books,infos) in orders.items():
                with connection.cursor() as cursor:
                    #找团购大类
                    sql = "SELECT `cat_id` FROM " + goodstypetable + " WHERE `cat_name`=%s"
                    res = cursor.execute(sql,params[u'name'])
                    if res:
                        goodtype = cursor._rows[0][0]
                        print(goodstypetable + ": " + str(goodtype))
                    else:
                        raise Exception("this goodtype %s for groupbuy is not jet inserted in database!" %params[u'name'])

                    #找团购大类的属性
                    sql = "SELECT `attr_id` FROM " + attrtable + " WHERE `cat_id`=%s"
                    cursor.execute(sql,goodtype)
                    attrids = ""
                    for i,row in enumerate(cursor._rows):
                        attrids += str(row[0]) + " "
                    print(attrtable + ": " + attrids)
                    attrid = cursor._rows[i][0]

                    #找团购商品
                    sql = "SELECT `goods_attr_id`,`goods_id` FROM " + goodsattrtable + " WHERE `attr_id`=%s"
                    cursor.execute(sql,attrid)
                    goodids = ""
                    for i,row in enumerate(cursor._rows):
                        goodids += str(row) + " "
                    print(goodsattrtable + ": " + goodids)
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

                    #订单商品属性
                    goodsattr = ""
                    goodsattrid = ""
                    for sn,num in books.items():
                        if num == 1:
                            goodsattr += params[u'attr'] + u':' + ddsns[sn][1] + u'[' + ddsns[sn][2] + u']' + u'\r\n'
                            goodsattrid += str(ddsns[sn][0]) + u','
                    
                    if infos[orderheads[u'diff']] == 1:
                        sn = params[u'dhl_diff_sn']
                        goodsattr += params[u'attr'] + u':' + ddsns[sn][1] + u'[' + ddsns[sn][2] + u']' + u'\r\n'
                        goodsattrid += str(ddsns[sn][0]) + u','

                    if goodsattrid:
                        goodsattrid = goodsattrid[0:-1]

                    
                    #----------其他订单属性----------#
                    #订单留言
                    ordercomment = ""
                    if infos[orderheads[u'comment']]:
                        ordercomment = infos[orderheads[u'comment']]

                    #支付金额
                    paid = "0.00"
                    topay = "0.00"
                    if infos[orderheads[u'pay']]:
                        if re.match(u'^a|b|p|w$',infos[orderheads[u'pay']],re.I):
                            paid = infos[orderheads[u'amount']]
                        else:
                            topay = infos[orderheads[u'amount']]
               
                    #国家，excel表格里必须有国家作为单独一列
                    country = 3409
                    if infos[orderheads[u'country']]:
                        #绝大多数是德国订单
                        if re.match(u'.*Deutschland.*|.*德国.*',infos[orderheads[u'country']]):
                                country = 3409
                        else:
                            for regex,code in countrys.items():
                                if re.match(regex,infos[orderheads[u'country']]):
                                    country = code
                                    break

                    #配送地区
                    area = 0
                    if country > 0:
                        sql = "SELECT `shipping_area_id` FROM " + areatable + " WHERE `region_id`=%s"
                        res = cursor.execute(sql,country)
                        if res:
                            area = cursor._rows[0][0]
                    

                    #配送方式
                    shipping = 0
                    if area > 0:
                        sql = "SELECT `shipping_id` FROM " + shippingareatable + " WHERE `shipping_area_id`=%s"
                        res = cursor.execute(sql,area)
                        if res:
                            shipping = cursor._rows[0][0]

                    shippingname = ""
                    if shipping > 0:
                        sql = "SELECT `shipping_name` FROM " + shippingtable + " WHERE `shipping_id`=%s"
                        res = cursor.execute(sql,shipping)
                        if res:
                            shippingname = cursor._rows[0][0]
                    
                    #支付方式
                    paycode = ""
                    paynote = ""
                    if infos[orderheads[u'pay']]:
                        if infos[orderheads[u'pay']].lower() == u'p':
                            paycode = "paypal"
                        elif infos[orderheads[u'pay']].lower() == u'b':
                            paycode = "bank"
                        elif infos[orderheads[u'pay']].lower() == u'a':
                            paycode = "bank"
                            paynote = u"支付宝"
                        elif infos[orderheads[u'pay']].lower() == u'w':
                            paycode = "bank"
                            paynote = u"微信支付"

                    payid = 0
                    payname = ""
                    if paycode:
                        sql = "SELECT `pay_id`,`pay_name` FROM " + paymenttable + " WHERE `pay_code`=%s"
                        res = cursor.execute(sql,paycode)
                        if res:
                            payid = cursor._rows[0][0]
                            payname = cursor._rows[0][1]

                    #联系方式
                    telefon = ""
                    if infos[orderheads[u"tel"]]:
                        telefon = infos[orderheads[u"tel"]]
                    
                    email = ""
                    if infos[orderheads[u"email"]]:
                        email = infos[orderheads[u"email"]]

                    wechat = ""
                    if infos[orderheads[u"wechat"]]:
                        telefon = infos[orderheads[u"wechat"]]

                    #10位时间戳
                    stamp = str(int(time.time()))

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
                        %s, %s, '0', '0', '0', %s, %s, %s, '', %s, \
                        %s, %s, %s, %s, %s, %s, %s, \
                        '有货商品先发，缺货商品退款', '', '', '', '', '', '', %s, \
                        '0.00', '0.00', '0.00', '0.00', '0.00', %s, \
                        '0.00', '0', '0.00', '0.00', %s, '0', '表单大师', \
                        %s, %s, %s, '0', '0', '0', '0', '', \
                        '', '0', '', %s, '0', '', '0.00', '0', \
                        '0', '0.00', '0.00', '0.00', %s, '0.00')"
                    cursor.execute(sql,(ordernr,
                                    infos[orderheads[u'name']],str(country),infos[orderheads[u'address']],infos[orderheads[u'postcode']],telefon,email,
                                    wechat,infos[orderheads[u'postcode']],ordercomment,shipping,shippingname,payid,payname,
                                    infos[orderheads[u'amount']],
                                    paid,
                                    topay,
                                    stamp,stamp,stamp,
                                    paynote,
                                    infos[orderheads[u'amount']]))

                    #订单编号
                    sql = "SELECT `order_id` FROM " + ordertable + " WHERE `order_sn`=%s"
                    res = cursor.execute(sql,ordernr)
                    if res:
                        orderid = cursor._rows[0][0]
                        print(ordertable + ": " + str(orderid))
                    else:
                        raise Exception("this ordernr %s for groupbuy is not jet inserted in database!" %ordernr)

                    
                    #订单商品
                    sql = "INSERT INTO " + ordergoodstable + " (`rec_id`, `order_id`, `goods_id`, `goods_name`, \
                        `goods_sn`, `product_id`, `goods_number`, `market_price`, `goods_price`, `goods_attr`, \
                        `send_number`, `is_real`, `extension_code`, `parent_id`, `is_gift`, `goods_attr_id`) \
                        VALUES (NULL, %s, %s, %s, \
                        %s, '0', '1', %s, %s, %s, \
                        '0', '1', '', '0', '0', %s)"
                    cursor.execute(sql,(orderid,goodid,params[u'goodsname'],
                                    goodsn,infos[orderheads[u'amount']],infos[orderheads[u'amount']],goodsattr,
                                    goodsattrid))

                    #订单状态
                    sql = "INSERT INTO " + orderactiontable + " (`action_id`, `order_id`, `action_user`, \
                        `order_status`, `shipping_status`, `pay_status`, `action_place`, `action_note`, `log_time`) \
                        VALUES (NULL, %s, 'zhongwenshu', \
                        '1', '0', '2', '0', '', '0')"
                    cursor.execute(sql,(orderid))

                connection.commit()
        finally:
            connection.close()

    print("Finished.")
    