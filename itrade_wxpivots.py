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
# 2006-03-1x    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from __future__ import absolute_import
import os
import logging

# wxPython system
import wx

# iTrade system
import itrade_config
from itrade_logging import setLevel, info


class iTrade_wxPivots(wx.Panel):
    def __init__(self, parent, quote, *args, **kwargs):
        info('iTrade_wxPivots::__init__')
        wx.Panel.__init__(self, *args, **kwargs)
        self.m_quote = quote

        self.m_font = wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.SetFont(font=self.m_font)

        self.m_sizer = wx.BoxSizer(wx.VERTICAL)

        # separator
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.m_sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # r2
        box = wx.BoxSizer(wx.HORIZONTAL)

        bmp = wx.Bitmap(os.path.join(itrade_config.dirRes, 'resist2.png'))
        bbmp = wx.StaticBitmap(parent=self, bitmap=bmp, size=wx.Size(bmp.GetWidth(), bmp.GetHeight()).IncBy(5))
        box.Add(bbmp, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.s_r2 = wx.StaticText(parent=self, label='')
        box.Add(self.s_r2, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.m_sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        wx.EVT_SIZE(self, self.OnSize)

        self.SetAutoLayout(autoLayout=True)
        self.SetSizerAndFit(self.m_sizer)
        self.refresh()

    def OnSize(self, event):
        w, h = self.GetClientSizeTuple()

    def refresh(self):
        pivot = self.m_quote.ov_pivots()
        if pivot:
            s2, s1, pivot, r1, r2 = pivot
            self.s_r2.SetLabel(label=u':.2f'.format(r2))
            print('pivots:', s2, s1, pivot, r1, r2)


class WndTest(wx.Frame):
    def __init__(self, parent, quote):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title='WndTest', size=(300, 300),
                          style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)
        self.m_pivots = iTrade_wxPivots(self, quote)
        self.m_quote = quote


def main():
    setLevel(logging.INFO)
    from itrade_local import gMessage
    gMessage.setLang('us')
    gMessage.load()
    ticker = 'AXL'
    from itrade_quotes import quotes
    quote = quotes.lookupTicker(ticker=ticker)
    quote.loadTrades()
    info('{}: {}'.format(ticker, quote))
    app = wx.App()
    frame = WndTest(None, quote)
    if frame:
        frame.Show(show=True)
        app.MainLoop()


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
