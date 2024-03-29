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
from __future__ import absolute_import
import logging

# iTrade system
import itrade_config

# wxPython system
if not itrade_config.nowxversion:
    import itrade_wxversion
import wx
from wx.lib import masked
# import sized_controls from wx.lib for wxPython version >= 2.8.8.0 (from wxaddons otherwise)
import wx.lib.sized_controls as sc
import wx.lib.newevent

# iTrade system
from itrade_logging import setLevel
from itrade_local import message,getGroupChar,getDecimalChar
from itrade_currency import list_of_currencies, currencies

# iTrade wxPython system
from itrade_wxutil import iTradeSizedDialog

# ============================================================================
# Creates a new Event class and a EVT binder function
# ============================================================================

UpdateConvertEvent, EVT_UPDATE_CONVERT = wx.lib.newevent.NewEvent()


class iTradeConverterDialog(iTradeSizedDialog):
    def __init__(self, parent, curSelected=(0, 1), *args, **kwargs):
        iTradeSizedDialog.__init__(self, parent=parent, title=message('converter_title'),
                                   size=(420, 420), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, *args, **kwargs)
        # container
        container = self.GetContentsPane()
        container.SetSizerType("vertical")

        # resizable pane
        pane = sc.SizedPanel(container, wx.ID_ANY)
        pane.SetSizerType("form")
        pane.SetSizerProps(expand=True)

        # Row 1 : Org Currency Value
        self.wxOrgVal = masked.Ctrl(pane, integerWidth=9, fractionWidth=2, controlType=masked.controlTypes.NUMBER, allowNegative=False, groupDigits=True, groupChar=getGroupChar(), decimalChar=getDecimalChar(), selectOnEntry=True )
        self.wxOrgVal.SetValue(1)
        masked.EVT_NUM(self, self.wxOrgVal.GetId(), self.OnValueChange)

        self.wxOrgCur = wx.ComboBox(pane, wx.ID_ANY, "", size=wx.Size(80,-1), style=wx.CB_DROPDOWN|wx.CB_READONLY)

        list = list_of_currencies()
        (curFrom, curTo) = curSelected

        for c in list:
            self.wxOrgCur.Append(c,c)

        self.wxOrgCur.SetSelection(n=curFrom)
        self.m_orgcur = list[curFrom]
        wx.EVT_COMBOBOX(self, self.wxOrgCur.GetId(), self.OnOrgCurrency)

        # Row 2 : Dest Currency Value
        self.wxDestVal = wx.StaticText(pane, wx.ID_ANY, "", size=(100, -1), style=wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE)
        self.wxDestVal.SetLabel(label='')
        self.wxDestVal.SetSizerProps(valign='center')
        self.wxDestCur = wx.ComboBox(pane, wx.ID_ANY, "", size=wx.Size(80, -1), style=wx.CB_DROPDOWN|wx.CB_READONLY)

        for c in list:
            self.wxDestCur.Append(c, c)

        self.wxDestCur.SetSelection(n=curTo)
        self.m_destcur = list[curTo]
        wx.EVT_COMBOBOX(self, self.wxDestCur.GetId(), self.OnDestCurrency)

        # Last Row : OK and Cancel
        btnpane = sc.SizedPanel(parent=container, id=wx.ID_ANY)
        btnpane.SetSizerType("horizontal")
        btnpane.SetSizerProps(expand=True)

        # context help
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)

        # CLOSE
        btn = wx.Button(btnpane, wx.ID_CANCEL, message('close'))
        btn.SetHelpText(text=message('close_desc'))

        # a little trick to make sure that you can't resize the dialog to
        # less screen space than the controls need
        self.Fit()
        self.SetMinSize(minSize=self.GetSize())

        EVT_UPDATE_CONVERT(self, self.OnUpdateConvert)
        self.convertValue()

    def OnUpdateConvert(self, event):
        # can be long ...
        wx.SetCursor(wx.HOURGLASS_CURSOR)

        currencies.update_rate(self.m_destcur, self.m_orgcur)

        # get the value and convert
        o = self.wxOrgVal.GetValue()
        d = currencies.convert(curTo=self.m_destcur, curFrom=self.m_orgcur, Value=o)
        self.wxDestVal.SetLabel(label=u'{:.3f}'.format(d))

        # should be enough !
        wx.SetCursor(wx.STANDARD_CURSOR)

    def convertValue(self):
        evt = UpdateConvertEvent()
        wx.PostEvent(self, evt)

    def OnOrgCurrency(self, event):
        self.m_orgcur = self.wxOrgCur.GetClientData(self.wxOrgCur.GetSelection())
        # print('$$$ org curr', self.m_orgcur)
        self.convertValue()

    def OnDestCurrency(self, event):
        self.m_destcur = self.wxDestCur.GetClientData(self.wxDestCur.GetSelection())
        # print('$$$ dest curr', self.m_destcur)
        self.convertValue()

    def OnValueChange(self, event):
        # print('$$$ OnValueChange')
        self.convertValue()

# ============================================================================
# open_iTradeConverter
#
#   win     parent window
# ============================================================================

def open_iTradeConverter(win, curSelected=(0, 1)):
    dlg = iTradeConverterDialog(win, curSelected)
    dlg.CentreOnParent()
    dlg.ShowModal()
    dlg.Destroy()

# ============================================================================
# Test me
# ============================================================================

def main():
    setLevel(logging.INFO)
    app = wx.App()
    # load configuration
    import itrade_config
    itrade_config.load_config()
    from itrade_local import gMessage
    gMessage.setLang('us')
    gMessage.load()
    open_iTradeConverter(None)


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
