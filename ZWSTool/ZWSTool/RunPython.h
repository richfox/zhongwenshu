
// RunPython.h : 头文件
//

#pragma once
#include "afxwin.h"
#include <string>
#include <vector>

#ifdef _DEBUG
   #undef _DEBUG
   #include "python.h"
   #define _DEBUG
#else
   #include "python.h"
#endif



namespace ZWST
{
   struct DangdangBook
   {
      std::string title;
      std::string page;
   };

   typedef std::vector<DangdangBook> DangdangBooks;

   class RunPython
   {
   public:
      RunPython();
      ~RunPython();

      void runGenerateXml();
      DangdangBooks runSpider(const char* url,const char* id);

   private:
      static PyObject* _pymodule;
   };
}