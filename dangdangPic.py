#-*-coding:utf-8-*-
#＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝网页爬取图片＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
#Python 2.7

import sys
import xml.dom.minidom
import webbrowser

# 正则
import re
# 操作系统功能
import os
# 网络交互
import requests



#辅助函数
def remove_noise(section):
    res = section
    for each in re.findall(u'<.*?>',section,re.S):
        res = res.replace(each,u'').replace(u'\r\n',u'')
    return res


#爬虫类
class Spider:
    def __init__(self,url):
        # 获取网页源代码
        self._html = requests.get(url).text

    #找图片
    def searchPicture(self):
        # 正则
        regX = '<img alt=\"\" src=\".*.jpg\" title=\"\" id=\"modalBigImg\">'

        #找到第一张大图
        elem_url = re.findall(regX,self._html,re.S)
        for each in elem_url:
            print(each)
            pic_url = re.findall('http://.*.jpg',each,re.S)
            webbrowser.open(pic_url[0])

        #找到共有几张图
        #问号表示非贪婪匹配
        regX = '<ul id=\"mask-small-list-slider\">.*?</ul>'
        elem_url = re.findall(regX,self._html,re.S)
        numPicture = 0
        for each in elem_url:
            pic_url = re.findall('data-imghref=\"http://.*?.jpg\"',each,re.S)
            for pic in pic_url:
                print(re.findall('http://.*.jpg',pic)[0])
                numPicture += 1
        print("Here is " + str(numPicture) + " pictures!\n")

    #找书籍信息
    def searchAttr(self):
        title = re.findall(u'<h1 title=.*?>.*?</h1>',self._html,re.S)[0]
        print(u'标题：' + remove_noise(title))
        subtitle = re.findall(u'<h2>.*?</h2>',self._html,re.S)[0]
        print(u'副标题：' + remove_noise(subtitle))
        author = re.findall(u'<span class=\"t1\" id=\"author\" dd_name=\"\u4f5c\u8005\".*?</span>',self._html,re.S)[0]
        print(u'作者：' + remove_noise(author))
        press = re.findall(u'<span class=\"t1\" dd_name=\"\u51fa\u7248\u793e\".*?</span>',self._html,re.S)[0]
        print(u'出版社：' + remove_noise(press))
        presstime = re.findall(u'<span class=\"t1\">\u51fa\u7248\u65f6\u95f4.*?</span>',self._html,re.S)[0]
        print(u'出版时间：' + remove_noise(presstime))
        page = re.findall(u'<li>\u9875 \u6570.*?</li>',self._html,re.S)[0]
        print(u'页数：' + remove_noise(page))
        word = re.findall(u'<li>\u5b57 \u6570.*?</li>',self._html,re.S)[0]
        print(u'字数：' + remove_noise(word))
        size = re.findall(u'<li>\u5f00 \u672c.*?</li>',self._html,re.S)[0]
        print(u'开本：' + remove_noise(size))
        material = re.findall(u'<li>\u7eb8 \u5f20.*?</li>',self._html,re.S)[0]
        print(u'纸张：' + remove_noise(material))
        pack = re.findall(u'<li>\u5305 \u88c5.*?</li>',self._html,re.S)[0]
        print(u'包装：' + remove_noise(pack))
        isbn = re.findall(u'<li>\u56fd\u9645\u6807\u51c6\u4e66\u53f7.*?</li>',self._html,re.S)[0]
        print(u'国际标准书号ISBN：' + remove_noise(isbn))
        classification = re.findall(u'<li class=\"clearfix fenlei\" dd_name=\"\u8be6\u60c5\u6240\u5c5e\u5206\u7c7b\".*?>.*?</li>',self._html,re.S)[0]
        print(u'所属分类：' + remove_noise(classification))
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


def spiderStart(urllist):
    for url in urllist:
        spider = Spider(url)
        spider.searchPicture()
        spider.searchAttr()



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
            spiderStart(url)

    print("\nFinished.")
    return True



main()