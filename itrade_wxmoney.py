#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxmoney.py
#
# Description: wxPython money management screens (risk, portfolio evaluation, ...)
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is	Gilles Dumortier.
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
# 2005-11-1x    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
from datetime import *

# iTrade system
import itrade_config

# wxPython system
if not itrade_config.nowxversion:
    import itrade_wxversion
import wx

# iTrade system
from itrade_logging import *
import itrade_config
from itrade_local import message
from itrade_quotes import QUOTE_BOTH,QUOTE_CASH,QUOTE_CREDIT
from itrade_portfolio import *

# iTrade wxPython system
from itrade_wxhtml import wxUrlClickHtmlWindow,EVT_HTML_URL_CLICK
import itrade_wxres
from itrade_wxmixin import iTrade_wxFrame

# ============================================================================
# menu identifier
# ============================================================================

ID_SAVE = 110
ID_CLOSE = 111

# ============================================================================
# iTradeMoneyPanel
#
#   Money management
# ============================================================================

class iTradeMoneyPanel(wx.Window):

    def __init__(self,parent,id,port):
        wx.Window.__init__(self, parent, id)
        self.m_port = port
        self.m_currentItem = -1

    def refresh(self):
        pass

# ============================================================================
# iTradeEvaluationChartPanel
#
#   Display portfolio evaluation chart
# ============================================================================

class iTradeEvaluationChartPanel(wx.Window):

    def __init__(self,parent,id,port):
        wx.Window.__init__(self, parent, id)
        self.m_port = port
        self.m_currentItem = -1

    def refresh(self):
        pass

# ============================================================================
# iTradeComputeChartPanel
#
#   Computer
# ============================================================================

class iTradeComputePanel(wx.Window):

    def __init__(self,parent,id,quote):
        wx.Window.__init__(self, parent, id)
        self.m_quote = quote
        self.m_currentItem = -1

    def refresh(self):
        pass

# ============================================================================
# iTradeEvaluationPanel
#
#   Display textual evaluation of the portfolio
# ============================================================================

class iTradeEvaluationPanel(wx.Window):

    def __init__(self,parent,id,port):
        wx.Window.__init__(self, parent, id)
        self.m_parent = parent
        self.m_port = port
        self.m_currentItem = -1

        self.m_html = wxUrlClickHtmlWindow(self, -1)
        EVT_HTML_URL_CLICK(self.m_html, self.OnLinkClick)

        wx.EVT_SIZE(self, self.OnSize)

        self.m_html.Show(False)

    # ---[ Default OnLinkClick handler ] --------------------------------------

    def OnLinkClick(self, event):
        info('iTradeEvaluationPanel::OnLinkClick: %s - ignore it' % event.linkinfo[0])
        #clicked = event.linkinfo[0]
        pass

    # ---[ Window Management ]-------------------------------------------------

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.m_html.SetDimensions(0, 0, w, h)

    def InitCurrentPage(self,bReset=True):
        if bReset:
            # update portfolio and matrix (just in case)
            self.m_portfolio = self.m_parent.m_portfolio
            self.m_matrix = self.m_parent.m_matrix

        # refresh page content
        self.refresh()
        self.m_html.Show(True)

    def DoneCurrentPage(self):
        self.m_html.Show(False)

    # ---[ Compute & Display Evaluation ]--------------------------------------

    def compute(self,year):
        self.m_port.computeOperations(year)
        return (self.m_port.nv_expenses(),self.m_port.nv_transfer(),self.m_port.nv_appreciation(),self.m_port.nv_taxable(),self.m_port.nv_taxes())

    def refresh(self):
        self.m_port.computeOperations()
        # __x localisation + better look + previous year information + ...
        # __x hopefully for next release :-)
        self.m_html.SetPage('<html><meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"><body>')
        self.m_html.AppendToPage('<table border="1" cellpadding="2" cellspacing="1" class="bright">')
        self.m_html.AppendToPage(' <tr align="right" class="T20">')
        self.m_html.AppendToPage('   <td align="left" nowrap><b>%s</b></td>' % message('money_portfolio'))
        self.m_html.AppendToPage('   <td align="left" nowrap>%s</td>' % self.m_port.filename())
        self.m_html.AppendToPage(' </tr>')
        self.m_html.AppendToPage(' <tr align="right" class="L20">')
        self.m_html.AppendToPage('   <td align="left" nowrap>%s</td>' % message('money_description'))
        self.m_html.AppendToPage('   <td align="left" nowrap>%s</td>' % self.m_port.name())
        self.m_html.AppendToPage(' </tr>')
        self.m_html.AppendToPage(' <tr align="right" class="L20">')
        self.m_html.AppendToPage('   <td align="left" nowrap>%s</td>' % message('money_account_number'))
        self.m_html.AppendToPage('   <td align="left" nowrap>%s</td>' % self.m_port.accountref())
        self.m_html.AppendToPage(' </tr>')
        self.m_html.AppendToPage('</table>')
        self.m_html.AppendToPage('<br><br>')
        self.m_html.AppendToPage('<table border="1" cellpadding="2" cellspacing="1" width="100%" class="bright">')
        self.m_html.AppendToPage(' <tr align="right" class="T20">')
        self.m_html.AppendToPage('   <td align="left" nowrap></td>')
        self.m_html.AppendToPage('   <td align="right" ><b>%s</b></td>' % message('money_initial_investment'))
        self.m_html.AppendToPage('   <td align="right" nowrap><b>%s %s</b></td>' % (message('money_value'),date.today()))
        self.m_html.AppendToPage('   <td align="right" nowrap><b>%s</b></td>' % message('money_performance'))
        self.m_html.AppendToPage('   <td align="center" nowrap><b>%</b></td>')
        self.m_html.AppendToPage(' </tr>')
        self.m_html.AppendToPage(' <tr align="right" class="L20">')
        self.m_html.AppendToPage('   <td align="left" nowrap><b>%s</b></td>' % message('money_investment_evaluation'))
        self.m_html.AppendToPage('   <td align="right" nowrap>%s</b></td>' % (self.m_port.sv_invest(bDispCurrency=True)))
        self.m_html.AppendToPage('   <td align="right" nowrap>%s</b></td>' % (self.m_port.sv_totalValue(bDispCurrency=True)))
        self.m_html.AppendToPage('   <td align="right" nowrap>%s</b></td>' % (self.m_port.sv_perfTotal(bDispCurrency=True)))
        self.m_html.AppendToPage('   <td align="right" nowrap>%s</b></td>' % (self.m_port.sv_perfTotalPercent()))
        self.m_html.AppendToPage(' </tr>')
        self.m_html.AppendToPage(' <tr align="right" class="L20">')
        self.m_html.AppendToPage('   <td align="left" nowrap>%s</td>' % (message('money_srd')))
        self.m_html.AppendToPage('   <td align="right" nowrap>%s</b></td>' % (self.m_port.sv_credit(bDispCurrency=True)))
        self.m_html.AppendToPage('   <td align="right" nowrap>%s</b></td>' % (self.m_port.sv_value(QUOTE_CREDIT,bDispCurrency=True)))
        self.m_html.AppendToPage('   <td align="right" nowrap>%s</b></td>' % (self.m_port.sv_perf(QUOTE_CREDIT,bDispCurrency=True)))
        self.m_html.AppendToPage('   <td align="center" nowrap>%s</td>'    % (self.m_port.sv_perfPercent(QUOTE_CREDIT)))
        self.m_html.AppendToPage(' </tr>') # __x
        self.m_html.AppendToPage(' <tr align="right" class="L20">')
        self.m_html.AppendToPage('   <td align="left" nowrap>%s (%2.2f%s)</td>' % (message('money_cash'),self.m_port.nv_percentCash(QUOTE_CASH),message('money_percent_of_portfolio')))
        self.m_html.AppendToPage('   <td align="right" nowrap></td>')
        self.m_html.AppendToPage('   <td align="right" nowrap>%s</b></td>' % (self.m_port.sv_cash(bDispCurrency=True)))
        self.m_html.AppendToPage(' </tr>')
        self.m_html.AppendToPage(' <tr align="right" class="L20">')
        self.m_html.AppendToPage('   <td align="left" nowrap>%s (%2.2f%s)</td>' % (message('money_quote'),self.m_port.nv_percentQuotes(QUOTE_CASH),message('money_percent_of_portfolio')))
        self.m_html.AppendToPage('   <td align="right" nowrap>%s</b></td>' % (self.m_port.sv_buy(QUOTE_CASH,bDispCurrency=True)))
        self.m_html.AppendToPage('   <td align="right" nowrap>%s</b></td>' % (self.m_port.sv_value(QUOTE_CASH,bDispCurrency=True)))
        self.m_html.AppendToPage('   <td align="right" nowrap>%s</b></td>' % (self.m_port.sv_perf(QUOTE_CASH,bDispCurrency=True)))
        self.m_html.AppendToPage('   <td align="center" nowrap>%s</td>'    % (self.m_port.sv_perfPercent(QUOTE_CASH)))
        self.m_html.AppendToPage(' </tr>')
        self.m_html.AppendToPage('</table>')
        self.m_html.AppendToPage('<br>')
        self.m_html.AppendToPage('<br>')
        self.m_html.AppendToPage('<table border="1" cellpadding="2" cellspacing="1" width="320" class="bright">')
        self.m_html.AppendToPage(' <tr align="right" class="T20">')
        self.m_html.AppendToPage('   <td align="left" nowrap><b>%s</b></td>' % message('money_fiscal_year'))
        self.m_html.AppendToPage('   <td align="right" class="percent" nowrap><b>%d</b></td>' % (date.today().year-2))
        self.m_html.AppendToPage('   <td align="right" class="percent" nowrap><b>%d</b></td>' % (date.today().year-1))
        self.m_html.AppendToPage('   <td align="right" class="percent" nowrap><b>%d</b></td>' % date.today().year)
        self.m_html.AppendToPage(' </tr>')

        expenses0,transfer0,appr0,taxable0,taxes0 = self.compute(date.today().year-2)
        expenses1,transfer1,appr1,taxable1,taxes1 = self.compute(date.today().year-1)
        expenses2,transfer2,appr2,taxable2,taxes2 = self.compute(date.today().year)

        self.m_html.AppendToPage(' <tr align="right" class="T20">')
        self.m_html.AppendToPage('   <td align="left" nowrap>%s</td>' % message('money_expenses_vat'))
        self.m_html.AppendToPage('   <td align="right" nowrap>%.2f %s</td>' % (expenses0,self.m_port.currency_symbol()))
        self.m_html.AppendToPage('   <td align="right" nowrap>%.2f %s</td>' % (expenses1,self.m_port.currency_symbol()))
        self.m_html.AppendToPage('   <td align="right" nowrap>%.2f %s</td>' % (expenses2,self.m_port.currency_symbol()))
        self.m_html.AppendToPage(' </tr>')
        self.m_html.AppendToPage(' <tr align="right" class="T20">')
        self.m_html.AppendToPage('   <td align="left" nowrap>%s</td>' % message('money_total_of_transfers'))
        self.m_html.AppendToPage('   <td align="right" nowrap>%.2f %s</td>' % (transfer0,self.m_port.currency_symbol()))
        self.m_html.AppendToPage('   <td align="right" nowrap>%.2f %s</td>' % (transfer1,self.m_port.currency_symbol()))
        self.m_html.AppendToPage('   <td align="right" nowrap>%.2f %s</td>' % (transfer2,self.m_port.currency_symbol()))
        self.m_html.AppendToPage(' </tr>')
        self.m_html.AppendToPage(' <tr align="right" class="T20">')
        self.m_html.AppendToPage('   <td align="left" nowrap>%s</td>' % message('money_financial_appreciation'))
        self.m_html.AppendToPage('   <td align="right" nowrap>%.2f %s</td>' % (appr0,self.m_port.currency_symbol()))
        self.m_html.AppendToPage('   <td align="right" nowrap>%.2f %s</td>' % (appr1,self.m_port.currency_symbol()))
        self.m_html.AppendToPage('   <td align="right" nowrap>%.2f %s</td>' % (appr2,self.m_port.currency_symbol()))
        self.m_html.AppendToPage(' </tr>')
        self.m_html.AppendToPage(' <tr align="right" class="T20">')
        self.m_html.AppendToPage('   <td align="left" nowrap>%s</td>' % message('money_taxable_amounts'))
        self.m_html.AppendToPage('   <td align="right" nowrap>%.2f %s</td>' % (taxable0,self.m_port.currency_symbol()))
        self.m_html.AppendToPage('   <td align="right" nowrap>%.2f %s</td>' % (taxable1,self.m_port.currency_symbol()))
        self.m_html.AppendToPage('   <td align="right" nowrap>%.2f %s</td>' % (taxable2,self.m_port.currency_symbol()))
        self.m_html.AppendToPage(' </tr>')
        self.m_html.AppendToPage(' <tr align="right" class="T20">')
        self.m_html.AppendToPage('   <td align="left" nowrap>%s</td>' % message('money_amount_of_taxes'))
        self.m_html.AppendToPage('   <td align="right" nowrap>%.2f %s</td>' % (taxes0,self.m_port.currency_symbol()))
        self.m_html.AppendToPage('   <td align="right" nowrap>%.2f %s</td>' % (taxes1,self.m_port.currency_symbol()))
        self.m_html.AppendToPage('   <td align="right" nowrap>%.2f %s</td>' % (taxes2,self.m_port.currency_symbol()))
        self.m_html.AppendToPage(' </tr>')
        self.m_html.AppendToPage('</table>')
        self.m_html.AppendToPage("</body></html>")

# ============================================================================
# iTradeMoneyNotebookWindow
# ============================================================================

class iTradeMoneyNotebookWindow(wx.Notebook):

    ID_PAGE_EVALUATION = 0
    ID_PAGE_COMPUTE = 1
    ID_PAGE_EVALCHART = 2
    ID_PAGE_MONEY = 3

    def __init__(self,parent,id,page,port,quote):
        wx.Notebook.__init__(self,parent,id,wx.DefaultPosition, style=wx.SIMPLE_BORDER|wx.NB_TOP)
        self.m_port = port
        self.m_quote = quote
        self.init()

        wx.EVT_NOTEBOOK_PAGE_CHANGED(self, id, self.OnPageChanged)
        wx.EVT_NOTEBOOK_PAGE_CHANGING(self, id, self.OnPageChanging)

        # __x select page

    def init(self):
        self.win = {}
        self.DeleteAllPages()

        self.win[self.ID_PAGE_EVALUATION] = iTradeEvaluationPanel(self,wx.NewId(),self.m_port)
        self.AddPage(self.win[self.ID_PAGE_EVALUATION], message('money_evaluation'))

        self.win[self.ID_PAGE_COMPUTE] = iTradeComputePanel(self,wx.NewId(),self.m_quote)
        self.AddPage(self.win[self.ID_PAGE_COMPUTE], message('money_compute'))

        self.win[self.ID_PAGE_EVALCHART] = iTradeEvaluationChartPanel(self,wx.NewId(),self.m_port)
        self.AddPage(self.win[self.ID_PAGE_EVALCHART], message('money_evaluationchart'))

        self.win[self.ID_PAGE_MONEY] = iTradeMoneyPanel(self,wx.NewId(),self.m_port)
        self.AddPage(self.win[self.ID_PAGE_MONEY], message('money_money'))

    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        info('OnPageChanged,  old:%d, new:%d, sel:%d\n' % (old, new, sel))
        if old != new:
            self.win[new].refresh()
        event.Skip()

    def OnPageChanging(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        info('OnPageChanging, old:%d, new:%d, sel:%d\n' % (old, new, sel))
        event.Skip()

# ============================================================================
# iTradeMoneyWindow
# ============================================================================

class iTradeMoneyWindow(wx.Frame,iTrade_wxFrame):

    def __init__(self,parent,id,title,page,port,quote):
        self.m_id = wx.NewId()
        wx.Frame.__init__(self,None,self.m_id, title, size = (640,480), style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        iTrade_wxFrame.__init__(self,parent,'money')
        self.m_port = port
        self.m_quote = quote
        self.m_page = page

        self.m_book = iTradeMoneyNotebookWindow(self, -1, page=self.m_page,port=self.m_port,quote=self.m_quote)

        wx.EVT_WINDOW_DESTROY(self, self.OnDestroy)
        wx.EVT_SIZE(self, self.OnSize)

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.m_book.SetDimensions(0, 0, w, h)

    def OnDestroy(self, evt):
        if self.m_parent:
            self.m_parent.m_hMoney = None

# ============================================================================
# open_iTradeMoney
# ============================================================================

def open_iTradeMoney(win,page=0,port=None,quote=None):
    debug('open_iTradeMoney')
    if win and win.m_hMoney:
        # set focus
        win.m_hMoney.SetFocus()
    else:
        if not isinstance(port,Portfolio):
            port = loadPortfolio()
        frame = iTradeMoneyWindow(win, -1, "%s - %s" %(message('money_title'),port.name()),page,port,quote)
        if win:
            win.m_hMoney = frame
        frame.Show()

# ============================================================================
# Test me
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    app = wx.App(False)

    from itrade_local import *
    setLang('us')
    gMessage.load()

    port,matrix = cmdline_evaluatePortfolio()

    open_iTradeMoney(None,port,None)
    app.MainLoop()

# ============================================================================
# That's all folks !
# ============================================================================
