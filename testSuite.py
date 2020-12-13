#-*-coding:utf-8-*-
# Configuring logger
#Python 3.7
#Author: Xiang Fu
#Email: tech@zhongwenshu.de

import sys
import os
import unittest
import Visitor
import logis


def run():
    suite = unittest.TestSuite()

    tests = [Visitor.TestVisitor("testSearchOrderGoods"),
             Visitor.TestVisitor("testSearchOrderGoodsTuan"),
             logis.TestLogis("testSplitter"),
             logis.TestLogis("testGenerateLogisExpr")]

    suite.addTests(tests)

    #verbosity默认是 1，如果设为 0，则不输出每一用例的执行结果，如果设为 2，则输出详细的执行结果
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)