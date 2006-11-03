#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxgraph.py
#
# Description: wxPython Generic Graph Panel
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
# 2005-10-26    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging

# wxPython system
import itrade_wxversion
import wx

# iTrade system
from itrade_logging import *
from itrade_local import message
from itrade_wxlabel import iTrade_wxLabel

# matplotlib system
import matplotlib
matplotlib.use('WX')
matplotlib.rcParams['numerix'] = 'numpy'

from pylab import *

from matplotlib.backends.backend_wx import FigureManager,FigureCanvasWx as FigureCanvas
#from matplotlib.backends.backend_wxagg import Toolbar, FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx,_load_bitmap

from matplotlib.figure import Figure
from matplotlib.axes import Subplot
from matplotlib.ticker import  IndexLocator, FuncFormatter, NullFormatter, MultipleLocator

# ============================================================================
# fmtVolumeFunc
#
# Formatter function for Volumes
# ============================================================================

def fmtVolumeFunc(x,pos):
    if pos%3==1:
        if abs(x)>=1000:
            if abs(x)>=1e6:
                return '%.1f M' % (x*1e-6)
            else:
                return '%d K' % int(x*1e-3)
        else:
            return '%d' % x
    else:
        return ''

def fmtVolumeFunc0(x,pos):
    if pos%3==0:
        if abs(x)>=1000:
            if abs(x)>=1e6:
                return '%.1f M' % (x*1e-6)
            else:
                return '%d K' % int(x*1e-3)
        else:
            return '%d' % x
    else:
        return ''

# ============================================================================
# iTrade_wxToolbarGraph
# ============================================================================

class iTrade_wxToolbarGraph(wx.ToolBar):
    def __init__(self, canvas):
        self.m_parent = canvas.GetParent()
        wx.ToolBar.__init__(self, self.m_parent, -1)
        self.canvas = canvas
        self._init_toolbar()

    def _init_toolbar(self):
        self._NTB2_HOME = wx.NewId()
        self._NTB2_PANLEFT = wx.NewId()
        self._NTB2_PANRIGHT = wx.NewId()
        self._NTB2_ZOOMOUT = wx.NewId()
        self._NTB2_ZOOMIN = wx.NewId()
        self._NTB2_CONFIG = wx.NewId()
        self._NTB2_SAVE = wx.NewId()

        self.SetToolBitmapSize(wx.Size(24,24))
        self.AddSimpleTool(self._NTB2_HOME, wx.ArtProvider.GetBitmap(wx.ART_GO_HOME, wx.ART_TOOLBAR),
                           message('tb_home'), message('tb_home'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_PANLEFT, wx.ArtProvider.GetBitmap(wx.ART_GO_BACK, wx.ART_TOOLBAR),
                           message('tb_pan_left'), message('tb_pan_left'))
        self.AddSimpleTool(self._NTB2_PANRIGHT, wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_TOOLBAR),
                           message('tb_pan_right'), message('tb_pan_right'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_ZOOMOUT, _load_bitmap('stock_zoom-out.xpm'),
                           message('tb_zoom_out'), message('tb_zoom_out'))
        self.AddSimpleTool(self._NTB2_ZOOMIN, _load_bitmap('stock_zoom-in.xpm'),
                           message('tb_zoom_in'), message('tb_zoom_in'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_CONFIG, wx.ArtProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_TOOLBAR),
                           message('tb_config'), message('tb_config'))
        self.AddSimpleTool(self._NTB2_SAVE, wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR),
                           message('tb_save_plot'), message('tb_save_plot'))

        wx.EVT_TOOL(self, self._NTB2_HOME, self.home)
        wx.EVT_TOOL(self, self._NTB2_PANLEFT, self.panLeft)
        wx.EVT_TOOL(self, self._NTB2_PANRIGHT, self.panRight)
        wx.EVT_TOOL(self, self._NTB2_ZOOMOUT, self.zoomOut)
        wx.EVT_TOOL(self, self._NTB2_ZOOMIN, self.zoomIn)
        wx.EVT_TOOL(self, self._NTB2_CONFIG, self.config)
        wx.EVT_TOOL(self, self._NTB2_SAVE, self.save)

        self.Realize()

    def config(self,event):
        self.m_parent.OnConfig(event)

    def home(self,event):
        self.m_parent.OnHome(event)

    def panLeft(self,event):
        self.m_parent.OnPanLeft(event)

    def panRight(self,event):
        self.m_parent.OnPanRight(event)

    def zoomOut(self,event):
        self.m_parent.OnZoomOut(event)

    def zoomIn(self,event):
        self.m_parent.OnZoomIn(event)

    def save(self,event):
        filetypes = self.canvas._get_imagesave_wildcards()
        dlg = wx.FileDialog(self.m_parent, message('save_to_file'), itrade_config.dirSnapshots, "", filetypes, wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            dirname  = dlg.GetDirectory()
            filename = dlg.GetFilename()
            debug('Save file dir:%s name:%s' % (dirname, filename))
            self.canvas.print_figure(os.path.join(dirname, filename))
        dlg.Destroy()

    def set_cursor(self, cursor):
        cursor = wx.StockCursor(cursord[cursor])
        self.canvas.SetCursor( cursor )

    def update(self):
        pass

# ============================================================================
# iTrade_wxPanelGraph
# ============================================================================

class iTrade_wxPanelGraph(object):
    def __init__(self, parent, id, size):
        self.m_parent = parent

        self.SetBackgroundColour(wx.NamedColor("WHITE"))

        # figure me
        self.figure = Figure(size, dpi = 96)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.canvas.mpl_connect('motion_notify_event', self.mouse_move)
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.toolbar = iTrade_wxToolbarGraph(self.canvas)

        wx.EVT_LEFT_DOWN(self.toolbar, self.OnLeftDown)

        # default parameters
        self.m_hasChart1Vol = False
        self.m_hasChart2Vol = False

        # size everything to fit in panel
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        sizer.Add(self.toolbar, 0, wx.GROW)
        self.SetSizerAndFit(sizer)
        wx.EVT_PAINT(self, self.OnPaint)

        # cursor need a timer
        self.cursorx,self.cursory = 0,0
        self.m_timer = wx.Timer(self)
        wx.EVT_TIMER(self, -1, self.OnTimer)

    def cursorState(self):
        # return False if something prevent cursor to show up
        return True

    def OnLeftDown(self, event):
        self.x = event.GetX()
        self.y = event.GetY()
        event.Skip()

    def OnTimer(self,event):
        debug('OnTimer')
        if self.cursorState():
            debug('OnTimer create label')
            try:
                self.m_xylabel = iTrade_wxLabel(self.canvas,self.m_xylabelPos,self.m_xylabelMax,label=self.GetXYLabel(self.m_xylabelAxis,self.m_xylabelData),multiline=True)
            except AttributeError:
                info('axis not managed')
                pass
            else:
                debug('OnTimer draw label')
                self.m_xylabel.Draw()

    def on_click(self,event):
        if self.cursorState():
            info('Click !')

    def mouse_move(self,event):
        if self.cursorState():
            # just in case mouse is bad (PinPoint :-( )
            if self.cursorx<>event.x or self.cursory<>event.y:
                debug('Move x:%d,y:%d!' %(event.x, event.y))
                self.m_timer.Stop()
                self.cursorx,self.cursory = event.x, event.y
                self.draw_cursor(event)
                if event.inaxes:
                    debug('Start timer x:%d,y:%d t:%d!' %(event.x, event.y,itrade_config.timerForXYPopup))
                    self.m_timer.Start(itrade_config.timerForXYPopup,oneShot=True)

    def erase_cursor(self):
        # erase xylabel
        try:
            xy = self.m_xylabel
            del self.m_xylabel
            del self.m_xylabelData
            del self.m_xylabelPos
            del self.m_xylabelMax
            del self.m_xylabelAxis
        except AttributeError:
            pass
        else:
            xy.Remove()

        # erase ylabel
        try:
            y = self.m_ylabel
            del self.m_ylabel
        except AttributeError:
            pass
        else:
            y.Remove()

        # erase xlabel
        try:
            x = self.m_xlabel
            del self.m_xlabel
        except AttributeError:
            pass
        else:
            x.Remove()

        # erase cursor
        try:
            lastline1, lastline2, lastax, lastdc = self.m_lastInfo
            del self.m_lastInfo
        except AttributeError:
            pass
        else:
            lastdc.DrawLine(*lastline1) # erase old
            lastdc.DrawLine(*lastline2) # erase old

    def draw_cursor(self, event):
        #event is a MplEvent.  Draw a cursor over the axes
        if event.inaxes is None:
            #info('Out !')
            self.erase_cursor()
            return

        figheight = self.canvas.figure.bbox.height()
        ax = event.inaxes
        left,bottom,width,height = ax.bbox.get_bounds()
        bottom = figheight-bottom
        top = bottom - height
        right = left + width
        x, y = event.x, event.y
        y = figheight-y

        time, value = event.xdata, event.ydata

        newx = left+((width/self.getPeriod())*int(time))
        debug('newx=%d width=%d period=%d time=%d' % (newx,width,self.getPeriod(),int(time)))

        dc = wx.ClientDC(self.canvas)
        dc.SetLogicalFunction(wx.XOR)
        wbrush = wx.Brush(wx.Colour(255,255,255), wx.TRANSPARENT)
        wpen = wx.Pen(wx.Colour(200, 200, 200), 1, wx.SOLID)
        dc.SetBrush(wbrush)
        dc.SetPen(wpen)

        dc.ResetBoundingBox()
        dc.BeginDrawing()

        x, y, left, right, bottom, top = [int(val) for val in newx, y, left, right, bottom, top]

        self.erase_cursor()
        line1 = (x, bottom, x, top)
        line2 = (left, y, right, y)
        self.m_lastInfo = line1, line2, ax, dc

        dc.DrawLine(*line1) # draw new
        dc.DrawLine(*line2) # draw new
        dc.EndDrawing()

        debug("Time=%d  Value=%f"% (time, value))

        # add x and y labels
        if int(time)<len(self.times):
            self.m_xlabel = iTrade_wxLabel(self.canvas,(x,bottom), label=self.GetXLabel(int(time)))
            self.m_xlabel.Draw()
            self.m_ylabel = iTrade_wxLabel(self.canvas,(right,y), label=self.GetYLabel(ax,value))
            self.m_ylabel.Draw()

            # save some data for Timed behaviour
            self.m_xylabelMax = (right,bottom)
            self.m_xylabelPos = (x,y)
            self.m_xylabelData = (int(time),value)
            self.m_xylabelAxis = ax

        dc.EndDrawing()

    def refresh(self):
        #self.toolbar.update() # Not sure why this is needed - ADS
        self.OnPaint()

    def onEraseBackground(self, evt):
        # this is supposed to prevent redraw flicker on some X servers...
        pass

    def GetToolBar(self):
        # You will need to override GetToolBar if you are using an
        # unmanaged toolbar in your frame
        return self.toolbar

    def BeginCharting(self):
        self.figure.clear()

        # by default : no legend
        self.legend1 = None
        self.legend2 = None
        self.legend3 = None

        # chart1 for pricing
        #                                left, bottom, width, height
        self.chart1 = self.figure.add_axes([0.07,0.22,0.86,0.73])
        self.chart1.yaxis.tick_right()
        self.chart1.xaxis.set_major_locator(MultipleLocator(10))
        self.chart1.grid(self.m_hasGrid)

        # chart1 for overlayed volume
        #                                left, bottom, width, height
        if self.m_hasChart1Vol:
            self.chart1vol = self.figure.add_axes([0.07,0.22,0.86,0.15],frameon=False)
            self.chart1vol.yaxis.tick_left()
            volumeFmt = FuncFormatter(fmtVolumeFunc)
            self.chart1vol.yaxis.set_major_formatter(volumeFmt)
            nullFmt = NullFormatter() # no labels
            self.chart1vol.xaxis.set_major_formatter(nullFmt)
            #self.chart1vol.grid(True)

        # chart2 for volume
        #                                left, bottom, width, height
        self.chart2 = self.figure.add_axes([0.07,0.02,0.86,0.15])
        self.chart2.yaxis.tick_right()
        volumeFmt = FuncFormatter(fmtVolumeFunc)
        self.chart2.yaxis.set_major_formatter(volumeFmt)
        nullFmt = NullFormatter() # no labels
        self.chart2.xaxis.set_major_formatter(nullFmt)
        self.chart2.grid(self.m_hasGrid)

        # chart2 for overlayed volume
        #                                left, bottom, width, height
        if self.m_hasChart2Vol:
            self.chart2vol = self.figure.add_axes([0.07,0.02,0.86,0.15],frameon=False)
            self.chart2vol.yaxis.tick_left()
            volumeFmt = FuncFormatter(fmtVolumeFunc0)
            self.chart2vol.yaxis.set_major_formatter(volumeFmt)
            nullFmt = NullFormatter() # no labels
            self.chart2vol.xaxis.set_major_formatter(nullFmt)
            #self.chart2vol.grid(True)

        left, top = 0.015, 0.80
        t = self.chart2.text(left, top, message('graph_volume'), fontsize = 7, transform = self.chart2.transAxes)

    def EndCharting(self):
        # adjust all font size
        if self.m_hasLegend:
            if self.legend1:
                for text in self.legend1.get_texts():
                    text.set_fontsize(7)
            if self.legend2:
                for text in self.legend2.get_texts():
                    text.set_fontsize(7)
            if self.legend3:
                for text in self.legend3.get_texts():
                    text.set_fontsize(7)

        setp(self.chart1.get_xticklabels(),fontsize=7)
        setp(self.chart1.get_yticklabels(),fontsize=7)
        if self.m_hasChart1Vol:
            setp(self.chart1vol.get_yticklabels(),fontsize=7)
        setp(self.chart2.get_yticklabels(),fontsize=7)
        if self.m_hasChart2Vol:
            setp(self.chart2vol.get_yticklabels(),fontsize=7)

        # format times correctly
        self.dateFmt =  IndexDateFormatter(self.times, '%d %b')
        self.chart1.xaxis.set_major_formatter(self.dateFmt)

# ============================================================================
# That's all folks !
# ============================================================================
