#-*-coding:utf-8-*-
# 文轩网接口
#Python 2.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de

import sys
import os
import hashlib
import json
import time



def get_authorization():
    res = {}
    jsonstring = open(".\\Globconfig.json",'r').read()
    allinfo = json.loads(jsonstring)
    for config in allinfo["configurations"]:
        if config.has_key("winxuan"):
            for wx in config["winxuan"]:
                res[wx["type"]] = (wx["address"],wx["key"],wx["secret"],wx["accesstoken"],wx["version"],wx["format"])
            break
    return res


def build_http_request(httpaddress,cparams,bparams,sign):
    hreq = httpaddress + "?"
    for ckey,cvalue in cparams.items():
        hreq += "&" + ckey + "=" + cvalue
    for bkey,bvalue in bparams.items():
        hreq += "&" + bkey + "=" + bvalue
    hreq += "&appSign=" + sign
    return hreq



def get_sign(cparams,bparams,secret):
    sign = ""
    if cparams or bparams:
        sign = secret
        allparams = cparams
        for bkey,bvalue in bparams.items():
            allparams[bkey] = bvalue
        for key,value in sorted(allparams.items()):
            if value:
                sign += key + value
        sign += secret
        return HEXSHA1(sign)
    return sign



def HEXSHA1(source):
    return hashlib.sha1(source.encode("utf-8")).hexdigest().upper()

def SHA1(source):
    barray = bytearray(hashlib.sha1(source.encode("utf-8")).digest())
    return byte2hex(barray)


def byte2hex(barray):
    sign = ""
    for b in barray:
        bhex = hex(b & 0xFF)
        if len(bhex) == 1:
            sign += "0"
        sign += bhex.upper()
    return sign


def get_shop_items():
    respond = ""
    
    (address,key,secret,accesstoken,version,format) = get_authorization()["sandbox"]
    method = "winxuan.shop.items.get"
    timestamp = str(int(time.time()*1000))

    #公共参数
    cparams = {"timeStamp":timestamp,
               "method":method,
               "v":version,
               "format":format,
               "appKey":key,
               "accessToken":accesstoken}

    #业务参数
    bparams = {"itemIds":"10000349"}

    #生成签名
    sign = get_sign(cparams,bparams,secret)

    #组装HTTP请求
    hreq = build_http_request(address,cparams,bparams,sign)

    return respond