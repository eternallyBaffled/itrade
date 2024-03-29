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
# 2006-04-2x    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import absolute_import
import os
import logging

# iTrade system
import itrade_config

# wxPython system
if not itrade_config.nowxversion:
    import itrade_wxversion
import wx
import wx.lib.mixins.listctrl as wxl
import wx.grid as gridlib
import wx.lib.newevent

# iTrade system
from itrade_logging import setLevel, debug, info
from itrade_local import message
from itrade_currency import currencies, list_of_currencies

# iTrade wxPython system
from itrade_wxmixin import iTrade_wxFrame
from itrade_wxlive import iTrade_wxLiveCurrencyMixin, EVT_UPDATE_LIVECURRENCY
from itrade_wxconvert import open_iTradeConverter

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

ID_CONVERT = 100

ID_CLOSE = 111

ID_REFRESH = 230
ID_AUTOREFRESH = 231


class iTradeCurrencyToolbar(wx.ToolBar):
    def __init__(self, parent, id):
        wx.ToolBar.__init__(self, parent=parent, id=id, style=wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        self.m_parent = parent
        self._init_toolbar()

    def _init_toolbar(self):
        self.SetToolBitmapSize(size=wx.Size(24, 24))
        close_tool = self.AddSimpleTool(wx.ID_ANY, wx.ArtProvider.GetBitmap(wx.ART_CROSS_MARK, wx.ART_TOOLBAR),
                           message('main_close'), message('main_desc_close'))

        self.AddControl(wx.StaticLine(self, wx.ID_ANY, size=(-1, 23), style=wx.LI_VERTICAL))
        convert_tool = self.AddSimpleTool(wx.ID_ANY, wx.Bitmap(os.path.join(itrade_config.dirRes, 'convert.png')),
                           message('main_view_convert'), message('main_view_desc_convert'))
        refresh_tool = self.AddSimpleTool(wx.ID_ANY, wx.Bitmap(os.path.join(itrade_config.dirRes, 'refresh.png')),
                           message('main_view_refresh'), message('main_view_desc_refresh'))

        self._NTB2_EXIT = close_tool.GetId()
        wx.EVT_TOOL(self, self._NTB2_EXIT, self.onExit)
        self._NTB2_CONVERT = convert_tool.GetId()
        wx.EVT_TOOL(self, self._NTB2_CONVERT, self.onConvert)
        self._NTB2_REFRESH = refresh_tool.GetId()
        wx.EVT_TOOL(self, self._NTB2_REFRESH, self.onRefresh)
        self.Realize()

    def onConvert(self, event):
        self.m_parent.OnConvert(event)

    def onRefresh(self, event):
        self.m_parent.OnRefresh(event)

    def onExit(self, event):
        self.m_parent.OnClose(event)

# ============================================================================
# iTradeCurrenciesListCtrl
# ============================================================================

class iTradeCurrenciesListCtrl(wx.ListCtrl, wxl.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, style=0, *args, **kwargs):
        wx.ListCtrl.__init__(self, parent=parent, id=ID, style=style, *args, **kwargs)
        wxl.ListCtrlAutoWidthMixin.__init__(self)


class iTradeCurrenciesMatrix(gridlib.Grid):
    def __init__(self, parent, ID, style=0, list=None, *args, **kwargs):
        gridlib.Grid.__init__(self, parent=parent, id=ID, style=style, *args, **kwargs)
        self.list = list
        count = len(list)

        grid = self.CreateGrid(count, count)
        self.EnableEditing(False)
        for i, currency in enumerate(list):
            self.SetColLabelValue(i, currency)
            self.SetRowLabelValue(i, currency)

        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, parent.OnDClick)


(PostInitEvent, EVT_POSTINIT) = wx.lib.newevent.NewEvent()


class iTradeCurrenciesWindow(wx.Frame, iTrade_wxFrame, iTrade_wxLiveCurrencyMixin):
    def __init__(self, parent, title, *args, **kwargs):
        wx.Frame.__init__(self, parent=parent,
                          title=title,
                          size=(640, 480),
                          style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE,
                          name='currencies', *args, **kwargs)
        iTrade_wxFrame.__init__(self, parent=parent,
                                name='currencies', *args, **kwargs)
        iTrade_wxLiveCurrencyMixin.__init__(self)
        self.filemenu = wx.Menu()
        # self.filemenu.Append(ID_SAVE, message('main_save'), message('main_desc_save'))
        # self.filemenu.AppendSeparator()
        self.filemenu.Append(ID_CLOSE, message('main_close'), message('main_desc_close'))

        self.viewmenu = wx.Menu()
        self.viewmenu.Append(ID_CONVERT, message('main_view_convert'), message('main_view_desc_convert'))
        self.viewmenu.Append(ID_REFRESH, message('main_view_refresh'), message('main_view_desc_refresh'))
        self.viewmenu.AppendCheckItem(ID_AUTOREFRESH,
                                      message('main_view_autorefresh'), message('main_view_desc_autorefresh'))

        # default checking
        self.updateCheckItems()

        # Creating the menubar
        menu_bar = wx.MenuBar()

        # Adding the "<x>menu" to the MenuBar
        menu_bar.Append(self.filemenu, message('currency_menu_file'))
        menu_bar.Append(self.viewmenu, message('currency_menu_view'))

        # Adding the MenuBar to the Frame content
        self.SetMenuBar(menubar=menu_bar)

        # Toolbar
        self.m_toolbar = iTradeCurrencyToolbar(parent=self, id=wx.ID_ANY)

        # default list is quotes
        self.m_list = iTradeCurrenciesMatrix(parent=self, ID=wx.ID_ANY,
                                 style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_SINGLE_SEL | wx.LC_VRULES | wx.LC_HRULES,
                                 list=list_of_currencies())
        # self.m_list.SetImageList(self.m_imagelist, wx.IMAGE_LIST_SMALL)
        self.m_list.SetFont(font=wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        wx.EVT_SIZE(self, self.OnSize)

        wx.EVT_MENU(self, ID_CLOSE, self.OnClose)
        wx.EVT_MENU(self, ID_CONVERT, self.OnConvert)
        wx.EVT_MENU(self, ID_REFRESH, self.OnRefresh)
        wx.EVT_MENU(self, ID_AUTOREFRESH, self.OnAutoRefresh)

        wx.EVT_WINDOW_DESTROY(self, self.OnDestroy)
        wx.EVT_CLOSE(self, self.OnCloseWindow)

        EVT_UPDATE_LIVECURRENCY(self, self.OnLiveCurrency)

        # refresh full view after window init finished
        EVT_POSTINIT(self, self.OnPostInit)
        wx.PostEvent(self, PostInitEvent())

        self.Show(show=True)

    # --- [ window management ] -------------------------------------

    def OnPostInit(self, event):
        self.populate(bDuringInit=True)
        self.updateCheckItems()
        self.OnRefresh(event)
        if itrade_config.bAutoRefreshCurrencyView:
            self.startLiveCurrency()

    def OnDestroy(self, evt):
        if self.m_parent:
            self.m_parent.m_hCurrency = None

    def OnClose(self, e):
        self.Close(True)

    def OnSize(self, event):
        debug('OnSize')
        w, h = self.GetClientSizeTuple()
        # self.m_toolbar.SetDimensions(0, 0, w, 32)
        self.m_list.SetDimensions(0, 32, w, h-32)
        event.Skip(False)

    def OnCloseWindow(self, evt):
        self.stopLiveCurrency()
        self.unregisterLiveCurrency()
        self.saveConfig()
        currencies.save()
        self.Destroy()

    # Used by the wxl.ColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.m_list

    def getColumnText(self, index, col):
        item = self.m_list.GetItem(index, col)
        return item.GetText()

    def updateCheckItems(self):
        m = self.viewmenu.FindItemById(ID_AUTOREFRESH)
        m.Check(itrade_config.bAutoRefreshCurrencyView)

    # --- [ autorefresh management ] -------------------------------------

    def OnAutoRefresh(self, e):
        itrade_config.bAutoRefreshCurrencyView = not itrade_config.bAutoRefreshCurrencyView
        itrade_config.save_config()
        self.updateCheckItems()
        if itrade_config.bAutoRefreshCurrencyView:
            self.startLiveCurrency()
        else:
            self.stopLiveCurrency(bBusy=True)

    def OnRefresh(self, e):
        lst = currencies.m_currencies
        keep_going = True
        if self.hasFocus():
            dlg = wx.ProgressDialog(message('currency_refreshing'),
                                    "",
                                    len(lst),
                                    self,
                                    wx.PD_CAN_ABORT | wx.PD_APP_MODAL)
        else:
            dlg = None
        with dlg:
            for x, eachKey in enumerate(lst):
                if not keep_going:
                    break
                cur_to = eachKey[:3]
                cur_from = eachKey[3:]
                if dlg:
                    (keep_going, skip) = dlg.Update(x, u"{} -> {}".format(cur_from, cur_to))
                currencies.get(cur_to, cur_from)
                self.refreshLine(eachKey, x, True)
            currencies.save()

    def OnLiveCurrency(self, evt):
        if self.isRunningCurrency(evt.key):
            self.refreshLine(evt.key, evt.param, True)

    # --- [ converter ] ----------------------------------------------

    def OnConvert(self, evt):
        open_iTradeConverter(self)

    def OnDClick(self, evt):
        row = evt.GetRow()
        col = evt.GetCol()
        open_iTradeConverter(self, (row, col))

    # --- [ content management ] -------------------------------------

    def refreshLine(self, key, x, disp):
        used, rate = currencies.m_currencies[key]
        # self.m_list.SetStringItem(x, IDC_RATE, "{:.4f}".format(rate))
        c_list = list_of_currencies()
        cur_to = key[:3]
        ind_to = [ind for ind, currency in enumerate(c_list) if currency == cur_to][0]
        cur_from = key[3:]
        ind_from = [ind for ind, currency in enumerate(c_list) if currency == cur_from][0]
        self.m_list.SetCellValue(ind_from, ind_to, "{:.4f}".format(rate))

    def populate(self, bDuringInit):
        info('populate duringinit={:d}'.format(bDuringInit))
        # clear current population
        self.stopLiveCurrency()
        self.unregisterLiveCurrency()

        clist = list_of_currencies()
        for i, to_currency in enumerate(clist):
            for j, from_currency in enumerate(clist):
                # currencies.rate format : curTo, curFrom
                self.m_list.SetCellValue(i, j, "{:.4f}".format(currencies.rate(from_currency, to_currency)))
                self.m_list.SetCellAlignment(i, j, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)

        if not bDuringInit and itrade_config.bAutoRefreshCurrencyView:
            self.startLiveCurrency()


def open_iTradeCurrencies(win):
    debug('open_iTradeCurrencies')
    if win and win.m_hCurrency:
        # set focus
        win.m_hCurrency.SetFocus()
    else:
        frame = iTradeCurrenciesWindow(win, message('currencies_title'))
        if win:
            win.m_hCurrency = frame
        frame.Show()


def main():
    setLevel(logging.DEBUG)
#    from itrade_local import setLang, gMessage
#    setLang('us')
#    gMessage.load()
    app = wx.App()
    open_iTradeCurrencies(None)
    app.MainLoop()


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
