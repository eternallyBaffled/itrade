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
# 2007-01-21    dgil  Move to the new extension mechanism
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from datetime import date
import logging
import os

# iTrade system
import itrade_config
from itrade_logging import setLevel, info, debug

# ============================================================================
# Importation from internet : HISTORIC
# (update) a quote
# ============================================================================

def import_from_internet(quote,fromdate=None,todate=None):
    bRet = False

    if quote.ticker()=='':
        info("import_from_internet(%s): no ticker" % quote.isin())
        #return bRet

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
            if data is not None:
                if data:
                    #debug('import_from_internet(%s): data:%s'% (quote.ticker(),data))
                    quote.importTrades(data,bLive=False)
                    bRet = True
                else:
                    if itrade_config.verbose:
                        print("import_from_internet(%s): nodata [%s,%s)" % (quote.ticker(),fromdate,todate))
                    bRet = False
            else:
                if itrade_config.verbose:
                    print("import_from_internet(%s): nodata [%s,%s)" % (quote.ticker(),fromdate,todate))
                bRet = False
        else:
            print("import_from_internet(%s): getstate() failure :-(" % quote.ticker())
            bRet = False

        abc.disconnect()
        return bRet
    else:
        print("import_from_internet(%s): connect() failure :-(" % quote.ticker())
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
            if data is not None:
                if data:
                    #debug('liveupdate_from_internet(%s): data:%s'% (quote.ticker(),data))
                    quote.importTrades(data,bLive=True)
                    bRet = True
                else:
                    #debug("liveupdate_from_internet(%s): nodata" % quote.ticker())
                    bRet = False
            else:
                if abc.alive():
                    if itrade_config.verbose:
                        print("liveupdate_from_internet(%s): alive but no trade yet" % quote.ticker())
                else:
                    if itrade_config.verbose:
                        print("liveupdate_from_internet(%s): not alive yet" % quote.ticker())
                bRet = False
        else:
            print("liveupdate_from_internet(%s): getstate() failure :-(" % quote.ticker())
            bRet = False

        abc.disconnect()

        abc.release()
        return bRet

    else:
        print("liveupdate_from_internet(%s): connect() failure :-(" % quote.ticker())

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
        if itrade_config.verbose:
            print('--- update the quote -- %d to %d ---' % (year-step+1,year))
        if spl:
            if not import_from_internet(quote,date(year-step+1,1,1),date(year,6,30)):
                bStop = True
            if not import_from_internet(quote,date(year-step+1,7,1),date(year,12,31)):
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
    if itrade_config.verbose:
        print('--- save the quote data ------')
    quote.saveTrades()
    return True

def cmdline_importQuoteFromFile(quote,file):
    if itrade_config.verbose:
        print('--- load data from file ------')
    if not os.access(file,os.R_OK):
        file = os.path.join(itrade_config.dirImport,file)
        if not os.access(file,os.R_OK):
            print('file not found %s!' % file)
            return False
    quote.loadTrades(file)
    if itrade_config.verbose:
        print('--- save the quote data ------')
    quote.saveTrades()
    return True

# ============================================================================
# CommandLine : -i / import the matrix
# ============================================================================

def cmdline_importMatrixFromInternet(matrix,dlg=None):
    year = date.today().year
    nyear = 0
    while nyear < itrade_config.numTradeYears:
        if itrade_config.verbose:
            print('--- update the matrix --%d--' % year)
        matrix.update(date(year,1,1),date(year,12,31))
        if dlg:
            dlg.Update(nyear)
        nyear = nyear + 1
        year = year -1
    if itrade_config.verbose:
        print('--- save the matrix data -----')
    matrix.saveTrades()
    return True

def cmdline_importMatrixFromFile(matrix,file):
    if itrade_config.verbose:
        print('--- load data from file ------ %s' % file)
    if not os.access(file,os.R_OK):
        file = os.path.join(itrade_config.dirImport,file)
        if not os.access(file,os.R_OK):
            print('file not found %s !' % file)
            return False
    matrix.loadTrades(file)
    if itrade_config.verbose:
        print('--- save the matrix data -----')
    matrix.saveTrades()
    return True

# ============================================================================
# Test ME
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    print('AUSY (Euronext market):')
    q = quotes.lookupTicker('OSI','EURONEXT')
    print('Country: %s, Market: %s' % (q.country(),q.market()))
    print("Get 15/03/2005 - 25/03/2005")
    q.update(date(2005,3,15),date(2005,3,25))
    print("Get Live %s " % date.today())
    q.update()

    print('APPLE (US market):')
    q = quotes.lookupTicker('AAPL','NASDAQ')
    print('Country: %s, Market: %s' % (q.country(),q.market()))
    print("Get 15/03/2005 - 25/03/2005")
    q.update(date(2005,3,15),date(2005,3,25))
    print("Get Live %s " % date.today())
    q.update()

# ============================================================================
# That's all folks !
# ============================================================================
