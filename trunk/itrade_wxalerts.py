#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxalerts.py
#
# Description: Alerts wx Front-End
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is	Gilles Dumortier.
#
# Portions created by the Initial Developer are Copyright (C) 2004-2007 the
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
# Imports
# ============================================================================

# python system
import logging

# wxPython system
import itrade_wxversion
import wx
import wx.lib.mixins.listctrl as wxl

# iTrade system
from itrade_logging import *
from itrade_local import message
from itrade_portfolio import *

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

class iTradeAlertsListCtrl(wx.ListCtrl, wxl.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        wxl.ListCtrlAutoWidthMixin.__init__(self)

# ============================================================================
# iTradeAlertsPanel
#
#   Display Alerts information
# ============================================================================

class iTradeAlertsPanel(wx.Window):

    def __init__(self,parent,id,port):
        wx.Window.__init__(self, parent, id)
        self.m_port = port

        wx.EVT_SIZE(self, self.OnSize)

        # create an image list
        self.m_imagelist = wx.ImageList(16,16)
        self.idx_tbref = self.m_imagelist.Add(wx.Bitmap('res/invalid.png'))

        # List
        tID = wx.NewId()

        self.m_list = iTradeAlertsListCtrl(self, tID, style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_SINGLE_SEL | wx.LC_VRULES | wx.LC_HRULES)
        self.m_list.SetImageList(self.m_imagelist, wx.IMAGE_LIST_SMALL)
        self.m_list.SetFont(wx.Font(10, wx.SWISS , wx.NORMAL, wx.NORMAL))

        # __x temp
        alerts.scan()
        self.refresh()

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        #self.m_toolbar.SetDimensions(0, 0, w, 32)
        self.m_list.SetDimensions(0, 32, w, h-32)
        event.Skip(False)

    # Used by the wxl.ColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.m_list

    def refresh(self):
        self.m_list.ClearAll()
        self.m_list.InsertColumn(IDC_DATE, message('date'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_TYPE, message('type'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_SOURCE, message('source'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_ISIN, message('isin'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_TITLE, message('title'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)

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
        self.m_list.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

        # adjust columns
        self.m_list.SetColumnWidth(IDC_DATE, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_TYPE, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_SOURCE, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_ISIN, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_TITLE, wx.LIST_AUTOSIZE)

# ============================================================================
# iTradeNewsPanel
#
#   Display news for all quotes in the portfolio
# ============================================================================

class iTradeNewsPanel(wx.Window):

    def __init__(self,parent,id,port):
        wx.Window.__init__(self, parent, id)
        self.m_port = port

    def refresh(self):
        pass

# ============================================================================
# iTradeAlertsNotebookWindow
# ============================================================================

class iTradeAlertsNotebookWindow(wx.Notebook):

    ID_PAGE_ALERTS = 0
    ID_PAGE_NEWS = 1

    def __init__(self,parent,id,port):
        wx.Notebook.__init__(self,parent,id,wx.DefaultPosition, style=wx.SIMPLE_BORDER|wx.NB_TOP)
        self.m_port = port
        self.init()

        wx.EVT_NOTEBOOK_PAGE_CHANGED(self, self.GetId(), self.OnPageChanged)
        wx.EVT_NOTEBOOK_PAGE_CHANGING(self, self.GetId(), self.OnPageChanging)

    def init(self):
        self.win = {}
        self.DeleteAllPages()

        self.win[self.ID_PAGE_ALERTS] = iTradeAlertsPanel(self,wx.NewId(),self.m_port)
        self.AddPage(self.win[self.ID_PAGE_ALERTS], message('alerts_alerts'))

        self.win[self.ID_PAGE_NEWS] = iTradeNewsPanel(self,wx.NewId(),self.m_port)
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

class iTradeAlertsWindow(wx.Frame,iTrade_wxFrame):

    def __init__(self,parent,id,title,port):
        self.m_id = wx.NewId()
        wx.Frame.__init__(self,None,self.m_id, title, size = (640,480), style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        iTrade_wxFrame.__init__(self,parent,'alerts')
        self.m_port = port

        self.m_book = iTradeAlertsNotebookWindow(self, -1, port=self.m_port)

        wx.EVT_WINDOW_DESTROY(self, self.OnDestroy)
        wx.EVT_SIZE(self, self.OnSize)

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

    app = wx.PySimpleApp()

    from itrade_local import *
    setLang('us')
    gMessage.load()

    import itrade_wxportfolio

    port = itrade_wxportfolio.select_iTradePortfolio(None,'default','select')
    if port:
        port = loadPortfolio(port.filename())
        open_iTradeAlerts(None,port)
        app.MainLoop()

    alerts.save()

# ============================================================================
# That's all folks !
# ============================================================================
