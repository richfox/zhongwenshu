#-*-coding:utf-8-*-
#＝＝＝＝＝＝图像处理＝＝＝＝＝＝＝＝
#Python 2.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de


import io
import PIL.Image
import requests



class ImgProcessor:
    def __init__(self,url):
        res = requests.get(url)
        self._image = PIL.Image.open(io.BytesIO(res.content))

    def Show(self):
        self._image.show()

    def Save(self,path,ext):
        self._image.save(path,ext)

    def Thumb(self,x,y):
        self._image.thumbnail((x,y))

    def Size(self):
        return self._image.size

    def Format(self):
        return self._image.format