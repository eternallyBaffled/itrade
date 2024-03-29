#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_liveupdate_realtime.py(boursorama)
#
# Description: Live update quotes from abcbourse.com
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is	Gilles Dumortier.
# New code for realtime is from Jean-Marie Pacquet and Michel Legrand.

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
# 2005-03-25    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from __future__ import absolute_import
from contextlib import closing
from datetime import date, datetime
import logging
import six.moves._thread
import os
import six.moves.urllib.request, six.moves.urllib.error, six.moves.urllib.parse
import six.moves.cPickle

# iTrade system
import itrade_config
from itrade_logging import setLevel, debug, info
from itrade_datation import jjmmaa2yyyymmdd
from itrade_quotes import quotes
from itrade_defs import QList, QTag
from itrade_ext import gLiveRegistry
from itrade_market import convertConnectorTimeToPlaceTime
from itrade_connection import ITradeConnection

# ============================================================================
# LiveUpdate_RealTime()
#
# ============================================================================

class LiveUpdate_RealTime(object):
    def __init__(self, market='EURONEXT'):
        debug('LiveUpdate_RealTime:__init__')
        self.m_connected = False
        self.m_livelock = six.moves._thread.allocate_lock()
        self.m_conn = None
        self.m_clock = {}
        self.m_dateindice = {}
        self.m_dcmpd = {}
        self.m_lastclock = 0
        self.m_lastdate = "20070101"
        self.m_market = market
        self.m_connection = ITradeConnection(proxy=itrade_config.proxyHostname,
                                             proxyAuth=itrade_config.proxyAuthentication,
                                             connectionTimeout=itrade_config.connectionTimeout
                                            )

        try:
            select_isin = []
            self.m_isinsymbol = {}
            symbol = ''

            # try to open dictionary of ticker_bourso.txt
            with open(os.path.join(itrade_config.dirUserData, 'ticker_bourso.txt'), 'r') as f:
                self.m_isinsymbol = six.moves.cPickle.load(f)

        except Exception:
            print('Missing or invalid file: ticker_bourso.txt')

            # read isin codes of properties.txt file in directory usrdata
            try:
                with open(os.path.join(itrade_config.dirUserData, 'properties.txt'), 'r') as source:
                    data = source.readlines()

                for linedata in data:
                    if 'live;realtime' in linedata:
                        isin = linedata[:linedata.find('.')]
                        debug(u'isin:{}'.format(isin))
                        select_isin.append(isin)
                        debug(u'{}'.format(select_isin))

                # extract pre_symbol
                for isin in select_isin:
                    req = six.moves.urllib.request.Request('https://www.boursorama.com/recherche/index.phtml?search%5Bquery%5D=' + isin)
                    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.5) Gecko/20041202 Firefox/1.0')
                    try:
                        with closing(six.moves.urllib.request.urlopen(req)) as f:
                            data = f.read()

                        ch = 'class="bourse fit block" >'

                        if data.find(ch) != -1:
                            b = data.find(ch)
                            if data.find('>Valeurs<', b) != - 1:
                                if data.find('class="exchange">Nyse Euro<', b) != -1:
                                    c = data.find('class="exchange">Nyse Euro<', b)
                                    a = data.rfind('href="/cours.phtml?symbole=', 0, c)
                                    symbol = data[a+27:a+43]
                                    symbol = symbol[:symbol.find('" >')]
                                    self.m_isinsymbol [isin] = symbol
                                    debug(u'{} found and added in dictionary ({})'.format(isin, symbol))
                    except Exception:
                        pass

                with open(os.path.join(itrade_config.dirUserData,'ticker_bourso.txt'), 'w') as dic:
                    six.moves.cPickle.dump(self.m_isinsymbol, dic)

            except Exception:
                pass

    # ---[ reentrant ] ---
    def acquire(self):
        self.m_livelock.acquire()

    def release(self):
        self.m_livelock.release()

    # ---[ properties ] ---

    def name(self):
        return 'realtime'

    def delay(self):
        return 0

    def timezone(self):
        # timezone of the livedata (see pytz all_timezones)
        return "Europe/Paris"

    # ---[ connection ] ---

    def connect(self):
        return True

    def disconnect(self):
        #pass
        if self.m_conn:
            self.m_conn.close()
        self.m_conn = None
        self.m_connected = False

    def alive(self):
        return self.m_connected

    # ---[ state ] ---

    def getstate(self):
        # no state
        return True

    # ---[ code to get data ] ---

    def splitLines(self, data):
        lines = data.split('\n')
        lines = [x for x in lines if x]
        def removeCarriage(s):
            if s[-1] == '\r':
                return s[:-1]
            else:
                return s
        lines = [removeCarriage(l) for l in lines]
        return lines

    def BoursoDate(self, date):
        sp = date.split(' ')

        # Date part is easy
        sdate = jjmmaa2yyyymmdd(sp[0])

        if len(sp) == 1:
            return sdate, "00:00"
        return sdate, sp[1]

    def convertClock(self, place, clock, date):
        min = clock[3:5]
        hour = clock[:2]
        val = (int(hour)*60) + int(min)

        if val > self.m_lastclock and date >= self.m_lastdate:
            self.m_lastdate = date
            self.m_lastclock = val

        # convert from connector timezone to marketplace timezone
        mdatetime = datetime(int(date[0:4]), int(date[4:6]), int(date[6:8]), val//60, val%60)
        mdatetime = convertConnectorTimeToPlaceTime(mdatetime, self.timezone(), place)

        return u"{:d}:{:02d}".format(mdatetime.hour, mdatetime.minute)

    def getdata(self, quote):
        self.m_connected = False
        debug(u"LiveUpdate_Bousorama:getdata quote:{} market:{}".format(quote, self.m_market))

        isin = quote.isin()

        # add a value, default is yahoo connector
        # with boursorama realtime connector, must have pre_symbol to extract quote

        if isin != '':
            if not isin in self.m_isinsymbol:
                req = six.moves.urllib.request.Request('https://www.boursorama.com/recherche/index.phtml?search%5Bquery%5D=' + isin)
                req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.5) Gecko/20041202 Firefox/1.0')

                try:
                    with closing(six.moves.urllib.request.urlopen(req)) as f:
                        data = f.read()

                    ch = 'class="bourse fit block" >'

                    if data.find(ch) != -1:
                        b = data.find(ch)
                        if data.find('>Valeurs<', b) != - 1:
                            if data.find('class="exchange">Nyse Euro<', b) != -1:
                                c = data.find('class="exchange">Nyse Euro<', b)
                                a = data.rfind('href="/cours.phtml?symbole=', 0, c)
                                symbol = data[a+27:a+43]
                                symbol = symbol[:symbol.find('" >')]
                                self.m_isinsymbol [isin] = symbol
                                debug(u'{} found and added in dictionary ({})'.format(isin, symbol))
                                with open(os.path.join(itrade_config.dirUserData, 'ticker_bourso.txt'), 'w') as dic:
                                    six.moves.cPickle.dump(self.m_isinsymbol, dic)
                            else:
                                return None
                        else:
                            return None
                    else:
                        return None

                except Exception:
                    debug('LiveUpdate_Boursorama:unable to connect :-(')
                    return None
        else:
            return None

        symbol = self.m_isinsymbol[isin]
        debug(u'Symbol={}'.format(symbol))

        # extract all datas

        try:
            if ('1rT' in symbol or
               '1RT' in symbol or
               '1z' in symbol or
               '1g' in symbol):
                req = six.moves.urllib.request.Request('https://www.boursorama.com/bourse/trackers/etf.phtml?symbole=' + symbol)
            else:
                req = six.moves.urllib.request.Request('https://www.boursorama.com/cours.phtml?symbole=' + symbol)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.5) Gecko/20041202 Firefox/1.0')

            with closing(six.moves.urllib.request.urlopen(req)) as f:
                data = f.read()
        except Exception:
            debug('LiveUpdate_Boursorama:unable to connect :-(')
            return None

        data = data.replace('\t', '').replace('</span>', '')
        lines = self.splitLines(data)
        n = -1
        for line in lines:
            n = n + 1
            if '<table class="info-valeur list">' in line:
                line = lines[n+6]
                value = line[line.find('"cotation">')+11:line.find('</b>')]
                if '(' in value:
                    stat = value[value.find('(')+1:value.find(')')]
                else:
                    stat = ''
                if ('USD' in value or
                   'GBX' in value or
                   'GBP' in value or
                   'CAD' in value or
                   'CHF' in value):
                    pass
                else:
                    last = value.replace(' ', '').replace('EUR', '').replace('Pts', '').replace('(s)', '').replace('(c)', '').replace('(h)', '').replace('(u)', '')
                    last = last.replace('%', '')
                    line = lines[n+11]
                    percent = line[line.rfind('">')+2:line.find('%</td>')].replace(' ', '')

                    line = lines[n+15]
                    date_time = line[line.find('<td>')+4:line.find('</td>')]
                    date_time = date_time[:8]+' '+date_time[-8:]

                    line = lines[n+19]
                    volume = line[line.rfind('">')+2:line.find('</td>')].replace(' ', '').replace('<td>', '').replace('td>', '')
                    if 'M' in line:
                        volume = '0'
                    if volume == '0' and quote.list() != QList.indices:
                        #info(u'volume : no trade to day {}'.format(symbol))
                        return None
                    line = lines[n+23]
                    first = line[line.find('"cotation">')+11:line.find('</td>')].replace(' ', '')

                    line = lines[n+27]
                    high = (line[line.find('"cotation">')+11:line.find('</td>')]).replace(' ', '')

                    line = lines[n+31]
                    low = line[line.find('"cotation">')+11:line.find('</td>')].replace(' ', '')

                    line = lines[n+35]
                    previous = line[line.find('"cotation">')+11:line.find('</td>')].replace(' ', '')

                    c_datetime = datetime.today()
                    c_date = u"{:04d}{:02d}{:02d}".format(c_datetime.year, c_datetime.month, c_datetime.day)

                    sdate, sclock = self.BoursoDate(date_time)

                    # be sure not an oldest day !
                    if (c_date == sdate) or (quote.list() == QList.indices):
                        key = quote.key()
                        self.m_dcmpd[key] = sdate
                        self.m_dateindice[key] = str(sdate[6:8]) + '/' + str(sdate[4:6]) + '/' + str(sdate[0:4])
                        self.m_clock[key] = self.convertClock(quote.place(), sclock, sdate)

                    data = ';'.join([quote.key(), sdate, first, high, low, last, volume, percent])
                    #print("connect to Boursorama", quote.key())
                    return data
        return None

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
        return False

    def currentNotebook(self, quote):
        key = quote.key()
        if key not in self.m_dcmpd:
            # no data for this quote !
            return [], []
        d = self.m_dcmpd[key]

        buy = []
        #buy.append([0, 0, '-'])

        sell = []
        #sell.append([0, 0, '-'])

        return buy, sell

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
            return self.m_dateindice[key]

    def currentTrades(self, quote):
        # clock,volume,value
        return None

    def currentMeans(self, quote):
        # means: sell, buy, last
        return "-", "-", "-"


# ============================================================================
# Export me
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.DEBUG)
gLiveRealTime = LiveUpdate_RealTime()
gLiveAlternext = LiveUpdate_RealTime()

gLiveRegistry.register('EURONEXT', 'PAR', QList.any, QTag.live, gLiveRealTime, bDefault=False)
#gLiveRegistry.register('EURONEXT', 'BRU', QList.any, QTag.live, gLiveRealTime, bDefault=False)
#gLiveRegistry.register('EURONEXT', 'AMS', QList.any, QTag.live, gLiveRealTime, bDefault=False)
#gLiveRegistry.register('EURONEXT', 'LIS', QList.any, QTag.live, gLiveRealTime, bDefault=False)
gLiveRegistry.register('EURONEXT', 'PAR', QList.indices, QTag.live, gLiveRealTime, bDefault=False)
gLiveRegistry.register('EURONEXT', 'BRU', QList.indices, QTag.live, gLiveRealTime, bDefault=False)
gLiveRegistry.register('EURONEXT', 'AMS', QList.indices, QTag.live, gLiveRealTime, bDefault=False)
gLiveRegistry.register('EURONEXT', 'LIS', QList.indices, QTag.live, gLiveRealTime, bDefault=False)
gLiveRegistry.register('ALTERNEXT', 'PAR', QList.any, QTag.live, gLiveRealTime, bDefault=False)

#gLiveRegistry.register('ALTERNEXT', 'AMS', QList.any, QTag.live, gLiveRealTime, bDefault=False)
#gLiveRegistry.register('ALTERNEXT', 'BRU', QList.any, QTag.live, gLiveRealTime, bDefault=False)
#gLiveRegistry.register('ALTERNEXT', 'LIS', QList.any, QTag.live, gLiveRealTime, bDefault=False)

gLiveRegistry.register('PARIS MARCHE LIBRE', 'PAR', QList.any, QTag.live, gLiveRealTime, bDefault=False)
#gLiveRegistry.register('BRUXELLES MARCHE LIBRE', 'BRU', QList.any, QTag.live, gLiveRealTime, bDefault=False)

# ============================================================================
# Test ME
#
# ============================================================================

def test(ticker):
    if gLiveRealTime.iscacheddataenoughfreshq():
        data = gLiveRealTime.getcacheddata(ticker)
        if data:
            debug(data)
        else:
            debug("nodata")

    elif gLiveRealTime.connect():

        state = gLiveRealTime.getstate()
        if state:
            debug(u"state={}".format(state))

            quote = quotes.lookupTicker(ticker=ticker, market='EURONEXT')
            if quote:
                data = gLiveRealTime.getdata(quote)
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

        gLiveRealTime.disconnect()
    else:
        print("connect() failure :-(")

if __name__ == '__main__':
    print(u'live {}'.format(date.today()))
   # load euronext import extension
    import itrade_ext
    itrade_ext.loadOneExtension('itrade_import_euronext.py', itrade_config.dirExtData)
    quotes.loadMarket('EURONEXT')

    test('OSI')
    test('GTO')
    gLiveRealTime.cacheddatanotfresh()
    test('GTO')

# ============================================================================
# That's all folks !
# ============================================================================
