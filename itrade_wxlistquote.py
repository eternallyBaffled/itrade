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
#from itrade_wxhtml import *
from itrade_wxmixin import iTradeSelectorListCtrl
#from itrade_wxlabel import iTrade_wxLabel
#from itrade_wxgraph import iTrade_wxPanelGraph,fmtVolumeFunc,fmtVolumeFunc0
#from itrade_wxlive import iTrade_wxLive,iTrade_wxLiveMixin,EVT_UPDATE_LIVE

# ============================================================================
# iTradeQuoteSelector
# ============================================================================

class iTradeQuoteSelectorListCtrlDialog(wxDialog, wxColumnSorterMixin):
    def __init__(self, parent, quote, filter = False):
        wxDialog.__init__(self, parent, -1, message('quote_select_title'), size=(420, 420))
        #wxPanel.__init__(self, parent, -1, style=wxWANTS_CHARS)
        if quote:
            self.m_isin = quote.isin()
            self.m_ticker = quote.ticker()
        else:
            self.m_isin = ''
            self.m_ticker = ''

        self.m_filter = filter

        tID = wxNewId()
        self.m_imagelist = wxImageList(16,16)
        self.sm_q = self.m_imagelist.Add(wxBitmap('res/invalid.gif'))
        self.sm_up = self.m_imagelist.Add(wxBitmap('res/sm_up.gif'))
        self.sm_dn = self.m_imagelist.Add(wxBitmap('res/sm_down.gif'))

        self.m_list = iTradeSelectorListCtrl(self, tID,
                                 style = wxLC_REPORT | wxSUNKEN_BORDER,
                                 size=(400, 380)
                                 )
        self.m_list.SetImageList(self.m_imagelist, wxIMAGE_LIST_SMALL)

        self.PopulateList()

        # Now that the list exists we can init the other base class,
        # see wxPython/lib/mixins/listctrl.py
        wxColumnSorterMixin.__init__(self, 3)

        EVT_LIST_COL_CLICK(self, tID, self.OnColClick)
        EVT_SIZE(self, self.OnSize)
        EVT_LIST_ITEM_ACTIVATED(self, tID, self.OnItemActivated)
        EVT_LIST_ITEM_SELECTED(self, tID, self.OnItemSelected)

        sizer = wxBoxSizer(wxVERTICAL)

        box = wxBoxSizer(wxHORIZONTAL)

        label = wxStaticText(self, -1, message('quote_select_textfield'))
        box.Add(label, 0, wxALIGN_CENTRE|wxALL, 5)

        self.wxTickerCtrl = wxTextCtrl(self, -1, self.m_ticker, size=(80,-1))
        box.Add(self.wxTickerCtrl, 1, wxALIGN_CENTRE|wxALL, 5)

        self.wxFilterCtrl = wxCheckBox(self, -1, message('quote_select_filterfield'))
        self.wxFilterCtrl.SetValue(self.m_filter)
        EVT_CHECKBOX(self, self.wxFilterCtrl.GetId(), self.OnFilter)

        sizer.AddSizer(box, 0, wxGROW|wxALIGN_CENTER_VERTICAL|wxALL, 5)
        sizer.Add(self.wxFilterCtrl, 1, wxALIGN_CENTRE|wxALL, 5)

        sizer.Add(self.m_list, 0, wxALIGN_CENTRE|wxALL, 5)

        box = wxBoxSizer(wxHORIZONTAL)
        btn = wxButton(self, wxID_OK, message('ok'))
        btn.SetDefault()
        btn.SetHelpText(message('ok_desc'))
        box.Add(btn, 0, wxALIGN_CENTRE|wxALL, 5)
        EVT_BUTTON(self, wxID_OK, self.OnValid)

        btn = wxButton(self, wxID_CANCEL, message('cancel'))
        btn.SetHelpText(message('cancel_desc'))
        box.Add(btn, 0, wxALIGN_CENTRE|wxALL, 5)

        sizer.AddSizer(box, 0, wxALIGN_CENTER_VERTICAL|wxALL, 5)

        self.SetAutoLayout(True)
        self.SetSizerAndFit(sizer)
        self.wxTickerCtrl.SetFocus()

    def OnFilter(self,event):
        self.m_filter = event.Checked()
        self.PopulateList()
        self.wxTickerCtrl.SetLabel(self.m_ticker)
        self.wxTickerCtrl.SetFocus()

    def PopulateList(self):
        self.m_list.ClearAll()

        # but since we want images on the column header we have to do it the hard way:
        info = wxListItem()
        info.m_mask = wxLIST_MASK_TEXT | wxLIST_MASK_IMAGE | wxLIST_MASK_FORMAT
        info.m_image = -1
        info.m_format = wxLIST_FORMAT_LEFT
        info.m_text = message('isin')
        self.m_list.InsertColumnInfo(0, info)

        info.m_format = wxLIST_FORMAT_LEFT
        info.m_text = message('ticker')
        self.m_list.InsertColumnInfo(1, info)

        info.m_format = wxLIST_FORMAT_LEFT
        info.m_text = message('name')
        self.m_list.InsertColumnInfo(2, info)

        x = 0
        self.currentItem = -1

        self.itemDataMap = {}
        if self.m_filter:
            for eachQuote in quotes.list():
                if eachQuote.isMatrix():
                    self.itemDataMap[x] = (eachQuote.isin(),eachQuote.ticker(),eachQuote.name())
                    x = x + 1
        else:
            for eachQuote in quotes.list():
                self.itemDataMap[x] = (eachQuote.isin(),eachQuote.ticker(),eachQuote.name())
                x = x + 1

        items = self.itemDataMap.items()
        for x in range(len(items)):
            key, data = items[x]
            self.m_list.InsertImageStringItem(x, data[0], self.sm_q)
            if data[0] == self.m_isin:  # current selection
                self.currentItem = x
            self.m_list.SetStringItem(x, 1, data[1])
            self.m_list.SetStringItem(x, 2, data[2])
            self.m_list.SetItemData(x, key)

        self.m_list.SetColumnWidth(0, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(1, wxLIST_AUTOSIZE_USEHEADER)
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
        quote = quotes.lookupISIN(self.m_list.GetItemText(self.currentItem))
        ticker = quote.ticker()
        if ticker=='':
            self.wxTickerCtrl.SetLabel(quote.isin())
        else:
            self.wxTickerCtrl.SetLabel(ticker)
        event.Skip()

    def OnValid(self,event):
        name = self.wxTickerCtrl.GetLabel()
        if name<>'':
            quote = quotes.lookupISIN(name)
            if not quote:
                quote = quotes.lookupTicker(name.upper())
            elif not quote:
                quote = quotes.lookupName(name)

            if quote:
                self.quote = quote
                self.EndModal(wxID_OK)

# ============================================================================
# select_iTradeQuote
#
#   win     parent window
#   dquote  Quote object or ISIN reference
# ============================================================================

def select_iTradeQuote(win,dquote=None,filter=False):
    if dquote:
        if not isinstance(dquote,Quote):
            dquote = quotes.lookupISIN(dquote)
    dlg = iTradeQuoteSelectorListCtrlDialog(win,dquote,filter)
    if dlg.ShowModal()==wxID_OK:
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

    app = wxPySimpleApp()

    from itrade_local import *
    setLang('us')
    gMessage.load()

    q = select_iTradeQuote(None,None,False)
    if q:
        print q.name()

# ============================================================================
# That's all folks !
# ============================================================================
# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
