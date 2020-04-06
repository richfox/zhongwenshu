#-*-coding:utf-8-*-
#＝＝＝＝＝＝表单大师接口＝＝＝＝＝＝＝＝
#Python 3.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de


import requests
import json


def get_jsform_data():
    url = 'http://api.jsform.com/api/v1/entry/query'
    payload = {'form_id':'5ad0974bbb7c7c5a08bf399a','fields':['field1','field5','field6','id'],'order_by':{'id':1}}
    headers = {'content-type':'application/json', 'Accept-Charset':'UTF-8'}
    r = requests.get(url, data=payload, headers=headers,auth=('58d0ec65bb7c7c744549ddf2','brSRwAMv7LtAQRPQ0sC62RLCsUnsy1S3'))
    r.json()