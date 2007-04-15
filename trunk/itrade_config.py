#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_config.py
#
# Description: Configuration
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
# 2004-04-11    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Version management
# ============================================================================

__author__ = "Gilles Dumortier (dgil@ieee.org)"
__version__ = "0.4.6"
__status__ = "alpha"
__copyright__ = "Copyright (c) 2004-2007 Gilles Dumortier"
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
# Read REVISION
# ============================================================================

# open the file
try:
    f = open('REVISION','r')
    infile = f.readlines()
    f.close()
    if len(infile)>1:
        infile = infile[1].split(' ')
        __svnversion__ = infile[0]
    else:
        __svnversion__ = 'r???'
except IOError:
    __svnversion__ = 'r???'

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
softwareLatest  = 'http://itrade.svn.sourceforge.net/viewvc/*checkout*/itrade/trunk/OFFICIAL'

# iTrade version (major.minor)
softwareVersion = __version__
softwareVersionName = 'Nausicaa2 - (unstable) (%s)' % __svnversion__
softwareStatus = __status__

print '%s(%s) - %s %s' % (softwareName,softwareStatus,softwareVersion,softwareVersionName)

# connection to network
global gbDisconnected
gbDisconnected = False

# support
bugTrackerURL = 'http://sourceforge.net/tracker/?group_id=128261&atid=711187'
donorsTrackerURL = 'http://sourceforge.net/donate/index.php?group_id=128261'
downloadURL = 'http://sourceforge.net/project/showfiles.php?group_id=128261'

manualURL = {}
manualURL['fr'] = 'http://itrade.sourceforge.net/fr/manual.htm'
manualURL['en'] = 'http://itrade.sourceforge.net/manual.htm'

supportURL = {}
supportURL['en'] = 'http://itrade.sourceforge.net/support.htm'
supportURL['fr'] = 'http://itrade.sourceforge.net/fr/support.htm'

forumURL = {}
forumURL['en'] = 'http://sourceforge.net/forum/forum.php?forum_id=436161'
forumURL['fr'] = 'http://sourceforge.net/forum/forum.php?forum_id=436160'

# use ANSI colors
useColors = False

# itrade root directory
dirRoot=os.path.dirname(sys.argv[0])

# directory for system data
dirSysData = os.path.join(dirRoot, 'data')
if not os.path.exists(dirSysData):
    raise('invalid installation ! %s folder does not exist !' % dirSysData)

# directory for brokers data
dirBrokersData = os.path.join(dirRoot, 'brokers')
if not os.path.exists(dirBrokersData):
    raise('invalid installation ! %s folder does not exist !' % dirBrokersData)

# directory for symbol lists
dirSymbData = os.path.join(dirRoot, 'symbols')
if not os.path.exists(dirSymbData):
    raise('invalid installation ! %s folder does not exist !' % dirSymbData)

# directory for extensions
dirExtData = os.path.join(dirRoot, 'ext')
if not os.path.exists(dirExtData):
    raise('invalid installation ! %s folder does not exist !' % dirExtData)
fileExtData = 'extensions.txt'

# directory for indicators
dirIndData = os.path.join(dirRoot, 'indicators')
if not os.path.exists(dirIndData):
    raise('invalid installation ! %s folder does not exist !' % dirIndData)
fileIndData = 'indicators.txt'

# directory for user data
dirUserData = os.path.join(dirRoot, 'usrdata')
if not os.path.exists(dirUserData):
    os.mkdir(dirUserData)

# directory for alerts
dirAlerts = os.path.join(dirRoot, 'alerts')
if not os.path.exists(dirAlerts):
    os.mkdir(dirAlerts)

# directory for quotes images
dirImageData = os.path.join(dirRoot, 'images')
if not os.path.exists(dirImageData):
    os.mkdir(dirImageData)

# directory for cache data (quote, window prop, ...)
dirCacheData = os.path.join(dirRoot, 'cache')
if not os.path.exists(dirCacheData):
    os.mkdir(dirCacheData)

# file to get the current portfolio
fileCurrentPortfolio = 'portfolio.txt'

# directory for importation
dirImport = os.path.join(dirRoot, 'import')
if not os.path.exists(dirImport):
    os.mkdir(dirImport)

# directory for exportation
dirExport = os.path.join(dirRoot, 'export')
if not os.path.exists(dirExport):
    os.mkdir(dirExport)

# directory for snapshots
dirSnapshots = os.path.join(dirRoot, 'snapshots')
if not os.path.exists(dirSnapshots):
    os.mkdir(dirSnapshots)

# directory for trading reports
dirReports = os.path.join(dirRoot, 'reports')
if not os.path.exists(dirReports):
    os.mkdir(dirReports)

# directory for image ressources
dirRes = os.path.join(dirRoot, 'res')
if not os.path.exists(dirRes):
    raise('invalid installation ! %s folder does not exist !' % dirRes)

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
intradayGraphUrl['ALTERNEXT'] = "http://www.abcbourse.com/Graphes/graphe.aspx?s=%sp&m=g&t=lc"
intradayGraphUrlUseISIN['ALTERNEXT'] = False
intradayGraphUrl['PARIS MARCHE LIBRE'] = "http://www.abcbourse.com/Graphes/graphe.aspx?s=%sp&m=g&t=lc"
intradayGraphUrlUseISIN['PARIS MARCHE LIBRE'] = False
intradayGraphUrl['BRUXELLES MARCHE LIBRE'] = "http://www.abcbourse.com/Graphes/graphe.aspx?s=%sp&m=g&t=lc"
intradayGraphUrlUseISIN['BRUXELLES MARCHE LIBRE'] = False
intradayGraphUrl['NASDAQ'] = "http://ichart.finance.yahoo.com/b?s=%s"
intradayGraphUrlUseISIN['NASDAQ'] = False
intradayGraphUrl['NYSE'] = "http://ichart.finance.yahoo.com/b?s=%s"
intradayGraphUrlUseISIN['NYSE'] = False
intradayGraphUrl['AMEX'] = "http://ichart.finance.yahoo.com/b?s=%s"
intradayGraphUrlUseISIN['AMEX'] = False
intradayGraphUrl['OTCBB'] = "http://ichart.finance.yahoo.com/b?s=%s.OB"
intradayGraphUrlUseISIN['OTCBB'] = False
intradayGraphUrl['ASX'] = "http://ichart.finance.yahoo.com/b?s=%s.AX"
intradayGraphUrlUseISIN['ASX'] = False
intradayGraphUrl['TSX'] = "http://ichart.finance.yahoo.com/b?s=%s.V"
intradayGraphUrlUseISIN['TSX'] = False
intradayGraphUrl['TSE'] = "http://ichart.finance.yahoo.com/b?s=%s.TO"
intradayGraphUrlUseISIN['TSE'] = False
intradayGraphUrl['MILAN EXCHANGE'] = "http://ichart.finance.yahoo.com/b?s=%s.MI"
intradayGraphUrlUseISIN['MILAN EXCHANGE'] = False
intradayGraphUrl['SWISS EXCHANGE.XSWX'] = "http://ichart.finance.yahoo.com/b?s=%s.SW"
intradayGraphUrlUseISIN['SWISS EXCHANGE.XSWX'] = False
intradayGraphUrl['SWISS EXCHANGE.XVTX'] = "http://ichart.finance.yahoo.com/b?s=%s.VX"
intradayGraphUrlUseISIN['SWISS EXCHANGE.XVTX'] = False
intradayGraphUrl['LSE'] = "http://ichart.finance.yahoo.com/b?s=%s.L"
intradayGraphUrlUseISIN['LSE'] = False

# in ms, time before activating XYPopup
timerForXYPopup = 500

# default lang = system
global lang
lang = 0

# verbose mode
if __svnversion__ != 'r???':
    verbose = False
else:
    print 'Verbose mode : forced ON (under development release)'
    verbose = True

# experimental features
experimental = False

# proxy data
global proxyHostname
proxyHostname = None

global proxyAuthentication
proxyAuthentication = None

# ============================================================================
# checkNewRelease()
#
# return None or link to download the new release
# ============================================================================

def checkNewRelease():
    # just to test : remove '#' from the line just below
    #__svnversion__ = 'r564'

    # development release : do not test
    if __svnversion__ == 'r???':
        if verbose:
            print 'checkNewRelease(): development release'
        return 'dev'

    from itrade_connection import ITradeConnection
    connection=ITradeConnection(cookies=None,
                                proxy=proxyHostname,
                                proxyAuth=proxyAuthentication)

    # get OFFICIAL file from svn
    try:
        latest=connection.getDataFromUrl(softwareLatest)
    except IOError:
        print 'checkNewRelease(): exeption getting OFFICIAL file'
        return 'err'

    if latest[0]!='r':
        if verbose:
            print 'checkNewRelease(): OFFICIAL file malformed'
        return 'err'

    current = int(__svnversion__[1:])
    latest = int(latest[1:])

    #print current,latest

    if current<latest:
        print 'checkNewRelease(): please update (%d vs %d) : %s' % (current,latest,downloadURL)
        return downloadURL
    else:
        print 'checkNewRelease(): up to date'
        return 'ok'

# ============================================================================
# loadConfig()
# ============================================================================

def loadConfig():

    # access global var
    global bAutoRefreshMatrixView
    global bAutoRefreshCurrencyView
    global matrixFontSize
    global operationFontSize
    global lang
    global proxyHostname
    global proxyAuthentication

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

    try:
        v = config.get("view","lang")
    except:
        v = 0
    if v:
        try:
            lang = int(v)
        except:
            lang = 0

    try:
        proxyHostname = config.get("net","proxyHostname")
    except:
        proxyHostname = None

    try:
        proxyAuthentication = config.get("net","proxyAuthentication")
    except:
        proxyAuthentication = None

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
    if (lang != 0) and (lang != 255):
        config.set("view","lang","%d" % lang)

    # create "Net" section
    config.add_section("net")
    if proxyHostname:
        config.set("net","proxyHostname",proxyHostname)
    if proxyAuthentication:
        config.set("net","proxyAuthentication",proxyAuthentication)

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

# __x loadConfig()

# ============================================================================
# Test
# ============================================================================

if __name__=='__main__':
    loadConfig()
    saveConfig()

    print __svnversion__

    print os.path.expanduser('~')

    print checkNewRelease()

# ============================================================================
# That's all folks !
# ============================================================================
