#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_import_yahoo.py
#
# Description: Import quotes from yahoo.com
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
# 2005-10-17    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
import logging
import string
from datetime import date, timedelta

# iTrade system
from itrade_logging import setLevel, debug
from itrade_quotes import quotes
from itrade_datation import Datation, dd_mmm_yy2yyyymmdd, re_p3_1
from itrade_defs import QList, QTag
from itrade_ext import gImportRegistry
from itrade_market import yahooTicker, yahooUrl
from itrade_connection import ITradeConnection
import itrade_config

# ============================================================================
# Import_yahoo()
# ============================================================================

class Import_yahoo(object):
    def __init__(self):
        debug('Import_yahoo:__init__')

        #self.m_connection=ITradeConnection(proxy="172.30.0.3:8080")
        self.m_connection = ITradeConnection(cookies = None,
                                           proxy = itrade_config.proxyHostname,
                                           proxyAuth = itrade_config.proxyAuthentication,
                                           connectionTimeout = itrade_config.connectionTimeout
                                           )

    def name(self):
        return 'yahoo'

    def interval_year(self):
        return 0.5

    def connect(self):
        return True

    def disconnect(self):
        pass

    def getstate(self):
        return True

    def parseDate(self,d):
        return (d.year, d.month, d.day)

    def splitLines(self,buf):
        lines = string.split(buf, '\n')
        lines = filter(lambda x:x, lines)
        def removeCarriage(s):
            if s[-1]=='\r':
                return s[:-1]
            else:
                return s
        lines = [removeCarriage(l) for l in lines]
        return lines

    def getdata(self,quote,datedebut=None,datefin=None):
        if not datefin:
            datefin = date.today()

        if not datedebut:
            datedebut = date.today()
        if isinstance(datedebut,Datation):
            datedebut = datedebut.date()

        if isinstance(datefin,Datation):
            datefin = datefin.date()

        d1 = self.parseDate(datedebut)
        d2 = self.parseDate(datefin)

        debug("Import_yahoo:getdata quote:%s begin:%s end:%s" % (quote,d1,d2))

        sname = yahooTicker(quote.ticker(),quote.market(),quote.place())

        if sname[0]=='^':
            ss = "%5E" + sname[1:]
        else:
            ss = sname
        query = (
            ('s', ss),
            ('a', '%02d' % (int(d1[1])-1)),
            ('b', d1[2]),
            ('c', d1[0]),
            ('d', '%02d' % (int(d2[1])-1)),
            ('e', d2[2]),
            ('f', d2[0]),
            ('y', '0'),
            ('g', 'd'),
            ('ignore', '.csv'),
        )
        query = map(lambda var_val: '%s=%s' % (var_val[0], str(var_val[1])), query)
        query = string.join(query, '&')
        url = yahooUrl(quote.market(),live=False) + '?' + query

        debug("Import_yahoo:getdata: url=%s ",url)
        try:
            buf = self.m_connection.getDataFromUrl(url)
        except Exception:
            debug('Import_yahoo:unable to connect :-(')
            return None

        # pull data
        lines = self.splitLines(buf)
        if len(lines)<=0:
            # empty content
            return None
        header = string.split(lines[0],',')
        data = ""

        if header[0] != "Date":
            # no valid content
            return None

        for eachLine in lines:
            sdata = string.split (eachLine, ',')
            sdate = sdata[0]
            if sdate != "Date":
                if re_p3_1.match(sdate):
                    #print 'already good format ! ',sdate,sdata
                    pass
                else:
                    sdate = dd_mmm_yy2yyyymmdd(sdate)
                open = string.atof(sdata[1])
                high = string.atof(sdata[2])
                low = string.atof(sdata[3])
                value = string.atof(sdata[6])   #   Adj. Close*
                volume = string.atoi(sdata[5])

                if volume >= 0:
                    # encode in EBP format
                    # ISIN;DATE;OPEN;HIGH;LOW;CLOSE;VOLUME
                    line = (
                       quote.key(),
                       sdate,
                       open,
                       high,
                       low,
                       value,
                       volume
                    )
                    line = map(lambda val: '%s' % str(val), line)
                    line = string.join(line, ';')
                    # append
                    data = data + line + '\r\n'

        return data

# ============================================================================
# Export me
# ============================================================================


gImportYahoo = Import_yahoo()


gImportRegistry.register('NASDAQ','NYC',QList.any,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('NYSE','NYC',QList.any,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('AMEX','NYC',QList.any,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('OTCBB','NYC',QList.any,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('LSE','LON',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('ASX','SYD',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('TORONTO VENTURE','TOR',QList.any,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('TORONTO EXCHANGE','TOR',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('LSE SETS','LON',QList.any,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('LSE SETSqx','LON',QList.any,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('LSE SEAQ','LON',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('MILAN EXCHANGE','MIL',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('SWISS EXCHANGE','XSWX',QList.any,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('SWISS EXCHANGE','XVTX',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('EURONEXT','PAR',QList.system,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('EURONEXT','PAR',QList.user,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('EURONEXT','PAR',QList.indices,QTag.imported,gImportYahoo,bDefault=False)

gImportRegistry.register('EURONEXT','AMS',QList.system,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('EURONEXT','AMS',QList.user,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('EURONEXT','AMS',QList.indices,QTag.imported,gImportYahoo,bDefault=False)

gImportRegistry.register('EURONEXT','BRU',QList.system,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('EURONEXT','BRU',QList.user,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('EURONEXT','BRU',QList.indices,QTag.imported,gImportYahoo,bDefault=False)

gImportRegistry.register('EURONEXT','LIS',QList.system,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('EURONEXT','LIS',QList.user,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('EURONEXT','LIS',QList.indices,QTag.imported,gImportYahoo,bDefault=False)

gImportRegistry.register('ALTERNEXT','PAR',QList.system,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('ALTERNEXT','PAR',QList.user,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('ALTERNEXT','PAR',QList.indices,QTag.imported,gImportYahoo,bDefault=False)

gImportRegistry.register('ALTERNEXT','BRU',QList.system,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('ALTERNEXT','BRU',QList.user,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('ALTERNEXT','BRU',QList.indices,QTag.imported,gImportYahoo,bDefault=False)

gImportRegistry.register('ALTERNEXT','AMS',QList.system,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('ALTERNEXT','AMS',QList.user,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('ALTERNEXT','AMS',QList.indices,QTag.imported,gImportYahoo,bDefault=False)


gImportRegistry.register('ALTERNEXT','LIS',QList.system,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('ALTERNEXT','LIS',QList.user,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('ALTERNEXT','LIS',QList.indices,QTag.imported,gImportYahoo,bDefault=False)

gImportRegistry.register('PARIS MARCHE LIBRE','PAR',QList.system,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('PARIS MARCHE LIBRE','PAR',QList.user,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('PARIS MARCHE LIBRE','PAR',QList.indices,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('BRUXELLES MARCHE LIBRE','BRU',QList.system,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('BRUXELLES MARCHE LIBRE','BRU',QList.user,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('BRUXELLES MARCHE LIBRE','BRU',QList.indices,QTag.imported,gImportYahoo,bDefault=False)

gImportRegistry.register('IRISH EXCHANGE','DUB',QList.any,QTag.imported,gImportYahoo,bDefault=True)
gImportRegistry.register('MADRID EXCHANGE','MAD',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('FRANKFURT EXCHANGE','FRA',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('STOCKHOLM EXCHANGE','STO',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('COPENHAGEN EXCHANGE','CSE',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('OSLO EXCHANGE','OSL',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('SAO PAULO EXCHANGE','SAO',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('HONG KONG EXCHANGE','HKG',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('SHANGHAI EXCHANGE','SHG',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('SHENZHEN EXCHANGE','SHE',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('NATIONAL EXCHANGE OF INDIA','NSE',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('BOMBAY EXCHANGE','BSE',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('NEW ZEALAND EXCHANGE','NZE',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('BUENOS AIRES EXCHANGE','BUE',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('MEXICO EXCHANGE','MEX',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('SINGAPORE EXCHANGE','SGX',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('KOREA STOCK EXCHANGE','KRX',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('KOREA KOSDAQ EXCHANGE','KOS',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('WIENER BORSE','WBO',QList.any,QTag.imported,gImportYahoo,bDefault=True)

gImportRegistry.register('TAIWAN STOCK EXCHANGE','TAI',QList.any,QTag.imported,gImportYahoo,bDefault=True)

# ============================================================================
# Test ME
#
# ============================================================================

def test(ticker,d):
    if gImportYahoo.connect():

        state = gImportYahoo.getstate()
        if state:
            debug("state=%s" % state)

            quote = quotes.lookupTicker(ticker,'NASDAQ')
            data = gImportYahoo.getdata(quote,d)
            if data is not None:
                if data:
                    debug(data)
                else:
                    debug("nodata")
            else:
                print("getdata() failure :-(")
        else:
            print("getstate() failure :-(")

        gImportYahoo.disconnect()
    else:
        print("connect() failure :-(")

if __name__ == '__main__':
    setLevel(logging.INFO)

    # never failed - fixed date
    print("15/03/2005")
    test('AAPL',date(2005,3,15))

    # never failed except week-end
    print("yesterday-today :-(")
    test('AAPL',date.today()-timedelta(1))

    # always failed
    print("tomorrow :-)")
    test('AAPL',date.today()+timedelta(1))

# ============================================================================
# That's all folks !
# ============================================================================
