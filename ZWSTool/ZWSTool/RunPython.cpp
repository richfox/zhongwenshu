
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


DangdangBooks RunPython::runSpider(const char* url,const char* id)
{
   PyObject* pyfunc = PyObject_GetAttrString(_pymodule,"generateConfig");
   PyObject* pyargs = PyTuple_New(2);
   PyTuple_SetItem(pyargs,0,Py_BuildValue("s",url));
   PyTuple_SetItem(pyargs,1,Py_BuildValue("s",id));
   PyEval_CallObject(pyfunc,pyargs);

   pyfunc = PyObject_GetAttrString(_pymodule,"parseConfigFile");
   pyargs = PyTuple_New(1);
   PyTuple_SetItem(pyargs,0,Py_BuildValue("s","dangdangConfig.xml"));
   PyObject* pyres = PyEval_CallObject(pyfunc,pyargs);

   DangdangBooks books;
   for (int i=0; i<PyList_Size(pyres); i++)
   {
      PyObject* vollurl = PyList_GetItem(pyres,i);
      PyObject* pyclass = PyObject_GetAttrString(_pymodule,"Spider");
      pyargs = PyTuple_New(1);
      PyTuple_SetItem(pyargs,0,Py_BuildValue("s",PyString_AsString(vollurl)));
      PyObject* pyinstance = PyInstance_New(pyclass,pyargs,0);
      PyObject* callres = PyObject_CallMethod(pyinstance,"searchPicture",0,0);
      callres = PyObject_CallMethod(pyinstance,"searchAttr",0,0);
      callres = PyObject_CallMethod(pyinstance,"getHtml",0,0);
      const char* html = PyUnicode_AS_DATA(callres);

      DangdangBook book;
      callres = PyObject_CallMethod(pyinstance,"getTitle",0,0);
      book.title = PyUnicode_AS_DATA(callres);
      callres = PyObject_CallMethod(pyinstance,"getPage",0,0);
      book.page = PyUnicode_AS_DATA(callres);
      books.push_back(book);
   }

   return books;
}