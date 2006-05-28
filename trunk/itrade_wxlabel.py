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
import string

# wxPython system
import itrade_wxversion
from wxPython.wx import *

# matplotlib system
import matplotlib
matplotlib.use('WXAgg')
matplotlib.rcParams['numerix'] = 'numarray'

# itrade system
from itrade_logging import *
from itrade_wxutil import wxMatplotColorToRGB

# ============================================================================
# iTrade_LabelPopup()
# ============================================================================

class iTrade_wxLabel(object):
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
                nlines.append((eachLine[idx+1:],wxMatplotColorToRGB(eachLine[:idx])))
            else:
                nlines.append((eachLine,wxMatplotColorToRGB('k')))

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
        self.pos = wxPoint(*pos)
        if max:
            self.max = wxPoint(*max)
        else:
            self.max = None
        self.parent = parent
        self.font = wxFont(8, wxROMAN, wxNORMAL, wxNORMAL)
        self.bg = wxNamedColor("YELLOW")
        return wxMemoryDC()

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

        self.bmp = wxEmptyBitmap(w,h)
        dc.SelectObject(self.bmp)
        dc.SetBackground(wxBrush(self.bg, wxSOLID))
        dc.Clear()
        dc.SetTextForeground(wxBLACK)
        dc.SetFont(self.font)
        dc.BeginDrawing()
        dc.DrawRectangle(0, 0, self.bmp.GetWidth(),self.bmp.GetHeight())

    def EndPaint(self,dc):
        dc.SelectObject(wxNullBitmap)
        dc.EndDrawing()
        mask = wxMaskColour(self.bmp, self.bg)
        self.bmp.SetMask(mask)

    def GetRect(self):
        return wxRect(self.pos.x, self.pos.y, self.bmp.GetWidth(), self.bmp.GetHeight())

    def Draw(self):
        dc = wxClientDC(self.parent)
        memDC = wxMemoryDC()

        # save previous bmp
        self.prevbmp = wxEmptyBitmap(self.bmp.GetWidth(), self.bmp.GetHeight())
        memDC.SelectObject(self.prevbmp)
        memDC.Blit(0, 0, self.bmp.GetWidth(), self.bmp.GetHeight(), dc, self.pos.x, self.pos.y, wxCOPY, True)

        # put new bmp
        memDC.SelectObject(self.bmp)
        dc.Blit(self.pos.x, self.pos.y,self.bmp.GetWidth(), self.bmp.GetHeight(),memDC, 0, 0, wxCOPY, True)

    def Remove(self):
        if self.prevbmp:
            dc = wxClientDC(self.parent)
            memDC = wxMemoryDC()
            memDC.SelectObject(self.prevbmp)
            dc.Blit(self.pos.x, self.pos.y,self.prevbmp.GetWidth(), self.prevbmp.GetHeight(),memDC, 0, 0, wxCOPY, True)
            del self.prevbmp
        del self.pos
        del self.bmp

# ============================================================================
# That's all folks !
# ============================================================================
# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:

