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

                #商品图片
                Spider.spider_picture(url)

                #创建书籍信息字典
                attrs = {1:author,2:press,3:isbn,4:pressdate,5:size,7:packing,8:paper}

                with connection.cursor() as cursor:
                    sql = "INSERT INTO `ecs_test_goods` (`goods_id`, `cat_id`, `goods_sn`,`goods_name`,\
                    `goods_name_style`, `click_count`, `brand_id`, `provider_name`, `goods_number`,\
                    `goods_weight`, `market_price`, `virtual_sales`, `shop_price`, `promote_price`,\
                    `promote_start_date`, `promote_end_date`, `warn_number`, `keywords`, `goods_brief`,\
                    `goods_desc`, `goods_thumb`, `goods_img`, `original_img`, `is_real`, `extension_code`,\
                    `is_on_sale`, `is_alone_sale`, `is_shipping`, `integral`, `add_time`, `sort_order`,\
                    `is_delete`, `is_best`, `is_new`, `is_hot`, `is_promote`, `bonus_type_id`, `last_update`,\
                    `goods_type`, `seller_note`, `give_integral`, `rank_integral`, `suppliers_id`, `is_check`) \
                    VALUES (NULL, '56', %s, %s,\
                    '+', '0', '0', '', '0',\
                    '0', '0', '', '0', '0.00',\
                    '0', '0', '1', '', '',\
                    '', '', '', '', '1', '',\
                    '0', '1', '0', '0', '0', '100',\
                    '0', '0', '1', '0', '0', '0', '0',\
                    '1', '', '-1', '-1', '0', NULL)"
                    cursor.execute(sql,(sn,title))

                    #唯一商品编号
                    sql = "SELECT `goods_id` FROM `ecs_test_goods` WHERE `goods_sn`=%s"
                    cursor.execute(sql,sn)
                    goodsid = cursor.fetchone()[0]
                    print(goodsid)

                    #填入书籍信息
                    for attrid,attr in attrs.items():
                        sql = "INSERT INTO `ecs_test_goods_attr` (`goods_attr_id`, `goods_id`, `attr_id`,\
                        `attr_value`, `attr_price`) VALUES (NULL, %s, %s, %s, '0')"
                        cursor.execute(sql,(goodsid,attrid,attr))

                    #新品到货
                    sql = "INSERT INTO `ecs_test_goods_cat` (`goods_id`, `cat_id`) VALUES (%s, '65')"
                    cursor.execute(sql,goodsid)
                    
                connection.commit()
        finally:
            connection.close()

    print("Finished.")