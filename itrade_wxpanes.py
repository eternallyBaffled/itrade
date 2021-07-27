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
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
import logging

# iTrade system
import itrade_config

# wxPython system
if not itrade_config.nowxversion:
    import itrade_wxversion
import wx
import wx.lib.mixins.listctrl as wxl

# iTrade system
from itrade_logging import *
from itrade_local import message
from itrade_matrix import *
from itrade_quotes import *
from itrade_currency import currencies

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
IDC_PRU = 2
IDC_PERCENT = 10
IDC_NAME = 11

# Portfolio view
IDC_QTY = 3
IDC_NOTUSED = 4
IDC_PR  = 5
IDC_PVU = 6
IDC_PERFDAY = 7
IDC_PV  = 8
IDC_PROFIT = 9
#IDC_PERCENT = 10
#IDC_NAME = 11

# trade view
IDC_VOLUME = 3
IDC_PREV = 4
IDC_OPEN = 5
IDC_HIGH = 6
IDC_LOW = 7
IDC_CLOSE = 8
IDC_PIVOTS = 9
#IDC_PERCENT = 10
#IDC_NAME = 11

# stops view
IDC_INVEST = 3
IDC_RISKM = 4
IDC_STOPLOSS = 5
IDC_CURRENT = 6
IDC_STOPWIN = 7
#IDC_PV  = 8
#IDC_PROFIT = 9
#IDC_PERCENT = 10
#IDC_NAME = 11

# indicators view
IDC_MA20 = 3
IDC_MA50 = 4
IDC_MA100 = 5
IDC_RSI = 6
IDC_MACD = 7
IDC_STOCH = 8
IDC_DMI = 9
IDC_EMV = 10
IDC_OVB = 11
IDC_LAST = 12

# ============================================================================
# iTradeMatrixListCtrl
# ============================================================================

class iTradeMatrixListCtrl(wx.ListCtrl, wxl.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style = 0):
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
        self.m_currentItem = -1

        self.m_mustInit = True

        # create an image list
        self.m_imagelist = wx.ImageList(16,16)

        self.idx_nochange = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'nochange.png')))
        self.idx_up = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'up.png')))
        self.idx_down = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'down.png')))
        self.idx_tbref = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'invalid.png')))
        self.idx_buy = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'buy.png')))
        self.idx_sell = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'sell.png')))
        self.idx_noop = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'noop.png')))

        self.sm_up = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'sm_up.png')))
        self.sm_dn = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'sm_down.png')))

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
        self.LoadSortColumn()

        # events
        wx.EVT_CLOSE(self, self.OnCloseWindow)
        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_ERASE_BACKGROUND(self,self.OnEraseBackground)
        wx.EVT_LIST_COL_CLICK(self,tID,self.OnColClick)

        EVT_UPDATE_LIVE(self, self.OnLive)

    # --- [ window management ] -------------------------------------

    def OnColClick(self,evt):
        self.SaveSortColumn()

    def OnEraseBackground(self, evt):
        pass

    def OnSize(self, evt):
        w,h = self.GetClientSizeTuple()
        self.m_list.SetDimensions(0, 0, w, h)
        #event.Skip(False)

    def OnCloseWindow(self, evt):
        self.stopLive(bBusy=False)
        self.SaveSortColumn()

    # --- [ wxl.ColumnSorterMixin management ] -------------------------------------

    # Used by the wxl.ColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.m_list

    # Used by the wxl.ColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)

    def LoadSortColumn(self):
        # extract
        a,b = itrade_config.column[self.name()].split(';')

        # load
        self.m_sort_colnum = long(a)
        self.m_sort_colasc = long(b)

        #
        if itrade_config.verbose:
            print('Load sorting',self.name(),'- column:',self.m_sort_colnum,'ascending:',self.m_sort_colasc)

    def SaveSortColumn(self):
        # update from current column
        self.m_sort_colnum = self._col
        if self._col!=-1:
            self.m_sort_colasc = self._colSortFlag[self._col]
        else:
            self.m_sort_colasc = 1

        #
        if itrade_config.verbose:
            print('Save sorting',self.name(),'- column:',self.m_sort_colnum,'ascending:',self.m_sort_colasc)

        # format for saving
        itrade_config.column[self.name()] = '%s;%s' % (self.m_sort_colnum,self.m_sort_colasc)

    def SortColumn(self):
        # sort the default column
        if self.m_sort_colnum!=-1:
            if itrade_config.verbose:
                print('Sorting',self.name(),'- column:',self.m_sort_colnum,'ascending:',self.m_sort_colasc)
            self.SortListItems(self.m_sort_colnum,ascending=self.m_sort_colasc)

    def needDynamicSortColumn(self):
        if self.m_sort_colnum<IDC_PRU:
            return False
        if self.m_sort_colnum>=IDC_NAME:
            return False
        return True

    def getQuoteAndItemOnTheLine(self,x):
        key = self.m_list.GetItemData(x)
        #print 'line:%d -> key=%d quote=%s' % (x,key,self.itemQuoteMap[key].ticker())
        quote = self.itemQuoteMap[key]
        item = self.m_list.GetItem(x)
        return quote,item

    def openCurrentQuote(self,page=0):
        quote,item = self.getQuoteAndItemOnTheLine(self.m_currentItem)
        if page==6:
            open_iTradeQuoteProperty(self.m_parent,quote)
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
        #info("OnRightDown: x, y = %s item=%d max=%d" % (str((self.x, self.y)), item,self.m_maxlines))
        if flags & wx.LIST_HITTEST_ONITEM:
            self.m_currentItem = item
        else:
            self.m_currentItem = -1
        self.updateQuoteItems()
        event.Skip()

    def OnLeftDown(self, event):
        self.x = event.GetX()
        self.y = event.GetY()
        item, flags = self.m_list.HitTest((self.x, self.y))
        #info("OnLeftDown: x, y = %s item=%d max=%d" % (str((self.x, self.y)), item,self.m_maxlines))
        if flags & wx.LIST_HITTEST_ONITEM:
            self.m_currentItem = item
        else:
            self.m_currentItem = -1
        self.updateQuoteItems()
        event.Skip()

    def OnItemActivated(self, event):
        self.m_currentItem = event.m_itemIndex
        if (self.m_currentItem>=0) and (self.m_currentItem<self.m_maxlines):
            #info("OnItemActivated: %s" % self.m_list.GetItemText(self.m_currentItem))
            self.openCurrentQuote()
            # __x if self.m_currentItem == self.m_maxlines, launch eval !

    def OnItemSelected(self, event):
        self.m_currentItem = event.m_itemIndex
        self.updateQuoteItems()
        if (self.m_currentItem>=0) and (self.m_currentItem<self.m_maxlines):
            #info("OnItemSelected: %s, %s, %s, %s\n" %
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
        self.openCurrentQuote(page=0)

    def OnPopup_Live(self, event):
        debug("OnPopup_Live")
        self.openCurrentQuote(page=1)

    def OnPopup_Properties(self, event):
        debug("OnPopup_Properties")
        self.openCurrentQuote(page=6)

    def OnPopup_Buy(self, event):
        debug("OnPopup_Buy")
        self.m_parent.OnBuyQuote(event)

    def OnPopup_Sell(self, event):
        debug("OnPopup_Sell")
        self.m_parent.OnSellQuote(event)

    # ---[ Indicator ] ---------------------------------------------

    def registerIndice(self):
        ind = self.m_parent.indice()
        if ind:
            self.registerLive(ind,itrade_config.refreshView,self.m_id)

    # ---[ Populate view ] -----------------------------------------

    def populate(self,bDuringInit):
        #debug('populate duringinit=%d' % bDuringInit)

        # clear current population
        self.stopLive(bBusy=False)
        self.unregisterLive()
        self.m_list.ClearAll()

        # start a new population
        self.populateList()

        # start Index management
        self.registerIndice()

        # start live
        if not bDuringInit and itrade_config.bAutoRefreshMatrixView:
            self.startLive()

    def populateMatrixBegin(self):
        # init item data (for sorting)
        self.itemDataMap = {}
        self.itemQuoteMap = {}
        self.itemTypeMap = {}

        # at least isin and ticker columns !
        self.m_list.InsertColumn(IDC_ISIN, message('isin'), wx.LIST_FORMAT_LEFT)
        self.m_list.InsertColumn(IDC_TICKER, message('ticker'), wx.LIST_FORMAT_LEFT)
        self.m_list.InsertColumn(IDC_PRU, message('UPP'), wx.LIST_FORMAT_RIGHT)

    def populateMatrixEnd(self):
        # fix the item data
        items = self.itemDataMap.items()
        for x in range(len(items)):
            key, data = items[x]
            self.m_list.SetItemData(x, key)

        # adjust columns width
        self.adjustColumns()

        # sort the default column
        self.SortColumn()

        # default selection
        if len(items)>0:
            self.m_currentItem = 0
            self.m_list.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
            self.m_list.EnsureVisible(self.m_currentItem)
        else:
            self.m_currentItem = -1

    # --- [ adjust columns width ] -------------------------------------

    def adjustColumns(self):
        for col in range(self.m_list.GetColumnCount() - 1):
            self.m_list.SetColumnWidth(col, wx.LIST_AUTOSIZE)
            if self.m_list.GetColumnWidth(col) < self.m_hdrcolwidths[col]:
                self.m_list.SetColumnWidth(col, self.m_hdrcolwidths[col])
        self.m_list.resizeLastColumn(15)

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

        if self.m_mustInit:
            # update portfolio and matrix (just in case)
            self.m_portfolio = self.m_parent.m_portfolio
            self.m_matrix = self.m_parent.m_matrix

            # create and display the list
            self.populate(bDuringInit=True)
            self.OnRefresh(None)

            self.m_mustInit = False

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
                        ref = self.OnLiveQuote(evt.quote,xline)
                        if ref and self.needDynamicSortColumn(): self.SortColumn()
                    else:
                        if itrade_config.verbose:
                            print('pane::OnLive %s: %s - bad : other view' % (evt.quote.key(),evt.param))
                        pass
            self.m_parent.refreshConnexion()
        else:
            if itrade_config.verbose:
                print('pane::OnLive %s: %s - bad : not running' % (evt.quote.key(),evt.param))
            pass

    # refresh list
    def OnRefresh(self,e):
        if self.m_portfolio.is_multicurrencies():
            self.refreshCurrencies()
        self.refreshList()

    def updateQuoteItems(self):
        op1 = (self.m_currentItem>=0) and (self.m_currentItem<self.m_maxlines)
        if op1:
            quote,item = self.getQuoteAndItemOnTheLine(self.m_currentItem)
            if not quote:
                if itrade_config.verbose: print('updateQuoteItems:',self.m_currentItem)
                op1 = False
            else:
                if itrade_config.verbose: print('updateQuoteItems:',self.m_currentItem,quote.name())
        else:
            quote = None

        self.m_parent.updateQuoteItems(op1,quote)

# ============================================================================
# iTrade_MatrixPortfolioPanel
# ============================================================================

class iTrade_MatrixPortfolioPanel(iTrade_MatrixPanel):

    def __init__(self,parent,wm,id,portfolio,matrix):
        iTrade_MatrixPanel.__init__(self, parent,wm, id, portfolio, matrix)

    def name(self):
        return "portfolio"

    def map(self,quote,key,xtype):
        if key in self.itemDataMap:
            old = self.itemDataMap[key]
        else:
            old = None
        self.itemDataMap[key] = ( quote.isin(),quote.ticker(),quote.nv_pru(xtype),
                                  quote.nv_number(xtype),quote.nv_pru(xtype),quote.nv_pr(xtype),
                                  quote.nv_close(),quote.nv_percent(),
                                  quote.nv_pv(self.m_portfolio.currency(),xtype),
                                  quote.nv_profit(self.m_portfolio.currency(),xtype),
                                  quote.nv_profitPercent(self.m_portfolio.currency(),xtype),
                                  quote.name()
                                )
        return old

    # populate the portfolio
    def populateList(self):
        self.populateMatrixBegin()

        self.m_list.InsertColumn(IDC_QTY, message('qty'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_NOTUSED, '', wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_PR, message('buy'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_PVU, message('USP'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_PERFDAY, message('perfday'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_PV, message('sell'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_PROFIT, message('profit'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_PERCENT, message('perfper'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_NAME, message('name'), wx.LIST_FORMAT_LEFT)

        # remember columns widths with just the header and no data
        self.m_hdrcolwidths = []
        for col in range(self.m_list.GetColumnCount() - 1):
            self.m_list.SetColumnWidth(col, wx.LIST_AUTOSIZE_USEHEADER)
            self.m_hdrcolwidths.append(self.m_list.GetColumnWidth(col))

        x = 0
        for eachQuote in self.m_matrix.list():
            # in portfolio view, display only traded values !
            if eachQuote.isTraded():
                if eachQuote.nv_number(QUOTE_CASH)>0:
                    self.m_list.InsertImageStringItem(x, eachQuote.isin(), self.idx_tbref)
                    self.m_list.SetStringItem(x,IDC_TICKER,eachQuote.ticker())
                    self.m_list.SetStringItem(x,IDC_QTY,eachQuote.sv_number(QUOTE_CASH))
                    if eachQuote.isTraded():
                        self.m_list.SetStringItem(x,IDC_PRU,"%s %s" % (eachQuote.sv_pru(QUOTE_CASH,"%.2f"),self.m_portfolio.currency_symbol()))
                    else:
                        self.m_list.SetStringItem(x,IDC_PRU,"-")
                    self.m_list.SetStringItem(x,IDC_PR, eachQuote.sv_pr(QUOTE_CASH,fmt="%.0f",bDispCurrency=True))
                    self.m_list.SetStringItem(x,IDC_NAME,eachQuote.name())

                    self.map(eachQuote,x,QUOTE_CASH)
                    self.itemQuoteMap[x] = eachQuote
                    self.itemTypeMap[x] = QUOTE_CASH
                    self.refreshPortfolioLine(x,False)

                    x = x + 1

                if eachQuote.nv_number(QUOTE_CREDIT)>0:
                    self.m_list.InsertImageStringItem(x, eachQuote.isin(), self.idx_tbref)
                    self.m_list.SetStringItem(x,IDC_TICKER,"%s (%s)" % (eachQuote.ticker(),message("money_srd")))
                    self.m_list.SetStringItem(x,IDC_QTY,eachQuote.sv_number(QUOTE_CREDIT))
                    if eachQuote.isTraded():
                        self.m_list.SetStringItem(x,IDC_PRU,"%s %s" % (eachQuote.sv_pru(QUOTE_CREDIT,"%.2f"),self.m_portfolio.currency_symbol()))
                    else:
                        self.m_list.SetStringItem(x,IDC_PRU,"-")
                    self.m_list.SetStringItem(x,IDC_PR, eachQuote.sv_pr(QUOTE_CREDIT,bDispCurrency=True))
                    self.m_list.SetStringItem(x,IDC_NAME,eachQuote.name())

                    self.map(eachQuote,x,QUOTE_CREDIT)
                    self.itemQuoteMap[x] = eachQuote
                    self.itemTypeMap[x] = QUOTE_CREDIT

                    self.refreshPortfolioLine(x,False)

                    x = x + 1

        for eachQuote in self.itemQuoteMap.values():
            self.registerLive(eachQuote,itrade_config.refreshView,self.m_id)

        self.m_list.InsertImageStringItem(x, '', -1)
        self.m_list.SetStringItem(x,IDC_NAME,'')
        self.itemDataMap[x] = ('ZZZZ1','ZZZZ1','ZZZZ1',9999999998,9999999998,9999999998,9999999998,9999999998,9999999998,9999999998,9999999998,'ZZZZ1')
        self.itemQuoteMap[x] = None
        self.itemTypeMap[x] = QUOTE_BOTH
        self.m_list.InsertImageStringItem(x+1, message('main_valuation'), -1)
        self.m_list.SetStringItem(x+1,IDC_NAME,'')
        self.itemDataMap[x+1] = ('ZZZZ2','ZZZZ2','ZZZZ2',9999999999,9999999999,9999999999,9999999999,9999999999,9999999999,9999999999,9999999999,'ZZZZ2')
        self.itemQuoteMap[x+1] = None
        self.itemTypeMap[x+1] = QUOTE_BOTH

        self.m_maxlines = x + 2

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

    # refresh one portfolio line
    def refreshPortfolioLine(self,x,disp):
        key = self.m_list.GetItemData(x)
        quote = self.itemQuoteMap[key]
        if quote==None: return False

        xtype = self.itemTypeMap[key]
        item  = self.m_list.GetItem(x)

        bRef = False

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

            pp = self.map(quote,key,xtype)
            bRef = (pp != self.itemDataMap[key])

        else:
            item.SetTextColour(wx.BLACK)
            item.SetImage(self.idx_tbref)
            self.m_list.SetStringItem(x,IDC_PVU," ---.-- ")
            self.m_list.SetStringItem(x,IDC_PERFDAY," ---.-- % ")
            self.m_list.SetStringItem(x,IDC_PV," ---.-- %s" % self.m_portfolio.currency_symbol())
            self.m_list.SetStringItem(x,IDC_PROFIT," ----.-- %s" % self.m_portfolio.currency_symbol())
            self.m_list.SetStringItem(x,IDC_PERCENT," +---.-- % ")

        self.m_list.SetItem(item)

        return bRef

    # refresh all the portfolio
    def refreshList(self):
        keepGoing = True
        if self.m_parent.hasFocus():
            dlg = wx.ProgressDialog(message('main_refreshing'),"",self.m_maxlines,self,wx.PD_CAN_ABORT | wx.PD_APP_MODAL)
        else:
            dlg = None

        for xline in range(0,self.m_maxlines):
            if keepGoing:
                key = self.m_list.GetItemData(xline)
                quote = self.itemQuoteMap[key]
                if quote:
                    if dlg:
                        keepGoing = dlg.Update(xline,quote.name())
                    quote.update()
                    self.refreshPortfolioLine(xline,True)

        self.m_portfolio.computeOperations()
        if self.m_sort_colasc:
            key = self.m_maxlines-1
        else:
            key = 0
        self.refreshEvalLine(key)

        if dlg:
            dlg.Destroy()

    def OnLiveQuote(self,quote,xline):
        return self.refreshPortfolioLine(xline,True)

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
        menu.Enable(self.m_popupID_Live,inList and quote!=None and quote.liveconnector().hasNotebook())
        menu.Append(self.m_popupID_Properties, message('main_popup_properties'))
        menu.Enable(self.m_popupID_Properties,inList)
        menu.AppendSeparator()
        menu.Append(self.m_popupID_Buy, message('main_popup_buy'))
        menu.Append(self.m_popupID_Sell, message('main_popup_sell'))

        # return the menu
        return menu

# ============================================================================
# iTrade_MatrixQuotesPanel
# ============================================================================

class iTrade_MatrixQuotesPanel(iTrade_MatrixPanel):

    def __init__(self,parent,wm,id,portfolio,matrix):
        iTrade_MatrixPanel.__init__(self, parent,wm, id, portfolio, matrix)

    def name(self):
        return "quotes"

    def map(self,quote,key,xtype):
        if key in self.itemDataMap:
            old = self.itemDataMap[key]
        else:
            old = None
        self.itemDataMap[key] = (quote.isin(),quote.ticker(),quote.nv_pru(xtype),quote.nv_volume(),
                                 quote.nv_prevclose(),quote.nv_open(),quote.nv_high(),quote.nv_low(),
                                 quote.nv_close(),quote.sv_pivots(),quote.nv_percent(),quote.name())
        return old

    # populate quotes
    def populateList(self):
        self.populateMatrixBegin()

        self.m_list.InsertColumn(IDC_VOLUME, message('volume'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_PREV, message('prev'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_OPEN, message('open'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_HIGH, message('high'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_LOW,  message('low'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_CLOSE,message('last'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_PIVOTS,message('pivots'), wx.LIST_FORMAT_LEFT)
        self.m_list.InsertColumn(IDC_PERCENT, ' % ', wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_NAME, message('name'), wx.LIST_FORMAT_LEFT)

        # remember columns widths with just the header and no data
        self.m_hdrcolwidths = []
        for col in range(self.m_list.GetColumnCount() - 1):
            self.m_list.SetColumnWidth(col, wx.LIST_AUTOSIZE_USEHEADER)
            self.m_hdrcolwidths.append(self.m_list.GetColumnWidth(col))

        x = 0
        for eachQuote in self.m_matrix.list():
            if (eachQuote.isTraded() or eachQuote.isMonitored()):
                self.m_list.InsertImageStringItem(x, eachQuote.isin(), self.idx_tbref)
                self.m_list.SetStringItem(x,IDC_TICKER,eachQuote.ticker())
                if eachQuote.isTraded():
                    self.m_list.SetStringItem(x,IDC_PRU,"%s %s" % (eachQuote.sv_pru(QUOTE_BOTH,"%.2f"),self.m_portfolio.currency_symbol()))
                else:
                    self.m_list.SetStringItem(x,IDC_PRU,"-")
                self.m_list.SetStringItem(x,IDC_NAME,eachQuote.name())

                self.map(eachQuote,x,QUOTE_BOTH)
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
        bRef = False

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

                key = self.m_list.GetItemData(x)
                pp = self.map(quote,key,QUOTE_BOTH)
                bRef = (pp != self.itemDataMap[key])

            else:
                # not already opened today ...
                self.m_list.SetStringItem(x,IDC_OPEN," ---.-- ")
                self.m_list.SetStringItem(x,IDC_HIGH," ---.-- ")
                self.m_list.SetStringItem(x,IDC_LOW," ---.-- ")
                self.m_list.SetStringItem(x,IDC_PIVOTS," ---- (-.--) ")
                self.m_list.SetStringItem(x,IDC_VOLUME," ---------- ")
                color = QUOTE_NOCHANGE
        else:
            self.m_list.SetStringItem(x,IDC_PREV," ---.-- ")
            self.m_list.SetStringItem(x,IDC_CLOSE," ----.-- %s " % quote.currency_symbol())
            self.m_list.SetStringItem(x,IDC_OPEN," ---.-- ")
            self.m_list.SetStringItem(x,IDC_HIGH," ---.-- ")
            self.m_list.SetStringItem(x,IDC_LOW," ---.-- ")
            self.m_list.SetStringItem(x,IDC_PIVOTS," ---- (-.--) ")
            self.m_list.SetStringItem(x,IDC_VOLUME," ---------- ")
            self.m_list.SetStringItem(x,IDC_PERCENT," +---.-- % ")
            color = QUOTE_INVALID

        self.refreshColorLine(x,color)

        # __x not working : change the full line :-(
        # __x item = self.m_list.GetItem(x,IDC_PREV)
        # __x item.SetTextColour(wx.BLACK)
        # __x self.m_list.SetItem(item)

        return bRef

    # refresh all quotes
    def refreshList(self):
        keepGoing = True
        if self.m_parent.hasFocus():
            dlg = wx.ProgressDialog(message('main_refreshing'),"",self.m_maxlines,self,wx.PD_CAN_ABORT | wx.PD_APP_MODAL)
        else:
            dlg = None

        for xline in range(0,self.m_maxlines):
            if keepGoing:
                key = self.m_list.GetItemData(xline)
                quote = self.itemQuoteMap[key]
                if dlg:
                    keepGoing = dlg.Update(xline,quote.name())
                quote.update()
                self.refreshQuoteLine(xline,True)

        if dlg:
            dlg.Destroy()

    def OnLiveQuote(self, quote, xline):
        return self.refreshQuoteLine(xline,True)

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
        menu.Append(self.m_popupID_Sell, message('main_popup_sell'))
        menu.AppendSeparator()
        menu.Append(self.m_popupID_Remove, message('main_popup_remove'))
        menu.Enable(self.m_popupID_Remove,inList and not quote.isTraded())

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

    def name(self):
        return "stops"

    def map(self,quote,key,xtype):
        if key in self.itemDataMap:
            old = self.itemDataMap[key]
        else:
            old = None
        self.itemDataMap[key] = ( quote.isin(),quote.ticker(),quote.nv_pru(xtype),
                                  quote.nv_pr(),quote.nv_riskmoney(self.m_portfolio.currency()),
                                  quote.nv_stoploss(),quote.nv_close(),quote.nv_stopwin(),
                                  quote.nv_pv(self.m_portfolio.currency()),
                                  quote.nv_profit(self.m_portfolio.currency()),
                                  quote.nv_profitPercent(self.m_portfolio.currency()),
                                  quote.name()
                                )
        return old

    # populate stops
    def populateList(self):
        self.populateMatrixBegin()

        self.m_list.InsertColumn(IDC_INVEST, message('buy'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_RISKM, message('risk'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_STOPLOSS, message('stop_minus'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_CURRENT, message('last'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_STOPWIN, message('stop_plus'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_PV, message('sell'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_PROFIT, message('profit'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_PERCENT, ' % ', wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_NAME, message('name'), wx.LIST_FORMAT_LEFT)

        # remember columns widths with just the header and no data
        self.m_hdrcolwidths = []
        for col in range(self.m_list.GetColumnCount() - 1):
            self.m_list.SetColumnWidth(col, wx.LIST_AUTOSIZE_USEHEADER)
            self.m_hdrcolwidths.append(self.m_list.GetColumnWidth(col))

        x = 0
        for eachQuote in self.m_matrix.list():
            # in portfolio view, display only traded values !
            if eachQuote.hasStops() and (eachQuote.isTraded() or eachQuote.isMonitored()):
                self.m_list.InsertImageStringItem(x, eachQuote.isin(), self.idx_tbref)
                self.m_list.SetStringItem(x,IDC_TICKER,eachQuote.ticker())
                if eachQuote.isTraded():
                    self.m_list.SetStringItem(x,IDC_PRU,"%s %s" % (eachQuote.sv_pru(QUOTE_BOTH,"%.2f"),self.m_portfolio.currency_symbol()))
                else:
                    self.m_list.SetStringItem(x,IDC_PRU,"-")
                self.m_list.SetStringItem(x,IDC_STOPLOSS,"~ %s " % eachQuote.sv_stoploss())
                self.m_list.SetStringItem(x,IDC_STOPWIN,"~ %s " % eachQuote.sv_stopwin())
                self.m_list.SetStringItem(x,IDC_NAME,eachQuote.name())

                self.map(eachQuote,x,QUOTE_BOTH)
                self.itemQuoteMap[x] = eachQuote
                self.itemTypeMap[x] = QUOTE_BOTH

                self.refreshStopLine(x,False)

                x = x + 1

        self.m_maxlines = x
        for eachQuote in self.itemQuoteMap.values():
            self.registerLive(eachQuote,itrade_config.refreshView,self.m_id)

        # finish populating
        self.populateMatrixEnd()

    # refresh one stop
    def refreshStopLine(self,x,disp):
        quote,item = self.getQuoteAndItemOnTheLine(x)
        bRef = False

        if disp:
            color = quote.colorStop()
            self.m_list.SetStringItem(x,IDC_CURRENT,quote.sv_close(bDispCurrency=True))
            if color==QUOTE_GREEN:
                self.m_list.SetStringItem(x,IDC_INVEST, "")
                self.m_list.SetStringItem(x,IDC_RISKM, "")
                self.m_list.SetStringItem(x,IDC_PV,"")
                self.m_list.SetStringItem(x,IDC_PROFIT,"")
                self.m_list.SetStringItem(x,IDC_PERCENT,"")
            else:
                self.m_list.SetStringItem(x,IDC_INVEST, quote.sv_pr(fmt="%.0f",bDispCurrency=True))
                self.m_list.SetStringItem(x,IDC_RISKM, quote.sv_riskmoney(self.m_portfolio.currency(),self.m_portfolio.currency_symbol()))
                self.m_list.SetStringItem(x,IDC_PV,"%s %s" % (quote.sv_pv(self.m_portfolio.currency(),fmt="%.0f"),self.m_portfolio.currency_symbol()))
                self.m_list.SetStringItem(x,IDC_PROFIT,"%s %s" % (quote.sv_profit(self.m_portfolio.currency(),fmt="%.0f"),self.m_portfolio.currency_symbol()))
                self.m_list.SetStringItem(x,IDC_PERCENT,quote.sv_profitPercent(self.m_portfolio.currency()))

                key = self.m_list.GetItemData(x)
                pp = self.map(quote,key,QUOTE_BOTH)
                bRef = (pp != self.itemDataMap[key])
        else:
            self.m_list.SetStringItem(x,IDC_INVEST, " ------ %s" % self.m_portfolio.currency_symbol())
            self.m_list.SetStringItem(x,IDC_RISKM, " ------ %s" % self.m_portfolio.currency_symbol())
            self.m_list.SetStringItem(x,IDC_CURRENT," ---.-- %s " % quote.currency_symbol())
            self.m_list.SetStringItem(x,IDC_PV," ------ %s" % self.m_portfolio.currency_symbol())
            self.m_list.SetStringItem(x,IDC_PROFIT," ------ %s" % self.m_portfolio.currency_symbol())
            self.m_list.SetStringItem(x,IDC_PERCENT," +---.-- % ")
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
        return bRef

    # refresh all the stop
    def refreshList(self):
        keepGoing = True
        if self.m_parent.hasFocus():
            dlg = wx.ProgressDialog(message('main_refreshing'),"",self.m_maxlines,self,wx.PD_CAN_ABORT | wx.PD_APP_MODAL)
        else:
            dlg = None

        for xline in range(0,self.m_maxlines):
            if keepGoing:
                key = self.m_list.GetItemData(xline)
                quote = self.itemQuoteMap[key]
                if dlg:
                    keepGoing = dlg.Update(xline,quote.name())
                quote.update()
                self.refreshStopLine(xline,True)

        if dlg:
            dlg.Destroy()

    def OnLiveQuote(self,quote,xline):
        return self.refreshStopLine(xline,True)

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
            wx.EVT_MENU(self, self.m_popupID_Edit, self.OnPopup_Edit)
            wx.EVT_MENU(self, self.m_popupID_Remove, self.OnPopup_Remove)

        # make a menu
        menu = wx.Menu()

        # add some items
        menu.Append(self.m_popupID_Update, message('main_popup_refreshall'))
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

        # return the menu
        return menu

    def OnPopup_Add(self, event):
        #debug("OnPopup_Add")
        self.m_parent.OnAddStops(event)

    def OnPopup_Edit(self, event):
        #debug("OnPopup_Edit")
        self.m_parent.OnEditStops(event)

    def OnPopup_Remove(self, event):
        #debug("OnPopup_Remove")
        self.m_parent.OnRemoveStops(event)

# ============================================================================
# iTrade_MatrixIndicatorsPanel
# ============================================================================

class iTrade_MatrixIndicatorsPanel(iTrade_MatrixPanel):

    def __init__(self,parent,wm,id,portfolio,matrix):
        iTrade_MatrixPanel.__init__(self, parent,wm, id, portfolio, matrix)

    def name(self):
        return "indicators"

    def needDynamicSortColumn(self):
        if self.m_sort_colnum<IDC_PRU:
            return False
        return True

    def map(self,quote,key,xtype):
        if key in self.itemDataMap:
            old = self.itemDataMap[key]
        else:
            old = None
        self.itemDataMap[key] = ( quote.isin(),quote.ticker(),quote.nv_pru(xtype),
                                  quote.nv_ma(20),quote.nv_ma(50),quote.nv_ma(100),
                                  quote.nv_rsi(14),key,quote.nv_stoK(),
                                  key,key,key,
                                  quote.nv_close()
                                )
        return old

    # populate indicators
    def populateList(self):
        self.populateMatrixBegin()

        self.m_list.InsertColumn(IDC_MA20, 'MMA20', wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_MA50, 'MMA50', wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_MA100, 'MMA100', wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_RSI, 'RSI (%s)'%14, wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_MACD, 'MACD', wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_STOCH, 'STO %K (%D)', wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_DMI, 'DMI', wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_EMV, 'EMV', wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_OVB, 'OVB', wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_LAST, message('last'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_LAST+1, '', wx.LIST_FORMAT_RIGHT)

        # remember columns widths with just the header and no data
        self.m_hdrcolwidths = []
        for col in range(self.m_list.GetColumnCount() - 1):
            self.m_list.SetColumnWidth(col, wx.LIST_AUTOSIZE_USEHEADER)
            self.m_hdrcolwidths.append(self.m_list.GetColumnWidth(col))

        x = 0
        for eachQuote in self.m_matrix.list():
            if (eachQuote.isTraded() or eachQuote.isMonitored()):
                self.m_list.InsertImageStringItem(x, eachQuote.isin(), self.idx_tbref)
                self.m_list.SetStringItem(x,IDC_TICKER,eachQuote.ticker())
                if eachQuote.isTraded():
                    self.m_list.SetStringItem(x,IDC_PRU,eachQuote.sv_pru(QUOTE_BOTH,"%.3f",False))
                else:
                    self.m_list.SetStringItem(x,IDC_PRU,"-")

                self.map(eachQuote,x,QUOTE_BOTH)
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
        bRef = False

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

            key = self.m_list.GetItemData(x)

            pp = self.map(quote,key,QUOTE_BOTH)
            bRef = (pp != self.itemDataMap[key])

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
            self.m_list.SetStringItem(x,IDC_LAST," ----.-- %s " % quote.currency_symbol())
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

        return bRef

    # refresh all indicators
    def refreshList(self):
        keepGoing = True
        if self.m_parent.hasFocus():
            dlg = wx.ProgressDialog(message('main_refreshing'),"",self.m_maxlines,self,wx.PD_CAN_ABORT | wx.PD_APP_MODAL)
        else:
            dlg = None

        for xline in range(0,self.m_maxlines):
            if keepGoing:
                key = self.m_list.GetItemData(xline)
                quote = self.itemQuoteMap[key]
                if dlg:
                    keepGoing = dlg.Update(xline,quote.name())
                quote.update()
                self.refreshIndicatorLine(xline,True)

        if dlg:
            dlg.Destroy()

    def OnLiveQuote(self, quote, xline):
        quote.compute()
        return self.refreshIndicatorLine(xline,True)

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
        menu.Append(self.m_popupID_Sell, message('main_popup_sell'))

        # return the menu
        return menu

# ============================================================================
# iTrade_TradingPanel
# ============================================================================

class iTrade_TradingPanel(wx.Panel):

    def __init__(self,parent,wm,id,portfolio,matrix):
        wx.Panel.__init__(self, parent, id)
        self.m_parent = parent
        self.m_portfolio = portfolio
        self.m_matrix = matrix

    # ---[ Window Management ]-------------------------------------------------

    def InitCurrentPage(self,bReset=True):
        if bReset:
            # update portfolio and matrix (just in case)
            self.m_portfolio = self.m_parent.m_portfolio
            self.m_matrix = self.m_parent.m_matrix

        # refresh page content
        self.refresh()

    def DoneCurrentPage(self):
        pass

    # ---[ Create page content ]-----------------------------------------------

    def refresh(self):
        pass

# ============================================================================
# That's all folks !
# ============================================================================
