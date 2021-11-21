#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxdatation.py
#
# Description: wxPython portfolio screens (operations, ...)
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
# 2005-08-2x    dgil  Wrote it from scratch
#
# DEPRECATED
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from datetime import date
import logging

# wxPython system
import wx
import wx.calendar as wxcal

# iTrade system
from itrade_logging import setLevel, debug
from itrade_local import message

# ============================================================================
# iTradeDatePicker
# ============================================================================

class iTradeDatePicker(wx.Dialog):
    def __init__(self, parent, title, ddate=None):
        wx.Dialog.__init__(self, parent=parent, id=wx.ID_ANY, title=title, size=(420, 420))
        self.dRet = ddate

        # calendar
        sizer = wx.BoxSizer(wx.VERTICAL)
        box = wx.BoxSizer(wx.HORIZONTAL)

        if ddate is None:
            dd = wx.DateTime_Now()
            debug('iTradeDatePicker() today date = %s' % dd.__str__())
        else:
            debug('iTradeDatePicker() default date = %d %d %d' % (ddate.day,ddate.month,ddate.year))
            dd = wx.DateTimeFromDMY(ddate.day,ddate.month-1,ddate.year)
            debug('iTradeDatePicker() default date = %s' % dd.__str__())

        self.cal = wxcal.CalendarCtrl(self, -1, dd, pos = (25,50),
                             style = wxcal.CAL_SHOW_HOLIDAYS
                             | wxcal.CAL_MONDAY_FIRST
                             | wxcal.CAL_SEQUENTIAL_MONTH_SELECTION
                             )

        box.Add(self.cal, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # buttons
        box = wx.BoxSizer(wx.HORIZONTAL)
        btn = wx.Button(self, wx.ID_OK, message('valid'))
        btn.SetDefault()
        btn.SetHelpText(message('valid_desc'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, btn.GetId(), self.OnValid)

        btn = wx.Button(self, wx.ID_CANCEL, message('cancel'))
        btn.SetHelpText(message('cancel_desc'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, btn.GetId(), self.OnCancel)

        sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        wx.EVT_SIZE(self, self.OnSize)

        self.SetAutoLayout(True)
        self.SetSizerAndFit(sizer)

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()

    def OnValid(self, event):
        if self.Validate() and self.TransferDataFromWindow():
            wxD = self.cal.GetDate()
            self.dRet = date(wxD.GetYear(),wxD.GetMonth()+1,wxD.GetDay())
            self.EndModal(wx.ID_OK)

    def OnCancel(self,event):
        self.dRet = None
        self.EndModal(wx.ID_CANCEL)

# ============================================================================
# itrade_datePicker()
#
#   op      operation to edit
#   opmode  operation mode (modify,add,delete)
# ============================================================================

def itrade_datePicker(win,title,ddate):
    dlg = iTradeDatePicker(win,title,ddate)
    dlg.ShowModal()
    dRet = dlg.dRet
    dlg.Destroy()
    return dRet

# ============================================================================
# Test me
# ============================================================================

def main():
    setLevel(logging.INFO)
    app = wx.App(False)
    print(itrade_datePicker(None, "Datepicker", date.today()))


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
