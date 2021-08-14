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
# 2004-04-11    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Version management
# ============================================================================

from __future__ import print_function
__author__ = "Gilles Dumortier (dgil@ieee.org)"
__version__ = "0.4.8"
__status__ = "alpha"
__copyright__ = "Copyright (c) 2004-2008 Gilles Dumortier"
__license__ = "GPLv3 or later"
__credits__ = """See requirements.txt for the list of libraries used."""

# ============================================================================
# Imports
# ============================================================================

# python system
import os
import sys
import imp
import ConfigParser

__revision__ = 'x???'


def read_revision():
    global __revision__
    try:
        with open('REVISION', 'r') as f:
            infile = f.readlines()

        if len(infile) > 1:
            revline = infile[1].split(' ')
            __revision__ = revline[0]
        else:
            __revision__ = 'x???'
    except IOError:
        __revision__ = 'x???'


# ============================================================================
# Default configuration
# ============================================================================

# software name
softwareName = 'iTrade'
softwareLicense = __license__
softwareAuthors = __author__
softwareCopyright = __copyright__
softwareCredits = __credits__
softwareWebsite = 'https://itrade.sourceforge.net/'
softwareLatest  = 'https://itrade.svn.sourceforge.net/svnroot/itrade/trunk/OFFICIAL'

# iTrade version (major.minor)
softwareVersion = __version__
softwareVersionName = 'Druuna - (unstable) (%s)' % __revision__
softwareStatus = __status__

# support
bugTrackerURL = 'https://sourceforge.net/tracker/?group_id=128261&atid=711187'
donorsTrackerURL = 'https://sourceforge.net/donate/index.php?group_id=128261'
downloadURL = 'https://sourceforge.net/project/showfiles.php?group_id=128261'

manualURL = {
    'fr': 'https://itrade.sourceforge.net/fr/manual.htm',
    'en': 'https://itrade.sourceforge.net/manual.htm'
}

supportURL = {
    'en': 'https://itrade.sourceforge.net/support.htm',
    'fr': 'https://itrade.sourceforge.net/fr/support.htm'
}

forumURL = {
    'en': 'https://sourceforge.net/forum/forum.php?forum_id=436161',
    'fr': 'https://sourceforge.net/forum/forum.php?forum_id=436160'
}

# use ANSI colors
useColors = False


class InstallError(Exception):
    """Base class for installation-related errors."""
    pass


class DirNotFoundError(InstallError):
    def __init__(self, folder_name):
        InstallError.__init__(self, 'Invalid installation: folder "{}" does not exist.'.format(folder_name))


def set_application_root_folder(folder):
    """Set the home folder of the application from which all other files and folders are derived."""
    global dirRoot
    dirRoot = folder


dirRoot = ''


def application_root_folder():
    return dirRoot


def check_folder(folder):
    if not os.path.exists(folder):
        raise DirNotFoundError(folder)


def ensure_folder(folder):
    if not os.path.exists(folder):
        os.mkdir(folder)


def resolve_folder(folder):
    return os.path.join(application_root_folder(), folder)

# directory for system data
dirSysData = resolve_folder('data')
# directory for brokers data
dirBrokersData = resolve_folder('brokers')
# directory for symbol lists
dirSymbData = resolve_folder('symbols')
# directory for extensions
dirExtData = resolve_folder('ext')
fileExtData = 'extensions.txt'
# directory for indicators
dirIndData = resolve_folder('indicators')
fileIndData = 'indicators.txt'
# directory for user data
dirUserData = resolve_folder('usrdata')
# directory for alerts
dirAlerts = resolve_folder('alerts')
# directory for quotes images
dirImageData = resolve_folder('images')
# directory for cache data (quote, window prop, ...)
dirCacheData = resolve_folder('cache')
# file to get the current portfolio
fileCurrentPortfolio = 'portfolio.txt'
# directory for importation
dirImport = resolve_folder('import')
# directory for exportation
dirExport = resolve_folder('export')
# directory for snapshots
dirSnapshots = resolve_folder('snapshots')
# directory for trading reports
dirReports = resolve_folder('reports')
# directory for image resources
dirRes = resolve_folder('res')


def ensure_setup():
    read_revision()
    print('{}({}) - {} {}'.format(softwareName, softwareStatus, softwareVersion, softwareVersionName))
    check_folder(dirSysData)
    check_folder(dirBrokersData)
    check_folder(dirSymbData)
    check_folder(dirExtData)
    check_folder(dirIndData)
    ensure_folder(dirUserData)
    ensure_folder(dirAlerts)
    ensure_folder(dirImageData)
    ensure_folder(dirCacheData)
    ensure_folder(dirImport)
    ensure_folder(dirExport)
    ensure_folder(dirSnapshots)
    ensure_folder(dirReports)
    check_folder(dirRes)


def default_closure_file():
    return os.path.join(dirSysData, 'closed.txt')


def default_srd_file():
    return os.path.join(dirSysData, 'srd.txt')


def default_alerts_file():
    return os.path.join(dirUserData, 'alerts.txt')


def user_configuration_file():
    return os.path.join(dirUserData, 'usrconfig.txt')

# number of trading years
#numTradeYears = 12
numTradeYears = 2

# refresh in seconds for a view
refreshView = 6
refreshLive = 1.5

# refresh in seconds for a currency view
refreshCurrencyView = 15

# auto refresh the matrix view
default_bAutoRefreshMatrixView = True
bAutoRefreshMatrixView = default_bAutoRefreshMatrixView

# auto refresh the currency view
default_bAutoRefreshCurrencyView = True
bAutoRefreshCurrencyView = default_bAutoRefreshCurrencyView

# matrix font size
default_matrixFontSize = 2
matrixFontSize = default_matrixFontSize

# operation font size
default_operationFontSize = 2
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

intradayGraphUrl['EURONEXT'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^FCHI&a=v&p=s&lang=fr-FR&region=FR"
intradayGraphUrlUseISIN['EURONEXT'] = False
intradayGraphUrl['ALTERNEXT'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^FCHI&a=v&p=s&lang=fr-FR&region=FR"
intradayGraphUrlUseISIN['ALTERNEXT'] = False
intradayGraphUrl['PARIS MARCHE LIBRE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^FCHI&a=v&p=s&lang=fr-FR&region=FR"
intradayGraphUrlUseISIN['PARIS MARCHE LIBRE'] = False
intradayGraphUrl['BRUXELLES MARCHE LIBRE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^FCHI&a=v&p=s&lang=fr-FR&region=FR"
intradayGraphUrlUseISIN['BRUXELLES MARCHE LIBRE'] = False
intradayGraphUrl['NASDAQ'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['NASDAQ'] = False
intradayGraphUrl['NYSE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['NYSE'] = False
intradayGraphUrl['AMEX'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['AMEX'] = False
intradayGraphUrl['OTCBB'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['OTCBB'] = False
intradayGraphUrl['ASX'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['ASX'] = False
intradayGraphUrl['TORONTO VENTURE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['TORONTO VENTURE'] = False
intradayGraphUrl['TORONTO EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['TORONTO EXCHANGE'] = False
intradayGraphUrl['MILAN EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['MILAN EXCHANGE'] = False
intradayGraphUrl['SWISS EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['SWISS EXCHANGE'] = False
intradayGraphUrl['LSE SEAQ'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^FTSE&a=v&p=s&lang=en-GB&region=GB"
intradayGraphUrlUseISIN['LSE SEAQ'] = False
intradayGraphUrl['LSE SETSqx'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^FTSE&a=v&p=s&lang=en-GB&region=GB"
intradayGraphUrlUseISIN['LSE SETSqx'] = False
intradayGraphUrl['LSE SETS'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^FTSE&a=v&p=s&lang=en-GB&region=GB"
intradayGraphUrlUseISIN['LSE SETS'] = False
intradayGraphUrl['IRISH EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^FTSE&a=v&p=s&lang=en-GB&region=GB"
intradayGraphUrlUseISIN['IRISH EXCHANGE'] = False
intradayGraphUrl['MADRID EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^FTSE&a=v&p=s&lang=en-GB&region=GB"
intradayGraphUrlUseISIN['MADRID EXCHANGE'] = False
intradayGraphUrl['FRANKFURT EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^FTSE&a=v&p=s&lang=en-GB&region=GB"
intradayGraphUrlUseISIN['FRANKFURT EXCHANGE'] = False
intradayGraphUrl['STOCKHOLM EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^FTSE&a=v&p=s&lang=en-GB&region=GB"
intradayGraphUrlUseISIN['STOCKHOLM EXCHANGE'] = False
intradayGraphUrl['COPENHAGEN EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['COPENHAGEN EXCHANGE'] = False
intradayGraphUrl['OSLO EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^FTSE&a=v&p=s&lang=en-GB&region=GB"
intradayGraphUrlUseISIN['OSLO EXCHANGE'] = False
intradayGraphUrl['SAO PAULO EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['SAO PAULO EXCHANGE'] = False
intradayGraphUrl['HONG KONG EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['HONG KONG EXCHANGE'] = False
intradayGraphUrl['SHANGHAI EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['SHANGHAI EXCHANGE'] = False
intradayGraphUrl['SHENZHEN EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['SHENZHEN EXCHANGE'] = False
intradayGraphUrl['NATIONAL EXCHANGE OF INDIA'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['NATIONAL EXCHANGE OF INDIA'] = False
intradayGraphUrl['BOMBAY EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['BOMBAY EXCHANGE'] = False
intradayGraphUrl['NEW ZEALAND EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['NEW ZEALAND EXCHANGE'] = False
intradayGraphUrl['BUENOS AIRES EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['BUENOS AIRES EXCHANGE'] = False
intradayGraphUrl['MEXICO EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['MEXICO EXCHANGE'] = False
intradayGraphUrl['SINGAPORE EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['SINGAPORE EXCHANGE'] = False
intradayGraphUrl['KOREA STOCK EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['KOREA STOCK EXCHANGE'] = False
intradayGraphUrl['KOREA KOSDAQ EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['KOREA KOSDAQ EXCHANGE'] = False
intradayGraphUrl['WIENER BORSE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['WIENER BORSE'] = False
intradayGraphUrl['TOKYO EXCHANGE'] = "https://gchart.yahoo.co.jp/b?s=%s&t=1y&q=c&l=off&z=m&p=m65,m130&a=&c="
intradayGraphUrlUseISIN['TOKYO EXCHANGE'] = False
intradayGraphUrl['TAIWAN STOCK EXCHANGE'] = "https://chart.finance.yahoo.com/z?s=%s&t=1d&q=l&l=on&z=l&c=^GSPC&a=v&p=s&lang=en-US&region=US"
intradayGraphUrlUseISIN['TAIWAN STOCK EXCHANGE'] = False

# in ms, time before activating XYPopup
timerForXYPopup = 500

# default lang = system
lang = 0

# verbose mode
if __revision__[0] != 'x':
    verbose = False
else:
    print('Verbose mode : forced ON (under development release)')
    verbose = True

# experimental features
experimental = False

# do not use wxversion
nowxversion = False

# proxy data
proxyHostname = None
proxyAuthentication = None

# connection timeout
default_connectionTimeout = 20
connectionTimeout = default_connectionTimeout

# column
column = {
    'portfolio': "-1;1",
    'quotes': "-1;1",
    'indicators': "-1;1",
    'stops': "-1;1"
}


# ============================================================================
# checkNewRelease()
#
# return None or link to download the new release
# ============================================================================

def checkNewRelease(ping=False):
    # just to test : remove '#' from the line just below
    #__revision__ = 'r565'

    # development release : do not test
    if not ping and __revision__[0] == 'x':
        if verbose:
            print('checkNewRelease(): development release')
        return 'dev'

    from itrade_connection import ITradeConnection
    connection = ITradeConnection(cookies = None,
                               proxy = proxyHostname,
                               proxyAuth = proxyAuthentication,
                               connectionTimeout = 3
                               )

    # get OFFICIAL file from svn
    try:
        latest=connection.getDataFromUrl(softwareLatest)
    except IOError:
        print('checkNewRelease(): exception getting OFFICIAL file')
        return 'err'

    if latest[0]!='r':
        if verbose:
            print('checkNewRelease(): OFFICIAL file malformed')
        return 'err'

    # development release : do not test
    if __revision__[0] == 'x':
        if verbose:
            print('checkNewRelease(): development release (ping)')
        return 'dev'

    current = int(__revision__[1:])
    latest = int(latest[1:])

    #print current,latest

    if current<latest:
        print('checkNewRelease(): please update (%d vs %d) : %s' % (current,latest,downloadURL))
        return downloadURL
    else:
        print('checkNewRelease(): up to date')
        return 'ok'


def load_config():
    # access global var
    global bAutoRefreshMatrixView
    global bAutoRefreshCurrencyView
    global matrixFontSize
    global operationFontSize
    global lang
    global proxyHostname
    global proxyAuthentication
    global connectionTimeout
    global column

    # create a configuration object
    config = ConfigParser.ConfigParser()

    # read the user configuration file
    fn = user_configuration_file()
    print('User Configuration :',fn)
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

    try:
        connectionTimeout = int(config.get("net","connectionTimeout"))
    except:
        connectionTimeout = default_connectionTimeout

    # read columns
    for i in column.keys():
        try:
            column[i] = config.get("column",i)
        except:
            column[i] = "-1;1"

# ============================================================================
# saveConfig()
# ============================================================================

def saveConfig():
    # create a configuration object
    config = ConfigParser.ConfigParser()

    # create "View" section
    config.add_section("view")
    if bAutoRefreshMatrixView != default_bAutoRefreshMatrixView:
        config.set("view", "AutoRefreshView", bAutoRefreshMatrixView)
    if bAutoRefreshCurrencyView != default_bAutoRefreshCurrencyView:
        config.set("view", "AutoRefreshCurrency", bAutoRefreshCurrencyView)
    if matrixFontSize != default_matrixFontSize:
        config.set("view","MatrixFontSize","%d" % matrixFontSize)
    if operationFontSize != default_operationFontSize:
        config.set("view","OperationFontSize","%d" % operationFontSize)
    if (lang != 0) and (lang != 255):
        config.set("view","lang","%d" % lang)

    # create "Net" section
    config.add_section("net")
    if proxyHostname:
        config.set("net","proxyHostname",proxyHostname)
    if proxyAuthentication:
        config.set("net","proxyAuthentication",proxyAuthentication)
    if connectionTimeout != default_connectionTimeout:
        config.set("net","connectionTimeout",connectionTimeout)

    # create "Column" section
    config.add_section("column")
    for i in column.keys():
        config.set("column",i,column[i])

    # write the new configuration file
    with open(user_configuration_file(), 'w') as f:
        config.write(f)

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
# ============================================================================

def readThenEvalFile(filename):
    with open(filename) as f:
        txt = '\n'.join(f.read().splitlines())
    return eval(txt, globals())

# ============================================================================
# disconnected
# ============================================================================

# connection to network
gbDisconnected = False

def setDisconnected(status=True):
    global gbDisconnected

    gbDisconnected = status
    if gbDisconnected:
        print('Network : No connexion')
    else:
        print('Network : Ready')

def isConnected():
    #print 'isConnected(): %s' % (not gbDisconnected)
    return not gbDisconnected

# ============================================================================
# During import
# ============================================================================

# ============================================================================
# Test
# ============================================================================

def main():
    load_config()
    saveConfig()
    print(__revision__)
    print(os.path.expanduser('~'))
    print(checkNewRelease())


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
