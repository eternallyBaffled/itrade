#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxlistquote.py
#
# Description: wxPython list quote display
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
# 2005-05-29    dgil  from itrade_wxquote.py
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
from itrade_import import getListSymbolConnector

from itrade_wxmixin import iTradeSelectorListCtrl

# ============================================================================
# iTradeQuoteSelector
# ============================================================================

IDC_ISIN = 0
IDC_TICKER = 1
IDC_NAME = 2
IDC_PLACE = 3
IDC_MARKET = 4

class iTradeQuoteSelectorListCtrlDialog(wx.Dialog, wxl.ColumnSorterMixin):
    def __init__(self, parent, quote, filter = False, market = None, updateAction=False):
        # context help
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        if updateAction:
            title = message('quote_list_title')
        else:
            title = message('quote_select_title')
        pre.Create(parent, -1, title, size=(460, 420))
        self.PostCreate(pre)

        # init
        if quote:
            self.m_isin = quote.isin()
            self.m_ticker = quote.ticker()
        else:
            self.m_isin = ''
            self.m_ticker = ''

        self.m_filter = filter
        self.m_market = market
        self.m_updateAction = updateAction

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

        self.PopulateList()

        # Now that the list exists we can init the other base class,
        # see wxPython/lib/mixins/listctrl.py
        wxl.ColumnSorterMixin.__init__(self, 5)

        wx.EVT_LIST_COL_CLICK(self, tID, self.OnColClick)
        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_LIST_ITEM_ACTIVATED(self, tID, self.OnItemActivated)
        wx.EVT_LIST_ITEM_SELECTED(self, tID, self.OnItemSelected)

        sizer = wx.BoxSizer(wx.VERTICAL)

        if not self.m_updateAction:
            # ISIN or name selection
            box = wx.BoxSizer(wx.HORIZONTAL)

            label = wx.StaticText(self, -1, message('quote_select_isin'))
            box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

            self.wxIsinCtrl = wx.TextCtrl(self, -1, self.m_isin, size=(40,-1))
            box.Add(self.wxIsinCtrl, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

            label = wx.StaticText(self, -1, message('quote_select_ticker'))
            box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

            self.wxTickerCtrl = wx.TextCtrl(self, -1, self.m_ticker, size=(80,-1))
            box.Add(self.wxTickerCtrl, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

            sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, message('quote_select_market'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.wxMarketCtrl = wx.ComboBox(self,-1, "", size=wx.Size(140,-1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
        box.Add(self.wxMarketCtrl, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_COMBOBOX(self,self.wxMarketCtrl.GetId(),self.OnMarket)

        count = 0
        idx = 0
        for eachCtrl in list_of_markets(bFilterMode=True):
            self.wxMarketCtrl.Append(eachCtrl,eachCtrl)
            if eachCtrl==self.m_market:
                idx = count
            count = count + 1

        self.wxMarketCtrl.SetSelection(idx)

        if not self.m_updateAction:
            self.wxFilterCtrl = wx.CheckBox(self, -1, message('quote_select_filterfield'))
            self.wxFilterCtrl.SetValue(self.m_filter)
            wx.EVT_CHECKBOX(self, self.wxFilterCtrl.GetId(), self.OnFilter)

            box.Add(self.wxFilterCtrl, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        sizer.Add(self.m_list, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        # context help
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)
            box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        # OK
        if not self.m_updateAction:
            btn = wx.Button(self, wx.ID_OK, message('ok'))
            btn.SetDefault()
            btn.SetHelpText(message('ok_desc'))
            box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
            wx.EVT_BUTTON(self, wx.ID_OK, self.OnValid)

        # CANCEL
        if self.m_updateAction:
            btn = wx.Button(self, wx.ID_CANCEL, message('close'))
            btn.SetHelpText(message('close_desc'))
        else:
            btn = wx.Button(self, wx.ID_CANCEL, message('cancel'))
            btn.SetHelpText(message('cancel_desc'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        # DOWNLOAD
        if self.m_updateAction:
            btn.SetDefault()
            btn = wx.Button(self, wx.ID_OK, message('download_symbols'))
            btn.SetHelpText(message('download_symbols_desc'))
            box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
            wx.EVT_BUTTON(self, wx.ID_OK, self.OnDownload)

        sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetAutoLayout(True)
        self.SetSizerAndFit(sizer)
        if not self.m_updateAction:
            self.wxTickerCtrl.SetFocus()

    def OnFilter(self,event):
        self.m_filter = event.Checked()
        self.PopulateList()
        if not self.m_updateAction:
            self.wxIsinCtrl.SetLabel(self.m_isin)
            self.wxTickerCtrl.SetLabel(self.m_ticker)
            self.wxTickerCtrl.SetFocus()

    def OnMarket(self,evt):
        idx = self.wxMarketCtrl.GetSelection()
        if idx==0:
            self.m_market = None
        else:
            self.m_market = self.wxMarketCtrl.GetClientData(idx)
        self.PopulateList()
        self.m_list.SetFocus()

    def PopulateList(self):
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
        if self.m_filter:
            for eachQuote in quotes.list():
                if eachQuote.isMatrix():
                    self.itemDataMap[x] = (eachQuote.isin(),eachQuote.ticker(),eachQuote.name(),eachQuote.place(),eachQuote.market())
                    x = x + 1
        else:
            for eachQuote in quotes.list():
                self.itemDataMap[x] = (eachQuote.isin(),eachQuote.ticker(),eachQuote.name(),eachQuote.place(),eachQuote.market())
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
                line += 1

        self.m_list.SetColumnWidth(IDC_ISIN, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_TICKER, wx.LIST_AUTOSIZE_USEHEADER)
        self.m_list.SetColumnWidth(IDC_NAME, 16*10)
        self.m_list.SetColumnWidth(IDC_PLACE, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_MARKET, wx.LIST_AUTOSIZE)
        if self.currentItem>=0:
            self.m_list.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
            self.m_list.EnsureVisible(self.currentItem)

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.m_list.SetDimensions(0, 0, w, h)

    # Used by the wxl.ColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.m_list

    # Used by the wxl.ColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)

    def OnColClick(self, event):
        debug("OnColClick: %d\n" % event.GetColumn())

    def OnItemActivated(self, event):
        self.currentItem = event.m_itemIndex
        debug("OnItemActivated: %s\nTopItem: %s" %
                           (self.m_list.GetItemText(self.currentItem), self.m_list.GetTopItem()))
        self.OnValid(event)

    def OnItemSelected(self, event):
        self.currentItem = event.m_itemIndex
        debug("OnItemSelected: %s\nTopItem: %s" %
                           (self.m_list.GetItemText(self.currentItem), self.m_list.GetTopItem()))
        if not self.m_updateAction:
            quote = quotes.lookupISIN(self.m_list.GetItemText(self.currentItem))
            ticker = quote.ticker()
            self.wxTickerCtrl.SetLabel(quote.ticker())
            self.wxIsinCtrl.SetLabel(quote.isin())
        event.Skip()

    def OnDownload(self,event):
        lst = list_of_markets()
        max = len(lst)+1
        keepGoing = True
        x = 0

        dlg = wx.ProgressDialog(message('download_symbols'),"",max,self,wx.PD_CAN_ABORT | wx.PD_APP_MODAL)
        for market in lst:
            if keepGoing:
                keepGoing = dlg.Update(x,market)
                fn = getListSymbolConnector(market)
                if fn:
                    fn(quotes,market)
                else:
                    print 'ListSymbolConnector for %s not found !' % market
                x = x + 1
        dlg.Update(x,message('save'))
        quotes.saveListOfQuotes()
        if dlg:
            dlg.Destroy()

    def OnValid(self,event):
        isin = self.wxIsinCtrl.GetLabel().upper()
        name = self.wxTickerCtrl.GetLabel().upper()
        quote = None

        if isin<>'':
            if not checkISIN(isin):
                dlg = wx.MessageDialog(self, message('invalid_isin') % isin, message('quote_select_title'), wx.OK | wx.ICON_ERROR)
                idRet = dlg.ShowModal()
                dlg.Destroy()
                return
            quote = quotes.lookupISIN(isin)

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
            dquote = quotes.lookupISIN(dquote)
    dlg = iTradeQuoteSelectorListCtrlDialog(win,dquote,filter,market)
    if dlg.ShowModal()==wx.ID_OK:
        info('select_iTradeQuote() : %s' % dlg.quote)
        quote = dlg.quote
    else:
        quote = None
    dlg.Destroy()
    return quote

# ============================================================================
# list_iTradeQuote
#
#   win     parent window
# ============================================================================

def list_iTradeQuote(win):
    dlg = iTradeQuoteSelectorListCtrlDialog(win,None,filter=False,market=None,updateAction=True)
    dlg.ShowModal()
    dlg.Destroy()

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    app = wx.PySimpleApp()

    from itrade_local import *
    setLang('us')
    gMessage.load()

    q = select_iTradeQuote(None,None,filter=False,market='EURONEXT')
    if q:
        print q.name()
    else:
        list_iTradeQuote(None)

# ============================================================================
# That's all folks !
# ============================================================================
