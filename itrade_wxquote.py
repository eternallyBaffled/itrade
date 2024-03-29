#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxquote.py
#
# Description: wxPython quote display
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
# 2005-03-27    dgil  Wrote it from scratch
# 2005-04-03    dgil  Add quote selector
# 2005-05-29    dgil  Move liste quote stuff to module itrade_wxlistquote.py
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from __future__ import absolute_import
import os
import logging

# iTrade system
from itrade_datation import gCal
from itrade_logging import setLevel, debug
from itrade_quotes import quotes, initQuotesModule, Quote
from itrade_local import message
import itrade_config
from six.moves import range

# wxPython system
if not itrade_config.nowxversion:
    import itrade_wxversion
import wx
import wx.grid as gridlib
# import sized_controls from wx.lib for wxPython version >= 2.8.8.0 (from wxaddons otherwise)
import wx.lib.sized_controls as sc

# matplotlib system
import matplotlib

from matplotlib.dates import date2num
import myfinance as mf

# iTrade wxPython system
from itrade_wxhtml import iTradeHtmlPanel, iTradeRSSPanel
from itrade_wxmixin import iTrade_wxFrame
from itrade_wxgraph import iTrade_wxPanelGraph, fmtVolumeFunc
from itrade_wxlive import iTrade_wxLive, iTrade_wxLiveMixin, EVT_UPDATE_LIVE
from itrade_wxselectquote import select_iTradeQuote
from itrade_wxpropquote import iTradeQuotePropertiesPanel
from itrade_wxdecision import iTrade_wxDecision
from itrade_market import yahoosuffix
# ============================================================================
# iTradeQuoteToolbar
#
# ============================================================================

class iTradeQuoteToolbar(wx.ToolBar):
    def __init__(self, parent, id, *args, **kwargs):
        wx.ToolBar.__init__(self, parent=parent, id=id, size=(120,32), style=wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT, *args, **kwargs)
        self.m_parent = parent
        self.m_Throbber = None
        self._init_toolbar()

    def _init_toolbar(self):
        self.SetToolBitmapSize(size=wx.Size(24, 24))
        exit_tool = self.AddSimpleTool(id=wx.ID_ANY, bitmap=wx.ArtProvider.GetBitmap(wx.ART_CROSS_MARK, wx.ART_TOOLBAR),
                           shortHelpString=message('main_close'), longHelpString=message('main_desc_close'))
        self.AddControl(wx.StaticLine(parent=self, id=wx.ID_ANY, size=(-1,23), style=wx.LI_VERTICAL))
        select_tool = self.AddSimpleTool(id=wx.ID_ANY, bitmap=wx.Bitmap(os.path.join(itrade_config.dirRes, 'quotes.png')),
                           shortHelpString=message('quote_select_title'), longHelpString=message('quote_select_title'))
        refresh_tool = self.AddSimpleTool(wx.ID_ANY, wx.Bitmap(os.path.join(itrade_config.dirRes, 'refresh.png')),
                           message('main_view_refresh'), message('main_view_desc_refresh'))

        self._NTB2_EXIT = exit_tool.GetId()
        wx.EVT_TOOL(self, self._NTB2_EXIT, self.exit)
        self._NTB2_SELECT = select_tool.GetId()
        wx.EVT_TOOL(self, self._NTB2_SELECT, self.select)
        self._NTB2_REFRESH = refresh_tool.GetId()
        wx.EVT_TOOL(self, self._NTB2_REFRESH, self.refresh)
        self.Realize()

    def refresh(self, event):
        if (not self.m_Throbber) or (not self.m_Throbber.Running()):
            # refresh
            self.m_parent.OnRefresh(event)

    def OnStop(self):
        # stop animation
        if self.m_Throbber:
            self.m_Throbber.Rest()

    def OnStart(self):
        # start animation
        if self.m_Throbber:
            self.m_Throbber.Start()

    def select(self, event):
        self.m_parent.OnSelectQuote(event)

    def exit(self, event):
        self.m_parent.OnExit(event)

# ============================================================================
# iTradeQuoteInfoWindow
#
#   Display informations on a specific quote
# ============================================================================

def exists(filename):
    try:
        with open(filename) as f:
            return True
    except Exception:
        return False

class iTradeQuoteInfoWindow(sc.SizedPanel):
    def __init__(self, parent, id, size, quote):
        sc.SizedPanel.__init__(self, parent, id, size=size, style=wx.SIMPLE_BORDER | wx.TAB_TRAVERSAL | wx.NO_FULL_REPAINT_ON_RESIZE)

        self.m_parent = parent
        self.m_quote = quote
        self.m_logo = None

        self.SetSizerType("vertical")

        # Toolbar
        self.m_toolbar = iTradeQuoteToolbar(self, wx.ID_ANY)

        # separator
        self.wxLine = wx.StaticLine(self, wx.ID_ANY, size=(20,-1), style=wx.LI_HORIZONTAL)
        self.wxLine.SetSizerProps(expand=True)

        # resizable pane
        pane = sc.SizedPanel(self, wx.ID_ANY)
        pane.SetSizerType("horizontal")
        pane.SetSizerProps(expand=True)

        self.wxTicker = wx.StaticText(pane, wx.ID_ANY, "???")
        self.wxTicker.SetSizerProps(valign='center')

        self.wxLogo = wx.StaticBitmap(pane, wx.ID_ANY)
        self.wxLogo.SetSizerProps(valign='center')

        # separator
        line = wx.StaticLine(self, wx.ID_ANY, size=(20,-1), style=wx.LI_HORIZONTAL)
        line.SetSizerProps(expand=True)

        self.wxDate = wx.StaticText(self, wx.ID_ANY, "???")

        # resizable pane
        pane = sc.SizedPanel(self, wx.ID_ANY)
        pane.SetSizerType("form")
        pane.SetSizerProps(expand=True)

        txt = wx.StaticText(pane, wx.ID_ANY, message('variation'))
        self.wxPercent = wx.StaticText(pane, wx.ID_ANY, "??? %")

        txt = wx.StaticText(pane, wx.ID_ANY, message('last'))
        self.wxLast = wx.StaticText(pane, wx.ID_ANY, "???")

        txt = wx.StaticText(pane, wx.ID_ANY, message('open'))
        self.wxOpen = wx.StaticText(pane, wx.ID_ANY, "???")

        txt = wx.StaticText(pane, wx.ID_ANY, message('high'))
        self.wxHigh = wx.StaticText(pane, wx.ID_ANY, "???")

        txt = wx.StaticText(pane, wx.ID_ANY, message('low'))
        self.wxLow = wx.StaticText(pane, wx.ID_ANY, "???")

        txt = wx.StaticText(pane, wx.ID_ANY, message('volume'))
        self.wxVolume = wx.StaticText(pane, wx.ID_ANY, "???")

        txt = wx.StaticText(pane, wx.ID_ANY, message('prev'))
        self.wxPrev = wx.StaticText(pane, wx.ID_ANY, "???")

        txt = wx.StaticText(pane, wx.ID_ANY, message('cmp'))
        self.wxCmp = wx.StaticText(pane, wx.ID_ANY, "???")

        # separator
        line = wx.StaticLine(self, wx.ID_ANY, size=(20,-1), style=wx.LI_HORIZONTAL)
        line.SetSizerProps(expand=True)

        # resizable pane
        pane = sc.SizedPanel(self, wx.ID_ANY)
        pane.SetSizerType("form")
        pane.SetSizerProps(expand=True)

        txt = wx.StaticText(pane, wx.ID_ANY, message('status'))
        self.wxStatus = wx.StaticText(pane, wx.ID_ANY, "")

        txt = wx.StaticText(pane, wx.ID_ANY, message('reopen'))
        self.wxReopen = wx.StaticText(pane, wx.ID_ANY, "???")

        txt = wx.StaticText(pane, wx.ID_ANY, message('high_threshold'))
        self.wxHigh_threshold = wx.StaticText(pane, wx.ID_ANY, "???")

        txt = wx.StaticText(pane, wx.ID_ANY, message('low_threshold'))
        self.wxLow_threshold = wx.StaticText(pane, wx.ID_ANY, "???")

        # separator
        line = wx.StaticLine(self, wx.ID_ANY, size=(20,-1), style=wx.LI_HORIZONTAL)
        line.SetSizerProps(expand=True)

        self.refresh()

    def OnSelectQuote(self, event):
        self.m_parent.SelectQuote()

    def OnRefresh(self, event):
        self.m_parent.refresh()

    def OnExit(self, evt):
        self.m_parent.OnExit(evt)

    def suffixLogo(self, ext):
        return u'{}-{}.{}'.format(self.m_quote.ticker().lower(), self.m_quote.market().lower(), ext)

    def paintLogo(self):
        if self.m_logo is None:
            fn = os.path.join(itrade_config.dirImageData, self.suffixLogo('gif'))
            if not exists(fn):
                fn = os.path.join(itrade_config.dirImageData, self.suffixLogo('png'))
            if not exists(fn):
                fn = os.path.join(itrade_config.dirImageData, self.suffixLogo('bmp'))
            if not exists(fn):
                fn = os.path.join(itrade_config.dirImageData, self.suffixLogo('jpg'))
            self.wxLogo.SetBitmap(wx.NullBitmap)
            if exists(fn):
                self.m_logo = wx.Bitmap(fn)
                self.wxLogo.SetBitmap(self.m_logo)

    def paint(self):
        # paint logo (if any)
        self.paintLogo()

        # paint fields
        self.wxTicker.SetLabel(label=self.m_quote.ticker())
        self.wxDate.SetLabel(label=u"{} | {} | {}".format(self.m_quote.sv_date(bDisplayShort=True), self.m_quote.sv_clock(), self.m_quote.sv_type_of_clock()))

        percent = self.m_quote.nv_percent()
        if percent == 0:
            self.wxPercent.SetForegroundColour(colour=wx.BLACK)
            self.wxLast.SetForegroundColour(colour=wx.BLACK)
        elif percent < 0:
            self.wxPercent.SetForegroundColour(colour=wx.RED)
            self.wxLast.SetForegroundColour(colour=wx.RED)
        else:
            self.wxPercent.SetForegroundColour(colour=wx.BLUE)
            self.wxLast.SetForegroundColour(colour=wx.BLUE)
        self.wxPercent.SetLabel(label=self.m_quote.sv_percent())

        self.wxLast.SetLabel(label=self.m_quote.sv_close(bDispCurrency=True))

        if self.m_quote.hasTraded():
            self.wxOpen.SetLabel(label=self.m_quote.sv_open())
            self.wxHigh.SetLabel(label=self.m_quote.sv_high())
            self.wxLow.SetLabel(label=self.m_quote.sv_low())
            self.wxVolume.SetLabel(label=self.m_quote.sv_volume())
        else:
            self.wxOpen.SetLabel(label=" ---.-- ")
            self.wxHigh.SetLabel(label=" ---.-- ")
            self.wxLow.SetLabel(label=" ---.-- ")
            self.wxVolume.SetLabel(label=" ---------- ")

        self.wxPrev.SetLabel(label=self.m_quote.sv_prevclose())
        self.wxCmp.SetLabel(label=self.m_quote.sv_waq())

        status = self.m_quote.sv_status()
        if status == "OK":
            self.wxStatus.SetForegroundColour(colour=wx.BLUE)
        else:
            self.wxStatus.SetForegroundColour(colour=wx.RED)

        self.wxStatus.SetLabel(label=status)
        self.wxReopen.SetLabel(label=self.m_quote.sv_reopen())
        self.wxHigh_threshold.SetLabel(label=u"{:.2f}".format(self.m_quote.high_threshold()))
        self.wxLow_threshold.SetLabel(label=u"{:.2f}".format(self.m_quote.low_threshold()))

    def refresh(self, nquote=None, live=False):
        debug(u'QuoteInfoWindow::refresh {}'.format(self.m_quote.ticker()))

        # update the logo if needed
        fit = False
        if nquote and nquote != self.m_quote:
            if itrade_config.verbose:
                print(u'QuoteInfoWindow::refresh New Quote {} - live={}'.format(nquote.ticker(), live))
            self.m_quote = nquote
            self.m_logo = None
            fit = True

        # __x to be removed - no need to update or compute at this stage
        if not itrade_config.experimental:
            if not live:
                self.m_quote.update()
            self.m_quote.compute()

        # paint the content
        if itrade_config.verbose:
            print(u'QuoteInfoWindow::refresh Paint Quote {} - live={}'.format(self.m_quote.ticker(), live))
        self.paint()

        # fit but stay on the space given by the parent
        if fit:
            size = self.GetSize()
            self.Fit()
            self.SetMinSize(minSize=size)
            self.SetSize(size=size)

# ============================================================================
# iTradeQuoteTablePanel
#
#   Table
# ============================================================================

class CustomDataTable(gridlib.PyGridTableBase):

    def __init__(self, quote):
        gridlib.PyGridTableBase.__init__(self)

        self.colLabels = [ message('date'),
                           message('volume'),
                           message('open'),
                           message('low'),
                           message('high'),
                           message('last'),
                         ]

        self.dataTypes = [gridlib.GRID_VALUE_STRING,
                          gridlib.GRID_VALUE_FLOAT + ':12,0',
                          gridlib.GRID_VALUE_FLOAT + ':6,3',
                          gridlib.GRID_VALUE_FLOAT + ':6,3',
                          gridlib.GRID_VALUE_FLOAT + ':6,3',
                          gridlib.GRID_VALUE_FLOAT + ':6,3',
                          ]

        self.data = []

        ltrades = quote.trades()

        if ltrades:
            for trade in ltrades.trades():
                self.data.append([trade.date(), trade.nv_volume(), trade.nv_open(), trade.nv_low(), trade.nv_high(), trade.nv_close()])

    # ---[ required methods for the wxPyGridTableBase interface ] -------------------

    def GetNumberRows(self):
        return len(self.data)

    def GetNumberCols(self):
        return len(self.colLabels)

    def IsEmptyCell(self, row, col):
        try:
            return not self.data[row][col]
        except IndexError:
            return True

    # Get/Set values in the table.  The Python version of these
    # methods can handle any data-type, (as long as the Editor and
    # Renderer understands the type too,) not just strings as in the
    # C++ version.
    def GetValue(self, row, col):
        try:
            return self.data[row][col]
        except IndexError:
            return ''

    def SetValue(self, row, col, value):
        try:
            self.data[row][col] = value
        except IndexError:
            # add a new row
            self.data.append([''] * self.GetNumberCols())
            self.SetValue(row, col, value)
            # tell the grid we've added a row
            msg = gridlib.GridTableMessage(self,            # The table
                    gridlib.GRIDTABLE_NOTIFY_ROWS_APPENDED, # what we did to it
                    1                                       # how many
                    )
            self.GetView().ProcessTableMessage(msg)

    # ---[ Some optional methods ] ---------------------------------------

    # Called when the grid needs to display labels
    def GetColLabelValue(self, col):
        return self.colLabels[col]

    # Called to determine the kind of editor/renderer to use by
    # default, doesn't necessarily have to be the same type used
    # natively by the editor/renderer if they know how to convert.
    def GetTypeName(self, row, col):
        return self.dataTypes[col]

    # Called to determine how the data can be fetched and stored by the
    # editor and renderer.  This allows you to enforce some type-safety
    # in the grid.
    def CanGetValueAs(self, row, col, typeName):
        colType = self.dataTypes[col].split(':')[0]
        if typeName == colType:
            return True
        else:
            return False

    def CanSetValueAs(self, row, col, typeName):
        return self.CanGetValueAs(row, col, typeName)

class CustTableGrid(gridlib.Grid):

    def __init__(self, parent, quote):
        gridlib.Grid.__init__(self, parent, wx.ID_ANY)
        table = CustomDataTable(quote)
        self.SetTable(table=table, takeOwnership=True)
        self.SetRowLabelSize(width=0)
        self.SetMargins(0, 0)
        self.AutoSizeColumns(False)
        gridlib.EVT_GRID_CELL_LEFT_DCLICK(self, self.OnLeftDClick)

    # I do this because I don't like the default behaviour of not starting the
    # cell editor on double clicks, but only a second click.
    def OnLeftDClick(self, evt):
        if self.CanEnableCellControl():
            self.EnableCellEditControl()

class iTradeQuoteTablePanel(wx.Panel):

    def __init__(self, parent, id, quote, *args, **kwargs):
        wx.Panel.__init__(self, parent, id, *args, **kwargs)
        self.m_quote = quote
        self.m_parent = parent
        self.m_port = parent.portfolio()

        # create the grid
        self.m_grid = CustTableGrid(self, quote)

        # --- vertical sizer
        bs = wx.BoxSizer(wx.VERTICAL)
        bs.Add(self.m_grid, 1, wx.GROW|wx.ALL, 5)
        self.SetSizer(sizer=bs)

    #def paint(self):
    #    pass
    #
    #def refresh(self):
    #    info('QuoteTablePanel::refresh %s' % self.m_quote.ticker())
    #    self.paint()

    def DonePage(self):
        self.m_grid.Show(show=False)

    def InitPage(self):
        self.m_grid.Show(show=True)

# ============================================================================
# iTradeQuoteAnalysisPanel
#
#   Display Candlestick / Analysis on a specific quote
# ============================================================================

class iTradeQuoteAnalysisPanel(wx.Window):

    def __init__(self, parent, id, quote, *args, **kwargs):
        wx.Window.__init__(self, parent, id, *args, **kwargs)
        self.m_quote = quote
        self.m_parent = parent
        self.m_port = parent.portfolio()

        txt = wx.StaticText(self, wx.ID_ANY, "Candle : ", wx.Point(5, 25), wx.Size(70, 20))
        self.m_candle = wx.StaticText(self, wx.ID_ANY, "???", wx.Point(80, 25), wx.Size(120, 20))

    #def paint(self):
    #    self.m_candle.SetLabel(self.m_quote.ov_candle().__str__())
    #
    #def refresh(self):
    #    info(u'QuoteAnalysisPanel::refresh {}'.format(self.m_quote.ticker()))
    #    self.paint()

    def InitPage(self):
        self.m_candle.SetLabel(label=self.m_quote.ov_candle().__str__())

    def DonePage(self):
        pass

# ============================================================================
# iTradeQuoteLivePanel
#
# ============================================================================

class iTradeQuoteLivePanel(wx.Panel):
    def __init__(self, parent, gparent, id, quote, *args, **kwargs):
        wx.Panel.__init__(self, parent, id, *args, **kwargs)
        self.m_quote = quote
        self.m_parent = gparent
        self.m_port = parent.portfolio()

        self.m_live = iTrade_wxLive(self, gparent, self.m_quote)
        self.m_decision = iTrade_wxDecision(self, self.m_quote, self.m_port)
        wx.EVT_SIZE(self, self.OnSize)

    def InitPage(self):
        self.m_live.InitPage()

    def DonePage(self):
        self.m_live.DonePage()

    def refresh(self):
        self.m_live.refresh()
        self.m_decision.refresh()

    def OnSize(self, event):
        w, h = self.GetClientSizeTuple()
        self.m_live.SetDimensions(0, 0, w, 180)
        self.m_decision.SetDimensions(0, 180, w, h-180)

# ============================================================================
# iTradeQuoteGraphPanel
# ============================================================================

class iTradeQuoteGraphPanel(wx.Panel, iTrade_wxPanelGraph):
    def __init__(self, parent, quote, *args, **kwargs):
        wx.Panel.__init__(self, parent=parent, size=(5,4), *args, **kwargs)
        iTrade_wxPanelGraph.__init__(self, parent=parent, size=(5,4), *args, **kwargs)
        self.m_quote = quote
        self.m_nIndex = self.m_quote.lastindex()
        # print('m_nIndex=', self.m_nIndex)

        self.zoomPeriod = (20,40,80,160,320)
        self.zoomIncPeriod = (5,10,20,40,80)
        self.zoomMultiple = (2,5,10,20,40)
        self.zoomLevel = 2
        self.zoomMaxLevel = len(self.zoomPeriod)-1

        # settings
        self.m_dispMA150 = False
        self.m_dispBollinger = True
        self.m_dispOverlaidVolume = False
        self.m_dispLegend = True
        self.m_dispGrid = True
        self.m_dispChart1Type = 'c'
        self.m_dispRSI14 = True
        self.m_dispSto = False

        # parameter iTrade_wxPanelGraph
        self.m_hasChart1Vol = self.m_dispOverlaidVolume
        self.m_hasChart2Vol = True
        self.m_hasGrid = self.m_dispGrid
        self.m_hasLegend = self.m_dispLegend

    def InitPage(self):
        print('$$$InitPage')
        self.RedrawAll(redraw=False)

    def DonePage(self):
        print('$$$DonePage')

    def RedrawAll(self, redraw=True):
        print('$$$RedrawAll redraw={}'.format(redraw))
        self.ChartRealize()
        if redraw:
            self.m_canvas.draw()
            self.drawAllObjects()

    def OnPaint(self, event):
        size = self.GetClientSize()
        print("OnPaint:", size)
        self.erase_cursor()
        event.Skip()

    def refresh(self):
        print('$$$refresh')
        self.RedrawAll()

    def OnHome(self, event):
        self.m_nIndex = self.m_quote.lastindex()
        self.zoomLevel = 2
        self.removeAllObjects()
        self.RedrawAll()

    def OnPanLeft(self, event):
        min = self.m_quote.firstindex() + self.zoomPeriod[self.zoomLevel]
        if self.m_nIndex >= min:
            self.m_nIndex = self.m_nIndex - self.zoomIncPeriod[self.zoomLevel]
            if self.m_nIndex <= min:
                self.m_nIndex = min
            self.RedrawAll()

    def OnPanRight(self, event):
        if self.m_nIndex < self.m_quote.lastindex():
            self.m_nIndex = self.m_nIndex + self.zoomIncPeriod[self.zoomLevel]
            if self.m_nIndex >= self.m_quote.lastindex():
                self.m_nIndex = self.m_quote.lastindex()
            self.RedrawAll()

    def OnZoomOut(self, event):
        if self.zoomLevel < self.zoomMaxLevel:
            self.zoomLevel = self.zoomLevel + 1
            if self.zoomLevel > self.zoomMaxLevel:
                self.zoomLevel = self.zoomMaxLevel
            self.RedrawAll()

    def OnZoomIn(self, event):
        if self.zoomLevel > 0:
            self.zoomLevel = self.zoomLevel - 1
            if self.zoomLevel < 0:
                self.zoomLevel = 0
            self.RedrawAll()

    def OnConfig(self, event):
        if not hasattr(self, "m_popupID_dispMA150"):
            self.m_popupID_dispMA150 = wx.NewId()
            wx.EVT_MENU(self, self.m_popupID_dispMA150, self.OnPopup_dispMA150)
            self.m_popupID_dispRSI14 = wx.NewId()
            wx.EVT_MENU(self, self.m_popupID_dispRSI14, self.OnPopup_dispRSI14)
            self.m_popupID_dispSto = wx.NewId()
            wx.EVT_MENU(self, self.m_popupID_dispSto, self.OnPopup_dispSto)
            self.m_popupID_dispBollinger = wx.NewId()
            wx.EVT_MENU(self, self.m_popupID_dispBollinger, self.OnPopup_dispBollinger)
            self.m_popupID_dispOverlaidVolume = wx.NewId()
            wx.EVT_MENU(self, self.m_popupID_dispOverlaidVolume, self.OnPopup_dispOverlaidVolume)
            self.m_popupID_dispLegend = wx.NewId()
            wx.EVT_MENU(self, self.m_popupID_dispLegend, self.OnPopup_dispLegend)
            self.m_popupID_dispGrid = wx.NewId()
            wx.EVT_MENU(self, self.m_popupID_dispGrid, self.OnPopup_dispGrid)
            self.m_popupID_dispChart1Candlestick = wx.NewId()
            wx.EVT_MENU(self, self.m_popupID_dispChart1Candlestick, self.OnPopup_dispChart1Candlestick)
            self.m_popupID_dispChart1OHLC = wx.NewId()
            wx.EVT_MENU(self, self.m_popupID_dispChart1OHLC, self.OnPopup_dispChart1OHLC)
            self.m_popupID_dispChart1Line = wx.NewId()
            wx.EVT_MENU(self, self.m_popupID_dispChart1Line, self.OnPopup_dispChart1Line)

        # make a menu
        self.popmenu = wx.Menu()
        # add items
        i = self.popmenu.AppendRadioItem(self.m_popupID_dispChart1Candlestick, message('quote_popup_dispChart1Candlestick'))
        i.Check(self.m_dispChart1Type == 'c')
        i = self.popmenu.AppendRadioItem(self.m_popupID_dispChart1OHLC, message('quote_popup_dispChart1OHLC'))
        i.Check(self.m_dispChart1Type == 'o')
        i = self.popmenu.AppendRadioItem(self.m_popupID_dispChart1Line, message('quote_popup_dispChart1Line'))
        i.Check(self.m_dispChart1Type == 'l')
        self.popmenu.AppendSeparator()
        i = self.popmenu.AppendCheckItem(self.m_popupID_dispLegend, message('quote_popup_dispLegend'))
        i.Check(self.m_dispLegend)
        i = self.popmenu.AppendCheckItem(self.m_popupID_dispGrid, message('quote_popup_dispGrid'))
        i.Check(self.m_dispGrid)
        self.popmenu.AppendSeparator()
        i = self.popmenu.AppendCheckItem(self.m_popupID_dispMA150, message('quote_popup_dispMA150'))
        i.Check(self.m_dispMA150)
        i = self.popmenu.AppendCheckItem(self.m_popupID_dispSto, message('quote_popup_dispSto'))
        i.Check(self.m_dispSto)
        i = self.popmenu.AppendCheckItem(self.m_popupID_dispRSI14, message('quote_popup_dispRSI14'))
        i.Check(self.m_dispRSI14)
        i = self.popmenu.AppendCheckItem(self.m_popupID_dispBollinger, message('quote_popup_dispBollinger'))
        i.Check(self.m_dispBollinger)
        self.popmenu.AppendSeparator()
        i = self.popmenu.AppendCheckItem(self.m_popupID_dispOverlaidVolume, message('quote_popup_dispOverlaidVolume'))
        i.Check(self.m_dispOverlaidVolume)

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.m_toolbar.PopupMenu(self.popmenu)
        self.popmenu.Destroy()

    def OnPopup_dispChart1Candlestick(self, event):
        self.m_dispChart1Type = 'c'
        m = self.popmenu.FindItemById(self.m_popupID_dispChart1Candlestick)
        m.Check(True)
        self.RedrawAll()

    def OnPopup_dispChart1OHLC(self, event):
        self.m_dispChart1Type = 'o'
        m = self.popmenu.FindItemById(self.m_popupID_dispChart1OHLC)
        m.Check(True)
        self.RedrawAll()

    def OnPopup_dispChart1Line(self, event):
        self.m_dispChart1Type = 'l'
        m = self.popmenu.FindItemById(self.m_popupID_dispChart1Line)
        m.Check(True)
        self.RedrawAll()

    def OnPopup_dispGrid(self, event):
        self.m_dispGrid = not self.m_dispGrid
        m = self.popmenu.FindItemById(self.m_popupID_dispGrid)
        m.Check(self.m_dispGrid)
        self.m_hasGrid = self.m_dispGrid
        self.RedrawAll()

    def OnPopup_dispLegend(self, event):
        self.m_dispLegend = not self.m_dispLegend
        m = self.popmenu.FindItemById(self.m_popupID_dispLegend)
        m.Check(self.m_dispLegend)
        self.m_hasLegend = self.m_dispLegend
        self.RedrawAll()

    def OnPopup_dispSto(self, event):
        self.m_dispSto = not self.m_dispSto
        m = self.popmenu.FindItemById(self.m_popupID_dispSto)
        m.Check(self.m_dispSto)
        self.RedrawAll()

    def OnPopup_dispRSI14(self, event):
        self.m_dispRSI14 = not self.m_dispRSI14
        m = self.popmenu.FindItemById(self.m_popupID_dispRSI14)
        m.Check(self.m_dispRSI14)
        self.RedrawAll()

    def OnPopup_dispMA150(self, event):
        self.m_dispMA150 = not self.m_dispMA150
        m = self.popmenu.FindItemById(self.m_popupID_dispMA150)
        m.Check(self.m_dispMA150)
        self.RedrawAll()

    def OnPopup_dispBollinger(self, event):
        self.m_dispBollinger = not self.m_dispBollinger
        m = self.popmenu.FindItemById(self.m_popupID_dispBollinger)
        m.Check(self.m_dispBollinger)
        self.RedrawAll()

    def OnPopup_dispOverlaidVolume(self, event):
        self.m_dispOverlaidVolume = not self.m_dispOverlaidVolume
        m = self.popmenu.FindItemById(self.m_popupID_dispOverlaidVolume)
        m.Check(self.m_dispOverlaidVolume)
        self.m_hasChart1Vol = self.m_dispOverlaidVolume
        self.RedrawAll()

    def getPeriod(self):
        return self.zoomPeriod[self.zoomLevel]

    def getMultiple(self):
        return self.zoomMultiple[self.zoomLevel]

    def getTextPeriod(self):
        return '{} {} {}'.format(message('graph_period'), self.getPeriod(), message('graph_days'))

    def ChartRealize(self):
        # special case __x
        if self.m_quote.m_daytrades is None:
            return

        if self.m_dispRSI14 or self.m_dispSto:
            nchart = 3
        else:
            nchart = 2
        self.BeginCharting(nchart)

        end = self.m_nIndex + 1
        begin = end - self.zoomPeriod[self.zoomLevel]
        min = self.m_quote.firstindex()
        if begin<min:
            begin = min

        self.times = []
        self.idx = []
        num = 0

        for i in range(begin, end):
            if self.m_quote.m_daytrades.has_trade(i):
                num = num + 1
            dt = gCal.date(i)
            if dt:
                d = date2num(dt)
                self.times.append(d)
                self.idx.append(i)
                if self.m_dispRSI14:
                    self.m_quote.m_daytrades.rsi14(i)
                if self.m_dispSto:
                    self.m_quote.m_daytrades.stoK(i)
                    self.m_quote.m_daytrades.stoD(i)
                self.m_quote.m_daytrades.ma(20,i)
                self.m_quote.m_daytrades.ma(50,i)
                self.m_quote.m_daytrades.ma(100,i)
                if self.m_dispMA150:
                    self.m_quote.m_daytrades.ma(150,i)
                self.m_quote.m_daytrades.vma(15,i)
                self.m_quote.m_daytrades.ovb(i)
                if self.m_dispBollinger:
                    self.m_quote.m_daytrades.bollinger(i,0)

        # self.m_quote.m_daytrades.m_[begin:end]
        # print('ChartRealize: begin:', begin, ' end:', end, ' num:', num)

        if num > 0:
            if self.m_dispChart1Type == 'c':
                lc = mf.candlestick2(self.chart1, self.m_quote.m_daytrades.m_inOpen[begin:end], self.m_quote.m_daytrades.m_inClose[begin:end], self.m_quote.m_daytrades.m_inHigh[begin:end], self.m_quote.m_daytrades.m_inLow[begin:end], colorup='g', alpha=1.0)
            elif self.m_dispChart1Type == 'l':
                lc = mf.plot_day_summary3(self.chart1, self.m_quote.m_daytrades.m_inClose[begin:end])
            elif self.m_dispChart1Type == 'o':
                lc = mf.plot_day_summary2(self.chart1, self.m_quote.m_daytrades.m_inOpen[begin:end], self.m_quote.m_daytrades.m_inClose[begin:end], self.m_quote.m_daytrades.m_inHigh[begin:end], self.m_quote.m_daytrades.m_inLow[begin:end])
            else:
                lc = None

            self.chart1.plot(self.m_quote.m_daytrades.m_ma50[begin:end],'r',scalex = False, label='MMA(50)')
            self.chart1.plot(self.m_quote.m_daytrades.m_ma100[begin:end],'b',scalex = False, label='MMA(100)')
            if self.m_dispMA150:
                self.chart1.plot(self.m_quote.m_daytrades.m_ma150[begin:end],'c',scalex = False, label='MMA(150)')

            if self.m_dispBollinger:
                self.chart1.plot(self.m_quote.m_daytrades.m_bollM[begin:end],'m--',scalex = False, label='MMA(20)')
                self.chart1.plot(self.m_quote.m_daytrades.m_bollUp[begin:end],'k',scalex = False)
                self.chart1.plot(self.m_quote.m_daytrades.m_bollDn[begin:end],'k',scalex = False)
            else:
                self.chart1.plot(self.m_quote.m_daytrades.m_ma20[begin:end],'m',scalex = False, label='MMA(20)')

            if self.m_dispOverlaidVolume:
                mf.volume_overlay(self.chart1vol, self.m_quote.m_daytrades.m_inClose[begin-1:end], self.m_quote.m_daytrades.m_inVol[begin-1:end], colorup='g', alpha=0.5)
            #l5 = self.chart1vol.plot(self.m_quote.m_daytrades.m_ovb[begin:end],'k')

            mf.volume_overlay(self.chart2, self.m_quote.m_daytrades.m_inClose[begin-1:end], self.m_quote.m_daytrades.m_inVol[begin-1:end], colorup='g')
            lvma15, = self.chart2.plot(self.m_quote.m_daytrades.m_vma15[begin:end], 'r', antialiased=False, linewidth=0.05, scalex=False, label='VMA(15)')
            lovb, = self.chart2vol.plot(self.m_quote.m_daytrades.m_ovb[begin:end], 'k', antialiased=False, linewidth=0.05, label='OVB')
            #index_bar(self.chart2, self.m_quote.m_daytrades.m_inVol[begin:end], facecolor='g', edgecolor='k', width=4,alpha=1.0)

            if self.m_dispRSI14:
                self.chart3.plot(self.m_quote.m_daytrades.m_rsi14[begin:end], 'k', antialiased=False, linewidth=0.05, label='RSI(14)')

            if self.m_dispSto:
                self.chart3.plot(self.m_quote.m_daytrades.m_stoK[begin:end], 'b', antialiased=False, linewidth=0.05, scalex = False, label='Sto %K')
                self.chart3.plot(self.m_quote.m_daytrades.m_stoD[begin:end], 'm--', antialiased=False, linewidth=0.05, scalex = False, label='Sto %D')

            if self.m_dispLegend:
                old = matplotlib.rcParams['lines.antialiased']
                matplotlib.rcParams['lines.antialiased']=False

                self.legend1 = self.chart1.legend(loc='upper left', numpoints=2, borderpad=0, borderaxespad=0,
                                                  labelspacing=0)

                self.legend2 = self.chart2.legend((lvma15, lovb), ('VMA(15)', 'OVB'), loc='upper left', numpoints=2, borderpad=0, borderaxespad=0, labelspacing=0)
#                self.legend2 = self.chart2.legend(loc='upper left', numpoints=2, borderpad=0, borderaxespad=0, labelspacing=0)
                self.legend3 = self.chart3.legend(loc='upper left', numpoints=2, borderpad=0, borderaxespad=0,
                                                  labelspacing=0)

                matplotlib.rcParams['lines.antialiased']=old

            left, top = 0.005, 1.005
            t = self.chart1.text(left, top, self.GetPeriod(1), fontsize = 7, transform = self.chart1.transAxes)

            left, top = 0.450, 1.005
            t = self.chart1.text(left, top, self.getTextPeriod(), fontsize = 7, transform = self.chart1.transAxes)

            left, top = 0.950, 1.005
            t = self.chart1.text(left, top, self.GetPeriod(-1), fontsize = 7, transform = self.chart1.transAxes)

        if self.m_quote.isTraded():
            self.chartUPL(self.m_quote.nv_pru())

        self.EndCharting()

    def GetPeriod(self,idxtime):
        dt = self.GetTime(idxtime)
        return dt.strftime(' %Y ')

    def GetXLabel(self, idxtime):
        dt = self.GetTime(idxtime)
        return dt.strftime(' %x ')

    def GetTime(self, idxtime):
        return gCal.date(self.GetIndexTime(idxtime))

    def GetIndexTime(self, idxtime):
        if idxtime < 0:
            idxtime = len(self.idx)+idxtime
        elif idxtime == 0:
            idxtime = len(self.idx)/2
        elif idxtime >= len(self.idx):
            idxtime = len(self.idx)-1
        return self.idx[idxtime]

    def GetYLabel(self, ax, value):
        if ax == self.chart1:
            return ' {:.2f} '.format(value)
        elif self.m_hasChart1Vol and (ax == self.chart1vol):
            return ' {} '.format(fmtVolumeFunc(value, 1))
        elif ax == self.chart2:
            return ' {} '.format(fmtVolumeFunc(value, 1))
        elif self.m_hasChart2Vol and (ax == self.chart2vol):
            return ' {} '.format(fmtVolumeFunc(value, 1))
        elif ax == self.chart3:
            return ' {:.2f}% '.format(value)
        else:
            return ' unknown axis '

    def space(self, msg, val):
        l = len(msg)
        m = max(22, len(self.m_quote.name()))
        while (l + len(val)) < m:
            val = ' ' + val
        return msg + val

    def GetXYLabel(self, ax, data):
        idx = self.idx[data[0]]
        dt = gCal.date(idx)
        chart = self.axe2chart(ax)
        if self.m_quote.m_daytrades.has_trade(idx):
            s = 'k, ' + self.m_quote.name() + ' ('+ dt.strftime('%x') + ') \n'
            s = s + 'k, '+ self.space(message('popup_open'), self.m_quote.sv_open(dt)) + ' \n'
            s = s + 'k, '+ self.space(message('popup_high'), self.m_quote.sv_high(dt)) + ' \n'
            s = s + 'k, '+ self.space(message('popup_low'), self.m_quote.sv_low(dt)) + ' \n'
            s = s + 'k, '+ self.space(message('popup_close'), self.m_quote.sv_close(dt)) + ' \n'
            s = s + 'k, '+ self.space(message('popup_percent').format(self.m_quote.sv_percent(dt)), self.m_quote.sv_unitvar(dt)) + ' \n'
            s = s + 'k, '+ self.space(message('popup_volume'), self.m_quote.sv_volume(dt)) + ' \n'
            if chart == 3:
                if self.m_dispRSI14:
                    s = s + 'k, '+ self.space('RSI ({})'.format(14), self.m_quote.sv_rsi(14,dt)) + ' \n'
                if self.m_dispSto:
                    s = s + 'b, '+ self.space('STO %K ({})'.format(14), self.m_quote.sv_stoK(dt)) + ' \n'
                    s = s + 'm, '+ self.space('STO %D ({})'.format(14), self.m_quote.sv_stoD(dt)) + ' \n'
            elif chart == 2:
                s = s + 'r, '+ self.space('VMA{}'.format(15), self.m_quote.sv_vma(15,dt)) + ' \n'
                s = s + 'k, '+ self.space('OVB', self.m_quote.sv_ovb(dt)) + ' \n'
            else:
                s = s + 'm, '+ self.space('MA{}'.format(20), self.m_quote.sv_ma(20,dt)) + ' \n'
                s = s + 'r, '+ self.space('MA{}'.format(50), self.m_quote.sv_ma(50,dt)) + ' \n'
                s = s + 'b, '+ self.space('MA{}'.format(100), self.m_quote.sv_ma(100,dt)) + ' \n'
                if self.m_dispMA150:
                    s = s + 'c, '+ self.space('MA{}'.format(150), self.m_quote.sv_ma(150,dt)) + ' \n'
        else:
            s = 'k, ' + self.m_quote.name() + ' ('+ dt.strftime('%x') + ') \n'
            s = s + 'k, ' + message('popup_notrade') + ' '

        return s

# ============================================================================
# iTradeQuoteNotebookWindow
#
#   Display Notebook on a specific quote
# ============================================================================

class iTradeQuoteNotebookWindow(wx.Notebook):

    ID_PAGE_GRAPH = 0
    ID_PAGE_LIVE = 1
    ID_PAGE_INTRADAY = 2
    ID_PAGE_NEWS = 3
    ID_PAGE_ANALYSIS = 4
    ID_PAGE_TABLE = 5
    ID_PAGE_PROP = 6

    def __init__(self, parent, id, size, quote, page=0, *args, **kwargs):
        wx.Notebook.__init__(self, parent=parent, id=id, pos=wx.DefaultPosition, size=size, style=wx.SIMPLE_BORDER|wx.NB_TOP, *args, **kwargs)
        self.m_quote = None
        self.m_parent = parent
        self.m_port = parent.portfolio()
        self.m_curpage = page
        page = self.init(quote, page, fromInit=True)
        wx.EVT_NOTEBOOK_PAGE_CHANGED(self, self.GetId(), self.OnPageChanged)
        self.SetSelection(n=page)

    def portfolio(self):
        return self.m_port

    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        if itrade_config.verbose:
            print()
            print(u'QuoteNotebookWindow::OnPageChanged: old={:d} new={:d} sel={:d}'.format(old, new, sel))
        if old != new:
            if old >= 0:
                self.win[old].DonePage()
            if new >= 0:
                self.m_curpage = new
                self.win[new].InitPage()
        event.Skip()

    def init(self, nquote=None, page=0, fromInit=False):
        # check new quote
        if nquote != self.m_quote:
            self.m_quote = nquote

            # regenerate pages with the new quote
            self.win = {}
            self.DeleteAllPages()

            self.win[self.ID_PAGE_GRAPH] = iTradeQuoteGraphPanel(parent=self, quote=self.m_quote)
            self.AddPage(self.win[self.ID_PAGE_GRAPH], message('quote_graphdaily'))

            self.win[self.ID_PAGE_LIVE] = iTradeQuoteLivePanel(parent=self, gparent=self.m_parent, id=wx.ID_ANY, quote=self.m_quote)
            self.AddPage(self.win[self.ID_PAGE_LIVE], message('quote_live'))

            # found the right URL for intraday charting
            m = self.m_quote.market()
            if yahoosuffix(market=self.m_quote.market(), place=self.m_quote.place()):
                suffix = yahoosuffix(market=self.m_quote.market(), place=self.m_quote.place())
            else:
                suffix = ''
            if '^' in self.m_quote.ticker():
                suffix = ''

            if m:
                url = itrade_config.intradayGraphUrl[m]
                isin = itrade_config.intradayGraphUrlUseISIN[m]

                if isin:
                    url = url.format(self.m_quote.isin())
                else:
                    url = url.format(self.m_quote.ticker()+suffix)
            else:
                # chart not available because no url
                url = ''

            self.win[self.ID_PAGE_INTRADAY] = iTradeHtmlPanel(parent=self, id=wx.ID_ANY, url=url)
            self.AddPage(self.win[self.ID_PAGE_INTRADAY], message('quote_intraday'))

            self.win[self.ID_PAGE_NEWS] = iTradeRSSPanel(self, wx.ID_ANY, self.m_quote)
            self.AddPage(self.win[self.ID_PAGE_NEWS], message('quote_news'))

            self.win[self.ID_PAGE_ANALYSIS] = iTradeQuoteAnalysisPanel(self, wx.ID_ANY, self.m_quote)
            self.AddPage(self.win[self.ID_PAGE_ANALYSIS], message('quote_analysis'))

            self.win[self.ID_PAGE_TABLE] = iTradeQuoteTablePanel(self, wx.ID_ANY, self.m_quote)
            self.AddPage(self.win[self.ID_PAGE_TABLE], message('quote_table'))

            self.win[self.ID_PAGE_PROP] = iTradeQuotePropertiesPanel(self, wx.ID_ANY, self.m_quote, self)
            self.AddPage(self.win[self.ID_PAGE_PROP], message('quote_properties'))

            # be sure to init & display the selected page
            if fromInit:
                self.win[page].InitPage()

            return page

    def refresh(self, nquote=None, live=False):
        if nquote:
            # refresh the new quote
            if itrade_config.verbose:
                print(u'QuoteNotebookWindow::refresh Init New Quote : {} - page: {}'.format(nquote.ticker(), self.m_curpage))
            page = self.init(nquote=nquote, page=self.m_curpage)
            if itrade_config.verbose:
                print(u'QuoteNotebookWindow::refresh Internal Page : {} - page: {}'.format(nquote.ticker(), page))
            self.SetSelection(n=page)
        else:
            # refresh current page
            if (self.m_curpage == self.ID_PAGE_LIVE) or (not live):
                if itrade_config.verbose:
                    print('QuoteNotebookWindow::refresh Current Quote {} live={} page: {}'.format(self.m_quote.ticker(), live, self.m_curpage))
                self.win[self.m_curpage].refresh()

    def OnRefresh(self, event=None):
        # called by a child to refresh the book on the current quote (after importing for example)
        if itrade_config.verbose:
            print()
            print('QuoteNotebookWindow::OnRefresh')

        # tp force the refresh
        nquote = self.m_quote
        self.m_quote = None
        self.refresh(nquote)

# ============================================================================
# iTradeQuoteWindow
#
# Container to display information and panels on a specific quote
# ============================================================================


class iTradeQuoteWindow(wx.Frame, iTrade_wxFrame, iTrade_wxLiveMixin):
    def __init__(self, parent, port, quote, dpage=0, *args, **kwargs):
        wx.Frame.__init__(self, parent=None, size=(800, 480), style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE, *args, **kwargs)
        iTrade_wxFrame.__init__(self, parent=parent, name='view', hasStatusBar=False, *args, **kwargs)
        iTrade_wxLiveMixin.__init__(self)

        # store linked information
        self.m_quote = quote
        self.m_parent = parent
        self.m_port = port

        # register live mechanism (-> OnLive handler must be implemented)
        self.registerLive(quote,itrade_config.refreshLive)

        # fix title
        self.setTitle()

        # info + panels
        self.m_infowindow = iTradeQuoteInfoWindow(parent=self, id=wx.ID_ANY, size=wx.DefaultSize, quote=self.m_quote)
        self.m_notewindow = iTradeQuoteNotebookWindow(parent=self, id=wx.ID_ANY, size=wx.DefaultSize, quote=self.m_quote, page=dpage)

        # handlers
        wx.EVT_WINDOW_DESTROY(self, self.OnDestroy)
        wx.EVT_SIZE(self, self.OnSize)
        EVT_UPDATE_LIVE(self, self.OnLive)

    # ---[ Linked information accessors ] -------------------------------------

    def portfolio(self):
        return self.m_port

    def parent(self):
        return self.m_parent

    def quote(self):
        return self.m_quote

    # ---[ Change the current window title ] ----------------------------------

    def setTitle(self):
        self.SetTitle(title=u"{} {} - {} : {}".format(message('quote_title'), self.m_quote.key(), self.m_quote.ticker(), self.m_quote.name()))

    # ---[ Select a new quote ] -----------------------------------------------

    def SelectQuote(self, nquote=None):
        if not nquote:
            nquote = select_iTradeQuote(self, self.m_quote, filter=True)
        if nquote and nquote != self.m_quote:
            if itrade_config.verbose:
                print()
                print('QuoteWindow::SelectQuote: {} -> {} {}'.format(self.m_quote.ticker(), nquote.ticker(), nquote.key()))
            self.stopLive(self.m_quote)
            self.unregisterLive(self.m_quote)
            self.m_notewindow.Hide()
            self.m_quote = nquote
            self.registerLive(self.m_quote, itrade_config.refreshLive)
            self.setTitle()
            self.refresh(self.m_quote)
            self.m_notewindow.Show()

    # ---[ Refresh mechanism ] ------------------------------------------------

    def refresh(self, nquote=None, live=False):
        if itrade_config.verbose:
            print('QuoteWindow::refresh {} {}: live={}'.format(self.m_quote.ticker(), self.m_quote.key(), live))
        self.m_infowindow.refresh(nquote, live)
        self.m_notewindow.refresh(nquote, live)

    def OnLive(self, evt):
        # be sure this quote is still under population
        if evt.quote == self.m_quote and self.isRunning(evt.quote):
            if itrade_config.verbose:
                print('QuoteWindow::OnLive {} {}: {}'.format(evt.quote.ticker(), evt.quote.key(), evt.param))
            self.refresh(live=True)
        else:
            if itrade_config.verbose:
                print('QuoteWindow::OnLive {} {}: {} - NOT RUNNING'.format(evt.quote.ticker(), evt.quote.key(), evt.param))

    # ---[ Default Windows handlers ] -----------------------------------------

    # Default OnSize handler
    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.m_infowindow.SetDimensions(0, 0, 129, h)
        self.m_notewindow.SetDimensions(130, 0, w-130, h)
        event.Skip()

    # Default OnDestroy handler
    def OnDestroy(self, evt):
        if self.GetId() == evt.GetId():
            # stop & unregister live
            self.stopLive(self.m_quote)
            self.unregisterLive(self.m_quote)

            # remove view from the parent stack
            if self.m_parent:
                self.m_parent.m_hView = None

    # Default OnExit handler
    def OnExit(self, evt):
        # save any configuration
        self.saveConfig()

        # close the view
        self.Close()

# ============================================================================
# open_iTradeQuote
#
#   win     parent window
#   quote   Quote object or ISIN reference to view
#   page    page to select
# ============================================================================

def open_iTradeQuote(win, port, quote, page=0):
    if not isinstance(quote, Quote):
        quote = quotes.lookupKey(quote)
    if win and win.m_hView:
        # set focus
        win.m_hView.SelectQuote(quote)
        win.m_hView.SetFocus()
    else:
        frame = iTradeQuoteWindow(parent=win, port=port, quote=quote, dpage=page)
        if win:
            win.m_hView = frame
        # __w frame.plot_data()
        frame.Show()

# ============================================================================
# addInMatrix_iTradeQuote
#
#   win         parent window
#   matrix      Matrix object
#   portfolio   Portfolio object
#   dquote      (optional) Quote object or ISIN reference
# ============================================================================

def addInMatrix_iTradeQuote(win, matrix, portfolio, dquote=None):
    if dquote:
        if not isinstance(dquote, Quote):
            dquote = quotes.lookupKey(dquote)
    else:
        dquote = select_iTradeQuote(win, market=portfolio.market())

    if dquote:
        matrix.addKey(dquote.key())
        return dquote
    return None

# ============================================================================
# removeFromMatrix_iTradeQuote
#
#   win     parent window
#   matrix  Matrix object
#   quote   Quote object or ISIN reference
# ============================================================================

def removeFromMatrix_iTradeQuote(matrix, quote):
    if not isinstance(quote, Quote):
        quote = quotes.lookupKey(quote)
    if quote:
        if not quote.isTraded():
            matrix.removeKey(quote.key())
            return True
    return False

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
    # load extensions
    import itrade_ext
    itrade_ext.loadExtensions(itrade_config.fileExtData, itrade_config.dirExtData)
    # init modules
    initQuotesModule()
    itrade_config.verbose = False
    from itrade_portfolio import initPortfolioModule, loadPortfolio
    initPortfolioModule()
    port = loadPortfolio('default')
    q = quotes.lookupTicker(ticker='GTO', market='EURONEXT')
    if q:
        open_iTradeQuote(None, port, q)
        app.MainLoop()


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
