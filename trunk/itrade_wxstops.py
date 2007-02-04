#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxstops.py
#
# Description: wxPython Stops management (add,edit,delete)
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
# 2007-02-03    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import os
import logging
#import webbrowser
#import datetime
#import locale

# wxPython system
import itrade_wxversion
import wx
#import  wx.grid as gridlib

# iTrade system
from itrade_logging import *
from itrade_quotes import *
#from itrade_local import message,setLocale
#from itrade_config import *

#from itrade_wxhtml import *
#from itrade_wxmixin import iTrade_wxFrame
#from itrade_wxgraph import iTrade_wxPanelGraph,fmtVolumeFunc,fmtVolumeFunc0
#from itrade_wxlive import iTrade_wxLive,iTrade_wxLiveMixin,EVT_UPDATE_LIVE
#from itrade_wxselectquote import select_iTradeQuote
#from itrade_wxpropquote import iTradeQuotePropertiesPanel

from itrade_wxutil import iTradeYesNo

# ============================================================================
# iTradeStopsDialog
# ============================================================================

class iTradeStopsDialog(wx.Dialog):

    def __init__(self, parent, quote, bAdd = True):
        # context help
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        if bAdd:
            title = message('stops_add_caption') % quote.name()
        else:
            title = message('stops_edit_caption') % quote.name()
        pre.Create(parent, -1, title, size=(420, 420))
        self.PostCreate(pre)

        # init
        self.m_add = bAdd
        self.m_quote = quote
        self.m_parent = parent

        # sizers
        sizer = wx.BoxSizer(wx.VERTICAL)

        # current quote
        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, quote.name())
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        label = wx.StaticText(self, -1, message('stops_last'))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        label = wx.StaticText(self, -1, quote.sv_close(bDispCurrency=True))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # Thresholds
        if quote.nv_number()==0:
            msgb = message('stops_noshares_loss')
            msgh = message('stops_noshares_win')
        else:
            msgb = message('stops_shares_loss')
            msgh = message('stops_shares_win')

            box = wx.BoxSizer(wx.HORIZONTAL)

            label = wx.StaticText(self, -1, message('stops_portfolio') % (quote.nv_number(),quote.sv_pr(bDispCurrency=True)) )
            box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

            sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)


        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, msgb)
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        label = wx.StaticText(self, -1, quote.sv_stoploss(bDispCurrency=True))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, msgh)
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        label = wx.StaticText(self, -1, quote.sv_stopwin(bDispCurrency=True))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # Commands (OK / CANCEL / Help)
        box = wx.BoxSizer(wx.HORIZONTAL)

        # context help
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)
            box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        # OK
        if bAdd:
            msg = message('stops_add')
            msgdesc = message('stops_add_desc')
        else:
            msg = message('stops_edit')
            msgdesc = message('stops_edit_desc')

        btn = wx.Button(self, wx.ID_OK, msg)
        btn.SetDefault()
        btn.SetHelpText(msgdesc)
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnValid)

        # CANCEL
        btn = wx.Button(self, wx.ID_CANCEL, message('cancel'))
        btn.SetHelpText(message('cancel_desc'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetAutoLayout(True)
        self.SetSizerAndFit(sizer)

    def OnValid(self,event):
        self.EndModal(wx.ID_OK)

# ============================================================================
# addOrEditStops_iTradeQuote
#
#   win         parent window
#   quote       Quote object or ISIN reference
# ============================================================================

def addOrEditStops_iTradeQuote(win,quote,bAdd=True):
    if not isinstance(quote,Quote):
        quote = quotes.lookupKey(quote)
    if quote:
        if not quote.hasStops():
            dlg = iTradeStopsDialog(win,quote,bAdd)
            idRet = dlg.ShowModal()
            dlg.Destroy()
            if idRet == wx.ID_OK:
                return True
    return False

# ============================================================================
# removeStops_iTradeQuote
#
#   win     parent window
#   quote   Quote object or ISIN reference
# ============================================================================

def removeStops_iTradeQuote(win,quote):
    if not isinstance(quote,Quote):
        quote = quotes.lookupKey(quote)
    if quote:
        if quote.hasStops():
            iRet = iTradeYesNo(win,message('stops_remove_text')%quote.name(),message('stops_remove_caption'))
            if iRet==wx.ID_YES:
                quotes.removeStops(quote.key())
                return True
    return False

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    app = wx.PySimpleApp()

    from itrade_local import *
    setLang('us')
    gMessage.load()

    itrade_config.verbose = False
    quotes.load()

    q = quotes.lookupTicker('SAF','EURONEXT')
    if q:
        addOrEditStops_iTradeQuote(None,q,bAdd= not q.hasStops())
    else:
        print 'quote not found'

# ============================================================================
# That's all folks !
# ============================================================================
