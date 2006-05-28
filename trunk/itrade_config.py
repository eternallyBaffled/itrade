#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_config.py
# Version      : $Id: itrade_config.py,v 1.42 2006/05/04 07:55:02 dgil Exp $
#
# Description: Configuration
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
# 2004-04-11    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Version management
# ============================================================================

__revision__ = "$Id: itrade_config.py,v 1.42 2006/05/04 07:55:02 dgil Exp $"
__author__ = "Gilles Dumortier (dgil@ieee.org)"
__version__ = "0.4.2"
__status__ = "alpha"
__cvsversion__ = "$Revision: 1.42 $"[11:-2]
__date__ = "$Date: 2006/05/04 07:55:02 $"[7:-2]
__copyright__ = "Copyright (c) 2004-2006 Gilles Dumortier"
__license__ = "GPL"
__credits__ = """Jeremiah Fincher (ansi colors in command line), Mark Pilgrim (Universal Feed Parser http://feedparser.org/)"""

# ============================================================================
# Imports
# ============================================================================

# python system
import os
import sys
import imp
import ConfigParser

# ============================================================================
# Default configuration
# ============================================================================

# software name
softwareName = 'iTrade'
softwareLicense = __license__
softwareAuthors = __author__
softwareCopyright = __copyright__
softwareCredits = __credits__
softwareWebsite = 'http://itrade.sourceforge.net/'

# iTrade version (major.minor)
softwareVersion = __version__
#softwareVersionName = 'Nausicaa - (unstable)'
softwareVersionName = 'Coca2 - (stable)'
softwareStatus = __status__

print '%s(%s) - %s %s' % (softwareName,softwareStatus,softwareVersion,softwareVersionName)

# connection to network
global gbDisconnected
gbDisconnected = False

# support
supportURL = 'http://itrade.sourceforge.net/support.htm'
bugTrackerURL = 'http://sourceforge.net/tracker/?group_id=128261&atid=711187'
donorsTrackerURL = 'http://sourceforge.net/donate/index.php?group_id=128261'

# use ANSI colors
useColors = False

# directory for system data
dirSysData = 'data'
if not os.path.exists(dirSysData):
    raise('invalid installation ! %s folder does not exist !' % dirSysData)

# directory for user data
dirUserData = 'usrdata'
if not os.path.exists(dirUserData):
    os.mkdir(dirUserData)

# directory for alerts
dirAlerts = 'alerts'
if not os.path.exists(dirAlerts):
    os.mkdir(dirAlerts)

# directory for quotes images
dirImageData = 'images'
if not os.path.exists(dirImageData):
    os.mkdir(dirImageData)

# directory for cache data (quote, window prop, ...)
dirCacheData = 'cache'
if not os.path.exists(dirCacheData):
    os.mkdir(dirCacheData)

# file to get the current portfolio
fileCurrentPortfolio = 'portfolio.txt'

# directory for importation
dirImport = 'import'
if not os.path.exists(dirImport):
    os.mkdir(dirImport)

# directory for snapshots
dirSnapshots = 'snapshots'
if not os.path.exists(dirSnapshots):
    os.mkdir(dirSnapshots)

# directory for trading reports
dirReports = 'reports'
if not os.path.exists(dirReports):
    os.mkdir(dirReports)

# number of trading years
numTradeYears = 12

# refresh in seconds for a view
refreshView = 6
refreshLive = 1.5

# refresh in seconds for a currency view
refreshCurrencyView = 15

# auto refresh the matrix view
default_bAutoRefreshMatrixView = True
global bAutoRefreshMatrixView
bAutoRefreshMatrixView = default_bAutoRefreshMatrixView

# auto refresh the currency view
default_bAutoRefreshCurrencyView = True
global bAutoRefreshCurrencyView
bAutoRefreshCurrencyView = default_bAutoRefreshCurrencyView

# matrix font size
default_matrixFontSize = 2
global matrixFontSize
matrixFontSize = default_matrixFontSize

# operation font size
default_operationFontSize = 2
global operationFontSize
operationFontSize = default_operationFontSize

# is data cached fresh ? (in seconds)
cachedDataFreshDelay = 3

# Taxes Threshold (in current currency)
taxesThreshold = 15000.00

# Taxes Percent
taxesPercent = 0.27

# get intraday bitmap
intradayGraphUrl = {}
intradayGraphUrlUseISIN = {}
#intradayGraphUrl['EURONEXT'] = "http://charts.production.euronext.com/i_chart.html?ISIN=%s&ID_EXCHANGE=1&QUALITY=DLY&PREV_CLOSE=1&SUPP_INFO=1&DISPLAY=1&VOL=1&GRID=1&SCALE=1"
#intradayGraphUrlUseISIN['EURONEXT'] = True
intradayGraphUrl['EURONEXT'] = "http://www.abcbourse.com/Graphes/graphe.aspx?s=%sp&m=g&t=lc"
intradayGraphUrlUseISIN['EURONEXT'] = False
intradayGraphUrl['NASDAQ'] = "http://ichart.finance.yahoo.com/b?s=%s"
intradayGraphUrlUseISIN['NASDAQ'] = False
intradayGraphUrl['NYSE'] = "http://ichart.finance.yahoo.com/b?s=%s"
intradayGraphUrlUseISIN['NYSE'] = False

# in ms, time before activating XYPopup
timerForXYPopup = 500

# ============================================================================
# loadConfig()
# ============================================================================

def loadConfig():

    # access global var
    global bAutoRefreshMatrixView
    global bAutoRefreshCurrencyView
    global matrixFontSize
    global operationFontSize

    # create a configuration object
    config = ConfigParser.ConfigParser()

    # read the user configuration file
    fn = os.path.join(dirUserData,'usrconfig.txt')
    print 'User Configuration :',fn
    config.read(fn)

    # try to read informations
    try:
        v = config.get("view","AutoRefreshView")
    except:
        v = None
    if v:
        if v=="False":
            bAutoRefreshMatrixView = False
        else:
            bAutoRefreshMatrixView = True

    try:
        v = config.get("view","AutoRefreshCurrency")
    except:
        v = None
    if v:
        if v=="False":
            bAutoRefreshCurrencyView = False
        else:
            bAutoRefreshCurrencyView = True

    try:
        v = config.get("view","MatrixFontSize")
    except:
        v = 2
    if v:
        try:
            matrixFontSize = int(v)
        except:
            matrixFontSize = 2

    try:
        v = config.get("view","OperationFontSize")
    except:
        v = 2
    if v:
        try:
            operationFontSize = int(v)
        except:
            operationFontSize = 2

# ============================================================================
# saveConfig()
# ============================================================================

def saveConfig():
    # create a configuration object
    config = ConfigParser.ConfigParser()

    # create "View" section
    config.add_section("view")
    if bAutoRefreshMatrixView <> default_bAutoRefreshMatrixView:
        config.set("view", "AutoRefreshView", bAutoRefreshMatrixView)
    if bAutoRefreshCurrencyView <> default_bAutoRefreshCurrencyView:
        config.set("view", "AutoRefreshCurrency", bAutoRefreshCurrencyView)
    if matrixFontSize <> default_matrixFontSize:
        config.set("view","MatrixFontSize","%d" % matrixFontSize)
    if operationFontSize <> default_operationFontSize:
        config.set("view","OperationFontSize","%d" % operationFontSize)

    # write the new configuration file
    fn = os.path.join(dirUserData,'usrconfig.txt')
    f = open(fn,'w')
    config.write(f)
    f.close()

# ============================================================================
# Thomas Heller's function for determining
# if a module is running standalone
# ============================================================================

def main_is_frozen():
    if sys.platform == 'darwin':
        # this is a temporary hack for bundlebuilder
        return not sys.executable == '/System/Library/Frameworks/Python.framework/Versions/2.3/Resources/Python.app/Contents/MacOS/Python'
    else:
        return (hasattr(sys, "frozen") or # new py2exe, McMillan
                hasattr(sys, "importers") # old py2exe
                or imp.is_frozen("__main__")) # tools/freeze, cx_freeze

def get_main_dir():
    if main_is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(sys.argv[0])

# ============================================================================
# readAndEvalFile()
#
# ============================================================================

def readThenEvalFile(filename):
    f = open(filename)
    txt = '\n'.join(f.read().splitlines())
    f.close()
    return eval(txt, globals())

# ============================================================================
# disconnected
# ============================================================================

def setDisconnected(status=True):
    global gbDisconnected

    gbDisconnected = status
    if gbDisconnected:
        print 'Network : No connexion'
    else:
        print 'Network : Ready'

def isConnected():
    global gbDisconnected

    #print 'isConnected(): %s' % (not gbDisconnected)
    return not gbDisconnected

# ============================================================================
# During import
# ============================================================================

loadConfig()

# ============================================================================
# Test
# ============================================================================

if __name__=='__main__':
    loadConfig()
    saveConfig()

# ============================================================================
# That's all folks !
# ============================================================================
# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
