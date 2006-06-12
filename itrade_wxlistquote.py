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

# matplotlib system
import matplotlib
matplotlib.use('WXAgg')

# wxPython system
import itrade_wxversion
from wxPython.wx import *
from wxPython.lib.mixins.listctrl import wxColumnSorterMixin, wxListCtrlAutoWidthMixin

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
IDC_MARKET = 3

class iTradeQuoteSelectorListCtrlDialog(wxDialog, wxColumnSorterMixin):
    def __init__(self, parent, quote, filter = False, market = None, updateAction=False):
        # context help
        pre = wxPreDialog()
        pre.SetExtraStyle(wxDIALOG_EX_CONTEXTHELP)
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

        tID = wxNewId()
        self.m_imagelist = wxImageList(16,16)
        self.sm_q = self.m_imagelist.Add(wxBitmap('res/invalid.gif'))
        self.sm_up = self.m_imagelist.Add(wxBitmap('res/sm_up.gif'))
        self.sm_dn = self.m_imagelist.Add(wxBitmap('res/sm_down.gif'))

        self.m_list = iTradeSelectorListCtrl(self, tID,
                                 style = wxLC_REPORT | wxSUNKEN_BORDER,
                                 size=(440, 380)
                                 )
        self.m_list.SetImageList(self.m_imagelist, wxIMAGE_LIST_SMALL)

        self.PopulateList()

        # Now that the list exists we can init the other base class,
        # see wxPython/lib/mixins/listctrl.py
        wxColumnSorterMixin.__init__(self, 4)

        EVT_LIST_COL_CLICK(self, tID, self.OnColClick)
        EVT_SIZE(self, self.OnSize)
        EVT_LIST_ITEM_ACTIVATED(self, tID, self.OnItemActivated)
        EVT_LIST_ITEM_SELECTED(self, tID, self.OnItemSelected)

        sizer = wxBoxSizer(wxVERTICAL)

        if not self.m_updateAction:
            # ISIN or name selection
            box = wxBoxSizer(wxHORIZONTAL)

            label = wxStaticText(self, -1, message('quote_select_isin'))
            box.Add(label, 0, wxALIGN_CENTRE|wxALL, 5)

            self.wxIsinCtrl = wxTextCtrl(self, -1, self.m_isin, size=(40,-1))
            box.Add(self.wxIsinCtrl, 1, wxALIGN_CENTRE|wxALL, 5)

            label = wxStaticText(self, -1, message('quote_select_ticker'))
            box.Add(label, 0, wxALIGN_CENTRE|wxALL, 5)

            self.wxTickerCtrl = wxTextCtrl(self, -1, self.m_ticker, size=(80,-1))
            box.Add(self.wxTickerCtrl, 1, wxALIGN_CENTRE|wxALL, 5)

            sizer.AddSizer(box, 0, wxGROW|wxALIGN_CENTER_VERTICAL|wxALL, 5)

        box = wxBoxSizer(wxHORIZONTAL)

        label = wxStaticText(self, -1, message('quote_select_market'))
        box.Add(label, 0, wxALIGN_CENTRE|wxALL, 5)

        self.wxMarketCtrl = wxComboBox(self,-1, "", size=wxSize(140,-1), style=wxCB_DROPDOWN|wxCB_READONLY)
        box.Add(self.wxMarketCtrl, 0, wxALIGN_CENTRE|wxALL, 5)
        EVT_COMBOBOX(self,self.wxMarketCtrl.GetId(),self.OnMarket)

        count = 0
        idx = 0
        for eachCtrl in list_of_markets(bFilterMode=True):
            self.wxMarketCtrl.Append(eachCtrl,eachCtrl)
            if eachCtrl==self.m_market:
                idx = count
            count = count + 1

        self.wxMarketCtrl.SetSelection(idx)

        if not self.m_updateAction:
            self.wxFilterCtrl = wxCheckBox(self, -1, message('quote_select_filterfield'))
            self.wxFilterCtrl.SetValue(self.m_filter)
            EVT_CHECKBOX(self, self.wxFilterCtrl.GetId(), self.OnFilter)

            box.Add(self.wxFilterCtrl, 1, wxALIGN_CENTRE|wxALL, 5)

        sizer.AddSizer(box, 0, wxGROW|wxALIGN_CENTER_VERTICAL|wxALL, 5)

        sizer.Add(self.m_list, 0, wxALIGN_CENTRE|wxALL, 5)

        box = wxBoxSizer(wxHORIZONTAL)

        # context help
        if wxPlatform != "__WXMSW__":
            btn = wxContextHelpButton(self)
            box.Add(btn, 0, wxALIGN_CENTRE|wxALL, 5)

        # OK
        if not self.m_updateAction:
            btn = wxButton(self, wxID_OK, message('ok'))
            btn.SetDefault()
            btn.SetHelpText(message('ok_desc'))
            box.Add(btn, 0, wxALIGN_CENTRE|wxALL, 5)
            EVT_BUTTON(self, wxID_OK, self.OnValid)

        # CANCEL
        if self.m_updateAction:
            btn = wxButton(self, wxID_CANCEL, message('close'))
            btn.SetHelpText(message('close_desc'))
        else:
            btn = wxButton(self, wxID_CANCEL, message('cancel'))
            btn.SetHelpText(message('cancel_desc'))
        box.Add(btn, 0, wxALIGN_CENTRE|wxALL, 5)

        # DOWNLOAD
        if self.m_updateAction:
            btn.SetDefault()
            btn = wxButton(self, wxID_OK, message('download_symbols'))
            btn.SetHelpText(message('download_symbols_desc'))
            box.Add(btn, 0, wxALIGN_CENTRE|wxALL, 5)
            EVT_BUTTON(self, wxID_OK, self.OnDownload)

        sizer.AddSizer(box, 0, wxALIGN_CENTER_VERTICAL|wxALL, 5)

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
        self.m_list.InsertColumn(IDC_ISIN, message('isin'), wxLIST_FORMAT_LEFT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_TICKER, message('ticker'), wxLIST_FORMAT_LEFT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_NAME, message('name'), wxLIST_FORMAT_LEFT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_MARKET, message('market'), wxLIST_FORMAT_LEFT, wxLIST_AUTOSIZE)

        x = 0
        self.currentItem = -1

        self.itemDataMap = {}
        if self.m_filter:
            for eachQuote in quotes.list():
                if eachQuote.isMatrix():
                    self.itemDataMap[x] = (eachQuote.isin(),eachQuote.ticker(),eachQuote.name(),eachQuote.market())
                    x = x + 1
        else:
            for eachQuote in quotes.list():
                self.itemDataMap[x] = (eachQuote.isin(),eachQuote.ticker(),eachQuote.name(),eachQuote.market())
                x = x + 1

        items = self.itemDataMap.items()
        line = 0
        for x in range(len(items)):
            key, data = items[x]
            if self.m_market==None or (self.m_market==data[3]):
                self.m_list.InsertImageStringItem(line, data[0], self.sm_q)
                if data[0] == self.m_isin:  # current selection
                    self.currentItem = line
                self.m_list.SetStringItem(line, IDC_TICKER, data[1])
                self.m_list.SetStringItem(line, IDC_NAME, data[2])
                self.m_list.SetStringItem(line, IDC_MARKET, data[3])
                self.m_list.SetItemData(line, key)
                line += 1

        self.m_list.SetColumnWidth(IDC_ISIN, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_TICKER, wxLIST_AUTOSIZE_USEHEADER)
        self.m_list.SetColumnWidth(IDC_NAME, 16*10)
        self.m_list.SetColumnWidth(IDC_MARKET, wxLIST_AUTOSIZE)
        if self.currentItem>=0:
            self.m_list.SetItemState(self.currentItem, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED)
            self.m_list.EnsureVisible(self.currentItem)

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.m_list.SetDimensions(0, 0, w, h)

    # Used by the wxColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.m_list

    # Used by the wxColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
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

        dlg = wxProgressDialog(message('download_symbols'),"",max,self,wxPD_CAN_ABORT | wxPD_APP_MODAL)
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
                dlg = wxMessageDialog(self, message('invalid_isin') % isin, message('quote_select_title'), wxOK | wxICON_ERROR)
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
            self.EndModal(wxID_OK)
        else:
            dlg = wxMessageDialog(self, message('symbol_not_found') % (isin,name), message('quote_select_title'), wxOK | wxICON_ERROR)
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
    if dlg.ShowModal()==wxID_OK:
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

    app = wxPySimpleApp()

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
# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
