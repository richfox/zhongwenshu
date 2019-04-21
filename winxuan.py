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
import ftplib
import ImageProcess


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
    hreq = httpaddress + "?appSign=" + sign
    for ckey,cvalue in cparams.items():
        hreq += "&" + ckey + "=" + cvalue
    for bkey,bvalue in bparams.items():
        hreq += "&" + bkey + "=" + bvalue
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
    bparams = {"itemIds":"10000001"}

    #生成签名
    sign = get_sign(cparams,bparams,secret)

    #组装HTTP请求
    hreq = build_http_request(address,cparams,bparams,sign)

    if hreq:
        urls[hreq] = format

    return urls


def import_winxuan_to_sql(server,urls):
    print("Starting Import winxuan article to database...\n")
    ignored = []
    sql = server["mysql"]
    ftp = server["ftp"]

    connection = pymysql.connect(sql[0],sql[1],sql[2],sql[3],charset=sql[4])
    fconn = ftplib.FTP(ftp[0],ftp[1],ftp[2])
    try:
        for url,tag in urls.items():
            text = utility.post_html_text(url)

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
            goodsimagepath = ""
            if sql[3] == 'zhongw_test':
                goodstable = "ecs_test_goods"
                goodsattrtable = "ecs_test_goods_attr"
                goodscattable = "ecs_test_goods_cat"
                goodsimagepath = "test/" + ftp[3]
            elif sql[3] == 'zhongwenshu_db1':
                goodstable = "ecs_goods"
                goodsattrtable = "ecs_goods_attr"
                goodscattable = "ecs_goods_cat"
                goodsimagepath = ftp[3]

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
            
            #ISBN
            isbn = ""
            if data["shop_items"][0].has_key("barcode"):
                isbn = data["shop_items"][0]["barcode"]

            #价格
            oriprice = "0.00"
            shopprice = 0.00
            marketprice = "0.00"
            if data["shop_items"][0].has_key("list_price"):
                oriprice = u"%s%.2f" % (u"¥",data["shop_items"][0]["list_price"])
                shopprice = data["shop_items"][0]["list_price"]*2/7
                marketprice = u"%.2f" % (data["shop_items"][0]["list_price"]*1.2)

            #重量kg
            goodsweight = 0.000

            #商品图片
            homeimgUrl = ""
            largeimgUrls = {}
            img = ImageProcess.Processor("")
            if data["shop_items"][0].has_key("shop_item_images"):
                for image in data["shop_items"][0]["shop_item_images"]:
                    if image["image_type"] == "HOME_IMAGE":
                        homeimgUrl = image["winxuan_image_url"]
                        img = ImageProcess.Processor(homeimgUrl)
                    elif image["image_type"] == "LARGE_IMAGE":
                        largeimgUrls[image["index"]] = image["winxuan_image_url"]
            
            oriImg = ""
            goodsImg = ""
            thumbImg = "" 
            if img.Loaded():
                fconn.cwd(goodsimagepath)
                src = img.Save("./temp",sn,img.Format())
                target = img.Upload(fconn,src,"source_img",sn,img.Format())
                if target:
                    oriImg = ftp[3] + "/" + target

                if img.Width()>230 and img.Height()>230:
                    img.Thumb(230,230)
                    src = img.Save("./temp",sn+"_G",img.Format())
                    target = img.Upload(fconn,src,"goods_img",sn+"_G",img.Format())
                    if target:
                        goodsImg = ftp[3] + "/" + target

                    img.Thumb(100,100)
                    src = img.Save("./temp",sn+"_T",img.Format())
                    target = img.Upload(fconn,src,"thumb_img",sn+"_T",img.Format())
                    if target:
                        thumbImg = ftp[3] + "/" + target
                else:
                    target = img.Upload(fconn,src,"goods_img",sn+"_G",img.Format())
                    if target:
                        goodsImg = ftp[3] + "/" + target

                    if img.Width()>100 and img.Height()>100:
                        img.Thumb(100,100)
                        src = img.Save("./temp",sn+"_T",img.Format())
                        target = img.Upload(fconn,src,"thumb_img",sn+"_T",img.Format())
                        if target:
                            humbImg = ftp[3] + "/" + target
                    else:
                        target = img.Upload(fconn,src,"thumb_img",sn+"_T",img.Format())
                        if target:
                            thumbImg = ftp[3] + "/" + target
                

            #商品详情
            fields = ["feature","editor_recommendation","content_introduce","author_introduce","catalog","preface","media_comment"]
            sections = {"feature":{"id":u"feature","title":u"产品特色"},
                        "editor_recommendation":{"id":u"abstract","title":u"编辑推荐"},
                        "content_introduce":{"id":u"content","title":u"内容简介"},
                        "author_introduce":{"id":u"authorIntroduction","title":u"作者简介"},
                        "catalog":{"id":u"catalog","title":u"目　　录"},
                        "preface":{"id":u"preface","title":u"在线试读"},
                        "media_comment":{"id":u"media","title":u"媒体评论"}}
            
            prodtext = u""
            if data["shop_items"][0].has_key("shop_item_attribute"):
                for field in fields:
                    sectiontext = u''
                    if data["shop_items"][0]["shop_item_attribute"].has_key(field):
                        sectiontext += u'<div class="section" id="' + sections[field]["id"] + '">\
                                <div class="title"><span>' + sections[field]["title"] + '</span></div>\
                                <div class="descrip">'
                        sectiontext += data["shop_items"][0]["shop_item_attribute"][field]
                        sectiontext += u'<div>&nbsp;</div></div></div>'
                    else:
                        if field == "feature":
                            if largeimgUrls:
                                sectiontext += u'<div class="section" id="' + sections[field]["id"] + '">\
                                            <div class="title"><span>' + sections[field]["title"] + '</span></div>\
                                            <div class="descrip">'
                                for url in largeimgUrls.values():
                                    sectiontext += '<img alt="" src="' + url + '" />'
                                sectiontext += u'<div>&nbsp;</div></div></div>'
                    prodtext += sectiontext

            if prodtext:
                zwsprodtext = u"<div><zws-product>" + prodtext + u"</zws-product></div>"
            else:
                zwsprodtext = u"<p>本商品暂无详情。</p>"

            #作者 出版社 出版时间 开本 包装 ISBN 定价
            attrs = {"author":"","publish_house":"","publish_date":"","size":"","binding":""}
            if data["shop_items"][0].has_key("shop_item_attribute"):
                for key in attrs:
                    if data["shop_items"][0]["shop_item_attribute"].has_key(key):
                        attrs[key] = data["shop_items"][0]["shop_item_attribute"][key]

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
                    %s, %s, %s, %s, '1', '',\
                    '1', '1', '0', '0', %s, '100',\
                    '0', '0', '0', '0', '0', '0', '0',\
                    %s, '', '-1', '-1', '0', NULL)"
                cursor.execute(sql,(catid,sn,title,
                                    goodsnumber,
                                    goodsweight,marketprice,shopprice,
                                    zwsprodtext,thumbImg,goodsImg,oriImg,
                                    addtime,
                                    gtype))

                #创建书籍信息字典
                #所有商品属性定义在表ecs_attribute中
                attridx = {1:attrs["author"],2:attrs["publish_house"],3:isbn,4:attrs["publish_date"],5:attrs["size"],7:attrs["binding"],232:oriprice}

                #唯一商品编号
                sql = "SELECT `goods_id` FROM " + goodstable + " WHERE `goods_sn`=%s"
                cursor.execute(sql,sn)
                goodsid = cursor.fetchone()[0]
                print(goodsid)

                #填入书籍信息
                for attrid,attr in attridx.items():
                    sql = "INSERT INTO " + goodsattrtable + " (`goods_attr_id`, `goods_id`, `attr_id`,\
                        `attr_value`, `attr_price`) VALUES (NULL, %s, %s, %s, '0')"
                    cursor.execute(sql,(goodsid,attrid,attr))

            connection.commit()
    finally:
        connection.close()
        fconn.quit()

    for url in ignored:
        print(url + " ignored!\n")

    print("Finished.")