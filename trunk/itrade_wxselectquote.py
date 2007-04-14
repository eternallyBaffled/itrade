#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxselectquote.py
#
# Description: wxPython list quote selection
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
# 2005-10-31    dgil  from itrade_wxlistquote.py
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import os
import logging
import webbrowser
import datetime
import locale

# wxPython system
import itrade_wxversion
import wx
import wx.lib.mixins.listctrl as wxl
import wxaddons.sized_controls as sc

# iTrade system
from itrade_logging import *
from itrade_quotes import *
from itrade_local import message
from itrade_config import *
from itrade_market import list_of_markets,market2place
from itrade_isin import checkISIN
from itrade_defs import *
from itrade_ext import *

from itrade_wxmixin import iTradeSelectorListCtrl
from itrade_wxutil import iTradeSizedDialog

# ============================================================================
# iTradeQuoteSelector
# ============================================================================

IDC_ISIN = 0
IDC_TICKER = 1
IDC_NAME = 2
IDC_PLACE = 3
IDC_MARKET = 4

import wx.lib.newevent
(PostInitEvent,EVT_POSTINIT) = wx.lib.newevent.NewEvent()

class iTradeQuoteSelectorListCtrlDialog(iTradeSizedDialog, wxl.ColumnSorterMixin):
    def __init__(self, parent, quote, filter = False, market = None, filterEnabled=True, tradableOnly=False):

        iTradeSizedDialog.__init__(self,parent,-1,message('quote_select_title'), size=(460, 460),style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.m_parent = parent

        # init
        if quote:
            self.m_isin = quote.isin()
            self.m_ticker = quote.ticker()
            self.m_market = quote.market()
            self.m_place = quote.place()
        else:
            self.m_isin = ''
            self.m_ticker = ''
            self.m_market = market
            self.m_place = market2place(market)

        self.m_filter = filter
        self.m_qlist = QLIST_ALL
        self.m_qlist_tradableOnly = tradableOnly

        self.m_editing = True

        tID = wx.NewId()
        self.m_imagelist = wx.ImageList(16,16)
        self.sm_q = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'quote.png')))
        self.sm_i = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'invalid.png')))
        self.sm_up = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'sm_up.png')))
        self.sm_dn = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'sm_down.png')))

        # container
        container = self.GetContentsPane()
        container.SetSizerType("vertical")

        # resizable pane
        pane = sc.SizedPanel(container, -1)
        pane.SetSizerType("horizontal")
        pane.SetSizerProps(expand=True)

        # pane : ISIN or Name selection
        label = wx.StaticText(pane, -1, message('quote_select_isin'))
        label.SetSizerProps(valign='center')

        tID = wx.NewId()
        self.wxIsinCtrl = wx.TextCtrl(pane, tID, self.m_isin)
        self.wxIsinCtrl.SetSizerProps(expand=True)
        wx.EVT_TEXT(self, tID, self.OnISINEdited)

        label = wx.StaticText(pane, -1, message('quote_select_ticker'))
        label.SetSizerProps(valign='center')

        tID = wx.NewId()
        self.wxTickerCtrl = wx.TextCtrl(pane, tID, self.m_ticker)
        self.wxTickerCtrl.SetSizerProps(expand=True)
        wx.EVT_TEXT(self, tID, self.OnTickerEdited)

        # resizable pane
        pane = sc.SizedPanel(container, -1)
        pane.SetSizerType("horizontal")
        pane.SetSizerProps(expand=True)

        # pane : market & list filters
        self.wxLabelMarketCtrl = wx.StaticText(pane, -1, message('quote_select_market'))
        self.wxLabelMarketCtrl.SetSizerProps(valign='center')

        self.wxMarketCtrl = wx.ComboBox(pane,-1, "", style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.wxMarketCtrl.SetSizerProps(expand=True)
        wx.EVT_COMBOBOX(self,self.wxMarketCtrl.GetId(),self.OnMarket)

        count = 0
        idx = 0
        for eachCtrl in list_of_markets(bFilterMode=False):
            self.wxMarketCtrl.Append(eachCtrl,eachCtrl)
            if eachCtrl==self.m_market:
                idx = count
            count = count + 1

        self.wxMarketCtrl.SetSelection(idx)

        self.wxLabelQListCtrl = wx.StaticText(pane, -1, message('quote_select_list'))
        self.wxLabelQListCtrl.SetSizerProps(valign='center')

        self.wxQListCtrl = wx.ComboBox(pane,-1, "", style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.wxQListCtrl.SetSizerProps(expand=True)
        wx.EVT_COMBOBOX(self,self.wxQListCtrl.GetId(),self.OnQuoteList)

        self.wxQListCtrl.Append(message('quote_select_alllist'),QLIST_ALL)
        self.wxQListCtrl.Append(message('quote_select_syslist'),QLIST_SYSTEM)
        self.wxQListCtrl.Append(message('quote_select_usrlist'),QLIST_USER)
        if not self.m_qlist_tradableOnly:
            self.wxQListCtrl.Append(message('quote_select_indiceslist'),QLIST_INDICES)
        self.wxQListCtrl.Append(message('quote_select_trackerslist'),QLIST_TRACKERS)
        self.wxQListCtrl.SetSelection(self.m_qlist)

        # select traded or not
        tID = wx.NewId()
        self.wxFilterCtrl = wx.CheckBox(container, tID, message('quote_select_filterfield'))
        self.wxFilterCtrl.SetValue(self.m_filter)
        wx.EVT_CHECKBOX(self, tID, self.OnFilter)
        self.wxFilterCtrl.Enable(filterEnabled)

        # List
        self.m_list = iTradeSelectorListCtrl(container, tID, style = wx.LC_REPORT | wx.SUNKEN_BORDER,size=(440, 380))
        self.m_list.SetSizerProps(expand=True)
        self.m_list.SetImageList(self.m_imagelist, wx.IMAGE_LIST_SMALL)

        # Now that the list exists we can init the other base class,
        # see wxPython/lib/mixins/listctrl.py
        wxl.ColumnSorterMixin.__init__(self, 5)

        wx.EVT_LIST_COL_CLICK(self, tID, self.OnColClick)
        wx.EVT_LIST_ITEM_ACTIVATED(self, tID, self.OnItemActivated)
        wx.EVT_LIST_ITEM_SELECTED(self, tID, self.OnItemSelected)

        # Last Row : OK and Cancel
        btnpane = sc.SizedPanel(container, -1)
        btnpane.SetSizerType("horizontal")
        btnpane.SetSizerProps(expand=True)

        # context help
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)

        # OK
        self.wxOK = wx.Button(btnpane, wx.ID_OK, message('valid'))
        self.wxOK.SetDefault()
        self.wxOK.SetHelpText(message('valid_desc'))
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnValid)

        # CANCEL
        btn = wx.Button(btnpane, wx.ID_CANCEL, message('cancel'))
        btn.SetHelpText(message('cancel_desc'))

        # set the right filter and fit everything
        self.OnFilter()

        EVT_POSTINIT(self, self.OnPostInit)
        wx.PostEvent(self,PostInitEvent())

    # --- [ window management ] -------------------------------------

    def OnPostInit(self,event):
        self.PopulateList(bDuringInit=True)
        self.wxTickerCtrl.SetFocus()
        print 'OnPostInit : market=',self.m_market

    def resetFields(self):
        self.m_isin = ''
        self.m_ticker = ''
        self.wxIsinCtrl.SetLabel('')
        self.wxTickerCtrl.SetLabel('')
        self.m_list.SetFocus()

    def OnFilter(self,event=None):
        if event:
            self.m_filter = event.Checked()
            self.resetFields()

        if self.m_filter:
            self.wxMarketCtrl.Show(False)
            self.wxLabelMarketCtrl.Show(False)
            self.wxQListCtrl.Show(False)
            self.wxLabelQListCtrl.Show(False)
        else:
            self.wxMarketCtrl.Show(True)
            self.wxLabelMarketCtrl.Show(True)
            self.wxQListCtrl.Show(True)
            self.wxLabelQListCtrl.Show(True)

        self.Fit()
        self.SetMinSize(self.GetSize())

        print 'OnFilter : market=',self.m_market

    def OnMarket(self,evt):
        idx = self.wxMarketCtrl.GetSelection()
        self.m_market = self.wxMarketCtrl.GetClientData(idx)
        self.resetFields()

    def OnQuoteList(self,evt):
        idx = self.wxQListCtrl.GetSelection()
        self.m_qlist = idx
        self.resetFields()

    def isFiltered(self,quote,bDuringInit):
        if (self.m_qlist == QLIST_ALL) or (self.m_qlist == quote.list() or self.m_filter):
            # good list
            if (not self.m_qlist_tradableOnly or quote.list() != QLIST_INDICES):
                # tradable
                if (self.m_market==None) or (self.m_market == quote.market() or self.m_filter):
                    # good market
                    if bDuringInit or ( quote.ticker().find(self.m_ticker,0)==0 and quote.isin().find(self.m_isin,0)==0 ):
                        # begin the same
                        return True
        return False

    def PopulateList(self,bDuringInit=False):
        wx.SetCursor(wx.HOURGLASS_CURSOR)

        # clear list
        self.m_list.ClearAll()
        self.currentItem = -1

        # but since we want images on the column header we have to do it the hard way:
        self.m_list.InsertColumn(IDC_ISIN, message('isin'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_TICKER, message('ticker'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_NAME, message('name'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PLACE, message('place'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_MARKET, message('market'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)

        x = 0

        self.itemDataMap = {}
        self.itemQuoteMap = {}
        self.itemLineMap = {}

        for eachQuote in quotes.list():
            if (not self.m_filter or eachQuote.isMatrix()) and self.isFiltered(eachQuote,bDuringInit):
                self.itemDataMap[x] = (eachQuote.isin(),eachQuote.ticker(),eachQuote.name(),eachQuote.place(),eachQuote.market())
                self.itemQuoteMap[x] = eachQuote
                x = x + 1

        items = self.itemDataMap.items()
        line = 0
        curline = -1
        for x in range(len(items)):
            key, data = items[x]
            if data[0]!='':
                self.m_list.InsertImageStringItem(line, data[0], self.sm_q)
            else:
                self.m_list.InsertImageStringItem(line, data[0], self.sm_i)
            if data[0] == self.m_isin and data[1]== self.m_ticker and data[3] == self.m_place and data[4] == self.m_market:
                # current selection
                curline = line
            self.m_list.SetStringItem(line, IDC_TICKER, data[1])
            self.m_list.SetStringItem(line, IDC_NAME, data[2])
            self.m_list.SetStringItem(line, IDC_PLACE, data[3])
            self.m_list.SetStringItem(line, IDC_MARKET, data[4])
            self.m_list.SetItemData(line, key)
            self.itemLineMap[data[1]] = line
            line += 1

        self.m_list.SetColumnWidth(IDC_ISIN, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_TICKER, wx.LIST_AUTOSIZE_USEHEADER)
        self.m_list.SetColumnWidth(IDC_NAME, 16*10)
        self.m_list.SetColumnWidth(IDC_PLACE, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_MARKET, wx.LIST_AUTOSIZE)
        self.SetCurrentItem(curline)

        wx.SetCursor(wx.STANDARD_CURSOR)

    def SetCurrentItem(self,line):
        #print 'SetCurrentItem: line=%d' % line
        if self.currentItem==line: return

        if self.currentItem>=0:
            self.m_list.SetItemState(self.currentItem, 0, wx.LIST_STATE_SELECTED)
        self.currentItem = line
        if self.currentItem>=0:
            self.m_list.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
            self.m_list.EnsureVisible(self.currentItem)

    # --- [ wxl.ColumnSorterMixin management ] -------------------------------------

    # Used by the wxl.ColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.m_list

    # Used by the wxl.ColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)

    def getQuoteOnTheLine(self,x):
        if x>=0:
            key = self.m_list.GetItemData(x)
            quote = self.itemQuoteMap[key]
            #print 'getQuoteOnTheLine(%d) : returns key=%d quote=%s' % (x,key,quote.ticker())
            return quote
        else:
            return None

    # --- [ On handlers management ] -------------------------------------

    def OnColClick(self, event):
        #debug("OnColClick: %d\n" % event.GetColumn())
        pass

    def OnTickerEdited(self,event):
        self.m_ticker = event.GetString().upper()
        #print 'ticker: (editing=%d) :' % self.m_editing,self.m_ticker,' currentItem:',self.currentItem

        if self.m_ticker!='':
            if self.m_editing:
                lst = quotes.lookupPartialTicker(self.m_ticker,self.m_market)
            else:
                lst = [quotes.lookupTicker(self.m_ticker,self.m_market)]
            if len(lst)==1:
                quote = lst[0]
                if quote and self.m_ticker == quote.ticker():
                    self.m_isin = quote.isin()
                    self.m_place = quote.place()
                else:
                    self.m_isin = ''
                    self.m_place = ''
                    self.wxIsinCtrl.SetLabel('')
            else:
                self.m_isin = ''
                self.m_place = ''
                self.wxIsinCtrl.SetLabel('')

        if self.m_editing:
            # refresh filtering begin of ticker
            self.PopulateList()
        self.m_editing = True
        event.Skip()

    def OnISINEdited(self,event):
        isin = event.GetString().upper()
        if isin!='' and isin!=self.m_isin:
            self.m_isin = isin
            lst = quotes.lookupISIN(self.m_isin,self.m_market)
            if len(lst)>0 and lst[0]:
                quote = lst[0]
                self.m_isin = quote.isin()
                self.m_ticker = quote.ticker()
                self.m_place = quote.place()
                v = self.wxTickerCtrl.GetLabel()
                #print 'isin:',isin,' label %s=?=%s' % (v,quote.ticker()), 'line=%d' % self.itemLineMap[quote.ticker()]
                if v!= quote.ticker():
                    self.wxTickerCtrl.SetLabel(quote.ticker())
            else:
                self.wxTickerCtrl.SetLabel('')
        #print 'isin:',isin,' currentItem:',self.currentItem
        event.Skip()

    def OnItemActivated(self, event):
        self.currentItem = event.m_itemIndex
        self.OnValid(event)
        event.Skip()

    def OnItemSelected(self, event):
        #print 'OnItemSelected --['
        # be sure we come from a click and not some editing in ticker/isin controls
        self.currentItem = event.m_itemIndex
        quote = self.getQuoteOnTheLine(self.currentItem)
        #print 'OnItemSelected:',quote,' currentItem:',self.currentItem
        self.m_editing = False
        self.m_isin = quote.isin()
        self.m_place = quote.place()
        self.m_ticker = quote.ticker()
        #if self.m_isin != self.wxIsinCtrl.GetLabel():
        self.wxIsinCtrl.SetLabel(self.m_isin)
        #if self.m_ticker != self.wxTickerCtrl.GetLabel():
        self.wxTickerCtrl.SetLabel(self.m_ticker)
        event.Skip()
        #print ']-- OnItemSelected'

    def OnValid(self,event):
        self.quote = self.getQuoteOnTheLine(self.currentItem)
        #print 'OnItemSelected:',self.quote,' item:',self.currentItem
        if self.quote:
            self.EndModal(wx.ID_OK)

# ============================================================================
# select_iTradeQuote
#
#   win             parent window
#   dquote          Quote object or ISIN reference
#   filter          display only 'is traded' symbols
#   market          filter to given market
#   filterEnabled   can use the filter
# ============================================================================

def select_iTradeQuote(win,dquote=None,filter=False,market=None,filterEnabled=True,tradableOnly=False):
    dlg = iTradeQuoteSelectorListCtrlDialog(win,dquote,filter,market,filterEnabled,tradableOnly)
    if dlg.ShowModal()==wx.ID_OK:
        info('select_iTradeQuote() : %s' % dlg.quote)
        quote = dlg.quote
    else:
        quote = None
    dlg.Destroy()
    return quote

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    app = wx.PySimpleApp()

    # load configuration
    import itrade_config
    itrade_config.loadConfig()

    from itrade_local import *
    setLang('us')
    gMessage.load()

    # load extensions
    import itrade_ext
    itrade_ext.loadExtensions(itrade_config.fileExtData,itrade_config.dirExtData)

    # init modules
    initQuotesModule()

    q = select_iTradeQuote(None,None,filter=False,market='EURONEXT')
    if q:
        print q.name()

# ============================================================================
# That's all folks !
# ============================================================================
