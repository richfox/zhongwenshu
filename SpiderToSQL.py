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
                titletree = htmltree.xpath('//*[@id="product_info"]/div[1]/h1/@title')
                title = ''
                if titletree:
                    title = titletree[0]

                sn = 'ABCD01234'

                authortree = htmltree.xpath('//*[@id="author"]//text()')
                author = ''
                for i,text in enumerate(authortree):
                    if i == 0:
                        for res in re.findall('\[.*\]',text):
                            author += res
                    else:
                        author += text

                presstree = htmltree.xpath('//*[@id="product_info"]/div[2]/span[2]/a/text()')
                press = ''
                if presstree:
                    press = presstree[0]

                isbntree = htmltree.xpath('//*[@id="detail_describe"]/ul/li[9]/text()')
                isbn = ''
                if isbntree:
                    for res in re.findall('[0-9]+',isbntree[0]):
                        isbn += res

                pressdatetree = htmltree.xpath('//*[@id="product_info"]/div[2]/span[3]/text()')
                pressdate = ''
                if pressdatetree:
                    res = re.split(':',pressdatetree[0])
                    if len(res) > 1:
                        pressdate = res[1]

                sizetree = htmltree.xpath('//*[@id="detail_describe"]/ul/li[5]/text()')
                size = ''
                if sizetree:
                    for res in re.findall('[0-9]+.*',sizetree[0]):
                        size += res

                packing = '平装'

                #创建书籍信息字典
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
                    
                connection.commit()
        finally:
            connection.close()

    print("Finished.")