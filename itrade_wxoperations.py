#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxoperations.py
#
# Description: wxPython portfolio operations screen
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
# 2006-01-1x    dgil  Split code from original itrade_wxportfolio.py module
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import absolute_import
from datetime import timedelta, datetime, date
import logging
import os

# iTrade system
import itrade_config
from six.moves import range

# wxPython system
if not itrade_config.nowxversion:
    import itrade_wxversion
import wx
import wx.lib.mixins.listctrl as wxl
from wx.lib import masked
# import sized_controls from wx.lib for wxPython version >= 2.8.8.0 (from wxaddons otherwise)
import wx.lib.sized_controls as sc

# iTrade system
from itrade_logging import setLevel, info, debug
from itrade_local import message, getGroupChar, getDecimalChar
from itrade_quotes import initQuotesModule, quotes
from itrade_portfolio import loadPortfolio, initPortfolioModule, create_operation, Portfolio, OPERATION_LIQUIDATION,\
    OPERATION_SELL, isOperationTypeHasShareNumber, signOfOperationType, isOperationTypeIncludeTaxes,\
    isOperationTypeAQuote, OPERATION_BUY, OPERATION_CREDIT, OPERATION_DEBIT, OPERATION_FEE, OPERATION_DIVIDEND,\
    OPERATION_DETACHMENT, OPERATION_INTEREST, OPERATION_BUY_SRD, OPERATION_SELL_SRD, OPERATION_QUOTE, OPERATION_REGISTER
from itrade_currency import currency2symbol

from itrade_wxselectquote import select_iTradeQuote
from itrade_wxmixin import iTrade_wxFrame
from itrade_wxutil import FontFromSize, iTradeSizedDialog

# ============================================================================
# menu identifier
# ============================================================================

ID_CLOSE = 111

ID_DISPALL = 120
ID_DISPQUOTES = 121
ID_DISPCASH = 122
ID_DISPSRD = 123
ID_DISPPVAL = 124

ID_SMALL_TEXT = 230
ID_NORMAL_TEXT = 231
ID_BIG_TEXT = 232

ID_MODIFY = 150
ID_DELETE = 151
ID_ADD = 152

ID_30DAYS = 200
ID_90DAYS = 201
ID_CURRENTYEAR = 202
ID_ALLYEARS = 203

# ============================================================================
# display mode
# ============================================================================

DISP_ALL    = 0
DISP_QUOTES = 1
DISP_CASH   = 2
DISP_SRD    = 3
DISP_PVAL   = 4

# ============================================================================
# period mode
# ============================================================================

PERIOD_30DAYS = 0
PERIOD_90DAYS = 1
PERIOD_CURRENTYEAR = 2
PERIOD_ALLYEARS = 3

# ============================================================================
# List identifier
# ============================================================================

IDC_DATE = 0
IDC_OPERATION = 1
IDC_DESCRIPTION = 2
IDC_PRU = 3
IDC_NUMBER = 4
IDC_DEBIT = 5
IDC_CREDIT = 6
IDC_EXPENSES = 7
IDC_BALANCE = 8
IDC_SRD = 9
IDC_RESERVED = 10

# ============================================================================
#
# ============================================================================

OPERATION_MODIFY = 0
OPERATION_ADD = 1
OPERATION_DELETE = 2

# ============================================================================
# List of supported operations
# ============================================================================

operation_ctrl = (
    (OPERATION_BUY, 'portfolio_ctrl_buy'),
    (OPERATION_SELL, 'portfolio_ctrl_sell'),
    (OPERATION_CREDIT, 'portfolio_ctrl_credit'),
    (OPERATION_DEBIT, 'portfolio_ctrl_debit'),
    (OPERATION_FEE, 'portfolio_ctrl_fee'),
    (OPERATION_DIVIDEND, 'portfolio_ctrl_dividend'),
    (OPERATION_DETACHMENT, 'portfolio_ctrl_detachment'),
    (OPERATION_INTEREST, 'portfolio_ctrl_interest'),
    (OPERATION_BUY_SRD, 'portfolio_ctrl_buy_srd'),
    (OPERATION_SELL_SRD, 'portfolio_ctrl_sell_srd'),
    (OPERATION_LIQUIDATION, 'portfolio_ctrl_liquidation'),
    (OPERATION_QUOTE, 'portfolio_ctrl_quote'),
    (OPERATION_REGISTER, 'portfolio_ctrl_register')
#    OPERATION_SPLIT     : 'portfolio_ctrl_split'
    )

# ============================================================================
# iTradeOperationsDialog
#
#   parent      parent window
#   op          Operation structure (pre-filling optional)
#   opmode      EDIT, ADD, DELETE
# ============================================================================

class iTradeOperationDialog(iTradeSizedDialog):
    def __init__(self, parent, op, opmode, market=None, currency='EUR'):
        # pre-init
        self.opmode = opmode

        self.m_market = market

        if op:
            self.m_type = op.type()
            self.m_value = op.nv_value()
            self.m_expenses = op.nv_expenses()
            self.m_number = op.nv_number()
            self.m_name = op.name()
            if op.isQuote():
                if op.quote():
                    self.m_name = op.quote().key()
                    self.m_market = op.quote().market()
            self.m_datetime = op.datetime()
            self.m_ref = op.ref()
        else:
            self.m_type = OPERATION_SELL
            self.m_value = 0.0
            self.m_expenses = 0.0
            self.m_number = 0
            self.m_name = ""
            self.m_datetime = datetime.now()
            self.m_ref = -1

        self.m_parent = parent

        if opmode == OPERATION_MODIFY:
            tb = message('portfolio_modify')
        elif opmode == OPERATION_ADD:
            tb = message('portfolio_new')
        elif opmode == OPERATION_DELETE:
            tb = message('portfolio_delete')
        else:
            tb = '??'
        tt = tb + ' {} - {} {}'
        if op:
            self.tt = tt.format(op.datetime().strftime('%x'), op.operation(), op.description())
        else:
            self.tt = tb

        # init
        iTradeSizedDialog.__init__(self, parent, wx.ID_ANY, self.tt, style=wx.DEFAULT_DIALOG_STYLE, size=(420, 480))

        # container
        container = self.GetContentsPane()
        container.SetSizerType("vertical")

        # resizable pane
        pane = sc.SizedPanel(container, wx.ID_ANY)
        pane.SetSizerType("form")
        pane.SetSizerProps(expand=True)

        # Row 1 : date
        label = wx.StaticText(parent=pane, id=wx.ID_ANY, label=message('portfolio_date'))
        label.SetSizerProps(valign='center')

        ssdatetime = wx.DateTimeFromDMY(day=self.m_datetime.day, month=self.m_datetime.month-1, year=self.m_datetime.year)
        self.wxDateCtrl = wx.DatePickerCtrl(parent=pane, id=wx.ID_ANY, dt=ssdatetime, size=(120, -1),
                                            style=wx.DP_DROPDOWN | wx.DP_SHOWCENTURY)
        wx.EVT_DATE_CHANGED(self, self.wxDateCtrl.GetId(), self.OnDate)

        # Row 2 : time
        label = wx.StaticText(parent=pane, id=wx.ID_ANY, label=message('portfolio_time'))
        label.SetSizerProps(valign='center')

        hhmmsstime = wx.DateTimeFromHMS(hour=self.m_datetime.hour, minute=self.m_datetime.minute, second=self.m_datetime.second)
        self.wxTimeCtrl = masked.TimeCtrl(parent=pane, id=wx.ID_ANY, value=hhmmsstime, format='24HHMMSS')
        self.Bind(masked.EVT_TIMEUPDATE, self.OnTime, self.wxTimeCtrl )

        # Row 3 : kind of operation
        label = wx.StaticText(parent=pane, id=wx.ID_ANY, label=message('portfolio_operation'))
        label.SetSizerProps(valign='center')

        self.wxTypeCtrl = wx.ComboBox(parent=pane, id=wx.ID_ANY, value="", size=wx.Size(160, -1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
        wx.EVT_COMBOBOX(self, self.wxTypeCtrl.GetId(), self.OnType)

        idx = wx.NOT_FOUND
        for count, (k, v) in enumerate(operation_ctrl):
            # print('***',message(v),k)
            self.wxTypeCtrl.Append(message(v), k)
            if k == self.m_type:
                idx = count

        self.wxTypeCtrl.SetSelection(n=idx)

        # Row 4 : quote
        btnpane = sc.SizedPanel(container, wx.ID_ANY)
        btnpane.SetSizerType("horizontal")
        btnpane.SetSizerProps(expand=True)

        self.wxNameLabel = wx.StaticText(parent=btnpane, id=wx.ID_ANY, label=message('portfolio_description'))
        self.wxNameLabel.SetSizerProps(valign='center')

        bmp = wx.Bitmap(os.path.join(itrade_config.dirRes, 'quotes.png'))
        self.wxNameButton = wx.BitmapButton(parent=btnpane, id=wx.ID_ANY, bitmap=bmp, size=wx.Size(bmp.GetWidth()+5, bmp.GetHeight()+5))
        wx.EVT_BUTTON(self, self.wxNameButton.GetId(), self.OnQuote)

        # print('creating ctrl:',self.m_name)
        self.wxNameCtrl = wx.TextCtrl(parent=btnpane, id=wx.ID_ANY, value=self.m_name, size=wx.Size(240, -1), style=wx.TE_LEFT)
        wx.EVT_TEXT(self, self.wxNameCtrl.GetId(), self.OnDescChange)
        self.wxNameCtrl.SetSizerProps(expand=True)

        # Row 5 : value
        btnpane = sc.SizedPanel(container, wx.ID_ANY)
        btnpane.SetSizerType("horizontal")
        btnpane.SetSizerProps(expand=True)

        self.wxValueLabel = wx.StaticText(parent=btnpane, id=wx.ID_ANY, label=message('portfolio_field_credit'))
        self.wxValueLabel.SetSizerProps(valign='center')

        self.wxValueCtrl = masked.Ctrl(btnpane, integerWidth=9, fractionWidth=2, controlType=masked.controlTypes.NUMBER,
                                       allowNegative=False, groupDigits=True, groupChar=getGroupChar(),
                                       decimalChar=getDecimalChar(), selectOnEntry=True)
        wx.EVT_TEXT( self, self.wxValueCtrl.GetId(), self.OnValueChange )

        self.wxValueTxt = wx.StaticText(parent=btnpane, id=wx.ID_ANY, label=currency2symbol(currency))
        self.wxValueTxt.SetSizerProps(valign='center')

        self.wxExpPreTxt = wx.StaticText(parent=btnpane, id=wx.ID_ANY, label='')
        self.wxExpPreTxt.SetSizerProps(valign='center')

        self.wxExpensesCtrl = masked.Ctrl(btnpane, integerWidth=4, fractionWidth=2,
                                          controlType=masked.controlTypes.NUMBER, allowNegative=False,
                                          groupDigits=True, groupChar=getGroupChar(), decimalChar=getDecimalChar(),
                                          selectOnEntry=True)
        wx.EVT_TEXT( self, self.wxExpensesCtrl.GetId(), self.OnExpensesChange )

        self.wxExpPostTxt = wx.StaticText(parent=btnpane, id=wx.ID_ANY, label=u"{} {}".format(currency2symbol(currency), message('portfolio_post_expenses')))
        self.wxExpPostTxt.SetSizerProps(valign='center')

        # resizable pane
        pane = sc.SizedPanel(container, wx.ID_ANY)
        pane.SetSizerType("form")
        pane.SetSizerProps(expand=True)

        # number
        label = wx.StaticText(parent=pane, id=wx.ID_ANY, label=message('portfolio_quantity'))
        label.SetSizerProps(valign='center')

        self.wxNumberCtrl = masked.Ctrl(pane, integerWidth=9, fractionWidth=0, controlType=masked.controlTypes.NUMBER,
                                        allowNegative=False, groupChar=getGroupChar(), decimalChar=getDecimalChar())
        wx.EVT_TEXT(self, self.wxNumberCtrl.GetId(), self.OnNumberChange)

        # separator
        line = wx.StaticLine(parent=container, id=wx.ID_ANY, size=(20,-1), style=wx.LI_HORIZONTAL)
        line.SetSizerProps(expand=True)

        # Last Row : OK and Cancel
        btnpane = sc.SizedPanel(container, wx.ID_ANY)
        btnpane.SetSizerType("horizontal")
        btnpane.SetSizerProps(expand=True)

        # context help
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(btnpane)

        # OK
        btn = wx.Button(btnpane, wx.ID_OK, tb)
        btn.SetDefault()
        btn.SetHelpText(text=message('ok_desc'))
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnValid)

        # CANCEL
        btn = wx.Button(btnpane, wx.ID_CANCEL, message('cancel'))
        btn.SetHelpText(text=message('cancel_desc'))
        wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)

        self.refreshPage()

    def OnCancel(self, event):
        self.aRet = None
        self.EndModal(wx.ID_CANCEL)

    def OnValid(self, event):
        if self.Validate() and self.TransferDataFromWindow():
            self.aRet = (self.m_datetime, self.m_type, self.m_name, self.m_value, self.m_expenses, self.m_number,
                         self.m_ref)
            self.EndModal(wx.ID_OK)

    def refreshPage(self):
        self.wxDateCtrl.SetValue(dt=wx.DateTimeFromDMY(self.m_datetime.day, self.m_datetime.month-1, self.m_datetime.year))
        self.wxValueCtrl.SetValue(self.m_value)
        self.wxExpensesCtrl.SetValue(self.m_expenses)
        self.wxNumberCtrl.SetValue(self.m_number)
        self.wxNameCtrl.SetLabel(label=self.m_name)

        if isOperationTypeIncludeTaxes(self.m_type):
            self.wxExpPreTxt.SetLabel(label=message('portfolio_pre_expenses1'))
        else:
            self.wxExpPreTxt.SetLabel(label=message('portfolio_pre_expenses2'))

        sign = signOfOperationType(self.m_type)
        if sign == '+':
            self.wxValueLabel.SetLabel(label=message('portfolio_field_credit'))
            self.wxExpensesCtrl.Show(True)
            self.wxValueCtrl.Show(True)
            self.wxValueTxt.Show(show=True)
            self.wxExpPreTxt.Show(show=True)
            self.wxExpPostTxt.Show(show=True)
        elif sign == '-':
            self.wxValueLabel.SetLabel(label=message('portfolio_field_debit'))
            self.wxExpensesCtrl.Show(True)
            self.wxValueCtrl.Show(True)
            self.wxValueTxt.Show(show=True)
            self.wxExpPreTxt.Show(show=True)
            self.wxExpPostTxt.Show(show=True)
        elif sign == '~':
            self.wxValueLabel.SetLabel(label=message('portfolio_field_valorization'))
            self.wxValueCtrl.Show(True)
            self.wxValueTxt.Show(show=True)
            self.wxExpensesCtrl.Show(False)
            self.wxExpPreTxt.Show(show=False)
            self.wxExpPostTxt.Show(show=False)
        else:
            self.wxValueLabel.SetLabel(label=message('portfolio_field_freeofcharges'))
            self.wxExpensesCtrl.Show(False)
            self.wxValueCtrl.Show(False)
            self.wxValueTxt.Show(show=False)
            self.wxExpPreTxt.Show(show=False)
            self.wxExpPostTxt.Show(show=False)

        if isOperationTypeAQuote(self.m_type):
            self.wxNameLabel.SetLabel(label=message('portfolio_quote'))
            self.wxNameButton.Enable(enable=True)
            self.wxNameButton.Show(show=True)
            self.wxNameCtrl.Enable(enable=False)
            if isOperationTypeHasShareNumber(self.m_type):
                self.wxNumberCtrl.Enable(True)
            else:
                self.wxNumberCtrl.Enable(False)
        else:
            self.wxNameLabel.SetLabel(label=message('portfolio_description'))
            self.wxNameButton.Enable(enable=False)
            self.wxNameButton.Show(show=False)
            self.wxNameCtrl.Enable(enable=True)
            self.wxNumberCtrl.Enable(False)

        if self.opmode == OPERATION_DELETE:
            self.wxNumberCtrl.Enable(False)
            self.wxNameCtrl.Enable(enable=False)
            self.wxNameButton.Enable(enable=False)
            self.wxNumberCtrl.Enable(False)
            self.wxExpensesCtrl.Enable(False)
            self.wxValueCtrl.Enable(False)
            self.wxDateCtrl.Enable(enable=False)
            self.wxTypeCtrl.Enable(enable=False)

        # a little trick to make sure that you can't resize the dialog to
        # less screen space than the controls need
        self.Fit()
        self.SetMinSize(minSize=self.GetSize())

    def OnDate(self, evt):
        dRet = self.wxDateCtrl.GetValue()
        if dRet:
            debug('OnDate: {}\n'.format(dRet))
            self.m_datetime = self.m_datetime.combine(date(dRet.GetYear(), dRet.GetMonth()+1, dRet.GetDay()),
                                                      self.m_datetime.time())
            self.refreshPage()

    def OnTime(self, evt):
        dRet = self.wxTimeCtrl.GetValue(as_wxDateTime=True)
        if dRet:
            debug('OnTime: {}\n'.format(dRet))
            self.m_datetime = self.m_datetime.combine(date=self.m_datetime.date(),
                                                      time=datetime.time(hour=dRet.GetHour(), minute=dRet.GetMinute(), second=dRet.GetSecond()))
            self.refreshPage()

    def OnType(self, evt):
        t = self.wxTypeCtrl.GetClientData(self.wxTypeCtrl.GetSelection())
        debug("OnType {}".format(t))
        self.m_type = t
        self.refreshPage()

    def OnQuote(self, evt):
        quote = quotes.lookupKey(self.m_name)
        quote = select_iTradeQuote(win=self, dquote=quote, filter=True, market=self.m_market, tradableOnly=True)
        if quote:
            debug(u'onQuote: {} - {}'.format(quote.ticker(), quote.key()))
            self.m_name = quote.key()
            self.m_market = quote.market()
            self.refreshPage()

    def OnValueChange(self, event):
        ctl = self.FindWindowById(event.GetId())
        if ctl.IsValid():
            debug(u'new value value = {}\n'.format(ctl.GetValue()))
            self.m_value = float(ctl.GetValue())

    def OnNumberChange(self, event):
        ctl = self.FindWindowById(event.GetId())
        if ctl.IsValid():
            debug(u'new number value = {}\n'.format(ctl.GetValue()))
            self.m_number = int(ctl.GetValue())

    def OnExpensesChange(self, event):
        ctl = self.FindWindowById(event.GetId())
        if ctl.IsValid():
            debug('new expenses value = {}\n'.format(ctl.GetValue()))
            self.m_expenses = float(ctl.GetValue())

    def OnDescChange(self, event):
        ctl = self.FindWindowById(event.GetId())
        debug('new value value = {}\n'.format(ctl.GetValue()))
        self.m_name = ctl.GetValue()


class iTradeOperationsListCtrl(wx.ListCtrl, wxl.ListCtrlAutoWidthMixin):
    def __init__(self, parent, style=0, *args, **kwargs):
        wx.ListCtrl.__init__(self, parent=parent, style=style, *args, **kwargs)
        wxl.ListCtrlAutoWidthMixin.__init__(self)


class iTradeOperationToolbar(wx.ToolBar):
    def __init__(self, parent, *args, **kwargs):
        wx.ToolBar.__init__(self, parent=parent, style=wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT, *args, **kwargs)
        self.m_parent = parent
        self._init_toolbar()

    def _init_toolbar(self):
        self.SetToolBitmapSize(size=wx.Size(24, 24))
        exit_tool = self.AddSimpleTool(id=wx.ID_ANY, bitmap=wx.ArtProvider.GetBitmap(wx.ART_CROSS_MARK, wx.ART_TOOLBAR),
                           shortHelpString=message('main_close'), longHelpString=message('main_desc_close'))
        self.AddControl(wx.StaticLine(self, wx.ID_ANY, size=(-1, 23), style=wx.LI_VERTICAL))

        dispall_tool = self.AddRadioLabelTool(id=wx.ID_ANY, label='', bitmap=wx.Bitmap(os.path.join(itrade_config.dirRes, 'dispall.png')), shortHelp=message('portfolio_dispall'), longHelp=message('portfolio_desc_dispall'))
        quotes_tool = self.AddRadioLabelTool(id=wx.ID_ANY, label='', bitmap=wx.Bitmap(os.path.join(itrade_config.dirRes, 'dispquote.png')), shortHelp=message('portfolio_dispquotes'), longHelp=message('portfolio_desc_dispquotes'))
        cash_tool = self.AddRadioLabelTool(id=wx.ID_ANY, label='', bitmap=wx.Bitmap(os.path.join(itrade_config.dirRes, 'dispcash.png')), shortHelp=message('portfolio_dispcash'), longHelp=message('portfolio_desc_dispcash'))
        srd_tool = self.AddRadioLabelTool(id=wx.ID_ANY, label='', bitmap=wx.Bitmap(os.path.join(itrade_config.dirRes, 'dispsrd.png')), shortHelp=message('portfolio_dispsrd'), longHelp=message('portfolio_desc_dispsrd'))
        pval_tool = self.AddRadioLabelTool(id=wx.ID_ANY, label='', bitmap=wx.Bitmap(os.path.join(itrade_config.dirRes, 'dispvalue.png')), shortHelp=message('portfolio_dispvalues'), longHelp=message('portfolio_desc_dispvalues'))

        self.AddControl(wx.StaticLine(parent=self, id=wx.ID_ANY, size=(-1,23), style=wx.LI_VERTICAL))

        add_tool = self.AddSimpleTool(wx.ID_ANY, wx.Bitmap(os.path.join(itrade_config.dirRes, 'add.png')), message('portfolio_opadd'), message('portfolio_desc_opadd'))
        modify_tool = self.AddSimpleTool(wx.ID_ANY, wx.Bitmap(os.path.join(itrade_config.dirRes, 'modify.png')), message('portfolio_opmodify'), message('portfolio_desc_opmodify'))
        delete_tool = self.AddSimpleTool(wx.ID_ANY, wx.Bitmap(os.path.join(itrade_config.dirRes, 'delete.png')), message('portfolio_opdelete'), message('portfolio_desc_opdelete'))

        self.AddControl(wx.StaticLine(self, wx.ID_ANY, size=(-1, 23), style=wx.LI_VERTICAL))

        d30_tool = self.AddRadioLabelTool(wx.ID_ANY, '', wx.Bitmap(os.path.join(itrade_config.dirRes, 'filter30.png')), shortHelp=message('portfolio_per30days'), longHelp=message('portfolio_desc_per30days'))
        d90_tool = self.AddRadioLabelTool(wx.ID_ANY, '', wx.Bitmap(os.path.join(itrade_config.dirRes, 'filter90.png')), shortHelp=message('portfolio_per90days'), longHelp=message('portfolio_desc_per90days'))
        year_tool = self.AddRadioLabelTool(wx.ID_ANY, '', wx.Bitmap(os.path.join(itrade_config.dirRes, 'filter.png')),  shortHelp=message('portfolio_peryear'), longHelp=message('portfolio_desc_peryear'))
        all_tool = self.AddRadioLabelTool(wx.ID_ANY, '', wx.Bitmap(os.path.join(itrade_config.dirRes, 'nofilter.png')), shortHelp=message('portfolio_perall'), longHelp=message('portfolio_desc_perall'))

        self._NTB2_EXIT = exit_tool.GetId()
        wx.EVT_TOOL(self, self._NTB2_EXIT, self.onExit)

        self._NTB2_DISPALL = dispall_tool.GetId()
        wx.EVT_TOOL(self, self._NTB2_DISPALL, self.onDispAll)
        self._NTB2_DISPQUOTES = quotes_tool.GetId()
        wx.EVT_TOOL(self, self._NTB2_DISPQUOTES, self.onDispQuotes)
        self._NTB2_DISPCASH = cash_tool.GetId()
        wx.EVT_TOOL(self, self._NTB2_DISPCASH, self.onDispCash)
        self._NTB2_DISPSRD = srd_tool.GetId()
        wx.EVT_TOOL(self, self._NTB2_DISPSRD, self.onDispSRD)
        self._NTB2_DISPPVAL = pval_tool.GetId()
        wx.EVT_TOOL(self, self._NTB2_DISPPVAL, self.onDispPVal)

        self._NTB2_MODIFY = modify_tool.GetId()
        wx.EVT_TOOL(self, self._NTB2_MODIFY, self.onModify)
        self._NTB2_DELETE = delete_tool.GetId()
        wx.EVT_TOOL(self, self._NTB2_DELETE, self.onDelete)
        self._NTB2_ADD = add_tool.GetId()
        wx.EVT_TOOL(self, self._NTB2_ADD, self.onAdd)

        self._NTB2_30DAYS = d30_tool.GetId()
        wx.EVT_TOOL(self, self._NTB2_30DAYS, self.on30Days)
        self._NTB2_90DAYS = d90_tool.GetId()
        wx.EVT_TOOL(self, self._NTB2_90DAYS, self.on90Days)
        self._NTB2_CURRENTYEAR = year_tool.GetId()
        wx.EVT_TOOL(self, self._NTB2_CURRENTYEAR, self.onCurrentYear)
        self._NTB2_ALLYEARS = all_tool.GetId()
        wx.EVT_TOOL(self, self._NTB2_ALLYEARS, self.onAllYears)

        self.Realize()

    def onDispAll(self, event):
        self.m_parent.OnDispAll(event)

    def onDispQuotes(self, event):
        self.m_parent.OnDispQuotes(event)

    def onDispCash(self, event):
        self.m_parent.OnDispCash(event)

    def onDispSRD(self, event):
        self.m_parent.OnDispSRD(event)

    def onDispPVal(self, event):
        self.m_parent.OnDispPVal(event)

    def onAdd(self, event):
        self.m_parent.OnAdd(event)

    def onModify(self, event):
        self.m_parent.OnModify(event)

    def onDelete(self, event):
        self.m_parent.OnDelete(event)

    def on30Days(self, event):
        self.m_parent.On30Days(event)

    def on90Days(self, event):
        self.m_parent.On90Days(event)

    def onCurrentYear(self, event):
        self.m_parent.OnCurrentYear(event)

    def onAllYears(self, event):
        self.m_parent.OnAllYears(event)

    def onExit(self, event):
        self.m_parent.OnClose(event)

# ============================================================================
# iTradeOperationsWindow
# ============================================================================

class iTradeOperationsWindow(wx.Frame, iTrade_wxFrame, wxl.ColumnSorterMixin):
    def __init__(self, parent, id, title, port):
        wx.Frame.__init__(self, parent=None, title=title, size=(800, 320), style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        iTrade_wxFrame.__init__(self, parent=parent, name='portfolio')
        self.m_port = port
        self.m_mode = DISP_ALL
        self.m_period = PERIOD_30DAYS
        self.m_currentItem = -1

        # the menu
        self.filemenu = wx.Menu()
        self.filemenu.Append(ID_CLOSE, message('main_close'), message('main_desc_close'))

        self.dispmenu = wx.Menu()
        self.dispmenu.AppendRadioItem(ID_DISPALL, message('portfolio_dispall'), message('portfolio_desc_dispall'))
        self.dispmenu.AppendRadioItem(ID_DISPQUOTES, message('portfolio_dispquotes'), message('portfolio_desc_dispquotes'))
        self.dispmenu.AppendRadioItem(ID_DISPCASH, message('portfolio_dispcash'), message('portfolio_desc_dispcash'))
        self.dispmenu.AppendRadioItem(ID_DISPSRD, message('portfolio_dispsrd'), message('portfolio_desc_dispsrd'))
        self.dispmenu.AppendRadioItem(ID_DISPPVAL, message('portfolio_dispvalues'), message('portfolio_desc_dispvalues'))
        self.dispmenu.AppendSeparator()
        self.textmenu = wx.Menu()
        self.dispmenu.AppendSubMenu(self.textmenu, message('portfolio_text'), message('portfolio_desc_text'))
        self.textmenu.AppendRadioItem(ID_SMALL_TEXT, message('portfolio_view_small'), message('portfolio_view_desc_small'))
        self.textmenu.AppendRadioItem(ID_NORMAL_TEXT, message('portfolio_view_normal'), message('portfolio_view_desc_normal'))
        self.textmenu.AppendRadioItem(ID_BIG_TEXT, message('portfolio_view_big'), message('portfolio_view_desc_big'))

        self.opmenu = wx.Menu()
        self.opmenu.Append(ID_MODIFY, message('portfolio_opmodify'), message('portfolio_desc_opmodify'))
        self.opmenu.Append(ID_DELETE, message('portfolio_opdelete'), message('portfolio_desc_opdelete'))
        self.opmenu.Append(ID_ADD, message('portfolio_opadd'), message('portfolio_desc_opadd'))

        self.permenu = wx.Menu()
        self.permenu.AppendRadioItem(ID_30DAYS, message('portfolio_per30days'), message('portfolio_desc_per30days'))
        self.permenu.AppendRadioItem(ID_90DAYS, message('portfolio_per90days'), message('portfolio_desc_per90days'))
        self.permenu.AppendRadioItem(ID_CURRENTYEAR, message('portfolio_peryear'), message('portfolio_desc_peryear'))
        self.permenu.AppendRadioItem(ID_ALLYEARS, message('portfolio_perall'), message('portfolio_desc_perall'))

        # default checking
        self.updateMenuItems()

        # Creating the menubar
        menuBar = wx.MenuBar()

        # Adding the "<x>menu" to the MenuBar
        menuBar.Append(self.filemenu, message('portfolio_menu_file'))
        menuBar.Append(self.dispmenu, message('portfolio_menu_disp'))
        menuBar.Append(self.opmenu, message('portfolio_menu_op'))
        menuBar.Append(self.permenu, message('portfolio_menu_per'))

        # Adding the MenuBar to the Frame content
        self.SetMenuBar(menubar=menuBar)

        # create an image list
        self.m_imagelist = wx.ImageList(16, 16)
        self.idx_plus = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'plus.png')))
        self.idx_minus = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'minus.png')))
        self.idx_neutral = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'neutral.png')))
        self.idx_unknown = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'unknown.png')))

        self.sm_up = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'sm_up.png')))
        self.sm_dn = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'sm_down.png')))

        self.m_list = iTradeOperationsListCtrl(parent=self,
                                 style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_SINGLE_SEL | wx.LC_VRULES | wx.LC_HRULES)
        self.m_list.SetImageList(imageList=self.m_imagelist, which=wx.IMAGE_LIST_SMALL)

        self.m_list.SetFont(font=FontFromSize(itrade_config.operationFontSize))

        # Now that the list exists, we can initialise the other base class,
        # see wxPython/lib/mixins/listctrl.py
        wxl.ColumnSorterMixin.__init__(self, numColumns=IDC_RESERVED)

        # Toolbar
        self.m_toolbar = iTradeOperationToolbar(parent=self)

        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_LIST_ITEM_ACTIVATED(self, self.m_list.GetId(), self.OnItemActivated)
        wx.EVT_LIST_ITEM_SELECTED(self, self.m_list.GetId(), self.OnItemSelected)

        wx.EVT_COMMAND_RIGHT_CLICK(self.m_list, self.m_list.GetId(), self.OnRightClick)

        wx.EVT_RIGHT_UP(self.m_list, self.OnRightClick)
        wx.EVT_RIGHT_DOWN(self.m_list, self.OnRightDown)

        wx.EVT_MENU(self, ID_CLOSE, self.OnClose)

        wx.EVT_MENU(self, ID_DISPALL, self.OnDispAll)
        wx.EVT_MENU(self, ID_DISPQUOTES, self.OnDispQuotes)
        wx.EVT_MENU(self, ID_DISPCASH, self.OnDispCash)
        wx.EVT_MENU(self, ID_DISPSRD, self.OnDispSRD)
        wx.EVT_MENU(self, ID_DISPPVAL, self.OnDispPVal)

        wx.EVT_MENU(self, ID_SMALL_TEXT, self.OnTextSmall)
        wx.EVT_MENU(self, ID_NORMAL_TEXT, self.OnTextNormal)
        wx.EVT_MENU(self, ID_BIG_TEXT, self.OnTextBig)

        wx.EVT_MENU(self, ID_MODIFY, self.OnModify)
        wx.EVT_MENU(self, ID_DELETE, self.OnDelete)
        wx.EVT_MENU(self, ID_ADD, self.OnAdd)

        wx.EVT_MENU(self, ID_30DAYS, self.On30Days)
        wx.EVT_MENU(self, ID_90DAYS, self.On90Days)
        wx.EVT_MENU(self, ID_CURRENTYEAR, self.OnCurrentYear)
        wx.EVT_MENU(self, ID_ALLYEARS, self.OnAllYears)

        wx.EVT_WINDOW_DESTROY(self, self.OnDestroy)
        wx.EVT_CLOSE(self, self.OnCloseWindow)

        self.populate()

    # --- [ wxl.ColumnSorterMixin management ] -------------------------------------

    # Used by the wxl.ColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.m_list

    # Used by the wxl.ColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)

    # --- [ Text font size management ] -------------------------------------

    def OnChangeViewText(self):
        itrade_config.saveConfig()
        self.updateMenuItems()
        self.m_list.SetFont(font=FontFromSize(itrade_config.operationFontSize))
        self.populate()

    def OnTextSmall(self, e):
        itrade_config.operationFontSize = 1
        self.OnChangeViewText()

    def OnTextNormal(self, e):
        itrade_config.operationFontSize = 2
        self.OnChangeViewText()

    def OnTextBig(self, e):
        itrade_config.operationFontSize = 3
        self.OnChangeViewText()

    # --- [ window management ] -------------------------------------

    def OnDestroy(self, evt):
        if self.m_parent:
            self.m_parent.m_hOperation = None

    def OnCloseWindow(self, evt):
        self.saveConfig()
        self.Destroy()

    # --- [ filter management ] -------------------------------------

    def filterSRDcolumn(self):
        if self.m_mode == DISP_ALL:
            return True
        if self.m_mode == DISP_QUOTES:
            return True
        if self.m_mode == DISP_CASH:
            return False
        if self.m_mode == DISP_SRD:
            return True
        if self.m_mode == DISP_PVAL:
            return False

    def filterDisplay(self, op):
        if self.m_mode == DISP_ALL:
            # no filter at all
            return True

        if self.m_mode == DISP_QUOTES:
            # display on quotes transfers
            return op.isQuote() and (op.type() != OPERATION_LIQUIDATION)

        if self.m_mode == DISP_CASH:
            # display on quotes transfers
            return op.isCash() and (not op.isSRD() or op.type() == OPERATION_LIQUIDATION)

        if self.m_mode == DISP_SRD:
            # display on SRD operations
            return op.isSRD()

        if self.m_mode == DISP_PVAL:
            return (op.type() == OPERATION_SELL) or (op.type() == OPERATION_LIQUIDATION)

        return False

    def filterPeriod(self, op):
        if self.m_period == PERIOD_ALLYEARS:
            return True
        elif self.m_period == PERIOD_CURRENTYEAR:
            # year should be the current one
            return op.date().year == date.today().year
        elif self.m_period == PERIOD_90DAYS:
            # last 90 days
            return (date.today() - op.date()) <= timedelta(90)
        elif self.m_period == PERIOD_30DAYS:
            # last 30 days
            return (date.today() - op.date()) <= timedelta(30)
        return False

    # --- [ list population ] -------------------------------------

    def populate(self):
        self.m_list.ClearAll()
        self.itemDataMap = {}
        self.itemOpMap = {}

        # set column headers
        self.m_list.InsertColumn(IDC_DATE, message('portfolio_list_date'), wx.LIST_FORMAT_LEFT)
        self.m_list.InsertColumn(IDC_OPERATION, message('portfolio_list_operation'), wx.LIST_FORMAT_LEFT)
        self.m_list.InsertColumn(IDC_DESCRIPTION, message('portfolio_list_description'), wx.LIST_FORMAT_LEFT)
        self.m_list.InsertColumn(IDC_NUMBER, message('portfolio_list_number'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_PRU, message('UPP'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_DEBIT,message('portfolio_list_debit'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_CREDIT,message('portfolio_list_credit'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_EXPENSES,message('portfolio_list_expense'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_BALANCE,message('portfolio_list_balance'), wx.LIST_FORMAT_RIGHT)
        if self.filterSRDcolumn():
            self.m_list.InsertColumn(IDC_SRD,message('portfolio_list_srd'), wx.LIST_FORMAT_RIGHT)
        self.m_list.InsertColumn(IDC_RESERVED, '', wx.LIST_FORMAT_LEFT)

        self.set_column_widths()
        self.populate_list()

        # fix the item data
        for x, key in enumerate(self.itemDataMap):
            self.m_list.SetItemData(x, key)

        # adjust size of columns
        self.adjustColumns()

        # default selection
        if len(self.itemDataMap) > 0:
            self.m_currentItem = 0
            self.m_list.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
            self.m_list.EnsureVisible(self.m_currentItem)
        else:
            self.m_currentItem = -1

    def populate_list(self):
        x = 0
        balance = 0
        srd = 0
        for operation in self.m_port.operations().list():
            if self.filterDisplay(operation):
                # print('populate:', operation)
                sign = operation.sign()

                if sign == '+':
                    if operation.isSRD():
                        if operation.type() == OPERATION_LIQUIDATION:
                            balance = balance + operation.nv_value()
                            srd = srd + (operation.nv_value() + operation.nv_expenses())
                        else:
                            srd = srd + operation.nv_value()
                    else:
                        if self.m_mode == DISP_PVAL:
                            balance = balance + operation.nv_pvalue()
                        else:
                            balance = balance + operation.nv_value()
                elif sign == '-':
                    if operation.isSRD():
                        srd = srd - operation.nv_value()
                    else:
                        balance = balance - operation.nv_value()

                # do we really need to display this op ?
                if self.filterPeriod(operation):
                    if sign == '+':
                        idx = self.idx_plus
                    elif sign == '-':
                        idx = self.idx_minus
                    elif sign == ' ' or sign == '~':
                        idx = self.idx_neutral
                    else:
                        idx = self.idx_unknown
                    sdate = operation.datetime().strftime('%x %X')
                    self.m_list.InsertImageStringItem(x, sdate, idx)
                    self.m_list.SetStringItem(x, IDC_OPERATION, operation.operation())
                    if operation.nv_number() > 0:
                        self.m_list.SetStringItem(x, IDC_NUMBER, u'{}'.format(operation.sv_number()))
                    else:
                        self.m_list.SetStringItem(x, IDC_NUMBER, '')
                    if sign == '+':
                        self.m_list.SetStringItem(x, IDC_CREDIT, operation.sv_value())
                        vdebit = 0.0
                        vcredit = operation.nv_value()
                    elif sign == '-':
                        self.m_list.SetStringItem(x, IDC_DEBIT, operation.sv_value())
                        vcredit = 0.0
                        vdebit = operation.nv_value()
                    elif sign == '~':
                        self.m_list.SetStringItem(x, IDC_CREDIT, operation.sv_value())
                        vcredit = operation.nv_value()
                        self.m_list.SetStringItem(x, IDC_DEBIT, operation.sv_value())
                        vdebit = operation.nv_value()
                    else:
                        vcredit = 0.0
                        vdebit = 0.0
                    self.m_list.SetStringItem(x, IDC_EXPENSES, operation.sv_expenses())
                    self.m_list.SetStringItem(x, IDC_DESCRIPTION, operation.description())
                    self.m_list.SetStringItem(x, IDC_BALANCE, u'{:.2f}'.format(balance))

                    if self.filterSRDcolumn():
                        if operation.isSRD():
                            self.m_list.SetStringItem(x, IDC_SRD, u'{:.2f}'.format(srd))
                            vsrd = srd
                        else:
                            self.m_list.SetStringItem(x, IDC_SRD, '')
                            vsrd = 0.0
                        self.m_list.SetStringItem(x, IDC_RESERVED, u'{:d}'.format(operation.ref()))
                    else:
                        vsrd = 0.0
                        self.m_list.SetStringItem(x, IDC_SRD, u'{:d}'.format(operation.ref()))

                    try:
                        pr = str(u'{:.2f}'.format((vcredit + vdebit) / operation.nv_number()))
                        if pr == '0.00':
                            pr = ''
                    except ZeroDivisionError:
                        pr = ''
                    self.m_list.SetStringItem(x, IDC_PRU, pr)

                    self.itemDataMap[x] = (operation.date().strftime('%Y%m%d'),
                                           operation.operation(),
                                           operation.description(),
                                           operation.nv_number(),
                                           pr,
                                           vdebit, vcredit, operation.nv_expenses(), balance, vsrd)
                    self.itemOpMap[x] = operation.ref()

                    item = self.m_list.GetItem(x)
                    if sign == '+':
                        item.SetTextColour(wx.BLACK)
                    elif sign == '-':
                        item.SetTextColour(wx.BLUE)
                    elif sign == ' ':
                        item.SetTextColour(wx.BLACK)
                    else:
                        item.SetTextColour(wx.RED)
                    self.m_list.SetItem(item)

                    # one more item !
                    # self.m_op[x] = operation

                    x = x + 1

    def set_column_widths(self):
        # remember columns widths with just the header and no data
        self.m_hdrcolwidths = []
        for col in range(self.m_list.GetColumnCount() - 1):
            self.m_list.SetColumnWidth(col, wx.LIST_AUTOSIZE_USEHEADER)
            self.m_hdrcolwidths.append(self.m_list.GetColumnWidth(col))

    # --- [ adjust columns width ] -------------------------------------

    def adjustColumns(self):
        for col in range(self.m_list.GetColumnCount() - 1):
            self.m_list.SetColumnWidth(col, wx.LIST_AUTOSIZE)
            if self.m_list.GetColumnWidth(col) < self.m_hdrcolwidths[col]:
                self.m_list.SetColumnWidth(col, self.m_hdrcolwidths[col])
        self.m_list.resizeLastColumn(15)

    # --- [ menu ] -------------------------------------

    def updateMenuItems(self):
        # period
        if self.m_period == PERIOD_ALLYEARS:
            m = self.permenu.FindItemById(ID_ALLYEARS)
        elif self.m_period == PERIOD_CURRENTYEAR:
            m = self.permenu.FindItemById(ID_CURRENTYEAR)
        elif self.m_period == PERIOD_90DAYS:
            m = self.permenu.FindItemById(ID_90DAYS)
        elif self.m_period == PERIOD_30DAYS:
            m = self.permenu.FindItemById(ID_30DAYS)
        m.Check(True)

        # operations
        m = self.opmenu.FindItemById(ID_DELETE)
        m.Enable(self.m_currentItem >= 0)

        m = self.opmenu.FindItemById(ID_MODIFY)
        m.Enable(self.m_currentItem >= 0)

        # display
        if self.m_mode == DISP_ALL:
            m = self.dispmenu.FindItemById(ID_DISPALL)
        elif self.m_mode == DISP_QUOTES:
            m = self.dispmenu.FindItemById(ID_DISPQUOTES)
        elif self.m_mode == DISP_CASH:
            m = self.dispmenu.FindItemById(ID_DISPCASH)
        elif self.m_mode == DISP_SRD:
            m = self.dispmenu.FindItemById(ID_DISPSRD)
        elif self.m_mode == DISP_PVAL:
            m = self.dispmenu.FindItemById(ID_DISPPVAL)
        m.Check(True)

        m = self.textmenu.FindItemById(ID_SMALL_TEXT)
        m.Check(itrade_config.operationFontSize == 1)
        m = self.textmenu.FindItemById(ID_NORMAL_TEXT)
        m.Check(itrade_config.operationFontSize == 2)
        m = self.textmenu.FindItemById(ID_BIG_TEXT)
        m.Check(itrade_config.operationFontSize == 3)

    def OnClose(self, e):
        self.Close(True)

    def OnDispAll(self, e):
        self.m_mode = DISP_ALL
        self.updateMenuItems()
        self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_DISPALL, True)
        self.populate()

    def OnDispQuotes(self, e):
        self.m_mode = DISP_QUOTES
        self.updateMenuItems()
        self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_DISPQUOTES, True)
        self.populate()

    def OnDispCash(self, e):
        self.m_mode = DISP_CASH
        self.updateMenuItems()
        self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_DISPCASH, True)
        self.populate()

    def OnDispSRD(self, e):
        self.m_mode = DISP_SRD
        self.updateMenuItems()
        self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_DISPSRD, True)
        self.populate()

    def OnDispPVal(self, e):
        self.m_mode = DISP_PVAL
        self.updateMenuItems()
        self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_DISPPVAL, True)
        self.populate()

    def On30Days(self, e):
        self.m_period = PERIOD_30DAYS
        self.updateMenuItems()
        self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_30DAYS, True)
        self.populate()

    def On90Days(self, e):
        self.m_period = PERIOD_90DAYS
        self.updateMenuItems()
        self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_90DAYS, True)
        self.populate()

    def OnCurrentYear(self, e):
        self.m_period = PERIOD_CURRENTYEAR
        self.updateMenuItems()
        self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_CURRENTYEAR, True)
        self.populate()

    def OnAllYears(self, e):
        self.m_period = PERIOD_ALLYEARS
        self.updateMenuItems()
        self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_ALLYEARS, True)
        self.populate()

    def OnSize(self, event):
        w, h = self.GetClientSizeTuple()
        self.m_toolbar.SetDimensions(0, 0, w, 32)
        self.m_list.SetDimensions(0, 32, w, h-32)
        event.Skip(False)

    def getColumnText(self, index, col):
        item = self.m_list.GetItem(index, col)
        return item.GetText()

    # --- [ popup menu ] ------------------------------------------------------

    def OnRightDown(self, event):
        self.x = event.GetX()
        self.y = event.GetY()
        debug(u"x, y = {}".format(str((self.x, self.y))))
        item, flags = self.m_list.HitTest((self.x, self.y))
        if flags & wx.LIST_HITTEST_ONITEM:
            pass
        else:
            self.m_currentItem = -1
            self.updateMenuItems()
        event.Skip()

    def OnItemActivated(self, event):
        self.m_currentItem = event.m_itemIndex
        self.updateMenuItems()
        if self.m_currentItem >= 0:
            debug(u"OnItemActivated: {}".format(self.m_list.GetItemText(self.m_currentItem)))
            self.OnModify(event)

    def OnItemSelected(self, event):
        self.m_currentItem = event.m_itemIndex
        self.updateMenuItems()
        if self.m_currentItem >= 0:
            debug(u"OnItemSelected: {}, {}, {}, {}\n".format(
                            self.m_currentItem,
                            self.m_list.GetItemText(self.m_currentItem),
                            self.getColumnText(self.m_currentItem, 1),
                            self.getColumnText(self.m_currentItem, 2)))
        event.Skip()

    def OnRightClick(self, event):
        if self.m_currentItem < 0:
            inList = False
        else:
            debug(u"OnRightClick {}\n".format(self.m_list.GetItemText(self.m_currentItem)))
            inList = True

        # only do this part the first time so the events are only bound once
        if not hasattr(self, "m_popupID_Modify"):
            self.m_popupID_Modify = ID_MODIFY
            self.m_popupID_Delete = ID_DELETE
            self.m_popupID_Add = ID_ADD
            wx.EVT_MENU(self, self.m_popupID_Modify, self.OnModify)
            wx.EVT_MENU(self, self.m_popupID_Delete, self.OnDelete)
            wx.EVT_MENU(self, self.m_popupID_Add, self.OnAdd)

        # make a menu
        menu = wx.Menu()
        # add some items
        menu.Append(self.m_popupID_Modify, message('main_popup_edit'))
        menu.Enable(self.m_popupID_Modify, inList)
        menu.Append(self.m_popupID_Delete, message('main_popup_remove'))
        menu.Enable(self.m_popupID_Delete, inList)
        menu.AppendSeparator()
        menu.Append(self.m_popupID_Add, message('main_popup_add'))

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu, wx.Point(self.x, self.y))
        menu.Destroy()

    def OnModify(self, event):
        key = self.m_list.GetItemData(self.m_currentItem)
        ind = self.itemOpMap[key]
        info("OnModify currentItem=%d key=%d ind=%d", self.m_currentItem, key, ind)

        aRet = edit_iTradeOperation(win=self, op=self.m_port.getOperation(ind), opmode=OPERATION_MODIFY, currency=self.m_port.currency())
        if aRet:
            info(u'OnModify: date={} type={} name={} value={:12.2f} expenses={:12.2f} number={:d} ref={:d}'.format(str(aRet[0]), aRet[1], aRet[2], aRet[3], aRet[4], aRet[5], aRet[6]))
            self.m_port.delOperation(ind)
            self.m_port.addOperation(aRet)
            self.RebuildList()

    def OnDelete(self, event):
        key = self.m_list.GetItemData(self.m_currentItem)
        ind = self.itemOpMap[key]
        info("OnDelete currentItem=%d key=%d ind=%d", self.m_currentItem, key, ind)

        aRet = edit_iTradeOperation(win=self, op=self.m_port.getOperation(ind), opmode=OPERATION_DELETE, currency=self.m_port.currency())
        if aRet:
            info(u'OnDelete: date={} type={} name={} value={:12.2f} expenses={:12.2f} number={:d} ref={:d}'.format(str(aRet[0]), aRet[1], aRet[2], aRet[3], aRet[4], aRet[5], aRet[6]))
            self.m_port.delOperation(ind)
            self.RebuildList()

    def OnAdd(self, event):
        info("OnAdd")
        aRet = edit_iTradeOperation(win=self, op=None, opmode=OPERATION_ADD, market=self.m_port.market(), currency=self.m_port.currency())
        if aRet:
            info(u'OnAdd: date={} type={} name={} value={:12.2f} expenses={:12.2f} number={:d} ref={:d}'.format(str(aRet[0]), aRet[1], aRet[2], aRet[3], aRet[4], aRet[5], aRet[6]))
            self.m_port.addOperation(aRet)
            self.RebuildList()

    # --- [ Rebuild screen and Parent ] ---------------------------------------

    def RebuildList(self):
        self.m_port.saveOperations()
        self.populate()
        if self.m_parent:
            self.m_parent.RebuildList()

# ============================================================================
# open_iTradeOperations
# ============================================================================

def open_iTradeOperations(win, port=None):
    debug('open_iTradeOperations')
    if win and win.m_hOperation:
        # set focus
        win.m_hOperation.SetFocus()
    else:
        if not isinstance(port, Portfolio):
            port = loadPortfolio()
        frame = iTradeOperationsWindow(parent=win, id=wx.ID_ANY, title=u"{} - {}".format(message('portfolio_title'), port.name()), port=port)
        if win:
            win.m_hOperation = frame
        frame.Show()

# ============================================================================
# edit_iTradeOperation()
#
#   op      operation to edit
#   opmode  operation mode (modify,add,delete)
#   market  default market (add only)
# ============================================================================

def edit_iTradeOperation(win, op, opmode, market=None, currency='EUR'):
    with iTradeOperationDialog(win, op, opmode, market, currency) as dlg:
        if dlg.ShowModal() == wx.ID_OK:
            aRet = dlg.aRet
        else:
            aRet = None
    return aRet

# ============================================================================
# add_iTradeOperation()
#
#   win     parent window
#   quote   quote involved in the operation
#   type    type of operation : OPERATION_xxx
#
# auto-filled information :
#   operation date is current date
#
# returns True if operation has been added
# ============================================================================

def add_iTradeOperation(win, portfolio, quote, type):
    if quote:
        key = quote.key()
    else:
        key = None
    op = create_operation(operation_type=type, d=datetime.now(), m=key, value='0.0', expenses='0.0', number='0', vat=portfolio.vat(), ref=-1)
    aRet = edit_iTradeOperation(win=win, op=op, opmode=OPERATION_ADD, market=portfolio.market(), currency=portfolio.currency())
    if aRet:
        info(u'add_iTradeOperation: date={} type={} name={} value={:12.2f} expenses={:12.2f} number={:d} ref={:d}'.format(str(aRet[0]), aRet[1], aRet[2], aRet[3], aRet[4], aRet[5], aRet[6]))
        portfolio.addOperation(aRet)
        portfolio.saveOperations()
        return True
    return False

# ============================================================================
# Test me
# ============================================================================

def main():
    setLevel(logging.INFO)
    app = wx.App()
    # load configuration
    itrade_config.load_config()
    from itrade_local import gMessage
#    gMessage.setLang('us')
#    gMessage.load()
    # load extensions
    import itrade_ext
    itrade_ext.loadExtensions(itrade_config.fileExtData, itrade_config.dirExtData)
    # init modules
    initQuotesModule()
    initPortfolioModule()
    import itrade_wxportfolio
    port = itrade_wxportfolio.select_iTradePortfolio(win=None, dportfolio='default')
    if port:
        port = loadPortfolio(port.filename())
        open_iTradeOperations(win=None, port=port)
        app.MainLoop()


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
