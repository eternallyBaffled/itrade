#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxalerts.py
# Version      : $Id: itrade_wxalerts.py,v 1.12 2006/05/03 14:45:40 dgil Exp $
#
# Description: Alerts wx Front-End
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
# 2005-10-20    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Version management
# ============================================================================

__revision__ = "$Id: itrade_wxalerts.py,v 1.12 2006/05/03 14:45:40 dgil Exp $"
__author__ = "Gilles Dumortier (dgil@ieee.org)"
__version__ = "0.4"
__status__ = "alpha"
__cvsversion__ = "$Revision: 1.12 $"[11:-2]
__date__ = "$Date: 2006/05/03 14:45:40 $"[7:-2]
__copyright__ = "Copyright (c) 2004-2006 Gilles Dumortier"
__license__ = "GPL"
__credits__ = """ """

# ============================================================================
# Imports
# ============================================================================

# python system
import logging

# wxPython system
import itrade_wxversion
from wxPython.wx import *
#from wxPython.calendar import *
from wxPython.lib.mixins.listctrl import wxColumnSorterMixin, wxListCtrlAutoWidthMixin
#from wxPython.lib.maskededit import wxMaskedTextCtrl

# iTrade system
from itrade_logging import *
from itrade_local import message
#from itrade_quotes import *
from itrade_portfolio import *

#from itrade_wxquote import select_iTradeQuote
import itrade_wxres
from itrade_wxmixin import iTrade_wxFrame

# Alerts subsystem
from itrade_alerts import alerts
import itrade_alerts_srd

# ============================================================================
# column number
# ============================================================================

IDC_DATE = 0
IDC_TYPE = 1
IDC_SOURCE = 2
IDC_ISIN = 3
IDC_TITLE = 4

# ============================================================================
# iTradeAlertsListCtrl
# ============================================================================

class iTradeAlertsListCtrl(wxListCtrl, wxListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wxDefaultPosition,
                 size=wxDefaultSize, style=0):
        wxListCtrl.__init__(self, parent, ID, pos, size, style)
        wxListCtrlAutoWidthMixin.__init__(self)

# ============================================================================
# iTradeAlertsPanel
#
#   Display Alerts information
# ============================================================================

class iTradeAlertsPanel(wxWindow):

    def __init__(self,parent,id,port):
        wxWindow.__init__(self, parent, id)
        self.m_port = port

        EVT_SIZE(self, self.OnSize)

        # create an image list
        self.m_imagelist = wxImageList(16,16)
        self.idx_tbref = self.m_imagelist.Add(wxBitmap('res/invalid.gif'))

        # List
        tID = wxNewId()

        self.m_list = iTradeAlertsListCtrl(self, tID, style=wxLC_REPORT | wxSUNKEN_BORDER | wxLC_SINGLE_SEL | wxLC_VRULES | wxLC_HRULES)
        self.m_list.SetImageList(self.m_imagelist, wxIMAGE_LIST_SMALL)
        self.m_list.SetFont(wxFont(10, wxSWISS , wxNORMAL, wxNORMAL))

        # __x temp
        alerts.scan()
        self.refresh()

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        #self.m_toolbar.SetDimensions(0, 0, w, 32)
        self.m_list.SetDimensions(0, 32, w, h-32)
        event.Skip(False)

    # Used by the wxColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.m_list

    def refresh(self):
        self.m_list.ClearAll()
        self.m_list.InsertColumn(IDC_DATE, message('date'), wxLIST_FORMAT_LEFT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_TYPE, message('type'), wxLIST_FORMAT_LEFT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_SOURCE, message('source'), wxLIST_FORMAT_LEFT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_ISIN, message('isin'), wxLIST_FORMAT_LEFT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_TITLE, message('title'), wxLIST_FORMAT_LEFT, wxLIST_AUTOSIZE)

        x = 0
        for eachAlert in alerts.listAlerts():
            self.m_list.InsertImageStringItem(x, "%s" % eachAlert.date(), self.idx_tbref)
            self.m_list.SetStringItem(x,IDC_TYPE,eachAlert.type_desc())
            self.m_list.SetStringItem(x,IDC_SOURCE,eachAlert.source())
            self.m_list.SetStringItem(x,IDC_ISIN,eachAlert.isin())
            self.m_list.SetStringItem(x,IDC_TITLE,eachAlert.title())

            x = x + 1

        # default selection
        self.m_currentItem = 0
        self.m_list.SetItemState(0, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED)

        # adjust columns
        self.m_list.SetColumnWidth(IDC_DATE, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_TYPE, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_SOURCE, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_ISIN, wxLIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_TITLE, wxLIST_AUTOSIZE)

# ============================================================================
# iTradeNewsPanel
#
#   Display news for all quotes in the portfolio
# ============================================================================

class iTradeNewsPanel(wxWindow):

    def __init__(self,parent,id,port):
        wxWindow.__init__(self, parent, id)
        self.m_port = port

    def refresh(self):
        pass

# ============================================================================
# iTradeAlertsNotebookWindow
# ============================================================================

class iTradeAlertsNotebookWindow(wxNotebook):

    ID_PAGE_ALERTS = 0
    ID_PAGE_NEWS = 1

    def __init__(self,parent,id,port):
        wxNotebook.__init__(self,parent,id,wxDefaultPosition, style=wxSIMPLE_BORDER|wxNB_TOP)
        self.m_port = port
        self.init()

        EVT_NOTEBOOK_PAGE_CHANGED(self, self.GetId(), self.OnPageChanged)
        EVT_NOTEBOOK_PAGE_CHANGING(self, self.GetId(), self.OnPageChanging)

    def init(self):
        self.win = {}
        self.DeleteAllPages()

        self.win[self.ID_PAGE_ALERTS] = iTradeAlertsPanel(self,wxNewId(),self.m_port)
        self.AddPage(self.win[self.ID_PAGE_ALERTS], message('alerts_alerts'))

        self.win[self.ID_PAGE_NEWS] = iTradeNewsPanel(self,wxNewId(),self.m_port)
        self.AddPage(self.win[self.ID_PAGE_NEWS], message('alerts_news'))

    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        info('OnPageChanged,  old:%d, new:%d, sel:%d\n' % (old, new, sel))
        if old<>new:
            self.win[new].refresh()
        event.Skip()

    def OnPageChanging(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        info('OnPageChanging, old:%d, new:%d, sel:%d\n' % (old, new, sel))
        event.Skip()

# ============================================================================
# iTradeAlertsWindow
# ============================================================================

class iTradeAlertsWindow(wxFrame,iTrade_wxFrame):

    def __init__(self,parent,id,title,port):
        self.m_id = wxNewId()
        wxFrame.__init__(self,None,self.m_id, title, size = (640,480), style=wxDEFAULT_FRAME_STYLE|wxNO_FULL_REPAINT_ON_RESIZE)
        iTrade_wxFrame.__init__(self,parent,'alerts')
        self.m_port = port

        self.m_book = iTradeAlertsNotebookWindow(self, -1, port=self.m_port)

        EVT_WINDOW_DESTROY(self, self.OnDestroy)
        EVT_SIZE(self, self.OnSize)

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.m_book.SetDimensions(0, 0, w, h)

    def OnDestroy(self, evt):
        if self.m_parent:
            self.m_parent.m_hAlerts = None

# ============================================================================
# open_iTradeAlerts
# ============================================================================

def open_iTradeAlerts(win,port=None):
    debug('open_iTradeAlerts')
    if win and win.m_hAlerts:
        # set focus
        win.m_hAlerts.SetFocus()
    else:
        if not isinstance(port,Portfolio):
            port = loadPortfolio()
        frame = iTradeAlertsWindow(win, -1, "%s - %s" %(message('alerts_title'),port.name()),port)
        if win:
            win.m_hAlerts = frame
        frame.Show()

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    alerts.load()

    app = wxPySimpleApp()

    from itrade_local import *
    setLang('us')
    gMessage.load()

    import itrade_wxportfolio

    port = itrade_wxportfolio.select_iTradePortfolio(None,'default','select')
    if port:
        open_iTradeAlerts(None,port)
        app.MainLoop()

    alerts.save()

# ============================================================================
# That's all folks !
# ============================================================================
# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
