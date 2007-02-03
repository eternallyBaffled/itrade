#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxstops.py
#
# Description: wxPython Stops management (add,edit,delete)
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is	Gilles Dumortier.
#
# Portions created by the Initial Developer are Copyright (C) 2004-2007 the
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
# 2007-02-03    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import os
import logging
#import webbrowser
#import datetime
#import locale

# wxPython system
import itrade_wxversion
import wx
#import  wx.grid as gridlib

# iTrade system
from itrade_logging import *
from itrade_quotes import *
#from itrade_local import message,setLocale
#from itrade_config import *

#from itrade_wxhtml import *
#from itrade_wxmixin import iTrade_wxFrame
#from itrade_wxgraph import iTrade_wxPanelGraph,fmtVolumeFunc,fmtVolumeFunc0
#from itrade_wxlive import iTrade_wxLive,iTrade_wxLiveMixin,EVT_UPDATE_LIVE
#from itrade_wxselectquote import select_iTradeQuote
#from itrade_wxpropquote import iTradeQuotePropertiesPanel

from itrade_wxutil import iTradeYesNo

# ============================================================================

# ============================================================================
# addOrEditStops_iTradeQuote
#
#   win         parent window
#   quote       Quote object or ISIN reference
# ============================================================================

def addOrEditStops_iTradeQuote(win,quote):
    if not isinstance(quote,Quote):
        quote = quotes.lookupKey(quote)
    if quote:
        if not quote.hasStops():
            return editStops(win,quote)
    return False

# ============================================================================
# removeStops_iTradeQuote
#
#   win     parent window
#   quote   Quote object or ISIN reference
# ============================================================================

def removeStops_iTradeQuote(win,quote):
    if not isinstance(quote,Quote):
        quote = quotes.lookupKey(quote)
    if quote:
        if quote.hasStops():
            iRet = iTradeYesNo(win,message('stops_remove_text')%quote.name(),message('stops_remove_caption'))
            if iRet==wx.ID_YES:
                quotes.removeStops(quote.key())
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

# ============================================================================
# That's all folks !
# ============================================================================

