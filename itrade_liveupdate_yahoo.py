#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_liveupdate_yahoo.py
#
# Description: Live update quotes from yahoo.com
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
# 2005-10-17    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import re
import thread
import string
import urllib
import time

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_quotes import *
from itrade_import import registerLiveConnector
from itrade_market import yahooTicker

# ============================================================================
# LiveUpdate_yahoo()
#
# ============================================================================

class LiveUpdate_yahoo(object):
    def __init__(self):
        debug('LiveUpdate_yahoo:__init__')
        self.m_url = "http://quote.yahoo.com/download/quotes.csv"
        self.m_connected = False
        self.m_livelock = thread.allocate_lock()
        self.m_clock = {}
        self.m_dcmpd = {}
        self.m_lastclock = 0

    # ---[ reentrant ] ---
    def acquire(self):
        self.m_livelock.acquire()

    def release(self):
        self.m_livelock.release()

    # ---[ properties ] ---

    def name(self):
        return 'yahoo'

    def delay(self):
        return 15

    # ---[ connexion ] ---

    def connect(self):
        return True

    def disconnect(self):
        pass

    def alive(self):
        return self.m_connected

    # ---[ state ] ---

    def getstate(self):
        # no state
        return True

    # ---[ code to get data ] ---

    def yahooDate (self,date):
        # Date part is easy.
        sdate = string.split (date[1:-1], '/')
        month = string.atoi (sdate[0])
        day = string.atoi (sdate[1])
        year = string.atoi (sdate[2])

        return "%4d%02d%02d" % (year,month,day)

    def convertClock(self,clock):
        clo = clock[:-2]
        min = clo[-2:]
        hour = clo[:-3]
        val = (int(hour)*60) + int(min)
        per = clock[-2:]
        #if per=='pm':
        #    val = val + 12*60
        # print clo,hour,min,val,per
        if val>self.m_lastclock:
            self.m_lastclock = val
        return "%d:%02d" % (val/60,val%60)

    def getdata(self,quote):
        debug("LiveUpdate_yahoo:getdata quote:%s " % quote)
        self.m_connected = False

        sname = yahooTicker(quote.ticker(),quote.market())

        query = (
          ('f', 'sl1d1t1c1ohgvbap'),
          ('s', sname),
          ('e', '.csv'),
        )
        query = map(lambda (var, val): '%s=%s' % (var, str(val)), query)
        query = string.join(query, '&')
        url = self.m_url + '?' + query

        debug("LiveUpdate_yahoo:getdata: url=%s",url)
        try:
            f = urllib.urlopen(url)
        except:
            debug('LiveUpdate_yahoo:unable to connect :-(')
            return None

        # pull data
        data = f.read()[:-2] # Get rid of CRLF
        sdata = string.split (data, ',')
        if len (sdata) < 9:
            return None

        #print sdata
        # connexion / clock
        self.m_connected = True

        # store for later use
        key = quote.key()

        sclock = sdata[3][1:-1]
        if sclock=="N/A" or sdata[2]=='"N/A"':
            info('invalid datation for %s' % (quote.ticker()))
            return None

        self.m_dcmpd[key] = sdata
        self.m_clock[key] = self.convertClock(sclock)

        # start decoding
        symbol = sdata[0][1:-1]
        if symbol<>sname:
            info('invalid ticker : ask for %s and receive %s' % (sname,symbol))
            return None
        value = string.atof (sdata[1])
        date = self.yahooDate (sdata[2])
        change = string.atof (sdata[4])
        if (sdata[5]=='N/A'):
            debug('invalid open : N/A')
            open = 0.0
            return None
        else:
            open = string.atof (sdata[5])
        if (sdata[6]=='N/A'):
            debug('invalid high : N/A')
            high = 0.0
            return None
        else:
            high = string.atof (sdata[6])
        if (sdata[7]=='N/A'):
            debug('invalid low : N/A')
            low = 0.0
            return None
        else:
            low = string.atof (sdata[7])
        volume = string.atoi (sdata[8])

        # ISIN;DATE;OPEN;HIGH;LOW;CLOSE;VOLUME
        data = (
          key,
          date,
          open,
          high,
          low,
          value,
          volume
        )
        data = map(lambda (val): '%s' % str(val), data)
        data = string.join(data, ';')

        print data
        return data

    # ---[ cache management on data ] ---

    def getcacheddata(self,quote):
        # no cache
        return None

    def iscacheddataenoughfreshq(self):
        # no cache
        return False

    def cacheddatanotfresh(self):
        # no cache
        pass

    # ---[ notebook of order ] ---

    def hasNotebook(self):
        return True

    def currentNotebook(self,quote):
        #
        key = quote.key()
        if not self.m_dcmpd.has_key(key):
            # no data for this quote !
            return [],[]
        d = self.m_dcmpd[key]

        buy = []
        buy.append([0,0,d[9]])

        sell = []
        sell.append([0,0,d[10]])

        return buy,sell

    # ---[ status of quote ] ---

    def hasStatus(self):
        return itrade_config.isConnected()

    def currentStatus(self,quote):
        #
        key = quote.key()
        if not self.m_dcmpd.has_key(key):
            # no data for this quote !
            return "UNKNOWN","::","0.00","0.00","::"
        d = self.m_dcmpd[key]

        st = 'OK'
        cl = '::'
        return st,cl,"-","-",self.m_clock[key]

    def currentClock(self,quote=None):
        if quote==None:
            if self.m_lastclock==0:
                return "::"
            # hh:mm
            return "%d:%02d" % (self.m_lastclock/60,self.m_lastclock%60)
        #
        key = quote.key()
        if not self.m_clock.has_key(key):
            # no data for this quote !
            return "::"
        else:
            return self.m_clock[key]

    def currentTrades(self,quote):
        # clock,volume,value
        return None

    def currentMeans(self,quote):
        # means: sell,buy,last
        return "-","-","-"

# ============================================================================
# Export me
# ============================================================================

try:
    ignore(gLiveYahoo)
except NameError:
    gLiveYahoo = LiveUpdate_yahoo()

registerLiveConnector('NASDAQ','NYC',gLiveYahoo,bDefault=True)
registerLiveConnector('NYSE','NYC',gLiveYahoo,bDefault=True)
registerLiveConnector('AMEX','NYC',gLiveYahoo,bDefault=True)
registerLiveConnector('OTCBB','NYC',gLiveYahoo,bDefault=True)
registerLiveConnector('LSE','LON',gLiveYahoo,bDefault=True)

registerLiveConnector('EURONEXT','PAR',gLiveYahoo,bDefault=False)
registerLiveConnector('ALTERNEXT','PAR',gLiveYahoo,bDefault=False)
registerLiveConnector('PARIS MARCHE LIBRE','PAR',gLiveYahoo,bDefault=False)

# ============================================================================
# Test ME
#
# ============================================================================

def test(ticker):
    if gLiveYahoo.iscacheddataenoughfreshq():
        data = gLiveYahoo.getcacheddata(ticker)
        if data:
            debug(data)
        else:
            debug("nodata")

    elif gLiveYahoo.connect():

        state = gLiveYahoo.getstate()
        if state:
            debug("state=%s" % (state))

            quote = quotes.lookupTicker(ticker,'NASDAQ')
            data = gLiveYahoo.getdata(Quote)
            if data!=None:
                if data:
                    info(data)
                else:
                    debug("nodata")
            else:
                print "getdata() failure :-("
        else:
            print "getstate() failure :-("

        gLiveYahoo.disconnect()
    else:
        print "connect() failure :-("

if __name__=='__main__':
    setLevel(logging.INFO)

    print 'live %s' % date.today()
    test('AAPL')

# ============================================================================
# That's all folks !
# ============================================================================
