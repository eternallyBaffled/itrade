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
# 2005-03-20    dgil  Wrote it from scratch
# 2006-01-2x    dgil  Split module. itrade_wxmatrix.py for matrix code !
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import os
import logging
import thread
import time

# wxPython system
import itrade_wxversion
from wxPython.wx import *

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_portfolio import loadPortfolio
from itrade_matrix import createMatrix

# iTrade wx system
from itrade_wxmatrix import iTradeMainWindow

# ============================================================================
# iTrade_SplashScreen
# ============================================================================

class iTrade_SplashScreen(wxSplashScreen):
    def __init__(self,app):
        bmp = wxImage("res/itrade.jpg").ConvertToBitmap()
        wxSplashScreen.__init__(self,bmp,wxSPLASH_CENTRE_ON_SCREEN,0,None,-1)
        EVT_CLOSE(self,self.OnClose)

        thread.start_new_thread(self.Run,())

        print '--- load current portfolio ---'
        self.m_portfolio = loadPortfolio()
        print 'Portfolio : %s:%s:%s:%s:%f ' % (self.m_portfolio.filename(),self.m_portfolio.name(),self.m_portfolio.accountref(),self.m_portfolio.market(),self.m_portfolio.vat())

        print '--- build a matrix -----------'
        self.m_matrix = createMatrix(self.m_portfolio.filename(),self.m_portfolio)

        self.m_frame = iTradeMainWindow(None, -1,self.m_portfolio,self.m_matrix)
        app.SetTopWindow(self.m_frame)

    def OnClose(self,evt):
        self.Hide()
        evt.Skip()

    def Run(self):
        time.sleep(3)
        self.Close(True)

# ============================================================================
# iTradeApp
# ============================================================================

class iTradeApp(wxApp):
    def OnInit(self):
        provider = wxSimpleHelpProvider()
        wxHelpProvider_Set(provider)

        wxSystemOptions.SetOptionInt("mac.window-plain-transition",1)
        self.m_splash = iTrade_SplashScreen(self)
        self.m_splash.Show()
        return True

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
    setLevel(logging.INFO)
    start_iTradeWindow()

# ============================================================================
# That's all folks !
# ============================================================================
