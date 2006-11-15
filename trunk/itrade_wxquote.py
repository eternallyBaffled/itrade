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
# 2005-03-27    dgil  Wrote it from scratch
# 2005-04-03    dgil  Add quote selector
# 2005-05-29    dgil  Move liste quote stuff to module itrade_wxlistquote.py
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import os
import logging
import webbrowser
import datetime
import locale

# wxPython system
import itrade_wxversion
import wx

# iTrade system
from itrade_logging import *
from itrade_quotes import *
from itrade_local import message,setLocale
from itrade_config import *

from itrade_wxhtml import *
from itrade_wxmixin import iTrade_wxFrame
from itrade_wxgraph import iTrade_wxPanelGraph,fmtVolumeFunc,fmtVolumeFunc0
from itrade_wxlive import iTrade_wxLive,iTrade_wxLiveMixin,EVT_UPDATE_LIVE
from itrade_wxselectquote import select_iTradeQuote
from itrade_wxpropquote import iTradeQuotePropertiesPanel

# matplotlib system
import matplotlib
matplotlib.use('WX')
matplotlib.rcParams['numerix'] = 'numpy'

from matplotlib.dates import date2num, num2date
from myfinance import candlestick, plot_day_summary2, candlestick2, index_bar, volume_overlay2

# ============================================================================
# iTradeQuoteToolbar
#
# ============================================================================

class iTradeQuoteToolbar(wx.ToolBar):

    def __init__(self,parent,id):
        wx.ToolBar.__init__(self,parent,id,size = (120,32), style = wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        self.m_parent = parent
        self.m_Throbber = None
        self._init_toolbar()

    def _init_toolbar(self):
        self._NTB2_EXIT = wx.NewId()
        self._NTB2_SELECT = wx.NewId()
        self._NTB2_REFRESH = wx.NewId()

        self.SetToolBitmapSize(wx.Size(24,24))
        self.AddSimpleTool(self._NTB2_EXIT, wx.ArtProvider.GetBitmap(wx.ART_CROSS_MARK, wx.ART_TOOLBAR),
                           message('main_close'), message('main_desc_close'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_SELECT, wx.Bitmap('res/quotes.png'),
                           message('quote_select_title'), message('quote_select_title'))
        self.AddSimpleTool(self._NTB2_REFRESH, wx.Bitmap('res/refresh.png'),
                           message('main_view_refresh'), message('main_view_desc_refresh'))

        wx.EVT_TOOL(self, self._NTB2_EXIT, self.exit)
        wx.EVT_TOOL(self, self._NTB2_SELECT, self.select)
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

    def select(self,event):
        self.m_parent.OnSelectQuote(event)

    def exit(self,event):
        self.m_parent.OnExit(event)

# ============================================================================
# iTradeQuoteInfoWindow
#
#   Display informations on a specific quote
# ============================================================================

def exists(filename):
    try:
        f = open(filename)
        f.close()
        return True
    except:
        return False

class iTradeQuoteInfoWindow(wx.Window):

    def __init__(self,parent,id,size,quote):
        wx.Window.__init__(self,parent,id,wx.DefaultPosition, size, style=wx.SIMPLE_BORDER)
        self.m_parent = parent
        self.m_quote = quote
        self.m_logo = None

        # Toolbar
        self.m_toolbar = iTradeQuoteToolbar(self, wx.NewId())

        self.m_ticker = wx.StaticText(self, -1, "???", wx.Point(5,37), wx.Size(70, 20))

        self.m_date = wx.StaticText(self, -1, "???", wx.Point(5,65), wx.Size(140, 20))

        txt = wx.StaticText(self, -1, message('variation'), wx.Point(5,80), wx.Size(70, 20))
        self.m_percent = wx.StaticText(self, -1, "??? %", wx.Point(50,80), wx.Size(70, 20))

        txt = wx.StaticText(self, -1, message('last'), wx.Point(5,95), wx.Size(70, 20))
        self.m_last = wx.StaticText(self, -1, "???", wx.Point(50,95), wx.Size(70, 20))

        txt = wx.StaticText(self, -1, message('open'), wx.Point(5,110), wx.Size(70, 20))
        self.m_open = wx.StaticText(self, -1, "???", wx.Point(50,110), wx.Size(70, 20))

        txt = wx.StaticText(self, -1, message('high'), wx.Point(5,125), wx.Size(70, 20))
        self.m_high = wx.StaticText(self, -1, "???", wx.Point(50,125), wx.Size(70, 20))

        txt = wx.StaticText(self, -1, message('low'), wx.Point(5,140), wx.Size(70, 20))
        self.m_low = wx.StaticText(self, -1, "???", wx.Point(50,140), wx.Size(70, 20))

        txt = wx.StaticText(self, -1, message('volume'), wx.Point(5,155), wx.Size(70, 20))
        self.m_volume = wx.StaticText(self, -1, "???", wx.Point(50,155), wx.Size(70, 20))

        txt = wx.StaticText(self, -1, message('prev'), wx.Point(5,170), wx.Size(70, 20))
        self.m_prev = wx.StaticText(self, -1, "???", wx.Point(50,170), wx.Size(70, 20))

        txt = wx.StaticText(self, -1, message('cmp'), wx.Point(5,185), wx.Size(70, 20))
        self.m_cmp = wx.StaticText(self, -1, "???", wx.Point(50,185), wx.Size(70, 20))

        txt = wx.StaticText(self, -1, message('status'), wx.Point(5,225), wx.Size(70, 20))
        self.m_status = wx.StaticText(self, -1, "", wx.Point(60,225), wx.Size(70, 20))

        txt = wx.StaticText(self, -1, message('reopen'), wx.Point(5,240), wx.Size(70, 20))
        self.m_reopen = wx.StaticText(self, -1, "???", wx.Point(60,240), wx.Size(70, 20))

        txt = wx.StaticText(self, -1, message('high_threshold'), wx.Point(5,255), wx.Size(70, 20))
        self.m_high_threshold = wx.StaticText(self, -1, "???", wx.Point(60,255), wx.Size(70, 20))

        txt = wx.StaticText(self, -1, message('low_threshold'), wx.Point(5,270), wx.Size(70, 20))
        self.m_low_threshold = wx.StaticText(self, -1, "???", wx.Point(60,270), wx.Size(70, 20))

        wx.EVT_PAINT(self, self.OnPaint)
        wx.EVT_SIZE(self,self.OnSize)
        self.refresh()

    def OnSelectQuote(self,event):
        self.m_parent.SelectQuote()

    def OnRefresh(self,event):
        self.m_parent.refresh()

    def OnExit(self, evt):
        self.m_parent.OnExit(evt)

    def paintLogo(self,dc):
        if self.m_logo == None:
            bgc = self.GetBackgroundColour()
            wbrush = wx.Brush(bgc, wx.SOLID)
            wpen = wx.Pen(bgc, 1, wx.SOLID)
            dc.SetBrush(wbrush)
            dc.SetPen(wpen)
            dc.DrawRectangle(60,33,80,62)

            fn = os.path.join(itrade_config.dirImageData,'%s.gif' % self.m_quote.ticker())
            if exists(fn):
                self.m_logo = wx.Bitmap(fn)
                if self.m_logo:
                    dc.DrawBitmap(self.m_logo,60,33,False)
        else:
            dc.DrawBitmap(self.m_logo,60,33,False)

    def OnPaint(self,event):
        dc = wx.PaintDC(self)
        self.paintLogo(dc)
        event.Skip()

    def paint(self):
        # paint logo (if any)
        dc = wx.ClientDC(self)
        self.paintLogo(dc)

        # paint fields
        self.m_ticker.SetLabel(self.m_quote.ticker())
        self.m_date.SetLabel("%s | %s | %s" % (self.m_quote.sv_date(bDisplayShort=True),self.m_quote.sv_clock(),self.m_quote.sv_type_of_clock()))
        self.m_percent.SetLabel(self.m_quote.sv_percent())
        self.m_last.SetLabel("%s %s" % (self.m_quote.sv_close(),self.m_quote.currency()))
        if self.m_quote.hasTraded():
            self.m_open.SetLabel(self.m_quote.sv_open())
            self.m_high.SetLabel(self.m_quote.sv_high())
            self.m_low.SetLabel(self.m_quote.sv_low())
            self.m_volume.SetLabel(self.m_quote.sv_volume())
        else:
            self.m_open.SetLabel(" ---.-- ")
            self.m_high.SetLabel(" ---.-- ")
            self.m_low.SetLabel(" ---.-- ")
            self.m_volume.SetLabel(" ---------- ")

        self.m_prev.SetLabel(self.m_quote.sv_prevclose())
        self.m_cmp.SetLabel(self.m_quote.sv_waq())

        self.m_status.SetLabel(self.m_quote.sv_status())
        self.m_reopen.SetLabel(self.m_quote.sv_reopen())
        self.m_high_threshold.SetLabel("%.2f" % self.m_quote.high_threshold())
        self.m_low_threshold.SetLabel("%.2f" % self.m_quote.low_threshold())

    def refresh(self,nquote=None,live=False):
        info('QuoteInfoWindow::refresh %s' % self.m_quote.ticker())
        if nquote and nquote<>self.m_quote:
            self.m_quote = nquote
            self.m_logo = None
        if not live:
            self.m_quote.update()
        self.m_quote.compute()
        self.paint()

    def OnSize(self,event):
        debug('QuoteInfoWindow::OnSize')
        w,h = self.GetClientSizeTuple()
        self.m_toolbar.SetDimensions(0, 0, w, 32)

# ============================================================================
# iTradeQuoteTablePanel
#
#   Table
# ============================================================================

class iTradeQuoteTablePanel(wx.Window):

    def __init__(self,parent,id,quote):
        wx.Window.__init__(self, parent, id)
        self.m_id = id
        self.m_quote = quote
        self.m_parent = parent
        self.m_port = parent.portfolio()

    def paint(self):
        pass

    def refresh(self):
        info('QuoteTablePanel::refresh %s' % self.m_quote.ticker())
        self.paint()

# ============================================================================
# iTradeQuoteAnalysisPanel
#
#   Display Candlestick / Analysis on a specific quote
# ============================================================================

class iTradeQuoteAnalysisPanel(wx.Window):

    def __init__(self,parent,id,quote):
        wx.Window.__init__(self, parent, id)
        self.m_id = id
        self.m_quote = quote
        self.m_parent = parent
        self.m_port = parent.portfolio()

        txt = wx.StaticText(self, -1, "Candle : ", wx.Point(5,25), wx.Size(70, 20))
        self.m_candle = wx.StaticText(self, -1, "???", wx.Point(80,25), wx.Size(120, 20))

    def paint(self):
        self.m_candle.SetLabel(self.m_quote.ov_candle().__str__())

    def refresh(self):
        info('QuoteAnalysisPanel::refresh %s' % self.m_quote.ticker())
        self.paint()

# ============================================================================
# iTradeQuoteGraphPanel
# ============================================================================

class iTradeQuoteGraphPanel(wx.Panel,iTrade_wxPanelGraph):
    def __init__(self, parent, id, quote):
        wx.Panel.__init__(self, parent, id)
        iTrade_wxPanelGraph.__init__(self, parent, id, size=(5,4))

        self.m_id = id
        self.m_quote = quote
        self.m_nIndex = self.m_quote.lastindex()
        #print 'm_nIndex=',self.m_nIndex

        self.zoomPeriod = (20,40,80,160)
        self.zoomIncPeriod = (5,10,20,40)
        self.zoomWidth = (9,6,3,2)
        self.zoomLevel = 2
        self.zoomMaxLevel = len(self.zoomPeriod)-1

        # settings
        self.m_dispMA150 = False
        self.m_dispBollinger = True
        self.m_dispOverlaidVolume = False
        self.m_dispLegend = True
        self.m_dispGrid = True
        self.m_dispChart1Type = 'c'

        # parameter iTrade_wxPanelGraph
        self.m_hasChart1Vol = self.m_dispOverlaidVolume
        self.m_hasChart2Vol = True
        self.m_hasGrid = self.m_dispGrid
        self.m_hasLegend = self.m_dispLegend

        #
        self.ChartRealize()

    def OnPaint(self,event=None):
        #debug('iTradeQuoteGraphPanel:OnPaint()')
        if not event:
            self.ChartRealize()
        self.erase_cursor()
        self.canvas.draw()
        if event:
            event.Skip()

    def OnHome(self,event):
        self.m_nIndex = self.m_quote.lastindex()
        self.zoomLevel = 2
        self.OnPaint()

    def OnPanLeft(self,event):
        if self.m_nIndex > self.zoomPeriod[self.zoomLevel]:
            self.m_nIndex = self.m_nIndex - self.zoomIncPeriod[self.zoomLevel]
            if self.m_nIndex <= self.zoomPeriod[self.zoomLevel]:
                self.m_nIndex = self.zoomPeriod[self.zoomLevel]
            self.OnPaint()

    def OnPanRight(self,event):
        if self.m_nIndex < self.m_quote.lastindex():
            self.m_nIndex = self.m_nIndex + self.zoomIncPeriod[self.zoomLevel]
            if self.m_nIndex >= self.m_quote.lastindex():
                self.m_nIndex = self.m_quote.lastindex()
            self.OnPaint()

    def OnZoomOut(self,event):
        if self.zoomLevel < self.zoomMaxLevel:
            self.zoomLevel = self.zoomLevel + 1
            if self.zoomLevel > self.zoomMaxLevel:
                self.zoomLevel = self.zoomMaxLevel
            self.OnPaint()

    def OnZoomIn(self,event):
        if self.zoomLevel > 0:
            self.zoomLevel = self.zoomLevel - 1
            if self.zoomLevel < 0:
                self.zoomLevel = 0
            self.OnPaint()

    def OnConfig(self,event):
        if not hasattr(self, "m_popupID_dispMA150"):
            self.m_popupID_dispMA150 = wx.NewId()
            wx.EVT_MENU(self, self.m_popupID_dispMA150, self.OnPopup_dispMA150)
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
        i = self.popmenu.AppendCheckItem(self.m_popupID_dispBollinger, message('quote_popup_dispBollinger'))
        i.Check(self.m_dispBollinger)
        self.popmenu.AppendSeparator()
        i = self.popmenu.AppendCheckItem(self.m_popupID_dispOverlaidVolume, message('quote_popup_dispOverlaidVolume'))
        i.Check(self.m_dispOverlaidVolume)

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.m_toolbar.PopupMenu(self.popmenu, wx.Point(self.x, self.y))
        self.popmenu.Destroy()

    def OnPopup_dispChart1Candlestick(self,event):
        self.m_dispChart1Type = 'c'
        m = self.popmenu.FindItemById(self.m_popupID_dispChart1Candlestick)
        m.Check(True)
        self.OnPaint()

    def OnPopup_dispChart1OHLC(self,event):
        self.m_dispChart1Type = 'o'
        m = self.popmenu.FindItemById(self.m_popupID_dispChart1OHLC)
        m.Check(True)
        self.OnPaint()

    def OnPopup_dispChart1Line(self,event):
        self.m_dispChart1Type = 'l'
        m = self.popmenu.FindItemById(self.m_popupID_dispChart1Line)
        m.Check(True)
        self.OnPaint()

    def OnPopup_dispGrid(self,event):
        self.m_dispGrid = not self.m_dispGrid
        m = self.popmenu.FindItemById(self.m_popupID_dispGrid)
        m.Check(self.m_dispGrid)
        self.m_hasGrid = self.m_dispGrid
        self.OnPaint()

    def OnPopup_dispLegend(self,event):
        self.m_dispLegend = not self.m_dispLegend
        m = self.popmenu.FindItemById(self.m_popupID_dispLegend)
        m.Check(self.m_dispLegend)
        self.m_hasLegend = self.m_dispLegend
        self.OnPaint()

    def OnPopup_dispMA150(self,event):
        self.m_dispMA150 = not self.m_dispMA150
        m = self.popmenu.FindItemById(self.m_popupID_dispMA150)
        m.Check(self.m_dispMA150)
        self.OnPaint()

    def OnPopup_dispMA150(self,event):
        self.m_dispMA150 = not self.m_dispMA150
        m = self.popmenu.FindItemById(self.m_popupID_dispMA150)
        m.Check(self.m_dispMA150)
        self.OnPaint()

    def OnPopup_dispBollinger(self,event):
        self.m_dispBollinger = not self.m_dispBollinger
        m = self.popmenu.FindItemById(self.m_popupID_dispBollinger)
        m.Check(self.m_dispBollinger)
        self.OnPaint()

    def OnPopup_dispOverlaidVolume(self,event):
        self.m_dispOverlaidVolume = not self.m_dispOverlaidVolume
        m = self.popmenu.FindItemById(self.m_popupID_dispOverlaidVolume)
        m.Check(self.m_dispOverlaidVolume)
        self.m_hasChart1Vol = self.m_dispOverlaidVolume
        self.OnPaint()

    def getPeriod(self):
        return self.zoomPeriod[self.zoomLevel]

    def getTextPeriod(self):
        return '%s %s %s' % (message('graph_period'),self.getPeriod(),message('graph_days'))

    def ChartRealize(self):
        self.BeginCharting()

        n = self.m_nIndex

        delta = 0
        begin = n
        end = n + 1
        #print 'begin=',begin
        while (begin>0) and (delta<self.zoomPeriod[self.zoomLevel]):
            if self.m_quote.m_daytrades.m_date.has_key(begin):
                delta = delta + 1
            begin = begin - 1

        opens = []
        closes = []
        highs = []
        lows = []
        volumes = []
        times = []
        idx = []
        ma20 = []
        ma50 = []
        ma100 = []
        ma150 = []
        vma = []
        ovb = []
        bollup = []
        bollm = []
        bolldn = []
        for i in range(begin,end): # n-self.zoomPeriod[self.zoomLevel]+1
            if self.m_quote.m_daytrades.m_date.has_key(i):
                dt = self.m_quote.m_daytrades.m_date[i]
                d = date2num(dt)
                o = self.m_quote.m_daytrades.m_inOpen[i]
                c = self.m_quote.m_daytrades.m_inClose[i]
                h = self.m_quote.m_daytrades.m_inHigh[i]
                l = self.m_quote.m_daytrades.m_inLow[i]
                v = self.m_quote.m_daytrades.m_inVol[i]
                #print begin,end,i
                #o,h,l,c,v = [float(val) for val in o,h,l,c,v]
                opens.append(o)
                closes.append(c)
                highs.append(h)
                lows.append(l)
                volumes.append(v)
                times.append(d)
                idx.append(i)
                ma50.append(self.m_quote.m_daytrades.ma(50,i))
                ma100.append(self.m_quote.m_daytrades.ma(100,i))
                if self.m_dispMA150:
                    ma150.append(self.m_quote.m_daytrades.ma(150,i))
                vma.append(self.m_quote.m_daytrades.vma(15,i))
                ovb.append(self.m_quote.m_daytrades.ovb(i))
                if self.m_dispBollinger:
                    bollm.append(self.m_quote.m_daytrades.bollinger(i,1))
                    bollup.append(self.m_quote.m_daytrades.bollinger(i,2))
                    bolldn.append(self.m_quote.m_daytrades.bollinger(i,0))
                else:
                    ma20.append(self.m_quote.m_daytrades.ma(20,i))
            else:
                debug('***************** %d ' % i)

        self.times = times[1:]
        self.idx = idx[1:]
        debug('len(self.times)==%d' % len(self.times))

        if len(opens)>1:

            if self.m_dispChart1Type == 'c':
                lc = candlestick2(self.chart1, opens[1:], closes[1:], highs[1:], lows[1:], width = self.zoomWidth[self.zoomLevel], colorup = 'g', colordown = 'r', alpha=1.0)
            elif self.m_dispChart1Type == 'l':
                lc = self.chart1.plot(closes[1:],'k',antialiased=False,linewidth=0.08)
            elif self.m_dispChart1Type == 'o':
                lc = plot_day_summary2(self.chart1, opens[1:], closes[1:], highs[1:], lows[1:], ticksize=self.zoomWidth[self.zoomLevel], colorup='k', colordown='r')
            else:
                lc = None

            if not self.m_dispBollinger:
                lma20 = self.chart1.plot(ma20[1:],'m')
            lma50 = self.chart1.plot(ma50[1:],'r')
            lma100 = self.chart1.plot(ma100[1:],'b')
            if self.m_dispMA150:
                lma150 = self.chart1.plot(ma150[1:],'c')

            #x = concatenate ( ( self.times,self.times[::-1]) )
            #y = concatenate ( ( bollup,bolldn[::-1] ) )
            #p = self.chart1.fill(x,y,'g')
            if self.m_dispBollinger:
                lma20 = self.chart1.plot(bollm[1:],'m--')
                lu = self.chart1.plot(bollup[1:],'k')
                ld = self.chart1.plot(bolldn[1:],'k')

            if self.m_dispOverlaidVolume:
                volume_overlay2(self.chart1vol, closes, volumes, colorup='g', colordown='r', width=self.zoomWidth[self.zoomLevel]+1,alpha=0.5)
            #l5 = self.chart1vol.plot(ovb,'k')

            volume_overlay2(self.chart2, closes, volumes, colorup='g', colordown='r', width=self.zoomWidth[self.zoomLevel]+1,alpha=1.0)
            lvma15 = self.chart2.plot(vma[1:],'r',antialiased=False,linewidth=0.08)
            lovb = self.chart2vol.plot(ovb[1:],'k',antialiased=False,linewidth=0.08)
            #index_bar(self.chart2, volumes, facecolor='g', edgecolor='k', width=4,alpha=1.0)

            if self.m_dispLegend:
                if self.m_dispMA150:
                    self.legend1 = self.chart1.legend((lma20, lma50, lma100, lma150), ('MA20','MA50','MA100','MA150'), 2) #'upper left'
                else:
                    self.legend1 = self.chart1.legend((lma20, lma50, lma100), ('MA20','MA50','MA100'), 2) #'upper left'

                self.legend2 = self.chart2.legend((lvma15, lovb), ('VMA15', 'OVB'), 2) #'upper left'

            left, top = 0.005, 1.005
            t = self.chart1.text(left, top, self.GetPeriod(1), fontsize = 7, transform = self.chart1.transAxes)

            left, top = 0.450, 1.005
            t = self.chart1.text(left, top, self.getTextPeriod(), fontsize = 7, transform = self.chart1.transAxes)

            left, top = 0.950, 1.005
            t = self.chart1.text(left, top, self.GetPeriod(-1), fontsize = 7, transform = self.chart1.transAxes)

        self.EndCharting()

    def GetPeriod(self,idxtime):
        dt = self.GetTime(idxtime)
        return dt.strftime(' %Y ')

    def GetXLabel(self,idxtime):
        dt = self.GetTime(idxtime)
        return dt.strftime(' %x ')

    def GetTime(self,idxtime):
        if idxtime<0:
            idxtime = len(self.idx)+idxtime
        elif idxtime==0:
            idxtime = len(self.idx)/2
        return self.m_quote.m_daytrades.m_date[self.idx[idxtime]]

    def GetYLabel(self,ax,value):
        if ax==self.chart1:
            return ' %.2f ' % value
        elif self.m_hasChart1Vol and (ax==self.chart1vol):
            return ' %s ' % fmtVolumeFunc(value,1)
        elif ax==self.chart2:
            return ' %s ' % fmtVolumeFunc(value,1)
        elif self.m_hasChart2Vol and (ax==self.chart2vol):
            return ' %s ' % fmtVolumeFunc(value,1)
        else:
           return ' unknown axis '

#"Time: %f\n Price:%f\nYOUPIE" %

    def space(self,msg,val):
        l = len(msg)
        m = max(22,len(self.m_quote.name()))
        while (l+len(val))<m:
            val = ' ' + val
        return msg+val

    def GetXYLabel(self,ax,data):
        dt = self.m_quote.m_daytrades.m_date[self.idx[data[0]]]
        s = 'k, ' + self.m_quote.name() + ' ('+ dt.strftime('%x') + ') \n'
        s = s + 'k, '+ self.space(message('popup_open'), self.m_quote.sv_open(dt)) + ' \n'
        s = s + 'k, '+ self.space(message('popup_high'), self.m_quote.sv_high(dt)) + ' \n'
        s = s + 'k, '+ self.space(message('popup_low'), self.m_quote.sv_low(dt)) + ' \n'
        s = s + 'k, '+ self.space(message('popup_close'), self.m_quote.sv_close(dt)) + ' \n'
        s = s + 'k, '+ self.space(message('popup_percent') % self.m_quote.sv_percent(dt), self.m_quote.sv_unitvar(dt)) + ' \n'
        s = s + 'k, '+ self.space(message('popup_volume') , self.m_quote.sv_volume(dt)) + ' \n'
        if ax == self.chart2:
            s = s + 'r, '+ self.space('VMA%s'%15, self.m_quote.sv_vma(15,dt)) + ' \n'
            s = s + 'k, '+ self.space('OVB', self.m_quote.sv_ovb(dt)) + ' \n'
        else:
            s = s + 'm, '+ self.space('MA%s'%20, self.m_quote.sv_ma(20,dt)) + ' \n'
            s = s + 'r, '+ self.space('MA%s'%50, self.m_quote.sv_ma(50,dt)) + ' \n'
            s = s + 'b, '+ self.space('MA%s'%100, self.m_quote.sv_ma(100,dt)) + ' \n'
            if self.m_dispMA150:
                s = s + 'c, '+ self.space('MA%s'%150, self.m_quote.sv_ma(150,dt)) + ' \n'
        return s

# ============================================================================
# iTradeQuoteNotebookWindow
#
#   Display Notebook on a specific quote
# ============================================================================

class iTradeQuoteNotebookWindow(wx.Notebook):

    def __init__(self,parent,id,size,quote,page):
        wx.Notebook.__init__(self,parent,id,wx.DefaultPosition, size, style=wx.SIMPLE_BORDER|wx.NB_TOP)
        self.m_quote = None
        self.m_parent = parent
        self.m_port = parent.portfolio()
        self.m_curpage = 0
        self.ID_PAGE_LIVE = 99
        page = self.init(quote,page)
        wx.EVT_NOTEBOOK_PAGE_CHANGED(self, self.GetId(), self.OnPageChanged)
        wx.EVT_NOTEBOOK_PAGE_CHANGING(self, self.GetId(), self.OnPageChanging)
        self.SetSelection(page)

    def portfolio(self):
        return self.m_port

    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        info('OnPageChanged,  old:%d, new:%d, sel:%d\n' % (old, new, sel))
        if old<>new:
            if old==self.ID_PAGE_LIVE:
                self.m_parent.stopLive(self.m_quote)
            if new==self.ID_PAGE_LIVE:
                self.m_parent.startLive(self.m_quote)
            self.m_curpage = new
            self.win[self.m_curpage].refresh()
        event.Skip()

    def OnPageChanging(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        info('OnPageChanging, old:%d, new:%d, sel:%d\n' % (old, new, sel))
        event.Skip()

    def init(self,nquote=None,page=1):
        if nquote<>self.m_quote:
            self.m_quote = nquote

            self.win = {}
            self.DeleteAllPages()

            page = page - 1
            self.ID_PAGE_GRAPH = 0
            if self.m_quote.liveconnector().hasNotebook():
                self.ID_PAGE_LIVE = 1
                self.ID_PAGE_INTRADAY = 2
            else:
                # connector for this quote can't manage notebook/lasttrades :-(
                self.ID_PAGE_LIVE = 99
                self.ID_PAGE_INTRADAY = 1
                if page>0: page = page - 1
            self.ID_PAGE_NEWS = self.ID_PAGE_INTRADAY+1
            self.ID_PAGE_ANALYSIS = self.ID_PAGE_NEWS+1
            self.ID_PAGE_TABLE = self.ID_PAGE_ANALYSIS+1
            self.ID_PAGE_PROP = self.ID_PAGE_TABLE+1

            self.win[self.ID_PAGE_GRAPH] = iTradeQuoteGraphPanel(self,wx.NewId(),self.m_quote)
            self.AddPage(self.win[self.ID_PAGE_GRAPH], message('quote_graphdaily'))

            if self.ID_PAGE_LIVE<>99:
                self.win[self.ID_PAGE_LIVE] = iTrade_wxLive(self,self.m_quote)
                self.AddPage(self.win[self.ID_PAGE_LIVE], message('quote_live'))

            url = itrade_config.intradayGraphUrl[self.m_quote.market()]
            isin = itrade_config.intradayGraphUrlUseISIN[self.m_quote.market()]

            if isin:
                url = url % self.m_quote.isin()
            else:
                url = url % self.m_quote.ticker()

            self.win[self.ID_PAGE_INTRADAY] = iTradeHtmlPanel(self,wx.NewId(), url)
            self.AddPage(self.win[self.ID_PAGE_INTRADAY], message('quote_intraday'))

            self.win[self.ID_PAGE_NEWS] = iTradeRSSPanel(self,wx.NewId(),self.m_quote)
            self.AddPage(self.win[self.ID_PAGE_NEWS], message('quote_news'))

            self.win[self.ID_PAGE_ANALYSIS] = iTradeQuoteAnalysisPanel(self,wx.NewId(),self.m_quote)
            self.AddPage(self.win[self.ID_PAGE_ANALYSIS], message('quote_analysis'))

            self.win[self.ID_PAGE_TABLE] = iTradeQuoteTablePanel(self,wx.NewId(),self.m_quote)
            self.AddPage(self.win[self.ID_PAGE_TABLE], message('quote_table'))

            self.win[self.ID_PAGE_PROP] = iTradeQuotePropertiesPanel(self,wx.NewId(),self.m_quote)
            self.AddPage(self.win[self.ID_PAGE_PROP], message('quote_properties'))

            return page

    def refresh(self,nquote=None,live=False):
        if nquote:
            # refresh the new quote
            info('QuoteNotebookWindow::refresh %s new quote' % self.m_quote.ticker())
            self.init(nquote)
        else:
            # refresh current page
            info('QuoteNotebookWindow::refresh %s live=%d page=%d' % (self.m_quote.ticker(),live,self.m_curpage))
            if (self.m_curpage==self.ID_PAGE_LIVE) or (not live):
                print 'LIVE'
                self.win[self.m_curpage].refresh()

# ============================================================================
# iTradeQuoteWindow
#
# ============================================================================

class iTradeQuoteWindow(wx.Frame,iTrade_wxFrame,iTrade_wxLiveMixin):

    def __init__(self,parent,id,port,quote,dpage=1):
        self.m_id = wx.NewId()
        wx.Frame.__init__(self,None,self.m_id, size = ( 800,480), style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
        iTrade_wxFrame.__init__(self,parent,'view',hasStatusBar=False)
        iTrade_wxLiveMixin.__init__(self)
        self.m_quote = quote
        self.m_parent = parent
        self.m_port = port
        self.registerLive(quote,itrade_config.refreshLive)

        # fix title
        self.setTitle()

        # info + panels
        self.m_infowindow = iTradeQuoteInfoWindow(self, -1, size=wx.DefaultSize ,quote=self.m_quote)
        self.m_notewindow = iTradeQuoteNotebookWindow(self, -1, size=wx.DefaultSize ,quote=self.m_quote, page=dpage)

        wx.EVT_WINDOW_DESTROY(self, self.OnDestroy)
        wx.EVT_SIZE(self, self.OnSize)
        EVT_UPDATE_LIVE(self, self.OnLive)

    def OnLive(self, evt):
        # be sure this quote is still under population
        if self.isRunning(evt.quote):
            info('%s: %s' % (evt.quote.key(),evt.param))
            self.refresh(live=True)
        else:
            info('%s: %s - bad' % (evt.quote.key(),evt.param))

    def portfolio(self):
        return self.m_port

    def OnSize(self, event):
        debug('QuoteWindow::OnSize')
        w,h = self.GetClientSizeTuple()
        self.m_infowindow.SetDimensions(0, 0, 130, h)
        self.m_notewindow.SetDimensions(130, 0, w-130, h)
        self.setTitle()
        event.Skip(False)

    def setTitle(self):
        w,h = self.GetClientSizeTuple()
        self.SetTitle("%s %s - %s : %s (%d,%d)" % (message('quote_title'),self.m_quote.key(),self.m_quote.ticker(),self.m_quote.name(),w,h))

    def SelectQuote(self,nquote=None):
        if not nquote:
            nquote = select_iTradeQuote(self,self.m_quote,filter=True,market=None)
        if nquote and nquote<>self.m_quote:
            info('SelectQuote: %s - %s' % (nquote.ticker(),nquote.key()))
            self.stopLive(self.m_quote)
            self.unregisterLive(self.m_quote)
            self.m_notewindow.Hide()
            self.m_quote = nquote
            self.refresh(self.m_quote)
            self.registerLive(self.m_quote,itrade_config.refreshLive)
            self.setTitle()
            self.m_notewindow.Show()

    def refresh(self,nquote=None,live=False):
        info('QuoteWindow::refresh %s' % self.m_quote.ticker())
        self.m_infowindow.refresh(nquote,live)
        self.m_notewindow.refresh(nquote,live)

    def OnDestroy(self, evt):
        self.stopLive(self.m_quote)
        self.unregisterLive(self.m_quote)
        if self.m_parent and (self.m_id == evt.GetId()):
            self.m_parent.m_hView = None

    def OnExit(self, evt):
        self.saveConfig()
        self.Close()

# ============================================================================
# open_iTradeQuote
#
#   win     parent window
#   quote   Quote object or ISIN reference to view
#   page    page to select
# ============================================================================

def open_iTradeQuote(win,port,quote,page=1):
    if not isinstance(quote,Quote):
        quote = quotes.lookupKey(quote)
    if win and win.m_hView:
        # set focus
        win.m_hView.SelectQuote(quote)
        win.m_hView.SetFocus()
    else:
        frame = iTradeQuoteWindow(win, -1,port,quote,page)
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

def addInMatrix_iTradeQuote(win,matrix,portfolio,dquote=None):
    if dquote:
        if not isinstance(dquote,Quote):
            dquote = quotes.lookupKey(dquote)
    else:
        dquote = select_iTradeQuote(win,dquote=None,filter=False,market=portfolio.market())

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

def removeFromMatrix_iTradeQuote(win,matrix,quote):
    if not isinstance(quote,Quote):
        quote = quotes.lookupKey(quote)
    if quote:
        if not quote.isTraded():
            matrix.removeKey(quote.key())
            return True
    return False

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    app = wx.PySimpleApp()

    from itrade_local import *
    setLang('us')
    gMessage.load()

    q = quotes.lookupTicker('SAF','EURONEXT')
    if q:
        open_iTradeQuote(None,None,q)
        app.MainLoop()

# ============================================================================
# That's all folks !
# ============================================================================
