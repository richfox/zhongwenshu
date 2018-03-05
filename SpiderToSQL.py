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
                treeTitle = htmltree.xpath('//*[@id="product_info"]/div[1]/h1/@title')
                title = treeTitle[0]
                sn = 'ABCD0123'

                treeAuthor = htmltree.xpath('//*[@id="author"]//text()')
                author = ''
                for text in treeAuthor:
                    author += text
                
                press = '吉林大学出版社'
                isbn = '0123456789'
                pressdate = '2018-3-5'
                size = '32开'
                packing = '平装'
                attrs = {1:author,2:press,3:isbn,4:pressdate,5:size,7:packing}

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
                    '+', '17', '0', '', '0',\
                    '1.520', '33.34', '', '27.79', '0.00',\
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
                    
                connection.commit()
        finally:
            connection.close()

    print("Finished.")