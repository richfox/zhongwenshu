#-*-coding:utf-8-*-
#＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝网页爬取图片＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
#Python 2.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de

import sys
import os
import Spider
import Visitor
import SQLimport



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
    print('python ${THIS_SCRIPT_NAME}.py ${configFile.xml}    Uses all settings of the xml configuration file')
    print("")
    print('python ${THIS_SCRIPT_NAME}.py ${file.html}    visit the html file')
    print("")
    print('python ${THIS_SCRIPT_NAME}.py {url,id}    Generates a special configuration file, then use it')
    print("")
    print('python ${THIS_SCRIPT_NAME}.py ${file.sxml}    import to database with settings of the xml file')
    print("")


def main():
    numArgs = 0
    for arg in sys.argv:
        numArgs += 1

    if numArgs == 1:
        print("Error: Required arguments not passed.")
    elif numArgs == 2:
        if Spider.matchGenerateConfigFile(sys.argv[1]):
            Spider.generateDefaultConfig()
            return True
        elif Spider.matchGenerateOrderConfigFile(sys.argv[1]):
            Spider.generateDefaultOrderConfig()
            return True
        elif Spider.matchGenerateSqlConigFile(sys.argv[1]):
            Spider.generateDefaultSqlConfig()
            return True
        elif Spider.matchConfigFile(sys.argv[1]):
            if not os.path.exists(sys.argv[1]):
                print('Error: config file does not exist.')
                return False
            else:
                urls = Spider.parseConfigFile(sys.argv[1])
                Spider.spiderStart(urls)
                return True
        elif Spider.matchOrderHtmlFile(sys.argv[1]):
            if not os.path.exists(sys.argv[1]):
                print('Error: config file does not exist.')
                return False
            else:
                Visitor.visitorStart(sys.argv[1])
                return True
        elif Spider.matSqlFile(sys.argv[1]):
            if not os.path.exists(sys.argv[1]):
                print('Error: sql config file does not exist.')
                return False
            else:
                sqls = Spider.parseSqlConfigFile(sys.argv[1])
                SQLimport.SQLimport(sqls)
                return True
    elif numArgs == 3:
        if Spider.matchUrl(sys.argv[1]):
            Spider.generateConfig(sys.argv[1],sys.argv[2])
            urls = Spider.parseConfigFile("dangdangConfig.xml")
            Spider.spiderStart(urls)
            return True

    printUsage()
    return False



main()