#-*-coding:utf-8-*-
#＝＝＝＝＝＝图像处理＝＝＝＝＝＝＝＝
#Python 2.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de


import io
import PIL.Image
import requests
import utility
import ftplib


class Processor:
    def __init__(self,url):
        self._loaded = False
        if url:
            bytes = utility.get_html_byte(url)
            self._image = PIL.Image.open(io.BytesIO(bytes))
            self._loaded = True

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
        self._image.thumbnail((width,height),PIL.Image.ANTIALIAS)

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