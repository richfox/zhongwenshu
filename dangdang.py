#-*-coding:utf-8-*-
#＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝网页爬取图片＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
#Python 2.7

import sys
import os
import Spider




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
    
    if Spider.matchGenerateConfigFile(sys.argv[1]):
        Spider.generateDefaultConfig()
        return True
    elif Spider.matchConfigFile(sys.argv[1]):
        if not os.path.exists(sys.argv[1]):
            print('Error: config file does not exist.')
            return False
        else:
            url = Spider.parseConfigFile(sys.argv[1])
            Spider.spiderStart(url)

    print("\nFinished.")
    return True



main()