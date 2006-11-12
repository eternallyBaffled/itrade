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
from itrade_market import list_of_markets,market2place
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
            self.m_place = quote.place()
        else:
            self.m_isin = ''
            self.m_ticker = ''
            self.m_market = market
            self.m_place = market2place(market)

        self.m_filter = filter
        self.m_qlist = QLIST_ALL

        self.m_editing = True

        tID = wx.NewId()
        self.m_imagelist = wx.ImageList(16,16)
        self.sm_q = self.m_imagelist.Add(wx.Bitmap('res/quote.png'))
        self.sm_i = self.m_imagelist.Add(wx.Bitmap('res/invalid.png'))
        self.sm_up = self.m_imagelist.Add(wx.Bitmap('res/sm_up.png'))
        self.sm_dn = self.m_imagelist.Add(wx.Bitmap('res/sm_down.png'))

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
        self.wxQListCtrl.Append(message('quote_select_indiceslist'),QLIST_INDICES)
        self.wxQListCtrl.Append(message('quote_select_trackerslist'),QLIST_TRACKERS)
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
        self.PopulateList(bDuringInit=True)
        self.wxTickerCtrl.SetFocus()

    def resetFields(self):
        self.m_isin = ''
        self.m_ticker = ''
        self.wxIsinCtrl.SetLabel('')
        self.wxTickerCtrl.SetLabel('')
        self.m_list.SetFocus()

    def OnFilter(self,event):
        self.m_filter = event.Checked()
        self.resetFields()

    def OnMarket(self,evt):
        idx = self.wxMarketCtrl.GetSelection()
        self.m_market = self.wxMarketCtrl.GetClientData(idx)
        self.resetFields()

    def OnQuoteList(self,evt):
        idx = self.wxQListCtrl.GetSelection()
        self.m_qlist = idx
        self.resetFields()

    def isFiltered(self,quote,bDuringInit):
        if (self.m_qlist == QLIST_ALL) or (self.m_qlist == quote.list()):
            # good list
            if (self.m_market==None) or (self.m_market == quote.market()):
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

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.m_list.SetDimensions(0, 0, w, h)

    def SetCurrentItem(self,line):
        print 'SetCurrentItem: line=%d' % line
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
            print 'getQuoteOnTheLine(%d) : returns key=%d quote=%s' % (x,key,quote.ticker())
            return quote
        else:
            return None

    # --- [ On handlers management ] -------------------------------------

    def OnColClick(self, event):
        #debug("OnColClick: %d\n" % event.GetColumn())
        pass

    def OnTickerEdited(self,event):
        self.m_ticker = event.GetString().upper()
        print 'ticker: (editing=%d) :' % self.m_editing,self.m_ticker,' currentItem:',self.currentItem

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
                print 'isin:',isin,' label %s=?=%s' % (v,quote.ticker()), 'line=%d' % self.itemLineMap[quote.ticker()]
                if v!= quote.ticker():
                    self.wxTickerCtrl.SetLabel(quote.ticker())
            else:
                self.wxTickerCtrl.SetLabel('')
        print 'isin:',isin,' currentItem:',self.currentItem
        event.Skip()

    def OnItemActivated(self, event):
        self.currentItem = event.m_itemIndex
        self.OnValid(event)
        event.Skip()

    def OnItemSelected(self, event):
        print 'OnItemSelected --['
        # be sure we come from a click and not some editing in ticker/isin controls
        self.currentItem = event.m_itemIndex
        quote = self.getQuoteOnTheLine(self.currentItem)
        print 'OnItemSelected:',quote,' currentItem:',self.currentItem
        self.m_editing = False
        self.m_isin = quote.isin()
        self.m_place = quote.place()
        self.m_ticker = quote.ticker()
        #if self.m_isin != self.wxIsinCtrl.GetLabel():
        self.wxIsinCtrl.SetLabel(self.m_isin)
        #if self.m_ticker != self.wxTickerCtrl.GetLabel():
        self.wxTickerCtrl.SetLabel(self.m_ticker)
        event.Skip()
        print ']-- OnItemSelected'

    def OnValid(self,event):
        self.quote = self.getQuoteOnTheLine(self.currentItem)
        print 'OnItemSelected:',self.quote,' item:',self.currentItem
        if self.quote:
            self.EndModal(wx.ID_OK)

# ============================================================================
# select_iTradeQuote
#
#   win     parent window
#   dquote  Quote object or ISIN reference
#   filter  display only 'is traded' symbols
#   market  filter to given market
# ============================================================================

def select_iTradeQuote(win,dquote=None,filter=False,market=None):
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
