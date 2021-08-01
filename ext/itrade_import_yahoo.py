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
from itrade_defs import QList, QTAG_IMPORT
from itrade_ext import registerImportConnector
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
            buf=self.m_connection.getDataFromUrl(url)
        except:
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

try:
    ignore(gImportYahoo)
except NameError:
    gImportYahoo = Import_yahoo()

registerImportConnector('NASDAQ','NYC',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('NYSE','NYC',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('AMEX','NYC',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('OTCBB','NYC',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('LSE','LON',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('ASX','SYD',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('TORONTO VENTURE','TOR',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('TORONTO EXCHANGE','TOR',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('LSE SETS','LON',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('LSE SETSqx','LON',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('LSE SEAQ','LON',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('MILAN EXCHANGE','MIL',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('SWISS EXCHANGE','XSWX',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('SWISS EXCHANGE','XVTX',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('EURONEXT','PAR',QList.system,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('EURONEXT','PAR',QList.user,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('EURONEXT','PAR',QList.indices,QTAG_IMPORT,gImportYahoo,bDefault=False)

registerImportConnector('EURONEXT','AMS',QList.system,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('EURONEXT','AMS',QList.user,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('EURONEXT','AMS',QList.indices,QTAG_IMPORT,gImportYahoo,bDefault=False)

registerImportConnector('EURONEXT','BRU',QList.system,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('EURONEXT','BRU',QList.user,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('EURONEXT','BRU',QList.indices,QTAG_IMPORT,gImportYahoo,bDefault=False)

registerImportConnector('EURONEXT','LIS',QList.system,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('EURONEXT','LIS',QList.user,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('EURONEXT','LIS',QList.indices,QTAG_IMPORT,gImportYahoo,bDefault=False)

registerImportConnector('ALTERNEXT','PAR',QList.system,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('ALTERNEXT','PAR',QList.user,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('ALTERNEXT','PAR',QList.indices,QTAG_IMPORT,gImportYahoo,bDefault=False)

registerImportConnector('ALTERNEXT','BRU',QList.system,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('ALTERNEXT','BRU',QList.user,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('ALTERNEXT','BRU',QList.indices,QTAG_IMPORT,gImportYahoo,bDefault=False)

registerImportConnector('ALTERNEXT','AMS',QList.system,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('ALTERNEXT','AMS',QList.user,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('ALTERNEXT','AMS',QList.indices,QTAG_IMPORT,gImportYahoo,bDefault=False)


registerImportConnector('ALTERNEXT','LIS',QList.system,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('ALTERNEXT','LIS',QList.user,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('ALTERNEXT','LIS',QList.indices,QTAG_IMPORT,gImportYahoo,bDefault=False)

registerImportConnector('PARIS MARCHE LIBRE','PAR',QList.system,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('PARIS MARCHE LIBRE','PAR',QList.user,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('PARIS MARCHE LIBRE','PAR',QList.indices,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('BRUXELLES MARCHE LIBRE','BRU',QList.system,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('BRUXELLES MARCHE LIBRE','BRU',QList.user,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('BRUXELLES MARCHE LIBRE','BRU',QList.indices,QTAG_IMPORT,gImportYahoo,bDefault=False)

registerImportConnector('IRISH EXCHANGE','DUB',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('MADRID EXCHANGE','MAD',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('FRANKFURT EXCHANGE','FRA',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('STOCKHOLM EXCHANGE','STO',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('COPENHAGEN EXCHANGE','CSE',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('OSLO EXCHANGE','OSL',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('SAO PAULO EXCHANGE','SAO',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('HONG KONG EXCHANGE','HKG',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('SHANGHAI EXCHANGE','SHG',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('SHENZHEN EXCHANGE','SHE',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('NATIONAL EXCHANGE OF INDIA','NSE',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('BOMBAY EXCHANGE','BSE',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('NEW ZEALAND EXCHANGE','NZE',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('BUENOS AIRES EXCHANGE','BUE',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('MEXICO EXCHANGE','MEX',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('SINGAPORE EXCHANGE','SGX',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('KOREA STOCK EXCHANGE','KRX',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('KOREA KOSDAQ EXCHANGE','KOS',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('WIENER BORSE','WBO',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('TAIWAN STOCK EXCHANGE','TAI',QList.any,QTAG_IMPORT,gImportYahoo,bDefault=True)

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
