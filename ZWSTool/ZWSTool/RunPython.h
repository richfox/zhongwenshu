
// RunPython.h : 头文件
//

#pragma once
#include "afxwin.h"

#ifdef _DEBUG
   #undef _DEBUG
   #include "python.h"
   #define _DEBUG
#else
   #include "python.h"
#endif



namespace ZWST
{
   class RunPython
   {
   public:
      RunPython();
      ~RunPython();

      void run_generate_xml();
      void run_spider();

   private:
      static PyObject* _spider;
   };
}