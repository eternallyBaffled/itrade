#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxpivots.py
#
# Description: wxPython "Points Pivots"
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
# 2006-03-1x    dgil  Wrote it from scratch
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

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_local import message

# ============================================================================
# iTrade_wxPivots
# ============================================================================

class iTrade_wxPivots(wxPanel):
    def __init__(self, parent,quote):
        info('iTrade_wxPivots::__init__')
        wxPanel.__init__(self,parent,-1)
        self.m_parent = parent
        self.m_quote = quote

        self.m_font = wxFont(10, wxMODERN, wxNORMAL, wxNORMAL)
        self.SetFont(self.m_font)

        self.m_sizer = wxBoxSizer(wxVERTICAL)

        # separator
        box = wxBoxSizer(wxHORIZONTAL)
        self.m_sizer.AddSizer(box, 0, wxGROW|wxALIGN_CENTER_VERTICAL|wxALL, 5)

        # r2
        box = wxBoxSizer(wxHORIZONTAL)

        bmp = wxBitmap('res/resist2.gif')
        bbmp = wxStaticBitmap(self, -1, bmp, size=wxSize(bmp.GetWidth()+5, bmp.GetHeight()+5))
        box.Add(bbmp, 0, wxALIGN_CENTRE|wxALL, 5)

        self.s_r2 = wxStaticText(self, -1, '')
        box.Add(self.s_r2, 0, wxALIGN_CENTRE|wxALL, 5)

        self.m_sizer.AddSizer(box, 0, wxGROW|wxALIGN_CENTER_VERTICAL|wxALL, 5)

        EVT_SIZE(self, self.OnSize)

        self.SetAutoLayout(True)
        self.SetSizerAndFit(self.m_sizer)
        self.refresh()

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()

    def refresh(self):
        pivot = self.m_quote.ov_pivots()
        if pivot:
            s2,s1,pivot,r1,r2 = pivot
            self.s_r2.SetLabel('%.2f'%r2)
            print 'pivots:',s2,s1,pivot,r1,r2
        pass

# ============================================================================
# WndTest
#
# ============================================================================

if __name__=='__main__':

    class WndTest(wxFrame):
        def __init__(self, parent,quote):
            wxFrame.__init__(self,parent,wxNewId(), 'WndTest', size = (300,300), style=wxDEFAULT_FRAME_STYLE|wxNO_FULL_REPAINT_ON_RESIZE)
            self.m_pivots = iTrade_wxPivots(self,quote)
            self.m_quote = quote

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    from itrade_local import *
    setLang('us')
    gMessage.load()

    ticker = 'AXL'

    from itrade_quotes import *
    quote = quotes.lookupTicker(ticker)
    quote.loadTrades()
    info('%s: %s' % (ticker,quote))

    app = wxPySimpleApp()

    frame = WndTest(None,quote)
    if frame:
        frame.Show(True)
        app.MainLoop()

# ============================================================================
# That's all folks !
# ============================================================================
