#-*-coding:utf-8-*-
# Configuring logger
#Python 3.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de

import sys
import os
import unittest
import Visitor


def run():
    suite = unittest.TestSuite()

    tests = [Visitor.TestVisitor("testSearchOrderGoods")            
            ]

    suite.addTests(tests)

    runner = unittest.TextTestRunner()
    runner.run(suite)