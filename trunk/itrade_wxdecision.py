#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxdecision.py
#
# Description: Decision Panel for a quote (idea from michel legrand)
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is Gilles Dumortier.
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
# 2007-02-2x    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
#import os
import logging
#import time
#import thread

# wxPython system
import itrade_wxversion
import wx
import wxaddons.sized_controls as sc

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_local import message
from itrade_quotes import *
#import itrade_import
#import itrade_currency

# ============================================================================
# iTrade_wxDecision
#
# ============================================================================

NBLINES = 7
LTLINES = 7

cNEUTRAL = wx.Colour(170,170,255)
cPOSITIF = wx.Colour(51,255,51)
cNEGATIF = wx.Colour(255,51,51)

class iTrade_wxDecision(sc.SizedPanel):
    def __init__(self, parent, wn, quote):
        sc.SizedPanel.__init__(self,parent,-1)

        # keep back reference
        self.m_parent = wn
        self.m_quote = quote

        # select a font
        self.m_font = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL)
        self.SetFont(self.m_font)

        # container
        self.SetSizerType("horizontal")

        # --- resizable pane #1 : Position on the value -----------------------
        pane1 = sc.SizedPanel(self, -1)
        pane1.SetSizerType("vertical")
        pane1.SetSizerProps(expand=True)

        # Pane#1 Row #1
        label = wx.StaticText(pane1, -1, message('decision_positiononquote_cash') % quote.name())
        label.SetSizerProps(valign='center')

        # Pane#1 Box #1
        box1 = sc.SizedPanel(pane1, -1)
        box1.SetSizerType("form")
        box1.SetSizerProps(expand=True)

        # Pane#1 Box #1 Row #1 : number of shares in portfolio
        label = wx.StaticText(box1, -1, message('decision_numofshares'))
        label.SetSizerProps(valign='center',halign='right')

        label = wx.StaticText(box1, -1, quote.sv_number(QUOTE_CASH))
        label.SetSizerProps(valign='center')

        # Pane#1 Box #1 Row #1 : PRU in portfolio
        label = wx.StaticText(box1, -1, message('decision_upp'))
        label.SetSizerProps(valign='center',halign='right')

        label = wx.StaticText(box1, -1, quote.sv_pru(QUOTE_CASH,bDispCurrency=True))
        label.SetSizerProps(valign='center')

        # Pane#1 Box #1 Row #2 : PR in portfolio
        label = wx.StaticText(box1, -1, message('decision_pp'))
        label.SetSizerProps(valign='center',halign='right')

        label = wx.StaticText(box1, -1, quote.sv_pr(QUOTE_CASH,bDispCurrency=True))
        label.SetSizerProps(valign='center')

        # Pane#1 Box #1 Row #3 : Profit in portfolio
        label = wx.StaticText(box1, -1, message('decision_profit') % quote.currency_symbol())
        label.SetSizerProps(valign='center',halign='right')

        str = "%s %s" % (quote.sv_profit(quote.currency(),QUOTE_CASH,fmt="%.0f"),quote.currency_symbol())
        label = wx.StaticText(box1, -1, str)
        label.SetSizerProps(valign='center')

        # Pane#1 Box #1 Row #4 : Profit Percent in portfolio
        label = wx.StaticText(box1, -1, message('decision_profitpercent'))
        label.SetSizerProps(valign='center',halign='right')

        label = wx.StaticText(box1, -1, quote.sv_profitPercent(quote.currency(),QUOTE_CASH))
        label.SetSizerProps(valign='center')

        # separator
        line = wx.StaticLine(pane1, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        line.SetSizerProps(expand=True)

        # Pane#1 Row #2
        label = wx.StaticText(pane1, -1, message('decision_positiononquote_credit') % quote.name())
        label.SetSizerProps(valign='center')

        # --- separator -------------------------------------------------------
        line = wx.StaticLine(self, -1, size=(-1,20), style=wx.LI_VERTICAL)
        line.SetSizerProps(expand=True)

        # --- resizable pane #2 : Purchasing Power ----------------------------
        pane2 = sc.SizedPanel(self, -1)
        pane2.SetSizerType("vertical")
        pane2.SetSizerProps(expand=True)

        # Pane#2 Row #1
        label = wx.StaticText(pane2, -1, message('decision_purchasingpower'))
        label.SetSizerProps(valign='center')

        # Pane#2 Box #2
        box2 = sc.SizedPanel(pane2, -1)
        box2.SetSizerType("form")
        box2.SetSizerProps(expand=True)

        # refresh everything
        self.refresh()

        # a little trick to make sure that you can't resize the dialog to
        # less screen space than the controls need
        self.Fit()
        self.SetMinSize(self.GetSize())

    # ---[ refresh the decision panel ]----------------------------------------

    def refresh(self):
        pass

# ============================================================================
# WndTest
#
# ============================================================================

if __name__=='__main__':

    class WndTest(wx.Frame):
        def __init__(self, parent,quote):
            wx.Frame.__init__(self,parent,wx.NewId(), 'WndTest', size = (600,190), style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
            self.m_decision = iTrade_wxDecision(self,parent,quote)

            self.Fit()
            self.SetMinSize(self.GetSize())

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

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

    ticker = 'GTO'

    quote = quotes.lookupTicker(ticker)
    info('%s: %s' % (ticker,quote))

    app = wx.PySimpleApp()

    frame = WndTest(None,quote)
    if frame:
        frame.Show(True)
        app.MainLoop()

# ============================================================================
# That's all folks !
# ============================================================================
