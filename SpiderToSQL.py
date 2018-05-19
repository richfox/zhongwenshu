#-*-coding:utf-8-*-
#＝＝＝＝＝＝登书系统＝＝＝＝＝＝＝＝
#Python 2.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de

import io
import re
import pymysql
import requests
import xml
import lxml
import Spider
import pinyin
import time


def generate_sn(hanzi):
    #转成拼音
    res = pinyin.get_initial(hanzi)
    #转成大写
    res = res.upper()
    #只保留数字和字母
    nondc = re.compile('[^A-Z0-9_]+')
    res = nondc.sub('',res)
    #截短
    if len(res) > 2:
        res = res[:2]
    #10位时间戳
    res += str(int(time.time()))

    return res



def SpiderToSQL(sqls):
    print("Spider to SQL start...\n")

    for host,(username,password,dbname,charset,urls) in sqls.items():
        connection = pymysql.connect(host=host,user=username,password=password,db=dbname,charset=charset)
        try:
            for url,tag in urls.items():
                htmltext = requests.get(url).text
                parser = lxml.html.HTMLParser()
                htmltree = xml.etree.ElementTree.fromstring(htmltext,parser)
                #res = lxml.html.tostring(htmltree,pretty_print=True)
                #print(res)

                #爬取书籍信息
                titlenode = htmltree.xpath('//*[@id="product_info"]/div[1]/h1/@title')
                title = ''
                sn = ''
                if titlenode:
                    title = titlenode[0]
                    #唯一商品货号
                    sn = generate_sn(title)
                    

                authornode = htmltree.xpath('//*[@id="author"]//text()')
                author = ''
                for i,text in enumerate(authornode):
                    if i == 0:
                        for res in re.findall('\[.*\]',text):
                            author += res
                    else:
                        author += text

                pressnode = htmltree.xpath('//*[@id="product_info"]/div[2]/span[2]/a/text()')
                press = ''
                if pressnode:
                    press = pressnode[0]

                isbnnode = htmltree.xpath('//*[@id="detail_describe"]/ul/li[9]/text()')
                isbn = ''
                if isbnnode:
                    for res in re.findall('[0-9]+',isbnnode[0]):
                        isbn += res

                pressdatenode = htmltree.xpath('//*[@id="product_info"]/div[2]/span[3]/text()')
                pressdate = ''
                if pressdatenode:
                    res = re.split(':',pressdatenode[0])
                    if len(res) > 1:
                        pressdate = res[1]

                sizenode = htmltree.xpath('//*[@id="detail_describe"]/ul/li[5]/text()')
                size = ''
                if sizenode:
                    for res in re.findall('[0-9]+.*',sizenode[0]):
                        size += res

                packingnode = htmltree.xpath('//*[@id="detail_describe"]/ul/li[7]/text()')
                packing = ''
                if packingnode:
                    if re.match(u'.*平装',packingnode[0]):
                        packing = '平装'
                    elif re.match(u'.*精装',packingnode[0]):
                        packing = '精装'
                    elif re.match(u'.*盒装',packingnode[0]):
                        packing = '盒装'

                papernode = htmltree.xpath('//*[@id="detail_describe"]/ul/li[6]/text()')
                paper = ''
                if papernode:
                    res = re.split(u'：',papernode[0])
                    if len(res) > 1:
                        paper = res[1]

                oriprice = '¥' + Spider.searchOriginalPrice(htmltree)

                #商品图片
                Spider.spider_picture(url)

                #创建书籍信息字典
                #所有商品属性定义在表ecs_attribute中
                attrs = {1:author,2:press,3:isbn,4:pressdate,5:size,7:packing,10:paper,232:oriprice}

                #添加时间戳
                addtime = str(int(time.time()))

                #商品分类定义在表ecs_category中，先登到准上架分类'134'
                catid = '134'

                #商品大类定义在表ecs_goods_type中, '1'代表书
                gtype = '1'

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
                        '+', '0', '0', '', '0',\
                        '0', '0', '', '0', '0.00',\
                        '0', '0', '1', '', '',\
                        '', '', '', '', '1', '',\
                        '0', '1', '0', '0', %s, '100',\
                        '0', '0', '1', '0', '0', '0', '0',\
                        %s, '', '-1', '-1', '0', NULL)"
                    cursor.execute(sql,(catid,sn,title,addtime,gtype))

                    #唯一商品编号
                    sql = "SELECT `goods_id` FROM " + goodstable + " WHERE `goods_sn`=%s"
                    cursor.execute(sql,sn)
                    goodsid = cursor.fetchone()[0]
                    print(goodsid)

                    #填入书籍信息
                    for attrid,attr in attrs.items():
                        sql = "INSERT INTO " + goodsattrtable + " (`goods_attr_id`, `goods_id`, `attr_id`,\
                            `attr_value`, `attr_price`) VALUES (NULL, %s, %s, %s, '0')"
                        cursor.execute(sql,(goodsid,attrid,attr))

                    #新品到货
                    sql = "INSERT INTO " + goodscattable + " (`goods_id`, `cat_id`) VALUES (%s, '65')"
                    cursor.execute(sql,goodsid)
                    
                connection.commit()
        finally:
            connection.close()

    print("Finished.")




def SpiderToSQL_tuangou(sqls,params):
    print("Spider to SQL start...\n")

    #calc param
    rate = float(params[u'discount']) * float(params[u'multiple']) / float(params[u'exchange'])
    diff = format(float(params[u'dhl_eu']) - float(params[u'dhl_de']),'.2f') #保留两位小数
    baseprice = format(float(params[u'dhl_de']) + float(params[u'packing']),'.2f')

    for host,(username,password,dbname,charset,urls) in sqls.items():
        connection = pymysql.connect(host=host,user=username,password=password,db=dbname,charset=charset)
        try:
            goodnames = ''
            goodsdict = {}
            for url,tag in urls.items():
                htmltext = requests.get(url).text
                parser = lxml.html.HTMLParser()
                htmltree = xml.etree.ElementTree.fromstring(htmltext,parser)
                
                #dangdang编号
                sn = Spider.split_ddsn(url)

                #爬取书籍名称和定价
                titlenode = htmltree.xpath('//*[@id="product_info"]/div[1]/h1/@title')
                title = ''
                if titlenode:
                    title = titlenode[0]
                    titlesn = title + ' [' + sn + ']'
                    goodnames += titlesn
                    goodnames += '\r\n'
                
                oriprice = Spider.searchOriginalPrice(htmltree)
                groupbuyprice = format(float(oriprice) * rate,'.2f')
                goodsdict[sn] = (titlesn,groupbuyprice)

            diffsn = u'666666'
            diffname = u'------欧洲境内邮费补差------' + ' [' + diffsn + ']'
            goodnames += diffname
            goodsdict[diffsn] = (diffname,diff)


            #区分测试和主数据库
            goodstypetable = ""
            attrtable = ""
            goodsattrtable = ""
            if dbname == 'zhongw_test':
                goodstypetable = "ecs_test_goods_type"
                attrtable = "ecs_test_attribute"
                goodstable = "ecs_test_goods"
                goodsattrtable = "ecs_test_goods_attr"
            elif dbname == 'zhongwenshu_db1':
                goodstypetable = "ecs_goods_type"
                attrtable = "ecs_attribute"
                goodstable = "ecs_goods"
                goodsattrtable = "ecs_goods_attr"

            with connection.cursor() as cursor:
                #大类里添加某月团，并且只能添加一次
                catname = params[u'name']
                sql = "SELECT `cat_id` FROM " + goodstypetable + " WHERE `cat_name`=%s"
                res = cursor.execute(sql,catname)
                if res:
                    raise Exception, "this goodtype %s for groupbuy is already inserted in database!" %catname

                sql = "INSERT INTO " + goodstypetable + " (`cat_id`,`cat_name`,`enabled`,`attr_group`) \
                    VALUES (NULL,%s,'1','')"
                cursor.execute(sql,catname)

                sql = "SELECT `cat_id` FROM " + goodstypetable + " WHERE `cat_name`=%s"
                cursor.execute(sql,catname)
                goodtype = cursor.fetchone()[0]
                print(goodtype)

                #大类的多商品属性
                attrname = params[u'attr']
                sql = "INSERT INTO " + attrtable + " (`attr_id`, `cat_id`, `attr_name`, `attr_input_type`,\
                    `attr_type`, `attr_values`, `attr_index`, `sort_order`, `is_linked`, `attr_group`)\
                    VALUES (NULL, %s, %s, '1', '2', %s, '0', '0', '0', '0')"
                cursor.execute(sql,(goodtype,attrname,goodnames))

                sql = "SELECT `attr_id` FROM " + attrtable + " WHERE `cat_id`=%s"
                cursor.execute(sql,goodtype)
                attrid = cursor.fetchone()[0]
                print(attrid)

                #添加团购商品
                goodsname = params[u'goodsname']
                addtime = str(int(time.time()))
                #登到团购分类
                catid = '135'
                sn = generate_sn(goodsname)
                sql = "INSERT INTO " + goodstable + " (`goods_id`, `cat_id`, `goods_sn`,`goods_name`,\
                    `goods_name_style`, `click_count`, `brand_id`, `provider_name`, `goods_number`,\
                    `goods_weight`, `market_price`, `virtual_sales`, `shop_price`, `promote_price`,\
                    `promote_start_date`, `promote_end_date`, `warn_number`, `keywords`, `goods_brief`,\
                    `goods_desc`, `goods_thumb`, `goods_img`, `original_img`, `is_real`, `extension_code`,\
                    `is_on_sale`, `is_alone_sale`, `is_shipping`, `integral`, `add_time`, `sort_order`,\
                    `is_delete`, `is_best`, `is_new`, `is_hot`, `is_promote`, `bonus_type_id`, `last_update`,\
                    `goods_type`, `seller_note`, `give_integral`, `rank_integral`, `suppliers_id`, `is_check`) \
                    VALUES (NULL, %s, %s, %s,\
                    '+', '0', '0', '', '1000',\
                    '0', %s, '', %s, '0.00',\
                    '0', '0', '1', '', '',\
                    '', '', '', '', '1', '',\
                    '0', '1', '1', '0', %s, '100',\
                    '0', '1', '1', '1', '0', '0', '0',\
                    %s, '', '-1', '-1', '0', NULL)"
                cursor.execute(sql,(catid,sn,goodsname,baseprice,baseprice,addtime,goodtype))

                #唯一商品编号
                sql = "SELECT `goods_id` FROM " + goodstable + " WHERE `goods_sn`=%s"
                cursor.execute(sql,sn)
                goodsid = cursor.fetchone()[0]
                print(goodsid)

                #添加商品属性
                for sn,(name,price) in goodsdict.items():
                    sql = "INSERT INTO " + goodsattrtable + " (`goods_attr_id`, `goods_id`, `attr_id`, `attr_value`, `attr_price`) \
                        VALUES (NULL, %s, %s, %s, %s)"
                    cursor.execute(sql,(goodsid,attrid,name,price))

                connection.commit()
        finally:
            connection.close()

    print("Finished.")