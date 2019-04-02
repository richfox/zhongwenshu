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
    for ckey,cvalue in cparams:
        hreq += "&" + ckey + "=" + cvalue
    for bkey,bvalue in bparams:
        hreq += "&" + bkey + "=" + bvalue
    hreq += "&appSign=" + sign
    return hreq



def get_sign(params,secret):
    sign = ""
    if params:
        sign = secret
        for key in sorted(params.keys()):
            if params[key]:
                sign += key + params[key]
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
    return respond