#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxmatrix.py
#
# Description: wxPython Matrix
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is	Gilles Dumortier.
#
# Portions created by the Initial Developer are Copyright (C) 2004-2006 the
# Initial Developer. All Rights Reserved.
#
# Contributor(s):
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; see http://www.gnu.org/licenses/gpl.html
#
# History       Rev   Description
# 2006-01-2x    dgil  Wrote it from itrade_wxmain.py module
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging

# wxPython system
import itrade_wxversion
from wxPython.wx import *
from wxPython.lib.mixins.listctrl import wxColumnSorterMixin, wxListCtrlAutoWidthMixin
#from wxPython.lib.throbber import Throbber

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_local import message
from itrade_portfolio import loadPortfolio
from itrade_matrix import *
from itrade_quotes import *
from itrade_import import getLiveConnector
from itrade_currency import currencies

# iTrade wx system
from itrade_wxquote import open_iTradeQuote,addInMatrix_iTradeQuote,removeFromMatrix_iTradeQuote
from itrade_wxportfolio import select_iTradePortfolio,properties_iTradePortfolio
from itrade_wxoperations import open_iTradeOperations
from itrade_wxmoney import open_iTradeMoney
from itrade_wxalerts import open_iTradeAlerts
from itrade_wxcurrency import open_iTradeCurrencies
from itrade_wxabout import iTradeAboutBox
from itrade_wxhtml import iTradeHtmlWindow,iTradeLaunchBrowser
from itrade_wxutil import wxFontFromSize

from itrade_wxmixin import iTrade_wxFrame
from itrade_wxlive import iTrade_wxLiveMixin,EVT_UPDATE_LIVE

# ============================================================================
# menu identifier
# ============================================================================

ID_OPEN = 100
ID_NEW = 101
ID_DELETE = 102
ID_SAVE = 103
ID_SAVEAS = 104
ID_EDIT = 105

ID_MANAGELIST = 110

ID_EXIT = 150

ID_PORTFOLIO = 200
ID_QUOTES = 201
ID_STOPS = 202
ID_INDICATORS = 203

ID_OPERATIONS = 210
ID_MONEY = 211
ID_CURRENCIES = 212
ID_ALERTS = 213

ID_COMPUTE = 221

ID_SMALL_VIEW = 230
ID_NORMAL_VIEW = 231
ID_BIG_VIEW = 232

ID_REFRESH = 240
ID_AUTOREFRESH = 241

ID_ADD_QUOTE = 300
ID_REMOVE_QUOTE = 301
ID_GRAPH_QUOTE = 310
ID_LIVE_QUOTE = 311
#ID_INTRADAY_QUOTE = 312
#ID_NEWS_QUOTE = 313
#ID_TABLE_QUOTE = 314
#ID_ANALYSIS_QUOTE = 315
#ID_BUY_QUOTE = 320
#ID_SELL_QUOTE = 321
ID_PROPERTY_QUOTE = 330

ID_CONTENT = 500
ID_SUPPORT = 501
ID_BUG = 502
ID_DONORS = 503
ID_ABOUT = 510

# ============================================================================
# view mode
# ============================================================================

LISTMODE_INIT = 0
LISTMODE_QUOTES = 1
LISTMODE_PORTFOLIO = 2
LISTMODE_STOPS = 3
LISTMODE_INDICATORS = 4

# ============================================================================
# column number
# ============================================================================

# (common) view
IDC_ISIN = 0
IDC_TICKER = 1
IDC_PERCENT = 9
IDC_NAME = 10

# Portfolio view
IDC_QTY = 2
IDC_PRU = 3
IDC_PR  = 4
IDC_PVU = 5
IDC_PERFDAY = 6
IDC_PV  = 7
IDC_PROFIT = 8
#IDC_PERCENT = 9
#IDC_NAME = 10

# trade view
IDC_VOLUME = 2
IDC_PREV = 3
IDC_OPEN = 4
IDC_HIGH = 5
IDC_LOW = 6
IDC_CLOSE = 7
IDC_PIVOTS = 8
#IDC_PERCENT = 9
#IDC_NAME = 10

# stops view
IDC_INVEST = 2
IDC_RISKM = 3
IDC_STOPLOSS = 4
IDC_CURRENT = 5
IDC_STOPWIN = 6
#IDC_PV  = 7
#IDC_PROFIT = 8
#IDC_PERCENT = 9
#IDC_NAME = 10

# indicators view
IDC_MA20 = 2
IDC_MA50 = 3
IDC_MA100 = 4
IDC_RSI = 5
IDC_MACD = 6
IDC_STOCH = 7
IDC_DMI = 8
IDC_EMV = 9
IDC_OVB = 10
IDC_LAST = 11

# ============================================================================
# iTradeMatrixListCtrl
# ============================================================================

class iTradeMatrixListCtrl(wxListCtrl, wxListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wxDefaultPosition,
                 size=wxDefaultSize, style=0):
        wxListCtrl.__init__(self, parent, ID, pos, size, style)
        wxListCtrlAutoWidthMixin.__init__(self)

# ============================================================================
# iTradeMainToolbar
#
# ============================================================================

cCONNECTED = wxColour(51,255,51)
cDISCONNECTED = wxColour(255,51,51)

class iTradeMainToolbar(wxToolBar):

    def __init__(self,parent,id):
        wxToolBar.__init__(self,parent,id,style = wxTB_HORIZONTAL | wxNO_BORDER | wxTB_FLAT)
        self.m_parent = parent
        self._init_toolbar()

    def _init_toolbar(self):
        self._NTB2_EXIT = wxNewId()
        self._NTB2_NEW = wxNewId()
        self._NTB2_OPEN = wxNewId()
        self._NTB2_EDIT = wxNewId()
        self._NTB2_SAVE = wxNewId()
        self._NTB2_SAVE_AS = wxNewId()
        self._NTB2_MONEY = wxNewId()
        self._NTB2_OPERATIONS = wxNewId()
        self._NTB2_ALERTS = wxNewId()
        self._NTB2_QUOTE = wxNewId()
        self._NTB2_REFRESH = wxNewId()
        self._NTB2_ABOUT = wxNewId()

        self.SetToolBitmapSize(wxSize(24,24))
        self.AddSimpleTool(self._NTB2_EXIT, wxArtProvider.GetBitmap(wxART_CROSS_MARK, wxART_TOOLBAR),
                           message('main_exit'), message('main_desc_exit'))
        self.AddControl(wxStaticLine(self, -1, size=(-1,23), style=wxLI_VERTICAL))
        self.AddSimpleTool(self._NTB2_NEW, wxArtProvider.GetBitmap(wxART_NEW, wxART_TOOLBAR),
                           message('main_new'), message('main_desc_new'))
        self.AddSimpleTool(self._NTB2_OPEN, wxArtProvider.GetBitmap(wxART_FILE_OPEN, wxART_TOOLBAR),
                           message('main_open'), message('main_desc_open'))
        self.AddSimpleTool(self._NTB2_EDIT, wxArtProvider.GetBitmap(wxART_EXECUTABLE_FILE, wxART_TOOLBAR),
                           message('main_edit'), message('main_desc_edit'))
        self.AddSimpleTool(self._NTB2_SAVE, wxArtProvider.GetBitmap(wxART_FILE_SAVE, wxART_TOOLBAR),
                           message('main_save'), message('main_desc_save'))
        self.AddControl(wxStaticLine(self, -1, size=(-1,23), style=wxLI_VERTICAL))
        self.AddSimpleTool(self._NTB2_OPERATIONS, wxArtProvider.GetBitmap(wxART_REPORT_VIEW, wxART_TOOLBAR),
                           message('main_view_operations'), message('main_view_desc_operations'))
        self.AddSimpleTool(self._NTB2_MONEY, wxBitmap('res/money.gif'),
                           message('main_view_money'), message('main_view_desc_money'))
        self.AddSimpleTool(self._NTB2_ALERTS, wxBitmap('res/bell.gif'),
                           message('main_view_alerts'), message('main_view_desc_alerts'))
        self.AddControl(wxStaticLine(self, -1, size=(-1,23), style=wxLI_VERTICAL))
        self.AddSimpleTool(self._NTB2_QUOTE, wxBitmap('res/graph.gif'),
                           message('main_view_current'), message('main_view_desc_current'))
        self.AddControl(wxStaticLine(self, -1, size=(-1,23), style=wxLI_VERTICAL))
        self.AddSimpleTool(self._NTB2_REFRESH, wxBitmap('res/refresh.png'),
                           message('main_view_refresh'), message('main_view_desc_refresh'))
        self.AddSimpleTool(self._NTB2_ABOUT, wxBitmap('res/about.gif'),
                           message('main_about'), message('main_desc_about'))
        self.AddControl(wxStaticLine(self, -1, size=(-1,23), style=wxLI_VERTICAL))
        self.m_indicator = wxStaticText(self, -1, "::", size=(180,15), style=wxALIGN_RIGHT|wxST_NO_AUTORESIZE)
        self.AddControl(self.m_indicator)

        EVT_TOOL(self, self._NTB2_EXIT, self.onExit)
        EVT_TOOL(self, self._NTB2_NEW, self.onNew)
        EVT_TOOL(self, self._NTB2_OPEN, self.onOpen)
        EVT_TOOL(self, self._NTB2_EDIT, self.onEdit)
        EVT_TOOL(self, self._NTB2_SAVE, self.onSave)
        EVT_TOOL(self, self._NTB2_OPERATIONS, self.onOperations)
        EVT_TOOL(self, self._NTB2_MONEY, self.onMoney)
        EVT_TOOL(self, self._NTB2_ALERTS, self.onAlerts)
        EVT_TOOL(self, self._NTB2_QUOTE, self.onQuote)
        EVT_TOOL(self, self._NTB2_ABOUT, self.onAbout)
        EVT_TOOL(self, self._NTB2_REFRESH, self.onRefresh)
        self.Realize()

    def onRefresh(self, event):
        self.m_parent.OnRefresh(event)

    def onOpen(self,event):
        self.m_parent.OnOpen(event)

    def onNew(self,event):
        self.m_parent.OnNew(event)

    def onEdit(self,event):
        self.m_parent.OnEdit(event)

    def onSave(self,event):
        self.m_parent.OnSave(event)

    def onExit(self,event):
        self.m_parent.OnExit(event)

    def onOperations(self,event):
        self.m_parent.OnOperations(event)

    def onMoney(self,event):
        self.m_parent.OnMoney(event)

    def onCompute(self,event):
        self.m_parent.OnCompute(event)

    def onAlerts(self,event):
        self.m_parent.OnAlerts(event)

    def onQuote(self,event):
        self.m_parent.OnGraphQuote(event)

    def onAbout(self,event):
        self.m_parent.OnAbout(event)

    # ---[ Market Indicator management ] ---

    def SetIndicator(self,market,clock):
        if clock=="::":
            label = market + ": Disconnected"
            self.m_indicator.SetBackgroundColour(cDISCONNECTED)
        else:
            label = market + ": " + clock
            if label==self.m_indicator.GetLabel():
                self.m_indicator.SetBackgroundColour(wxNullColour)
            else:
                self.m_indicator.SetBackgroundColour(cCONNECTED)
        self.m_indicator.ClearBackground()
        self.m_indicator.SetLabel(label)

# ============================================================================
# iTradeMainWindow
#
# ============================================================================

import wx.lib.newevent
(PostInitEvent,EVT_POSTINIT) = wx.lib.newevent.NewEvent()

class iTradeMainWindow(wxFrame,iTrade_wxFrame,iTrade_wxLiveMixin, wxColumnSorterMixin):
    def __init__(self,parent,id,portfolio,matrix):
        self.m_id = wxNewId()
        wxFrame.__init__(self,parent,self.m_id, "", size = ( 640,480), style=wxDEFAULT_FRAME_STYLE|wxNO_FULL_REPAINT_ON_RESIZE)
        iTrade_wxFrame.__init__(self,parent, 'main')
        iTrade_wxLiveMixin.__init__(self)

        self.m_portfolio = portfolio
        self.m_matrix = matrix

        self.m_market = self.m_portfolio.market()
        self.m_connector = getLiveConnector(self.m_market)

        # link to other windows
        self.m_hOperation = None
        self.m_hMoney = None
        self.m_hAlerts = None
        self.m_hView = None
        self.m_hCurrency = None

        EVT_CLOSE(self, self.OnCloseWindow)
        EVT_WINDOW_DESTROY(self, self.OnDestroyWindow)

        # the main menu
        self.filemenu = wxMenu()
        self.filemenu.Append(ID_OPEN,message('main_open'),message('main_desc_open'))
        self.filemenu.Append(ID_NEW,message('main_new'),message('main_desc_new'))
        self.filemenu.Append(ID_SAVE,message('main_save'),message('main_desc_save'))
        self.filemenu.Append(ID_SAVEAS,message('main_saveas'),message('main_desc_saveas'))
        self.filemenu.Append(ID_DELETE,message('main_delete'),message('main_desc_delete'))
        self.filemenu.AppendSeparator()
        self.filemenu.Append(ID_EDIT,message('main_edit'),message('main_desc_edit'))
        self.filemenu.AppendSeparator()
        self.filemenu.Append(ID_MANAGELIST,message('main_managelist'),message('main_desc_managelist'))
        self.filemenu.AppendSeparator()
        self.filemenu.Append(ID_EXIT,message('main_exit'),message('main_desc_exit'))

        self.matrixmenu = wxMenu()
        self.matrixmenu.AppendRadioItem(ID_PORTFOLIO, message('main_view_portfolio'),message('main_view_desc_portfolio'))
        self.matrixmenu.AppendRadioItem(ID_QUOTES, message('main_view_quotes'),message('main_view_desc_quotes'))
        self.matrixmenu.AppendRadioItem(ID_STOPS, message('main_view_stops'),message('main_view_desc_stops'))
        self.matrixmenu.AppendRadioItem(ID_INDICATORS, message('main_view_indicators'),message('main_view_desc_indicators'))
        self.matrixmenu.AppendSeparator()
        self.matrixmenu.AppendRadioItem(ID_SMALL_VIEW, message('main_view_small'),message('main_view_desc_small'))
        self.matrixmenu.AppendRadioItem(ID_NORMAL_VIEW, message('main_view_normal'),message('main_view_desc_normal'))
        self.matrixmenu.AppendRadioItem(ID_BIG_VIEW, message('main_view_big'),message('main_view_desc_big'))
        self.matrixmenu.AppendSeparator()
        self.matrixmenu.Append(ID_REFRESH, message('main_view_refresh'),message('main_view_desc_refresh'))
        self.matrixmenu.AppendCheckItem(ID_AUTOREFRESH, message('main_view_autorefresh'),message('main_view_desc_autorefresh'))

        self.quotemenu = wxMenu()
        self.quotemenu.Append(ID_ADD_QUOTE, message('main_quote_add'),message('main_quote_desc_add'))
        self.quotemenu.Append(ID_REMOVE_QUOTE, message('main_quote_remove'),message('main_quote_desc_add'))
        self.quotemenu.AppendSeparator()
        self.quotemenu.Append(ID_GRAPH_QUOTE, message('main_quote_graph'),message('main_quote_desc_graph'))
        self.quotemenu.Append(ID_LIVE_QUOTE, message('main_quote_live'),message('main_quote_desc_live'))
        self.quotemenu.AppendSeparator()
        self.quotemenu.Append(ID_PROPERTY_QUOTE, message('main_quote_property'),message('main_quote_desc_property'))

        self.viewmenu = wxMenu()
        self.viewmenu.Append(ID_OPERATIONS, message('main_view_operations'),message('main_view_desc_operations'))
        self.viewmenu.Append(ID_MONEY, message('main_view_money'),message('main_view_desc_money'))
        self.viewmenu.AppendSeparator()
        self.viewmenu.Append(ID_CURRENCIES, message('main_view_currencies'),message('main_view_desc_currencies'))
        self.viewmenu.Append(ID_ALERTS, message('main_view_alerts'),message('main_view_desc_alerts'))
        self.viewmenu.AppendSeparator()
        self.viewmenu.Append(ID_COMPUTE, message('main_view_compute'),message('main_view_desc_compute'))

        self.helpmenu = wxMenu()
        self.helpmenu.Append(ID_CONTENT, message('main_help_contents'),message('main_help_desc_contents'))
        self.helpmenu.AppendSeparator()
        self.helpmenu.Append(ID_SUPPORT, message('main_help_support'),message('main_help_desc_support'))
        self.helpmenu.Append(ID_BUG, message('main_help_bugs'),message('main_help_desc_bugs'))
        self.helpmenu.Append(ID_DONORS, message('main_help_donors'),message('main_help_desc_donors'))
        self.helpmenu.AppendSeparator()
        self.helpmenu.Append(ID_ABOUT, message('main_about'), message('main_desc_about'))

        # Creating the menubar
        menuBar = wxMenuBar()

        # Adding the "filemenu" to the MenuBar
        menuBar.Append(self.filemenu,message('main_file'))
        menuBar.Append(self.matrixmenu,message('main_matrix'))
        menuBar.Append(self.viewmenu,message('main_view'))
        menuBar.Append(self.quotemenu,message('main_quote'))
        menuBar.Append(self.helpmenu,message('main_help'))

        # Adding the MenuBar to the Frame content
        self.SetMenuBar(menuBar)

        EVT_MENU(self, ID_OPEN, self.OnOpen)
        EVT_MENU(self, ID_NEW, self.OnNew)
        EVT_MENU(self, ID_DELETE, self.OnDelete)
        EVT_MENU(self, ID_SAVE, self.OnSave)
        EVT_MENU(self, ID_SAVEAS, self.OnSaveAs)
        EVT_MENU(self, ID_EDIT, self.OnEdit)
        EVT_MENU(self, ID_MANAGELIST, self.OnManageList)
        EVT_MENU(self, ID_EXIT, self.OnExit)
        EVT_MENU(self, ID_SUPPORT, self.OnSupport)
        EVT_MENU(self, ID_BUG, self.OnBug)
        EVT_MENU(self, ID_DONORS, self.OnDonors)
        EVT_MENU(self, ID_PORTFOLIO, self.OnPortfolio)
        EVT_MENU(self, ID_QUOTES, self.OnQuotes)
        EVT_MENU(self, ID_STOPS, self.OnStops)
        EVT_MENU(self, ID_INDICATORS, self.OnIndicators)
        EVT_MENU(self, ID_OPERATIONS, self.OnOperations)
        EVT_MENU(self, ID_MONEY, self.OnMoney)
        EVT_MENU(self, ID_COMPUTE, self.OnCompute)
        EVT_MENU(self, ID_ALERTS, self.OnAlerts)
        EVT_MENU(self, ID_CURRENCIES, self.OnCurrencies)

        EVT_MENU(self, ID_ADD_QUOTE, self.OnAddQuote)
        EVT_MENU(self, ID_REMOVE_QUOTE, self.OnRemoveCurrentQuote)
        EVT_MENU(self, ID_GRAPH_QUOTE, self.OnGraphQuote)
        EVT_MENU(self, ID_LIVE_QUOTE, self.OnLiveQuote)
        EVT_MENU(self, ID_PROPERTY_QUOTE, self.OnPropertyQuote)

        EVT_MENU(self, ID_SMALL_VIEW, self.OnViewSmall)
        EVT_MENU(self, ID_NORMAL_VIEW, self.OnViewNormal)
        EVT_MENU(self, ID_BIG_VIEW, self.OnViewBig)

        EVT_MENU(self, ID_REFRESH, self.OnRefresh)
        EVT_MENU(self, ID_AUTOREFRESH, self.OnAutoRefresh)
        EVT_MENU(self, ID_ABOUT, self.OnAbout)

        # create an image list
        self.m_imagelist = wxImageList(16,16)

        self.idx_nochange = self.m_imagelist.Add(wxBitmap('res/nochange.gif'))
        self.idx_up = self.m_imagelist.Add(wxBitmap('res/up.gif'))
        self.idx_down = self.m_imagelist.Add(wxBitmap('res/down.gif'))
        self.idx_tbref = self.m_imagelist.Add(wxBitmap('res/invalid.gif'))
        self.idx_buy = self.m_imagelist.Add(wxBitmap('res/buy.gif'))
        self.idx_sell = self.m_imagelist.Add(wxBitmap('res/sell.gif'))
        self.idx_noop = self.m_imagelist.Add(wxBitmap('res/noop.gif'))

        self.sm_up = self.m_imagelist.Add(wxBitmap('res/sm_up.gif'))
        self.sm_dn = self.m_imagelist.Add(wxBitmap('res/sm_down.gif'))

        # List
        tID = wxNewId()

        self.m_list = iTradeMatrixListCtrl(self, tID,
                                 style = wxLC_REPORT | wxSUNKEN_BORDER | wxLC_SINGLE_SEL | wxLC_VRULES | wxLC_HRULES)
        EVT_LIST_ITEM_ACTIVATED(self, tID, self.OnItemActivated)
        EVT_LIST_ITEM_SELECTED(self, tID, self.OnItemSelected)
        EVT_COMMAND_RIGHT_CLICK(self.m_list, tID, self.OnRightClick)
        EVT_RIGHT_UP(self.m_list, self.OnRightClick)
        EVT_RIGHT_DOWN(self.m_list, self.OnRightDown)
        EVT_LEFT_DOWN(self.m_list, self.OnLeftDown)

        self.m_list.SetImageList(self.m_imagelist, wxIMAGE_LIST_SMALL)
        self.m_list.SetFont(wxFontFromSize(itrade_config.matrixFontSize))

        # Now that the list exists we can init the other base class,
        # see wxPython/lib/mixins/listctrl.py
        wxColumnSorterMixin.__init__(self, IDC_LAST+1)

        # Toolbar
        self.m_toolbar = iTradeMainToolbar(self, wxNewId())

        # default list is quotes
        self.m_listmode = LISTMODE_INIT

        EVT_SIZE(self, self.OnSize)

        EVT_UPDATE_LIVE(self, self.OnLive)

        # refresh full view after window init finished
        EVT_POSTINIT(self, self.OnPostInit)
        wxPostEvent(self,PostInitEvent())

        self.Show(True)

    # --- [ wxColumnSorterMixin management ] -------------------------------------

    # Used by the wxColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.m_list

    # Used by the wxColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)

    # --- [ window management ] -------------------------------------

    def OnPostInit(self,event):
        self.m_listmode = LISTMODE_QUOTES
        self.populate(bDuringInit=True)
        self.updateTitle()
        self.updateCheckItems()
        self.OnRefresh(event)
        if itrade_config.bAutoRefreshMatrixView:
            self.startLive()

    def OnSize(self, event):
        debug('OnSize')
        w,h = self.GetClientSizeTuple()
        self.m_toolbar.SetDimensions(0, 0, w, 32)
        self.m_list.SetDimensions(0, 32, w, h-32)
        event.Skip(False)

    def CloseLinks(self):
        if self.m_hOperation:
            self.m_hOperation.Close()
        if self.m_hMoney:
            self.m_hMoney.Close()
        if self.m_hAlerts:
            self.m_hAlerts.Close()
        if self.m_hView:
            self.m_hView.Close()
        if self.m_hCurrency:
            self.m_hCurrency.Close()

    def OnExit(self,e):
        if self.manageDirty(message('main_save_matrix_data')):
            self.Close(True)

    def OnCloseWindow(self, evt):
        if self.manageDirty(message('main_save_matrix_data')):
            self.stopLive(bBusy=False)
            self.Destroy()

    def OnDestroyWindow(self, evt):
        if evt.GetId()==self.m_id:
            self.CloseLinks()

    # --- [ menu ] -------------------------------------

    def OnOpen(self,e):
        if self.manageDirty(message('main_save_matrix_data'),fnt='open'):
            dp = select_iTradePortfolio(self,self.m_portfolio,'select')
            if dp:
                self.NewContext(dp)

    def NewContext(self,dp):
        # close links
        self.CloseLinks()

        # change portfolio
        self.m_portfolio = dp

        self.m_matrix = createMatrix(dp.filename(),dp)
        self.m_market = self.m_portfolio.market()
        self.m_connector = getLiveConnector(self.m_market)

        # populate current view and refresh
        self.OnPostInit(None)

    def OnNew(self,e):
        if self.manageDirty(message('main_save_matrix_data'),fnt='open'):
            dp = properties_iTradePortfolio(self,None,'create')
            if dp:
                self.NewContext(dp)
                self.setDirty()

    def OnEdit(self,e):
        properties_iTradePortfolio(self,self.m_portfolio,'edit')

    def OnDelete(self,e):
        dp = select_iTradePortfolio(self,self.m_portfolio,'delete')
        if dp:
            properties_iTradePortfolio(self,dp,'delete')

    def OnSaveAs(self,e):
        if self.manageDirty(message('main_save_matrix_data'),fnt='open'):
            dp = properties_iTradePortfolio(self,self.m_portfolio,'rename')
            if dp:
                self.NewContext(dp)

    def OnSave(self,e):
        self.m_matrix.save(self.m_portfolio.filename())
        itrade_config.saveConfig()
        self.saveConfig()
        self.clearDirty()

    def OnSupport(self,e):
        iTradeLaunchBrowser(itrade_config.supportURL,new=True)

    def OnBug(self,e):
        iTradeLaunchBrowser(itrade_config.bugTrackerURL,new=True)

    def OnDonors(self,e):
        iTradeLaunchBrowser(itrade_config.donorsTrackerURL,new=True)

    def OnManageList(self,e):
        pass

    def OnAbout(self,e):
        d = iTradeAboutBox(self)
        d.ShowModal()
        d.Destroy()

    def updateCheckItems(self):
        # refresh Check state based on current View
        m = self.matrixmenu.FindItemById(ID_PORTFOLIO)
        m.Check(self.m_listmode == LISTMODE_PORTFOLIO)

        m = self.matrixmenu.FindItemById(ID_QUOTES)
        m.Check(self.m_listmode == LISTMODE_QUOTES)

        m = self.matrixmenu.FindItemById(ID_STOPS)
        m.Check(self.m_listmode == LISTMODE_STOPS)

        m = self.matrixmenu.FindItemById(ID_INDICATORS)
        m.Check(self.m_listmode == LISTMODE_INDICATORS)

        m = self.matrixmenu.FindItemById(ID_AUTOREFRESH)
        m.Check(itrade_config.bAutoRefreshMatrixView)

        m = self.matrixmenu.FindItemById(ID_SMALL_VIEW)
        m.Check(itrade_config.matrixFontSize==1)

        m = self.matrixmenu.FindItemById(ID_NORMAL_VIEW)
        m.Check(itrade_config.matrixFontSize==2)

        m = self.matrixmenu.FindItemById(ID_BIG_VIEW)
        m.Check(itrade_config.matrixFontSize==3)

        # refresh Enable state based on current View
        m = self.quotemenu.FindItemById(ID_ADD_QUOTE)
        m.Enable(self.m_listmode == LISTMODE_QUOTES)

    def updateQuoteItems(self):
        op1 = (self.m_currentItem>=0) and (self.m_currentItem<self.m_maxlines)
        if op1:
            quote = quotes.lookupISIN(self.m_list.GetItemText(self.m_currentItem))
        else:
            quote = None

        m = self.quotemenu.FindItemById(ID_GRAPH_QUOTE)
        m.Enable(op1)
        m = self.quotemenu.FindItemById(ID_LIVE_QUOTE)
        m.Enable(op1 and quote.liveconnector().hasNotebook())
        m = self.quotemenu.FindItemById(ID_PROPERTY_QUOTE)
        m.Enable(op1)

        m = self.quotemenu.FindItemById(ID_REMOVE_QUOTE)
        m.Enable((self.m_listmode == LISTMODE_QUOTES) and op1 and not quote.isTraded())

    def updateTitle(self):
        if self.m_listmode == LISTMODE_PORTFOLIO:
            title = message('main_title_portfolio')
        elif self.m_listmode == LISTMODE_QUOTES:
            title = message('main_title_quotes')
        elif self.m_listmode == LISTMODE_STOPS:
            title = message('main_title_stops')
        elif self.m_listmode == LISTMODE_INDICATORS:
            title = message('main_title_indicators')
        else:
            title = '??? %s:%s'
        self.SetTitle(title % (self.m_portfolio.name(),self.m_portfolio.accountref()))

    def RebuildList(self):
        self.m_matrix.build()
        self.populate(bDuringInit=False)
        self.OnRefresh(None)

    def OnPortfolio(self,e):
        if self.m_listmode != LISTMODE_PORTFOLIO:
            self.m_listmode = LISTMODE_PORTFOLIO
            self.populate(bDuringInit=False)
            self.updateTitle()
        self.updateCheckItems()
        self.OnRefresh(None)

    def OnQuotes(self,e):
        if self.m_listmode != LISTMODE_QUOTES:
            self.m_listmode = LISTMODE_QUOTES
            self.populate(bDuringInit=False)
            self.updateTitle()
        self.updateCheckItems()
        self.OnRefresh(None)

    def OnStops(self,e):
        if self.m_listmode != LISTMODE_STOPS:
            self.m_listmode = LISTMODE_STOPS
            self.populate(bDuringInit=False)
            self.updateTitle()
        self.updateCheckItems()
        self.OnRefresh(None)

    def OnIndicators(self,e):
        if self.m_listmode != LISTMODE_INDICATORS:
            self.m_listmode = LISTMODE_INDICATORS
            self.populate(bDuringInit=False)
            self.updateTitle()
        self.updateCheckItems()
        self.OnRefresh(None)

    def OnOperations(self,e):
        open_iTradeOperations(self,self.m_portfolio)

    def OnMoney(self,e):
        if self.m_currentItem>=0:
            quote = self.m_list.GetItemText(self.m_currentItem)
        else:
            quote = None
        open_iTradeMoney(self,0,self.m_portfolio,quote)

    def OnCompute(self,e):
        if self.m_currentItem>=0:
            quote = self.m_list.GetItemText(self.m_currentItem)
        else:
            quote = None
        open_iTradeMoney(self,1,self.m_portfolio,quote)

    def OnAlerts(self,e):
        open_iTradeAlerts(self,self.m_portfolio)

    def OnCurrencies(self,e):
        open_iTradeCurrencies(self)

    def OnGraphQuote(self,e):
        if self.m_currentItem>=0:
            debug("OnGraphQuote: %s" % self.m_list.GetItemText(self.m_currentItem))
            open_iTradeQuote(self,self.m_portfolio,self.m_list.GetItemText(self.m_currentItem),page=1)

    def OnLiveQuote(self,e):
        if self.m_currentItem>=0:
            debug("OnLiveQuote: %s" % self.m_list.GetItemText(self.m_currentItem))
            open_iTradeQuote(self,self.m_portfolio,self.m_list.GetItemText(self.m_currentItem),page=2)

    def OnPropertyQuote(self,e):
        if self.m_currentItem>=0:
            debug("OnPropertyQuote: %s" % self.m_list.GetItemText(self.m_currentItem))
            open_iTradeQuote(self,self.m_portfolio,self.m_list.GetItemText(self.m_currentItem),page=7)

    # --- [ Text font size management ] -------------------------------------

    def OnChangeViewText(self):
        self.setDirty()
        self.updateCheckItems()
        self.m_list.SetFont(wxFontFromSize(itrade_config.matrixFontSize))
        for i in range(0,IDC_LAST+1):
            self.m_list.SetColumnWidth(i, wxLIST_AUTOSIZE)

    def OnViewSmall(self,e):
        itrade_config.matrixFontSize = 1
        self.OnChangeViewText()

    def OnViewNormal(self,e):
        itrade_config.matrixFontSize = 2
        self.OnChangeViewText()

    def OnViewBig(self,e):
        itrade_config.matrixFontSize = 3
        self.OnChangeViewText()

    # --- [ autorefresh management ] -------------------------------------

    def OnAutoRefresh(self,e):
        itrade_config.bAutoRefreshMatrixView = not itrade_config.bAutoRefreshMatrixView
        self.setDirty()
        self.updateCheckItems()
        if itrade_config.bAutoRefreshMatrixView:
            self.startLive()
        else:
            self.stopLive(bBusy=True)

    # --- [ refresh lists ] -------------------------------------

    def OnLive(self, evt):
        # be sure this quote is still under population
        if self.isRunning(evt.quote):
            idview = evt.param
            for xline in range(0,self.m_maxlines):
                if self.itemQuoteMap[xline] == evt.quote:
                    #print 'live %d %d %d VS %d' % (xline,idview,xtype,self.m_listmode)
                    if idview == self.m_listmode:
                        #debug('%s: %s' % (evt.quote.isin(),evt.param))
                        if self.m_listmode == LISTMODE_QUOTES:
                            self.refreshQuoteLine(xline,True)
                        elif self.m_listmode == LISTMODE_PORTFOLIO:
                            self.refreshPortfolioLine(xline,True)
                        elif self.m_listmode == LISTMODE_INDICATORS:
                            evt.quote.compute()
                            self.refreshIndicatorLine(xline,True)
                        else:
                            self.refreshStopLine(xline,True)
                        self.refreshConnexion()
                    else:
                        debug('%s: %s - bad : other view' % (evt.quote.isin(),evt.param))
        else:
            debug('%s: %s - bad : not running' % (evt.quote.isin(),evt.param))

    def OnRefresh(self,e):
        if self.m_portfolio.is_multicurrencies():
            self.refreshCurrencies()
        if self.m_listmode == LISTMODE_QUOTES:
            self.refreshQuotes()
        elif self.m_listmode == LISTMODE_PORTFOLIO:
            self.refreshPortfolio()
        elif self.m_listmode == LISTMODE_INDICATORS:
            self.refreshIndicators()
        else:
            self.refreshStops()

    def refreshCurrencies(self):
        x = 0
        lst = currencies.m_currencies
        max = len(lst)
        keepGoing = True
        if self.hasFocus():
            dlg = wxProgressDialog(message('currency_refreshing'),"",max,self,wxPD_CAN_ABORT | wxPD_APP_MODAL)
        else:
            dlg = None
        for eachKey in lst:
            if keepGoing:
                curTo = eachKey[:3]
                curFrom = eachKey[3:]
                if currencies.used(curTo,curFrom):
                    if dlg:
                        keepGoing = dlg.Update(x,"%s -> %s" % (curFrom,curTo))
                    currencies.get(curTo,curFrom)
                    x = x + 1

        currencies.save()
        if dlg:
            dlg.Destroy()

    def refreshConnexion(self):
        self.m_toolbar.SetIndicator(self.m_market,self.m_connector.currentClock())

    def refreshColorLine(self,x,color):
        # update line color and icon
        item = self.m_list.GetItem(x)
        if color == QUOTE_INVALID:
            item.SetTextColour(wxBLACK)
            item.SetImage(self.idx_tbref)
        elif color == QUOTE_RED:
            item.SetTextColour(wxRED)
            item.SetImage(self.idx_down)
        elif color == QUOTE_GREEN:
            item.SetTextColour(wxBLUE)
            item.SetImage(self.idx_up)
        else:
            item.SetTextColour(wxBLACK)
            item.SetImage(self.idx_nochange)
        self.m_list.SetItem(item)

    def refreshEvalLine(self,x):
        self.m_list.SetStringItem(x,IDC_PR,"%s %s" % (self.m_portfolio.sv_buy(fmt="%.0f"),self.m_portfolio.currency_symbol()))
        self.m_list.SetStringItem(x,IDC_PV,"%s %s" % (self.m_portfolio.sv_value(fmt="%.0f"),self.m_portfolio.currency_symbol()))
        self.m_list.SetStringItem(x,IDC_PROFIT,"%s %s" % (self.m_portfolio.sv_perf(fmt="%.0f"),self.m_portfolio.currency_symbol()))
        self.m_list.SetStringItem(x,IDC_PERCENT,self.m_portfolio.sv_perfPercent())

        if self.m_portfolio.nv_perf()>=0:
            self.refreshColorLine(x,QUOTE_GREEN)
        else:
            self.refreshColorLine(x,QUOTE_RED)

        # enough space for data ?
        self.m_list.SetColumnWidth(IDC_PV, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PR, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PROFIT, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PERCENT, wxLIST_AUTOSIZE)

    def refreshQuoteLine(self,x,disp):
        key = self.m_list.GetItemData(x)
        #print 'line:%d -> key=%d quote=%s' % (x,key,self.itemQuoteMap[key].ticker())
        quote = self.itemQuoteMap[key]

        # refresh line text
        if disp:
            self.m_list.SetStringItem(x,IDC_PREV,quote.sv_prevclose())
            self.m_list.SetStringItem(x,IDC_CLOSE,quote.sv_close(bDispCurrency=True))
            self.m_list.SetStringItem(x,IDC_PERCENT,quote.sv_percent())
            if quote.hasTraded():
                self.m_list.SetStringItem(x,IDC_OPEN,quote.sv_open())
                self.m_list.SetStringItem(x,IDC_HIGH,quote.sv_high())
                self.m_list.SetStringItem(x,IDC_LOW,quote.sv_low())
                self.m_list.SetStringItem(x,IDC_PIVOTS," ----- ") # __x
                self.m_list.SetStringItem(x,IDC_VOLUME,quote.sv_volume())
                color = quote.colorTrend()
            else:
                # not already opened today ...
                self.m_list.SetStringItem(x,IDC_OPEN," ---.-- ")
                self.m_list.SetStringItem(x,IDC_HIGH," ---.-- ")
                self.m_list.SetStringItem(x,IDC_LOW," ---.-- ")
                self.m_list.SetStringItem(x,IDC_PIVOTS," ----- ")
                self.m_list.SetStringItem(x,IDC_VOLUME," ---------- ")
                color = QUOTE_NOCHANGE
        else:
            self.m_list.SetStringItem(x,IDC_PREV," ---.-- ")
            self.m_list.SetStringItem(x,IDC_CLOSE," ---.-- %s" % quote.currency_symbol())
            self.m_list.SetStringItem(x,IDC_OPEN," ---.-- ")
            self.m_list.SetStringItem(x,IDC_HIGH," ---.-- ")
            self.m_list.SetStringItem(x,IDC_LOW," ---.-- ")
            self.m_list.SetStringItem(x,IDC_PIVOTS," ----- ")
            self.m_list.SetStringItem(x,IDC_VOLUME," ---------- ")
            self.m_list.SetStringItem(x,IDC_PERCENT," ---.-- %")
            color = QUOTE_INVALID

        self.refreshColorLine(x,color)

        # enough space for data ?
        self.m_list.SetColumnWidth(IDC_VOLUME, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PREV, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_OPEN, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_HIGH, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_LOW, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PIVOTS, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_CLOSE, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PERCENT, wxLIST_AUTOSIZE)

    def refreshQuotes(self):
        x = 0
        lst = self.m_matrix.list()
        max = len(lst)
        keepGoing = True
        if self.hasFocus():
            dlg = wxProgressDialog(message('main_refreshing'),"",max,self,wxPD_CAN_ABORT | wxPD_APP_MODAL)
        else:
            dlg = None
        for eachQuote in lst:
            if keepGoing and (eachQuote.isTraded() or eachQuote.isMonitored()):
                debug('refreshQuotes: OK : %s' % eachQuote.ticker())
                if dlg:
                    keepGoing = dlg.Update(x,eachQuote.name())
                eachQuote.update()
                for xline in range(0,self.m_maxlines):
                    if self.itemQuoteMap[xline] == eachQuote:
                        self.refreshQuoteLine(xline,True)
                x = x + 1
            else:
                debug('refreshQuotes: ignore : %s' % eachQuote.ticker())

        if dlg:
            dlg.Destroy()

    def refreshPortfolioLine(self,x,disp):
        key = self.m_list.GetItemData(x)
        #print 'line:%d -> key=%d quote=%s' % (x,key,self.itemQuoteMap[key].ticker())
        quote = self.itemQuoteMap[key]
        if quote==None: return
        xtype = self.itemTypeMap[key]
        item = self.m_list.GetItem(x)

        # refresh line text
        if disp:
            self.m_list.SetStringItem(x,IDC_PVU,quote.sv_close(bDispCurrency=True))
            if quote.hasTraded():
                self.m_list.SetStringItem(x,IDC_PERFDAY,quote.sv_percent())
            else:
                self.m_list.SetStringItem(x,IDC_PERFDAY," ---.-- % ")
            self.m_list.SetStringItem(x,IDC_PV,"%s %s" % (quote.sv_pv(self.m_portfolio.currency(),xtype,fmt="%.0f"),self.m_portfolio.currency_symbol()))
            self.m_list.SetStringItem(x,IDC_PROFIT,"%s %s" % (quote.sv_profit(self.m_portfolio.currency(),xtype,fmt="%.0f"),self.m_portfolio.currency_symbol()))
            self.m_list.SetStringItem(x,IDC_PERCENT,quote.sv_profitPercent(self.m_portfolio.currency(),xtype))
            # line color depending on pricing
            if quote.nv_pru(xtype) >= quote.nv_close():
                item.SetImage(self.idx_down)
                item.SetTextColour(wxRED)
            else:
                item.SetImage(self.idx_up)
                item.SetTextColour(wxBLUE)
        else:
            item.SetTextColour(wxBLACK)
            item.SetImage(self.idx_tbref)
            self.m_list.SetStringItem(x,IDC_PVU," ---.-- ")
            self.m_list.SetStringItem(x,IDC_PERFDAY," ---.-- % ")
            self.m_list.SetStringItem(x,IDC_PV," ---.-- %s" % self.m_portfolio.currency_symbol())
            self.m_list.SetStringItem(x,IDC_PROFIT," ----.-- %s" % self.m_portfolio.currency_symbol())
            self.m_list.SetStringItem(x,IDC_PERCENT," ---.-- % ")

        self.m_list.SetItem(item)

        self.m_list.SetColumnWidth(IDC_PVU, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PERFDAY, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PV, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PROFIT, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PERCENT, wxLIST_AUTOSIZE)

    def refreshPortfolio(self):
        x = 0
        lst = self.m_matrix.list()
        max = len(lst)
        keepGoing = True
        if self.hasFocus():
            dlg = wxProgressDialog(message('main_refreshing'),"",max,self,wxPD_CAN_ABORT | wxPD_APP_MODAL)
        else:
            dlg = None
        for eachQuote in lst:
            # in portfolio view, display only traded values !
            if keepGoing and eachQuote.isTraded():
                if dlg:
                    keepGoing = dlg.Update(x,eachQuote.name())
                eachQuote.update()
                for xline in range(0,self.m_maxlines):
                    if self.itemQuoteMap[xline] == eachQuote:
                       self.refreshPortfolioLine(xline,True)
                x = x + 1

        self.m_portfolio.computeOperations()
        self.refreshEvalLine(self.m_maxlines+1)

        if dlg:
            dlg.Destroy()

    def refreshStopLine(self,x,disp):
        key = self.m_list.GetItemData(x)
        #print 'line:%d -> key=%d quote=%s' % (x,key,self.itemQuoteMap[key].ticker())
        quote = self.itemQuoteMap[key]

        item = self.m_list.GetItem(x)

        if disp:
            self.m_list.SetStringItem(x,IDC_CURRENT,quote.sv_close(bDispCurrency=True))
            self.m_list.SetStringItem(x,IDC_PV,"%s %s" % (quote.sv_pv(self.m_portfolio.currency(),fmt="%.0f"),self.m_portfolio.currency_symbol()))
            self.m_list.SetStringItem(x,IDC_PROFIT,"%s %s" % (quote.sv_profit(self.m_portfolio.currency(),fmt="%.0f"),self.m_portfolio.currency_symbol()))
            self.m_list.SetStringItem(x,IDC_PERCENT,quote.sv_profitPercent(self.m_portfolio.currency()))
            color = quote.colorStop()
        else:
            self.m_list.SetStringItem(x,IDC_CURRENT," ---.-- %s " % quote.currency_symbol())
            self.m_list.SetStringItem(x,IDC_PV," ------ %s" % self.m_portfolio.currency_symbol())
            self.m_list.SetStringItem(x,IDC_PROFIT," ------ %s" % self.m_portfolio.currency_symbol())
            self.m_list.SetStringItem(x,IDC_PERCENT," ---.-- % ")
            color = QUOTE_INVALID

        # update line color and icon
        if color == QUOTE_INVALID:
            item.SetTextColour(wxBLACK)
            item.SetImage(self.idx_tbref)
        elif color == QUOTE_RED:
            item.SetTextColour(wxRED)
            item.SetImage(self.idx_sell)
        elif color == QUOTE_GREEN:
            item.SetTextColour(wxBLUE)
            item.SetImage(self.idx_buy)
        else:
            item.SetTextColour(wxBLACK)
            item.SetImage(self.idx_noop)

        self.m_list.SetItem(item)
        self.m_list.SetColumnWidth(IDC_CURRENT, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PV, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PROFIT, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PERCENT, wxLIST_AUTOSIZE)

    def refreshStops(self):
        x = 0
        lst = self.m_matrix.list()
        max = len(lst)
        keepGoing = True
        if self.hasFocus():
            dlg = wxProgressDialog(message('main_refreshing'),"",max,self,wxPD_CAN_ABORT | wxPD_APP_MODAL)
        else:
            dlg = None
        for eachQuote in lst:
            if keepGoing and eachQuote.hasStops() and (eachQuote.isTraded() or eachQuote.isMonitored()):
                if dlg:
                    keepGoing = dlg.Update(x,eachQuote.name())
                eachQuote.update()
                for xline in range(0,self.m_maxlines):
                    if self.itemQuoteMap[xline] == eachQuote:
                        self.refreshStopLine(xline,True)
                x = x + 1

        if dlg:
            dlg.Destroy()

    def refreshIndicatorLine(self,x,disp):
        key = self.m_list.GetItemData(x)
        #print 'line:%d -> key=%d quote=%s' % (x,key,self.itemQuoteMap[key].ticker())
        quote = self.itemQuoteMap[key]

        item = self.m_list.GetItem(x)

        if disp:
            self.m_list.SetStringItem(x,IDC_LAST,quote.sv_close(bDispCurrency=True))
            if quote.hasTraded():
                color = quote.colorTrend()
            else:
                color = QUOTE_NOCHANGE
            self.m_list.SetStringItem(x,IDC_MA20,quote.sv_ma(20))
            self.m_list.SetStringItem(x,IDC_MA50,quote.sv_ma(50))
            self.m_list.SetStringItem(x,IDC_MA100,quote.sv_ma(100))
        else:
            # no information
            self.m_list.SetStringItem(x,IDC_MA20," ---.--- ")
            self.m_list.SetStringItem(x,IDC_MA50," ---.--- ")
            self.m_list.SetStringItem(x,IDC_MA100," ---.--- ")
            self.m_list.SetStringItem(x,IDC_RSI," ---.-- ")
            self.m_list.SetStringItem(x,IDC_MACD," ---.-- ")
            self.m_list.SetStringItem(x,IDC_STOCH," ---.-- ")
            self.m_list.SetStringItem(x,IDC_DMI," ---.-- ")
            self.m_list.SetStringItem(x,IDC_EMV," ---.-- ")
            self.m_list.SetStringItem(x,IDC_OVB," ---.-- ")
            self.m_list.SetStringItem(x,IDC_LAST," ---.-- %s" % quote.currency_symbol())
            color = QUOTE_NOCHANGE

        # update line color and icon
        item = self.m_list.GetItem(x)
        if color == QUOTE_INVALID:
            item.SetTextColour(wxBLACK)
            item.SetImage(self.idx_tbref)
        elif color == QUOTE_RED:
            item.SetTextColour(wxRED)
            item.SetImage(self.idx_down)
        elif color == QUOTE_GREEN:
            item.SetTextColour(wxBLUE)
            item.SetImage(self.idx_up)
        else:
            item.SetTextColour(wxBLACK)
            item.SetImage(self.idx_nochange)
        self.m_list.SetItem(item)

        # enough space for data ?
        self.m_list.SetColumnWidth(IDC_MA20, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_MA50, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_MA100, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_RSI, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_MACD, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_STOCH, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_DMI, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_EMV, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_OVB, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_LAST, wxLIST_AUTOSIZE)

    def refreshIndicators(self):
        x = 0
        lst = self.m_matrix.list()
        max = len(lst)
        keepGoing = True
        if self.hasFocus():
            dlg = wxProgressDialog(message('main_refreshing'),"",max,self,wxPD_CAN_ABORT | wxPD_APP_MODAL)
        else:
            dlg = None
        for eachQuote in lst:
            if keepGoing and (eachQuote.isTraded() or eachQuote.isMonitored()):
                if dlg:
                    keepGoing = dlg.Update(x,eachQuote.name())
                eachQuote.update()
                eachQuote.compute()
                for xline in range(0,self.m_maxlines):
                    if self.itemQuoteMap[xline] == eachQuote:
                        self.refreshIndicatorLine(xline,True)
                x = x + 1

        if dlg:
            dlg.Destroy()

    # ---[ Populate view ] -----------------------------------------

    def populate(self,bDuringInit):
        info('populate duringinit=%d'%bDuringInit)
        # clear current population
        self.stopLive(bBusy=False)
        self.unregisterLive()
        self.m_list.ClearAll()

        # start a new population
        if self.m_listmode == LISTMODE_QUOTES:
            self.populateQuotes()
        elif self.m_listmode == LISTMODE_PORTFOLIO:
            self.populatePortfolio()
        elif self.m_listmode == LISTMODE_INDICATORS:
            self.populateIndicators()
        else:
            self.populateStops()
        if not bDuringInit and itrade_config.bAutoRefreshMatrixView:
            self.startLive()

    def populateMatrixBegin(self):
        # init item data (for sorting)
        self.itemDataMap = {}
        self.itemQuoteMap = {}
        self.itemTypeMap = {}

        # at least isin and ticker columns !
        self.m_list.InsertColumn(IDC_ISIN, message('isin'), wxLIST_FORMAT_LEFT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_TICKER, message('ticker'), wxLIST_FORMAT_LEFT, wxLIST_AUTOSIZE_USEHEADER)

    def populateMatrixEnd(self):
        # fix the item data
        items = self.itemDataMap.items()
        for x in range(len(items)):
            key, data = items[x]
            self.m_list.SetItemData(x, key)

        # adjust column
        self.m_list.SetColumnWidth(IDC_ISIN, wxLIST_AUTOSIZE_USEHEADER)
        self.m_list.SetColumnWidth(IDC_TICKER, wxLIST_AUTOSIZE_USEHEADER)

        # default selection
        self.m_currentItem = 0
        self.m_list.SetItemState(0, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED)

    def populatePortfolio(self):
        self.populateMatrixBegin()

        self.m_list.InsertColumn(IDC_QTY, message('qty'), wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PRU, message('UPP'), wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PR, message('buy'), wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PVU, message('USP'), wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PERFDAY, message('perfday'), wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PV, message('sell'), wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PROFIT, message('profit'), wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PERCENT, message('perfper'), wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_NAME, message('name'), wxLIST_FORMAT_LEFT, wxLIST_AUTOSIZE)

        x = 0
        for eachQuote in self.m_matrix.list():
            # in portfolio view, display only traded values !
            if eachQuote.isTraded():
                if eachQuote.nv_number(QUOTE_CASH)>0:
                    self.m_list.InsertImageStringItem(x, eachQuote.isin(), self.idx_tbref)
                    self.m_list.SetStringItem(x,IDC_TICKER,eachQuote.ticker())
                    self.m_list.SetStringItem(x,IDC_QTY,eachQuote.sv_number(QUOTE_CASH))
                    self.m_list.SetStringItem(x,IDC_PRU,"%s %s" % (eachQuote.sv_pru(QUOTE_CASH),self.m_portfolio.currency_symbol()))
                    self.m_list.SetStringItem(x,IDC_PR,"%s %s" % (eachQuote.sv_pr(QUOTE_CASH,fmt="%.0f"),self.m_portfolio.currency_symbol()))
                    self.m_list.SetStringItem(x,IDC_NAME,eachQuote.name())

                    self.itemDataMap[x] = (eachQuote.isin(),eachQuote.ticker(),x,x,x,x,x,x,x,x,eachQuote.name())
                    self.itemQuoteMap[x] = eachQuote
                    self.itemTypeMap[x] = QUOTE_CASH

                    self.refreshPortfolioLine(x,False)

                    x = x + 1

                if eachQuote.nv_number(QUOTE_CREDIT)>0:
                    self.m_list.InsertImageStringItem(x, eachQuote.isin(), self.idx_tbref)
                    self.m_list.SetStringItem(x,IDC_TICKER,"%s (%s)" % (eachQuote.ticker(),message("money_srd")))
                    self.m_list.SetStringItem(x,IDC_QTY,eachQuote.sv_number(QUOTE_CREDIT))
                    self.m_list.SetStringItem(x,IDC_PRU,"%s %s" % (eachQuote.sv_pru(QUOTE_CREDIT),self.m_portfolio.currency_symbol()))
                    self.m_list.SetStringItem(x,IDC_PR,"%s %s" % (eachQuote.sv_pr(QUOTE_CREDIT),self.m_portfolio.currency_symbol()))
                    self.m_list.SetStringItem(x,IDC_NAME,eachQuote.name())

                    self.itemDataMap[x] = (eachQuote.isin(),eachQuote.ticker(),x,x,x,x,x,x,x,x,eachQuote.name())
                    self.itemQuoteMap[x] = eachQuote
                    self.itemTypeMap[x] = QUOTE_CREDIT

                    self.refreshPortfolioLine(x,False)

                    x = x + 1

        self.m_maxlines = x
        for eachQuote in self.itemQuoteMap.values():
            self.registerLive(eachQuote,itrade_config.refreshView,LISTMODE_PORTFOLIO)

        self.m_list.InsertImageStringItem(x, '', -1)
        self.itemDataMap[x] = ('ZZZZ1','ZZZZ1','ZZZZ1','ZZZZ1','ZZZZ1','ZZZZ1','ZZZZ1','ZZZZ1','ZZZZ1','ZZZZ1','ZZZZ1')
        self.itemQuoteMap[x] = None
        self.itemTypeMap[x] = QUOTE_BOTH
        self.m_list.InsertImageStringItem(x+1, message('main_valuation'), -1)
        self.itemDataMap[x+1] = ('ZZZZ2','ZZZZ2','ZZZZ2','ZZZZ2','ZZZZ2','ZZZZ2','ZZZZ2','ZZZZ2','ZZZZ2','ZZZZ2','ZZZZ2')
        self.itemQuoteMap[x+1] = None
        self.itemTypeMap[x+1] = QUOTE_BOTH

        # adjust some column's size
        self.m_list.SetColumnWidth(IDC_QTY, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PRU, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PR, wxLIST_AUTOSIZE)

        # finish populating
        self.populateMatrixEnd()

    def populateStops(self):
        self.populateMatrixBegin()

        self.m_list.InsertColumn(IDC_INVEST, 'Buy', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_RISKM, 'Risk', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_STOPLOSS, 'Stop-', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_CURRENT, 'USP', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_STOPWIN, 'Stop+', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PV, 'Sell', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PROFIT, 'Profit', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PERCENT, ' % ', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_NAME, message('name'), wxLIST_FORMAT_LEFT, wxLIST_AUTOSIZE)

        x = 0
        for eachQuote in self.m_matrix.list():
            # in portfolio view, display only traded values !
            if eachQuote.hasStops() and (eachQuote.isTraded() or eachQuote.isMonitored()):
                self.m_list.InsertImageStringItem(x, eachQuote.isin(), self.idx_tbref)
                self.m_list.SetStringItem(x,IDC_TICKER,eachQuote.ticker())
                self.m_list.SetStringItem(x,IDC_INVEST,"%s %s" % (eachQuote.sv_pr(fmt="%.0f"),self.m_portfolio.currency_symbol()))
                self.m_list.SetStringItem(x,IDC_RISKM,"%s %s" % (eachQuote.sv_riskmoney(self.m_portfolio.currency()),self.m_portfolio.currency_symbol()))
                self.m_list.SetStringItem(x,IDC_STOPLOSS,"~ %s " % eachQuote.sv_stoploss())
                self.m_list.SetStringItem(x,IDC_CURRENT,eachQuote.sv_close(bDispCurrency=True))
                self.m_list.SetStringItem(x,IDC_STOPWIN,"~ %s " % eachQuote.sv_stopwin())
                self.m_list.SetStringItem(x,IDC_NAME,eachQuote.name())

                self.itemDataMap[x] = (eachQuote.isin(),eachQuote.ticker(),x,x,x,x,x,x,x,x,eachQuote.name())
                self.itemQuoteMap[x] = eachQuote
                self.itemTypeMap[x] = QUOTE_BOTH

                self.refreshStopLine(x,False)

                x = x + 1

        self.m_maxlines = x
        for eachQuote in self.itemQuoteMap.values():
            self.registerLive(eachQuote,itrade_config.refreshView,LISTMODE_STOPS)

        # adjust some column's size
        self.m_list.SetColumnWidth(IDC_INVEST, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_RISKM, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_STOPLOSS, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_STOPWIN, wxLIST_AUTOSIZE)

        # finish populating
        self.populateMatrixEnd()

    def populateQuotes(self):
        self.populateMatrixBegin()

        self.m_list.InsertColumn(IDC_VOLUME, message('volume'), wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PREV, message('prev'), wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_OPEN, message('open'), wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_HIGH, message('high'), wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_LOW,  message('low'), wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_CLOSE,message('last'), wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PIVOTS,message('pivots'), wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PERCENT, ' % ', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_NAME, message('name'), wxLIST_FORMAT_LEFT, wxLIST_AUTOSIZE)

        x = 0
        for eachQuote in self.m_matrix.list():
            if (eachQuote.isTraded() or eachQuote.isMonitored()):
                self.m_list.InsertImageStringItem(x, eachQuote.isin(), self.idx_tbref)
                self.m_list.SetStringItem(x,IDC_TICKER,eachQuote.ticker())
                self.m_list.SetStringItem(x,IDC_NAME,eachQuote.name())

                self.itemDataMap[x] = (eachQuote.isin(),eachQuote.ticker(),x,x,x,x,x,x,x,x,eachQuote.name())
                self.itemQuoteMap[x] = eachQuote
                self.itemTypeMap[x] = QUOTE_BOTH

                self.refreshQuoteLine(x,False)

                x = x + 1

        self.m_maxlines = x
        for eachQuote in self.itemQuoteMap.values():
            self.registerLive(eachQuote,itrade_config.refreshView,LISTMODE_QUOTES)

        self.populateMatrixEnd()

    def populateIndicators(self):
        self.populateMatrixBegin()

        self.m_list.InsertColumn(IDC_MA20, 'ma20', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_MA50, 'ma50', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_MA100, 'ma100', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_RSI, 'RSI', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_MACD, 'MACD', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_STOCH, 'STOCH', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_DMI, 'DMI', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_EMV, 'EMV', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_OVB, 'OVB', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_LAST, 'Last', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_LAST+1, '', wxLIST_FORMAT_RIGHT, wxLIST_AUTOSIZE)

        x = 0
        for eachQuote in self.m_matrix.list():
            if (eachQuote.isTraded() or eachQuote.isMonitored()):
                self.m_list.InsertImageStringItem(x, eachQuote.isin(), self.idx_tbref)
                self.m_list.SetStringItem(x,IDC_TICKER,eachQuote.ticker())

                self.itemDataMap[x] = (eachQuote.isin(),eachQuote.ticker(),x,x,x,x,x,x,x,x,eachQuote.name())
                self.itemQuoteMap[x] = eachQuote
                self.itemTypeMap[x] = QUOTE_BOTH

                self.refreshIndicatorLine(x,False)

                x = x + 1

        self.m_maxlines = x
        for eachQuote in self.itemQuoteMap.values():
            self.registerLive(eachQuote,itrade_config.refreshView,LISTMODE_INDICATORS)

        self.populateMatrixEnd()

    # ---[ List commands and pop-up ] -----------------------------------------

    def getColumnText(self, index, col):
        item = self.m_list.GetItem(index, col)
        return item.GetText()

    def OnRightDown(self, event):
        self.x = event.GetX()
        self.y = event.GetY()
        item, flags = self.m_list.HitTest((self.x, self.y))
        debug("OnRightDown: x, y = %s item=%d max=%d" % (str((self.x, self.y)), item,self.m_maxlines))
        if flags & wxLIST_HITTEST_ONITEM:
            pass
        else:
            self.m_currentItem = -1
        self.updateQuoteItems()
        event.Skip()

    def OnLeftDown(self, event):
        self.x = event.GetX()
        self.y = event.GetY()
        debug("OnLeftDown: x, y = %s" % str((self.x, self.y)))
        item, flags = self.m_list.HitTest((self.x, self.y))
        if flags & wxLIST_HITTEST_ONITEM:
            pass
        else:
            self.m_currentItem = -1
        self.updateQuoteItems()
        event.Skip()

    def OnItemActivated(self, event):
        self.m_currentItem = event.m_itemIndex
        if (self.m_currentItem>=0) and (self.m_currentItem<self.m_maxlines):
            debug("OnItemActivated: %s" % self.m_list.GetItemText(self.m_currentItem))
            open_iTradeQuote(self,self.m_portfolio,self.m_list.GetItemText(self.m_currentItem))
            # __x if self.m_currentItem == self.m_maxlines, launch eval !

    def OnItemSelected(self, event):
        self.m_currentItem = event.m_itemIndex
        self.updateQuoteItems()
        if (self.m_currentItem>=0) and (self.m_currentItem<self.m_maxlines):
            debug("OnItemSelected: %s, %s, %s, %s\n" %
                               (self.m_currentItem,
                                self.m_list.GetItemText(self.m_currentItem),
                                self.getColumnText(self.m_currentItem, 1),
                                self.getColumnText(self.m_currentItem, 2)))
            # __x if self.m_currentItem == self.m_maxlines, launch eval !
        event.Skip()

    def OnRightClick(self, event):
        if (self.m_currentItem<0) or (self.m_currentItem>=self.m_maxlines):
            # __x if self.m_currentItem == self.m_maxlines, launch eval !
            inList = False
        else:
            inList = True
            quote = quotes.lookupISIN(self.m_list.GetItemText(self.m_currentItem))
            info("OnRightClick %s : %s\n" % (self.m_list.GetItemText(self.m_currentItem),quote))

        # only do this part the first time so the events are only bound once
        if not hasattr(self, "m_popupID_Update"):
            self.m_popupID_Update = wxNewId()
            self.m_popupID_View = wxNewId()
            self.m_popupID_Live = wxNewId()
            self.m_popupID_Properties = wxNewId()
            self.m_popupID_Add = wxNewId()
            self.m_popupID_Remove = wxNewId()
            self.m_popupID_Edit = wxNewId()
            self.m_popupID_Buy = wxNewId()
            self.m_popupID_Sell = wxNewId()
            EVT_MENU(self, self.m_popupID_Update, self.OnPopup_Update)
            EVT_MENU(self, self.m_popupID_View, self.OnPopup_View)
            EVT_MENU(self, self.m_popupID_Live, self.OnPopup_Live)
            EVT_MENU(self, self.m_popupID_Properties, self.OnPopup_Properties)
            EVT_MENU(self, self.m_popupID_Add, self.OnPopup_Add)
            EVT_MENU(self, self.m_popupID_Edit, self.OnPopup_Add)
            EVT_MENU(self, self.m_popupID_Remove, self.OnPopup_Remove)
            EVT_MENU(self, self.m_popupID_Buy, self.OnPopup_Buy)
            EVT_MENU(self, self.m_popupID_Sell, self.OnPopup_Sell)

        # make a menu
        menu = wxMenu()
        # add some items
        menu.Append(self.m_popupID_Update, message('main_popup_refreshall'))
        if self.m_listmode == LISTMODE_QUOTES:
            menu.AppendSeparator()
            menu.Append(self.m_popupID_Add, message('main_popup_add'))
            menu.AppendSeparator()
            menu.Append(self.m_popupID_View, message('main_popup_view'))
            menu.Enable(self.m_popupID_View,inList)
            menu.Append(self.m_popupID_Live, message('main_popup_live'))
            menu.Enable(self.m_popupID_Live,inList and quote.liveconnector().hasNotebook())
            menu.Append(self.m_popupID_Properties, message('main_popup_properties'))
            menu.Enable(self.m_popupID_Properties,inList)
            menu.AppendSeparator()
            menu.Append(self.m_popupID_Buy, message('main_popup_buy'))
            menu.Enable(self.m_popupID_Buy,inList)
            menu.Append(self.m_popupID_Sell, message('main_popup_sell'))
            menu.Enable(self.m_popupID_Sell,inList)
            menu.AppendSeparator()
            menu.Append(self.m_popupID_Remove, message('main_popup_remove'))
            menu.Enable(self.m_popupID_Remove,inList and not quote.isTraded())
            # __x temp (not yet available)
            menu.Enable(self.m_popupID_Buy,False)
            menu.Enable(self.m_popupID_Sell,False)
        elif self.m_listmode == LISTMODE_PORTFOLIO:
            menu.AppendSeparator()
            menu.Append(self.m_popupID_View, message('main_popup_view'))
            menu.Enable(self.m_popupID_View,inList)
            menu.Append(self.m_popupID_Live, message('main_popup_live'))
            menu.Enable(self.m_popupID_Live,inList and quote.liveconnector().hasNotebook())
            menu.Append(self.m_popupID_Properties, message('main_popup_properties'))
            menu.Enable(self.m_popupID_Properties,inList)
            menu.AppendSeparator()
            menu.Append(self.m_popupID_Buy, message('main_popup_buy'))
            menu.Enable(self.m_popupID_Buy,inList)
            menu.Append(self.m_popupID_Sell, message('main_popup_sell'))
            menu.Enable(self.m_popupID_Sell,inList)
            # __x temp (not yet available)
            menu.Enable(self.m_popupID_Buy,False)
            menu.Enable(self.m_popupID_Sell,False)
        elif self.m_listmode == LISTMODE_INDICATORS:
            menu.AppendSeparator()
            menu.Append(self.m_popupID_View, message('main_popup_view'))
            menu.Enable(self.m_popupID_View,inList)
            menu.Append(self.m_popupID_Live, message('main_popup_live'))
            menu.Enable(self.m_popupID_Live,inList and quote.liveconnector().hasNotebook())
            menu.Append(self.m_popupID_Properties, message('main_popup_properties'))
            menu.Enable(self.m_popupID_Properties,inList)
            menu.AppendSeparator()
            menu.Append(self.m_popupID_Buy, message('main_popup_buy'))
            menu.Enable(self.m_popupID_Buy,inList)
            menu.Append(self.m_popupID_Sell, message('main_popup_sell'))
            menu.Enable(self.m_popupID_Sell,inList)
            # __x temp (not yet available)
            menu.Enable(self.m_popupID_Buy,False)
            menu.Enable(self.m_popupID_Sell,False)
        elif self.m_listmode == LISTMODE_STOPS:
            menu.AppendSeparator()
            menu.Append(self.m_popupID_Add, message('main_popup_add'))
            menu.AppendSeparator()
            menu.Append(self.m_popupID_Edit, message('main_popup_edit'))
            menu.Enable(self.m_popupID_Edit,inList)
            menu.Append(self.m_popupID_Remove, message('main_popup_remove'))
            menu.Enable(self.m_popupID_Remove,inList)
            # __x temp (not yet available)
            menu.Enable(self.m_popupID_Add,False)
            menu.Enable(self.m_popupID_Edit,False)
            menu.Enable(self.m_popupID_Remove,False)

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu, wxPoint(self.x, self.y))
        menu.Destroy()

    def OnPopup_Update(self, event):
        debug("OnPopup_Update")
        self.OnRefresh(event)

    def OnPopup_View(self, event):
        debug("OnPopup_View")
        open_iTradeQuote(self,self.m_portfolio,self.m_list.GetItemText(self.m_currentItem),page=1)

    def OnPopup_Live(self, event):
        debug("OnPopup_Live")
        open_iTradeQuote(self,self.m_portfolio,self.m_list.GetItemText(self.m_currentItem),page=2)

    def OnPopup_Properties(self, event):
        debug("OnPopup_Properties")
        open_iTradeQuote(self,self.m_portfolio,self.m_list.GetItemText(self.m_currentItem),page=7)

    def OnAddQuote(self,e):
        quote = addInMatrix_iTradeQuote(self,self.m_matrix)
        if quote:
            self.m_portfolio.setupCurrencies()
            self.setDirty()
            self.m_listmode = LISTMODE_INIT
            self.OnQuotes(None)

    def OnPopup_Add(self, event):
        debug("OnPopup_Add")
        if self.m_listmode == LISTMODE_STOPS:
            pass
        elif self.m_listmode == LISTMODE_QUOTES:
            self.OnAddQuote(None)

    def OnPopup_Edit(self, event):
        debug("OnPopup_Edit")
        if self.m_listmode == LISTMODE_STOPS:
            pass

    def OnRemoveCurrentQuote(self,e):
        if removeFromMatrix_iTradeQuote(self,self.m_matrix,self.m_list.GetItemText(self.m_currentItem)):
            self.m_portfolio.setupCurrencies()
            self.setDirty()
            self.m_listmode = LISTMODE_INIT
            self.OnQuotes(None)

    def OnPopup_Remove(self, event):
        debug("OnPopup_Remove")
        if self.m_listmode == LISTMODE_STOPS:
            pass
        elif self.m_listmode == LISTMODE_QUOTES:
            self.OnRemoveCurrentQuote(None)

    def OnPopup_Buy(self, event):
        debug("OnPopup_Buy")

    def OnPopup_Sell(self, event):
        debug("OnPopup_Sell")

# ============================================================================
# That's all folks !
# ============================================================================
# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
