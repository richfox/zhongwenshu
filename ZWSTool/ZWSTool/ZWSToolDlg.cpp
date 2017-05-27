
// ZWSToolDlg.cpp : 实现文件
//

#include "stdafx.h"
#include "ZWSTool.h"
#include "ZWSToolDlg.h"
#include "afxdialogex.h"


#ifdef _DEBUG
#define new DEBUG_NEW
#endif

using namespace std;
using namespace ZWST;


// 用于应用程序“关于”菜单项的 CAboutDlg 对话框

class CAboutDlg : public CDialogEx
{
public:
	CAboutDlg();

// 对话框数据
	enum { IDD = IDD_ABOUTBOX };

	protected:
	virtual void DoDataExchange(CDataExchange* pDX);    // DDX/DDV 支持

// 实现
protected:
	DECLARE_MESSAGE_MAP()
};

CAboutDlg::CAboutDlg() : CDialogEx(CAboutDlg::IDD)
{
}

void CAboutDlg::DoDataExchange(CDataExchange* pDX)
{
	CDialogEx::DoDataExchange(pDX);
}

BEGIN_MESSAGE_MAP(CAboutDlg, CDialogEx)
END_MESSAGE_MAP()


// CZWSToolDlg 对话框

BEGIN_DHTML_EVENT_MAP(CZWSToolDlg)
	DHTML_EVENT_ONCLICK(_T("ButtonOK"), OnButtonOK)
	DHTML_EVENT_ONCLICK(_T("ButtonCancel"), OnButtonCancel)
END_DHTML_EVENT_MAP()


CZWSToolDlg::CZWSToolDlg(CWnd* pParent /*=NULL*/)
	: CDHtmlDialog(CZWSToolDlg::IDD, CZWSToolDlg::IDH, pParent),
    _python(new RunPython)
{
	m_hIcon = AfxGetApp()->LoadIcon(IDR_MAINFRAME);
}

void CZWSToolDlg::DoDataExchange(CDataExchange* pDX)
{
   CDHtmlDialog::DoDataExchange(pDX);
   DDX_Control(pDX, IDC_EDIT_PRODUCTID, _editID);
   DDX_Control(pDX, IDC_BUTTON_SPIDER, _btnSpider);
   DDX_Control(pDX, IDC_COMBO_URL, _comboUrl);
   DDX_Control(pDX, IDC_BUTTON_DEFAULT, _btnDefault);
   DDX_Control(pDX, IDC_EDIT1, _editTitle);
}

BEGIN_MESSAGE_MAP(CZWSToolDlg, CDHtmlDialog)
	ON_WM_SYSCOMMAND()
    ON_BN_CLICKED(IDC_BUTTON_SPIDER, &CZWSToolDlg::OnBnClickedButtonSpider)
    ON_BN_CLICKED(IDC_BUTTON_DEFAULT, &CZWSToolDlg::OnBnClickedButtonDefault)
END_MESSAGE_MAP()


// CZWSToolDlg 消息处理程序

BOOL CZWSToolDlg::OnInitDialog()
{
	CDHtmlDialog::OnInitDialog();

	// 将“关于...”菜单项添加到系统菜单中。

	// IDM_ABOUTBOX 必须在系统命令范围内。
	ASSERT((IDM_ABOUTBOX & 0xFFF0) == IDM_ABOUTBOX);
	ASSERT(IDM_ABOUTBOX < 0xF000);

	CMenu* pSysMenu = GetSystemMenu(FALSE);
	if (pSysMenu != NULL)
	{
		BOOL bNameValid;
		CString strAboutMenu;
		bNameValid = strAboutMenu.LoadString(IDS_ABOUTBOX);
		ASSERT(bNameValid);
		if (!strAboutMenu.IsEmpty())
		{
			pSysMenu->AppendMenu(MF_SEPARATOR);
			pSysMenu->AppendMenu(MF_STRING, IDM_ABOUTBOX, strAboutMenu);
		}
	}

	// 设置此对话框的图标。当应用程序主窗口不是对话框时，框架将自动
	//  执行此操作
	SetIcon(m_hIcon, TRUE);			// 设置大图标
	SetIcon(m_hIcon, FALSE);		// 设置小图标

	// TODO: 在此添加额外的初始化代码
    _comboUrl.AddString(L"product.dangdang.com");
    _comboUrl.SetItemData(0,Url_Dangdang);
    _comboUrl.SetCurSel(-1);

	return TRUE;  // 除非将焦点设置到控件，否则返回 TRUE
}

void CZWSToolDlg::OnSysCommand(UINT nID, LPARAM lParam)
{
	if ((nID & 0xFFF0) == IDM_ABOUTBOX)
	{
		CAboutDlg dlgAbout;
		dlgAbout.DoModal();
	}
	else
	{
		CDHtmlDialog::OnSysCommand(nID, lParam);
	}
}

// 如果向对话框添加最小化按钮，则需要下面的代码
//  来绘制该图标。对于使用文档/视图模型的 MFC 应用程序，
//  这将由框架自动完成。

void CZWSToolDlg::OnPaint()
{
	if (IsIconic())
	{
		CPaintDC dc(this); // 用于绘制的设备上下文

		SendMessage(WM_ICONERASEBKGND, reinterpret_cast<WPARAM>(dc.GetSafeHdc()), 0);

		// 使图标在工作区矩形中居中
		int cxIcon = GetSystemMetrics(SM_CXICON);
		int cyIcon = GetSystemMetrics(SM_CYICON);
		CRect rect;
		GetClientRect(&rect);
		int x = (rect.Width() - cxIcon + 1) / 2;
		int y = (rect.Height() - cyIcon + 1) / 2;

		// 绘制图标
		dc.DrawIcon(x, y, m_hIcon);
	}
	else
	{
		CDHtmlDialog::OnPaint();
	}
}

//当用户拖动最小化窗口时系统调用此函数取得光标
//显示。
HCURSOR CZWSToolDlg::OnQueryDragIcon()
{
	return static_cast<HCURSOR>(m_hIcon);
}

HRESULT CZWSToolDlg::OnButtonOK(IHTMLElement* /*pElement*/)
{
	OnOK();
	return S_OK;
}

HRESULT CZWSToolDlg::OnButtonCancel(IHTMLElement* /*pElement*/)
{
	OnCancel();
	return S_OK;
}


void CZWSToolDlg::OnBnClickedButtonSpider()
{
   CString url,id;
   _comboUrl.GetWindowText(url);
   _editID.GetWindowText(id);
   const auto& books = _python->runSpider(CW2A(url.Trim()).m_szBuffer,CW2A(id.Trim()).m_szBuffer);

   for (const auto& book : books)
   {
      CStringA title = book.title.c_str();
      _editTitle.SetWindowText(CA2W(title));
   }
}


void ZWST::CZWSToolDlg::OnBnClickedButtonDefault()
{
   _python->runGenerateXml();

   for (int i=0; i<_comboUrl.GetCount(); i++)
   {
      if (_comboUrl.GetItemData(i) == Url_Dangdang)
      {
         _comboUrl.SetCurSel(i);
         break;
      }
   }

   _editID.SetWindowText(L"20771643");
}
