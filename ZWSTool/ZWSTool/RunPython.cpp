
// RunPython.cpp : 定义应用程序的类行为。
//

#include "stdafx.h"
#include "RunPython.h"




using namespace std;
using namespace ZWST;


PyObject* RunPython::_spider = nullptr;

RunPython::RunPython()
{
   Py_Initialize();

   if (Py_IsInitialized())
   {
      PyRun_SimpleString("import os, sys\n"
                        "sys.path.append(os.getcwd())\n"
                        "sys.path.append(os.path.dirname(os.getcwd()))\n"
                        "sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))\n");

      _spider = PyImport_ImportModule("Spider");
   }
}

RunPython::~RunPython()
{
   Py_Finalize();
}


void RunPython::run_generate_xml()
{
   PyObject* pyfunc = PyObject_GetAttrString(_spider,"generateDefaultConfig");
   PyEval_CallObject(pyfunc,0);
}


void RunPython::run_spider()
{}