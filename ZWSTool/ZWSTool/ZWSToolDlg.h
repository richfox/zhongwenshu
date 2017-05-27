
// ZWSToolDlg.h : 头文件
//

#pragma once
#include "afxwin.h"
#include <string>
#include <memory>
#include "RunPython.h"



namespace ZWST
{
   enum URL
   {
      Url_Undefined,
      Url_Dangdang,
      Url_Ravensburger
   };

   // CZWSToolDlg 对话框
   class CZWSToolDlg : public CDHtmlDialog
   {
   // 构造
   public:
	   CZWSToolDlg(CWnd* pParent = NULL);	// 标准构造函数

   // 对话框数据
	   enum { IDD = IDD_ZWSTOOL_DIALOG, IDH = IDR_HTML_ZWSTOOL_DIALOG };

	   protected:
	   virtual void DoDataExchange(CDataExchange* pDX);	// DDX/DDV 支持

	   HRESULT OnButtonOK(IHTMLElement *pElement);
	   HRESULT OnButtonCancel(IHTMLElement *pElement);

   // 实现
   protected:
	   HICON m_hIcon;

	   // 生成的消息映射函数
	   virtual BOOL OnInitDialog();
	   afx_msg void OnSysCommand(UINT nID, LPARAM lParam);
	   afx_msg void OnPaint();
	   afx_msg HCURSOR OnQueryDragIcon();
	   DECLARE_MESSAGE_MAP()
	   DECLARE_DHTML_EVENT_MAP()
   public:
      afx_msg void OnBnClickedButtonSpider();
   protected:
      CEdit _editID;
      CButton _btnSpider;

      std::unique_ptr<RunPython> _python;
      CComboBox _comboUrl;
      CButton _btnDefault;
   public:
      afx_msg void OnBnClickedButtonDefault();
   protected:
      CEdit _editTitle;
   };
}