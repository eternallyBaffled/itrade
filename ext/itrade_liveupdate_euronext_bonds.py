#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_liveupdate_euronext_bonds.py
#
# Description: Live update quotes from euronext.com : EURONEXT, ALTERNEXT,
# MARCHE LIBRE (PARIS & BRUXELLES)
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is	Gilles Dumortier.
# New code for euronext_bonds is from Michel Legrand.
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
# 2005-06-10    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from __future__ import absolute_import
import logging
import six.moves._thread
import six.moves.urllib.request, six.moves.urllib.error, six.moves.urllib.parse
from contextlib import closing
from datetime import date, datetime

# iTrade system
from itrade_logging import setLevel, debug, info
from itrade_quotes import quotes
from itrade_datation import jjmmaa2yyyymmdd
from itrade_defs import QTag, QList
from itrade_ext import gLiveRegistry
from itrade_market import euronextmic, convertConnectorTimeToPlaceTime
from itrade_connection import ITradeConnection
import itrade_config

# ============================================================================
# LiveUpdate_Euronext_bonds()
#
#  Euronext returns all the quotes then we have to extract only the quote
#  we want to return :-(
#  design idea : if the quote is requested within the same second, use a
#  cached data to extract !
# ============================================================================

class LiveUpdate_Euronext_bonds(object):
    def __init__(self,market='EURONEXT'):
        debug('LiveUpdate_Euronext_bonds:__init__')
        self.m_connected = False
        self.m_livelock = six.moves._thread.allocate_lock()
        self.m_data = None

        self.m_clock = {}
        self.m_dateindice = {}
        self.m_dcmpd = {}
        self.m_lastclock = 0
        self.m_lastdate = "20070101"

        self.m_market = market
        self.m_url = 'https://bonds.nyx.com/fr/nyx_eu_listings/real-time/quote?_=&'

        self.m_connection = ITradeConnection(proxy=itrade_config.proxyHostname,
                                             proxyAuth=itrade_config.proxyAuthentication,
                                             connectionTimeout=itrade_config.connectionTimeout
                                            )

    # ---[ reentrant ] ---
    def acquire(self):
        # not reentrant because of global states : m_viewstate/m_data
        self.m_livelock.acquire()

    def release(self):
        self.m_livelock.release()

    # ---[ properties ] ---
    def name(self):
        return 'euronext_bonds'

    def delay(self):
        return 15

    def timezone(self):
        # timezone of the livedata (see pytz all_timezones)
        return "CET"

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
    def splitLines(self, buf):
        lines = buf.split('\n')
        lines = [x for x in lines if x]
        def removeCarriage(s):
            if s[-1]=='\r':
                return s[:-1]
            else:
                return s
        lines = [removeCarriage(l) for l in lines]
        return lines

    def euronextDate(self, date):
        sp = date.split(' ')
        #print('euronextDate:', sp)

        # Date part is easy
        sdate = jjmmaa2yyyymmdd(sp[0])

        if len(sp) == 1:
            return sdate, "00:00"
        return sdate, sp[1]

    def convertClock(self, place, clock, date):
        min = clock[3:5]
        hour = clock[:2]
        val = (int(hour)*60) + int(min)
        #print 'clock:',clock,hour,min,val
        if val>self.m_lastclock and date>=self.m_lastdate:
            self.m_lastdate = date
            self.m_lastclock = val

        # convert from connector timezone to marketplace timezone
        mdatetime = datetime(int(date[0:4]), int(date[4:6]), int(date[6:8]), val//60, val%60)
        mdatetime = convertConnectorTimeToPlaceTime(mdatetime, self.timezone(), place)

        return u"{:d}:{:02d}".format(mdatetime.hour, mdatetime.minute)

    def parseFValue(self, d):
        val = d.split(',')
        ret = ''
        for val in val:
            ret = ret + val
        return float(ret)

    def parseLValue(self, d):
        if d == '-':
            return 0
        if ',' in d:
            s = ','
        else:
            s = '\xA0'
        val = d.split(s)
        ret = ''
        for val in val:
            ret = ret + val
        return int(ret)

    def getdata(self, quote):
        self.m_connected = False
        debug(u"LiveUpdate_Euronext_bonds:getdata quote:{} market:{}".format(quote, self.m_market))

        mic = euronextmic(quote.market(), quote.place())

        query = (
            ('isin', quote.isin()),
            ('mic', mic),
        )
        query = [u'{}={}'.format(var_val[0], str(var_val[1])) for var_val in query]
        query = '&'.join(query)

        url = self.m_url + query
        print('url_liveupdate:', url)
        debug("LiveUpdate_Euronext_bonds:getdata: url=%s ", url)

        try:
            req = six.moves.urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.5) Gecko/20041202 Firefox/1.0')

            with closing(six.moves.urllib.request.urlopen(req)) as f:
                buf = f.read()

            #buf=self.m_connection.getDataFromUrl(url)
        except Exception:
            debug('LiveUpdate_Euronext_bonds:unable to connect :-(')
            return None

        # pull data
        lines = self.splitLines(buf)

        i = 0
        count = 0
        for eachLine in lines:
            count = count + 1

            if '"datetimeLastvalue">' in eachLine:
                iDate = eachLine[eachLine.find('"datetimeLastvalue">')+20:eachLine.find(' CET</span>')]
                i = i +1

            if '"lastPriceint">' in eachLine:
                lastPriceint = eachLine[eachLine.find('"lastPriceint">')+15:eachLine.find('</span>')].replace(',','.')
                lastPriceint = lastPriceint.replace(',','.')
                i = i +1
            if '"lastPricefract">' in eachLine:
                lastPricefract = eachLine[eachLine.find('"lastPricefract">')+17:eachLine.find('</sup>')]
                i = i +1
                iLast = lastPriceint + lastPricefract

            if '"cnDiffRelvalue">(' in eachLine:
                iPercent = eachLine[eachLine.find('"cnDiffRelvalue">(')+18:eachLine.find(')</span>')]
                iPercent = iPercent.replace('%','').replace(',','.').replace('+','')
                i = i +1

            if '"todayVolumevalue">' in eachLine:
                iVolume = eachLine[eachLine.find('"todayVolumevalue">')+19:eachLine.find('&nbsp')].replace('.','').replace(',','')
                i = i +1

            if '>Ouvert<' in eachLine:
                eachLine = lines[count]
                iOpen = eachLine[:eachLine.find('</td>')].replace(',','.')

                if '%' in iOpen:
                    iOpen = iOpen[iOpen.find('%')+1:]
                elif '$' in iOpen:
                    iOpen = iOpen[iOpen.find('$')+1:]
                elif '&euro;'  in iOpen :
                    iOpen = iOpen[iOpen.find('&euro;')+6:]
                elif '&pound;'  in iOpen :
                    iOpen = iOpen[iOpen.find('&pound;')+7:]

                i = i + 1

            if '"highPricevalue">' in eachLine:
                iHigh = eachLine[eachLine.find('"highPricevalue">')+17:eachLine.find('&nbsp')].replace(',','.')
                count = count + 1
                i = i +1

            if '"lowPricevalue">' in eachLine:
                iLow = eachLine[eachLine.find('"lowPricevalue">')+16:eachLine.find('&nbsp')].replace(',','.')
                count = count + 1
                i = i +1

            if i == 8:
                count = 0
                i = 0
                c_datetime = datetime.today()
                c_date = u"{:04d}{:02d}{:02d}".format(c_datetime.year, c_datetime.month, c_datetime.day)
                #print 'Today is :', c_date

                sdate, sclock = self.euronextDate(iDate)

                # be sure we have volume (or indices)
                if quote.list() == QList.indices or iVolume != '':
                    # be sure not an oldest day !
                    if (c_date == sdate) or (quote.list() == QList.indices):
                        key = quote.key()
                        self.m_dcmpd[key] = sdate
                        self.m_dateindice[key] = str(sdate[6:8]) + '/' + str(sdate[4:6]) + '/' + str(sdate[0:4])
                        self.m_clock[key] = self.convertClock(quote.place(), sclock, sdate)

                    # ISIN;DATE;OPEN;HIGH;LOW;CLOSE;VOLUME;PERCENT
                    data = ';'.join([quote.key(), sdate, iOpen, iHigh, iLow, iLast, iVolume, iPercent])
                    return data
        return None

    # ---[ cache management on data ] ---
    def getcacheddata(self, quote):
        return None

    def iscacheddataenoughfreshq(self):
        return False

    def cacheddatanotfresh(self):
        # no cache
        pass

    # ---[ notebook of order ] ---
    def hasNotebook(self):
        return False

    # ---[ status of quote ] ---
    def hasStatus(self):
        return itrade_config.isConnected()

    def currentStatus(self, quote):
        key = quote.key()
        if key not in self.m_dcmpd:
            # no data for this quote !
            return "UNKNOWN", "::", "0.00", "0.00", "::"

        st = 'OK'
        cl = '::'
        return st, cl, "-", "-", self.m_clock[key]

    def currentTrades(self, quote):
        # clock,volume,value
        return None

    def currentMeans(self, quote):
        # means: sell, buy, last
        return "-", "-", "-"

    def currentClock(self, quote=None):
        if quote is None:
            if self.m_lastclock == 0:
                return "::"
            # hh:mm
            return u"{:d}:{:02d}".format(self.m_lastclock//60, self.m_lastclock%60)
        #
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
            return self.m_dateindice[key]

# ============================================================================
# Export me
# ============================================================================


gLiveEuronextBonds = LiveUpdate_Euronext_bonds()


gLiveRegistry.register('EURONEXT', 'PAR', QList.bonds, QTag.live, gLiveEuronextBonds, bDefault=True)
gLiveRegistry.register('EURONEXT', 'BRU', QList.bonds, QTag.live, gLiveEuronextBonds, bDefault=True)
gLiveRegistry.register('EURONEXT', 'AMS', QList.bonds, QTag.live, gLiveEuronextBonds, bDefault=True)
gLiveRegistry.register('EURONEXT', 'LIS', QList.bonds, QTag.live, gLiveEuronextBonds, bDefault=True)

# ============================================================================
# Test ME
#
# ============================================================================

def test(ticker):
    if gLiveEuronextBonds.iscacheddataenoughfreshq():
        data = gLiveEuronextBonds.getcacheddata(ticker)
        if data:
            debug(data)
        else:
            debug("nodata")

    elif gLiveEuronextBonds.connect():
        state = gLiveEuronextBonds.getstate()
        if state:
            debug(u"state={}".format(state))

            quote = quotes.lookupTicker(ticker=ticker, market='EURONEXT')
            if quote:
                data = gLiveEuronextBonds.getdata(quote)
                if data is not None:
                    if data:
                        info(data)
                    else:
                        debug("nodata")
                else:
                    print("getdata() failure :-(")
            else:
                print(u"Unknown ticker {} on EURONEXT".format(ticker))
        else:
            print("getstate() failure :-(")

        gLiveEuronextBonds.disconnect()
    else:
        print("connect() failure :-(")

if __name__ == '__main__':
    setLevel(logging.DEBUG)

    print(u'live {}'.format(date.today()))

   # load euronext import extension
    import itrade_ext
    itrade_ext.loadOneExtension('itrade_import_euronext.py', itrade_config.dirExtData)
    quotes.loadMarket('EURONEXT')

    test('OSI')
    test('GTO')
    gLiveEuronextBonds.cacheddatanotfresh()
    test('GTO')

# ============================================================================
# That's all folks !
# ============================================================================
