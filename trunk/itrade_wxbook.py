#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxbook.py
#
# Description: wxPython Notebook for the Matrix
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is	Gilles Dumortier.
#
# Portions created by the Initial Developer are Copyright (C) 2004-2008 the
# Initial Developer. All Rights Reserved.
#
# Contributor(s):
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
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
# 2007-01-2x    dgil  Notebook re-architecture -> itrade_wxbook.py
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
#import logging

# wxPython system
import wx
#import wx.lib.mixins.listctrl as wxl

# iTrade system
import itrade_config
import time
from itrade_logging import *
from itrade_local import message,gMessage,getLang
from itrade_portfolio import loadPortfolio,OPERATION_BUY,OPERATION_SELL
from itrade_matrix import *
from itrade_quotes import *
from itrade_defs import *
from itrade_ext import *
from itrade_login import *

# iTrade wx system
if not itrade_config.nowxversion:
    import itrade_wxversion
from itrade_wxquote import open_iTradeQuote,addInMatrix_iTradeQuote,removeFromMatrix_iTradeQuote
from itrade_wxpropquote import open_iTradeQuoteProperty
from itrade_wxportfolio import select_iTradePortfolio,properties_iTradePortfolio
from itrade_wxoperations import open_iTradeOperations,add_iTradeOperation
from itrade_wxmoney import open_iTradeMoney
from itrade_wxalerts import open_iTradeAlerts
from itrade_wxcurrency import open_iTradeCurrencies
from itrade_wxabout import iTradeAboutBox
from itrade_wxhtml import iTradeLaunchBrowser
from itrade_wxlistquote import list_iTradeQuote
#from itrade_wxlogin import login_UI
from itrade_wxconnection import connection_UI
from itrade_wxstops import addOrEditStops_iTradeQuote,removeStops_iTradeQuote
from itrade_wxmixin import iTrade_wxFrame
from itrade_wxconvert import open_iTradeConverter

from itrade_wxpanes import iTrade_MatrixPortfolioPanel,iTrade_MatrixQuotesPanel,iTrade_MatrixStopsPanel,iTrade_MatrixIndicatorsPanel,iTrade_TradingPanel
from itrade_wxmoney import iTradeEvaluationPanel
from itrade_wxutil import iTradeYesNo,iTradeInformation,iTradeError,FontFromSize
from itrade_market import date_format

# ============================================================================
# menu identifier
# ============================================================================

#ID_OPEN = 100
#ID_NEW = 101
#ID_DELETE = 102
#ID_SAVEAS = 103
#ID_EDIT = 104

ID_MANAGELIST = 110

#ID_EXIT = 150

ID_QUOTES = 200
ID_PORTFOLIO = 201
ID_STOPS = 202
ID_INDICATORS = 203

ID_OPERATIONS = 210
ID_TRADING = 211
ID_EVALUATION = 212
ID_CURRENCIES = 213
ID_ALERTS = 214

ID_COMPUTE = 221
ID_CONVERT = 222

ID_SMALL_VIEW = 230
ID_NORMAL_VIEW = 231
ID_BIG_VIEW = 232

#ID_REFRESH = 240
ID_AUTOREFRESH = 241
ID_AUTOSIZE = 242

ID_ADD_QUOTE = 300
ID_REMOVE_QUOTE = 301
ID_GRAPH_QUOTE = 310
ID_LIVE_QUOTE = 311
#ID_INTRADAY_QUOTE = 312
#ID_NEWS_QUOTE = 313
#ID_TABLE_QUOTE = 314
#ID_ANALYSIS_QUOTE = 315
ID_BUY_QUOTE = 320
ID_SELL_QUOTE = 321
ID_PROPERTY_QUOTE = 330

ID_ACCESS = 350
# ... free up 399

ID_LANG = 399
ID_LANG_FIRST = 400
#ID_LANG_SYSTEM = 400
#ID_LANG_ENGLISH = 401
#ID_LANG_FRENCH = 402
#ID_LANG_PORTUGUESE = 403
#ID_LANG_GERMAN = 404
#ID_LANG_ITALIAN = 405
ID_LANG_LAST = 405

# Since "A MenuItem ID of Zero does not work under Mac" and wx.LANGUAGE_DEFAULT=0
# use an offset for this language selection submenu
ID_MAC_OFFSET = 1

ID_CACHE = 499
ID_CACHE_ERASE_DATA = 500
ID_CACHE_ERASE_NEWS = 501
ID_CACHE_ERASE_ALL = 510

ID_CONNEXION = 599

#ID_HELP_CONTENTS = 800
ID_SUPPORT = 801
ID_BUG = 802
ID_FORUM = 803
ID_DONORS = 804
ID_CHECKSOFTWARE = 805
#ID_ABOUT = 810

# ============================================================================
# Notebook Page identifier
# ============================================================================

ID_PAGE_QUOTES = 0
ID_PAGE_PORTFOLIO = 1
ID_PAGE_STOPS = 2
ID_PAGE_INDICATORS = 3
ID_PAGE_TRADING = 4
ID_PAGE_EVALUATION = 5

# ============================================================================
# iTradeMainToolbar
#
# ============================================================================

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
        self._NTB2_SAVE_AS = wx.NewId()
        self._NTB2_MONEY = wx.NewId()
        self._NTB2_CURRENCIES = wx.NewId()
        self._NTB2_OPERATIONS = wx.NewId()
        self._NTB2_ALERTS = wx.NewId()
        self._NTB2_QUOTE = wx.NewId()
        self._NTB2_REFRESH = wx.NewId()
        self._NTB2_AUTOSIZE = wx.NewId()
        self._NTB2_ABOUT = wx.NewId()

        self.SetToolBitmapSize(wx.Size(24,24))
        self.AddSimpleTool(self._NTB2_EXIT, wx.ArtProvider.GetBitmap(wx.ART_CROSS_MARK, wx.ART_TOOLBAR),
                           message('main_exit'), message('main_desc_exit'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_NEW, wx.ArtProvider.GetBitmap(wx.ART_NEW, wx.ART_TOOLBAR),
                           message('main_new'), message('main_desc_new'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_OPEN, wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR),
                           message('main_open'), message('main_desc_open'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_EDIT, wx.ArtProvider.GetBitmap(wx.ART_EXECUTABLE_FILE, wx.ART_TOOLBAR),
                           message('main_edit'), message('main_desc_edit'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_OPERATIONS, wx.ArtProvider.GetBitmap(wx.ART_REPORT_VIEW, wx.ART_TOOLBAR),
                           message('main_view_operations'), message('main_view_desc_operations'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_MONEY, wx.Bitmap(os.path.join(itrade_config.dirRes, 'money.png')),
                           message('main_view_money'), message('main_view_desc_money'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_ALERTS, wx.Bitmap(os.path.join(itrade_config.dirRes, 'bell.png')),
                           message('main_view_alerts'), message('main_view_desc_alerts'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_CURRENCIES, wx.Bitmap(os.path.join(itrade_config.dirRes, 'currencies.png')),
                           message('main_view_currencies'), message('main_view_desc_currencies'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_QUOTE, wx.Bitmap(os.path.join(itrade_config.dirRes, 'graph.png')),
                           message('main_quote_graph'), message('main_quote_desc_graph'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_REFRESH, wx.Bitmap(os.path.join(itrade_config.dirRes, 'refresh.png')),
                           message('main_view_refresh'), message('main_view_desc_refresh'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_AUTOSIZE, wx.Bitmap(os.path.join(itrade_config.dirRes, 'adjust_column.png')),
                           message('main_view_autosize'), message('main_view_desc_autosize'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_ABOUT, wx.Bitmap(os.path.join(itrade_config.dirRes, 'about.png')),
                           message('main_about'), message('main_desc_about'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.m_indicator = wx.TextCtrl(self, -1, "", size=(300,15),style=wx.BORDER_NONE|wx.ALIGN_LEFT|wx.TE_READONLY)

        self.AddControl(self.m_indicator)
        self.ClearIndicator()

        wx.EVT_TOOL(self, self._NTB2_EXIT, self.onExit)
        wx.EVT_TOOL(self, self._NTB2_NEW, self.onNew)
        wx.EVT_TOOL(self, self._NTB2_OPEN, self.onOpen)
        wx.EVT_TOOL(self, self._NTB2_EDIT, self.onEdit)
        wx.EVT_TOOL(self, self._NTB2_OPERATIONS, self.onOperations)
        wx.EVT_TOOL(self, self._NTB2_CURRENCIES, self.onCurrencies)
        wx.EVT_TOOL(self, self._NTB2_MONEY, self.onMoney)
        wx.EVT_TOOL(self, self._NTB2_ALERTS, self.onAlerts)
        wx.EVT_TOOL(self, self._NTB2_QUOTE, self.onQuote)
        wx.EVT_TOOL(self, self._NTB2_ABOUT, self.onAbout)
        wx.EVT_TOOL(self, self._NTB2_REFRESH, self.onRefresh)
        wx.EVT_TOOL(self, self._NTB2_AUTOSIZE, self.onAutoSize)
        self.Realize()

    def onRefresh(self, event):
        self.m_parent.OnRefresh(event)

    def onAutoSize(self, event):
        self.m_parent.OnAutoSize(event)

    def onOpen(self,event):
        self.m_parent.OnOpen(event)

    def onNew(self,event):
        self.m_parent.OnNew(event)

    def onEdit(self,event):
        self.m_parent.OnEdit(event)

    def onExit(self,event):
        self.m_parent.OnExit(event)

    def onOperations(self,event):
        self.m_parent.OnOperations(event)

    def onMoney(self,event):
        self.m_parent.OnMoney(event)

    def onCurrencies(self,event):
        self.m_parent.OnCurrencies(event)

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
            label = " " + message('indicator_autorefresh')
        else:
            label = " " + message('indicator_noautorefresh')
        self.m_indicator.SetForegroundColour(wx.NullColour)
        #self.m_indicator.ClearBackground()
        self.m_indicator.ChangeValue(label)

    def SetIndicator(self,market,connector,indice):
        dateclock = connector.currentDate(indice)
        if dateclock != "----":
            conv=time.strptime(dateclock,"%d/%m/%Y")
            dateclock = time.strftime(date_format[indice.market()][0],conv)

        clock = connector.currentClock(indice)
        if clock != '::':
            #print'clock:',clock
            conv=time.strptime(clock,"%H:%M")
            clock = time.strftime(date_format[indice.market()][1],conv)
            #print'clock am pm:',clock
        if clock == "::":
            label = " " + indice.market() + " : " + message('indicator_disconnected')
            self.m_indicator.SetForegroundColour(wx.BLACK)

        else:
            label = " " + indice.market() + " - " + dateclock+ " - " + clock
            if indice:
                label = label + "  -  " + indice.name() + " : "+ indice.sv_close()+ "  ( " + indice.sv_percent()+ " )"
                if indice.sv_percent()[0] == '-':
                    # red FF0000
                    color = wx.Colour(255,0,0)
                elif indice.sv_percent()[0] == ' ':
                    color = wx.BLACK
                else:
                    # blue4 00008B
                    color = wx.Colour(0,0,139)

            if label==self.m_indicator.GetValue():
                # display indice red or blue
                self.ClearIndicator()
                self.m_indicator.SetForegroundColour(color)
            else:
                if indice.sv_percent()[0] == '-':
                    # Orange - FF7F00 Indice change
                    color = wx.Colour(255,127,0)
                elif indice.sv_percent()[0] == ' ':
                    color = wx.BLACK
                else:
                    # green4 008B00 Indice change
                    color = wx.Colour(0,139,0)
                self.ClearIndicator()
                self.m_indicator.SetForegroundColour(color)
        self.m_indicator.ChangeValue(label)
        # get indicator and toolbar positions and sizes
        indicatorposition = self.m_indicator.GetScreenPosition()
        indicatorsize = self.m_indicator.GetClientSize()
        toolbarposition = self.GetScreenPosition()
        toolbarsize = self.GetClientSize()
        # compute width... minus 2 because it only works that way with gtk 2.6
        computedwidth = toolbarsize.width + toolbarposition.x - indicatorposition.x - 2
        if indicatorsize.width != computedwidth:
            indicatorsize.SetWidth(computedwidth)
            self.m_indicator.SetSize(indicatorsize)


# ============================================================================
# iTradeMainNotebookWindow
# ============================================================================

class iTradeMainNotebookWindow(wx.Notebook):

    def __init__(self,parent,id,page,portfolio,matrix):
        wx.Notebook.__init__(self,parent,id,style=wx.SIMPLE_BORDER|wx.NB_TOP)
        self.m_portfolio = portfolio
        self.m_matrix = matrix
        self.m_parent = parent
        self.init(parent)

        # events
        wx.EVT_NOTEBOOK_PAGE_CHANGED(self, id, self.OnPageChanged)
        wx.EVT_NOTEBOOK_PAGE_CHANGING(self, id, self.OnPageChanging)
        wx.EVT_ERASE_BACKGROUND(self,self.OnEraseBackground)

    # --- [ window management ] -------------------------------------

    def OnEraseBackground(self, evt):
        pass

    # --- [ page management ] -------------------------------------

    def init(self,parent):
        #print 'book init --['
        self.win = {}
        self.DeleteAllPages()

        self.win[ID_PAGE_QUOTES] = iTrade_MatrixQuotesPanel(self,parent,wx.NewId(),self.m_portfolio,self.m_matrix)
        self.AddPage(self.win[ID_PAGE_QUOTES], message('page_quotes'))

        self.win[ID_PAGE_PORTFOLIO] = iTrade_MatrixPortfolioPanel(self,parent,wx.NewId(),self.m_portfolio,self.m_matrix)
        self.AddPage(self.win[ID_PAGE_PORTFOLIO], message('page_portfolio'))

        self.win[ID_PAGE_STOPS] = iTrade_MatrixStopsPanel(self,parent,wx.NewId(),self.m_portfolio,self.m_matrix)
        self.AddPage(self.win[ID_PAGE_STOPS], message('page_stops'))

        self.win[ID_PAGE_INDICATORS] = iTrade_MatrixIndicatorsPanel(self,parent,wx.NewId(),self.m_portfolio,self.m_matrix)
        self.AddPage(self.win[ID_PAGE_INDICATORS], message('page_indicators'))

        self.win[ID_PAGE_TRADING] = iTrade_TradingPanel(self,parent,wx.NewId(),self.m_portfolio,self.m_matrix)
        self.AddPage(self.win[ID_PAGE_TRADING], message('page_trading'))

        self.win[ID_PAGE_EVALUATION] = iTradeEvaluationPanel(self,wx.NewId(),self.m_portfolio)
        self.AddPage(self.win[ID_PAGE_EVALUATION], message('page_evaluation'))
        #print ']-- book init'

    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        info('OnPageChanged,  old:%d, new:%d, sel:%d\n' % (old, new, sel))
        if old != new:
            if old >= 0:
                self.win[old].DoneCurrentPage()
            if new >= 0:
                self.win[new].InitCurrentPage()
                self.m_parent.updateTitle(new)
        event.Skip()

    def OnPageChanging(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        info('OnPageChanging, old:%d, new:%d, sel:%d\n' % (old, new, sel))
        event.Skip()

    def OnRefresh(self, event):
        sel = self.GetSelection()
        self.win[sel].OnRefresh(event)

    def ResetPages(self):
        # reset all pages
        print 'Reset All Pages'
        self.win[ID_PAGE_QUOTES].m_mustInit = True
        self.win[ID_PAGE_PORTFOLIO].m_mustInit = True
        self.win[ID_PAGE_STOPS].m_mustInit = True
        self.win[ID_PAGE_INDICATORS].m_mustInit = True
        self.win[ID_PAGE_TRADING].m_mustInit = True
        self.win[ID_PAGE_EVALUATION].m_mustInit = True

    def InitCurrentPage(self,bReset,bInit):
        if bInit:
            self.ChangeSelection(0)
        if bReset:
            self.ResetPages()

        # Init current page
        sel = self.GetSelection()
        self.win[sel].InitCurrentPage()
        #print 'book::InitCurrentPage: page:',sel

    def DoneCurrentPage(self):
        sel = self.GetSelection()
        self.win[sel].DoneCurrentPage()

# ============================================================================
# iTradeMainWindow
#
# ============================================================================

import wx.lib.newevent
(PostInitEvent,EVT_POSTINIT) = wx.lib.newevent.NewEvent()

class iTradeMainWindow(wx.Frame,iTrade_wxFrame):

    def __init__(self,parent,portfolio,matrix):
        self.m_id = wx.NewId()
        wx.Frame.__init__(self,parent,self.m_id, "", size = ( 640,480), style = wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        iTrade_wxFrame.__init__(self,parent, 'main')

        self.m_portfolio = portfolio
        self.m_matrix = matrix

        self.m_market = self.m_portfolio.market()

        self.initIndice()

        # Set Lang
        self.SetLang(bDuringInit=True)

        self.m_bookId = wx.NewId()
        self.m_book = iTradeMainNotebookWindow(self, self.m_bookId, page=-1, portfolio=self.m_portfolio,matrix=self.m_matrix)

        # link to other windows
        self.m_hOperation = None
        self.m_hMoney = None
        self.m_hAlerts = None
        self.m_hView = None
        self.m_hProperty = None
        self.m_hCurrency = None

        wx.EVT_CLOSE(self, self.OnCloseWindow)
        wx.EVT_WINDOW_DESTROY(self, self.OnDestroyWindow)

        # Build the main menu
        self.buildMenu()

        # Toolbar
        self.m_toolbar = iTradeMainToolbar(self, wx.NewId())

        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_ERASE_BACKGROUND(self,self.OnEraseBackground)

        # refresh full view after window init finished
        EVT_POSTINIT(self, self.OnPostInit)
        wx.PostEvent(self,PostInitEvent())

        # last
        self.Show(True)

    # --- [ Menus ] ----------------------------------------------------------------

    def buildMenu(self):
        # the main menu
        self.filemenu = wx.Menu()
        self.filemenu.Append(wx.ID_OPEN,message('main_open'),message('main_desc_open'))
        self.filemenu.Append(wx.ID_NEW,message('main_new'),message('main_desc_new'))
        self.filemenu.Append(wx.ID_SAVEAS,message('main_saveas'),message('main_desc_saveas'))
        self.filemenu.Append(wx.ID_DELETE,message('main_delete'),message('main_desc_delete'))
        self.filemenu.AppendSeparator()
        self.filemenu.Append(wx.ID_EDIT,message('main_edit'),message('main_desc_edit'))
        self.filemenu.AppendSeparator()
        self.filemenu.Append(ID_MANAGELIST,message('main_managelist'),message('main_desc_managelist'))
        self.filemenu.AppendSeparator()
        self.filemenu.Append(wx.ID_EXIT,message('main_exit'),message('main_desc_exit'))

        self.matrixmenu = wx.Menu()
        self.matrixmenu.Append(ID_QUOTES, message('main_view_quotes'),message('main_view_desc_quotes'))
        self.matrixmenu.Append(ID_PORTFOLIO, message('main_view_portfolio'),message('main_view_desc_portfolio'))
        self.matrixmenu.Append(ID_STOPS, message('main_view_stops'),message('main_view_desc_stops'))
        self.matrixmenu.Append(ID_INDICATORS, message('main_view_indicators'),message('main_view_desc_indicators'))
        self.matrixmenu.AppendSeparator()
        self.matrixmenu.AppendRadioItem(ID_SMALL_VIEW, message('main_view_small'),message('main_view_desc_small'))
        self.matrixmenu.AppendRadioItem(ID_NORMAL_VIEW, message('main_view_normal'),message('main_view_desc_normal'))
        self.matrixmenu.AppendRadioItem(ID_BIG_VIEW, message('main_view_big'),message('main_view_desc_big'))
        self.matrixmenu.AppendSeparator()
        self.matrixmenu.Append(wx.ID_REFRESH, message('main_view_refresh'),message('main_view_desc_refresh'))
        self.matrixmenu.AppendCheckItem(ID_AUTOREFRESH, message('main_view_autorefresh'),message('main_view_desc_autorefresh'))
        self.matrixmenu.Append(ID_AUTOSIZE, message('main_view_autosize'),message('main_view_desc_autosize'))

        self.quotemenu = wx.Menu()
        self.quotemenu.Append(ID_ADD_QUOTE, message('main_quote_add'),message('main_quote_desc_add'))
        self.quotemenu.Append(ID_REMOVE_QUOTE, message('main_quote_remove'),message('main_quote_desc_add'))
        self.quotemenu.AppendSeparator()
        self.quotemenu.Append(ID_GRAPH_QUOTE, message('main_quote_graph'),message('main_quote_desc_graph'))
        self.quotemenu.Append(ID_LIVE_QUOTE, message('main_quote_live'),message('main_quote_desc_live'))
        self.quotemenu.AppendSeparator()
        self.quotemenu.Append(ID_BUY_QUOTE, message('main_quote_buy'),message('main_quote_desc_buy'))
        self.quotemenu.Append(ID_SELL_QUOTE, message('main_quote_sell'),message('main_quote_desc_sell'))
        self.quotemenu.AppendSeparator()
        self.quotemenu.Append(ID_PROPERTY_QUOTE, message('main_quote_property'),message('main_quote_desc_property'))

        self.viewmenu = wx.Menu()
        self.viewmenu.Append(ID_OPERATIONS, message('main_view_operations'),message('main_view_desc_operations'))
        self.viewmenu.AppendSeparator()
        self.viewmenu.Append(ID_TRADING, message('main_view_trading'),message('main_view_desc_trading'))
        self.viewmenu.Append(ID_EVALUATION, message('main_view_evaluation'),message('main_view_desc_evaluation'))
        self.viewmenu.AppendSeparator()
        self.viewmenu.Append(ID_CURRENCIES, message('main_view_currencies'),message('main_view_desc_currencies'))
        self.viewmenu.Append(ID_ALERTS, message('main_view_alerts'),message('main_view_desc_alerts'))
        self.viewmenu.AppendSeparator()
        self.viewmenu.Append(ID_CONVERT, message('main_view_convert'),message('main_view_desc_convert'))
        self.viewmenu.Append(ID_COMPUTE, message('main_view_compute'),message('main_view_desc_compute'))

        self.optionsmenu = wx.Menu()
        self.accessmenu = wx.Menu()

        ncon = 0
        for aname,acon in listLoginConnector():
            self.accessmenu.Append(ID_ACCESS+ncon+1, acon.name(), acon.desc())
            ncon = ncon + 1
        if ncon>0:
            # menu->options->login only if there at least one login plugin loaded
            self.optionsmenu.AppendMenu(ID_ACCESS,message('main_options_access'),self.accessmenu,message('main_options_desc_access'))

        self.langmenu = wx.Menu()
        self.langmenu.AppendRadioItem(wx.LANGUAGE_DEFAULT + ID_MAC_OFFSET, message('main_options_lang_default'),message('main_options_lang_default'))
        self.langmenu.AppendRadioItem(wx.LANGUAGE_ENGLISH + ID_MAC_OFFSET, message('main_options_lang_english'),message('main_options_lang_english'))
        self.langmenu.AppendRadioItem(wx.LANGUAGE_FRENCH + ID_MAC_OFFSET, message('main_options_lang_french'),message('main_options_lang_french'))
        self.langmenu.AppendRadioItem(wx.LANGUAGE_PORTUGUESE + ID_MAC_OFFSET, message('main_options_lang_portuguese'),message('main_options_lang_portuguese'))
        self.langmenu.AppendRadioItem(wx.LANGUAGE_GERMAN + ID_MAC_OFFSET, message('main_options_lang_deutch'),message('main_options_lang_deutch'))
        self.langmenu.AppendRadioItem(wx.LANGUAGE_ITALIAN + ID_MAC_OFFSET, message('main_options_lang_italian'),message('main_options_lang_italian'))
        self.optionsmenu.AppendMenu(ID_LANG,message('main_options_lang'),self.langmenu,message('main_options_desc_lang'))
        if itrade_config.lang == 255:
            self.optionsmenu.Enable(ID_LANG,False)

        self.cachemenu = wx.Menu()
        self.cachemenu.Append(ID_CACHE_ERASE_DATA, message('main_cache_erase_data'),message('main_cache_desc_erase_data'))
        self.cachemenu.Append(ID_CACHE_ERASE_NEWS, message('main_cache_erase_news'),message('main_cache_desc_erase_news'))
        self.cachemenu.AppendSeparator()
        self.cachemenu.Append(ID_CACHE_ERASE_ALL, message('main_cache_erase_all'),message('main_cache_desc_erase_all'))
        self.optionsmenu.AppendMenu(ID_CACHE,message('main_options_cache'),self.cachemenu,message('main_options_desc_cache'))

        self.optionsmenu.Append(ID_CONNEXION,message('main_options_connexion'),message('main_options_desc_connexion'))

        self.helpmenu = wx.Menu()
        self.helpmenu.Append(wx.ID_HELP_CONTENTS, message('main_help_contents'),message('main_help_desc_contents'))
        self.helpmenu.AppendSeparator()
        self.helpmenu.Append(ID_SUPPORT, message('main_help_support'),message('main_help_desc_support'))
        self.helpmenu.Append(ID_BUG, message('main_help_bugs'),message('main_help_desc_bugs'))
        self.helpmenu.Append(ID_FORUM, message('main_help_forum'),message('main_help_desc_forum'))
        self.helpmenu.Append(ID_DONORS, message('main_help_donors'),message('main_help_desc_donors'))
        self.helpmenu.AppendSeparator()
        self.helpmenu.Append(ID_CHECKSOFTWARE, message('main_help_checksoftware'),message('main_help_desc_checksoftware'))
        self.helpmenu.AppendSeparator()
        self.helpmenu.Append(wx.ID_ABOUT, message('main_about'), message('main_desc_about'))

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

        wx.EVT_MENU(self, wx.ID_OPEN, self.OnOpen)
        wx.EVT_MENU(self, wx.ID_NEW, self.OnNew)
        wx.EVT_MENU(self, wx.ID_DELETE, self.OnDelete)
        wx.EVT_MENU(self, wx.ID_SAVEAS, self.OnSaveAs)
        wx.EVT_MENU(self, wx.ID_EDIT, self.OnEdit)
        wx.EVT_MENU(self, ID_MANAGELIST, self.OnManageList)
        wx.EVT_MENU(self, wx.ID_EXIT, self.OnExit)
        wx.EVT_MENU(self, wx.ID_HELP_CONTENTS, self.OnContent)
        wx.EVT_MENU(self, ID_SUPPORT, self.OnSupport)
        wx.EVT_MENU(self, ID_BUG, self.OnBug)
        wx.EVT_MENU(self, ID_FORUM, self.OnForum)
        wx.EVT_MENU(self, ID_DONORS, self.OnDonors)
        wx.EVT_MENU(self, ID_CHECKSOFTWARE, self.OnCheckSoftware)
        wx.EVT_MENU(self, ID_PORTFOLIO, self.OnPortfolio)
        wx.EVT_MENU(self, ID_QUOTES, self.OnQuotes)
        wx.EVT_MENU(self, ID_STOPS, self.OnStops)
        wx.EVT_MENU(self, ID_INDICATORS, self.OnIndicators)
        wx.EVT_MENU(self, ID_TRADING, self.OnTrading)
        wx.EVT_MENU(self, ID_OPERATIONS, self.OnOperations)
        wx.EVT_MENU(self, ID_EVALUATION, self.OnEvaluation)
        wx.EVT_MENU(self, ID_CONVERT, self.OnConvert)
        wx.EVT_MENU(self, ID_COMPUTE, self.OnCompute)
        wx.EVT_MENU(self, ID_ALERTS, self.OnAlerts)
        wx.EVT_MENU(self, ID_CURRENCIES, self.OnCurrencies)

        wx.EVT_MENU(self, ID_ADD_QUOTE, self.OnAddQuote)
        wx.EVT_MENU(self, ID_REMOVE_QUOTE, self.OnRemoveCurrentQuote)
        wx.EVT_MENU(self, ID_GRAPH_QUOTE, self.OnGraphQuote)
        wx.EVT_MENU(self, ID_LIVE_QUOTE, self.OnLiveQuote)
        wx.EVT_MENU(self, ID_BUY_QUOTE, self.OnBuyQuote)
        wx.EVT_MENU(self, ID_SELL_QUOTE, self.OnSellQuote)
        wx.EVT_MENU(self, ID_PROPERTY_QUOTE, self.OnPropertyQuote)

        wx.EVT_MENU(self, ID_SMALL_VIEW, self.OnViewSmall)
        wx.EVT_MENU(self, ID_NORMAL_VIEW, self.OnViewNormal)
        wx.EVT_MENU(self, ID_BIG_VIEW, self.OnViewBig)

        for i in range(0,ncon):
            wx.EVT_MENU(self, ID_ACCESS+i+1, self.OnAccess)

        wx.EVT_MENU(self, wx.LANGUAGE_DEFAULT + ID_MAC_OFFSET, self.OnLangDefault)
        wx.EVT_MENU(self, wx.LANGUAGE_ENGLISH + ID_MAC_OFFSET, self.OnLangEnglish)
        wx.EVT_MENU(self, wx.LANGUAGE_FRENCH + ID_MAC_OFFSET, self.OnLangFrench)
        wx.EVT_MENU(self, wx.LANGUAGE_PORTUGUESE + ID_MAC_OFFSET, self.OnLangPortuguese)
        wx.EVT_MENU(self, wx.LANGUAGE_GERMAN + ID_MAC_OFFSET, self.OnLangDeutch)
        wx.EVT_MENU(self, wx.LANGUAGE_ITALIAN + ID_MAC_OFFSET, self.OnLangItalian)

        wx.EVT_MENU(self, ID_CACHE_ERASE_DATA, self.OnCacheEraseData)
        wx.EVT_MENU(self, ID_CACHE_ERASE_NEWS, self.OnCacheEraseNews)
        wx.EVT_MENU(self, ID_CACHE_ERASE_ALL, self.OnCacheEraseAll)

        wx.EVT_MENU(self, ID_CONNEXION, self.OnConnexion)

        wx.EVT_MENU(self, wx.ID_REFRESH, self.OnRefresh)
        wx.EVT_MENU(self, ID_AUTOREFRESH, self.OnAutoRefresh)
        wx.EVT_MENU(self, ID_AUTOSIZE, self.OnAutoSize)
        wx.EVT_MENU(self, wx.ID_ABOUT, self.OnAbout)

    # --- [ window management ] -------------------------------------

    def OnEraseBackground(self, evt):
        pass

    def OnPostInit(self,event):
        self.updateTitle()
        self.updateCheckItems()
        self.InitCurrentPage(bReset=True,bInit=True)

    def OnRefresh(self,event=None):
        # called by a child (toolbar button, property window, ...)
        if itrade_config.verbose:
            print
            print 'MainWindow::OnRefresh event=%s' % event

        # to force a refresh of the book
        self.m_book.OnRefresh(event)

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.m_toolbar.SetDimensions(0, 0, w, 32)
        self.m_book.SetDimensions(0, 32, w, h-32)
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
        self.Close(True)

    def OnCloseWindow(self, evt):
        self.DoneCurrentPage()
        self.Save()
        self.Destroy()

    def OnDestroyWindow(self, evt):
        if evt.GetId()==self.m_id:
            self.CloseLinks()

    def InitCurrentPage(self,bReset,bInit):
        self.m_book.InitCurrentPage(bReset,bInit)

    def DoneCurrentPage(self):
        self.m_book.DoneCurrentPage()

    # --- [ menu ] -------------------------------------

    def OnOpen(self,e):
        dp = select_iTradePortfolio(self,self.m_portfolio,'select')
        if dp and dp != self.m_portfolio:
            # can be long ...
            wx.SetCursor(wx.HOURGLASS_CURSOR)
            self.DoneCurrentPage()

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
        self.initIndice()

        # should be enough !
        wx.SetCursor(wx.STANDARD_CURSOR)

        # populate current view and refresh
        self.OnPostInit(None)

    def OnNew(self,e):
        dp = properties_iTradePortfolio(self,None,'create')
        if dp:
            self.NewContext(dp)
            self.Save()

    def OnEdit(self,e):
        dp = properties_iTradePortfolio(self,self.m_portfolio,'edit')
        if dp:
            self.NewContext(dp)
            self.Save()

    def OnDelete(self,e):
        dp = select_iTradePortfolio(self,self.m_portfolio,'delete')
        if dp:
            properties_iTradePortfolio(self,dp,'delete')

    def OnSaveAs(self,e):
        dp = properties_iTradePortfolio(self,self.m_portfolio,'rename')
        if dp:
            self.NewContext(dp)

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
        id = getLang()
        if itrade_config.forumURL.has_key(id):
            url = itrade_config.forumURL[id]
        else:
            url = itrade_config.forumURL['en']
        iTradeLaunchBrowser(url,new=True)

    def OnDonors(self,e):
        iTradeLaunchBrowser(itrade_config.donorsTrackerURL,new=True)

    def OnCheckSoftware(self,e):
        # can be long ...
        wx.SetCursor(wx.HOURGLASS_CURSOR)

        url = itrade_config.checkNewRelease()

        # restore
        wx.SetCursor(wx.STANDARD_CURSOR)

        if url=='ok':
            iTradeInformation(self,message('checksoftware_uptodate'),message('checksoftware_title'))
        elif url=='dev':
            iTradeInformation(self,message('checksoftware_development'),message('checksoftware_title'))
        elif url=='err':
            iTradeError(self,message('checksoftware_error'),message('checksoftware_title'))
        else:
            if iTradeYesNo(self,message('checksoftware_needupdate'),message('checksoftware_title'))==wx.ID_YES:
                iTradeLaunchBrowser(url,new=True)

    def OnManageList(self,e):
        list_iTradeQuote(self,self.m_portfolio.market())

    def OnAbout(self,e):
        d = iTradeAboutBox(self)
        d.CentreOnParent()
        d.ShowModal()
        d.Destroy()

    def updateCheckItems(self):
        m = self.matrixmenu.FindItemById(ID_AUTOREFRESH)
        m.Check(itrade_config.bAutoRefreshMatrixView)

        m = self.matrixmenu.FindItemById(ID_SMALL_VIEW)
        m.Check(itrade_config.matrixFontSize==1)

        m = self.matrixmenu.FindItemById(ID_NORMAL_VIEW)
        m.Check(itrade_config.matrixFontSize==2)

        m = self.matrixmenu.FindItemById(ID_BIG_VIEW)
        m.Check(itrade_config.matrixFontSize==3)

        if itrade_config.lang != 255:
            m = self.langmenu.FindItemById(wx.LANGUAGE_DEFAULT + ID_MAC_OFFSET)
            m.Check(itrade_config.lang==0)

            m = self.langmenu.FindItemById(wx.LANGUAGE_ENGLISH + ID_MAC_OFFSET)
            m.Check(itrade_config.lang==1)

            m = self.langmenu.FindItemById(wx.LANGUAGE_FRENCH + ID_MAC_OFFSET)
            m.Check(itrade_config.lang==2)

            m = self.langmenu.FindItemById(wx.LANGUAGE_PORTUGUESE + ID_MAC_OFFSET)
            m.Check(itrade_config.lang==3)

            m = self.langmenu.FindItemById(wx.LANGUAGE_GERMAN + ID_MAC_OFFSET)
            m.Check(itrade_config.lang==4)

            m = self.langmenu.FindItemById(wx.LANGUAGE_ITALIAN + ID_MAC_OFFSET)
            m.Check(itrade_config.lang==5)

        # refresh Enable state based on current View
        m = self.quotemenu.FindItemById(ID_ADD_QUOTE)
        m.Enable(self.m_book.GetSelection() == ID_PAGE_QUOTES)

    def updateQuoteItems(self,op1,quote):
        m = self.quotemenu.FindItemById(ID_GRAPH_QUOTE)
        m.Enable(op1)
        m = self.quotemenu.FindItemById(ID_LIVE_QUOTE)
        m.Enable(op1)
        m = self.quotemenu.FindItemById(ID_PROPERTY_QUOTE)
        m.Enable(op1)

        m = self.quotemenu.FindItemById(ID_REMOVE_QUOTE)
        m.Enable((self.m_book.GetSelection() == ID_PAGE_QUOTES) and op1 and not quote.isTraded())

    def updateTitle(self,page=None):
        # get current page
        if page == None:
            page = self.m_book.GetSelection()

        if page == ID_PAGE_PORTFOLIO:
            title = message('main_title_portfolio')
        elif page == ID_PAGE_QUOTES:
            title = message('main_title_quotes')
        elif page == ID_PAGE_STOPS:
            title = message('main_title_stops')
        elif page == ID_PAGE_INDICATORS:
            title = message('main_title_indicators')
        elif page == ID_PAGE_TRADING:
            title = message('main_title_trading')
        elif page == ID_PAGE_EVALUATION:
            title = message('main_title_evaluation')
        else:
            title = '??? %s:%s'
        self.SetTitle(title % (self.m_portfolio.name(),self.m_portfolio.accountref()))

    def RebuildList(self):
        self.Save()
        self.DoneCurrentPage()
        self.m_matrix.build()
        self.InitCurrentPage(bReset=True,bInit=False)

    def OnPortfolio(self,e):
        # check current page
        if self.m_book.GetSelection() != ID_PAGE_PORTFOLIO:
            self.m_book.SetSelection(ID_PAGE_PORTFOLIO)
        self.updateTitle()

    def OnQuotes(self,e):
        # check current page
        if self.m_book.GetSelection() != ID_PAGE_QUOTES:
            self.m_book.SetSelection(ID_PAGE_QUOTES)
        self.updateTitle()

    def OnStops(self,e):
        # check current page
        if self.m_book.GetSelection() != ID_PAGE_STOPS:
            self.m_book.SetSelection(ID_PAGE_STOPS)
        self.updateTitle()

    def OnIndicators(self,e):
        # check current page
        if self.m_book.GetSelection() != ID_PAGE_INDICATORS:
            self.m_book.SetSelection(ID_PAGE_INDICATORS)
        self.updateTitle()

    def OnTrading(self,e):
        # check current page
        if self.m_book.GetSelection() != ID_PAGE_TRADING:
            self.m_book.SetSelection(ID_PAGE_TRADING)
        self.updateTitle()

    def OnEvaluation(self,e):
        # check current page
        if self.m_book.GetSelection() != ID_PAGE_EVALUATION:
            self.m_book.SetSelection(ID_PAGE_EVALUATION)
        self.updateTitle()

    def OnOperations(self,e):
        open_iTradeOperations(self,self.m_portfolio)

    def OnCompute(self,e):
        quote = self.currentQuote()
        open_iTradeMoney(self,1,self.m_portfolio,quote)

    def OnConvert(self,e):
        open_iTradeConverter(self)

    def OnAlerts(self,e):
        open_iTradeAlerts(self,self.m_portfolio)

    def OnCurrencies(self,e):
        open_iTradeCurrencies(self)

    def OnGraphQuote(self,e):
        if self.currentItem()>=0:
            debug("OnGraphQuote: %s" % self.currentItemText())
            self.openCurrentQuote(page=0)

    def OnLiveQuote(self,e):
        if self.currentItem()>=0:
            debug("OnLiveQuote: %s" % self.currentItemText())
            self.openCurrentQuote(page=1)

    def OnPropertyQuote(self,e):
        if self.currentItem()>=0:
            debug("OnPropertyQuote: %s" % self.currentItemText())
            self.openCurrentQuote(page=6)

    # --- [ Save any persistant data ] ----------------------------------------

    def Save(self):
        self.m_matrix.save(self.m_portfolio.filename())
        self.m_portfolio.saveStops()
        itrade_config.saveConfig()
        self.saveConfig()

    # --- [ buy / sell from the matrix ] ------------------------------------

    def OnBuyQuote(self,e):
        quote = self.currentQuote()
        if quote and quote.list()==QLIST_INDICES: quote=None
        if add_iTradeOperation(self,self.m_portfolio,quote,OPERATION_BUY):
            if self.m_hOperation:
                self.m_hOperation.RebuildList()
                # self will also RebuildList() from Operation View
            else:
                self.RebuildList()

    def OnSellQuote(self,e):
        quote = self.currentQuote()
        if quote and quote.list()==QLIST_INDICES: quote=None
        if add_iTradeOperation(self,self.m_portfolio,quote,OPERATION_SELL):
            if self.m_hOperation:
                self.m_hOperation.RebuildList()
                # self will also RebuildList() from Operation View
            else:
                self.RebuildList()

    # --- [ item management ] -----------------------------------------------

    def currentItem(self):
        sel = self.m_book.GetSelection()
        win = self.m_book.win[sel]
        return win.m_currentItem

    def currentItemText(self):
        sel = self.m_book.GetSelection()
        win = self.m_book.win[sel]
        return win.m_list.GetItemText(win.m_currentItem)

    def currentQuote(self):
        sel = self.m_book.GetSelection()
        win = self.m_book.win[sel]
        if win.m_currentItem>=0:
            quote,item = win.getQuoteAndItemOnTheLine(win.m_currentItem)
        else:
            quote = None
        return quote

    def openCurrentQuote(self,page=0):
        quote = self.currentQuote()
        if page==6:
            open_iTradeQuoteProperty(self,quote)
        else:
            open_iTradeQuote(self,self.m_portfolio,quote,page)

    # --- [ Text font size management ] -------------------------------------

    def OnChangeViewText(self):
        itrade_config.saveConfig()
        self.updateCheckItems()
        sel = self.m_book.GetSelection()
        win = self.m_book.win[sel]
        win.m_list.SetFont(FontFromSize(itrade_config.matrixFontSize))
        win.populate(bDuringInit=False)

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
        elif itrade_config.lang==5:
            lang = 'it'
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
                self.m_book.DoneCurrentPage()
                self.m_book.init(self)

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

    def OnLangItalian(self,e):
        itrade_config.lang = 5
        self.OnChangeLang()

    # --- [ cache management ] -------------------------------------

    def OnCacheEraseData(self,e):
        idRet = iTradeYesNo(self, message('cache_erase_confirm_data'), message('cache_erase_confirm_title'))
        if idRet == wx.ID_YES:
            self.m_matrix.flushTrades()

    def OnCacheEraseNews(self,e):
        idRet = iTradeYesNo(self, message('cache_erase_confirm_news'), message('cache_erase_confirm_title'))
        if idRet == wx.ID_YES:
            self.m_matrix.flushNews()

    def OnCacheEraseAll(self,e):
        idRet = iTradeYesNo(self, message('cache_erase_confirm_all'), message('cache_erase_confirm_title'))
        if idRet == wx.ID_YES:
            self.m_matrix.flushAll()

    # --- [ connexion management ] ---------------------------------------

    def OnConnexion(self,e):
        itrade_config.proxyHostname,itrade_config.proxyAuthentication,itrade_config.connectionTimeout = connection_UI(self,itrade_config.proxyHostname,itrade_config.proxyAuthentication,itrade_config.connectionTimeout)
        itrade_config.saveConfig()

    # --- [ autosize management ] -------------------------------------

    def OnAutoSize(self,e):
        sel = self.m_book.GetSelection()
        win = self.m_book.win[sel]
        win.adjustColumns()

    # --- [ autorefresh management ] -------------------------------------

    def OnAutoRefresh(self,e):
        self.DoneCurrentPage()
        itrade_config.bAutoRefreshMatrixView = not itrade_config.bAutoRefreshMatrixView
        itrade_config.saveConfig()
        self.updateCheckItems()
        self.m_toolbar.ClearIndicator()
        self.InitCurrentPage(bReset=False,bInit=False)

    def refreshConnexion(self):
        self.m_toolbar.SetIndicator(self.m_market,self.m_connector,self.m_indice)

    # ---[ Quotes ] -----------------------------------------

    def AddAndRefresh(self,quote=None):
        quote = addInMatrix_iTradeQuote(self,self.m_matrix,self.m_portfolio,quote)
        if quote:
            print 'AddAndRefresh:',quote
            self.m_portfolio.setupCurrencies()
            self.m_portfolio.loginToServices(quote)
            self.RebuildList()

    def OnAddQuote(self,e):
        self.AddAndRefresh(None)

    def OnRemoveCurrentQuote(self,e):
        quote = self.currentQuote()
        # ask a confirmation
        idRet = iTradeYesNo(self, message('remove_quote_info') % quote.name(), message('remove_quote_title'))
        if idRet == wx.ID_YES:
            if removeFromMatrix_iTradeQuote(self,self.m_matrix,quote):
                print 'OnRemoveCurrentQuote:',quote
                self.m_portfolio.setupCurrencies()
                self.RebuildList()

    # ---[ Stops ] -----------------------------------------

    def OnAddStops(self,e):
        quote = addOrEditStops_iTradeQuote(self,quote=None,market=self.m_portfolio.market(),bAdd=True)
        if quote:
            self.AddAndRefresh(quote)

    def OnRemoveStops(self,e):
        if removeStops_iTradeQuote(self,quote=self.currentQuote()):
            self.RebuildList()

    def OnEditStops(self,e):
        quote=self.currentQuote()
        if addOrEditStops_iTradeQuote(self,quote,market=quote.market(),bAdd=False):
            self.RebuildList()

    # ---[ Indice ] -----------------------------------------

    def indice(self):
        return self.m_indice

    def initIndice(self):
        self.m_connector = getDefaultLiveConnector(self.m_market,QLIST_INDICES)
        indice = self.m_portfolio.indice()
        #if itrade_config.verbose:
        #    print 'initIndice: indice %s use connector %s' % (indice,self.m_connector)
        if indice:
            lind = quotes.lookupISIN(indice)
            if len(lind)>=1:
                self.m_indice = lind[0]
                if self.m_indice:
                    self.m_connector = self.m_indice.liveconnector(bDebug=False)
                    #if itrade_config.verbose:
                    #    print 'initIndice: indice %s use connector %s' % (indice,self.m_connector)
                else:
                    if itrade_config.verbose:
                        print 'initIndice: indice %s not found' % indice
            else:
                if itrade_config.verbose:
                    print 'initIndice: indice %s not found' % indice
                self.m_indice = None
        else:
            if itrade_config.verbose:
                print 'initIndice: no indice sets up for this portfolio'
            self.m_indice = None

# ============================================================================
# That's all folks !
# ============================================================================
