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
from __future__ import absolute_import
import logging

# iTrade system
from itrade_logging import setLevel, info
from itrade_quotes import quotes, initQuotesModule, QuoteType
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
    def __init__(self, parent, quote, portfolio, *args, **kwargs):
        sc.SizedPanel.__init__(self, parent=parent, *args, **kwargs)

        # keep back reference
        self.m_parent = parent
        self.m_quote = quote
        self.m_portfolio = portfolio

        # select a font
        #self.m_font = wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        #self.SetFont(self.m_font)

        # container
        self.SetSizerType("horizontal")

        # --- resizable pane #1 : Cash Position on the value ------------------
        pane1 = sc.SizedPanel(self, wx.ID_ANY)
        pane1.SetSizerType("vertical")
        pane1.SetSizerProps(expand=True)

        # Pane#1 Row #1
        label = wx.StaticText(pane1, wx.ID_ANY, message('decision_positiononquote_cash'))
        label.SetSizerProps(valign='center')

        # Pane#1 Box #1
        box1 = sc.SizedPanel(pane1, wx.ID_ANY)
        box1.SetSizerType("form")
        box1.SetSizerProps(expand=True)

        # Pane#1 Box #1 Row #1 : number of shares in portfolio
        label = wx.StaticText(box1, wx.ID_ANY, message('decision_numofshares'))
        label.SetSizerProps(valign='center', halign='right')

        self.wxCashNumOfShares = wx.StaticText(box1, wx.ID_ANY, '')
        self.wxCashNumOfShares.SetSizerProps(valign='center')

        # Pane#1 Box #1 Row #2 : PRU in portfolio
        label = wx.StaticText(box1, wx.ID_ANY, message('decision_upp'))
        label.SetSizerProps(valign='center', halign='right')

        self.wxCashPRU = wx.StaticText(box1, wx.ID_ANY, '')
        self.wxCashPRU.SetSizerProps(valign='center')

        # Pane#1 Box #1 Row #3 : PR in portfolio
        label = wx.StaticText(box1, wx.ID_ANY, message('decision_pp'))
        label.SetSizerProps(valign='center', halign='right')

        self.wxCashPR = wx.StaticText(box1, wx.ID_ANY, '')
        self.wxCashPR.SetSizerProps(valign='center')

        # Pane#1 Box #1 Row #4 : Profit in portfolio
        label = wx.StaticText(box1, wx.ID_ANY, message('decision_profit').format(quote.currency_symbol()))
        label.SetSizerProps(valign='center', halign='right')

        self.wxCashProfit = wx.StaticText(box1, wx.ID_ANY, '')
        self.wxCashProfit.SetSizerProps(valign='center')

        # Pane#1 Box #1 Row #5 : Profit Percent in portfolio
        label = wx.StaticText(box1, wx.ID_ANY, message('decision_profitpercent'))
        label.SetSizerProps(valign='center', halign='right')

        self.wxCashProfitPercent = wx.StaticText(box1, wx.ID_ANY, '')
        self.wxCashProfitPercent.SetSizerProps(valign='center')

        # --- separator -------------------------------------------------------

        line = wx.StaticLine(self, wx.ID_ANY, size=(-1,20), style=wx.LI_VERTICAL)
        line.SetSizerProps(expand=True)

        # --- resizable pane #2 : Marging Position on the value ---------------

        pane2 = sc.SizedPanel(self, wx.ID_ANY)
        pane2.SetSizerType("vertical")
        pane2.SetSizerProps(expand=True)

        # Pane#2 Row #2
        label = wx.StaticText(pane2, wx.ID_ANY, message('decision_positiononquote_credit'))
        label.SetSizerProps(valign='center')

        # Pane#2 Box #2
        box2 = sc.SizedPanel(pane2, wx.ID_ANY)
        box2.SetSizerType("form")
        box2.SetSizerProps(expand=True)

        # Pane#2 Box #2 Row #1 : number of shares in portfolio
        label = wx.StaticText(box2, wx.ID_ANY, message('decision_numofshares'))
        label.SetSizerProps(valign='center', halign='right')

        self.wxCreditNumOfShares = wx.StaticText(box2, wx.ID_ANY, '')
        self.wxCreditNumOfShares.SetSizerProps(valign='center')

        # Pane#2 Box #2 Row #2 : PRU in portfolio
        label = wx.StaticText(box2, wx.ID_ANY, message('decision_upp'))
        label.SetSizerProps(valign='center', halign='right')

        self.wxCreditPRU = wx.StaticText(box2, wx.ID_ANY, '')
        self.wxCreditPRU.SetSizerProps(valign='center')

        # Pane#2 Box #2 Row #3 : PR in portfolio
        label = wx.StaticText(box2, wx.ID_ANY, message('decision_pp'))
        label.SetSizerProps(valign='center', halign='right')

        self.wxCreditPR = wx.StaticText(box2, wx.ID_ANY, '')
        self.wxCreditPR.SetSizerProps(valign='center')

        # Pane#2 Box #2 Row #4 : Profit in portfolio
        label = wx.StaticText(box2, wx.ID_ANY, message('decision_profit').format(quote.currency_symbol()))
        label.SetSizerProps(valign='center', halign='right')

        self.wxCreditProfit = wx.StaticText(box2, wx.ID_ANY, '')
        self.wxCreditProfit.SetSizerProps(valign='center')

        # Pane#2 Box #2 Row #5 : Profit Percent in portfolio
        label = wx.StaticText(box2, wx.ID_ANY, message('decision_profitpercent'))
        label.SetSizerProps(valign='center', halign='right')

        self.wxCreditProfitPercent = wx.StaticText(box2, wx.ID_ANY, '')
        self.wxCreditProfitPercent.SetSizerProps(valign='center')

        # --- separator -------------------------------------------------------

        line = wx.StaticLine(self, wx.ID_ANY, size=(-1,20), style=wx.LI_VERTICAL)
        line.SetSizerProps(expand=True)

        # --- resizable pane #3 : Purchasing Power ----------------------------
        pane3 = sc.SizedPanel(self, wx.ID_ANY)
        pane3.SetSizerType("vertical")
        pane3.SetSizerProps(expand=True)

        # Pane#3 Row #1
        label = wx.StaticText(pane3, wx.ID_ANY, message('decision_purchasingpower'))
        label.SetSizerProps(valign='center')

        # Pane#3 Box #1
        box1 = sc.SizedPanel(pane3, wx.ID_ANY)
        box1.SetSizerType("form")
        box1.SetSizerProps(expand=True)

        # Pane#3 Box #1 Row #1 : Available Cash in portfolio currency
        label = wx.StaticText(box1, wx.ID_ANY, message('decision_availablecash').format(portfolio.currency_symbol()))
        label.SetSizerProps(valign='center', halign='right')

        self.wxAvailableCash = wx.StaticText(box1, wx.ID_ANY, '')
        self.wxAvailableCash.SetSizerProps(valign='center')

        # Pane#3 Box #1 Row #2 : Available Cash in quote currency
        self.wxLabelAvailableCashQC = wx.StaticText(box1, wx.ID_ANY, message('decision_availablecash').format(quote.currency_symbol()))
        self.wxLabelAvailableCashQC.SetSizerProps(valign='center', halign='right')

        self.wxAvailableCashQC = wx.StaticText(box1, wx.ID_ANY, '')
        self.wxAvailableCashQC.SetSizerProps(valign='center')

        # Pane#3 Box #1 Row #3 : Committed Credit
        label = wx.StaticText(box1, wx.ID_ANY, message('decision_committedcredit').format(portfolio.currency_symbol()))
        label.SetSizerProps(valign='center', halign='right')

        self.wxCommittedCredit = wx.StaticText(box1, wx.ID_ANY, '')
        self.wxCommittedCredit.SetSizerProps(valign='center')

        # Pane#3 Box #1 Row #4 : Available Credit in portfolio currency
        label = wx.StaticText(box1, wx.ID_ANY, message('decision_availablecredit').format(portfolio.currency_symbol()))
        label.SetSizerProps(valign='center', halign='right')

        self.wxAvailableCredit = wx.StaticText(box1, wx.ID_ANY, '')
        self.wxAvailableCredit.SetSizerProps(valign='center')

        # Pane#3 Box #1 Row #5 : Available Credit in quote currency
        self.wxLabelAvailableCreditQC = wx.StaticText(box1, wx.ID_ANY, message('decision_availablecredit').format(quote.currency_symbol()))
        self.wxLabelAvailableCreditQC.SetSizerProps(valign='center', halign='right')

        self.wxAvailableCreditQC = wx.StaticText(box1, wx.ID_ANY, '')
        self.wxAvailableCreditQC.SetSizerProps(valign='center')

        # refresh everything
        self.refresh()

    # ---[ refresh the decision panel ]----------------------------------------

    def refresh(self):
        # refresh cash
        self.wxCashNumOfShares.SetLabel(label=self.m_quote.sv_number(QuoteType.cash))
        self.wxCashPRU.SetLabel(label=self.m_quote.sv_pru(QuoteType.cash, fmt="{:.2f}", bDispCurrency=True))
        self.wxCashPR.SetLabel(label=self.m_quote.sv_pr(QuoteType.cash, bDispCurrency=True))

        profit = self.m_quote.nv_profit(self.m_quote.currency(), QuoteType.cash)
        if profit == 0:
            self.wxCashProfit.SetForegroundColour(colour=wx.BLACK)
            self.wxCashProfitPercent.SetForegroundColour(colour=wx.BLACK)
        elif profit < 0:
            self.wxCashProfit.SetForegroundColour(colour=wx.RED)
            self.wxCashProfitPercent.SetForegroundColour(colour=wx.RED)
        else:
            self.wxCashProfit.SetForegroundColour(colour=wx.BLUE)
            self.wxCashProfitPercent.SetForegroundColour(colour=wx.BLUE)

        self.wxCashProfit.SetLabel(label=u"{} {}".format(self.m_quote.sv_profit(self.m_quote.currency(), QuoteType.cash, fmt="{:.0f}"), self.m_quote.currency_symbol()))
        self.wxCashProfitPercent.SetLabel(label=self.m_quote.sv_profitPercent(self.m_quote.currency(), QuoteType.cash))

        # refresh credit
        self.wxCreditNumOfShares.SetLabel(label=self.m_quote.sv_number(QuoteType.credit))
        self.wxCreditPRU.SetLabel(label=self.m_quote.sv_pru(QuoteType.credit, fmt="{:.2f}", bDispCurrency=True))
        self.wxCreditPR.SetLabel(label=self.m_quote.sv_pr(QuoteType.credit, bDispCurrency=True))

        profit = self.m_quote.nv_profit(self.m_quote.currency(), QuoteType.credit)
        if profit == 0:
            self.wxCreditProfit.SetForegroundColour(colour=wx.BLACK)
            self.wxCreditProfitPercent.SetForegroundColour(colour=wx.BLACK)
        elif profit < 0:
            self.wxCreditProfit.SetForegroundColour(colour=wx.RED)
            self.wxCreditProfitPercent.SetForegroundColour(colour=wx.RED)
        else:
            self.wxCreditProfit.SetForegroundColour(colour=wx.BLUE)
            self.wxCreditProfitPercent.SetForegroundColour(colour=wx.BLUE)

        self.wxCreditProfit.SetLabel(label=u"{} {}".format(self.m_quote.sv_profit(self.m_quote.currency(), QuoteType.credit, fmt="{:.0f}"), self.m_quote.currency_symbol()))
        self.wxCreditProfitPercent.SetLabel(label=self.m_quote.sv_profitPercent(self.m_quote.currency(), QuoteType.credit))

        # Purchasing Power
        self.m_portfolio.computeOperations()

        cash = self.m_portfolio.nv_cash()
        if cash == 0:
            self.wxAvailableCash.SetForegroundColour(colour=wx.BLACK)
            self.wxAvailableCashQC.SetForegroundColour(colour=wx.BLACK)
        elif cash < 0:
            self.wxAvailableCash.SetForegroundColour(colour=wx.RED)
            self.wxAvailableCashQC.SetForegroundColour(colour=wx.RED)
        else:
            self.wxAvailableCash.SetForegroundColour(colour=wx.BLUE)
            self.wxAvailableCashQC.SetForegroundColour(colour=wx.BLUE)
        self.wxAvailableCash.SetLabel(label=self.m_portfolio.sv_cash(currency=self.m_portfolio.currency(), fmt="{:.0f}", bDispCurrency=True))
        self.wxAvailableCashQC.SetLabel(label=self.m_portfolio.sv_cash(currency=self.m_quote.currency(), fmt="{:.0f}", bDispCurrency=True))

        self.wxCommittedCredit.SetLabel(label=self.m_portfolio.sv_credit(currency=self.m_portfolio.currency(), fmt="{:.0f}", bDispCurrency=True))
        self.wxAvailableCredit.SetLabel(label=u'?')
        self.wxAvailableCreditQC.SetLabel(label=u'?')

        show = (self.m_portfolio.currency() != self.m_quote.currency())
        self.wxLabelAvailableCashQC.Show(show=show)
        self.wxAvailableCashQC.Show(show=show)
        self.wxLabelAvailableCreditQC.Show(show=show)
        self.wxAvailableCreditQC.Show(show=show)

        # a little trick to make sure that you can't resize the dialog to
        # less screen space than the controls need
        self.Fit()
        self.SetMinSize(minSize=self.GetSize())


class WndTest(wx.Frame):
    def __init__(self, parent, quote, portfolio):
        wx.Frame.__init__(self, parent=parent, title='WndTest', size=(600,190), style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        self.m_decision = iTrade_wxDecision(self, quote, portfolio)

        self.Fit()
        self.SetMinSize(minSize=self.GetSize())

# ============================================================================
# Test me
# ============================================================================

def main():
    setLevel(logging.INFO)
    # load configuration
    import itrade_config
    itrade_config.load_config()
    from itrade_local import gMessage
    gMessage.setLang('us')
    gMessage.load()
    # load extensions
    import itrade_ext
    itrade_ext.loadExtensions(itrade_config.fileExtData, itrade_config.dirExtData)
    # init modules
    initQuotesModule()
    ticker = 'GTO'
    quote = quotes.lookupTicker(ticker=ticker)
    info(u'{}: {}'.format(ticker, quote))
    from itrade_portfolio import initPortfolioModule, loadPortfolio
    initPortfolioModule()
    port = loadPortfolio('default')
    app = wx.App()
    frame = WndTest(None, quote, port)
    if frame:
        frame.Show(show=True)
        app.MainLoop()


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
