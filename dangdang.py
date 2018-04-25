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
import re
import xml.dom.minidom



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
    print('python ${THIS_SCRIPT_NAME}.py {-taobao | -t}    spider taobao.com')
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

def matchTuangou(arg):
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
            "    <url>product.dangdang.com</url>\n" + \
            "    <productID>20771643</productID>\n" + \
            "  </http>\n" + \
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
    

def getNodeText(nodelist):
    text = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            text.append(node.data)
    return "".join(text)


#解析配置文件
def parseConfigFile(configFile):
    urls = {}
    tree = xml.dom.minidom.parse(configFile)
    configNode = tree.getElementsByTagName(u"config")[0]
    for node in configNode.childNodes:
        if node.nodeName == 'http':
            fullurl = "http://"
            tag = -1
            for http in node.childNodes:
                if http.nodeName == 'url':
                    url = getNodeText(http.childNodes)
                    fullurl += url + "/"
                elif http.nodeName == 'productID':
                    productID = getNodeText(http.childNodes)
                    fullurl += productID
                    fullurl += ".html"
                    tag = 0
                elif http.nodeName == 'orderID':
                    orderID = getNodeText(http.childNodes)
                    fullurl += "orderdetails.aspx?orderid=" + orderID
                    tag = 1

            print(fullurl)
            urls[fullurl] = tag

    return urls


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
                    if (tag != 0):
                        del urls[url]
                sqls[host] = (username,password,dbname,charset,urls)
            SpiderToSQL.SpiderToSQL(sqls)
            return True
        elif matchConfigFile(sys.argv[1]) and matchTuangou(sys.argv[2]):
            return True
        elif matchOrderHtmlFile(sys.argv[1]) and matchTuangou(sys.argv[2]):
            if not os.path.exists(sys.argv[1]):
                print('Error: config file does not exist.')
                return False
            Visitor.visitorStart(sys.argv[1],True)
            return True

    printUsage()
    return False



main()