#-*-coding:utf-8-*-
#＝＝＝＝＝＝登书系统＝＝＝＝＝＝＝＝
#Python 3.7
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
import sys
import proxy
import webbrowser
import json
import utility
import ftplib
import ImageProcess
import os
import win32com.client


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




def get_prodSpuInfo(text):
    info = ""
    bpair = {'{':'}'}
    idx = text.find("prodSpuInfo")
    jsonstart = text.find("{",idx)
    jsonend = -1
    if jsonstart != -1:
        jsonend = utility.search_close_bracket(text,jsonstart,bpair)
        if jsonend != -1:
            info = text[jsonstart:jsonend+1]

    return info


def get_xpath_index(tree,path,attr,separator):
    index = -1
    nodes = tree.xpath(path)
    for i,node in enumerate(nodes):
        name = re.split(separator,node.text)[0]
        if re.match(u'.*'+attr,name.replace(' ','')):
            index = i
            break
    return index+1



def show_all(tree,key):
    shownode = tree.xpath('//*[@id="%s"]//*[@id="%s-show"]' % (key,key))
    if shownode:
        shownode[0].set('style','display: none;')
    showallnode = tree.xpath('//*[@id="%s"]//*[@id="%s-show-all"]' % (key,key))
    areanode = tree.xpath('//*[@id="%s"]//*[@id="%s-textarea"]' % (key,key))
    if areanode:
        if showallnode:
            showallnode[0].set('style','display: inline;')
            #添加所有areanode子节点
            for child in areanode[0].xpath('child::node()'):
                if lxml.etree.iselement(child):
                    if child.tag == 'div':
                        if child.xpath('./img'):
                            imgnode = child.xpath('./img')[0]
                            data = imgnode.get('data-original')
                            alternativ = imgnode.get('alt')
                            child.remove(imgnode)
                            imgnode.clear()
                            imgnode.set('src',data)
                            imgnode.set('alt',alternativ)
                            imgnode.set('style','display: block;')
                            imgnode.set('width','716') #匹配网页宽度
                            child.append(imgnode)
                    elif child.tag == 'br':
                        child.tail = '' #去掉尾巴
                    showallnode[0].append(child)
                else:
                    lxml.etree.SubElement(showallnode[0],'span').text = child
        #从父节点删除areanode
        areanode[0].xpath('..')[0].remove(areanode[0])
    showmorenode = tree.xpath('//*[@id="%s"]//*[@class="section_show_more"]' % key)
    if showmorenode:
        showmorenode[0].clear()
        showmorenode[0].set('class','section_show_more')


#找到第一张大图并存储为3种尺寸
def saveFirstPicture(text,sn,fconn):
    imgurl = {}
    oriImg = ""
    goodsImg = ""
    thumbImg = ""
    galleryOriImg = ""
    galleryGoodsImg = ""
    galleryThumbImg = ""

    reg = '<img alt=\"\" src=\".*.jpg\" title=\"\" id=\"modalBigImg\">'
    urls = re.findall(reg,text,re.S)
    if urls:
        pic_url = re.findall('//.*.jpg',urls[0],re.S)
        if pic_url:
            webbrowser.open('http:' + pic_url[0])
            img = ImageProcess.Processor('http:' + pic_url[0])
            if img.Loaded():
                try:
                    if "server" in fconn:
                        src = img.Save("./temp",sn,img.Format())
                        target = img.Upload(fconn["server"],src,"source_img",sn,img.Format())
                        if target:
                            oriImg = fconn["path"] + target
                        target = img.Upload(fconn["server"],src,"source_img",sn+"_P",img.Format())
                        if target:
                            galleryOriImg = fconn["path"] + target
                        target = img.Upload(fconn["server"],src,"goods_img",sn+"_G_P",img.Format())
                        if target:
                            galleryGoodsImg = fconn["path"] + target

                        if img.Width()>230 and img.Height()>230:
                            img.Thumb(230,230)
                            src = img.Save("./temp",sn+"_G",img.Format())
                            target = img.Upload(fconn["server"],src,"goods_img",sn+"_G",img.Format())
                            if target:
                                goodsImg = fconn["path"] + target

                            img.Thumb(100,100)
                            src = img.Save("./temp",sn+"_T",img.Format())
                            target = img.Upload(fconn["server"],src,"thumb_img",sn+"_T",img.Format())
                            if target:
                                thumbImg = fconn["path"] + target
                            target = img.Upload(fconn["server"],src,"thumb_img",sn+"_T_P",img.Format())
                            if target:
                                galleryThumbImg = fconn["path"] + target
                        else:
                            target = img.Upload(fconn["server"],src,"goods_img",sn+"_G",img.Format())
                            if target:
                                goodsImg = fconn["path"] + target

                            if img.Width()>100 and img.Height()>100:
                                img.Thumb(100,100)
                                src = img.Save("./temp",sn+"_T",img.Format())
                                target = img.Upload(fconn["server"],src,"thumb_img",sn+"_T",img.Format())
                                if target:
                                    humbImg = fconn["path"] + target
                                target = img.Upload(fconn["server"],src,"thumb_img",sn+"_T_P",img.Format())
                                if target:
                                    galleryThumbImg = fconn["path"] + target
                            else:
                                target = img.Upload(fconn["server"],src,"thumb_img",sn+"_T",img.Format())
                                if target:
                                    thumbImg = fconn["path"] + target
                                target = img.Upload(fconn["server"],src,"thumb_img",sn+"_T_P",img.Format())
                                if target:
                                    galleryThumbImg = fconn["path"] + target
                    elif "local" in fconn:
                        root = "C:/xampp"
                        if not os.path.exists(root):
                            if os.path.exists(root + ".lnk"):
                                shell = win32com.client.Dispatch("WScript.Shell")
                                shortcut = shell.CreateShortCut(root + ".lnk")
                                root = shortcut.Targetpath
                        if not re.match(r".*test.*",fconn["local"]):
                            root += "/htdocs/ecshop/"
                        else:
                            root += "/htdocs/ecshop/test/"

                        img.Save(root+fconn["path"]+"source_img",sn,img.Format())
                        oriImg = fconn["path"] + "source_img/" + sn + "." + img.Format()
                        img.Save(root+fconn["path"]+"source_img",sn+"_P",img.Format())
                        galleryOriImg = fconn["path"] + "source_img/" + sn + "_P." + img.Format()
                        img.Save(root+fconn["path"]+"goods_img",sn+"_G_P",img.Format())
                        galleryGoodsImg = fconn["path"] + "goods_img/" + sn + "_G_P." + img.Format()

                        if img.Width()>230 and img.Height()>230:
                            img.Thumb(230,230)
                            img.Save(root+fconn["path"]+"goods_img/",sn+"_G",img.Format())
                            goodsImg = fconn["path"] + "goods_img/" + sn + "_G." + img.Format()

                            img.Thumb(100,100)
                            img.Save(root+fconn["path"]+"thumb_img/",sn+"_T",img.Format())
                            thumbImg = fconn["path"] + "thumb_img/" + sn + "_T." + img.Format()
                            img.Save(root+fconn["path"]+"thumb_img/",sn+"_T_P",img.Format())
                            galleryThumbImg = fconn["path"] + "thumb_img/" + sn + "_T_P." + img.Format()
                        else:
                            img.Save(root+fconn["path"]+"goods_img/",sn+"_G",img.Format())
                            goodsImg = fconn["path"] + "goods_img/" + sn + "_G." + img.Format()

                            if img.Width()>100 and img.Height()>100:
                                img.Thumb(100,100)
                                img.Save(root+fconn["path"]+"thumb_img/",sn+"_T",img.Format())
                                thumbImg = fconn["path"] + "thumb_img/" + sn + "_T." + img.Format()
                                img.Save(root+fconn["path"]+"thumb_img/",sn+"_T_P",img.Format())
                                galleryThumbImg = fconn["path"] + "thumb_img/" + sn + "_T_P." + img.Format()
                            else:
                                img.Save(root+fconn["path"]+"thumb_img/",sn+"_T",img.Format())
                                thumbImg = fconn["path"] + "thumb_img/" + sn + "_T." + img.Format()
                                img.Save(root+fconn["path"]+"thumb_img/",sn+"_T_P",img.Format())
                                galleryThumbImg = fconn["path"] + "thumb_img/" + sn + "_T_P." + img.Format()
                except:
                    oriImg = ""
                    goodsImg = ""
                    thumbImg = ""
                    galleryOriImg = ""
                    galleryGoodsImg = ""
                    galleryThumbImg = ""
                    print("unexpected error: {0}".format(sys.exc_info()[0]))
    
    imgurl["ori"] = oriImg
    imgurl["goods"] = goodsImg
    imgurl["thumb"] = thumbImg
    imgurl["galleryori"] = galleryOriImg
    imgurl["gallerygoods"] = galleryGoodsImg
    imgurl["gallerythumb"] = galleryThumbImg
    return imgurl


def SpiderToSQL(sqls):
    print("Spider to SQL start...\n")
    ignored = []

    for host,(username,password,dbname,charset,ftp,urls) in sqls.items():
        #连接数据库
        connection = pymysql.connect(host=host,user=username,password=password,database=dbname,charset=charset)
        
        #区分ftp服务器和本地
        fconn = {}
        fconn["path"] = ftp[3]
        if re.match(r".*your-server\.de$",ftp[0]):
            if ftp[4] == '0':
                fconn["server"] = ftplib.FTP(ftp[0],ftp[1],ftp[2])
            elif ftp[4] == '1':
                fconn["server"] = ftplib.FTP_TLS(ftp[0],ftp[1],ftp[2])
        elif re.match(r".*local.*",ftp[0]):
            fconn["local"] = ftp[0]

        try:
            #设置ftp上传路径
            if "server" in fconn:
                if ftp[4] == '1':
                    fconn["server"].prot_p()
                if dbname == 'zhongw_test':
                    fconn["server"].cwd("test/" + ftp[3])
                elif dbname == 'zhongwenshu_db1':
                    fconn["server"].cwd(ftp[3])

            for url,tag in urls.items():
                htmltext = ""
                ddsn = ""
                cookies = {}
                if tag == 0:
                    ddsn = Spider.split_ddsn(url)
                    cookies = Spider.split_params(url)
                    url = Spider.remove_params(url)
                    htmltext = utility.get_html_text(url,cookies)
                elif tag == 2:
                    tabledata = json.loads(url)
                    ddsn = tabledata[u'sn']
                    url = "http://product.dangdang.com/" + ddsn + ".html"
                    htmltext = utility.get_html_text(url)

                if not htmltext:
                    ignored.append(url)
                    continue

                parser = lxml.html.HTMLParser()
                htmltree = xml.etree.ElementTree.fromstring(htmltext,parser)
                
                headtitlenode = htmltree.xpath('/html/head/title/text()')
                if not headtitlenode:
                    print(url + " not exist!")
                    ignored.append(url)
                    continue
                else:
                    webbrowser.open(url)

                #爬取书籍信息
                attrnames = [u'开本',u'纸张',u'包装',u'ISBN']
                attrpath = '//*[@id="detail_describe"]/ul/li'
                attrindexs = Spider.get_xpath_indexs(htmltree,attrpath,attrnames,u'：')

                title = ''
                if tag == 0:
                    titlenode = htmltree.xpath('//*[@id="product_info"]/div[1]/h1/@title')
                    if titlenode:
                        title = titlenode[0]
                elif tag == 2:
                    if u'title' in tabledata:
                        title = tabledata[u'title']
                    
                #唯一商品货号
                sn = ''
                if title:
                    sn = generate_sn(title)
                    
                #数量
                goodsnumber = '0'
                if tag == 2:
                    if u'quantity' in tabledata:
                        goodsnumber = tabledata[u'quantity']

                #重量kg
                goodsweight = '0.000'
                if tag == 2:
                    if u'weight' in tabledata:
                        goodsweight = u"%.3f" % (float(tabledata[u'weight'])/1000)
                
                #价格
                shopprice = '0.00'
                marketprice = '0.00'
                if tag == 2:
                    if u'price' in tabledata:
                        shopprice = tabledata[u'price']
                        marketprice = u"%.2f" % (float(shopprice)*1.2)
                    elif u'rprice' in tabledata:
                        shopprice = tabledata[u'rprice']
                        marketprice = u"%.2f" % (float(shopprice)*1.2)

                oriprice = Spider.searchOriginalPrice(htmltree)
                if oriprice:
                    oriprice = '¥' + oriprice

                #作者
                authornode = htmltree.xpath('//*[@id="author"]//text()')
                author = ''
                for i,text in enumerate(authornode):
                    if i == 0:
                        for res in re.findall('\[.*\]',text):
                            author += res
                    else:
                        author += text

                #出版社
                pressnode = htmltree.xpath('//*[@id="product_info"]/div[2]/span[2]/a/text()')
                press = ''
                if pressnode:
                    press = pressnode[0]

                #ISBN
                isbn = ''
                if u'ISBN' in attrindexs:
                    isbnnode = htmltree.xpath(attrpath + '[' + str(attrindexs[u'ISBN']) + ']' + '/text()')
                    if isbnnode:
                        for res in re.findall('[0-9]+',isbnnode[0]):
                            isbn += res

                #出版时间
                pressdatenode = htmltree.xpath('//*[@id="product_info"]/div[2]/span[3]/text()')
                pressdate = ''
                if pressdatenode:
                    res = re.split(':',pressdatenode[0])
                    if len(res) > 1:
                        pressdate = res[1]

                #开本
                size = ''
                if u'开本' in attrindexs:
                    sizenode = htmltree.xpath(attrpath + '[' + str(attrindexs[u'开本']) + ']' + '/text()')
                    if sizenode:
                        for res in re.findall('[0-9]+.*',sizenode[0]):
                            size += res

                #包装
                packing = ''
                if u'包装' in attrindexs:
                    packingnode = htmltree.xpath(attrpath + '[' + str(attrindexs[u'包装']) + ']' + '/text()')
                    if packingnode:
                        if re.match(u'.*平装',packingnode[0]):
                            packing = '平装'
                        elif re.match(u'.*精装',packingnode[0]):
                            packing = '精装'
                        elif re.match(u'.*盒装',packingnode[0]):
                            packing = '盒装'

                #纸张
                paper = ''
                if u'纸张' in attrindexs:
                    papernode = htmltree.xpath(attrpath + '[' + str(attrindexs[u'纸张']) + ']' + '/text()')
                    if papernode:
                        res = re.split(u'：',papernode[0])
                        if len(res) > 1:
                            paper = res[1]

                #商品图片
                imgurl = saveFirstPicture(htmltext,sn,fconn)

                #商品标志
                psstr = get_prodSpuInfo(htmltext)
                psdata = json.loads(psstr)

                shopid = psdata["shopId"]
                catpath = psdata["categoryPath"]
                descmap = psdata["describeMap"]
                if descmap:
                    lastmap = descmap.split(',')[-1]
                    descmap = lastmap.split(':')[0] + "%3A" + lastmap.split(':')[1]

                #商品详情Ajax请求
                ajaxbaseurl = "http://product.dangdang.com/index.php?r=callback%2Fdetail&productId={id}&templateType=publish&describeMap={descmap}&shopId={shopid}&categoryPath={catpath}"
                ajaxurl = ajaxbaseurl.format(id=ddsn,descmap=descmap,shopid=shopid,catpath=catpath)
                ajaxtext = utility.get_html_text(ajaxurl,cookies=cookies)
                ajaxdata = json.loads(ajaxtext)
                ajaxhtmltext = ajaxdata["data"]["html"]
                zwsprodtext = u""
                if ajaxhtmltext:
                    ajaxhtmltree = utility.get_html_tree(ajaxhtmltext)
                    
                    #需要显示全部的块，比如插图和目录
                    show_all(ajaxhtmltree,"attachImage")
                    show_all(ajaxhtmltree,"catalog")
                    show_all(ajaxhtmltree,"authorIntroduction")

                    #产品特色图片匹配
                    imgnodes = ajaxhtmltree.xpath('//*[@id="feature"]//img')
                    for img in imgnodes:
                        img.set('width','716')

                    #编辑推荐图片匹配
                    imgnodes = ajaxhtmltree.xpath('//*[@id="abstract"]//img')
                    for img in imgnodes:
                        img.set('width','716')

                    #在线试读图片匹配
                    imgnodes = ajaxhtmltree.xpath('//*[@id="extract"]//img')
                    for img in imgnodes:
                        img.set('width','716')

                    #书摘插画图片匹配
                    imgnodes = ajaxhtmltree.xpath('//*[@id="attachImage"]//img')
                    for img in imgnodes:
                        if img.get('src') == 'images/loading.gif':
                            img.set('src',img.get('data-original'))
                            img.set('data-original','')
                            img.set('width','716')

                    #商品描述
                    producttext = ""
                    for item in ajaxhtmltree.body:
                        #重磅推荐广告忽略
                        if re.match('^describe_http:.*\.xml$',item.attrib["id"]):
                            continue
                        
                        try:
                            producttext += xml.etree.ElementTree.tostring(item,encoding="unicode")
                        except:
                            print("item \"%s\" ignored!" % item.attrib["id"])

                    #自定义样式
                    zwsprodtext = u"<div><zws-product>" + producttext + u"</zws-product></div>"
                else:
                    #非json格式的商品描述
                    ajaxbaseurl = "http://product.dangdang.com/index.php?r=callback%2Fdetail&productId={id}&templateType=mall&describeMap={descmap}&shopId={shopid}&categoryPath={catpath}"
                    ajaxurl = ajaxbaseurl.format(id=ddsn,descmap=descmap,shopid=shopid,catpath=catpath)
                    ajaxtext = utility.get_html_text(ajaxurl,cookies=cookies)
                    if ajaxtext:
                        ajaxhtmltree = utility.get_html_tree(ajaxtext)

                        #详情图片匹配
                        imgnodes = ajaxhtmltree.xpath('//*[@class="descrip"]//img')
                        for img in imgnodes:
                            if img.get('src') == 'images/loading.gif':
                                img.set('src',img.get('data-original'))
                                img.set('data-original','')
                                img.set('width','716')

                        #商品描述
                        producttext = ""
                        for item in ajaxhtmltree.body:
                            producttext += xml.etree.ElementTree.tostring(item,encoding="unicode")

                        #自定义样式
                        zwsprodtext = u"<div><zws-product>" + producttext + u"</zws-product></div>"
                    else:
                        zwsprodtext = u"<p>本商品暂无详情。</p>"


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
                goodsgallerytable = ""
                if dbname == 'zhongw_test':
                    goodstable = "ecs_test_goods"
                    goodsattrtable = "ecs_test_goods_attr"
                    goodscattable = "ecs_test_goods_cat"
                    goodsgallerytable = "ecs_test_goods_gallery"
                elif dbname == 'zhongwenshu_db1':
                    goodstable = "ecs_goods"
                    goodsattrtable = "ecs_goods_attr"
                    goodscattable = "ecs_goods_cat"
                    goodsgallerytable = "ecs_goods_gallery"

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
                        '0', '1', '0', '0', %s, '100',\
                        '0', '0', '1', '0', '0', '0', '0',\
                        %s, '', '-1', '-1', '0', NULL)"
                    cursor.execute(sql,(catid,sn,title,
                                        goodsnumber,
                                        goodsweight,marketprice,shopprice,
                                        zwsprodtext,imgurl["thumb"],imgurl["goods"],imgurl["ori"],
                                        addtime,
                                        gtype))

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

                    #填入书籍画册
                    if imgurl["galleryori"]:
                        sql = "INSERT INTO " + goodsgallerytable + " (`img_id`, `goods_id`, `img_url`, `img_desc`,\
                            `thumb_url`, `img_original`) VALUES (NULL, %s, %s, '', %s, %s)"
                        cursor.execute(sql,(goodsid,imgurl["gallerygoods"],imgurl["gallerythumb"],imgurl["galleryori"]))
                    
                connection.commit()
        finally:
            connection.close()

            if "server" in fconn:
                fconn["server"].quit()

    for url in ignored:
        print(url + " ignored!\n")

    print("Finished.")




def SpiderToSQL_tuangou(sqls,params):
    print("Spider to SQL start...\n")

    #calc param
    rate = float(params[u'discount']) * float(params[u'multiple']) / float(params[u'exchange'])
    diff = format(float(params[u'dhl_eu']) - float(params[u'dhl_de']),'.2f') #保留两位小数
    baseprice = format(float(params[u'dhl_de']) + float(params[u'packing']),'.2f')
    recssn = [rec.strip() for rec in params[u"recommend"].split('+')] #分解本期推荐当当单号，去除空格

    for host,(username,password,dbname,charset,urls) in sqls.items():
        connection = pymysql.connect(host=host,user=username,password=password,db=dbname,charset=charset)
        try:
            goodnames = ''
            goodsdict = {}
            recstext = {}
            for url,tag in urls.items():
                htmltext = ""
                ddsn = ""
                cookies = {}
                if tag == 0:
                    ddsn = Spider.split_ddsn(url)
                    cookies = Spider.split_params(url)
                    url = Spider.remove_params(url)
                    htmltext = utility.get_html_text(url,cookies)
                elif tag == 2:
                    data = json.loads(url)
                    ddsn = data[u'sn']
                    url = "http://product.dangdang.com/" + ddsn + ".html"
                    htmltext = utility.get_html_text(url)

                parser = lxml.html.HTMLParser()
                htmltree = xml.etree.ElementTree.fromstring(htmltext,parser)


                #爬取书籍名称和定价
                titlenode = htmltree.xpath('//*[@id="product_info"]/div[1]/h1/@title')
                titlesn = ''
                if titlenode:
                    title = titlenode[0]
                    titlesn = title + ' [' + ddsn + ']'
                    goodnames += titlesn
                    goodnames += '\r\n'
                
                oriprice = Spider.searchOriginalPrice(htmltree)
                groupbuyprice = 0.0
                if oriprice:
                    #dangdang 自营
                    if len(ddsn) == 8:
                        groupbuyprice = format(float(oriprice) * rate + float(params[u'offset']),'.2f')
                    #非dangdang 自营
                    else:
                        groupbuyprice = format(float(oriprice) * rate + float(params[u'offset2']),'.2f')

                goodsdict[ddsn] = (titlesn,groupbuyprice)

                #本期推荐
                if ddsn in recssn:
                    #商品标志
                    psstr = get_prodSpuInfo(htmltext)
                    psdata = json.loads(psstr)

                    shopid = psdata["shopId"]
                    catpath = psdata["categoryPath"]
                    descmap = psdata["describeMap"]
                    if descmap:
                        lastmap = descmap.split(',')[-1]
                        descmap = lastmap.split(':')[0] + "%3A" + lastmap.split(':')[1]

                    #商品详情Ajax请求
                    ajaxbaseurl = "http://product.dangdang.com/index.php?r=callback%2Fdetail&productId={id}&templateType=publish&describeMap={descmap}&shopId={shopid}&categoryPath={catpath}"
                    ajaxurl = ajaxbaseurl.format(id=ddsn,descmap=descmap,shopid=shopid,catpath=catpath)
                    ajaxtext = utility.get_html_text(ajaxurl,cookies=cookies)
                    ajaxdata = json.loads(ajaxtext)
                    ajaxhtmltext = ajaxdata["data"]["html"]
                    producttext = u""
                    if ajaxhtmltext:
                        ajaxhtmltree = utility.get_html_tree(ajaxhtmltext)

                        #需要显示全部的块，比如插图和目录
                        show_all(ajaxhtmltree,"attachImage")
                        show_all(ajaxhtmltree,"catalog")
                        show_all(ajaxhtmltree,"authorIntroduction")

                        #产品特色图片匹配
                        imgnode = ajaxhtmltree.xpath('//*[@id="feature"]//img')
                        if imgnode:
                            imgnode[0].set('width','716')

                        #商品描述
                        producttext = ""
                        for item in ajaxhtmltree.body:
                            #重磅推荐广告忽略
                            if re.match('^describe_http:.*\.xml$',item.attrib["id"]):
                                continue

                            try:
                                producttext += xml.etree.ElementTree.tostring(item,encoding="unicode")
                            except:
                                print("item \"%s\" ignored!" % item.attrib["id"])
                    else:
                        producttext = u"<p>本商品暂无详情。</p>"

                    recstext[ddsn] = producttext


            diffsn = params[u'dhl_diff_sn']
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
                    raise Exception("this goodtype %s for groupbuy is already inserted in database!" %catname)

                sql = "INSERT INTO " + goodstypetable + " (`cat_id`,`cat_name`,`enabled`,`attr_group`) \
                    VALUES (NULL,%s,'1','')"
                cursor.execute(sql,catname)

                sql = "SELECT `cat_id` FROM " + goodstypetable + " WHERE `cat_name`=%s"
                cursor.execute(sql,catname)
                goodtype = cursor.fetchone()[0]
                print(goodstypetable + ": " + str(goodtype))

                #大类的多商品属性
                attrname = params[u'attr']
                sql = "INSERT INTO " + attrtable + " (`attr_id`, `cat_id`, `attr_name`, `attr_input_type`,\
                    `attr_type`, `attr_values`, `attr_index`, `sort_order`, `is_linked`, `attr_group`)\
                    VALUES (NULL, %s, %s, '1', '2', %s, '0', '0', '0', '0')"
                cursor.execute(sql,(goodtype,attrname,goodnames))

                sql = "SELECT `attr_id` FROM " + attrtable + " WHERE `cat_id`=%s"
                cursor.execute(sql,goodtype)
                attrid = cursor.fetchone()[0]
                print(attrtable + ":" + str(attrid))

                #本期推荐描述
                zwsprodtext = u"<div><zws-product>"
                for ddsn,text in recstext.items():
                    zwsprodtext += text
                zwsprodtext += u"</zws-product></div>"

                #添加团购商品
                goodsname = params[u'goodsname']
                addtime = str(int(time.time()))
                #登到团购分类，定义在表ecs_category中
                catid = '135'
                #商品品牌定义在表ecs_brand中，限定为团购7%增值税
                brand = '53'
                #唯一商品货号
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
                    '+', '0', %s, '', '1000',\
                    '0', %s, '', %s, '0.00',\
                    '0', '0', '1', '', '',\
                    %s, '', '', '', '1', '',\
                    '0', '1', '1', '0', %s, '100',\
                    '0', '1', '1', '1', '0', '0', '0',\
                    %s, '', '-1', '-1', '0', NULL)"
                cursor.execute(sql,(catid,sn,goodsname,brand,baseprice,baseprice,zwsprodtext,addtime,goodtype))

                sql = "SELECT `goods_id` FROM " + goodstable + " WHERE `goods_sn`=%s"
                cursor.execute(sql,sn)
                goodsid = cursor.fetchone()[0]
                print(goodstable + ":" + str(goodsid))

                #添加商品属性
                for ddsn,(name,price) in goodsdict.items():
                    sql = "INSERT INTO " + goodsattrtable + " (`goods_attr_id`, `goods_id`, `attr_id`, `attr_value`, `attr_price`) \
                        VALUES (NULL, %s, %s, %s, %s)"
                    cursor.execute(sql,(goodsid,attrid,name,price))

                connection.commit()
        finally:
            connection.close()

    print("Finished.")