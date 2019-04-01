#-*-coding:utf-8-*-
#＝＝＝＝＝＝command line＝＝＝＝＝
#Python 2.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de

import sys
import os
import Spider
import Visitor
import SQLimport
import SpiderToSQL
import taobao
import winxuan
import re
import xml.dom.minidom
import ExcelToSQL
import json



def printUsage():
    print("")
    print("Usage modes:")
    print("")
    print('python ${THIS_SCRIPT_NAME}.py {--generate | -g}   Generates a default configuration file')
    print("")
    print('python ${THIS_SCRIPT_NAME}.py {-o}   Generates a default order configuration file')
    print("")
    print('python ${THIS_SCRIPT_NAME}.py {-sql}    Generates a default sql configuration file')
    print("")
    print('python ${THIS_SCRIPT_NAME}.py {-t | -taobao}    spider taobao.com')
    print("")
    print('python ${THIS_SCRIPT_NAME}.py {-wx}   interface for winxuan.com')
    print("")
    print('python ${THIS_SCRIPT_NAME}.py {-tuan | -tuangou}    Generates a config file for parameters of grouping buy')
    print("")
    print('python ${THIS_SCRIPT_NAME}.py ${config.xml}    Uses all settings of the xml configuration file')
    print("")
    print('python ${THIS_SCRIPT_NAME}.py ${file.html}    visit the html file and write result to _books.xlsx')
    print("")
    print('python ${THIS_SCRIPT_NAME}.py ${file.html} {-tuan | -tuangou}    visit the html file and write result to _books.xlsx for groupbuy')
    print("")
    print('python ${THIS_SCRIPT_NAME}.py {url,id}    Generates a special configuration file, then use it')
    print("")
    print('python ${THIS_SCRIPT_NAME}.py ${sql.sxml}    import to database with settings of the sxml file')
    print("")
    print('python ${THIS_SCRIPT_NAME}.py ${config.xml} ${sql.sxml}   use config to search attributes than import to database with settings of the sxml file')
    print("")
    print('python ${THIS_SCRIPT_NAME}.py ${config.xml} {-tuan | -tuangou}   use config to search attributes write result to _books.xlsx for groupbuy')
    print("")
    print('python ${THIS_SCRIPT_NAME}.py ${config.xml} ${sql.sxml} ${groupbuyConfig.xml}  use config to search attributes than import to database with settings of the sxml file for groupbuy')
    print("")
    print('python ${THIS_SCRIPT_NAME}.py ${_jsform.xlsx} ${sql.sxml} ${groupbuyConfig.xml}   write jsform data from excel to database with settings of the sxml file for groupbuy')
    print("")


#匹配命令行参数
def scanForMatch(pattern,arg):
    match = re.match(pattern,arg)
    if match:
        return True
    else:
        return False


#命令行参数：生成配置文件
def matchGenerateConfigFile(arg):
    regex = r"-generate$|-g$"
    res = scanForMatch(regex,arg)
    return res

def matchGenerateOrderConfigFile(arg):
    regex = r"-o$"
    res = scanForMatch(regex,arg)
    return res

def matchGenerateSqlConigFile(arg):
    regex = r"-sql$"
    res = scanForMatch(regex,arg)
    return res

def matchTaobao(arg):
    regex = r"-taobao$|-t$"
    res = scanForMatch(regex,arg)
    return res

def matchWinxuan(arg):
    regex = r"-wx$"
    res = scanForMatch(regex,arg)
    return res

def matchTuangou(arg):
    regex = r"-tuan$|-tuangou$"
    res = scanForMatch(regex,arg)
    return res

def matchGenerateGroupbuyConigFile(arg):
    regex = r"-tuan$|-tuangou$"
    res = scanForMatch(regex,arg)
    return res

#命令行参数：解析配置文件
def matchConfigFile(arg):
    regex = r".*[a-zA-Z0-9_]*\.xml$"
    res = scanForMatch(regex,arg)
    return res

def matchOrderHtmlFile(arg):
    regex = r".*[a-zA-Z0-9_]*\.html$"
    res = scanForMatch(regex,arg)
    return res


def matSqlFile(arg):
    regex = r".*[a-zA-Z0-9_]*\.sxml$"
    res = scanForMatch(regex,arg)
    return res

def matchGroupbuyConfigFile(arg):
    regex = r".*groupbuyConfig\.xml$"
    res = scanForMatch(regex,arg)
    return res

def matchJsformDataFile(arg):
    regex = r".*_jsform\.xlsx$"
    res = scanForMatch(regex,arg)
    return res


#命令行参数：更新配置文件
def matchUrl(arg):
    regex = r".*[a-zA-Z0-9_]*\.com$"
    res = scanForMatch(regex,arg)
    return res


#生成默认配置文件
def generateDefaultConfig():
    fp = open('dangdangConfig.xml','w')

    content = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + \
            "<config>\n" + \
            "  <!-- Exmaple for catch picture from dangdang: http://product.dangdang.com/20771643.html -->\n" + \
            "  <http>\n" + \
            "    <url domain=\"product.dangdang.com\">\n" + \
            "      <productID>20771643</productID>\n" + \
            "      <productID>21022011</productID>\n" + \
            "    </url>\n" + \
            "  </http>\n" + \
            "  <excel>\n" + \
            "    <col index=\"title dprice bonus quantity sum total sn rprice price weight\">\n" + \
            "      <row>test	¥87.60		1	87.6		23295770	25.03	13.51	1670</row>\n" + \
            "    </col>\n" + \
            "  </excel>\n" + \
            "</config>\n"

    fp.write(content)
    fp.close()
    print('Generated default config file: dangdangConfig.xml')

def generateDefaultOrderConfig():
    fp = open('dangdangConfig.xml','w')

    content = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + \
            "<config>\n" + \
            "  <!-- Exmaple for order from dangdang: http://order.dangdang.com/orderdetails.aspx?orderid=35672123788 -->\n" + \
            "  <http>\n" + \
            "    <url>order.dangdang.com</url>\n" + \
            "    <orderID>35672123788</orderID>\n" + \
            "  </http>\n" + \
            "</config>\n"

    fp.write(content)
    fp.close()
    print('Generated default order config file: dangdangConfig.xml')

def generateDefaultSqlConfig():
    fp = open('mySQLConfig.sxml','w')

    content = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + \
            "<config>\n" + \
            "  <!-- Exmaple for mysql server: https://konsoleh.your-server.de/ -->\n" + \
            "  <mysql>\n" + \
            "    <host>konsoleh.your-server.de</host>\n" + \
            "    <user>to_input</user>\n" + \
            "    <password>to_input</password>\n" + \
            "    <db>zhongw_test</db>\n" + \
            "    <charset>utf8</charset>\n" + \
            "  </mysql>\n" + \
            "</config>\n"

    fp.write(content)
    fp.close()
    print('Generated default sql config file: mySQLConfig.sxml')


def generateDefaultGroupbuyConfig():
    fp = open('groupbuyConfig.xml','w')

    content = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + \
            "<config>\n" + \
            "  <!-- parameter for grouping buy -->\n" + \
            "  <!-- 团购类型名称，必须独一无二！！！ -->\n" + \
            "  <name>20180501GBuy</name>\n" + \
            "  <!-- 团购类型属性 -->\n" + \
            "  <attr>团购商品</attr>\n" + \
            "  <goodsname>5月团</goodsname>\n" + \
            "  <discount>0.60</discount>\n" + \
            "  <multiple>1.40</multiple>\n" + \
            "  <exchange>7.80</exchange>\n" + \
            "  <dhl_de>5.00</dhl_de>\n" + \
            "  <dhl_eu>10.00</dhl_eu>\n" + \
            "  <packing>3.00</packing>\n" + \
            "  <dhl_diff_sn>666666</dhl_diff_sn>\n" + \
            "</config>\n"

    fp.write(content)
    fp.close()
    print('Generated default grouping buy parameter file: groupbuyConfig.xml')


def getNodeText(nodelist):
    text = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            text.append(node.data)
    return "".join(text)


#解析配置文件
def parseConfigFile(configFile):
    values = {}
    tag = -1
    tree = xml.dom.minidom.parse(configFile)
    configNode = tree.getElementsByTagName(u"config")[0]
    for node in configNode.childNodes:
        if node.nodeName == "http":
            protocol = "http://"
            for locator in node.childNodes:
                if locator.nodeName == "url":
                    domain = locator.getAttribute("domain")
                    url = protocol + domain + "/"
                    for id in locator.childNodes:
                        if id.nodeName == "productID":
                            productID = getNodeText(id.childNodes)
                            fullurl = url + productID + ".html"
                            tag = 0
                            print(fullurl)
                            values[fullurl] = tag
                        elif id.nodeName == "orderID":
                            orderID = getNodeText(id.childNodes)
                            fullurl = url + "orderdetails.aspx?orderid=" + orderID
                            tag = 1
                            print(fullurl)
                            values[fullurl] = tag
        elif node.nodeName == 'excel':
            for column in node.childNodes:
                if column.nodeName == 'col':
                    idx = column.getAttribute("index").split(' ')
                    print(idx)
                    for row in column.childNodes:
                        if row.nodeName == 'row':
                            cells = getNodeText(row.childNodes).split('\t')
                            tag = 2
                            print(cells)
                            data = {}
                            for i,cell in enumerate(cells):
                                data[idx[i]] = cell
                            values[json.dumps(data)] = tag

    return values


def parseSqlConfigFile(configFile):
    sqls = {}
    tree = xml.dom.minidom.parse(configFile)
    configNode = tree.getElementsByTagName(u"config")[0]
    for node in configNode.childNodes:
        if node.nodeName == 'mysql':
            host = ""
            username = ""
            password = ""
            dbname = ""
            charset = ""
            for mysql in node.childNodes:
                if mysql.nodeName == 'host':
                    host = getNodeText(mysql.childNodes)
                elif mysql.nodeName == 'user':
                    username = getNodeText(mysql.childNodes)
                elif mysql.nodeName == 'password':
                    password = getNodeText(mysql.childNodes)
                elif mysql.nodeName == 'db':
                    dbname = getNodeText(mysql.childNodes)
                elif mysql.nodeName == 'charset':
                    charset = getNodeText(mysql.childNodes)

            sqls[host] = (username,password,dbname,charset)
    return sqls


def parseGroupbuyConfigFile(configFile):
    groupbuyparams = {}
    tree = xml.dom.minidom.parse(configFile)
    configNode = tree.getElementsByTagName(u"config")[0]
    for node in configNode.childNodes:
        groupbuyparams[node.nodeName] = getNodeText(node.childNodes)

    return groupbuyparams


#生成配置文件
def generateConfig(url,id):
    config = xml.etree.ElementTree.Element("config")
    http = xml.etree.ElementTree.SubElement(config,"http")
    xml.etree.ElementTree.SubElement(http,"url").text = url
    xml.etree.ElementTree.SubElement(http,"productID").text = id
    tree = xml.etree.ElementTree.ElementTree(config)
    tree.write("dangdangConfig.xml","utf-8")
    print('Generated special config file: dangdangConfig.xml')



def main():
    numArgs = 0
    for arg in sys.argv:
        numArgs += 1

    if numArgs == 1:
        print("Error: Required arguments not passed.")
    elif numArgs == 2:
        if matchGenerateConfigFile(sys.argv[1]):
            generateDefaultConfig()
            return True
        elif matchGenerateOrderConfigFile(sys.argv[1]):
            generateDefaultOrderConfig()
            return True
        elif matchGenerateSqlConigFile(sys.argv[1]):
            generateDefaultSqlConfig()
            return True
        elif matchTaobao(sys.argv[1]):
            taobao.aptamil()
            return True
        elif matchWinxuan(sys.argv[1]):
            winxuan.get_shop_items()
            return True
        elif matchGenerateGroupbuyConigFile(sys.argv[1]):
            generateDefaultGroupbuyConfig()
            return True
        elif matchConfigFile(sys.argv[1]):
            if not os.path.exists(sys.argv[1]):
                print('Error: config file does not exist.')
                return False
            else:
                urls = parseConfigFile(sys.argv[1])
                Spider.spiderStart(urls)
                return True
        elif matchOrderHtmlFile(sys.argv[1]):
            if not os.path.exists(sys.argv[1]):
                print('Error: config file does not exist.')
                return False
            else:
                Visitor.visitorStart(sys.argv[1])
                return True
        elif matSqlFile(sys.argv[1]):
            if not os.path.exists(sys.argv[1]):
                print('Error: sql config file does not exist.')
                return False
            else:
                sqls = parseSqlConfigFile(sys.argv[1])
                SQLimport.SQLimport(sqls)
                return True
    elif numArgs == 3:
        if matchUrl(sys.argv[1]):
            generateConfig(sys.argv[1],sys.argv[2])
            urls = parseConfigFile("dangdangConfig.xml")
            Spider.spiderStart(urls)
            return True
        elif matchConfigFile(sys.argv[1]) and matSqlFile(sys.argv[2]):
            if not os.path.exists(sys.argv[1]):
                print('Error: config file does not exist.')
                return False
            if not os.path.exists(sys.argv[2]):
                print('Error: sql config file does not exist.')
                return False
            urls = parseConfigFile(sys.argv[1])
            sqls = parseSqlConfigFile(sys.argv[2])
            for host,(username,password,dbname,charset) in sqls.items():
                for url,tag in urls.items():
                    if (tag == 1):
                        del urls[url]
                sqls[host] = (username,password,dbname,charset,urls)
            SpiderToSQL.SpiderToSQL(sqls)
            return True
        elif matchConfigFile(sys.argv[1]) and matchTuangou(sys.argv[2]):
            if not os.path.exists(sys.argv[1]):
                print('Error: config file does not exist.')
                return False
            urls = parseConfigFile(sys.argv[1])
            Spider.spider_to_excel(urls)
            return True
        elif matchOrderHtmlFile(sys.argv[1]) and matchTuangou(sys.argv[2]):
            if not os.path.exists(sys.argv[1]):
                print('Error: config file does not exist.')
                return False
            Visitor.visitorStart(sys.argv[1],True)
            return True
    elif numArgs == 4:
        if matchConfigFile(sys.argv[1]) and matSqlFile(sys.argv[2]) and matchGroupbuyConfigFile(sys.argv[3]):
            if not os.path.exists(sys.argv[1]):
                print('Error: config file does not exist, use -g to generate it')
                return False
            if not os.path.exists(sys.argv[2]):
                print('Error: sql config file does not exist, use -sql to generate it')
                return False
            if not os.path.exists(sys.argv[3]):
                print('Error: grouping bug config file does not exist, use -tuan to generate it')
                return False
            urls = parseConfigFile(sys.argv[1])
            sqls = parseSqlConfigFile(sys.argv[2])
            params = parseGroupbuyConfigFile(sys.argv[3])
            for host,(username,password,dbname,charset) in sqls.items():
                for url,tag in urls.items():
                    if (tag == 1):
                        del urls[url]
                sqls[host] = (username,password,dbname,charset,urls)
            SpiderToSQL.SpiderToSQL_tuangou(sqls,params)
            return True
        elif matchJsformDataFile(sys.argv[1]) and matSqlFile(sys.argv[2]) and matchGroupbuyConfigFile(sys.argv[3]):
            if not os.path.exists(sys.argv[1]):
                print('Error: jsform excel file does not exist, use jsform to export it')
                return False
            if not os.path.exists(sys.argv[2]):
                print('Error: sql config file does not exist, use -sql to generate it')
                return False
            if not os.path.exists(sys.argv[3]):
                print('Error: grouping bug config file does not exist, use -tuan to generate it')
                return False
            sqls = parseSqlConfigFile(sys.argv[2])
            params = parseGroupbuyConfigFile(sys.argv[3])
            ExcelToSQL.ExcelToSQLGBuy(sqls,params)
            return True

    printUsage()
    return False



main()