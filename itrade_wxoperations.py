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
# 2006-01-1x    dgil  Split code from original itrade_wxportfolio.py module
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from datetime import *
import logging

# wxPython system
import itrade_wxversion
import wx
import wx.lib.mixins.listctrl as wxl
from wxPython.lib.maskededit import wxMaskedTextCtrl

# iTrade system
from itrade_logging import *
from itrade_local import message
from itrade_quotes import *
from itrade_portfolio import *

#from itrade_wxdatation import itrade_datePicker
from itrade_wxselectquote import select_iTradeQuote
import itrade_wxres
from itrade_wxmixin import iTrade_wxFrame,iTradeSelectorListCtrl
from itrade_wxutil import FontFromSize

# ============================================================================
# menu identifier
# ============================================================================

ID_SAVE = 110
ID_CLOSE = 111

ID_DISPALL = 120
ID_DISPQUOTES = 121
ID_DISPCASH = 122
ID_DISPSRD = 123
ID_DISPPVAL = 124

ID_SMALL_VIEW = 230
ID_NORMAL_VIEW = 231
ID_BIG_VIEW = 232

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

DISP_QUOTES = 1
DISP_CASH   = 2
DISP_PVAL   = 4
DISP_SRD    = 8
DISP_ALL    = 15

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
IDC_NUMBER = 3
IDC_DEBIT = 4
IDC_CREDIT = 5
IDC_EXPENSES = 6
IDC_BALANCE = 7
IDC_SRD = 8
IDC_RESERVED = 9

# ============================================================================
#
# ============================================================================

OPERATION_MODIFY = 0
OPERATION_ADD = 1
OPERATION_DELETE = 2

# ============================================================================
#
# ============================================================================

operation_ctrl = {
    OPERATION_BUY       : 'portfolio_ctrl_buy',
    OPERATION_BUY_SRD   : 'portfolio_ctrl_buy_srd',
    OPERATION_SELL      : 'portfolio_ctrl_sell',
    OPERATION_SELL_SRD  : 'portfolio_ctrl_sell_srd',
    OPERATION_CREDIT    : 'portfolio_ctrl_credit',
    OPERATION_DEBIT     : 'portfolio_ctrl_debit',
    OPERATION_FEE       : 'portfolio_ctrl_fee',
    OPERATION_INTEREST  : 'portfolio_ctrl_interest',
    OPERATION_DETACHMENT: 'portfolio_ctrl_detachment',
    OPERATION_DIVIDEND  : 'portfolio_ctrl_dividend',
    OPERATION_QUOTE     : 'portfolio_ctrl_quote',
    OPERATION_LIQUIDATION  : 'portfolio_ctrl_liquidation',
    OPERATION_REGISTER  : 'portfolio_ctrl_register'
#    OPERATION_SPLIT     : 'portfolio_ctrl_split'
}

# ============================================================================
# iTradeOperationsDialog
# ============================================================================

class iTradeOperationDialog(wx.Dialog):
    def __init__(self, parent, op, opmode):
        # context help
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)

        # pre-init
        self.opmode = opmode

        if op:
            self.m_type = op.type()
            self.m_value = op.nv_value()
            self.m_expenses = op.nv_expenses()
            self.m_number = op.nv_number()
            if op.isQuote():
                self.m_name = op.quote().key()
            else:
                self.m_name = op.name()
            self.m_date = op.date()
            self.m_ref = op.ref()
        else:
            self.m_type = OPERATION_SELL
            self.m_value = 0.0
            self.m_expenses = 0.0
            self.m_number = 0
            self.m_name = ""
            self.m_date = date.today()
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
        tt = tb + ' %s - %s %s'
        if op:
            self.tt = tt % (op.date().strftime('%x'),op.operation(),op.description())
        else:
            self.tt = tb

        # post-init
        pre.Create(parent, -1, self.tt, size=(420, 420))
        self.PostCreate(pre)

        #
        self.m_sizer = wx.BoxSizer(wx.VERTICAL)

        # separator
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.m_sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # date
        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, message('portfolio_date'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        ssdatetime = wx.DateTimeFromDMY(self.m_date.day,self.m_date.month-1,self.m_date.year)
        self.wxDateCtrl = wx.DatePickerCtrl(self, -1, ssdatetime , size = (120,-1), style = wx.DP_DROPDOWN | wx.DP_SHOWCENTURY)
        wx.EVT_DATE_CHANGED(self, self.wxDateCtrl.GetId(), self.OnDate)
        box.Add(self.wxDateCtrl, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.m_sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # separator
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.m_sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # kind of operation

        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, message('portfolio_operation'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.wxTypeCtrl = wx.ComboBox(self,-1, "", size=wx.Size(160,-1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
        box.Add(self.wxTypeCtrl, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_COMBOBOX(self,self.wxTypeCtrl.GetId(),self.OnType)

        count = 0
        for eachCtrl in operation_ctrl.items():
            #print '***',message(eachCtrl[1]),eachCtrl[0]
            self.wxTypeCtrl.Append(message(eachCtrl[1]),eachCtrl[0])
            if eachCtrl[0]==self.m_type:
                idx = count
            count = count + 1

        self.wxTypeCtrl.SetSelection(idx)

        self.m_sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # quote
        box = wx.BoxSizer(wx.HORIZONTAL)

        self.wxNameLabel = wx.StaticText(self, -1, message('portfolio_description'))
        box.Add(self.wxNameLabel, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        bmp = wx.Bitmap('res/quotes.gif')
        self.wxNameButton = wx.BitmapButton(self, -1, bmp, size=wx.Size(bmp.GetWidth()+5, bmp.GetHeight()+5))
        box.Add(self.wxNameButton, 0, wx.ALIGN_CENTRE|wx.SHAPED, 5)
        wx.EVT_BUTTON(self, self.wxNameButton.GetId(), self.OnQuote)

        self.wxNameCtrl = wx.TextCtrl(self, -1, self.m_name, size=wx.Size(240,-1), style = wx.TE_LEFT)
        wx.EVT_TEXT( self, self.wxNameCtrl.GetId(), self.OnDescChange )
        box.Add(self.wxNameCtrl, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.m_sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # value
        box = wx.BoxSizer(wx.HORIZONTAL)

        self.wxValueLabel = wx.StaticText(self, -1, message('portfolio_field_credit'))
        box.Add(self.wxValueLabel, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.wxValueCtrl = wxMaskedTextCtrl(self, -1, mask="#{9}.##", formatcodes="SF_-R")
        self.wxValueCtrl.SetFieldParameters(0, formatcodes='r<', validRequired=True)  # right-insert, require explicit cursor movement to change fields
        self.wxValueCtrl.SetFieldParameters(1, defaultValue='00')                     # don't allow blank fraction
        wx.EVT_TEXT( self, self.wxValueCtrl.GetId(), self.OnValueChange )

        box.Add(self.wxValueCtrl, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.wxValueTxt = wx.StaticText(self, -1, "€")
        box.Add(self.wxValueTxt, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.wxExpPreTxt = wx.StaticText(self, -1, '')
        box.Add(self.wxExpPreTxt, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.wxExpensesCtrl = wxMaskedTextCtrl(self, -1, mask="#{4}.##", formatcodes="SF_R")
        self.wxExpensesCtrl.SetFieldParameters(0, formatcodes='r<', validRequired=True)  # right-insert, require explicit cursor movement to change fields
        self.wxExpensesCtrl.SetFieldParameters(1, defaultValue='00')                     # don't allow blank fraction
        box.Add(self.wxExpensesCtrl, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_TEXT( self, self.wxExpensesCtrl.GetId(), self.OnExpensesChange )

        self.wxExpPostTxt = wx.StaticText(self, -1, "€ %s" % message('portfolio_post_expenses'))
        box.Add(self.wxExpPostTxt, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.m_sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # number
        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, message('portfolio_quantity'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.wxNumberCtrl = wxMaskedTextCtrl(self, -1, mask="#{9}", formatcodes='SFR')
        box.Add(self.wxNumberCtrl, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_TEXT( self, self.wxNumberCtrl.GetId(), self.OnNumberChange )

        self.m_sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # buttons
        box = wx.BoxSizer(wx.HORIZONTAL)

        # context help
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)
            box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        # OK
        btn = wx.Button(self, wx.ID_OK, tb)
        btn.SetDefault()
        btn.SetHelpText(message('ok_desc'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnValid)

        # CANCEL
        btn = wx.Button(self, wx.ID_CANCEL, message('cancel'))
        btn.SetHelpText(message('cancel_desc'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)

        self.m_sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        wx.EVT_SIZE(self, self.OnSize)

        self.SetAutoLayout(True)
        self.SetSizerAndFit(self.m_sizer)
        self.refreshPage()

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()

    def OnCancel(self,event):
        self.aRet = None
        self.EndModal(wx.ID_CANCEL)

    def OnValid(self,event):
        if self.Validate() and self.TransferDataFromWindow():
            self.aRet = (self.m_date.__str__(),self.m_type,self.m_name,self.m_value,self.m_expenses,self.m_number,self.m_ref)
            self.EndModal(wx.ID_OK)

    def refreshPage(self):
        self.wxDateCtrl.SetValue(wx.DateTimeFromDMY(self.m_date.day,self.m_date.month-1,self.m_date.year))
        self.wxValueCtrl.SetLabel('%12.2f' % self.m_value)
        self.wxExpensesCtrl.SetLabel('%6.2f' % self.m_expenses)
        self.wxNumberCtrl.SetValue('%6d' % self.m_number)
        self.wxNameCtrl.SetLabel(self.m_name)

        if isOperationTypeIncludeTaxes(self.m_type):
            self.wxExpPreTxt.SetLabel(message('portfolio_pre_expenses1'))
        else:
            self.wxExpPreTxt.SetLabel(message('portfolio_pre_expenses2'))

        sign = signOfOperationType(self.m_type)
        if sign =='+':
            self.wxValueLabel.SetLabel(message('portfolio_field_credit'))
            self.wxExpensesCtrl.Show(True)
            self.wxValueCtrl.Show(True)
            self.wxValueTxt.Show(True)
            self.wxExpPreTxt.Show(True)
            self.wxExpPostTxt.Show(True)
        elif sign == '-':
            self.wxValueLabel.SetLabel(message('portfolio_field_debit'))
            self.wxExpensesCtrl.Show(True)
            self.wxValueCtrl.Show(True)
            self.wxValueTxt.Show(True)
            self.wxExpPreTxt.Show(True)
            self.wxExpPostTxt.Show(True)
        elif sign == '~':
            self.wxValueLabel.SetLabel(message('portfolio_field_valorization'))
            self.wxValueCtrl.Show(True)
            self.wxValueTxt.Show(True)
            self.wxExpensesCtrl.Show(False)
            self.wxExpPreTxt.Show(False)
            self.wxExpPostTxt.Show(False)
        else:
            self.wxValueLabel.SetLabel(message('portfolio_field_freeofcharges'))
            self.wxExpensesCtrl.Show(False)
            self.wxValueCtrl.Show(False)
            self.wxValueTxt.Show(False)
            self.wxExpPreTxt.Show(False)
            self.wxExpPostTxt.Show(False)

        if isOperationTypeAQuote(self.m_type):
            self.wxNameLabel.SetLabel(message('portfolio_quote'))
            self.wxNameButton.Enable(True)
            self.wxNameButton.Show(True)
            self.wxNameCtrl.Enable(False)
            if isOperationTypeHasShareNumber(self.m_type):
                self.wxNumberCtrl.Enable(True)
            else:
                self.wxNumberCtrl.Enable(False)
        else:
            self.wxNameLabel.SetLabel(message('portfolio_description'))
            self.wxNameButton.Enable(False)
            self.wxNameButton.Show(False)
            self.wxNameCtrl.Enable(True)
            self.wxNumberCtrl.Enable(False)

        if self.opmode == OPERATION_DELETE:
            self.wxNumberCtrl.Enable(False)
            self.wxNameCtrl.Enable(False)
            self.wxNameButton.Enable(False)
            self.wxNumberCtrl.Enable(False)
            self.wxExpensesCtrl.Enable(False)
            self.wxValueCtrl.Enable(False)
            self.wxDateCtrl.Enable(False)
            self.wxTypeCtrl.Enable(False)

        #self.SetSizerAndFit(self.m_sizer)
        self.Layout()

    def OnDate(self, evt):
        dRet = self.wxDateCtrl.GetValue()
        if dRet:
            debug('OnDate: %s\n' % dRet)
            self.m_date = date(dRet.GetYear(),dRet.GetMonth()+1,dRet.GetDay())
            self.refreshPage()

    def OnType(self,evt):
        t = self.wxTypeCtrl.GetClientData(self.wxTypeCtrl.GetSelection())
        debug("OnType %s" % t)
        self.m_type = t
        self.refreshPage()

    def OnQuote(self,evt):
        quote = quotes.lookupKey(self.m_name)
        quote = select_iTradeQuote(self,quote,filter=True,market=None)
        if quote:
            debug('onQuote: %s - %s' % (quote.ticker(),quote.key()))
            self.m_name = quote.key()
            self.refreshPage()

    def OnValueChange(self,event):
        ctl = self.FindWindowById( event.GetId() )
        if ctl.IsValid():
            debug('new value value = %s\n' % ctl.GetValue() )
            self.m_value = float(ctl.GetValue())

    def OnNumberChange( self, event ):
        ctl = self.FindWindowById( event.GetId() )
        if ctl.IsValid():
            debug('new number value = %s\n' % ctl.GetValue() )
            self.m_number = int(ctl.GetValue())

    def OnExpensesChange(self,event):
        ctl = self.FindWindowById(event.GetId())
        if ctl.IsValid():
            debug('new expenses value = %s\n' % ctl.GetValue() )
            self.m_expenses = float(ctl.GetValue())

    def OnDescChange(self,event):
        ctl = self.FindWindowById( event.GetId() )
        debug('new value value = %s\n' % ctl.GetValue() )
        self.m_name = ctl.GetValue()

# ============================================================================
# iTradeOperationsListCtrl
# ============================================================================

class iTradeOperationsListCtrl(wx.ListCtrl, wxl.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        wxl.ListCtrlAutoWidthMixin.__init__(self)

# ============================================================================
# iTradeOperationToolbar
#
# ============================================================================

class iTradeOperationToolbar(wx.ToolBar):

    def __init__(self,parent,id):
        wx.ToolBar.__init__(self,parent,id,style = wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        self.m_parent = parent
        self._init_toolbar()

    def _init_toolbar(self):
        self._NTB2_EXIT = wx.NewId()

        self._NTB2_DISPALL = wx.NewId()
        self._NTB2_DISPQUOTES = wx.NewId()
        self._NTB2_DISPCASH = wx.NewId()
        self._NTB2_DISPPVAL = wx.NewId()
        self._NTB2_DISPSRD = wx.NewId()

        self._NTB2_ADD = wx.NewId()
        self._NTB2_MODIFY = wx.NewId()
        self._NTB2_DELETE = wx.NewId()

        self._NTB2_30DAYS = wx.NewId()
        self._NTB2_90DAYS = wx.NewId()
        self._NTB2_CURRENTYEAR = wx.NewId()
        self._NTB2_ALLYEARS = wx.NewId()

        self.SetToolBitmapSize(wx.Size(24,24))
        self.AddSimpleTool(self._NTB2_EXIT, wx.ArtProvider.GetBitmap(wx.ART_CROSS_MARK, wx.ART_TOOLBAR),
                           message('main_close'), message('main_desc_close'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))

        self.AddRadioLabelTool(self._NTB2_DISPALL,'',wx.Bitmap('res/dispall.gif'),wx.NullBitmap,message('portfolio_dispall'),message('portfolio_desc_dispall'))
        self.AddRadioLabelTool(self._NTB2_DISPQUOTES,'',wx.Bitmap('res/dispquote.gif'),wx.NullBitmap,message('portfolio_dispquotes'),message('portfolio_desc_dispquotes'))
        self.AddRadioLabelTool(self._NTB2_DISPCASH,'',wx.Bitmap('res/dispcash.gif'),wx.NullBitmap,message('portfolio_dispcash'),message('portfolio_desc_dispcash'))
        self.AddRadioLabelTool(self._NTB2_DISPPVAL,'',wx.Bitmap('res/dispvalue.gif'),wx.NullBitmap,message('portfolio_dispvalues'),message('portfolio_desc_dispvalues'))
        self.AddRadioLabelTool(self._NTB2_DISPSRD,'',wx.Bitmap('res/dispsrd.gif'),wx.NullBitmap,message('portfolio_dispsrd'),message('portfolio_desc_dispsrd'))

        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))

        self.AddSimpleTool(self._NTB2_ADD,wx.Bitmap('res/add.gif'),message('portfolio_opadd'),message('portfolio_desc_opadd'))
        self.AddSimpleTool(self._NTB2_MODIFY,wx.Bitmap('res/modify.gif'),message('portfolio_opmodify'),message('portfolio_desc_opmodify'))
        self.AddSimpleTool(self._NTB2_DELETE,wx.Bitmap('res/delete.gif'),message('portfolio_opdelete'),message('portfolio_desc_opdelete'))

        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))

        self.AddRadioLabelTool(self._NTB2_30DAYS,'',wx.Bitmap('res/filter30.gif'),wx.NullBitmap,message('portfolio_per30days'),message('portfolio_desc_per30days'))
        self.AddRadioLabelTool(self._NTB2_90DAYS,'',wx.Bitmap('res/filter90.gif'),wx.NullBitmap,message('portfolio_per90days'),message('portfolio_desc_per90days'))
        self.AddRadioLabelTool(self._NTB2_CURRENTYEAR,'',wx.Bitmap('res/filter365.gif'),wx.NullBitmap,message('portfolio_peryear'),message('portfolio_desc_peryear'))
        self.AddRadioLabelTool(self._NTB2_ALLYEARS,'',wx.Bitmap('res/nofilter.gif'),wx.NullBitmap,message('portfolio_perall'),message('portfolio_desc_perall'))

        wx.EVT_TOOL(self, self._NTB2_EXIT, self.onExit)

        wx.EVT_TOOL(self, self._NTB2_DISPALL, self.onDispAll)
        wx.EVT_TOOL(self, self._NTB2_DISPQUOTES, self.onDispQuotes)
        wx.EVT_TOOL(self, self._NTB2_DISPCASH, self.onDispCash)
        wx.EVT_TOOL(self, self._NTB2_DISPPVAL, self.onDispPVal)
        wx.EVT_TOOL(self, self._NTB2_DISPSRD, self.onDispSRD)

        wx.EVT_TOOL(self, self._NTB2_MODIFY, self.onModify)
        wx.EVT_TOOL(self, self._NTB2_DELETE, self.onDelete)
        wx.EVT_TOOL(self, self._NTB2_ADD, self.onAdd)

        wx.EVT_TOOL(self, self._NTB2_30DAYS, self.on30Days)
        wx.EVT_TOOL(self, self._NTB2_90DAYS, self.on90Days)
        wx.EVT_TOOL(self, self._NTB2_CURRENTYEAR, self.onCurrentYear)
        wx.EVT_TOOL(self, self._NTB2_ALLYEARS, self.onAllYears)

        self.Realize()

    def onDispAll(self,event):
        self.m_parent.OnDispAll(event)

    def onDispQuotes(self,event):
        self.m_parent.OnDispQuotes(event)

    def onDispCash(self,event):
        self.m_parent.OnDispCash(event)

    def onDispPVal(self,event):
        self.m_parent.OnDispPVal(event)

    def onDispSRD(self,event):
        self.m_parent.OnDispSRD(event)

    def onAdd(self,event):
        self.m_parent.OnAdd(event)

    def onModify(self,event):
        self.m_parent.OnModify(event)

    def onDelete(self,event):
        self.m_parent.OnDelete(event)

    def on30Days(self,event):
        self.m_parent.On30Days(event)

    def on90Days(self,event):
        self.m_parent.On90Days(event)

    def onCurrentYear(self,event):
        self.m_parent.OnCurrentYear(event)

    def onAllYears(self,event):
        self.m_parent.OnAllYears(event)

    def onExit(self,event):
        self.m_parent.OnClose(event)

# ============================================================================
# iTradeOperationsWindow
# ============================================================================

class iTradeOperationsWindow(wx.Frame,iTrade_wxFrame,wxl.ColumnSorterMixin):

    # window  identifier
    ID_WINDOW_TOP = 300
    ID_WINDOW_INFO = 301

    def __init__(self,parent,id,title,port):
        self.m_id = wx.NewId()
        wx.Frame.__init__(self,None,self.m_id, title, size = (800,320), style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        iTrade_wxFrame.__init__(self,parent,'portfolio')
        self.m_port = port
        self.m_mode = DISP_ALL
        self.m_period = PERIOD_30DAYS
        self.m_currentItem = -1

        # the menu
        self.filemenu = wx.Menu()
        self.filemenu.Append(ID_SAVE,message('main_save'),message('main_desc_save'))
        self.filemenu.AppendSeparator()
        self.filemenu.Append(ID_CLOSE,message('main_close'),message('main_desc_close'))

        self.dispmenu = wx.Menu()
        self.dispmenu.AppendRadioItem(ID_DISPALL,message('portfolio_dispall'),message('portfolio_desc_dispall'))
        #self.dispmenu.AppendSeparator()
        self.dispmenu.AppendRadioItem(ID_DISPQUOTES,message('portfolio_dispquotes'),message('portfolio_desc_dispquotes'))
        self.dispmenu.AppendRadioItem(ID_DISPCASH,message('portfolio_dispcash'),message('portfolio_desc_dispcash'))
        self.dispmenu.AppendRadioItem(ID_DISPPVAL,message('portfolio_dispvalues'),message('portfolio_desc_dispvalues'))
        self.dispmenu.AppendRadioItem(ID_DISPSRD,message('portfolio_dispsrd'),message('portfolio_desc_dispsrd'))
        self.dispmenu.AppendSeparator()
        self.dispmenu.AppendRadioItem(ID_SMALL_VIEW, message('portfolio_view_small'),message('portfolio_view_desc_small'))
        self.dispmenu.AppendRadioItem(ID_NORMAL_VIEW, message('portfolio_view_normal'),message('portfolio_view_desc_normal'))
        self.dispmenu.AppendRadioItem(ID_BIG_VIEW, message('portfolio_view_big'),message('portfolio_view_desc_big'))

        self.opmenu = wx.Menu()
        self.opmenu.Append(ID_MODIFY,message('portfolio_opmodify'),message('portfolio_desc_opmodify'))
        self.opmenu.Append(ID_DELETE,message('portfolio_opdelete'),message('portfolio_desc_opdelete'))
        self.opmenu.Append(ID_ADD,message('portfolio_opadd'),message('portfolio_desc_opadd'))

        self.permenu = wx.Menu()
        self.permenu.AppendRadioItem(ID_30DAYS,message('portfolio_per30days'),message('portfolio_desc_per30days'))
        self.permenu.AppendRadioItem(ID_90DAYS,message('portfolio_per90days'),message('portfolio_desc_per90days'))
        self.permenu.AppendRadioItem(ID_CURRENTYEAR,message('portfolio_peryear'),message('portfolio_desc_peryear'))
        self.permenu.AppendRadioItem(ID_ALLYEARS,message('portfolio_perall'),message('portfolio_desc_perall'))

        # default checking
        self.updateMenuItems()

        # Creating the menubar
        menuBar = wx.MenuBar()

        # Adding the "<x>menu" to the MenuBar
        menuBar.Append(self.filemenu,message('portfolio_menu_file'))
        menuBar.Append(self.dispmenu,message('portfolio_menu_disp'))
        menuBar.Append(self.opmenu,message('portfolio_menu_op'))
        menuBar.Append(self.permenu,message('portfolio_menu_per'))

        # Adding the MenuBar to the Frame content
        self.SetMenuBar(menuBar)

        # create an image list
        self.m_imagelist = wx.ImageList(16,16)
        self.idx_plus = self.m_imagelist.Add(wx.Bitmap('res/plus.gif'))
        self.idx_minus = self.m_imagelist.Add(wx.Bitmap('res/minus.gif'))
        self.idx_neutral = self.m_imagelist.Add(wx.Bitmap('res/neutral.gif'))
        self.idx_unknown = self.m_imagelist.Add(wx.Bitmap('res/unknown.gif'))

        self.sm_up = self.m_imagelist.Add(wx.Bitmap('res/sm_up.gif'))
        self.sm_dn = self.m_imagelist.Add(wx.Bitmap('res/sm_down.gif'))

        #
        tID = wx.NewId()

        self.m_list = iTradeOperationsListCtrl(self, tID,
                                 style = wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_SINGLE_SEL | wx.LC_VRULES | wx.LC_HRULES)
        self.m_list.SetImageList(self.m_imagelist, wx.IMAGE_LIST_SMALL)

        self.m_list.SetFont(FontFromSize(itrade_config.operationFontSize))

        # Now that the list exists we can init the other base class,
        # see wxPython/lib/mixins/listctrl.py
        wxl.ColumnSorterMixin.__init__(self, IDC_RESERVED)

        # Toolbar
        self.m_toolbar = iTradeOperationToolbar(self, wx.NewId())

        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_LIST_ITEM_ACTIVATED(self, tID, self.OnItemActivated)
        wx.EVT_LIST_ITEM_SELECTED(self, tID, self.OnItemSelected)

        wx.EVT_COMMAND_RIGHT_CLICK(self.m_list, tID, self.OnRightClick)

        wx.EVT_RIGHT_UP(self.m_list, self.OnRightClick)
        wx.EVT_RIGHT_DOWN(self.m_list, self.OnRightDown)

        wx.EVT_MENU(self, ID_SAVE, self.OnSave)
        wx.EVT_MENU(self, ID_CLOSE, self.OnClose)

        wx.EVT_MENU(self, ID_DISPALL, self.OnDispAll)
        wx.EVT_MENU(self, ID_DISPQUOTES, self.OnDispQuotes)
        wx.EVT_MENU(self, ID_DISPCASH, self.OnDispCash)
        wx.EVT_MENU(self, ID_DISPPVAL, self.OnDispPVal)
        wx.EVT_MENU(self, ID_DISPSRD, self.OnDispSRD)

        wx.EVT_MENU(self, ID_SMALL_VIEW, self.OnViewSmall)
        wx.EVT_MENU(self, ID_NORMAL_VIEW, self.OnViewNormal)
        wx.EVT_MENU(self, ID_BIG_VIEW, self.OnViewBig)

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
        self.setDirty()
        self.updateMenuItems()
        self.m_list.SetFont(FontFromSize(itrade_config.operationFontSize))
        for i in range(0,IDC_RESERVED):
            self.m_list.SetColumnWidth(i, wx.LIST_AUTOSIZE)

    def OnViewSmall(self,e):
        itrade_config.operationFontSize = 1
        self.OnChangeViewText()

    def OnViewNormal(self,e):
        itrade_config.operationFontSize = 2
        self.OnChangeViewText()

    def OnViewBig(self,e):
        itrade_config.operationFontSize = 3
        self.OnChangeViewText()

    # --- [ window management ] -------------------------------------

    def OnDestroy(self, evt):
        if self.m_parent:
            self.m_parent.m_hOperation = None

    def OnCloseWindow(self, evt):
        if self.manageDirty(message('main_save_operation_data'),fnt='close'):
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

    def filterDisplay(self,op):
        if self.m_mode == DISP_ALL:
            # no filter at all
            return True

        if self.m_mode == DISP_QUOTES:
            # display on quotes transfers
            return op.isQuote() and (op.type()!=OPERATION_LIQUIDATION)

        if self.m_mode == DISP_CASH:
            # display on quotes transfers
            return op.isCash() and (not op.isSRD() or op.type()==OPERATION_LIQUIDATION)

        if self.m_mode == DISP_SRD:
            # display on SRD operations
            return op.isSRD()

        if self.m_mode == DISP_PVAL:
            return (op.type() == OPERATION_SELL) or (op.type()==OPERATION_LIQUIDATION)

        return False

    def filterPeriod(self,op):
        if self.m_period == PERIOD_ALLYEARS:
            return True
        elif self.m_period == PERIOD_CURRENTYEAR:
            # year should be the current one
            return op.date().year==date.today().year
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
        self.m_list.InsertColumn(IDC_DATE, message('portfolio_list_date'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_OPERATION, message('portfolio_list_operation'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE_USEHEADER)
        self.m_list.InsertColumn(IDC_DESCRIPTION, message('portfolio_list_description'), wx.LIST_FORMAT_LEFT, 100)
        self.m_list.InsertColumn(IDC_NUMBER, message('portfolio_list_number'), wx.LIST_FORMAT_RIGHT, 55)
        self.m_list.InsertColumn(IDC_DEBIT,message('portfolio_list_debit'), wx.LIST_FORMAT_RIGHT, 75)
        self.m_list.InsertColumn(IDC_CREDIT,message('portfolio_list_credit'), wx.LIST_FORMAT_RIGHT, 75)
        self.m_list.InsertColumn(IDC_EXPENSES,message('portfolio_list_expense'), wx.LIST_FORMAT_RIGHT, 75)
        self.m_list.InsertColumn(IDC_BALANCE,message('portfolio_list_balance'), wx.LIST_FORMAT_RIGHT, 75)
        if self.filterSRDcolumn():
            self.m_list.InsertColumn(IDC_SRD,message('portfolio_list_srd'), wx.LIST_FORMAT_RIGHT, 75)
        self.m_list.InsertColumn(IDC_RESERVED, '', wx.LIST_FORMAT_LEFT, 1)

        # populate the list
        x = 0
        balance = 0
        srd = 0
        for eachOp in self.m_port.operations().list():
            if self.filterDisplay(eachOp):
                #print 'populate:',eachOp
                sign = eachOp.sign()

                if sign=='+':
                    if eachOp.isSRD():
                        if eachOp.type()==OPERATION_LIQUIDATION:
                            balance = balance + eachOp.nv_value()
                            srd = srd + ( eachOp.nv_value() + eachOp.nv_expenses() )
                        else:
                            srd = srd - eachOp.nv_value()
                    else:
                        if self.m_mode == DISP_PVAL:
                            balance = balance + eachOp.nv_pvalue()
                        else:
                            balance = balance + eachOp.nv_value()
                elif sign=='-':
                    if eachOp.isSRD():
                        srd = srd + eachOp.nv_value()
                    else:
                        balance = balance - eachOp.nv_value()

                # do we really need to display this op ?
                if self.filterPeriod(eachOp):
                    if sign=='+':
                        idx = self.idx_plus
                    elif sign=='-':
                        idx = self.idx_minus
                    elif sign==' ' or sign=='~':
                        idx = self.idx_neutral
                    else:
                        idx = self.idx_unknown
                    sdate = eachOp.date().strftime('%x')
                    self.m_list.InsertImageStringItem(x, sdate, idx)
                    self.m_list.SetStringItem(x,IDC_OPERATION,eachOp.operation())
                    if eachOp.nv_number()>0:
                        self.m_list.SetStringItem(x,IDC_NUMBER,'%s' % eachOp.sv_number())
                    else:
                        self.m_list.SetStringItem(x,IDC_NUMBER,'')
                    if sign=='+':
                        self.m_list.SetStringItem(x,IDC_CREDIT,eachOp.sv_value())
                        vdebit = 0.0
                        vcredit = eachOp.nv_value()
                    elif sign=='-':
                        self.m_list.SetStringItem(x,IDC_DEBIT,'- %s' % eachOp.sv_value())
                        vcredit = 0.0
                        vdebit = eachOp.nv_value()
                    elif sign=='~':
                        self.m_list.SetStringItem(x,IDC_CREDIT,eachOp.sv_value())
                        vcredit = eachOp.nv_value()
                        self.m_list.SetStringItem(x,IDC_DEBIT,'- %s' % eachOp.sv_value())
                        vdebit = eachOp.nv_value()
                    else:
                        vcredit = 0.0
                        vdebit = 0.0
                    self.m_list.SetStringItem(x,IDC_EXPENSES,eachOp.sv_expenses())
                    self.m_list.SetStringItem(x,IDC_DESCRIPTION,eachOp.description())
                    self.m_list.SetStringItem(x,IDC_BALANCE,'%.2f' % balance)

                    if self.filterSRDcolumn():
                        if eachOp.isSRD():
                            self.m_list.SetStringItem(x,IDC_SRD,'%.2f' % srd)
                            vsrd = srd
                        else:
                            self.m_list.SetStringItem(x,IDC_SRD,'')
                            vsrd = 0.0
                    else:
                        vsrd = 0.0

                    self.m_list.SetStringItem(x,IDC_RESERVED,'%d' % eachOp.ref())
                    self.itemDataMap[x] = (sdate,eachOp.operation(),eachOp.description(),eachOp.nv_number(),vdebit,vcredit,eachOp.nv_expenses(),balance,vsrd)
                    self.itemOpMap[x] = eachOp.ref()

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
                    #self.m_op[x] = eachOp

                    x = x + 1

        # fix the item data
        items = self.itemDataMap.items()
        for x in range(len(items)):
            key, data = items[x]
            self.m_list.SetItemData(x, key)

        # adjust size of column
        self.m_list.SetColumnWidth(IDC_DATE, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_DESCRIPTION, wx.LIST_AUTOSIZE)

        # default selection
        self.m_currentItem = 0
        self.m_list.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

    # --- [ menu ] -------------------------------------

    def updateMenuItems(self):
        # period
        m = self.permenu.FindItemById(ID_30DAYS)
        m.Check(self.m_period == PERIOD_30DAYS)
        m = self.permenu.FindItemById(ID_90DAYS)
        m.Check(self.m_period == PERIOD_90DAYS)
        m = self.permenu.FindItemById(ID_CURRENTYEAR)
        m.Check(self.m_period == PERIOD_CURRENTYEAR)
        m = self.permenu.FindItemById(ID_ALLYEARS)
        m.Check(self.m_period == PERIOD_ALLYEARS)

        # operations
        m = self.opmenu.FindItemById(ID_DELETE)
        m.Enable(self.m_currentItem>=0)

        m = self.opmenu.FindItemById(ID_MODIFY)
        m.Enable(self.m_currentItem>=0)

        # display
        m = self.dispmenu.FindItemById(ID_DISPALL)
        m.Check(self.m_mode == DISP_ALL)
        m = self.dispmenu.FindItemById(ID_DISPQUOTES)
        m.Check(self.m_mode == DISP_QUOTES)
        m = self.dispmenu.FindItemById(ID_DISPCASH)
        m.Check(self.m_mode == DISP_CASH)
        m = self.dispmenu.FindItemById(ID_DISPSRD)
        m.Check(self.m_mode == DISP_SRD)
        m = self.dispmenu.FindItemById(ID_DISPPVAL)
        m.Check(self.m_mode == DISP_PVAL)

        m = self.dispmenu.FindItemById(ID_SMALL_VIEW)
        m.Check(itrade_config.operationFontSize==1)
        m = self.dispmenu.FindItemById(ID_NORMAL_VIEW)
        m.Check(itrade_config.operationFontSize==2)
        m = self.dispmenu.FindItemById(ID_BIG_VIEW)
        m.Check(itrade_config.operationFontSize==3)


    def OnSave(self,e):
        self.m_port.saveOperations()
        self.saveConfig()
        self.clearDirty()

    def OnClose(self,e):
        if self.manageDirty(message('main_save_operation_data'),fnt='close'):
            self.Close(True)

    def OnDispAll(self,e):
        self.m_mode = DISP_ALL
        self.populate()
        self.updateMenuItems()
        self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_DISPALL,True)

    def OnDispQuotes(self,e):
        self.m_mode = DISP_QUOTES
        self.populate()
        self.updateMenuItems()
        self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_DISPQUOTES,True)

    def OnDispCash(self,e):
        self.m_mode = DISP_CASH
        self.populate()
        self.updateMenuItems()
        self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_DISPCASH,True)

    def OnDispSRD(self,e):
        self.m_mode = DISP_SRD
        self.populate()
        self.updateMenuItems()
        self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_DISPSRD,True)

    def OnDispPVal(self,e):
        self.m_mode = DISP_PVAL
        self.populate()
        self.updateMenuItems()
        self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_DISPPVAL,True)

    def On30Days(self,e):
        self.m_period = PERIOD_30DAYS
        self.populate()
        self.updateMenuItems()
        self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_30DAYS,True)

    def On90Days(self,e):
        self.m_period = PERIOD_90DAYS
        self.populate()
        self.updateMenuItems()
        self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_90DAYS,True)

    def OnCurrentYear(self,e):
        self.m_period = PERIOD_CURRENTYEAR
        self.populate()
        self.updateMenuItems()
        self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_CURRENTYEAR,True)

    def OnAllYears(self,e):
        self.m_period = PERIOD_ALLYEARS
        self.populate()
        self.updateMenuItems()
        self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_ALLYEARS,True)

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.m_toolbar.SetDimensions(0, 0, w, 32)
        self.m_list.SetDimensions(0, 32, w, h-32)
        event.Skip(False)

    def getColumnText(self, index, col):
        item = self.m_list.GetItem(index, col)
        return item.GetText()

    # --- [ popup menu ] -------------------------------------

    def OnRightDown(self, event):
        self.x = event.GetX()
        self.y = event.GetY()
        debug("x, y = %s" % str((self.x, self.y)))
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
        if self.m_currentItem>=0:
            debug("OnItemActivated: %s" % self.m_list.GetItemText(self.m_currentItem))
            self.OnModify(event)

    def OnItemSelected(self, event):
        self.m_currentItem = event.m_itemIndex
        self.updateMenuItems()
        if self.m_currentItem>=0:
            debug("OnItemSelected: %s, %s, %s, %s\n" %
                           (self.m_currentItem,
                            self.m_list.GetItemText(self.m_currentItem),
                            self.getColumnText(self.m_currentItem, 1),
                            self.getColumnText(self.m_currentItem, 2)))
        event.Skip()

    def OnRightClick(self, event):
        if self.m_currentItem<0:
            inList = False
        else:
            debug("OnRightClick %s\n" % self.m_list.GetItemText(self.m_currentItem))
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
        menu.Enable(self.m_popupID_Modify,inList)
        menu.Append(self.m_popupID_Delete, message('main_popup_delete'))
        menu.Enable(self.m_popupID_Delete,inList)
        menu.AppendSeparator()
        menu.Append(self.m_popupID_Add, message('main_popup_add'))

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu, wx.Point(self.x, self.y))
        menu.Destroy()

    def OnModify(self, event):
        key = self.m_list.GetItemData(self.m_currentItem)
        ind = self.itemOpMap[key]
        info("OnModify currentItem=%d key=%d ind=%d",self.m_currentItem,key,ind)

        aRet = edit_iTradeOperation(self,self.m_port.getOperation(ind),OPERATION_MODIFY)
        if aRet:
            info('OnModify: date=%s type=%s name=%s value=%12.2f expenses=%12.2f number=%d ref=%d' %(aRet[0],aRet[1],aRet[2],aRet[3],aRet[4],aRet[5],aRet[6]))
            self.m_port.delOperation(ind)
            self.m_port.addOperation(aRet)
            self.setDirty()
            self.populate()
            if self.m_parent:
                self.m_parent.RebuildList()

    def OnDelete(self, event):
        key = self.m_list.GetItemData(self.m_currentItem)
        ind = self.itemOpMap[key]
        info("OnDelete currentItem=%d key=%d ind=%d",self.m_currentItem,key,ind)

        aRet = edit_iTradeOperation(self,self.m_port.getOperation(ind),OPERATION_DELETE)
        if aRet:
            info('OnDelete: date=%s type=%s name=%s value=%12.2f expenses=%12.2f number=%d ref=%d' %(aRet[0],aRet[1],aRet[2],aRet[3],aRet[4],aRet[5],aRet[6]))
            self.m_port.delOperation(ind)
            self.setDirty()
            self.populate()
            if self.m_parent:
                self.m_parent.RebuildList()

    def OnAdd(self, event):
        info("OnAdd")
        aRet = edit_iTradeOperation(self,None,OPERATION_ADD)
        if aRet:
            info('OnAdd: date=%s type=%s name=%s value=%12.2f expenses=%12.2f number=%d ref=%d' %(aRet[0],aRet[1],aRet[2],aRet[3],aRet[4],aRet[5],aRet[6]))
            self.m_port.addOperation(aRet)
            self.setDirty()
            self.populate()
            if self.m_parent:
                self.m_parent.RebuildList()

# ============================================================================
# open_iTradeOperations
# ============================================================================

def open_iTradeOperations(win,port=None):
    debug('open_iTradeOperations')
    if win and win.m_hOperation:
        # set focus
        win.m_hOperation.SetFocus()
    else:
        if not isinstance(port,Portfolio):
            port = loadPortfolio()
        frame = iTradeOperationsWindow(win, -1, "%s - %s" %(message('portfolio_title'),port.name()),port)
        if win:
            win.m_hOperation = frame
        frame.Show()

# ============================================================================
# edit_iTradeOperation()
#
#   op      operation to edit
#   opmode  operation mode (modify,add,delete)
# ============================================================================

def edit_iTradeOperation(win,op,opmode):
    dlg = iTradeOperationDialog(win,op,opmode)
    if dlg.ShowModal()==wx.ID_OK:
        aRet = dlg.aRet
    else:
        aRet = None
    dlg.Destroy()
    return aRet

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    app = wx.PySimpleApp()

    from itrade_local import *
    setLang('us')
    gMessage.load()

    import itrade_wxportfolio

    port = itrade_wxportfolio.select_iTradePortfolio(None,'default','select')
    if port:
        port = loadPortfolio(port.filename())
        open_iTradeOperations(None,port)
        app.MainLoop()

# ============================================================================
# That's all folks !
# ============================================================================
