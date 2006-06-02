#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxcurrency.py
#
# Description: wxPython Currencies
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is Gilles Dumortier.
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
# 2006-04-2x    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import os
import logging
import time
import thread

# wxPython system
import itrade_wxversion
from wxPython.wx import *
from wxPython.lib.mixins.listctrl import wxColumnSorterMixin, wxListCtrlAutoWidthMixin

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_local import message
from itrade_currency import currencies

from itrade_wxmixin import iTrade_wxFrame
from itrade_wxlive import iTrade_wxLiveCurrencyMixin,EVT_UPDATE_LIVECURRENCY

# ============================================================================
# column number
# ============================================================================

# (common) view
IDC_FROM = 0
IDC_RATE = 1
IDC_TO = 2
IDC_DESC = 3

# ============================================================================
# menu identifier
# ============================================================================

ID_CLOSE = 111

ID_REFRESH = 230
ID_AUTOREFRESH = 231

# ============================================================================
# iTradeCurrencyToolbar
#
# ============================================================================

class iTradeCurrencyToolbar(wxToolBar):

    def __init__(self,parent,id):
        wxToolBar.__init__(self,parent,id,style = wxTB_HORIZONTAL | wxNO_BORDER | wxTB_FLAT)
        self.m_parent = parent
        self._init_toolbar()

    def _init_toolbar(self):
        self._NTB2_EXIT = wxNewId()
        self._NTB2_REFRESH = wxNewId()

        self.SetToolBitmapSize(wxSize(24,24))
        self.AddSimpleTool(self._NTB2_EXIT, wxArtProvider.GetBitmap(wxART_CROSS_MARK, wxART_TOOLBAR),
                           message('main_close'), message('main_desc_close'))

        self.AddControl(wxStaticLine(self, -1, size=(-1,23), style=wxLI_VERTICAL))
        self.AddSimpleTool(self._NTB2_REFRESH, wxBitmap('res/refresh.png'),
                           message('main_view_refresh'), message('main_view_desc_refresh'))

        EVT_TOOL(self, self._NTB2_EXIT, self.onExit)
        EVT_TOOL(self, self._NTB2_REFRESH, self.onRefresh)
        self.Realize()

    def onRefresh(self, event):
        self.m_parent.OnRefresh(event)

    def onExit(self,event):
        self.m_parent.OnClose(event)

# ============================================================================
# iTradeCurrenciesListCtrl
# ============================================================================

class iTradeCurrenciesListCtrl(wxListCtrl, wxListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wxDefaultPosition,
                 size=wxDefaultSize, style=0):
        wxListCtrl.__init__(self, parent, ID, pos, size, style)
        wxListCtrlAutoWidthMixin.__init__(self)

# ============================================================================
# iTradeCurrenciesWindow
# ============================================================================

import wx.lib.newevent
(PostInitEvent,EVT_POSTINIT) = wx.lib.newevent.NewEvent()

class iTradeCurrenciesWindow(wxFrame,iTrade_wxFrame,iTrade_wxLiveCurrencyMixin):
    def __init__(self, parent,id,title):
        self.m_id = wxNewId()
        wxFrame.__init__(self,None,self.m_id, title, size = (640,480), style=wxDEFAULT_FRAME_STYLE|wxNO_FULL_REPAINT_ON_RESIZE)
        iTrade_wxFrame.__init__(self,parent,'currencies')
        iTrade_wxLiveCurrencyMixin.__init__(self)

        # the menu
        self.filemenu = wxMenu()
        #self.filemenu.Append(ID_SAVE,message('main_save'),message('main_desc_save'))
        #self.filemenu.AppendSeparator()
        self.filemenu.Append(ID_CLOSE,message('main_close'),message('main_desc_close'))

        self.viewmenu = wxMenu()
        self.viewmenu.Append(ID_REFRESH, message('main_view_refresh'),message('main_view_desc_refresh'))
        self.viewmenu.AppendCheckItem(ID_AUTOREFRESH, message('main_view_autorefresh'),message('main_view_desc_autorefresh'))

        # default checking
        self.updateCheckItems()

        # Creating the menubar
        menuBar = wxMenuBar()

        # Adding the "<x>menu" to the MenuBar
        menuBar.Append(self.filemenu,message('currency_menu_file'))
        menuBar.Append(self.viewmenu,message('currency_menu_view'))

        # Adding the MenuBar to the Frame content
        self.SetMenuBar(menuBar)

        # Toolbar
        self.m_toolbar = iTradeCurrencyToolbar(self, wxNewId())

        # default list is quotes
        self.m_list = iTradeCurrenciesListCtrl(self, wxNewId(),
                                 style = wxLC_REPORT | wxSUNKEN_BORDER | wxLC_SINGLE_SEL | wxLC_VRULES | wxLC_HRULES)
        #self.m_list.SetImageList(self.m_imagelist, wxIMAGE_LIST_SMALL)
        self.m_list.SetFont(wxFont(10, wxSWISS , wxNORMAL, wxNORMAL))

        EVT_SIZE(self, self.OnSize)

        EVT_MENU(self, ID_CLOSE, self.OnClose)
        EVT_MENU(self, ID_REFRESH, self.OnRefresh)
        EVT_MENU(self, ID_AUTOREFRESH, self.OnAutoRefresh)

        EVT_WINDOW_DESTROY(self, self.OnDestroy)
        EVT_CLOSE(self, self.OnCloseWindow)

        EVT_UPDATE_LIVECURRENCY(self, self.OnLiveCurrency)

        # refresh full view after window init finished
        EVT_POSTINIT(self, self.OnPostInit)
        wxPostEvent(self,PostInitEvent())

        self.Show(True)

    # --- [ window management ] -------------------------------------

    def OnPostInit(self,event):
        self.populate(bDuringInit=True)
        self.updateCheckItems()
        self.OnRefresh(event)
        if itrade_config.bAutoRefreshCurrencyView:
            self.startLiveCurrency()

    def OnDestroy(self, evt):
        if self.m_parent:
            self.m_parent.m_hCurrency = None

    def OnClose(self,e):
        self.saveConfig()
        currencies.save()
        self.Close(True)

    def OnSize(self, event):
        debug('OnSize')
        w,h = self.GetClientSizeTuple()
        #self.m_toolbar.SetDimensions(0, 0, w, 32)
        self.m_list.SetDimensions(0, 32, w, h-32)
        event.Skip(False)

    def OnCloseWindow(self, evt):
        self.stopLiveCurrency(bBusy=False)
        self.Destroy()

    # Used by the wxColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.m_list

    def getColumnText(self, index, col):
        item = self.m_list.GetItem(index, col)
        return item.GetText()

    def updateCheckItems(self):
        m = self.viewmenu.FindItemById(ID_AUTOREFRESH)
        m.Check(itrade_config.bAutoRefreshCurrencyView)

    # --- [ autorefresh management ] -------------------------------------

    def OnAutoRefresh(self,e):
        itrade_config.bAutoRefreshCurrencyView = not itrade_config.bAutoRefreshCurrencyView
        self.setDirty()
        self.updateCheckItems()
        if itrade_config.bAutoRefreshCurrencyView:
            self.startLiveCurrency()
        else:
            self.stopLiveCurrency(bBusy=True)

    def OnRefresh(self,e):
        x = 0
        lst = currencies.m_currencies
        max = len(lst)
        keepGoing = True
        if self.hasFocus():
            dlg = wxProgressDialog(message('currency_refreshing'),"",max,self,wxPD_CAN_ABORT | wxPD_APP_MODAL)
        else:
            dlg = None
        for eachKey in lst:
            if keepGoing:
                curTo = eachKey[:3]
                curFrom = eachKey[3:]
                if dlg:
                    keepGoing = dlg.Update(x,"%s -> %s" % (curFrom,curTo))
                currencies.get(curTo,curFrom)
                self.refreshLine(eachKey,x,True)
                x = x + 1

        currencies.save()
        if dlg:
            dlg.Destroy()

    def OnLiveCurrency(self, evt):
        if self.isRunningCurrency(evt.key):
            self.refreshLine(evt.key,evt.param,True)

    # --- [ content management ] -------------------------------------

    def refreshLine(self,key,x,disp):
        used ,rate = currencies.m_currencies[key]
        self.m_list.SetStringItem(x,IDC_RATE,"%.4f" % rate)

    def populate(self,bDuringInit):
        info('populate duringinit=%d'%bDuringInit)
        # clear current population
        self.stopLiveCurrency(bBusy=False)
        self.unregisterLiveCurrency()
        self.m_list.ClearAll()

        self.m_list.InsertColumn(IDC_FROM, message('currency_from'), wxLIST_FORMAT_LEFT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_RATE, message('currency_rate'), wxLIST_FORMAT_LEFT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_TO, message('currency_to'), wxLIST_FORMAT_LEFT, wxLIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_DESC, '', wxLIST_FORMAT_LEFT, wxLIST_AUTOSIZE)

        x = 0
        for eachKey in currencies.m_currencies.keys():
            curTo = eachKey[:3]
            curFrom = eachKey[3:]
            self.m_list.InsertImageStringItem(x, "1 %s = " % curFrom, -1)
            self.m_list.SetStringItem(x,IDC_TO,"%s" % curTo)
            self.registerLiveCurrency(eachKey,itrade_config.refreshCurrencyView,x)
            self.refreshLine(eachKey,x,False)
            x = x + 1

        if not bDuringInit and itrade_config.bAutoRefreshCurrencyView:
            self.startLiveCurrency()

# ============================================================================
# open_iTradeCurrencies
# ============================================================================

def open_iTradeCurrencies(win):
    debug('open_iTradeCurrencies')
    if win and win.m_hCurrency:
        # set focus
        win.m_hCurrency.SetFocus()
    else:
        frame = iTradeCurrenciesWindow(win, -1, message('currencies_title'))
        if win:
            win.m_hCurrency = frame
        frame.Show()

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    from itrade_local import *
    setLang('us')
    gMessage.load()

    app = wxPySimpleApp()

    open_iTradeCurrencies(None)
    app.MainLoop()

# ============================================================================
# That's all folks !
# ============================================================================
# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
