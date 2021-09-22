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
# 2005-10-26    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
import os

# iTrade system
from itrade_logging import debug, info
from itrade_local import message
import itrade_config

# wxPython system
if not itrade_config.nowxversion:
    import itrade_wxversion
import wx

# iTrade wxPython system
from itrade_wxlabel import iTrade_wxLabelPopup, DrawRectLabel
from itrade_wxprint import iTrade_wxPanelPrint as PanelPrint, CanvasPrintout

# matplotlib system
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, MultipleLocator
from matplotlib.pyplot import setp
from matplotlib.dates import IndexDateFormatter

# ============================================================================
# GTool
# ============================================================================

GTOOL_IND = 0
GTOOL_HLINE = 1
GTOOL_VLINE = 2
GTOOL_OLINE = 3
GTOOL_FIBO = 4
GTOOL_UPL = 254
GTOOL_TRASH = 255


class GTool(object):
    def __init__(self, kind, parent, canvas):
        self.m_kind = kind
        self.m_parent = parent
        self.m_canvas = canvas

    def kind(self):
        return self.m_kind

    def parent(self):
        return self.m_parent

    def canvas(self):
        return self.m_canvas

    def on_click(self, x, y, time, val, chart):
        info(u'Tool {} on_click x:{:d},y:{:d} time={} val={} chart={:d}!'.format(self.kind(), x, y, time, val, chart))

    def is_cursor_state(self, chart):
        return True


class GToolInd(GTool):
    def __init__(self, parent, canvas):
        super(GToolInd, self).__init__(kind=GTOOL_IND, parent=parent, canvas=canvas)

    def is_cursor_state(self, chart):
        return True


class GToolHLine(GTool):
    def __init__(self, parent, canvas):
        super(GToolHLine, self).__init__(kind=GTOOL_HLINE, parent=parent, canvas=canvas)

    def is_cursor_state(self, chart):
        return True

    def on_click(self, x, y, time, val, chart):
        # create the object
        obj = (self, chart, time, val)

        # stack it
        self.m_parent.stackObject(obj)

        # draw it
        self.m_parent.drawObject(obj)

    def draw(self, parent, dc, obj, rect):
        # obj: (self,chart,time,val)
        # rect: (left,top,right,bottom,width,height)
        axe = parent.chart2axe(obj[1])

        a,b = axe.get_ylim()
        y = rect[3] - int((obj[3] - a) * (rect[5] / (b-a)))

        # print('rect:', rect, 'y range:', a, b, b-a, ' val=', obj[3], (obj[3] - a), ' y=', y)
        if rect[3] >= y >= rect[1]:
            lc = wx.NamedColour("BLACK")
            bg = "BLUE"
            font = wx.Font(8, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

            dc.SetPen(wx.Pen(lc, 1, wx.PENSTYLE_SOLID))
            dc.DrawLine(rect[0], y, rect[2], y)

            label = parent.GetYLabel(axe, obj[3])
            textExtent = self.m_parent.GetFullTextExtent(label, font)

            DrawRectLabel(dc, label, rect[0], y, textExtent[0], textExtent[1], lc, bg, font, vert='top', horz='right')


class GToolUPL(GTool):
    def __init__(self, parent, canvas):
        super(GToolUPL, self).__init__(kind=GTOOL_UPL, parent=parent, canvas=canvas)

    def is_cursor_state(self, chart):
        return True

    def on_click(self, x, y, time, val, chart):
        # do nothing
        pass

    def draw(self, parent, dc, obj, rect):
        # obj: (self,chart,time,val)
        # rect: (left,top,right,bottom,width,height)
        axe = parent.chart2axe(obj[1])

        a, b = axe.get_ylim()
        y = rect[3] - int((obj[3] - a) * (rect[5] / (b-a)))

        # print('rect:', rect, 'y range:', a, b, b-a, ' val=', obj[3], (obj[3] - a), ' y=', y)
        if rect[3] >= y >= rect[1]:
            lc = wx.NamedColour("BLACK")
            bg = "RED"
            font = wx.Font(8, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

            dc.SetPen(wx.Pen(lc, 1, wx.PENSTYLE_SOLID))
            dc.DrawLine(rect[0], y, rect[2], y)

            label = parent.GetYLabel(axe, obj[3])
            textExtent = self.m_parent.GetFullTextExtent(label, font)

            DrawRectLabel(dc, label, rect[0], y, textExtent[0], textExtent[1], lc, bg, font, vert='top', horz='right')


class GToolVLine(GTool):
    def __init__(self, parent, canvas):
        super(GToolVLine, self).__init__(kind=GTOOL_VLINE, parent=parent, canvas=canvas)

    def is_cursor_state(self,chart):
        return True

    def on_click(self, x, y, time, val, chart):
        # create the object
        obj = (self,chart,time,val,self.m_parent.GetIndexTime(0),self.m_parent.getPeriod())

        # stack it
        self.m_parent.stackObject(obj)

        # draw it
        self.m_parent.drawObject(obj)

    def draw(self,parent,dc,obj,rect):
        # obj: (self, chart, time, val, offtime, periodtime)
        # rect: (left, top, right, bottom, width, height)
        axe = parent.chart2axe(obj[1])
        time = obj[2]

        #print 'time',time,' initial:',obj[4],' current:',parent.GetIndexTime(0),' new time:',obj[4] - parent.GetIndexTime(0) + time
        time = obj[4]-parent.GetIndexTime(0)+time

        # update time on the grid
        a,b = axe.get_xlim()
        period = b - a

        #print 'period:',period,' inital period:',obj[5],' delta:',obj[5]-period, ' new time:',time - (obj[5]-period) / 2

        time = time - int((obj[5]-period) / 2)

        if a <= time <= b:
            x = rect[0] + int( (time - a) * (rect[4] / period) )

            #print 'rect:',rect,'x range:',a,b,b-a,' val=',time,(time - a),' x=',x

            lc = wx.NamedColour("BLACK")
            bg = "BLUE"
            font = wx.Font(8, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

            dc.SetPen(wx.Pen(lc, 1, wx.PENSTYLE_SOLID))
            dc.DrawLine(x, rect[1], x, rect[3])

            label = parent.GetXLabel(time)
            textExtent = self.m_parent.GetFullTextExtent(label,font)

            DrawRectLabel(dc,label,x,rect[3], textExtent[0], textExtent[1],lc,bg,font,vert='bottom',horz='center')


class GToolOLine(GTool):
    def __init__(self, parent, canvas):
        super(GToolOLine, self).__init__(kind=GTOOL_OLINE, parent=parent, canvas=canvas)

    def is_cursor_state(self, chart):
        return True


class GToolFibo(GTool):
    def __init__(self, parent, canvas):
        super(GToolFibo, self).__init__(kind=GTOOL_FIBO, parent=parent, canvas=canvas)

    def is_cursor_state(self, chart):
        # Fibo supported only in main chart
        if chart != 1:
            return False
        return True


class GToolTrash(GTool):
    def __init__(self, parent, canvas):
        super(GToolTrash, self).__init__(kind=GTOOL_TRASH, parent=parent, canvas=canvas)

    def is_cursor_state(self, chart):
        return True

    def on_click(self, x, y, time, val, chart):
        lst = self.m_parent.listObjects()

# ============================================================================
# GObject
# ============================================================================

class GObject(object):
    def __init__(self, canvas):
        self.m_canvas = canvas
        self.objects = []

    def listObjects(self):
        return self.objects

    def stackObject(self, obj):
        self.objects.append(obj)

    def unstackObject(self, obj):
        self.objects.remove(obj)

    def removeAllObjects(self):
        self.objects = []

    def drawObject(self, obj, dc=None):
        # obj: (self,chart,time,val,...)
        axe = self.chart2axe(obj[1])

        # compute rect
        figheight = self.m_canvas.figure.bbox.height
        left,bottom,width,height = axe.bbox.bounds
        bottom = figheight-bottom
        top = bottom - height
        right = left + width

        rect = (int(left),int(top),int(right),int(bottom),int(width),int(height))

        # start drawing in the DC
        if not dc:
            dc = wx.ClientDC(self.m_canvas)
            dc.ResetBoundingBox()

        dc.BeginDrawing()

        # callback object to draw itself
        obj[0].draw(self,dc,obj,rect)

        # end of drawing in the DC
        dc.EndDrawing()

    def drawAllObjects(self, dc=None):
        for obj in self.objects:
            self.drawObject(obj, dc)

# ============================================================================
# fmtVolumeFunc
#
# Formatter function for Volumes
# ============================================================================

def fmtVolumeFunc(x, pos):
    if pos%3 == 1:
        if abs(x) >= 1000:
            if abs(x) >= 1e6:
                return '%.1f M' % (x*1e-6)
            else:
                return '%d K' % int(x*1e-3)
        else:
            return '%d' % x
    else:
        return ''

def fmtVolumeFunc0(x, pos):
    if pos%3 == 0:
        if abs(x) >= 1000:
            if abs(x) >= 1e6:
                return '%.1f M' % (x*1e-6)
            else:
                return '%d K' % int(x*1e-3)
        else:
            return '%d' % x
    else:
        return ''

# ============================================================================
# fmtPercentFunc
#
# Formatter function for Percent
# ============================================================================

def fmtPercentFunc(x,pos):
    if x==10 or x==20 or x==30 or x==40 or x==50 or x==60 or x==70 or x==80 or x==90:
        return '%d %%' % x
    else:
        return ''

# ============================================================================
# iTrade_wxToolbarGraph
# ============================================================================

class iTrade_wxToolbarGraph(wx.ToolBar):
    def __init__(self, canvas):
        self.m_parent = canvas.GetParent()
        super(iTrade_wxToolbarGraph, self).__init__(parent=self.m_parent, id=wx.ID_ANY)
        self.m_canvas = canvas
        self._init_toolbar()

    def _init_toolbar(self):
        self._NTB2_HOME = wx.NewId()
        self._NTB2_PANLEFT = wx.NewId()
        self._NTB2_PANRIGHT = wx.NewId()
        self._NTB2_ZOOMOUT = wx.NewId()
        self._NTB2_ZOOMIN = wx.NewId()
        self._NTB2_CONFIG = wx.NewId()
        self._NTB2_SAVE = wx.NewId()
        self._NTB2_PRINT = wx.NewId()
        self._NTB2_SETUP = wx.NewId()
        self._NTB2_PREVIEW = wx.NewId()

        self._NTB2_TOOL_IND   = wx.NewId()
        self._NTB2_TOOL_HLINE = wx.NewId()
        self._NTB2_TOOL_VLINE = wx.NewId()
        self._NTB2_TOOL_OLINE = wx.NewId()
        self._NTB2_TOOL_FIBO = wx.NewId()
        self._NTB2_TOOL_TRASH = wx.NewId()

        self.SetToolBitmapSize(wx.Size(24,24))
        self.AddSimpleTool(self._NTB2_HOME, wx.ArtProvider.GetBitmap(wx.ART_GO_HOME, wx.ART_TOOLBAR),
                           message('tb_home'), message('tb_home'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_PANLEFT, wx.ArtProvider.GetBitmap(wx.ART_GO_BACK, wx.ART_TOOLBAR),
                           message('tb_pan_left'), message('tb_pan_left'))
        self.AddSimpleTool(self._NTB2_PANRIGHT, wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_TOOLBAR),
                           message('tb_pan_right'), message('tb_pan_right'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_ZOOMOUT, wx.Bitmap(os.path.join(itrade_config.dirRes, 'stock_zoom-out.xpm')),
                           message('tb_zoom_out'), message('tb_zoom_out'))
        self.AddSimpleTool(self._NTB2_ZOOMIN, wx.Bitmap(os.path.join(itrade_config.dirRes, 'stock_zoom-in.xpm')),
                           message('tb_zoom_in'), message('tb_zoom_in'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_CONFIG, wx.ArtProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_TOOLBAR),
                           message('tb_config'), message('tb_config'))
        self.AddSimpleTool(self._NTB2_SAVE, wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR),
                           message('tb_save_file'), message('tb_save_file'))
        self.AddSimpleTool(self._NTB2_SETUP, wx.Bitmap(os.path.join(itrade_config.dirRes, 'printsetup.png')), message('tb_setup'), message('tb_setup'))
        self.AddSimpleTool(self._NTB2_PRINT, wx.Bitmap(os.path.join(itrade_config.dirRes, 'print.png')), message('tb_print'), message('tb_print'))
        self.AddSimpleTool(self._NTB2_PREVIEW, wx.Bitmap(os.path.join(itrade_config.dirRes, 'printpreview.png')), message('tb_preview'), message('tb_preview'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))

        self.AddRadioLabelTool(self._NTB2_TOOL_IND, '', wx.Bitmap(os.path.join(itrade_config.dirRes, 'toolind.png')), wx.NullBitmap, message('tb_tool_ind'), message('tb_tool_ind'))
        self.AddRadioLabelTool(self._NTB2_TOOL_HLINE, '', wx.Bitmap(os.path.join(itrade_config.dirRes, 'toolhline.png')), wx.NullBitmap, message('tb_tool_hline'), message('tb_tool_hline'))
        self.AddRadioLabelTool(self._NTB2_TOOL_VLINE, '', wx.Bitmap(os.path.join(itrade_config.dirRes, 'toolvline.png')), wx.NullBitmap, message('tb_tool_vline'), message('tb_tool_vline'))
        self.AddRadioLabelTool(self._NTB2_TOOL_OLINE, '', wx.Bitmap(os.path.join(itrade_config.dirRes, 'toololine.png')), wx.NullBitmap, message('tb_tool_oline'), message('tb_tool_oline'))
        self.AddRadioLabelTool(self._NTB2_TOOL_FIBO, '', wx.Bitmap(os.path.join(itrade_config.dirRes, 'toolfibo.png')), wx.NullBitmap, message('tb_tool_fibo'), message('tb_tool_fibo'))
        self.AddRadioLabelTool(self._NTB2_TOOL_TRASH, '', wx.Bitmap(os.path.join(itrade_config.dirRes, 'tooltrash.png')), wx.NullBitmap, message('tb_tool_trash'), message('tb_tool_trash'))

        wx.EVT_TOOL(self, self._NTB2_HOME, self.home)
        wx.EVT_TOOL(self, self._NTB2_PANLEFT, self.panLeft)
        wx.EVT_TOOL(self, self._NTB2_PANRIGHT, self.panRight)
        wx.EVT_TOOL(self, self._NTB2_ZOOMOUT, self.zoomOut)
        wx.EVT_TOOL(self, self._NTB2_ZOOMIN, self.zoomIn)
        wx.EVT_TOOL(self, self._NTB2_CONFIG, self.config)
        wx.EVT_TOOL(self, self._NTB2_SAVE, self.save)
        wx.EVT_TOOL(self, self._NTB2_SETUP, self.printSetup)
        wx.EVT_TOOL(self, self._NTB2_PRINT, self.doPrint)
        wx.EVT_TOOL(self, self._NTB2_PREVIEW, self.doPreview)

        wx.EVT_TOOL(self, self._NTB2_TOOL_IND, self.toolInd)
        wx.EVT_TOOL(self, self._NTB2_TOOL_HLINE, self.toolHLine)
        wx.EVT_TOOL(self, self._NTB2_TOOL_VLINE, self.toolVLine)
        wx.EVT_TOOL(self, self._NTB2_TOOL_OLINE, self.toolOLine)
        wx.EVT_TOOL(self, self._NTB2_TOOL_FIBO, self.toolFibo)
        wx.EVT_TOOL(self, self._NTB2_TOOL_TRASH, self.toolTrash)

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

    def toolInd(self,event):
        self.m_parent.OnToolInd(event)

    def toolHLine(self,event):
        self.m_parent.OnToolHLine(event)

    def toolVLine(self,event):
        self.m_parent.OnToolVLine(event)

    def toolOLine(self,event):
        self.m_parent.OnToolOLine(event)

    def toolFibo(self,event):
        self.m_parent.OnToolFibo(event)

    def toolTrash(self,event):
        self.m_parent.OnToolTrash(event)

    def save(self,event):
        filetypes, exts, filter_index = self.m_canvas._get_imagesave_wildcards()
        default_file = self.m_parent.m_quote.name() + "." + self.m_canvas.get_default_filetype()
        dlg = wx.FileDialog(self.m_parent, message('save_to_file'),
                            itrade_config.dirSnapshots, default_file, filetypes,
                            wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR)
        dlg.SetFilterIndex(filter_index)
        if dlg.ShowModal() == wx.ID_OK:
            dirname = dlg.GetDirectory()
            filename = dlg.GetFilename()
            debug('Save file dir:%s name:%s' % (dirname, filename), 3, self)
            self.m_canvas.print_figure(os.path.join(dirname, filename))
        dlg.Destroy()

    def doPreview(self,event):
        self.m_parent.OnPrintPreview(event)

    def doPrint(self, event):
        self.m_parent.OnDoPrint(event)

    def printSetup(self, event):
        self.m_parent.OnPageSetup(event)

    def set_cursor(self, cursor):
        # cursor = wx.StockCursor(cursord[cursor])
        # self.m_canvas.SetCursor( cursor )
        pass

    def update(self):
        pass

# ============================================================================
# Cursor mode
# ============================================================================

CURSOR_MODE_IND = 0
CURSOR_MODE_HLINE = 1
CURSOR_MODE_VLINE = 2
CURSOR_MODE_OLINE = 3
CURSOR_MODE_FIBO = 4
CURSOR_MODE_TRASH = 255


class FigureCanvasEx(FigureCanvas):
    """be sure the parent is able to draw all its objects"""

    def __init__(self, parent, id, figure):
        super(FigureCanvasEx, self).__init__(parent=parent, id=id, figure=figure)
        self.m_parent = parent

    def _onPaint(self, event):
        # print('$$$ _onPaint ex : call default _onPaint')
        FigureCanvas._onPaint(self, event)
        # print('$$$ _onPaint ex : call drawAllObjects in parent')
        self.m_parent.drawAllObjects()


class iTrade_wxPanelGraph(GObject, PanelPrint):
    def __init__(self, parent, id, size):
        self.m_parent = parent

        self.SetBackgroundColour("WHITE")

        # figure me
        self.figure = Figure(size, dpi = 96)
        self.m_canvas = FigureCanvasEx(self, -1, self.figure)

        super(iTrade_wxPanelGraph, self).__init__(canvas=self.m_canvas, parent=parent, po=CanvasPrintout, orientation=wx.LANDSCAPE)

        self.m_canvas.mpl_connect('motion_notify_event', self.mouse_move)
        self.m_canvas.mpl_connect('button_press_event', self.on_click)

        self.m_toolbar = iTrade_wxToolbarGraph(self.m_canvas)

        wx.EVT_LEFT_DOWN(self.m_toolbar, self.OnLeftDown)

        # Default Tool is IND
        self.OnToolInd(None)

        # default parameters
        self.m_hasChart1Vol = False
        self.m_hasChart2Vol = False

        # size everything to fit in panel
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.m_canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        sizer.Add(self.m_toolbar, 0, wx.GROW)
        self.SetSizerAndFit(sizer)
        wx.EVT_PAINT(self, self.OnPaint)

        # cursor need a timer
        self.cursorx,self.cursory = 0,0
        self.m_timer = wx.Timer(self)
        wx.EVT_TIMER(self, -1, self.OnTimer)

    # ---[ CURSOR MANAGEMENT ] -----------------------------------------------

    def set_cursor_mode(self,mode):
        self.m_cursormode = mode
        if mode == CURSOR_MODE_HLINE:
            self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_TOOL_HLINE,True)
        elif mode == CURSOR_MODE_TRASH:
            self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_TOOL_TRASH,True)
        else:
            self.m_cursormode = CURSOR_MODE_IND
            self.m_toolbar.ToggleTool(self.m_toolbar._NTB2_TOOL_IND,True)

    def cursorState(self,ax):
        # return False if something prevent cursor to show up
        if ax:
            chart = self.axe2chart(ax)
            return self.m_tool.is_cursor_state(chart)
        else:
            # Timed request : always True
            return True

    def is_display_vcursor(self):
        if self.m_cursormode == CURSOR_MODE_HLINE:
            return False
        if self.m_cursormode == CURSOR_MODE_TRASH:
            return False
        if self.m_cursormode == CURSOR_MODE_OLINE:
            return False
        if self.m_cursormode == CURSOR_MODE_FIBO:
            return False
        return True

    def is_display_hcursor(self):
        if self.m_cursormode == CURSOR_MODE_VLINE:
            return False
        if self.m_cursormode == CURSOR_MODE_TRASH:
            return False
        if self.m_cursormode == CURSOR_MODE_OLINE:
            return False
        return True

    # ---[ TOOLBOX MANAGEMENT ] ---------------------------------------------

    def OnToolInd(self,event):
        self.m_cursormode = CURSOR_MODE_IND
        self.m_tool = GToolInd(self,self.m_canvas)
        if event:
            event.Skip()

    def OnToolHLine(self,event):
        self.m_cursormode = CURSOR_MODE_HLINE
        self.m_tool = GToolHLine(self,self.m_canvas)
        if event:
            event.Skip()

    def OnToolVLine(self,event):
        self.m_cursormode = CURSOR_MODE_VLINE
        self.m_tool = GToolVLine(self,self.m_canvas)
        if event:
            event.Skip()

    def OnToolOLine(self,event):
        self.m_cursormode = CURSOR_MODE_OLINE
        self.m_tool = GToolOLine(self,self.m_canvas)
        if event:
            event.Skip()

    def OnToolFibo(self,event):
        self.m_cursormode = CURSOR_MODE_FIBO
        self.m_tool = GToolFibo(self,self.m_canvas)
        if event:
            event.Skip()

    def OnToolTrash(self,event):
        self.m_cursormode = CURSOR_MODE_TRASH
        self.m_tool = GToolTrash(self,self.m_canvas)
        if event:
            event.Skip()

    # ---[ MOUSE MANAGEMENT ] -----------------------------------------------

    def OnLeftDown(self, event):
        self.x = event.GetX()
        self.y = event.GetY()
        event.Skip()

    def OnTimer(self,event):
        #debug('OnTimer')
        if self.cursorState(None) and (self.m_cursormode == CURSOR_MODE_IND):
            #debug('OnTimer create label')
            try:
                self.m_xylabel = iTrade_wxLabelPopup(self.m_canvas,self.m_xylabelPos,self.m_xylabelMax,label=self.GetXYLabel(self.m_xylabelAxis,self.m_xylabelData),multiline=True)
            except AttributeError:
                info('axis not managed')
            else:
                #debug('OnTimer draw label')
                self.m_xylabel.Draw()

    def on_click(self,event):
        if self.cursorState(event.inaxes):
            chart = self.axe2chart(event.inaxes)
            if chart>0 and event.xdata is not None:
                self.erase_cursor()
                self.m_tool.on_click(event.x, event.y, int(event.xdata), event.ydata, chart)
                self.draw_cursor(event)

    def mouse_move(self,event):
        if self.cursorState(event.inaxes):
            # just in case mouse is bad (PinPoint :-( )
            if self.cursorx != event.x or self.cursory != event.y:
                debug('Move x:%d,y:%d!' %(event.x, event.y))
                self.m_timer.Stop()
                self.cursorx,self.cursory = event.x, event.y
                self.draw_cursor(event)
                if event.inaxes:
                    debug('Start timer x:%d,y:%d t:%d!' %(event.x, event.y,itrade_config.timerForXYPopup))
                    self.m_timer.Start(itrade_config.timerForXYPopup,oneShot=True)

    # ---[ CURSOR DRAWING during MOVE ] -----------------------------------------------------------------

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
            if self.is_display_vcursor():
                lastdc.DrawLine(*lastline1) # erase old
            if self.is_display_hcursor():
                lastdc.DrawLine(*lastline2) # erase old

    def draw_cursor(self, event):
        #event is a MplEvent.  Draw a cursor over the axes
        if event.inaxes is None:
            #info('Out !')
            self.erase_cursor()
            return

        figheight = self.m_canvas.figure.bbox.height
        ax = event.inaxes
        left,bottom,width,height = ax.bbox.bounds
        bottom = figheight-bottom
        top = bottom - height
        right = left + width
        x, y = event.x, event.y
        y = figheight-y

        time, value = event.xdata, event.ydata

        a,b = ax.get_xlim()
        period = b - a
        newx = left+((width/period)*int(time))
        #debug('newx=%d width=%d period=%d time=%d' % (newx,width,period,int(time)))

        dc = wx.ClientDC(self.m_canvas)
        dc.SetLogicalFunction(wx.XOR)
        dc.SetBrush(wx.Brush(wx.Colour(255,255,255), wx.BRUSHSTYLE_TRANSPARENT))
        dc.SetPen(wx.Pen(wx.Colour(200, 200, 200), 1, wx.PENSTYLE_SOLID))

        dc.ResetBoundingBox()
        dc.BeginDrawing()

        x, y, left, right, bottom, top = [int(val) for val in (newx, y, left, right, bottom, top)]

        self.erase_cursor()
        line1 = (x, bottom, x, top)
        line2 = (left, y, right, y)
        self.m_lastInfo = line1, line2, ax, dc

        if self.is_display_vcursor():
            dc.DrawLine(*line1) # draw new
        if self.is_display_hcursor():
            dc.DrawLine(*line2) # draw new
        #dc.EndDrawing()

        debug("Time=%d  Value=%f"% (time, value))

        # add x and y labels
        if int(time)<len(self.times):
            if self.is_display_vcursor():
                self.m_xlabel = iTrade_wxLabelPopup(self.m_canvas,(x,bottom), label=self.GetXLabel(int(time)))
                self.m_xlabel.Draw()
            if self.is_display_hcursor():
                self.m_ylabel = iTrade_wxLabelPopup(self.m_canvas,(right,y), label=self.GetYLabel(ax,value))
                self.m_ylabel.Draw()

            # save some data for Timed behaviour
            self.m_xylabelMax = (right,bottom)
            self.m_xylabelPos = (x,y)
            self.m_xylabelData = (int(time),value)
            self.m_xylabelAxis = ax

        dc.EndDrawing()

    # ---[ GRAPHING EVERYTHING ] --------------------------------------------------------------

    #def refresh(self):
    #    self.RedrawAll()

    def onEraseBackground(self, evt):
        # this is supposed to prevent redraw flicker on some X servers...
        pass

    def GetToolBar(self):
        # You will need to override GetToolBar if you are using an
        # unmanaged toolbar in your frame
        return self.m_toolbar

    def axe2chart(self, ax):
        if ax == self.chart1 or ax == self.chart1vol:
            return 1
        elif ax == self.chart2 or ax == self.chart2vol:
            return 2
        elif ax == self.chart3:
            return 3
        else:
            return 0

    def chart2axe(self, chart):
        if chart == 1:
            return self.chart1
        elif chart == 2:
            return self.chart2
        elif chart == 3:
            return self.chart3
        else:
            return None

    def chartUPL(self, strval):
        if itrade_config.verbose:
            print('chartUPL with xval=', strval)

        # create the object
        obj = (GToolUPL(self, self.m_canvas), 1, 0, strval)

        # stack it
        self.stackObject(obj)

    def BeginCharting(self, nchart=2):
        # print('BeginCharting --[')

        self.figure.clear()

        if nchart == 2:
            # left, bottom, width, height
            ra1 = [0.07, 0.20, 0.86, 0.76]
            ra1ovl = [0.07, 0.20, 0.86, 0.15]
            ra2 = [0.07, 0.02, 0.86, 0.15]
            ra2ovl = [0.07, 0.02, 0.86, 0.15]
        else:
            # left, bottom, width, height
            ra1 = [0.07, 0.38, 0.86, 0.58]
            ra1ovl = [0.07, 0.38, 0.86, 0.15]
            ra2 = [0.07, 0.20, 0.86, 0.15]
            ra2ovl = [0.07, 0.20, 0.86, 0.15]
            ra3 = [0.07, 0.02, 0.86, 0.15]

        # by default : no legend
        self.legend1 = None
        self.legend2 = None
        self.legend3 = None

        # chart1 for pricing
        self.chart1 = self.figure.add_axes(ra1)
        self.chart1.yaxis.tick_right()
        self.chart1.xaxis.set_major_locator(MultipleLocator(self.getMultiple()))
        self.chart1.grid(self.m_hasGrid)

        # chart1 for overlayed volume
        if self.m_hasChart1Vol:
            self.chart1vol = self.figure.add_axes(ra1ovl, frameon=False)
            self.chart1vol.yaxis.tick_left()
            volumeFmt = FuncFormatter(fmtVolumeFunc)
            self.chart1vol.yaxis.set_major_formatter(volumeFmt)
            self.chart1vol.xaxis.set_major_locator(MultipleLocator(self.getMultiple()))
            # self.chart1vol.grid(True)
        else:
            self.chart1vol = None

        # chart2 for volume
        self.chart2 = self.figure.add_axes(ra2)
        self.chart2.yaxis.tick_right()
        volumeFmt = FuncFormatter(fmtVolumeFunc)
        self.chart2.yaxis.set_major_formatter(volumeFmt)
        self.chart2.xaxis.set_major_locator(MultipleLocator(self.getMultiple()))
        self.chart2.grid(self.m_hasGrid)

        # chart2 for overlayed volume
        if self.m_hasChart2Vol:
            self.chart2vol = self.figure.add_axes(ra2ovl, frameon=False)
            self.chart2vol.yaxis.tick_left()
            volumeFmt = FuncFormatter(fmtVolumeFunc0)
            self.chart2vol.yaxis.set_major_formatter(volumeFmt)
            self.chart2vol.xaxis.set_major_locator(MultipleLocator(self.getMultiple()))
            # self.chart2vol.grid(True)
        else:
            self.chart2vol = None

        left, top = 0.015, 0.80
        t = self.chart2.text(left, top, message('graph_volume'), fontsize=7, transform=self.chart2.transAxes)

        if nchart == 3:
            self.chart3 = self.figure.add_axes(ra3)
            self.chart3.yaxis.tick_right()
            percentFmt = FuncFormatter(fmtPercentFunc)
            self.chart3.yaxis.set_major_formatter(percentFmt)
            self.chart3.xaxis.set_major_locator(MultipleLocator(self.getMultiple()))
            self.chart3.grid(self.m_hasGrid)
        else:
            self.chart3 = None

        # print(']-- BeginCharting')

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

        setp(self.chart1.get_xticklabels(), fontsize=7)
        setp(self.chart1.get_yticklabels(), fontsize=7)
        if self.m_hasChart1Vol:
            setp(self.chart1vol.get_yticklabels(), fontsize=7)
            setp(self.chart1vol.get_xticklabels(), fontsize=7)
        setp(self.chart2.get_xticklabels(), fontsize=7)
        setp(self.chart2.get_yticklabels(), fontsize=7)
        if self.m_hasChart2Vol:
            setp(self.chart2vol.get_xticklabels(), fontsize=7)
            setp(self.chart2vol.get_yticklabels(), fontsize=7)
        if self.chart3:
            setp(self.chart3.get_xticklabels(), fontsize=7)
            setp(self.chart3.get_yticklabels(), fontsize=7)

        # format times correctly
        self.dateFmt = IndexDateFormatter(self.times, '%d %b')
        self.chart1.xaxis.set_major_formatter(self.dateFmt)
        self.chart2.xaxis.set_major_formatter(self.dateFmt)
        if self.chart3:
            self.chart3.xaxis.set_major_formatter(self.dateFmt)
        if self.m_hasChart1Vol:
            self.chart1vol.xaxis.set_major_formatter(self.dateFmt)
        if self.m_hasChart2Vol:
            self.chart2vol.xaxis.set_major_formatter(self.dateFmt)

# ============================================================================
# That's all folks !
# ============================================================================
