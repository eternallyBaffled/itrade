#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxpanes.py
#
# Description: wxPython Panes for the Matrix
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
from itrade_local import message
from itrade_matrix import *
from itrade_quotes import *

# iTrade wx system
from itrade_wxquote import open_iTradeQuote
from itrade_wxpropquote import open_iTradeQuoteProperty
from itrade_wxutil import FontFromSize
from itrade_wxlive import iTrade_wxLiveMixin,EVT_UPDATE_LIVE

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
# iTrade_MatrixPanel
#
# Root of - basic mechanism
# ============================================================================

class iTrade_MatrixPanel(wx.Panel,wxl.ColumnSorterMixin,iTrade_wxLiveMixin):

    def __init__(self,parent,wm,id,portfolio,matrix):
        wx.Panel.__init__(self, parent, id)
        iTrade_wxLiveMixin.__init__(self)

        self.m_parent = wm
        self.m_portfolio = portfolio
        self.m_matrix = matrix
        self.m_id = id

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

        # events
        wx.EVT_CLOSE(self, self.OnCloseWindow)
        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_ERASE_BACKGROUND(self,self.OnEraseBackground)
        EVT_UPDATE_LIVE(self, self.OnLive)

    # --- [ window management ] -------------------------------------

    def OnEraseBackground(self, evt):
        pass

    def OnSize(self, evt):
        w,h = self.GetClientSizeTuple()
        self.m_list.SetDimensions(0, 0, w, h)
        #event.Skip(False)

    def OnCloseWindow(self, evt):
        self.stopLive(bBusy=False)

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
            open_iTradeQuoteProperty(self.m_parent,self.m_portfolio,quote)
        else:
            open_iTradeQuote(self.m_parent,self.m_portfolio,quote,page)

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

    # ---[ popup menu management ] --------------------------------------------

    def OnRightClick(self, event):
        if (self.m_currentItem<0) or (self.m_currentItem>=self.m_maxlines):
            # __x if self.m_currentItem == self.m_maxlines, launch eval !
            inList = False
            quote = None
        else:
            inList = True
            quote,item = self.getQuoteAndItemOnTheLine(self.m_currentItem)
            #debug("OnRightClick %s : %s\n" % (self.m_list.GetItemText(self.m_currentItem),quote))

        menu = self.OpenContextMenu(inList,quote)

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

    def OnPopup_Buy(self, event):
        debug("OnPopup_Buy")

    def OnPopup_Sell(self, event):
        debug("OnPopup_Sell")

    # ---[ Populate view ] -----------------------------------------

    def populate(self,bDuringInit):
        debug('populate duringinit=%d' % bDuringInit)

        # clear current population
        self.stopLive(bBusy=False)
        self.unregisterLive()
        self.m_list.ClearAll()

        # start a new population
        self.populateList()

        # start live
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

    # refresh color of one line
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

    # refresh currencies
    def refreshCurrencies(self):
        x = 0
        lst = currencies.m_currencies
        max = len(lst)
        keepGoing = True
        if self.m_parent.hasFocus():
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

    # --- [ manage current page ] -------------------------------------

    def InitCurrentPage(self):
        self.m_list.Show(True)

        # update portfolio and matrix (just in case)
        self.m_portfolio = self.m_parent.m_portfolio
        self.m_matrix = self.m_parent.m_matrix

        # create and display the list
        self.populate(bDuringInit=True)
        self.OnRefresh(None)

        if itrade_config.bAutoRefreshMatrixView:
            self.startLive()
        else:
            self.stopLive(bBusy=True)

    def DoneCurrentPage(self):
        # be sure to stop the live (if any)
        self.m_list.Show(False)
        self.stopLive(bBusy=False)

    # --- [ refresh lists ] -------------------------------------

    def OnLive(self, evt):
        # be sure this quote is still under population
        if self.isRunning(evt.quote):
            idview = evt.param
            for xline in range(0,self.m_maxlines):
                if self.itemQuoteMap[xline] == evt.quote:
                    #print 'live %d %d %d VS %d' % (xline,idview,xtype,self.m_id)
                    if idview == self.m_id:
                        #debug('%s: %s' % (evt.quote.key(),evt.param))
                        self.OnLiveQuote(evt.quote,xline)
                        self.m_parent.refreshConnexion()
                    else:
                        debug('%s: %s - bad : other view' % (evt.quote.key(),evt.param))
        else:
            debug('%s: %s - bad : not running' % (evt.quote.key(),evt.param))

    # refresh list
    def OnRefresh(self,e):
        if self.m_portfolio.is_multicurrencies():
            self.refreshCurrencies()
        self.refreshList()

    def updateQuoteItems(self):
        op1 = (self.m_currentItem>=0) and (self.m_currentItem<self.m_maxlines)
        if op1:
            quote,item = self.getQuoteAndItemOnTheLine(self.m_currentItem)
        else:
            quote = None

        self.m_parent.updateQuoteItems(op1,quote)

# ============================================================================
# iTrade_MatrixPortfolioPanel
# ============================================================================

class iTrade_MatrixPortfolioPanel(iTrade_MatrixPanel):

    def __init__(self,parent,wm,id,portfolio,matrix):
        iTrade_MatrixPanel.__init__(self, parent,wm, id, portfolio, matrix)

    # populate the portfolio
    def populateList(self):
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
            self.registerLive(eachQuote,itrade_config.refreshView,self.m_id)

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

    # refresh the evaluation portfolio line
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


    # refresh one portfolio line
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

    # refresh all the portfolio
    def refreshList(self):
        x = 0
        lst = self.m_matrix.list()
        max = len(lst)
        keepGoing = True
        if self.m_parent.hasFocus():
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

    def OnLiveQuote(self,quote,xline):
        self.refreshPortfolioLine(xline,True)

    # ---[ popup menu management ] --------------------------------------------

    def OpenContextMenu(self,inList,quote):
        # only do this part the first time so the events are only bound once
        if not hasattr(self, "m_popupID_Update"):
            self.m_popupID_Update = wx.NewId()
            self.m_popupID_View = wx.NewId()
            self.m_popupID_Live = wx.NewId()
            self.m_popupID_Properties = wx.NewId()
            self.m_popupID_Buy = wx.NewId()
            self.m_popupID_Sell = wx.NewId()
            wx.EVT_MENU(self, self.m_popupID_Update, self.OnPopup_Update)
            wx.EVT_MENU(self, self.m_popupID_View, self.OnPopup_View)
            wx.EVT_MENU(self, self.m_popupID_Live, self.OnPopup_Live)
            wx.EVT_MENU(self, self.m_popupID_Properties, self.OnPopup_Properties)
            wx.EVT_MENU(self, self.m_popupID_Buy, self.OnPopup_Buy)
            wx.EVT_MENU(self, self.m_popupID_Sell, self.OnPopup_Sell)

        # make a menu
        menu = wx.Menu()

        # add some items
        menu.Append(self.m_popupID_Update, message('main_popup_refreshall'))
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

        # return the menu
        return menu

# ============================================================================
# iTrade_MatrixQuotesPanel
# ============================================================================

class iTrade_MatrixQuotesPanel(iTrade_MatrixPanel):

    def __init__(self,parent,wm,id,portfolio,matrix):
        iTrade_MatrixPanel.__init__(self, parent,wm, id, portfolio, matrix)

    # populate quotes
    def populateList(self):
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
            self.registerLive(eachQuote,itrade_config.refreshView,self.m_id)

        self.populateMatrixEnd()

    # refresh one quote
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


    # refresh all quotes
    def refreshList(self):
        x = 0
        lst = self.m_matrix.list()
        max = len(lst)
        keepGoing = True
        if self.m_parent.hasFocus():
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

    def OnLiveQuote(self, quote, xline):
        self.refreshQuoteLine(xline,True)

    # ---[ popup menu management ] --------------------------------------------

    def OpenContextMenu(self,inList,quote):
        # only do this part the first time so the events are only bound once
        if not hasattr(self, "m_popupID_Update"):
            self.m_popupID_Update = wx.NewId()
            self.m_popupID_View = wx.NewId()
            self.m_popupID_Live = wx.NewId()
            self.m_popupID_Properties = wx.NewId()
            self.m_popupID_Add = wx.NewId()
            self.m_popupID_Remove = wx.NewId()
            self.m_popupID_Buy = wx.NewId()
            self.m_popupID_Sell = wx.NewId()
            wx.EVT_MENU(self, self.m_popupID_Update, self.OnPopup_Update)
            wx.EVT_MENU(self, self.m_popupID_View, self.OnPopup_View)
            wx.EVT_MENU(self, self.m_popupID_Live, self.OnPopup_Live)
            wx.EVT_MENU(self, self.m_popupID_Properties, self.OnPopup_Properties)
            wx.EVT_MENU(self, self.m_popupID_Add, self.OnPopup_Add)
            wx.EVT_MENU(self, self.m_popupID_Remove, self.OnPopup_Remove)
            wx.EVT_MENU(self, self.m_popupID_Buy, self.OnPopup_Buy)
            wx.EVT_MENU(self, self.m_popupID_Sell, self.OnPopup_Sell)

        # make a menu
        menu = wx.Menu()

        # add some items
        menu.Append(self.m_popupID_Update, message('main_popup_refreshall'))
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

        # return the menu
        return menu

    def OnPopup_Add(self, event):
        debug("OnPopup_Add")
        self.m_parent.OnAddQuote(None)

    def OnPopup_Remove(self, event):
        debug("OnPopup_Remove")
        self.m_parent.OnRemoveCurrentQuote(None)

# ============================================================================
# iTrade_MatrixStopsPanel
# ============================================================================

class iTrade_MatrixStopsPanel(iTrade_MatrixPanel):

    def __init__(self,parent,wm,id,portfolio,matrix):
        iTrade_MatrixPanel.__init__(self, parent,wm, id, portfolio, matrix)

    # populate stops
    def populateList(self):
        self.populateMatrixBegin()

        self.m_list.InsertColumn(IDC_INVEST, 'Buy', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_RISKM, 'Risk', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_STOPLOSS, 'Stop-', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_CURRENT, 'USP', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_STOPWIN, 'Stop+', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PV, 'Sell', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PROFIT, 'Profit', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PERCENT, ' % ', wx.LIST_FORMAT_RIGHT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_NAME, message('name'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)

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
            self.registerLive(eachQuote,itrade_config.refreshView,self.m_id)

        # adjust some column's size
        self.m_list.SetColumnWidth(IDC_INVEST, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_RISKM, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_STOPLOSS, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_STOPWIN, wx.LIST_AUTOSIZE)

        # finish populating
        self.populateMatrixEnd()

    # refresh one stop
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

    # refresh all the stop
    def refreshList(self):
        x = 0
        lst = self.m_matrix.list()
        max = len(lst)
        keepGoing = True
        if self.m_parent.hasFocus():
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

    def OnLiveQuote(self,quote,xline):
        self.refreshStopsLine(xline,True)

    # ---[ popup menu management ] --------------------------------------------

    def OpenContextMenu(self,inList,quote):
        # only do this part the first time so the events are only bound once
        if not hasattr(self, "m_popupID_Update"):
            self.m_popupID_Update = wx.NewId()
            self.m_popupID_Add = wx.NewId()
            self.m_popupID_Remove = wx.NewId()
            self.m_popupID_Edit = wx.NewId()
            wx.EVT_MENU(self, self.m_popupID_Update, self.OnPopup_Update)
            wx.EVT_MENU(self, self.m_popupID_Add, self.OnPopup_Add)
            wx.EVT_MENU(self, self.m_popupID_Edit, self.OnPopup_Add)
            wx.EVT_MENU(self, self.m_popupID_Remove, self.OnPopup_Remove)

        # make a menu
        menu = wx.Menu()

        # add some items
        menu.Append(self.m_popupID_Update, message('main_popup_refreshall'))
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

        # return the menu
        return menu

    def OnPopup_Add(self, event):
        debug("OnPopup_Add")
        pass

    def OnPopup_Edit(self, event):
        debug("OnPopup_Edit")
        pass

    def OnPopup_Remove(self, event):
        debug("OnPopup_Remove")
        pass

# ============================================================================
# iTrade_MatrixIndicatorsPanel
# ============================================================================

class iTrade_MatrixIndicatorsPanel(iTrade_MatrixPanel):

    def __init__(self,parent,wm,id,portfolio,matrix):
        iTrade_MatrixPanel.__init__(self, parent,wm, id, portfolio, matrix)

    # populate indicators
    def populateList(self):
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
            self.registerLive(eachQuote,itrade_config.refreshView,self.m_id)

        self.populateMatrixEnd()

    # refresh one indicator
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

    # refresh all indicators
    def refreshList(self):
        x = 0
        lst = self.m_matrix.list()
        max = len(lst)
        keepGoing = True
        if self.m_parent.hasFocus():
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

    def OnLiveQuote(self, quote, xline):
        quote.compute()
        self.refreshIndicatorLine(xline,True)

    # ---[ popup menu management ] --------------------------------------------

    def OpenContextMenu(self,inList,quote):
        # only do this part the first time so the events are only bound once
        if not hasattr(self, "m_popupID_Update"):
            self.m_popupID_Update = wx.NewId()
            self.m_popupID_View = wx.NewId()
            self.m_popupID_Live = wx.NewId()
            self.m_popupID_Properties = wx.NewId()
            self.m_popupID_Buy = wx.NewId()
            self.m_popupID_Sell = wx.NewId()
            wx.EVT_MENU(self, self.m_popupID_Update, self.OnPopup_Update)
            wx.EVT_MENU(self, self.m_popupID_View, self.OnPopup_View)
            wx.EVT_MENU(self, self.m_popupID_Live, self.OnPopup_Live)
            wx.EVT_MENU(self, self.m_popupID_Properties, self.OnPopup_Properties)
            wx.EVT_MENU(self, self.m_popupID_Buy, self.OnPopup_Buy)
            wx.EVT_MENU(self, self.m_popupID_Sell, self.OnPopup_Sell)

        # make a menu
        menu = wx.Menu()

        # add some items
        menu.Append(self.m_popupID_Update, message('main_popup_refreshall'))
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

        # return the menu
        return menu

# ============================================================================
# That's all folks !
# ============================================================================
