#-*-coding:utf-8-*-
#＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝网页爬取图片＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
#Python 2.7

# 正则
import re
# 网络交互
import requests
# 操作系统功能
import os

import sys
import xml.dom.minidom
import webbrowser

# 定义一个类
class Spider:

    #定义一个函数
    def savePicture(self, _url):

        # 要爬的网址
        url = _url

        # 获取网页源代码
        html = requests.get(url).text

        # 正则
        regX = '<img alt=\"\" src=\".*.jpg\" title=\"\" id=\"modalBigImg\">'

        #找到第一张大图
        elem_url = re.findall(regX,html,re.S)
        for each in elem_url:
            print(each)
            pic_url = re.findall('http://.*.jpg',each,re.S)
            webbrowser.open(pic_url[0])

        #找到共有几张图
        #问号表示非贪婪匹配
        regX = '<ul id=\"mask-small-list-slider\">.*?</ul>'
        elem_url = re.findall(regX,html,re.S)
        numPicture = 0
        for each in elem_url:
            pic_url = re.findall('data-imghref=\"http://.*?.jpg\"',each,re.S)
            for pic in pic_url:
                print(re.findall('http://.*.jpg',pic)[0])
                numPicture += 1
        print("Here is " + str(numPicture) + " pictures!\n")

        #找书籍信息
        print("title: ")
        title = re.findall('<h1.*?</h1>',html,re.S)[0]
        print("subtitle: ")
        subtitle = re.findall('<h2>.*?</h2>',html,re.S)[0]
        print("author: ")
        author = re.findall('<span class=\"t1\" id=\"author\" dd_name=\".*?</span>',html,re.S)[0]
        print("press: ")
        press = re.findall('<span class=\"t1\" dd_name=\".*?</span>',html,re.S)[0]
        print("press time: ")
        presstime = re.findall('</span><span class=\"t1\">.*?</span>',html,re.S)[0]
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


#命令行参数：解析配置文件
def matchConfigFile(arg):

    regex = r".*[a-zA-Z0-9_]*\.xml$"
    res = scanForMatch(regex,arg)
    return res


#生成配置文件
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


def getNodeText(nodelist):
    text = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            text.append(node.data)
    return "".join(text)


#解析配置文件
def parseConfigFile(configFile):
    
    fullurl = []
    tree = xml.dom.minidom.parse(configFile)
    configNode = tree.getElementsByTagName(u"config")[0]
    for node in configNode.childNodes:
        if node.nodeName == 'http':
            picurl = "http://"
            for http in node.childNodes:
                if http.nodeName == 'url':
                    url = getNodeText(http.childNodes)
                    picurl += url + "/"
                elif http.nodeName == 'productID':
                    productID = getNodeText(http.childNodes)
                    picurl += productID
            picurl += ".html"
            print(picurl)
            fullurl.append(picurl)

    return fullurl


def spiderPictures(urllist):
    
    spider = Spider()

    for url in urllist:
        spider.savePicture(url)



def printUsage():

    print("")
    print("Usage modes:")
    print("")
    print('python ${THIS_SCRIPT_NAME}.py {--generate | -g}   (Generates a default configuration file')
    print("")    
    print('python ${THIS_SCRIPT_NAME}.py ${configFile}    (Uses all settings of the configuration file')
    print("")    


def main():

    print("Starting spider...\n")

    numArgs = 0
    for arg in sys.argv:
        numArgs += 1

    if numArgs == 1:
        print("Error: Required arguments not passed.")
        printUsage()
        return False
    
    if matchGenerateConfigFile(sys.argv[1]):
        generateDefaultConfig()
        return True
    elif matchConfigFile(sys.argv[1]):
        if not os.path.exists(sys.argv[1]):
            print('Error: config file does not exist.')
            return False
        else:
            url = parseConfigFile(sys.argv[1])
            spiderPictures(url)

    print("\nFinished.")
    return True



main()