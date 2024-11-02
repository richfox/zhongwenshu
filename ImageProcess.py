#-*-coding:utf-8-*-
#＝＝＝＝＝＝图像处理＝＝＝＝＝＝＝＝
#Python 3.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de


import io
import PIL.Image
import requests
import utility
import ftplib
import sys
import proxy


class Processor:
    def __init__(self,url):
        self._loaded = False
        if url:
            try:
                res = requests.get(url,timeout=6,headers=proxy.get_http_headers())
                if res.ok:
                    self._image = PIL.Image.open(io.BytesIO(res.content))
                    self._loaded = True
            except:
                print("unexpected error: {0} {1} {2}".format(sys.exc_info()[0],url,"fetch failed!"))
            else:
                print(url + " fetched successfully!")

    def Loaded(self):
        return self._loaded

    def Show(self):
        self._image.show()

    def Save(self,path,name,ext):
        target = path + "/" + name + "." + ext
        self._image.save(target)
        return target

    def Upload(self,conn,source,path,name,ext):
        file = open(source,"rb")
        target = path + "/" + name + "." + ext
        conn.storbinary("STOR " + target,file)
        file.close()
        return target

    def Thumb(self,width,height):
        self._image.thumbnail((width,height),PIL.Image.Resampling.LANCZOS)

    def Width(self):
        return self._image.size[0]

    def Height(self):
        return self._image.size[1]

    def Format(self):
        return self._image.format

    def Mode(self):
        return self._image.mode

    def Info(self):
        return self._image.Info