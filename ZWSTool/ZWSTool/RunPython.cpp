
// RunPython.cpp : 定义应用程序的类行为。
//

#include "stdafx.h"
#include "RunPython.h"




using namespace std;
using namespace ZWST;


PyObject* RunPython::_pymodule = nullptr;

RunPython::RunPython()
{
   Py_Initialize();

   if (Py_IsInitialized())
   {
      PyRun_SimpleString("import os, sys\n"
                        "sys.path.append(os.getcwd())\n"
                        "sys.path.append(os.path.dirname(os.getcwd()))\n"
                        "sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))\n"
                        "sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd()))))\n");

      _pymodule = PyImport_ImportModule("Spider");
   }
}

RunPython::~RunPython()
{
   Py_Finalize();
}


void RunPython::runGenerateXml()
{
   PyObject* pyfunc = PyObject_GetAttrString(_pymodule,"generateDefaultConfig");
   PyEval_CallObject(pyfunc,0);
}


void RunPython::runSpider()
{}