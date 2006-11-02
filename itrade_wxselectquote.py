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

# iTrade system
from itrade_logging import *
from itrade_quotes import *
from itrade_local import message
from itrade_config import *
from itrade_market import list_of_markets
from itrade_isin import checkISIN

from itrade_wxmixin import iTradeSelectorListCtrl

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

class iTradeQuoteSelectorListCtrlDialog(wx.Dialog, wxl.ColumnSorterMixin):
    def __init__(self, parent, quote, filter = False, market = None):
        # context help
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        title = message('quote_select_title')
        pre.Create(parent, -1, title, size=(460, 460))
        self.PostCreate(pre)

        self.m_parent = parent

        # init
        if quote:
            self.m_isin = quote.isin()
            self.m_ticker = quote.ticker()
            self.m_market = quote.market()
            self.m_qlist = quote.list()
        else:
            self.m_isin = ''
            self.m_ticker = ''
            self.m_market = market
            self.m_qlist = QLIST_ALL

        self.m_filter = filter

        tID = wx.NewId()
        self.m_imagelist = wx.ImageList(16,16)
        self.sm_q = self.m_imagelist.Add(wx.Bitmap('res/invalid.gif'))
        self.sm_up = self.m_imagelist.Add(wx.Bitmap('res/sm_up.gif'))
        self.sm_dn = self.m_imagelist.Add(wx.Bitmap('res/sm_down.gif'))

        self.m_list = iTradeSelectorListCtrl(self, tID,
                                 style = wx.LC_REPORT | wx.SUNKEN_BORDER,
                                 size=(440, 380)
                                 )
        self.m_list.SetImageList(self.m_imagelist, wx.IMAGE_LIST_SMALL)

        # Now that the list exists we can init the other base class,
        # see wxPython/lib/mixins/listctrl.py
        wxl.ColumnSorterMixin.__init__(self, 5)

        wx.EVT_LIST_COL_CLICK(self, tID, self.OnColClick)
        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_LIST_ITEM_ACTIVATED(self, tID, self.OnItemActivated)
        wx.EVT_LIST_ITEM_SELECTED(self, tID, self.OnItemSelected)

        sizer = wx.BoxSizer(wx.VERTICAL)

        # ISIN or name selection
        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, message('quote_select_isin'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        tID = wx.NewId()
        self.wxIsinCtrl = wx.TextCtrl(self, tID, self.m_isin, size=(40,-1))
        wx.EVT_TEXT(self, tID, self.OnISINEdited)
        box.Add(self.wxIsinCtrl, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        label = wx.StaticText(self, -1, message('quote_select_ticker'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        tID = wx.NewId()
        self.wxTickerCtrl = wx.TextCtrl(self, tID, self.m_ticker, size=(80,-1))
        wx.EVT_TEXT(self, tID, self.OnTickerEdited)
        box.Add(self.wxTickerCtrl, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # market filter
        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, message('quote_select_market'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.wxMarketCtrl = wx.ComboBox(self,-1, "", size=wx.Size(140,-1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
        box.Add(self.wxMarketCtrl, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_COMBOBOX(self,self.wxMarketCtrl.GetId(),self.OnMarket)

        count = 0
        idx = 0
        for eachCtrl in list_of_markets(bFilterMode=False):
            self.wxMarketCtrl.Append(eachCtrl,eachCtrl)
            if eachCtrl==self.m_market:
                idx = count
            count = count + 1

        self.wxMarketCtrl.SetSelection(idx)

        label = wx.StaticText(self, -1, message('quote_select_list'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.wxQListCtrl = wx.ComboBox(self,-1, "", size=wx.Size(140,-1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
        box.Add(self.wxQListCtrl, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_COMBOBOX(self,self.wxQListCtrl.GetId(),self.OnQuoteList)

        self.wxQListCtrl.Append(message('quote_select_alllist'),QLIST_ALL)
        self.wxQListCtrl.Append(message('quote_select_syslist'),QLIST_SYSTEM)
        self.wxQListCtrl.Append(message('quote_select_usrlist'),QLIST_USER)
        self.wxQListCtrl.SetSelection(self.m_qlist)

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        # select traded or not
        tID = wx.NewId()
        self.wxFilterCtrl = wx.CheckBox(self, tID, message('quote_select_filterfield'))
        self.wxFilterCtrl.SetValue(self.m_filter)
        wx.EVT_CHECKBOX(self, tID, self.OnFilter)

        box.Add(self.wxFilterCtrl, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        sizer.Add(self.m_list, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        # context help
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)
            box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        # OK
        self.wxOK = wx.Button(self, wx.ID_OK, message('ok'))
        self.wxOK.SetDefault()
        self.wxOK.SetHelpText(message('ok_desc'))
        box.Add(self.wxOK, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnValid)

        # CANCEL
        btn = wx.Button(self, wx.ID_CANCEL, message('cancel'))
        btn.SetHelpText(message('cancel_desc'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetAutoLayout(True)
        self.SetSizerAndFit(sizer)

        EVT_POSTINIT(self, self.OnPostInit)
        wx.PostEvent(self,PostInitEvent())

    # --- [ window management ] -------------------------------------

    def OnPostInit(self,event):
        self.PopulateList()
        self.wxTickerCtrl.SetFocus()

    def OnFilter(self,event):
        self.m_filter = event.Checked()
        self.PopulateList()
        self.wxIsinCtrl.SetLabel(self.m_isin)
        self.wxTickerCtrl.SetLabel(self.m_ticker)
        self.wxTickerCtrl.SetFocus()

    def OnMarket(self,evt):
        idx = self.wxMarketCtrl.GetSelection()
        self.m_market = self.wxMarketCtrl.GetClientData(idx)
        self.PopulateList()
        self.m_list.SetFocus()

    def OnQuoteList(self,evt):
        idx = self.wxQListCtrl.GetSelection()
        self.m_qlist = idx
        self.PopulateList()
        self.m_list.SetFocus()

    def PopulateList(self):
        wx.SetCursor(wx.HOURGLASS_CURSOR)

        self.m_list.ClearAll()

        # but since we want images on the column header we have to do it the hard way:
        self.m_list.InsertColumn(IDC_ISIN, message('isin'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_TICKER, message('ticker'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_NAME, message('name'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PLACE, message('place'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_MARKET, message('market'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)

        x = 0
        self.currentItem = -1

        self.itemDataMap = {}
        self.itemQuoteMap = {}
        self.itemLineMap = {}

        if self.m_filter:
            for eachQuote in quotes.list():
                if eachQuote.isMatrix() and (self.m_qlist==QLIST_ALL or self.m_qlist==eachQuote.list()):
                    self.itemDataMap[x] = (eachQuote.isin(),eachQuote.ticker(),eachQuote.name(),eachQuote.place(),eachQuote.market())
                    self.itemQuoteMap[x] = eachQuote
                    x = x + 1
        else:
            for eachQuote in quotes.list():
                if  self.m_qlist==QLIST_ALL or self.m_qlist==eachQuote.list():
                    self.itemDataMap[x] = (eachQuote.isin(),eachQuote.ticker(),eachQuote.name(),eachQuote.place(),eachQuote.market())
                    self.itemQuoteMap[x] = eachQuote
                    x = x + 1

        items = self.itemDataMap.items()
        line = 0
        for x in range(len(items)):
            key, data = items[x]
            if self.m_market==None or (self.m_market==data[4]):
                self.m_list.InsertImageStringItem(line, data[0], self.sm_q)
                if data[0] == self.m_isin:  # current selection
                    self.currentItem = line
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
        self.SetCurrentItem()

        wx.SetCursor(wx.STANDARD_CURSOR)

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.m_list.SetDimensions(0, 0, w, h)

    def SetCurrentItem(self,line=None):
        if self.currentItem>=0:
            self.m_list.SetItemState(self.currentItem, 0, wx.LIST_STATE_SELECTED)
        if line:
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
            return quote
        else:
            return None

    # --- [ On handlers management ] -------------------------------------

    def OnColClick(self, event):
        debug("OnColClick: %d\n" % event.GetColumn())

    def OnTickerEdited(self,event):
        ticker = event.GetString()
        if ticker!='':
            quote = quotes.lookupTicker(ticker,self.m_market)
            if quote:
                v = self.wxIsinCtrl.GetLabel()
                print 'ticker:',ticker,' label %s=?=%s' % (v,quote.isin()), 'line=%d' % self.itemLineMap[quote.ticker()]
                if v!= quote.isin():
                    self.wxIsinCtrl.SetLabel(quote.isin())
                self.SetCurrentItem(self.itemLineMap[quote.ticker()])
            else:
                self.wxIsinCtrl.SetLabel('')

        print 'ticker:',ticker

    def OnISINEdited(self,event):
        isin = event.GetString()
        if isin!='':
            quote = quotes.lookupISIN(isin,self.m_market)
            if quote:
                v = self.wxTickerCtrl.GetLabel()
                print 'isin:',isin,' label %s=?=%s' % (v,quote.ticker()), 'line=%d' % self.itemLineMap[quote.ticker()]
                if v!= quote.ticker():
                    self.wxTickerCtrl.SetLabel(quote.ticker())
                self.SetCurrentItem(self.itemLineMap[quote.ticker()])
            else:
                self.wxTickerCtrl.SetLabel('')
        print 'isin:',isin

    def OnItemActivated(self, event):
        self.currentItem = event.m_itemIndex
        self.OnValid(event)

    def OnItemSelected(self, event):
        # be sure we come from a click and not some editing in ticker/isin controls
        if self.currentItem != event.m_itemIndex:
            self.currentItem = event.m_itemIndex
            quote = self.getQuoteOnTheLine(self.currentItem)
            self.wxTickerCtrl.SetLabel(quote.ticker())
            self.wxIsinCtrl.SetLabel(quote.isin())
            info('OnItemSelected: %s'%quote)
        event.Skip()

    def OnValid(self,event):
        isin = self.wxIsinCtrl.GetLabel().upper()
        name = self.wxTickerCtrl.GetLabel().upper()
        quote = None

        if isin=='' and name=='': return

        if isin<>'':
            if not checkISIN(isin):
                dlg = wx.MessageDialog(self, message('invalid_isin') % isin, message('quote_select_title'), wx.OK | wx.ICON_ERROR)
                idRet = dlg.ShowModal()
                dlg.Destroy()
                return
            quote = quotes.lookupISIN(isin,self.m_market)

        if not quote:
            quote = quotes.lookupTicker(name,self.m_market)
        elif not quote:
            quote = quotes.lookupName(name,self.m_market)

        if quote:
            self.quote = quote
            self.EndModal(wx.ID_OK)
        else:
            dlg = wx.MessageDialog(self, message('symbol_not_found') % (isin,name), message('quote_select_title'), wx.OK | wx.ICON_ERROR)
            idRet = dlg.ShowModal()
            dlg.Destroy()

# ============================================================================
# select_iTradeQuote
#
#   win     parent window
#   dquote  Quote object or ISIN reference
#   filter  display only 'is traded' symbols
#   market  filter to given market
# ============================================================================

def select_iTradeQuote(win,dquote=None,filter=False,market=None):
    if dquote:
        if not isinstance(dquote,Quote):
            dquote = quotes.lookupISIN(dquote,market)
    dlg = iTradeQuoteSelectorListCtrlDialog(win,dquote,filter,market)
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

    q = select_iTradeQuote(None,None,filter=False,market='EURONEXT')
    if q:
        print q.name()

# ============================================================================
# That's all folks !
# ============================================================================
