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
# 2005-08-2x    dgil  Wrote it from scratch
#
# DEPRECATED
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging

# wxPython system
import itrade_wxversion
from wxPython.wx import *
from wxPython.calendar import *

# iTrade system
from itrade_logging import *
from itrade_datation import *
from itrade_local import message
#import itrade_wxres

# ============================================================================
# iTradeDatePicker
# ============================================================================

class iTradeDatePicker(wxDialog):
    def __init__(self, parent, title, ddate=None):
        wxDialog.__init__(self, parent, -1, title, size=(420, 420))
        self.dRet = ddate

        # calendar
        sizer = wxBoxSizer(wxVERTICAL)
        box = wxBoxSizer(wxHORIZONTAL)

        if ddate==None:
            dd = wxDateTime_Now()
            debug('iTradeDatePicker() today date = %s' % dd.__str__())
        else:
            debug('iTradeDatePicker() default date = %d %d %d' % (ddate.day,ddate.month,ddate.year))
            dd = wxDateTimeFromDMY(ddate.day,ddate.month-1,ddate.year)
            debug('iTradeDatePicker() default date = %s' % dd.__str__())

        self.cal = wxCalendarCtrl(self, -1, dd, pos = (25,50),
                             style = wxCAL_SHOW_HOLIDAYS
                             | wxCAL_MONDAY_FIRST
                             | wxCAL_SEQUENTIAL_MONTH_SELECTION
                             )

        box.Add(self.cal, 1, wxALIGN_CENTRE|wxALL, 5)

        sizer.AddSizer(box, 0, wxGROW|wxALIGN_CENTER_VERTICAL|wxALL, 5)

        # buttons
        box = wxBoxSizer(wxHORIZONTAL)
        btn = wxButton(self, wxID_OK, message('ok'))
        btn.SetDefault()
        btn.SetHelpText(message('ok_desc'))
        box.Add(btn, 0, wxALIGN_CENTRE|wxALL, 5)
        EVT_BUTTON(self, btn.GetId(), self.OnValid)

        btn = wxButton(self, wxID_CANCEL, message('cancel'))
        btn.SetHelpText(message('cancel_desc'))
        box.Add(btn, 0, wxALIGN_CENTRE|wxALL, 5)
        EVT_BUTTON(self, btn.GetId(), self.OnCancel)

        sizer.AddSizer(box, 0, wxALIGN_CENTER_VERTICAL|wxALL, 5)

        EVT_SIZE(self, self.OnSize)

        self.SetAutoLayout(True)
        self.SetSizerAndFit(sizer)

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()

    def OnValid(self, event):
        if self.Validate() and self.TransferDataFromWindow():
            wxD = self.cal.GetDate()
            self.dRet = date(wxD.GetYear(),wxD.GetMonth()+1,wxD.GetDay())
            self.EndModal(wxID_OK)

    def OnCancel(self,event):
        self.dRet = None
        self.EndModal(wxID_CANCEL)

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

if __name__=='__main__':
    setLevel(logging.INFO)

    app = wxPySimpleApp()
    print itrade_datePicker(None,"Datepicker",date.today())

# ============================================================================
# That's all folks !
# ============================================================================
# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
