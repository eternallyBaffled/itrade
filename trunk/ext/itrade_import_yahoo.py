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
# 2005-10-17    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import re
import string
import urllib
from datetime import *

# iTrade system
from itrade_logging import *
from itrade_quotes import *
from itrade_datation import Datation,dd_mmm_yy2yyyymmdd,re_p3_1
from itrade_ext import *
from itrade_market import yahooTicker

# ============================================================================
# Import_yahoo()
#
# ============================================================================

class Import_yahoo(object):
    def __init__(self):
        debug('Import_yahoo:__init__')
        self.m_url = 'http://ichart.finance.yahoo.com/table.csv'

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

        query = (
            ('a', '%02d' % (int(d1[1])-1)),
            ('b', d1[2]),
            ('c', d1[0]),
            ('d', '%02d' % (int(d2[1])-1)),
            ('e', d2[2]),
            ('f', d2[0]),
            ('s', sname),
            ('y', '0'),
            ('g', 'd'),
            ('ignore', '.csv'),
        )
        query = map(lambda (var, val): '%s=%s' % (var, str(val)), query)
        query = string.join(query, '&')
        url = self.m_url + '?' + query

        debug("Import_yahoo:getdata: url=%s ",url)
        try:
            f = urllib.urlopen(url)
        except:
            debug('Import_yahoo:unable to connect :-(')
            return None

        # pull data
        buf = f.read()
        lines = self.splitLines(buf)
        header = string.split(lines[0],',')
        data = ""

        if (header[0]<>"Date"):
            # no valid content
            return None

        for eachLine in lines:
            sdata = string.split (eachLine, ',')
            sdate = sdata[0]
            if (sdate<>"Date"):
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

                if volume>0:
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
                    line = map(lambda (val): '%s' % str(val), line)
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

registerImportConnector('NASDAQ','NYC',QLIST_ANY,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('NYSE','NYC',QLIST_ANY,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('AMEX','NYC',QLIST_ANY,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('OTCBB','NYC',QLIST_ANY,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('LSE','LON',QLIST_ANY,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('ASX','SYD',QLIST_ANY,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerLiveConnector('TSX','TOR',QLIST_ANY,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerLiveConnector('TSE','TOR',QLIST_ANY,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerLiveConnector('MILAN EXCHANGE','MIL',QLIST_ANY,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerLiveConnector('SWISS EXCHANGE','GEN',QLIST_ANY,QTAG_IMPORT,gImportYahoo,bDefault=True)

registerImportConnector('EURONEXT','PAR',QLIST_SYSTEM,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('EURONEXT','PAR',QLIST_USER,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('EURONEXT','AMS',QLIST_SYSTEM,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('EURONEXT','AMS',QLIST_USER,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('ALTERNEXT','PAR',QLIST_SYSTEM,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('ALTERNEXT','PAR',QLIST_USER,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('PARIS MARCHE LIBRE','PAR',QLIST_SYSTEM,QTAG_IMPORT,gImportYahoo,bDefault=True)
registerImportConnector('PARIS MARCHE LIBRE','PAR',QLIST_USER,QTAG_IMPORT,gImportYahoo,bDefault=True)

# ============================================================================
# Test ME
#
# ============================================================================

def test(ticker,d):
    if gImportYahoo.connect():

        state = gImportYahoo.getstate()
        if state:
            debug("state=%s" % (state))

            quote = quotes.lookupTicker(ticker,'NASDAQ')
            data = gImportYahoo.getdata(quote,d)
            if data!=None:
                if data:
                    debug(data)
                else:
                    debug("nodata")
            else:
                print "getdata() failure :-("
        else:
            print "getstate() failure :-("

        gImportYahoo.disconnect()
    else:
        print "connect() failure :-("

if __name__=='__main__':
    setLevel(logging.INFO)

    # never failed - fixed date
    print "15/03/2005"
    test('AAPL',date(2005,03,15))

    # never failed except week-end
    print "yesterday-today :-("
    test('AAPL',date.today()-timedelta(1))

    # always failed
    print "tomorrow :-)"
    test('AAPL',date.today()+timedelta(1))

# ============================================================================
# That's all folks !
# ============================================================================
