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
# Portions created by the Initial Developer are Copyright (C) 2004-2007 the
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
import wx
import wx.lib.mixins.listctrl as wxl

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_local import message,gMessage,getLang
from itrade_portfolio import loadPortfolio
from itrade_matrix import *
from itrade_quotes import *
from itrade_ext import *
from itrade_login import *
from itrade_currency import currencies

# iTrade wx system
from itrade_wxquote import open_iTradeQuote,addInMatrix_iTradeQuote,removeFromMatrix_iTradeQuote
from itrade_wxpropquote import open_iTradeQuoteProperty
from itrade_wxportfolio import select_iTradePortfolio,properties_iTradePortfolio
from itrade_wxoperations import open_iTradeOperations
from itrade_wxmoney import open_iTradeMoney
from itrade_wxalerts import open_iTradeAlerts
from itrade_wxcurrency import open_iTradeCurrencies
from itrade_wxabout import iTradeAboutBox
from itrade_wxhtml import iTradeLaunchBrowser
from itrade_wxutil import FontFromSize
from itrade_wxlistquote import list_iTradeQuote
from itrade_wxlogin import login_UI
from itrade_wxstops import addOrEditStops_iTradeQuote,removeStops_iTradeQuote
from itrade_wxmixin import iTrade_wxFrame
from itrade_wxlive import iTrade_wxLiveMixin,EVT_UPDATE_LIVE

from itrade_wxutil import iTradeYesNo

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

ID_ACCESS = 350
# ... free up 399

ID_LANG = 399
ID_LANG_FIRST = 400
ID_LANG_SYSTEM = 400
ID_LANG_ENGLISH = 401
ID_LANG_FRENCH = 402
ID_LANG_PORTUGUESE = 403
ID_LANG_DEUTCH = 404
ID_LANG_LAST = 404

ID_CACHE = 499
ID_CACHE_ERASE_DATA = 500
ID_CACHE_ERASE_NEWS = 501
ID_CACHE_ERASE_ALL = 510

ID_CONTENT = 800
ID_SUPPORT = 801
ID_BUG = 802
ID_FORUM = 803
ID_DONORS = 804
ID_ABOUT = 810

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

class iTradeMatrixListCtrl(wx.ListCtrl, wxl.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        wxl.ListCtrlAutoWidthMixin.__init__(self)

# ============================================================================
# iTradeMainToolbar
#
# ============================================================================

cCONNECTED = wx.Colour(51,255,51)
cDISCONNECTED = wx.Colour(255,51,51)

class iTradeMainToolbar(wx.ToolBar):

    def __init__(self,parent,id):
        wx.ToolBar.__init__(self,parent,id,style = wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        self.m_parent = parent
        self._init_toolbar()

    def _init_toolbar(self):
        self.ClearTools()

        self._NTB2_EXIT = wx.NewId()
        self._NTB2_NEW = wx.NewId()
        self._NTB2_OPEN = wx.NewId()
        self._NTB2_EDIT = wx.NewId()
        self._NTB2_SAVE = wx.NewId()
        self._NTB2_SAVE_AS = wx.NewId()
        self._NTB2_MONEY = wx.NewId()
        self._NTB2_OPERATIONS = wx.NewId()
        self._NTB2_ALERTS = wx.NewId()
        self._NTB2_QUOTE = wx.NewId()
        self._NTB2_REFRESH = wx.NewId()
        self._NTB2_ABOUT = wx.NewId()

        self.SetToolBitmapSize(wx.Size(24,24))
        self.AddSimpleTool(self._NTB2_EXIT, wx.ArtProvider.GetBitmap(wx.ART_CROSS_MARK, wx.ART_TOOLBAR),
                           message('main_exit'), message('main_desc_exit'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_NEW, wx.ArtProvider.GetBitmap(wx.ART_NEW, wx.ART_TOOLBAR),
                           message('main_new'), message('main_desc_new'))
        self.AddSimpleTool(self._NTB2_OPEN, wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR),
                           message('main_open'), message('main_desc_open'))
        self.AddSimpleTool(self._NTB2_EDIT, wx.ArtProvider.GetBitmap(wx.ART_EXECUTABLE_FILE, wx.ART_TOOLBAR),
                           message('main_edit'), message('main_desc_edit'))
        self.AddSimpleTool(self._NTB2_SAVE, wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR),
                           message('main_save'), message('main_desc_save'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_OPERATIONS, wx.ArtProvider.GetBitmap(wx.ART_REPORT_VIEW, wx.ART_TOOLBAR),
                           message('main_view_operations'), message('main_view_desc_operations'))
        self.AddSimpleTool(self._NTB2_MONEY, wx.Bitmap('res/money.png'),
                           message('main_view_money'), message('main_view_desc_money'))
        self.AddSimpleTool(self._NTB2_ALERTS, wx.Bitmap('res/bell.png'),
                           message('main_view_alerts'), message('main_view_desc_alerts'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_QUOTE, wx.Bitmap('res/graph.png'),
                           message('main_quote_graph'), message('main_quote_desc_graph'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_REFRESH, wx.Bitmap('res/refresh.png'),
                           message('main_view_refresh'), message('main_view_desc_refresh'))
        self.AddSimpleTool(self._NTB2_ABOUT, wx.Bitmap('res/about.png'),
                           message('main_about'), message('main_desc_about'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.m_indicator = wx.StaticText(self, -1, "", size=(180,15), style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
        self.AddControl(self.m_indicator)
        self.ClearIndicator()

        wx.EVT_TOOL(self, self._NTB2_EXIT, self.onExit)
        wx.EVT_TOOL(self, self._NTB2_NEW, self.onNew)
        wx.EVT_TOOL(self, self._NTB2_OPEN, self.onOpen)
        wx.EVT_TOOL(self, self._NTB2_EDIT, self.onEdit)
        wx.EVT_TOOL(self, self._NTB2_SAVE, self.onSave)
        wx.EVT_TOOL(self, self._NTB2_OPERATIONS, self.onOperations)
        wx.EVT_TOOL(self, self._NTB2_MONEY, self.onMoney)
        wx.EVT_TOOL(self, self._NTB2_ALERTS, self.onAlerts)
        wx.EVT_TOOL(self, self._NTB2_QUOTE, self.onQuote)
        wx.EVT_TOOL(self, self._NTB2_ABOUT, self.onAbout)
        wx.EVT_TOOL(self, self._NTB2_REFRESH, self.onRefresh)
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

    def ClearIndicator(self):
        if itrade_config.bAutoRefreshMatrixView:
            label = message('indicator_autorefresh')
        else:
            label = message('indicator_noautorefresh')
        self.m_indicator.SetBackgroundColour(wx.NullColour)
        self.m_indicator.ClearBackground()
        self.m_indicator.SetLabel(label)

    def SetIndicator(self,market,clock):
        if clock=="::":
            label = market + ": " + message('indicator_disconnected')
            self.m_indicator.SetBackgroundColour(cDISCONNECTED)
        else:
            label = market + ": " + clock
            if label==self.m_indicator.GetLabel():
                self.m_indicator.SetBackgroundColour(wx.NullColour)
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

class iTradeMainWindow(wx.Frame,iTrade_wxFrame,iTrade_wxLiveMixin, wxl.ColumnSorterMixin):
    def __init__(self,parent,portfolio,matrix):
        self.m_id = wx.NewId()
        wx.Frame.__init__(self,parent,self.m_id, "", size = ( 640,480), style = wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        iTrade_wxFrame.__init__(self,parent, 'main')
        iTrade_wxLiveMixin.__init__(self)

        self.m_portfolio = portfolio
        self.m_matrix = matrix

        self.m_market = self.m_portfolio.market()
        self.m_connector = getDefaultLiveConnector(self.m_market,QLIST_INDICES)

        # link to other windows
        self.m_hOperation = None
        self.m_hMoney = None
        self.m_hAlerts = None
        self.m_hView = None
        self.m_hProperty = None
        self.m_hCurrency = None

        wx.EVT_CLOSE(self, self.OnCloseWindow)
        wx.EVT_WINDOW_DESTROY(self, self.OnDestroyWindow)

        # Set Lang then buildMenu
        self.SetLang(bDuringInit=True)
        self.buildMenu()

        # create an image list
        self.m_imagelist = wx.ImageList(16,16)

        self.idx_nochange = self.m_imagelist.Add(wx.Bitmap('res/nochange.png'))
        self.idx_up = self.m_imagelist.Add(wx.Bitmap('res/up.png'))
        self.idx_down = self.m_imagelist.Add(wx.Bitmap('res/down.png'))
        self.idx_tbref = self.m_imagelist.Add(wx.Bitmap('res/invalid.png'))
        self.idx_buy = self.m_imagelist.Add(wx.Bitmap('res/buy.png'))
        self.idx_sell = self.m_imagelist.Add(wx.Bitmap('res/sell.png'))
        self.idx_noop = self.m_imagelist.Add(wx.Bitmap('res/noop.png'))

        self.sm_up = self.m_imagelist.Add(wx.Bitmap('res/sm_up.png'))
        self.sm_dn = self.m_imagelist.Add(wx.Bitmap('res/sm_down.png'))

        # List
        tID = wx.NewId()

        self.m_list = iTradeMatrixListCtrl(self, tID,
                                 style = wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_SINGLE_SEL | wx.LC_VRULES | wx.LC_HRULES)
        wx.EVT_LIST_ITEM_ACTIVATED(self, tID, self.OnItemActivated)
        wx.EVT_LIST_ITEM_SELECTED(self, tID, self.OnItemSelected)
        wx.EVT_COMMAND_RIGHT_CLICK(self.m_list, tID, self.OnRightClick)
        wx.EVT_RIGHT_UP(self.m_list, self.OnRightClick)
        wx.EVT_RIGHT_DOWN(self.m_list, self.OnRightDown)
        wx.EVT_LEFT_DOWN(self.m_list, self.OnLeftDown)

        self.m_list.SetImageList(self.m_imagelist, wx.IMAGE_LIST_SMALL)
        self.m_list.SetFont(FontFromSize(itrade_config.matrixFontSize))

        # Now that the list exists we can init the other base class,
        # see wxPython/lib/mixins/listctrl.py
        wxl.ColumnSorterMixin.__init__(self, IDC_LAST+1)

        # Toolbar
        self.m_toolbar = iTradeMainToolbar(self, wx.NewId())

        # default list is quotes
        self.m_listmode = LISTMODE_INIT

        wx.EVT_SIZE(self, self.OnSize)

        EVT_UPDATE_LIVE(self, self.OnLive)

        # refresh full view after window init finished
        EVT_POSTINIT(self, self.OnPostInit)
        wx.PostEvent(self,PostInitEvent())

        self.Show(True)

    # --- [ Menus ] ----------------------------------------------------------------

    def buildMenu(self):
        # the main menu
        self.filemenu = wx.Menu()
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

        self.matrixmenu = wx.Menu()
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

        self.quotemenu = wx.Menu()
        self.quotemenu.Append(ID_ADD_QUOTE, message('main_quote_add'),message('main_quote_desc_add'))
        self.quotemenu.Append(ID_REMOVE_QUOTE, message('main_quote_remove'),message('main_quote_desc_add'))
        self.quotemenu.AppendSeparator()
        self.quotemenu.Append(ID_GRAPH_QUOTE, message('main_quote_graph'),message('main_quote_desc_graph'))
        self.quotemenu.Append(ID_LIVE_QUOTE, message('main_quote_live'),message('main_quote_desc_live'))
        self.quotemenu.AppendSeparator()
        self.quotemenu.Append(ID_PROPERTY_QUOTE, message('main_quote_property'),message('main_quote_desc_property'))

        self.viewmenu = wx.Menu()
        self.viewmenu.Append(ID_OPERATIONS, message('main_view_operations'),message('main_view_desc_operations'))
        self.viewmenu.Append(ID_MONEY, message('main_view_money'),message('main_view_desc_money'))
        self.viewmenu.AppendSeparator()
        self.viewmenu.Append(ID_CURRENCIES, message('main_view_currencies'),message('main_view_desc_currencies'))
        self.viewmenu.Append(ID_ALERTS, message('main_view_alerts'),message('main_view_desc_alerts'))
        self.viewmenu.AppendSeparator()
        self.viewmenu.Append(ID_COMPUTE, message('main_view_compute'),message('main_view_desc_compute'))

        self.optionsmenu = wx.Menu()
        self.accessmenu = wx.Menu()

        ncon = 0
        for aname,acon in listLoginConnector():
            self.accessmenu.Append(ID_ACCESS+ncon+1, acon.name(), acon.desc())
            ncon = ncon + 1
        self.optionsmenu.AppendMenu(ID_ACCESS,message('main_options_access'),self.accessmenu,message('main_options_desc_access'))

        self.langmenu = wx.Menu()
        self.langmenu.AppendRadioItem(ID_LANG_SYSTEM, message('main_options_lang_default'),message('main_options_lang_default'))
        self.langmenu.AppendRadioItem(ID_LANG_ENGLISH, message('main_options_lang_english'),message('main_options_lang_english'))
        self.langmenu.AppendRadioItem(ID_LANG_FRENCH, message('main_options_lang_french'),message('main_options_lang_french'))
        self.langmenu.AppendRadioItem(ID_LANG_PORTUGUESE, message('main_options_lang_portuguese'),message('main_options_lang_portuguese'))
        self.langmenu.AppendRadioItem(ID_LANG_DEUTCH, message('main_options_lang_deutch'),message('main_options_lang_deutch'))
        self.optionsmenu.AppendMenu(ID_LANG,message('main_options_lang'),self.langmenu,message('main_options_desc_lang'))
        if itrade_config.lang == 255:
            self.optionsmenu.Enable(ID_LANG,False)

        self.cachemenu = wx.Menu()
        self.cachemenu.Append(ID_CACHE_ERASE_DATA, message('main_cache_erase_data'),message('main_cache_desc_erase_data'))
        self.cachemenu.Append(ID_CACHE_ERASE_NEWS, message('main_cache_erase_news'),message('main_cache_desc_erase_news'))
        self.cachemenu.AppendSeparator()
        self.cachemenu.Append(ID_CACHE_ERASE_ALL, message('main_cache_erase_all'),message('main_cache_desc_erase_all'))
        self.optionsmenu.AppendMenu(ID_CACHE,message('main_options_cache'),self.cachemenu,message('main_options_desc_cache'))

        self.helpmenu = wx.Menu()
        self.helpmenu.Append(ID_CONTENT, message('main_help_contents'),message('main_help_desc_contents'))
        self.helpmenu.AppendSeparator()
        self.helpmenu.Append(ID_SUPPORT, message('main_help_support'),message('main_help_desc_support'))
        self.helpmenu.Append(ID_BUG, message('main_help_bugs'),message('main_help_desc_bugs'))
        self.helpmenu.Append(ID_FORUM, message('main_help_forum'),message('main_help_desc_forum'))
        self.helpmenu.Append(ID_DONORS, message('main_help_donors'),message('main_help_desc_donors'))
        self.helpmenu.AppendSeparator()
        self.helpmenu.Append(ID_ABOUT, message('main_about'), message('main_desc_about'))

        # Creating the menubar
        menuBar = wx.MenuBar()

        # Adding the "filemenu" to the MenuBar
        menuBar.Append(self.filemenu,message('main_file'))
        menuBar.Append(self.matrixmenu,message('main_matrix'))
        menuBar.Append(self.viewmenu,message('main_view'))
        menuBar.Append(self.quotemenu,message('main_quote'))
        menuBar.Append(self.optionsmenu,message('main_options'))
        menuBar.Append(self.helpmenu,message('main_help'))

        # Adding the MenuBar to the Frame content
        self.SetMenuBar(menuBar)

        wx.EVT_MENU(self, ID_OPEN, self.OnOpen)
        wx.EVT_MENU(self, ID_NEW, self.OnNew)
        wx.EVT_MENU(self, ID_DELETE, self.OnDelete)
        wx.EVT_MENU(self, ID_SAVE, self.OnSave)
        wx.EVT_MENU(self, ID_SAVEAS, self.OnSaveAs)
        wx.EVT_MENU(self, ID_EDIT, self.OnEdit)
        wx.EVT_MENU(self, ID_MANAGELIST, self.OnManageList)
        wx.EVT_MENU(self, ID_EXIT, self.OnExit)
        wx.EVT_MENU(self, ID_SUPPORT, self.OnSupport)
        wx.EVT_MENU(self, ID_CONTENT, self.OnContent)
        wx.EVT_MENU(self, ID_BUG, self.OnBug)
        wx.EVT_MENU(self, ID_FORUM, self.OnForum)
        wx.EVT_MENU(self, ID_DONORS, self.OnDonors)
        wx.EVT_MENU(self, ID_PORTFOLIO, self.OnPortfolio)
        wx.EVT_MENU(self, ID_QUOTES, self.OnQuotes)
        wx.EVT_MENU(self, ID_STOPS, self.OnStops)
        wx.EVT_MENU(self, ID_INDICATORS, self.OnIndicators)
        wx.EVT_MENU(self, ID_OPERATIONS, self.OnOperations)
        wx.EVT_MENU(self, ID_MONEY, self.OnMoney)
        wx.EVT_MENU(self, ID_COMPUTE, self.OnCompute)
        wx.EVT_MENU(self, ID_ALERTS, self.OnAlerts)
        wx.EVT_MENU(self, ID_CURRENCIES, self.OnCurrencies)

        wx.EVT_MENU(self, ID_ADD_QUOTE, self.OnAddQuote)
        wx.EVT_MENU(self, ID_REMOVE_QUOTE, self.OnRemoveCurrentQuote)
        wx.EVT_MENU(self, ID_GRAPH_QUOTE, self.OnGraphQuote)
        wx.EVT_MENU(self, ID_LIVE_QUOTE, self.OnLiveQuote)
        wx.EVT_MENU(self, ID_PROPERTY_QUOTE, self.OnPropertyQuote)

        wx.EVT_MENU(self, ID_SMALL_VIEW, self.OnViewSmall)
        wx.EVT_MENU(self, ID_NORMAL_VIEW, self.OnViewNormal)
        wx.EVT_MENU(self, ID_BIG_VIEW, self.OnViewBig)

        for i in range(0,ncon):
            wx.EVT_MENU(self, ID_ACCESS+i+1, self.OnAccess)

        wx.EVT_MENU(self, ID_LANG_SYSTEM, self.OnLangDefault)
        wx.EVT_MENU(self, ID_LANG_ENGLISH, self.OnLangEnglish)
        wx.EVT_MENU(self, ID_LANG_FRENCH, self.OnLangFrench)
        wx.EVT_MENU(self, ID_LANG_PORTUGUESE, self.OnLangPortuguese)
        wx.EVT_MENU(self, ID_LANG_DEUTCH, self.OnLangDeutch)

        wx.EVT_MENU(self, ID_CACHE_ERASE_DATA, self.OnCacheEraseData)
        wx.EVT_MENU(self, ID_CACHE_ERASE_NEWS, self.OnCacheEraseNews)
        wx.EVT_MENU(self, ID_CACHE_ERASE_ALL, self.OnCacheEraseAll)

        wx.EVT_MENU(self, ID_REFRESH, self.OnRefresh)
        wx.EVT_MENU(self, ID_AUTOREFRESH, self.OnAutoRefresh)
        wx.EVT_MENU(self, ID_ABOUT, self.OnAbout)

    # --- [ wxl.ColumnSorterMixin management ] -------------------------------------

    # Used by the wxl.ColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.m_list

    # Used by the wxl.ColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)

    def getQuoteAndItemOnTheLine(self,x):
        key = self.m_list.GetItemData(x)
        #print 'line:%d -> key=%d quote=%s' % (x,key,self.itemQuoteMap[key].ticker())
        quote = self.itemQuoteMap[key]
        item = self.m_list.GetItem(x)
        return quote,item

    def openCurrentQuote(self,page=1):
        quote,item = self.getQuoteAndItemOnTheLine(self.m_currentItem)
        if page==7:
            open_iTradeQuoteProperty(self,self.m_portfolio,quote)
        else:
            open_iTradeQuote(self,self.m_portfolio,quote,page)

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
        if self.m_hProperty:
            self.m_hProperty.Close()
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
                # can be long ...
                wx.SetCursor(wx.HOURGLASS_CURSOR)
                self.stopLive(bBusy=False)

                dp = loadPortfolio(dp.filename())
                self.NewContext(dp)

    def NewContext(self,dp):
        # can be long ...
        wx.SetCursor(wx.HOURGLASS_CURSOR)

        # close links
        self.CloseLinks()

        # change portfolio
        self.m_portfolio = dp

        self.m_matrix = createMatrix(dp.filename(),dp)
        self.m_market = self.m_portfolio.market()
        self.m_connector = getDefaultLiveConnector(self.m_market,QLIST_INDICES)

        # should be enough !
        wx.SetCursor(wx.STANDARD_CURSOR)

        # populate current view and refresh
        self.OnPostInit(None)

    def OnNew(self,e):
        if self.manageDirty(message('main_save_matrix_data'),fnt='open'):
            dp = properties_iTradePortfolio(self,None,'create')
            if dp:
                self.NewContext(dp)
                self.setDirty()

    def OnEdit(self,e):
        dp = properties_iTradePortfolio(self,self.m_portfolio,'edit')
        if dp:
            self.NewContext(dp)
            self.setDirty()

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
        self.m_portfolio.saveStops()
        itrade_config.saveConfig()
        self.saveConfig()
        self.clearDirty()

    def OnSupport(self,e):
        id = getLang()
        if itrade_config.supportURL.has_key(id):
            url = itrade_config.supportURL[id]
        else:
            url = itrade_config.supportURL['en']
        iTradeLaunchBrowser(url,new=True)

    def OnContent(self,e):
        id = getLang()
        if itrade_config.manualURL.has_key(id):
            url = itrade_config.manualURL[id]
        else:
            url = itrade_config.manualURL['en']
        iTradeLaunchBrowser(url,new=True)

    def OnBug(self,e):
        iTradeLaunchBrowser(itrade_config.bugTrackerURL,new=True)

    def OnForum(self,e):
        iTradeLaunchBrowser(itrade_config.forumURL,new=True)

    def OnDonors(self,e):
        iTradeLaunchBrowser(itrade_config.donorsTrackerURL,new=True)

    def OnManageList(self,e):
        list_iTradeQuote(self,self.m_portfolio.market())

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

        if itrade_config.lang != 255:
            m = self.langmenu.FindItemById(ID_LANG_SYSTEM)
            m.Check(itrade_config.lang==0)

            m = self.langmenu.FindItemById(ID_LANG_ENGLISH)
            m.Check(itrade_config.lang==1)

            m = self.langmenu.FindItemById(ID_LANG_FRENCH)
            m.Check(itrade_config.lang==2)

            m = self.langmenu.FindItemById(ID_LANG_PORTUGUESE)
            m.Check(itrade_config.lang==3)

            m = self.langmenu.FindItemById(ID_LANG_DEUTCH)
            m.Check(itrade_config.lang==4)

        # refresh Enable state based on current View
        m = self.quotemenu.FindItemById(ID_ADD_QUOTE)
        m.Enable(self.m_listmode == LISTMODE_QUOTES)

    def updateQuoteItems(self):
        op1 = (self.m_currentItem>=0) and (self.m_currentItem<self.m_maxlines)
        if op1:
            quote,item = self.getQuoteAndItemOnTheLine(self.m_currentItem)
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
            quote,item = self.getQuoteAndItemOnTheLine(self.m_currentItem)
        else:
            quote = None
        open_iTradeMoney(self,0,self.m_portfolio,quote)

    def OnCompute(self,e):
        if self.m_currentItem>=0:
            quote,item = self.getQuoteAndItemOnTheLine(self.m_currentItem)
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
            self.openCurrentQuote(page=1)

    def OnLiveQuote(self,e):
        if self.m_currentItem>=0:
            debug("OnLiveQuote: %s" % self.m_list.GetItemText(self.m_currentItem))
            self.openCurrentQuote(page=2)

    def OnPropertyQuote(self,e):
        if self.m_currentItem>=0:
            debug("OnPropertyQuote: %s" % self.m_list.GetItemText(self.m_currentItem))
            self.openCurrentQuote(page=7)

    # --- [ Text font size management ] -------------------------------------

    def OnChangeViewText(self):
        itrade_config.saveConfig()
        self.updateCheckItems()
        self.m_list.SetFont(FontFromSize(itrade_config.matrixFontSize))
        for i in range(0,IDC_LAST+1):
            self.m_list.SetColumnWidth(i, wx.LIST_AUTOSIZE)

    def OnViewSmall(self,e):
        itrade_config.matrixFontSize = 1
        self.OnChangeViewText()

    def OnViewNormal(self,e):
        itrade_config.matrixFontSize = 2
        self.OnChangeViewText()

    def OnViewBig(self,e):
        itrade_config.matrixFontSize = 3
        self.OnChangeViewText()

    # --- [ Access management ] -------------------------------------

    def OnAccess(self,e):
        # get the connector
        m = self.accessmenu.FindItemById(e.GetId())
        m = m.GetText()
        c = getLoginConnector(m)
        if c:
            # with the connector, load user info and open UI
            u,p = c.loadUserInfo()
            u,p = login_UI(self,u,p,c)

            # now, save new user info
            wx.SetCursor(wx.HOURGLASS_CURSOR)
            c.saveUserInfo(u,p)
            if itrade_config.isConnected():
                # and apply these ne login info
                c.login(u,p)
            wx.SetCursor(wx.STANDARD_CURSOR)

    # --- [ Language management ] -------------------------------------

    def SetLang(self,bDuringInit=False):

        if itrade_config.lang==1:
            lang = 'us'
        elif itrade_config.lang==2:
            lang = 'fr'
        elif itrade_config.lang==3:
            lang = 'pt'
        elif itrade_config.lang==4:
            lang = 'de'
        elif itrade_config.lang==0:
            lang = gMessage.getAutoDetectedLang('us')
        else:
            # has been forced by the command line
            lang = gMessage.getLang()

        if lang != gMessage.getLang():
            gMessage.setLang(lang)
            gMessage.load()

            if not bDuringInit:
                # restore everything with the new lang
                self.CloseLinks()
                self.buildMenu()
                self.m_toolbar._init_toolbar()
                self.RebuildList()

        if not bDuringInit:
            self.updateCheckItems()

    def OnChangeLang(self):
        itrade_config.saveConfig()
        self.SetLang()

    def OnLangDefault(self,e):
        itrade_config.lang = 0
        self.OnChangeLang()

    def OnLangEnglish(self,e):
        itrade_config.lang = 1
        self.OnChangeLang()

    def OnLangFrench(self,e):
        itrade_config.lang = 2
        self.OnChangeLang()

    def OnLangPortuguese(self,e):
        itrade_config.lang = 3
        self.OnChangeLang()

    def OnLangDeutch(self,e):
        itrade_config.lang = 4
        self.OnChangeLang()

    # --- [ cache management ] -------------------------------------

    def OnCacheEraseData(self,e):
        #__xdlg = wx.MessageDialog(self, message('cache_erase_confirm_data'), message('cache_erase_confirm_title'), wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
        #__xidRet = dlg.ShowModal()
        #__xdlg.Destroy()
        idRet = iTradeYesNo(self, message('cache_erase_confirm_data'), message('cache_erase_confirm_title'))
        if idRet == wx.ID_YES:
            self.m_matrix.flushTrades()

    def OnCacheEraseNews(self,e):
        #__xdlg = wx.MessageDialog(self, message('cache_erase_confirm_news'), message('cache_erase_confirm_title'), wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
        #__xidRet = dlg.ShowModal()
        #__xdlg.Destroy()
        idRet = iTradeYesNo(self, message('cache_erase_confirm_news'), message('cache_erase_confirm_title'))
        if idRet == wx.ID_YES:
            self.m_matrix.flushNews()

    def OnCacheEraseAll(self,e):
        #__xdlg = wx.MessageDialog(self, message('cache_erase_confirm_all'), message('cache_erase_confirm_title'), wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
        #__xidRet = dlg.ShowModal()
        #__xdlg.Destroy()
        idRet = iTradeYesNo(self, message('cache_erase_confirm_all'), message('cache_erase_confirm_title'))
        if idRet == wx.ID_YES:
            self.m_matrix.flushAll()

    # --- [ autorefresh management ] -------------------------------------

    def OnAutoRefresh(self,e):
        itrade_config.bAutoRefreshMatrixView = not itrade_config.bAutoRefreshMatrixView
        itrade_config.saveConfig()
        self.updateCheckItems()
        self.m_toolbar.ClearIndicator()
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
                        #debug('%s: %s' % (evt.quote.key(),evt.param))
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
                        debug('%s: %s - bad : other view' % (evt.quote.key(),evt.param))
        else:
            debug('%s: %s - bad : not running' % (evt.quote.key(),evt.param))

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
            dlg = wx.ProgressDialog(message('currency_refreshing'),"",max,self,wx.PD_CAN_ABORT | wx.PD_APP_MODAL)
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
            item.SetTextColour(wx.BLACK)
            item.SetImage(self.idx_tbref)
        elif color == QUOTE_RED:
            item.SetTextColour(wx.RED)
            item.SetImage(self.idx_down)
        elif color == QUOTE_GREEN:
            item.SetTextColour(wx.BLUE)
            item.SetImage(self.idx_up)
        else:
            item.SetTextColour(wx.BLACK)
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
        self.m_list.SetColumnWidth(IDC_PV, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PR, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PROFIT, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PERCENT, wx.LIST_AUTOSIZE)

    def refreshQuoteLine(self,x,disp):
        quote,item = self.getQuoteAndItemOnTheLine(x)

        # refresh line text
        if disp:
            self.m_list.SetStringItem(x,IDC_PREV,quote.sv_prevclose())
            self.m_list.SetStringItem(x,IDC_CLOSE,quote.sv_close(bDispCurrency=True))
            self.m_list.SetStringItem(x,IDC_PERCENT,quote.sv_percent())
            if quote.hasTraded():
                self.m_list.SetStringItem(x,IDC_OPEN,quote.sv_open())
                self.m_list.SetStringItem(x,IDC_HIGH,quote.sv_high())
                self.m_list.SetStringItem(x,IDC_LOW,quote.sv_low())
                self.m_list.SetStringItem(x,IDC_PIVOTS,quote.sv_pivots())
                self.m_list.SetStringItem(x,IDC_VOLUME,quote.sv_volume())
                color = quote.colorTrend()
            else:
                # not already opened today ...
                self.m_list.SetStringItem(x,IDC_OPEN," ---.-- ")
                self.m_list.SetStringItem(x,IDC_HIGH," ---.-- ")
                self.m_list.SetStringItem(x,IDC_LOW," ---.-- ")
                self.m_list.SetStringItem(x,IDC_PIVOTS," --- (-.--) ")
                self.m_list.SetStringItem(x,IDC_VOLUME," ---------- ")
                color = QUOTE_NOCHANGE
        else:
            self.m_list.SetStringItem(x,IDC_PREV," ---.-- ")
            self.m_list.SetStringItem(x,IDC_CLOSE," ---.-- %s" % quote.currency_symbol())
            self.m_list.SetStringItem(x,IDC_OPEN," ---.-- ")
            self.m_list.SetStringItem(x,IDC_HIGH," ---.-- ")
            self.m_list.SetStringItem(x,IDC_LOW," ---.-- ")
            self.m_list.SetStringItem(x,IDC_PIVOTS," --- (-.--) ")
            self.m_list.SetStringItem(x,IDC_VOLUME," ---------- ")
            self.m_list.SetStringItem(x,IDC_PERCENT," ---.-- %")
            color = QUOTE_INVALID

        self.refreshColorLine(x,color)

        # enough space for data ?
        self.m_list.SetColumnWidth(IDC_VOLUME, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PREV, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_OPEN, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_HIGH, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_LOW, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PIVOTS, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_CLOSE, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PERCENT, wx.LIST_AUTOSIZE)

    def refreshQuotes(self):
        x = 0
        lst = self.m_matrix.list()
        max = len(lst)
        keepGoing = True
        if self.hasFocus():
            dlg = wx.ProgressDialog(message('main_refreshing'),"",max,self,wx.PD_CAN_ABORT | wx.PD_APP_MODAL)
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
        quote,item = self.getQuoteAndItemOnTheLine(x)
        if quote==None: return
        xtype = self.itemTypeMap[self.m_list.GetItemData(x)]

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
                item.SetTextColour(wx.RED)
            else:
                item.SetImage(self.idx_up)
                item.SetTextColour(wx.BLUE)
        else:
            item.SetTextColour(wx.BLACK)
            item.SetImage(self.idx_tbref)
            self.m_list.SetStringItem(x,IDC_PVU," ---.-- ")
            self.m_list.SetStringItem(x,IDC_PERFDAY," ---.-- % ")
            self.m_list.SetStringItem(x,IDC_PV," ---.-- %s" % self.m_portfolio.currency_symbol())
            self.m_list.SetStringItem(x,IDC_PROFIT," ----.-- %s" % self.m_portfolio.currency_symbol())
            self.m_list.SetStringItem(x,IDC_PERCENT," ---.-- % ")

        self.m_list.SetItem(item)

        self.m_list.SetColumnWidth(IDC_PVU, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PERFDAY, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PV, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PROFIT, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PERCENT, wx.LIST_AUTOSIZE)

    def refreshPortfolio(self):
        x = 0
        lst = self.m_matrix.list()
        max = len(lst)
        keepGoing = True
        if self.hasFocus():
            dlg = wx.ProgressDialog(message('main_refreshing'),"",max,self,wx.PD_CAN_ABORT | wx.PD_APP_MODAL)
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
        quote,item = self.getQuoteAndItemOnTheLine(x)

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
            item.SetTextColour(wx.BLACK)
            item.SetImage(self.idx_tbref)
        elif color == QUOTE_RED:
            item.SetTextColour(wx.RED)
            item.SetImage(self.idx_sell)
        elif color == QUOTE_GREEN:
            item.SetTextColour(wx.BLUE)
            item.SetImage(self.idx_buy)
        else:
            item.SetTextColour(wx.BLACK)
            item.SetImage(self.idx_noop)

        self.m_list.SetItem(item)
        self.m_list.SetColumnWidth(IDC_CURRENT, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PV, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PROFIT, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PERCENT, wx.LIST_AUTOSIZE)

    def refreshStops(self):
        x = 0
        lst = self.m_matrix.list()
        max = len(lst)
        keepGoing = True
        if self.hasFocus():
            dlg = wx.ProgressDialog(message('main_refreshing'),"",max,self,wx.PD_CAN_ABORT | wx.PD_APP_MODAL)
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
        quote,item = self.getQuoteAndItemOnTheLine(x)

        if disp:
            self.m_list.SetStringItem(x,IDC_LAST,quote.sv_close(bDispCurrency=True))
            if quote.hasTraded():
                color = quote.colorTrend()
            else:
                color = QUOTE_NOCHANGE
            self.m_list.SetStringItem(x,IDC_MA20,quote.sv_ma(20))
            self.m_list.SetStringItem(x,IDC_MA50,quote.sv_ma(50))
            self.m_list.SetStringItem(x,IDC_MA100,quote.sv_ma(100))
            self.m_list.SetStringItem(x,IDC_RSI,quote.sv_rsi(14))
            self.m_list.SetStringItem(x,IDC_STOCH,'%s (%s)' % (quote.sv_stoK(),quote.sv_stoD()))
        else:
            # no information
            self.m_list.SetStringItem(x,IDC_MA20," ---.--- ")
            self.m_list.SetStringItem(x,IDC_MA50," ---.--- ")
            self.m_list.SetStringItem(x,IDC_MA100," ---.--- ")
            self.m_list.SetStringItem(x,IDC_RSI," ---.--- ")
            self.m_list.SetStringItem(x,IDC_MACD," ---.--- ")
            self.m_list.SetStringItem(x,IDC_STOCH," ---.-- (---.--) ")
            self.m_list.SetStringItem(x,IDC_DMI," ---.-- ")
            self.m_list.SetStringItem(x,IDC_EMV," ---.-- ")
            self.m_list.SetStringItem(x,IDC_OVB," ------ ")
            self.m_list.SetStringItem(x,IDC_LAST," ---.-- %s" % quote.currency_symbol())
            color = QUOTE_NOCHANGE

        # update line color and icon
        item = self.m_list.GetItem(x)
        if color == QUOTE_INVALID:
            item.SetTextColour(wx.BLACK)
            item.SetImage(self.idx_tbref)
        elif color == QUOTE_RED:
            item.SetTextColour(wx.RED)
            item.SetImage(self.idx_down)
        elif color == QUOTE_GREEN:
            item.SetTextColour(wx.BLUE)
            item.SetImage(self.idx_up)
        else:
            item.SetTextColour(wx.BLACK)
            item.SetImage(self.idx_nochange)
        self.m_list.SetItem(item)

        # enough space for data ?
        self.m_list.SetColumnWidth(IDC_MA20, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_MA50, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_MA100, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_RSI, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_MACD, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_STOCH, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_DMI, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_EMV, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_OVB, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_LAST, wx.LIST_AUTOSIZE)

    def refreshIndicators(self):
        x = 0
        lst = self.m_matrix.list()
        max = len(lst)
        keepGoing = True
        if self.hasFocus():
            dlg = wx.ProgressDialog(message('main_refreshing'),"",max,self,wx.PD_CAN_ABORT | wx.PD_APP_MODAL)
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
        debug('populate duringinit=%d' % bDuringInit)

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
        self.m_list.InsertColumn(IDC_ISIN, message('isin'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_TICKER, message('ticker'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE_USEHEADER)

    def populateMatrixEnd(self):
        # fix the item data
        items = self.itemDataMap.items()
        for x in range(len(items)):
            key, data = items[x]
            self.m_list.SetItemData(x, key)

        # adjust column
        self.m_list.SetColumnWidth(IDC_ISIN, wx.LIST_AUTOSIZE_USEHEADER)
        self.m_list.SetColumnWidth(IDC_TICKER, wx.LIST_AUTOSIZE_USEHEADER)

        # default selection
        if len(items)>0:
            self.m_currentItem = 0
            self.m_list.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
            self.m_list.EnsureVisible(self.m_currentItem)
        else:
            self.m_currentItem = -1

    def populatePortfolio(self):
        self.populateMatrixBegin()

        self.m_list.InsertColumn(IDC_QTY, message('qty'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PRU, message('UPP'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PR, message('buy'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PVU, message('USP'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PERFDAY, message('perfday'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PV, message('sell'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PROFIT, message('profit'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PERCENT, message('perfper'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_NAME, message('name'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)

        x = 0
        for eachQuote in self.m_matrix.list():
            # in portfolio view, display only traded values !
            if eachQuote.isTraded():
                if eachQuote.nv_number(QUOTE_CASH)>0:
                    self.m_list.InsertImageStringItem(x, eachQuote.isin(), self.idx_tbref)
                    self.m_list.SetStringItem(x,IDC_TICKER,eachQuote.ticker())
                    self.m_list.SetStringItem(x,IDC_QTY,eachQuote.sv_number(QUOTE_CASH))
                    self.m_list.SetStringItem(x,IDC_PRU,"%s %s" % (eachQuote.sv_pru(QUOTE_CASH),self.m_portfolio.currency_symbol()))
                    self.m_list.SetStringItem(x,IDC_PR, eachQuote.sv_pr(QUOTE_CASH,fmt="%.0f",bDispCurrency=True))
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
                    self.m_list.SetStringItem(x,IDC_PR, eachQuote.sv_pr(QUOTE_CREDIT,bDispCurrency=True))
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
        self.m_list.SetColumnWidth(IDC_QTY, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PRU, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_PR, wx.LIST_AUTOSIZE)

        # finish populating
        self.populateMatrixEnd()

    def populateStops(self):
        self.populateMatrixBegin()

        self.m_list.InsertColumn(IDC_INVEST, message('buy'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_RISKM, message('risk'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_STOPLOSS, message('stop_minus'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_CURRENT, message('USP'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_STOPWIN, message('stop_plus'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PV, message('sell'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PROFIT, message('profit'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PERCENT, ' % ', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_NAME, message('name'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)

        x = 0
        for eachQuote in self.m_matrix.list():
            # in portfolio view, display only traded values !
            if eachQuote.hasStops() and (eachQuote.isTraded() or eachQuote.isMonitored()):
                self.m_list.InsertImageStringItem(x, eachQuote.isin(), self.idx_tbref)
                self.m_list.SetStringItem(x,IDC_TICKER,eachQuote.ticker())
                self.m_list.SetStringItem(x,IDC_INVEST, eachQuote.sv_pr(fmt="%.0f",bDispCurrency=True))
                self.m_list.SetStringItem(x,IDC_RISKM, eachQuote.sv_riskmoney(self.m_portfolio.currency(),self.m_portfolio.currency_symbol()))
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
        self.m_list.SetColumnWidth(IDC_INVEST, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_RISKM, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_STOPLOSS, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_STOPWIN, wx.LIST_AUTOSIZE)

        # finish populating
        self.populateMatrixEnd()

    def populateQuotes(self):
        self.populateMatrixBegin()

        self.m_list.InsertColumn(IDC_VOLUME, message('volume'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PREV, message('prev'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_OPEN, message('open'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_HIGH, message('high'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_LOW,  message('low'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_CLOSE,message('last'), wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PIVOTS,message('pivots'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PERCENT, ' % ', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_NAME, message('name'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)

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

        self.m_list.InsertColumn(IDC_MA20, 'MMA20', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_MA50, 'MMA50', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_MA100, 'MMA100', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_RSI, 'RSI (%s)'%14, wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_MACD, 'MACD', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_STOCH, 'STO %K (%D)', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_DMI, 'DMI', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_EMV, 'EMV', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_OVB, 'OVB', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_LAST, 'Last', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_LAST+1, '', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)

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
        #debug("OnRightDown: x, y = %s item=%d max=%d" % (str((self.x, self.y)), item,self.m_maxlines))
        if flags & wx.LIST_HITTEST_ONITEM:
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
        if flags & wx.LIST_HITTEST_ONITEM:
            pass
        else:
            self.m_currentItem = -1
        self.updateQuoteItems()
        event.Skip()

    def OnItemActivated(self, event):
        self.m_currentItem = event.m_itemIndex
        if (self.m_currentItem>=0) and (self.m_currentItem<self.m_maxlines):
            #debug("OnItemActivated: %s" % self.m_list.GetItemText(self.m_currentItem))
            self.openCurrentQuote()
            # __x if self.m_currentItem == self.m_maxlines, launch eval !

    def OnItemSelected(self, event):
        self.m_currentItem = event.m_itemIndex
        self.updateQuoteItems()
        if (self.m_currentItem>=0) and (self.m_currentItem<self.m_maxlines):
            #debug("OnItemSelected: %s, %s, %s, %s\n" %
            #                   (self.m_currentItem,
            #                    self.m_list.GetItemText(self.m_currentItem),
            #                    self.getColumnText(self.m_currentItem, 1),
            #                    self.getColumnText(self.m_currentItem, 2)))
            # __x if self.m_currentItem == self.m_maxlines, launch eval !
            pass
        event.Skip()

    def OnRightClick(self, event):
        if (self.m_currentItem<0) or (self.m_currentItem>=self.m_maxlines):
            # __x if self.m_currentItem == self.m_maxlines, launch eval !
            inList = False
        else:
            inList = True
            quote,item = self.getQuoteAndItemOnTheLine(self.m_currentItem)
            #debug("OnRightClick %s : %s\n" % (self.m_list.GetItemText(self.m_currentItem),quote))

        # only do this part the first time so the events are only bound once
        if not hasattr(self, "m_popupID_Update"):
            self.m_popupID_Update = wx.NewId()
            self.m_popupID_View = wx.NewId()
            self.m_popupID_Live = wx.NewId()
            self.m_popupID_Properties = wx.NewId()
            self.m_popupID_Add = wx.NewId()
            self.m_popupID_Remove = wx.NewId()
            self.m_popupID_Edit = wx.NewId()
            self.m_popupID_Buy = wx.NewId()
            self.m_popupID_Sell = wx.NewId()
            wx.EVT_MENU(self, self.m_popupID_Update, self.OnPopup_Update)
            wx.EVT_MENU(self, self.m_popupID_View, self.OnPopup_View)
            wx.EVT_MENU(self, self.m_popupID_Live, self.OnPopup_Live)
            wx.EVT_MENU(self, self.m_popupID_Properties, self.OnPopup_Properties)
            wx.EVT_MENU(self, self.m_popupID_Add, self.OnPopup_Add)
            wx.EVT_MENU(self, self.m_popupID_Edit, self.OnPopup_Edit)
            wx.EVT_MENU(self, self.m_popupID_Remove, self.OnPopup_Remove)
            wx.EVT_MENU(self, self.m_popupID_Buy, self.OnPopup_Buy)
            wx.EVT_MENU(self, self.m_popupID_Sell, self.OnPopup_Sell)

        # make a menu
        menu = wx.Menu()
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
            menu.Append(self.m_popupID_Add, message('main_popup_add_stops'))
            menu.AppendSeparator()
            menu.Append(self.m_popupID_Edit, message('main_popup_edit_stops'))
            menu.Enable(self.m_popupID_Edit,inList)
            menu.Append(self.m_popupID_Remove, message('main_popup_remove_stops'))
            menu.Enable(self.m_popupID_Remove,inList)
            menu.Enable(self.m_popupID_Add,True)
            if inList:
                menu.Enable(self.m_popupID_Edit,quote.hasStops())
                menu.Enable(self.m_popupID_Remove,quote.hasStops())
            else:
                menu.Enable(self.m_popupID_Edit,False)
                menu.Enable(self.m_popupID_Remove,False)

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu, wx.Point(self.x, self.y))
        menu.Destroy()

    def OnPopup_Update(self, event):
        debug("OnPopup_Update")
        self.OnRefresh(event)

    def OnPopup_View(self, event):
        debug("OnPopup_View")
        self.openCurrentQuote(page=1)

    def OnPopup_Live(self, event):
        debug("OnPopup_Live")
        self.openCurrentQuote(page=2)

    def OnPopup_Properties(self, event):
        debug("OnPopup_Properties")
        self.openCurrentQuote(page=7)

    def OnPopup_Add(self, event):
        #debug("OnPopup_Add")
        if self.m_listmode == LISTMODE_STOPS:
            self.OnAddStops(event)
        elif self.m_listmode == LISTMODE_QUOTES:
            self.OnAddQuote(event)

    def OnPopup_Edit(self, event):
        #debug("OnPopup_Edit")
        if self.m_listmode == LISTMODE_STOPS:
            self.OnEditStops(event)

    def OnPopup_Remove(self, event):
        #debug("OnPopup_Remove")
        if self.m_listmode == LISTMODE_STOPS:
            self.OnRemoveStops(event)
        elif self.m_listmode == LISTMODE_QUOTES:
            self.OnRemoveCurrentQuote(event)

    def OnPopup_Buy(self, event):
        debug("OnPopup_Buy")

    def OnPopup_Sell(self, event):
        debug("OnPopup_Sell")

    # ---[ Quotes ] -----------------------------------------

    def OnAddQuote(self,e):
        quote = addInMatrix_iTradeQuote(self,self.m_matrix,self.m_portfolio)
        if quote:
            self.m_portfolio.setupCurrencies()
            self.m_portfolio.loginToServices(quote)
            self.setDirty()
            self.m_listmode = LISTMODE_INIT
            self.OnQuotes(e)

    def OnRemoveCurrentQuote(self,e):
        quote,item = self.getQuoteAndItemOnTheLine(self.m_currentItem)
        if removeFromMatrix_iTradeQuote(self,self.m_matrix,quote):
            self.m_portfolio.setupCurrencies()
            self.setDirty()
            self.m_listmode = LISTMODE_INIT
            self.OnQuotes(e)

    # ---[ Stops ] -----------------------------------------

    def OnAddStops(self,e):
        if addOrEditStops_iTradeQuote(self,None,bAdd=True):
            self.setDirty()
            self.m_listmode = LISTMODE_INIT
            self.OnStops(e)

    def OnRemoveStops(self,e):
        quote,item = self.getQuoteAndItemOnTheLine(self.m_currentItem)
        if removeStops_iTradeQuote(self,quote):
            self.setDirty()
            self.m_listmode = LISTMODE_INIT
            self.OnStops(e)

    def OnEditStops(self,e):
        quote,item = self.getQuoteAndItemOnTheLine(self.m_currentItem)
        print 'OnEditStops:',quote,item,self.m_currentItem
        if addOrEditStops_iTradeQuote(self,quote,bAdd=False):
            self.setDirty()
            self.m_listmode = LISTMODE_INIT
            self.OnStops(e)

# ============================================================================
# That's all folks !
# ============================================================================
