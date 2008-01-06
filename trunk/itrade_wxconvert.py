#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxconvert.py
#
# Description: wxPython currency converter
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
# 2008-01-06    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system

# wxPython system
import itrade_wxversion
import wx
from wx.lib import masked
import wxaddons.sized_controls as sc

# iTrade system
from itrade_logging import *
from itrade_local import message,getGroupChar,getDecimalChar
from itrade_config import *
from itrade_currency import list_of_currencies

# iTrade wxPython system
from itrade_wxutil import iTradeSizedDialog

# ============================================================================
# iTradeConverterDialog
# ============================================================================

class iTradeConverterDialog(iTradeSizedDialog):

    def __init__(self, parent):

        iTradeSizedDialog.__init__(self,parent,-1,message('converter_title'),size=(420, 420),style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        # container
        container = self.GetContentsPane()
        container.SetSizerType("vertical")

        # resizable pane
        pane = sc.SizedPanel(container, -1)
        pane.SetSizerType("form")
        pane.SetSizerProps(expand=True)

        # Row 1 : Org Currency Value
        self.wxOrgVal = masked.Ctrl(pane, integerWidth=9, fractionWidth=2, controlType=masked.controlTypes.NUMBER, allowNegative = False, groupDigits = True, groupChar=getGroupChar(), decimalChar=getDecimalChar(), selectOnEntry=True )
        self.wxOrgVal.SetValue(1)
        self.wxOrgCur = wx.ComboBox(pane,-1, "", size=wx.Size(80,-1), style=wx.CB_DROPDOWN|wx.CB_READONLY)

        for c in list_of_currencies():
            self.wxOrgCur.Append(c,c)

        self.wxOrgCur.SetSelection(0)
        wx.EVT_COMBOBOX(self,self.wxOrgCur.GetId(),self.OnOrgCurrency)

        # Row 2 : Dest Currency Value
        self.wxDestVal = masked.Ctrl(pane, integerWidth=9, fractionWidth=2, controlType=masked.controlTypes.NUMBER, allowNegative = False, groupDigits = True, groupChar=getGroupChar(), decimalChar=getDecimalChar(), selectOnEntry=True )
        self.wxDestVal.SetValue(1)
        self.wxDestCur = wx.ComboBox(pane,-1, "", size=wx.Size(80,-1), style=wx.CB_DROPDOWN|wx.CB_READONLY)

        for c in list_of_currencies():
            self.wxDestCur.Append(c,c)

        self.wxDestCur.SetSelection(1)
        wx.EVT_COMBOBOX(self,self.wxDestCur.GetId(),self.OnDestCurrency)

        # Last Row : OK and Cancel
        btnpane = sc.SizedPanel(container, -1)
        btnpane.SetSizerType("horizontal")
        btnpane.SetSizerProps(expand=True)

        # context help
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)

        # CLOSE
        btn = wx.Button(btnpane, wx.ID_CANCEL, message('close'))
        btn.SetHelpText(message('close_desc'))

        # a little trick to make sure that you can't resize the dialog to
        # less screen space than the controls need
        self.Fit()
        self.SetMinSize(self.GetSize())

    def OnOrgCurrency(self,event):
        pass

    def OnDestCurrency(self,event):
        pass

# ============================================================================
# open_iTradeConverter
#
#   win     parent window
# ============================================================================

def open_iTradeConverter(win):
    dlg = iTradeConverterDialog(win)
    dlg.ShowModal()
    dlg.Destroy()

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    app = wx.PySimpleApp()

    # load configuration
    import itrade_config
    itrade_config.loadConfig()

    from itrade_local import *
    setLang('us')
    gMessage.load()

    open_iTradeConverter(None)

# ============================================================================
# That's all folks !
# ============================================================================
