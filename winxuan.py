#-*-coding:utf-8-*-
# 文轩网接口
#Python 2.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de

import sys
import os
import hashlib
import json
import time
import utility
import pymysql
import SpiderToSQL



def get_authorization():
    res = {}
    jsonstring = open(".\\Globconfig.json",'r').read()
    allinfo = json.loads(jsonstring)
    for config in allinfo["configurations"]:
        if config.has_key("winxuan"):
            for wx in config["winxuan"]:
                res[wx["type"]] = (wx["address"],wx["key"],wx["secret"],wx["accesstoken"],wx["version"],wx["format"])
            break
    return res


def build_http_request(httpaddress,cparams,bparams,sign):
    hreq = httpaddress + "?"
    for ckey,cvalue in cparams.items():
        hreq += "&" + ckey + "=" + cvalue
    for bkey,bvalue in bparams.items():
        hreq += "&" + bkey + "=" + bvalue
    hreq += "&appSign=" + sign
    return hreq



def get_sign(cparams,bparams,secret):
    sign = ""
    if cparams or bparams:
        sign = secret
        allparams = cparams
        for bkey,bvalue in bparams.items():
            allparams[bkey] = bvalue
        for key,value in sorted(allparams.items()):
            if value:
                sign += key + value
        sign += secret
        return HEXSHA1(sign)
    return sign



def HEXSHA1(source):
    return hashlib.sha1(source.encode("utf-8")).hexdigest().upper()

def SHA1(source):
    barray = bytearray(hashlib.sha1(source.encode("utf-8")).digest())
    return byte2hex(barray)


def byte2hex(barray):
    sign = ""
    for b in barray:
        bhex = hex(b & 0xFF)
        if len(bhex) == 1:
            sign += "0"
        sign += bhex.upper()
    return sign


def get_shop_items():
    urls = {}
    
    (address,key,secret,accesstoken,version,format) = get_authorization()["sandbox"]
    method = "winxuan.shop.items.get"
    timestamp = str(int(time.time()*1000))

    #公共参数
    cparams = {"timeStamp":timestamp,
               "method":method,
               "v":version,
               "format":format,
               "appKey":key,
               "accessToken":accesstoken}

    #业务参数
    bparams = {"itemIds":"10000349"}

    #生成签名
    sign = get_sign(cparams,bparams,secret)

    #组装HTTP请求
    hreq = build_http_request(address,cparams,bparams,sign)

    if hreq:
        urls[hreq] = format

    return urls


def import_winxuan_to_sql(sqls):
    print("Starting Import winxuan article to database...\n")
    ignored = []

    for host,(username,password,dbname,charset,urls) in sqls.items():
        connection = pymysql.connect(host=host,user=username,password=password,db=dbname,charset=charset)
        try:
            for url,tag in urls.items():
                text = utility.get_html_text(url)

                if not text:
                    ignored.append(url)
                    continue

                data = ""
                if tag == "json":
                    data = json.loads(text)
                
                #区分测试和主数据库
                goodstable = ""
                goodsattrtable = ""
                goodscattable = ""
                if dbname == 'zhongw_test':
                    goodstable = "ecs_test_goods"
                    goodsattrtable = "ecs_test_goods_attr"
                    goodscattable = "ecs_test_goods_cat"
                elif dbname == 'zhongwenshu_db1':
                    goodstable = "ecs_goods"
                    goodsattrtable = "ecs_goods_attr"
                    goodscattable = "ecs_goods_cat"

                #商品分类定义在表ecs_category中，先登到准上架分类'134'
                catid = "134"

                #唯一商品货号
                sn = ""
                title = ""
                if data["shop_items"][0].has_key("title"):
                    title = data["shop_items"][0]["title"]
                    if title:
                        sn = SpiderToSQL.generate_sn(data["shop_items"][0]["title"])
                
                #数量
                goodsnumber = 0
                if data["shop_items"][0].has_key("stock"):
                    goodsnumber = data["shop_items"][0]["stock"]

                #重量kg
                goodsweight = "0.000"

                #价格
                shopprice = 0.00
                marketprice = "0.00"
                if data["shop_items"][0].has_key("shop_item_price"):
                    if data["shop_items"][0]["shop_item_price"].has_key("sell_price"):
                        shopprice = data["shop_items"][0]["shop_item_price"]["sell_price"]
                        marketprice = u"%.2f" % (float(shopprice)*1.2)
                elif data["shop_items"][0].has_key("shop_item_price.sell_price"):
                    shopprice = data["shop_items"][0]["shop_item_price.sell_price"]
                    marketprice = u"%.2f" % (float(shopprice)*1.2)

                #商品详情
                zwsprodtext = u"<p>本商品暂无详情。</p>"

                #时间戳
                addtime = str(int(time.time()))

                #商品大类定义在表ecs_goods_type中, '1'代表书
                gtype = '1'

                with connection.cursor() as cursor:
                    sql = "INSERT INTO " + goodstable + " (`goods_id`, `cat_id`, `goods_sn`,`goods_name`,\
                        `goods_name_style`, `click_count`, `brand_id`, `provider_name`, `goods_number`,\
                        `goods_weight`, `market_price`, `virtual_sales`, `shop_price`, `promote_price`,\
                        `promote_start_date`, `promote_end_date`, `warn_number`, `keywords`, `goods_brief`,\
                        `goods_desc`, `goods_thumb`, `goods_img`, `original_img`, `is_real`, `extension_code`,\
                        `is_on_sale`, `is_alone_sale`, `is_shipping`, `integral`, `add_time`, `sort_order`,\
                        `is_delete`, `is_best`, `is_new`, `is_hot`, `is_promote`, `bonus_type_id`, `last_update`,\
                        `goods_type`, `seller_note`, `give_integral`, `rank_integral`, `suppliers_id`, `is_check`) \
                        VALUES (NULL, %s, %s, %s,\
                        '+', '0', '0', '', %s,\
                        %s, %s, '', %s, '0.00',\
                        '0', '0', '1', '', '',\
                        %s, '', '', '', '1', '',\
                        '0', '1', '0', '0', %s, '100',\
                        '0', '0', '1', '0', '0', '0', '0',\
                        %s, '', '-1', '-1', '0', NULL)"
                    cursor.execute(sql,(catid,sn,title,goodsnumber,goodsweight,marketprice,shopprice,zwsprodtext,addtime,gtype))

                connection.commit()
        finally:
            connection.close()

    for url in ignored:
        print(url + " ignored!\n")

    print("Finished.")