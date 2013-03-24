#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxlabel.py
#
# Description: wxPython label (popup on panel)
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
import logging
import string

# itrade system
from itrade_logging import *
import itrade_config

# wxPython system
if not itrade_config.nowxversion:
    import itrade_wxversion
import wx

# itrade wxPython system
from itrade_wxutil import MatplotColorToRGB

# ============================================================================
# iTrade_wxLabelPopup()
# ============================================================================

class iTrade_wxLabelPopup(object):
    def __init__(self,parent,pos,max=None,label='',multiline=False):
        dc = self.InitPaint(parent,pos,max)
        if multiline:
            self.MultiLines(dc,label)
        else:
            self.SimpleLine(dc,label)

    def SimpleLine(self,dc,label):
        textExtent = self.parent.GetFullTextExtent(label, self.font)
        self.BeginPaint(dc,textExtent[0], textExtent[1])
        dc.DrawText(label, 0, 0)
        self.EndPaint(dc)

    def MultiLines(self,dc,label):
        # split the lines
        lines = label.split('\n')

        # detect color information for the line
        nlines = []
        for eachLine in lines:
            idx = string.find(eachLine,',')
            if idx>=0:
                debug('idx=%d line=%s color=%s' %(idx,eachLine[idx+1:],eachLine[:idx]))
                nlines.append((eachLine[idx+1:],MatplotColorToRGB(eachLine[:idx])))
            else:
                nlines.append((eachLine,MatplotColorToRGB('k')))

        # calculate space to display the string
        tx = 0
        ty = 0
        for eachLine in nlines:
            textExtent = self.parent.GetFullTextExtent(eachLine[0], self.font)
            tx = max(tx,textExtent[0])
            ty = ty + textExtent[1] + 2

        # display each line with the right color
        self.BeginPaint(dc,tx,ty)
        y = 0
        for eachLine in nlines:
            textExtent = self.parent.GetFullTextExtent(eachLine[0], self.font)
            dc.SetTextForeground(eachLine[1])
            dc.DrawText(eachLine[0], 0, y)
            y = y + textExtent[1] + 2
        self.EndPaint(dc)

    def InitPaint(self,parent,pos,max):
        self.pos = wx.Point(*pos)
        if max:
            self.max = wx.Point(*max)
        else:
            self.max = None
        self.parent = parent
        self.font = wx.Font(8, wx.ROMAN, wx.NORMAL, wx.NORMAL)
        self.bg = wx.NamedColor("YELLOW")
        return wx.MemoryDC()

    def BeginPaint(self,dc,w,h):
        if self.max:
            if (self.pos.x + w + 16) > self.max.x:
                self.pos.x = self.pos.x - w - 16
            else:
                self.pos.x = self.pos.x + 16

            if (self.pos.y + h + 16) > self.max.y:
                self.pos.y = self.pos.y - h - 16
            else:
                self.pos.y = self.pos.y + 16

        self.bmp = wx.EmptyBitmap(w,h)
        dc.SelectObject(self.bmp)
        dc.SetBackground(wx.Brush(self.bg, wx.SOLID))
        dc.Clear()
        dc.SetTextForeground(wx.BLACK)
        dc.SetFont(self.font)
        dc.BeginDrawing()
        dc.DrawRectangle(0, 0, self.bmp.GetWidth(),self.bmp.GetHeight())

    def EndPaint(self,dc):
        dc.SelectObject(wx.NullBitmap)
        dc.EndDrawing()
        mask = wx.Mask(self.bmp, self.bg)
        self.bmp.SetMask(mask)

    def GetRect(self):
        return wx.Rect(self.pos.x, self.pos.y, self.bmp.GetWidth(), self.bmp.GetHeight())

    def Draw(self):
        dc = wx.ClientDC(self.parent)
        memDC = wx.MemoryDC()

        # save previous bmp
        self.prevbmp = wx.EmptyBitmap(self.bmp.GetWidth(), self.bmp.GetHeight())
        memDC.SelectObject(self.prevbmp)
        memDC.Blit(0, 0, self.bmp.GetWidth(), self.bmp.GetHeight(), dc, self.pos.x, self.pos.y, wx.COPY, True)

        # put new bmp
        memDC.SelectObject(self.bmp)
        dc.Blit(self.pos.x, self.pos.y,self.bmp.GetWidth(), self.bmp.GetHeight(),memDC, 0, 0, wx.COPY, True)

    def Remove(self):
        if self.prevbmp:
            dc = wx.ClientDC(self.parent)
            memDC = wx.MemoryDC()
            memDC.SelectObject(self.prevbmp)
            dc.Blit(self.pos.x, self.pos.y,self.prevbmp.GetWidth(), self.prevbmp.GetHeight(),memDC, 0, 0, wx.COPY, True)
            del self.prevbmp
        del self.pos
        del self.bmp

# ============================================================================
# DrawRectLabel
#   dc          display context
#   label       text to display
#   x,y         position in dc
#   w,h         width and height of the box (textextend)
#   colorpen    wx.Color for Text Foreground
#   colorbg     wx.Color for Background
#   font        wx.Font for Text drawing
#   vert        'top','center','bottom'
#   horz        'left','right','center'
# ============================================================================

def DrawRectLabel(dc,label,x,y,w,h,colorpen,colorbg,font,vert='top',horz='center'):

    memDC = wx.MemoryDC()
    bmp = wx.EmptyBitmap(w,h)

    memDC.SelectObject(bmp)
    memDC.SetBackground(wx.Brush(colorbg, wx.SOLID))
    memDC.Clear()
    memDC.SetTextForeground(colorpen)
    memDC.SetFont(font)
    memDC.BeginDrawing()
    memDC.DrawRectangle(0, 0, bmp.GetWidth(),bmp.GetHeight())
    memDC.DrawText(label, 0, 0)
    #memDC.SelectObject(wx.NullBitmap)
    memDC.EndDrawing()

    #mask = wx.Mask(bmp, bg)
    #bmp.SetMask(mask)
    #memDC.SelectObject(bmp)

    if vert=='top':
        y = y - h + 1
    if vert=='center':
        y = y - (h/2) + 1

    if horz=='left':
        x = x - w
    if horz=='center':
        x = x - (w/2)

    dc.Blit(x, y, bmp.GetWidth(), bmp.GetHeight(),memDC, 0, 0, wx.COPY, True)

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    app = wx.PySimpleApp()
    app.MainLoop()

# ============================================================================
# That's all folks !
# ============================================================================
