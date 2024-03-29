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
from __future__ import absolute_import
import logging
from datetime import date, datetime
import re
import six.moves._thread
import time
from pytz import timezone

# iTrade system
import itrade_config
from itrade_logging import setLevel, debug, info
from itrade_quotes import quotes, Quote
from itrade_defs import QList, QTag
from itrade_ext import gLiveRegistry
from itrade_market import yahooTicker, yahooUrl, convertConnectorTimeToPlaceTime
from itrade_connection import ITradeConnection

# ============================================================================
# LiveUpdate_yahoo()
#
# ============================================================================

class LiveUpdate_yahoo(object):
    def __init__(self):
        debug('LiveUpdate_yahoo:__init__')

        self.m_connected = False
        self.m_livelock = six.moves._thread.allocate_lock()
        self.m_dateindice = {}
        self.m_clock = {}
        self.m_dcmpd = {}
        self.m_lastclock = 0
        self.m_lastdate = "20070101"

        self.m_connection = ITradeConnection(proxy=itrade_config.proxyHostname,
                                             proxyAuth=itrade_config.proxyAuthentication,
                                             connectionTimeout=itrade_config.connectionTimeout
                                            )

    # ---[ reentrant ] ---
    def acquire(self):
        self.m_livelock.acquire()

    def release(self):
        self.m_livelock.release()

    # ---[ properties ] ---
    def name(self):
        # name of the connector
        return 'yahoo'

    def delay(self):
        # delay in minuts to get a live data
        # put 0 if no delay (realtime)
        return 15

    def timezone(self):
        # timezone of the livedata (see pytz all_timezones)
        return "EST"

    # ---[ connection ] ---
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
    def yahooDate (self, date):
        # Date part is easy.
        sdate = date[1:-1].split('/')
        month = int(sdate[0])
        day = int(sdate[1])
        year = int(sdate[2])

        return u"{:4d}{:02d}{:02d}".format(year, month, day)

    def convertClock(self, place, clock, date):
        clo = clock[:-2]
        min = clo[-2:]
        hour = clo[:-3]
        val = (int(hour)*60) + int(min)
        per = clock[-2:]
        if per == 'pm':
            if int(hour) < 12:
                val = val + 12*60
        elif per == 'am':
            if int(hour) >= 12:
                val = val - 12*60

        # yahoo return EDT OR EST time
        eastern = timezone('US/Eastern')
        mdatetime = datetime(int(date[0:4]), int(date[4:6]), int(date[6:8]), val//60, val%60)
        loc_dt = eastern.localize(mdatetime)
        if str(loc_dt.strftime('%Z')) == 'EDT':
            val = val-60
            if val <= 0:
                val = (12*60)-60

        #print(clock, clo, hour, min, val, per, date)

        if val > self.m_lastclock and date >= self.m_lastdate:
            self.m_lastdate = date
            self.m_lastclock = val

        # convert from connector timezone to marketplace timezone
        mdatetime = datetime(int(date[0:4]), int(date[4:6]), int(date[6:8]), val//60, val%60)
        mdatetime = convertConnectorTimeToPlaceTime(mdatetime, self.timezone(), place)
        return u"{:d}:{:02d}".format(mdatetime.hour, mdatetime.minute)

    def getdata(self, quote):
        debug(u"LiveUpdate_yahoo:getdata quote:{} ".format(quote))
        self.m_connected = False

        sname = yahooTicker(quote.ticker(), quote.market(), quote.place())

        if sname[0] == '^':
            ss = "%5E" + sname[1:]
        else:
            ss = sname


        query = (
            ('s', ss),
            ('f', 'sl1d1t1c1ohgv'),
            ('e', '.csv'),
        )
        query = [u'{}={}'.format(var_val[0], str(var_val[1])) for var_val in query]
        query = '&'.join(query)
        url = yahooUrl(quote.market(), live=True) + '?' + query

        debug("LiveUpdate_yahoo:getdata: url=%s", url)
        try:
            data = self.m_connection.getDataFromUrl(url)[:-2]  # Get rid of CRLF
        except Exception:
            debug('LiveUpdate_yahoo:unable to connect :-(')
            return None

        # pull data
        s400 = re.search(r"400 Bad Request", data, re.IGNORECASE|re.MULTILINE)
        if s400:
            if itrade_config.verbose:
                info(u'unknown {} quote (400 Bad Request) from Yahoo'.format(quote.ticker()))
            return None

        sdata = data.split(',')
        if len (sdata) < 9:
            if itrade_config.verbose:
                info(u'invalid data (bad answer length) for {} quote'.format(quote.ticker()))
            return None

        #print(sdata)

        # connection / clock
        self.m_connected = True

        # store for later use
        key = quote.key()

        sclock = sdata[3][1:-1]
        if sclock == "N/A" or sdata[2] == '"N/A"' or len(sclock) < 5:
            if itrade_config.verbose:
                info(u'invalid datation for {} : {} {}'.format(quote.ticker(), sclock, sdata[2]))
                #print sdata
            return None

        # start decoding
        symbol = sdata[0][1:-1]
        if symbol != sname:
            if itrade_config.verbose:
                info(u'invalid ticker : ask for {} and receive {}'.format(sname, symbol))
            return None

        # date
        try:
            date = self.yahooDate(sdata[2])
            self.m_dcmpd[key] = sdata
            self.m_clock[key] = self.convertClock(quote.place(), sclock, date)
            self.m_dateindice[key] = sdata[2].replace('"', '')
        except ValueError:
            if itrade_config.verbose:
                info(u'invalid datation for {} : {} {}'.format(quote.ticker(), sclock, sdata[2]))
            return None

        # decode data
        value = float(sdata[1])

        if sdata[4] == 'N/A':
            debug('invalid change : N/A')
            change = 0.0
            return None
        else:
            change = float(sdata[4])
        if sdata[5] == 'N/A':
            debug('invalid open : N/A')
            open = 0.0
            return None
        else:
            open = float(sdata[5])
        if sdata[6] == 'N/A':
            debug('invalid high : N/A')
            high = 0.0
            return None
        else:
            high = float(sdata[6])
        if sdata[7] == 'N/A':
            debug('invalid low : N/A')
            low = 0.0
            return None
        else:
            low = float(sdata[7])

        volume = int(sdata[8])
        if volume < 0:
            debug(u'volume : invalid negative {:d}'.format(volume))
            return None
        if volume == 0 and quote.list() != QList.indices:
            debug(u'volume : invalid zero value {:d}'.format(volume))
            return None
        else:
            if value-change <= 0:
                return None
            else:
                percent = (change / (value - change))*100.0

        # ISIN;DATE;OPEN;HIGH;LOW;CLOSE;VOLUME;PERCENT;PREVIOUS
        data = (
          key,
          date,
          open,
          high,
          low,
          value,
          volume,
          percent,
          (value-change)
        )
        data = [u'{}'.format(str(val)) for val in data]
        data = ';'.join(data)

        # temp: hunting an issue (SF bug 1848473)
        # if itrade_config.verbose:
        #    print data

        return data

    # ---[ cache management on data ] ---

    def getcacheddata(self, quote):
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

    def currentNotebook(self, quote):
        key = quote.key()

        if key not in self.m_dcmpd:
            # no data for this quote !
            return [], []
        d = self.m_dcmpd[key]

        #buy = []
        #buy.append([0, 0, d[9]])

        #sell = []
        #sell.append([0, 0, d[10]])

        #return buy, sell
        return [], []

    # ---[ status of quote ] ---
    def hasStatus(self):
        return itrade_config.isConnected()

    def currentStatus(self, quote):
        key = quote.key()
        if key not in self.m_dcmpd:
            # no data for this quote !
            return "UNKNOWN", "::", "0.00", "0.00", "::"
        d = self.m_dcmpd[key]

        st = 'OK'
        cl = '::'
        return st, cl, "-", "-", self.m_clock[key]

    def currentClock(self, quote=None):
        if quote is None:
            if self.m_lastclock == 0:
                return "::"
            # hh:mm
            return u"{:d}:{:02d}".format(self.m_lastclock//60, self.m_lastclock%60)

        key = quote.key()
        if key not in self.m_clock:
            # no data for this quote !
            return "::"
        else:
            return self.m_clock[key]

    def currentDate(self, quote=None):
        key = quote.key()
        if key not in self.m_dateindice:
            # no date for this quote !
            return "----"
        else:
            # convert yahoo date
            conv = time.strptime(self.m_dateindice[key], "%m/%d/%Y")
            return time.strftime("%d/%m/%Y", conv)

    def currentTrades(self, quote):
        # clock,volume,value
        return None

    def currentMeans(self, quote):
        # means: sell, buy, last
        return "-", "-", "-"

# ============================================================================
# Export me
# ============================================================================


gLiveYahoo = LiveUpdate_yahoo()

gLiveRegistry.register('NASDAQ','NYC',QList.any,QTag.differed,gLiveYahoo,bDefault=True)
gLiveRegistry.register('NYSE','NYC',QList.any,QTag.differed,gLiveYahoo,bDefault=True)
gLiveRegistry.register('AMEX','NYC',QList.any,QTag.differed,gLiveYahoo,bDefault=True)
gLiveRegistry.register('OTCBB','NYC',QList.any,QTag.differed,gLiveYahoo,bDefault=True)
gLiveRegistry.register('LSE','LON',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('ASX','SYD',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('TORONTO VENTURE','TOR',QList.any,QTag.differed,gLiveYahoo,bDefault=True)
gLiveRegistry.register('TORONTO EXCHANGE','TOR',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('LSE SETS','LON',QList.any,QTag.differed,gLiveYahoo,bDefault=True)
gLiveRegistry.register('LSE SETSqx','LON',QList.any,QTag.differed,gLiveYahoo,bDefault=True)
gLiveRegistry.register('LSE SEAQ','LON',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('MILAN EXCHANGE','MIL',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('SWISS EXCHANGE','XSWX',QList.any,QTag.differed,gLiveYahoo,bDefault=True)
gLiveRegistry.register('SWISS EXCHANGE','XVTX',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('EURONEXT','PAR',QList.any,QTag.differed,gLiveYahoo,bDefault=True)
gLiveRegistry.register('EURONEXT','BRU',QList.any,QTag.differed,gLiveYahoo,bDefault=True)
gLiveRegistry.register('EURONEXT','AMS',QList.any,QTag.differed,gLiveYahoo,bDefault=True)
gLiveRegistry.register('EURONEXT','LIS',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('EURONEXT','PAR',QList.indices,QTag.differed,gLiveYahoo,bDefault=True)
gLiveRegistry.register('EURONEXT','AMS',QList.indices,QTag.differed,gLiveYahoo,bDefault=True)
gLiveRegistry.register('EURONEXT','BRU',QList.indices,QTag.differed,gLiveYahoo,bDefault=True)
gLiveRegistry.register('EURONEXT','LIS',QList.indices,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('ALTERNEXT','PAR',QList.any,QTag.differed,gLiveYahoo,bDefault=True)
gLiveRegistry.register('ALTERNEXT','AMS',QList.any,QTag.differed,gLiveYahoo,bDefault=True)
gLiveRegistry.register('ALTERNEXT','BRU',QList.any,QTag.differed,gLiveYahoo,bDefault=True)
gLiveRegistry.register('ALTERNEXT','LIS',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('PARIS MARCHE LIBRE','PAR',QList.any,QTag.differed,gLiveYahoo,bDefault=True)
gLiveRegistry.register('PARIS MARCHE LIBRE','BRU',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('BRUXELLES MARCHE LIBRE','BRU',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('IRISH EXCHANGE','DUB',QList.any,QTag.differed,gLiveYahoo,bDefault=True)
gLiveRegistry.register('MADRID EXCHANGE','MAD',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('FRANKFURT EXCHANGE','FRA',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('STOCKHOLM EXCHANGE','STO',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('COPENHAGEN EXCHANGE','CSE',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('OSLO EXCHANGE','OSL',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('SAO PAULO EXCHANGE','SAO',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('HONG KONG EXCHANGE','HKG',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('SHANGHAI EXCHANGE','SHG',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('SHENZHEN EXCHANGE','SHE',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('NATIONAL EXCHANGE OF INDIA','NSE',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('BOMBAY EXCHANGE','BSE',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('NEW ZEALAND EXCHANGE','NZE',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('BUENOS AIRES EXCHANGE','BUE',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('MEXICO EXCHANGE','MEX',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('SINGAPORE EXCHANGE','SGX',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('KOREA STOCK EXCHANGE','KRX',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('KOREA KOSDAQ EXCHANGE','KOS',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('WIENER BORSE','WBO',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

gLiveRegistry.register('TAIWAN STOCK EXCHANGE','TAI',QList.any,QTag.differed,gLiveYahoo,bDefault=True)

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
            debug(u"state={}".format(state))

            quote = quotes.lookupTicker(ticker=ticker, market='NASDAQ')
            data = gLiveYahoo.getdata(Quote)
            if data is not None:
                if data:
                    info(data)
                else:
                    debug("nodata")
            else:
                print("getdata() failure :-(")
        else:
            print("getstate() failure :-(")

        gLiveYahoo.disconnect()
    else:
        print("connect() failure :-(")

if __name__ == '__main__':
    setLevel(logging.INFO)

    print(u'live {}'.format(date.today()))
    test('AAPL')

# ============================================================================
# That's all folks !
# ============================================================================
