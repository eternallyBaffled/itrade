#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxmain.py
#
# Description: wxPython main
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
# 2005-03-20    dgil  Wrote it from scratch
# 2006-01-2x    dgil  Split module. itrade_wxmatrix.py for matrix code !
# 2007-01-2x    dgil  Notebook re-architecture -> itrade_wxbook.py
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
import os
import logging

# iTrade system
import itrade_config

# wxPython system
if not itrade_config.nowxversion:
    import itrade_wxversion
import wx

import itrade_logging
from itrade_portfolio import loadPortfolio
from itrade_matrix import createMatrix

# iTrade wxPython system
from itrade_wxbook import iTradeMainWindow

# ============================================================================
# iTrade_SplashScreen
# ============================================================================

class iTrade_SplashScreen(wx.SplashScreen):
    def __init__(self,app):
        image = wx.Image(os.path.join(itrade_config.dirRes, "itrade.jpg"))
        wx.SplashScreen.__init__(self,
                                image.ConvertToBitmap(),
                                wx.SPLASH_CENTRE_ON_SCREEN|wx.SPLASH_NO_TIMEOUT,
                                0, None, -1)

# ============================================================================
# iTradeApp
# ============================================================================

class iTradeApp(wx.App):
    def OnInit(self):
        splash = iTrade_SplashScreen(self)
        splash.Show()

        provider = wx.SimpleHelpProvider()
        wx.HelpProvider_Set(provider)
        wx.SystemOptions.SetOptionInt("mac.window-plain-transition", 1)
        self._init_app()

        splash.Destroy()
        return True

    def _init_app(self):
        #itrade_logging.setLevel(logging.DEBUG)
        #print '--- load current portfolio ---'
        portfolio = loadPortfolio()
        #print 'Portfolio : %s:%s:%s:%s:%f ' % (portfolio.filename(), portfolio.name(), portfolio.accountref(), portfolio.market(), portfolio.vat())

        print('--- build a matrix -----------')
        matrix = createMatrix(portfolio.filename(), portfolio)

        frame = iTradeMainWindow(None, portfolio, matrix)
        self.SetTopWindow(frame)

# ============================================================================
# start_iTradeWindow
# ============================================================================

def start_iTradeWindow():
    app = iTradeApp(False)
    app.MainLoop()

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    itrade_logging.setLevel(logging.INFO)
    start_iTradeWindow()

# ============================================================================
# That's all folks !
# ============================================================================
