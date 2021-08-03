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
# 2007-02-2x    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging

# iTrade system
from itrade_logging import setLevel, info
from itrade_quotes import quotes, initQuotesModule, QUOTE_CASH, QUOTE_CREDIT
from itrade_local import message
import itrade_config

# wxPython system
if not itrade_config.nowxversion:
    import itrade_wxversion
import wx
# import sized_controls from wx.lib for wxPython version >= 2.8.8.0 (from wxaddons otherwise)
import wx.lib.sized_controls as sc

# ============================================================================
# iTrade_wxDecision
#
# ============================================================================

class iTrade_wxDecision(sc.SizedPanel):
    def __init__(self, parent, quote, portfolio):
        sc.SizedPanel.__init__(self,parent,-1)

        # keep back reference
        self.m_parent = parent
        self.m_quote = quote
        self.m_portfolio = portfolio

        # select a font
        #self.m_font = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL)
        #self.SetFont(self.m_font)

        # container
        self.SetSizerType("horizontal")

        # --- resizable pane #1 : Cash Position on the value ------------------
        pane1 = sc.SizedPanel(self, -1)
        pane1.SetSizerType("vertical")
        pane1.SetSizerProps(expand=True)

        # Pane#1 Row #1
        label = wx.StaticText(pane1, -1, message('decision_positiononquote_cash'))
        label.SetSizerProps(valign='center')

        # Pane#1 Box #1
        box1 = sc.SizedPanel(pane1, -1)
        box1.SetSizerType("form")
        box1.SetSizerProps(expand=True)

        # Pane#1 Box #1 Row #1 : number of shares in portfolio
        label = wx.StaticText(box1, -1, message('decision_numofshares'))
        label.SetSizerProps(valign='center',halign='right')

        self.wxCashNumOfShares = wx.StaticText(box1, -1, '')
        self.wxCashNumOfShares.SetSizerProps(valign='center')

        # Pane#1 Box #1 Row #2 : PRU in portfolio
        label = wx.StaticText(box1, -1, message('decision_upp'))
        label.SetSizerProps(valign='center',halign='right')

        self.wxCashPRU = wx.StaticText(box1, -1, '')
        self.wxCashPRU.SetSizerProps(valign='center')

        # Pane#1 Box #1 Row #3 : PR in portfolio
        label = wx.StaticText(box1, -1, message('decision_pp'))
        label.SetSizerProps(valign='center',halign='right')

        self.wxCashPR = wx.StaticText(box1, -1, '')
        self.wxCashPR.SetSizerProps(valign='center')

        # Pane#1 Box #1 Row #4 : Profit in portfolio
        label = wx.StaticText(box1, -1, message('decision_profit') % quote.currency_symbol())
        label.SetSizerProps(valign='center',halign='right')

        self.wxCashProfit = wx.StaticText(box1, -1, '')
        self.wxCashProfit.SetSizerProps(valign='center')

        # Pane#1 Box #1 Row #5 : Profit Percent in portfolio
        label = wx.StaticText(box1, -1, message('decision_profitpercent'))
        label.SetSizerProps(valign='center',halign='right')

        self.wxCashProfitPercent = wx.StaticText(box1, -1, '')
        self.wxCashProfitPercent.SetSizerProps(valign='center')

        # --- separator -------------------------------------------------------

        line = wx.StaticLine(self, -1, size=(-1,20), style=wx.LI_VERTICAL)
        line.SetSizerProps(expand=True)

        # --- resizable pane #2 : Marging Position on the value ---------------

        pane2 = sc.SizedPanel(self, -1)
        pane2.SetSizerType("vertical")
        pane2.SetSizerProps(expand=True)

        # Pane#2 Row #2
        label = wx.StaticText(pane2, -1, message('decision_positiononquote_credit'))
        label.SetSizerProps(valign='center')

        # Pane#2 Box #2
        box2 = sc.SizedPanel(pane2, -1)
        box2.SetSizerType("form")
        box2.SetSizerProps(expand=True)

        # Pane#2 Box #2 Row #1 : number of shares in portfolio
        label = wx.StaticText(box2, -1, message('decision_numofshares'))
        label.SetSizerProps(valign='center',halign='right')

        self.wxCreditNumOfShares = wx.StaticText(box2, -1, '')
        self.wxCreditNumOfShares.SetSizerProps(valign='center')

        # Pane#2 Box #2 Row #2 : PRU in portfolio
        label = wx.StaticText(box2, -1, message('decision_upp'))
        label.SetSizerProps(valign='center',halign='right')

        self.wxCreditPRU = wx.StaticText(box2, -1, '')
        self.wxCreditPRU.SetSizerProps(valign='center')

        # Pane#2 Box #2 Row #3 : PR in portfolio
        label = wx.StaticText(box2, -1, message('decision_pp'))
        label.SetSizerProps(valign='center',halign='right')

        self.wxCreditPR = wx.StaticText(box2, -1, '')
        self.wxCreditPR.SetSizerProps(valign='center')

        # Pane#2 Box #2 Row #4 : Profit in portfolio
        label = wx.StaticText(box2, -1, message('decision_profit') % quote.currency_symbol())
        label.SetSizerProps(valign='center',halign='right')

        self.wxCreditProfit = wx.StaticText(box2, -1, '')
        self.wxCreditProfit.SetSizerProps(valign='center')

        # Pane#2 Box #2 Row #5 : Profit Percent in portfolio
        label = wx.StaticText(box2, -1, message('decision_profitpercent'))
        label.SetSizerProps(valign='center',halign='right')

        self.wxCreditProfitPercent = wx.StaticText(box2, -1, '')
        self.wxCreditProfitPercent.SetSizerProps(valign='center')

        # --- separator -------------------------------------------------------

        line = wx.StaticLine(self, -1, size=(-1,20), style=wx.LI_VERTICAL)
        line.SetSizerProps(expand=True)

        # --- resizable pane #3 : Purchasing Power ----------------------------
        pane3 = sc.SizedPanel(self, -1)
        pane3.SetSizerType("vertical")
        pane3.SetSizerProps(expand=True)

        # Pane#3 Row #1
        label = wx.StaticText(pane3, -1, message('decision_purchasingpower'))
        label.SetSizerProps(valign='center')

        # Pane#3 Box #1
        box1 = sc.SizedPanel(pane3, -1)
        box1.SetSizerType("form")
        box1.SetSizerProps(expand=True)

        # Pane#3 Box #1 Row #1 : Available Cash in portfolio currency
        label = wx.StaticText(box1, -1, message('decision_availablecash') % portfolio.currency_symbol())
        label.SetSizerProps(valign='center',halign='right')

        self.wxAvailableCash = wx.StaticText(box1, -1, '')
        self.wxAvailableCash.SetSizerProps(valign='center')

        # Pane#3 Box #1 Row #2 : Available Cash in quote currency
        self.wxLabelAvailableCashQC = wx.StaticText(box1, -1, message('decision_availablecash') % quote.currency_symbol())
        self.wxLabelAvailableCashQC.SetSizerProps(valign='center',halign='right')

        self.wxAvailableCashQC = wx.StaticText(box1, -1, '')
        self.wxAvailableCashQC.SetSizerProps(valign='center')

        # Pane#3 Box #1 Row #3 : Committed Credit
        label = wx.StaticText(box1, -1, message('decision_committedcredit') % portfolio.currency_symbol())
        label.SetSizerProps(valign='center',halign='right')

        self.wxCommittedCredit = wx.StaticText(box1, -1, '')
        self.wxCommittedCredit.SetSizerProps(valign='center')

        # Pane#3 Box #1 Row #4 : Available Credit in portfolio currency
        label = wx.StaticText(box1, -1, message('decision_availablecredit') % portfolio.currency_symbol())
        label.SetSizerProps(valign='center',halign='right')

        self.wxAvailableCredit = wx.StaticText(box1, -1, '')
        self.wxAvailableCredit.SetSizerProps(valign='center')

        # Pane#3 Box #1 Row #5 : Available Credit in quote currency
        self.wxLabelAvailableCreditQC = wx.StaticText(box1, -1, message('decision_availablecredit') % quote.currency_symbol())
        self.wxLabelAvailableCreditQC.SetSizerProps(valign='center',halign='right')

        self.wxAvailableCreditQC = wx.StaticText(box1, -1, '')
        self.wxAvailableCreditQC.SetSizerProps(valign='center')

        # refresh everything
        self.refresh()

    # ---[ refresh the decision panel ]----------------------------------------

    def refresh(self):
        # refresh cash
        self.wxCashNumOfShares.SetLabel(self.m_quote.sv_number(QUOTE_CASH))
        self.wxCashPRU.SetLabel(self.m_quote.sv_pru(QUOTE_CASH,fmt="%.2f",bDispCurrency=True))
        self.wxCashPR.SetLabel(self.m_quote.sv_pr(QUOTE_CASH,bDispCurrency=True))

        profit = self.m_quote.nv_profit(self.m_quote.currency(),QUOTE_CASH)
        if profit==0:
            self.wxCashProfit.SetForegroundColour(wx.BLACK)
            self.wxCashProfitPercent.SetForegroundColour(wx.BLACK)
        elif profit<0:
            self.wxCashProfit.SetForegroundColour(wx.RED)
            self.wxCashProfitPercent.SetForegroundColour(wx.RED)
        else:
            self.wxCashProfit.SetForegroundColour(wx.BLUE)
            self.wxCashProfitPercent.SetForegroundColour(wx.BLUE)

        self.wxCashProfit.SetLabel("%s %s" % (self.m_quote.sv_profit(self.m_quote.currency(),QUOTE_CASH,fmt="%.0f"),self.m_quote.currency_symbol()))
        self.wxCashProfitPercent.SetLabel(self.m_quote.sv_profitPercent(self.m_quote.currency(),QUOTE_CASH))

        # refresh credit
        self.wxCreditNumOfShares.SetLabel(self.m_quote.sv_number(QUOTE_CREDIT))
        self.wxCreditPRU.SetLabel(self.m_quote.sv_pru(QUOTE_CREDIT,fmt="%.2f",bDispCurrency=True))
        self.wxCreditPR.SetLabel(self.m_quote.sv_pr(QUOTE_CREDIT,bDispCurrency=True))

        profit = self.m_quote.nv_profit(self.m_quote.currency(),QUOTE_CREDIT)
        if profit==0:
            self.wxCreditProfit.SetForegroundColour(wx.BLACK)
            self.wxCreditProfitPercent.SetForegroundColour(wx.BLACK)
        elif profit<0:
            self.wxCreditProfit.SetForegroundColour(wx.RED)
            self.wxCreditProfitPercent.SetForegroundColour(wx.RED)
        else:
            self.wxCreditProfit.SetForegroundColour(wx.BLUE)
            self.wxCreditProfitPercent.SetForegroundColour(wx.BLUE)

        self.wxCreditProfit.SetLabel("%s %s" % (self.m_quote.sv_profit(self.m_quote.currency(),QUOTE_CREDIT,fmt="%.0f"),self.m_quote.currency_symbol()))
        self.wxCreditProfitPercent.SetLabel(self.m_quote.sv_profitPercent(self.m_quote.currency(),QUOTE_CREDIT))

        # Purchasing Power
        self.m_portfolio.computeOperations()

        cash = self.m_portfolio.nv_cash()
        if cash==0:
            self.wxAvailableCash.SetForegroundColour(wx.BLACK)
            self.wxAvailableCashQC.SetForegroundColour(wx.BLACK)
        elif cash<0:
            self.wxAvailableCash.SetForegroundColour(wx.RED)
            self.wxAvailableCashQC.SetForegroundColour(wx.RED)
        else:
            self.wxAvailableCash.SetForegroundColour(wx.BLUE)
            self.wxAvailableCashQC.SetForegroundColour(wx.BLUE)
        self.wxAvailableCash.SetLabel(self.m_portfolio.sv_cash(currency=self.m_portfolio.currency(),fmt="%.0f",bDispCurrency=True))
        self.wxAvailableCashQC.SetLabel(self.m_portfolio.sv_cash(currency=self.m_quote.currency(),fmt="%.0f",bDispCurrency=True))

        self.wxCommittedCredit.SetLabel(self.m_portfolio.sv_credit(currency=self.m_portfolio.currency(),fmt="%.0f",bDispCurrency=True))
        self.wxAvailableCredit.SetLabel('?')
        self.wxAvailableCreditQC.SetLabel('?')

        show = self.m_portfolio.currency()!=self.m_quote.currency()
        self.wxLabelAvailableCashQC.Show(show)
        self.wxAvailableCashQC.Show(show)
        self.wxLabelAvailableCreditQC.Show(show)
        self.wxAvailableCreditQC.Show(show)

        # a little trick to make sure that you can't resize the dialog to
        # less screen space than the controls need
        self.Fit()
        self.SetMinSize(self.GetSize())

# ============================================================================
# WndTest
#
# ============================================================================

if __name__ == '__main__':

    class WndTest(wx.Frame):
        def __init__(self, parent,quote,portfolio):
            wx.Frame.__init__(self,parent,wx.NewId(), 'WndTest', size = (600,190), style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
            self.m_decision = iTrade_wxDecision(self,quote,portfolio)

            self.Fit()
            self.SetMinSize(self.GetSize())

# ============================================================================
# Test me
# ============================================================================

def main():
    global ticker, quote
    setLevel(logging.INFO)
    # load configuration
    import itrade_config
    itrade_config.loadConfig()
    from itrade_local import setLang, gMessage
    setLang('us')
    gMessage.load()
    # load extensions
    import itrade_ext
    itrade_ext.loadExtensions(itrade_config.fileExtData, itrade_config.dirExtData)
    # init modules
    initQuotesModule()
    ticker = 'GTO'
    quote = quotes.lookupTicker(ticker)
    info('%s: %s' % (ticker, quote))
    from itrade_portfolio import initPortfolioModule, loadPortfolio
    initPortfolioModule()
    port = loadPortfolio('default')
    app = wx.App(False)
    frame = WndTest(None, quote, port)
    if frame:
        frame.Show(True)
        app.MainLoop()


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
