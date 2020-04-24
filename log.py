#-*-coding:utf-8-*-
# Configuring logger
#Python 3.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de

import sys
import os
import utility
import logging



class Logger:
    def __init__(self,logfile):
        self._logger = logging.getLogger('zws')
        self._logger.setLevel(logging.DEBUG)
        handle = logging.FileHandler(logfile)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handle.setFormatter(formatter)
        self._logger.addHandler(handle)

    def getLogger(self):
        return self._logger

    def logInfo(self,message):
        self._logger.info(message)