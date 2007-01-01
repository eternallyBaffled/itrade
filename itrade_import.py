#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_import.py
#
# Description: Import quotes from files / web site / ...
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
# 2005-03-20    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import thread
from datetime import *

# iTrade system
from itrade_logging import *
from itrade_datation import Datation
import itrade_config
from itrade_market import market2place

# ============================================================================
# LIST
# ============================================================================

QLIST_ALL      = 0
QLIST_ANY      = 0
QLIST_SYSTEM   = 1
QLIST_USER     = 2
QLIST_INDICES  = 3
QLIST_TRACKERS = 4

# ============================================================================
# TAG
# ============================================================================

QTAG_ANY = 0
QTAG_LIVE = 1
QTAG_DIFFERED = 2
QTAG_IMPORT = 3
QTAG_LIST = 4

# ============================================================================
# ConnectorRegistry
# ============================================================================

class ConnectorRegistry(object):
    def __init__(self):
        self.m_conn = []

    def register(self,market,place,qlist,qtag,connector,bDefault=True):
        self.m_conn.append((market,place,bDefault,connector,qlist,qtag))
        #print 'Register %s for market :' % self, market,' qlist:',qlist,' qtag:',qtag
        return True

    def get(self,market,qlist,qtag,place=None,name=None):
        if place==None:
            place = market2place(market)
        if name:
            for amarket,aplace,adefault,aconnector,aqlist,aqtag in self.m_conn:
                #print amarket,aqlist,aqtag,aplace,aconnector.name(),adefault
                if market==amarket and place==aplace and aconnector.name()==name and (aqlist==QLIST_ANY or aqlist==qlist) and (qtag==QTAG_ANY or aqtag==qtag):
                    return aconnector
        else:
            for amarket,aplace,adefault,aconnector,aqlist,aqtag in self.m_conn:
                if market==amarket and place==aplace and (aqlist==QLIST_ANY or qlist==aqlist) and adefault and (qtag==QTAG_ANY or aqtag==qtag):
                    return aconnector
        return None

    def list(self,market,qlist,place):
        lst = []
        for amarket,aplace,adefault,aconnector,aqlist,aqtag in self.m_conn:
            if amarket==market and aplace==place and (aqlist==QLIST_ANY or aqlist==qlist):
                lst.append((aconnector.name(),amarket,aplace,adefault,aconnector,aqlist,aqtag))
        return lst

# ============================================================================
# Export Live and Import Registries
# ============================================================================

try:
    ignore(gLiveRegistry)
except NameError:
    gLiveRegistry = ConnectorRegistry()

registerLiveConnector = gLiveRegistry.register
getLiveConnector = gLiveRegistry.get
listLiveConnector = gLiveRegistry.list

def getDefaultLiveConnector(market,list,place=None):
    if itrade_config.isDiffered():
        # force differed connector
        ret = getLiveConnector(market,list,QTAG_DIFFERED,place)
    else:
        # try live connector
        ret = getLiveConnector(market,list,QTAG_LIVE,place)
        if ret==None:
            # no live connector : fall-back to differed connector
            ret = getLiveConnector(market,list,QTAG_DIFFERED,place)
    if ret==None:
        print 'No default connector %s for market :' % self,market,' qlist:',qlist
    return ret

try:
    ignore(gImportRegistry)
except NameError:
    gImportRegistry = ConnectorRegistry()

registerImportConnector = gImportRegistry.register
getImportConnector = gImportRegistry.get
listImportConnector = gImportRegistry.list

# ============================================================================
# Export ListSymbol Registry
# ============================================================================

try:
    ignore(gListSymbolRegistry)
except NameError:
    gListSymbolRegistry = ConnectorRegistry()

registerListSymbolConnector = gListSymbolRegistry.register
getListSymbolConnector = gListSymbolRegistry.get
listListSymbolConnector = gListSymbolRegistry.list

# ============================================================================
# __x be more dynamic ...
# ============================================================================

# Euronext market connectors : ABCBourse (deprecated), Euronext or Fortuneo
import itrade_import_euronext
import itrade_liveupdate_euronext

import itrade_liveupdate_fortuneo

import itrade_import_abcbourse
import itrade_liveupdate_abcbourse

# all others market connectors (incl. euronext) : Yahoo
import itrade_import_yahoo
import itrade_liveupdate_yahoo

# list of symbols : Euronext, Nyse, BarChart (Amex,Nasdaq,OTCBB)
import itrade_quotes_euronext

import itrade_quotes_nyse

import itrade_quotes_barchart

# ============================================================================
# Importation from internet : HISTORIC
# (update) a quote
# ============================================================================

def import_from_internet(quote,fromdate=None,todate=None):
    bRet = False

    if quote.ticker()=='':
        info("import_from_internet(%s): no ticker" % quote.isin())
        return bRet

    if not itrade_config.isConnected():
        info("import_from_internet(%s): no connexion" % quote.ticker())
        return bRet

    abc = quote.importconnector()
    if abc and abc.connect():

        state = abc.getstate()
        if state:
            #debug("state=%s" % (state))
            #debug('import historic %s from %s ...' % (quote.ticker(),abc.name()))
            data = abc.getdata(quote,fromdate,todate)
            if data!=None:
                if data:
                    #debug('import_from_internet(%s): data:%s'% (quote.ticker(),data))
                    quote.importTrades(data,bLive=False)
                    bRet = True
                else:
                    print "import_from_internet(%s): nodata [%s,%s)" % (quote.ticker(),fromdate,todate)
                    bRet = False
            else:
                print "import_from_internet(%s): nodata [%s,%s)" % (quote.ticker(),fromdate,todate)
                bRet = False
        else:
            print "import_from_internet(%s): getstate() failure :-(" % quote.ticker()
            bRet = False

        abc.disconnect()
        return bRet
    else:
        print "import_from_internet(%s): connect() failure :-(" % quote.ticker()
        return bRet

# ============================================================================
# LiveUpdate from internet : LIVE
#
# (update) a quote
# ============================================================================

def liveupdate_from_internet(quote):
    bRet = False

    if not itrade_config.isConnected():
        debug("liveupdate_from_internet(%s): no connexion" % quote.ticker())
        return bRet

    abc = quote.liveconnector()
    abc.acquire()
    if abc.iscacheddataenoughfreshq():
        data = abc.getcacheddata(quote)
        if data:
            #debug(data)
            debug("liveupdate_from_internet(%s): import live from cache" % quote.ticker())
            quote.importTrades(data,bLive=True)
            bRet = True
        else:
            #debug("liveupdate_from_internet(%s): nodata" % quote.ticker())
            bRet = False

        abc.release()
        return bRet

    elif abc.connect():

        state = abc.getstate()
        if state:
            #debug("state=%s" % (state))
            #debug('liveupdate_from_internet(%s): import live from abcbourse ...' % quote.ticker())
            data = abc.getdata(quote)
            if data!=None:
                if data:
                    #debug('liveupdate_from_internet(%s): data:%s'% (quote.ticker(),data))
                    quote.importTrades(data,bLive=True)
                    bRet = True
                else:
                    #debug("liveupdate_from_internet(%s): nodata" % quote.ticker())
                    bRet = False
            else:
                if abc.alive():
                    print "liveupdate_from_internet(%s): alive but no trade yet" % quote.ticker()
                else:
                    print "liveupdate_from_internet(%s): not alive yet" % quote.ticker()
                bRet = False
        else:
            print "liveupdate_from_internet(%s): getstate() failure :-(" % quote.ticker()
            bRet = False

        abc.disconnect()

        abc.release()
        return bRet

    else:

        print "liveupdate_from_internet(%s): connect() failure :-(" % quote.ticker()

        abc.release()
        return bRet

# ============================================================================
# CommandLine : -i / import a quote
# ============================================================================

def cmdline_importQuoteFromInternet(quote,dlg=None):
    year = date.today().year
    ic = quote.importconnector()
    spl = False
    if ic:
        step = ic.interval_year()
        if step == 0.5:
            spl = True
            step = 1
    else:
        step = 1
    nyear = 0
    bStop = False
    while (not bStop) and (nyear < itrade_config.numTradeYears):
        print '--- update the quote -- %d to %d ---' % (year-step+1,year)
        if spl:
            if not import_from_internet(quote,date(year-step+1,1,1),date(year,6,30)):
                bStop = True
            if not bStop and not import_from_internet(quote,date(year-step+1,7,1),date(year,12,31)):
                bStop = True
        else:
            if not import_from_internet(quote,date(year-step+1,1,1),date(year,12,31)):
                bStop = True
        if year == date.today().year:
            # SF bug 1625731 : at the year begins, it's possible import_from_internet returns no data
            # but iTrade needs to continue importing previous years ...
            bStop = False
        if dlg:
            dlg.Update(nyear)
        nyear = nyear + step
        year = year - step
    print '--- save the quote data ------'
    quote.saveTrades()
    return True

def cmdline_importQuoteFromFile(quote,file):
    print '--- load data from file ------'
    if not os.access(file,os.R_OK):
        file = os.path.join(itrade_config.dirImport,file)
        if not os.access(file,os.R_OK):
            print 'file not found !'
            return False
    quote.loadTrades(file)
    print '--- save the quote data ------'
    quote.saveTrades()
    return True

# ============================================================================
# CommandLine : -i / import the matrix
# ============================================================================

def cmdline_importMatrixFromInternet(matrix,dlg=None):
    year = date.today().year
    nyear = 0
    while nyear < itrade_config.numTradeYears:
        print '--- update the matrix --%d--' % year
        matrix.update(date(year,1,1),date(year,12,31))
        if dlg:
            dlg.Update(nyear)
        nyear = nyear + 1
        year = year -1
    print '--- save the matrix data -----'
    matrix.saveTrades()
    return True

def cmdline_importMatrixFromFile(matrix,file):
    print '--- load data from file ------ %s' % file
    if not os.access(file,os.R_OK):
        file = os.path.join(itrade_config.dirImport,file)
        if not os.access(file,os.R_OK):
            print 'file not found !'
            return False
    matrix.loadTrades(file)
    print '--- save the matrix data -----'
    matrix.saveTrades()
    return True

# ============================================================================
# Test ME
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    from itrade_quotes import *

    print 'AUSY (Euronext market):'
    q = quotes.lookupTicker('OSI','EURONEXT')
    print 'Country: %s, Market: %s' % (q.country(),q.market())
    print "Get 15/03/2005 - 25/03/2005"
    q.update(date(2005,03,15),date(2005,03,25))
    print "Get Live %s " % date.today()
    q.update()

    print 'APPLE (US market):'
    q = quotes.lookupTicker('AAPL','NASDAQ')
    print 'Country: %s, Market: %s' % (q.country(),q.market())
    print "Get 15/03/2005 - 25/03/2005"
    q.update(date(2005,03,15),date(2005,03,25))
    print "Get Live %s " % date.today()
    q.update()

# ============================================================================
# That's all folks !
# ============================================================================
