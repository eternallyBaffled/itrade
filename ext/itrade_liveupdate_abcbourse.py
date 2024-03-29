#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_liveupdate_abcbourse.py
#
# Description: Live update quotes from abcbourse.com
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
# 2005-03-25    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from __future__ import absolute_import
import logging
import re
import six.moves._thread
from datetime import date, datetime, timedelta

from six.moves.urllib.parse import urlencode
from six.moves.http_client import HTTPConnection

# iTrade system
import itrade_config
import itrade_csv
from itrade_logging import setLevel, debug, info
from itrade_quotes import quotes

# ============================================================================
# LiveUpdate_ABCBourse()
#
#  abcbourse returns all the quotes then we have to extract only the quote
#  we want to return :-(
#  design idea : if the quote is requested within the same second, use a
#  cached data to extract !
# ============================================================================

class LiveUpdate_ABCBourse(object):
    def __init__(self):
        debug('LiveUpdate_ABCBourse:__init__')
        self.m_host = "download.abcbourse.com"
        self.m_conn = None
        self.m_url = "/telechargement_intraday.aspx"
        self.m_viewstate = None
        self.m_data = None
        self.m_clock = "::"
        self.m_livelock = six.moves._thread.allocate_lock()

    # ---[ reentrant ] ---
    def acquire(self):
        # not reentrant because of global states : m_viewstate/m_data
        self.m_livelock.acquire()

    def release(self):
        self.m_livelock.release()

    # ---[ properties ] ---

    def name(self):
        return 'abcbourse'

    def delay(self):
        return 15

    def timezone(self):
        # timezone of the livedata (see pytz all_timezones)
        return "Europe/Paris"

    # ---[ connection ] ---

    def connect(self):
        debug('LiveUpdate_ABCBourse:connect to web site')
        try:
            self.m_conn = HTTPConnection(self.m_host,80)
        except Exception:
            debug('LiveUpdate_ABCBourse:unable to connect :-(')
            return False
        return True

    def disconnect(self):
        if self.m_conn:
            self.m_conn.close()
        self.m_conn = None

    def alive(self):
        return self.m_data is not None

    # ---[ state ] ---

    def getstate(self):
        # check we have a connection
        if not self.m_conn:
            raise Exception('LiveUpdate_ABCBourse:no connection')

        # init headers
        headers = { "Keep-Alive":300, "Accept-Charset:":"ISO-8859-1", "Accept-Language": "en-us,en", "Accept": "text/html,text/plain", "Connection": "keep-alive", "Host": self.m_host }

        # GET the main download page
        try:
            self.m_conn.request("GET", self.m_url, None, headers)
            response = self.m_conn.getresponse()
        except Exception:
            debug('LiveUpdate_ABCBourse:GET failure')
            return None

        debug(u"status:{} reason:{}".format(response.status, response.reason))
        if response.status != 200:
            debug('LiveUpdate_ABCBourse:status!=200')
            return None

        # search for the ___VIEWSTATE variable
        data = response.read()
        m = re.search(r'name=\"__VIEWSTATE\"\s*value=\"\S+\"', data)
        if m is None:
            debug('LiveUpdate_ABCBourse:viewstate statement not found !')
            return None

        # extract the variable content
        m = m.group()[26:-1]
        self.m_viewstate = m

        return m

    # ---[ code to get data ] ---

    def getdata(self,quote):
        # check we have a connection
        if not self.m_conn:
            raise Exception('LiveUpdate_ABCBourse:no connection / missing connect() call !')
        # check we have a viewstate
        if not self.m_viewstate:
            raise Exception('LiveUpdate_ABCBourse:no viewstate / missing getstate() call !')

        debug(u"LiveUpdate_ABCBourse:getdata quote:{} ".format(quote))

        # init params and headers
        params = urlencode({'f': 'ebp', '__VIEWSTATE': self.m_viewstate, 'm': 'complet', 'ImageButton1.x': 4, 'ImageButton1.y': 13 })
        debug(params)
        headers = { "Keep-Alive":300, "Accept-Charset:":"ISO-8859-1", "Accept-Language": "en-us,en", "Content-type": "application/x-www-form-urlencoded", "Accept": "text/html,text/plain", "Connection": "keep-alive", "Host": self.m_host  }

        # POST the request
        try:
            self.m_conn.request("POST", self.m_url, params, headers)
            response = self.m_conn.getresponse()
        except Exception:
            debug('LiveUpdate_ABCBourse:POST failure')
            return None

        debug(u"status:{} reason:{}".format(response.status, response.reason))
        if response.status != 200:
            debug('LiveUpdate_ABCBourse:status!=200')
            return None

        # returns the data
        data = response.read()
        self.m_datatime = datetime.today()
        self.m_clock = u"{:d}:{:02d}".format(self.m_datatime.hour, self.m_datatime.minute)

        debug(u'!!! datatime = {} clock={}'.format(self.m_datatime, self.m_clock))

        # detect EBP file then split by line
        if data[:8] != "30111998":
            self.m_data = ""
            return ""
        self.m_data = data[8:].split('\r\n')

        # extract the quote we are looking for
        return self.getcacheddata(quote)

    # ---[ cache management on data ] ---

    def getcacheddata(self, quote):
        debug(u'getcacheddata {}'.format(self.m_data))
        for eachLine in self.m_data:
            item = itrade_csv.parse(eachLine, 7)
            if item:
                if item[0] == quote.isin():
                    #print item
                    # convert to string format :-(
                    return u'{};{};{};{};{};{};{}'.format(item[0], item[1], item[2], item[3], item[4], item[5], item[6])
        return ""

    def iscacheddataenoughfreshq(self):
        if self.m_data is None:
            #print
            debug('iscacheddataenoughfreshq : no cache !')
            return False
        if not self.m_datatime:
            debug('iscacheddataenoughfreshq : no data time !')
            return False
        delta = timedelta(0, itrade_config.cachedDataFreshDelay)
        newtime = self.m_datatime + delta
        if datetime.today() > newtime:
            debug(u'datatime = {}  currentdatatime = {}  newtime = {} delta = {} : False'.format(self.m_datatime, datetime.today(), newtime, delta))
            return False
        debug(u'datatime = {}  currentdatatime = {}  newtime = {} delta = {} : True'.format(self.m_datatime, datetime.today(), newtime,delta))
        return True

    def cacheddatanotfresh(self):
        self.m_data = None

    # ---[ notebook of order ] ---

    def hasNotebook(self):
        return False

    # ---[ status of quote ] ---

    def hasStatus(self):
        return itrade_config.isConnected()

    def currentStatus(self, quote):
        st = 'OK'
        cl = '::'
        return st, cl, "-", "-", self.m_clock

    def currentTrades(self, quote):
        # clock,volume,value
        return None

    def currentMeans(self,quote):
        # means: sell,buy,last
        return "-", "-", "-"

    def currentClock(self, quote=None):
        return self.m_clock

# ============================================================================
# Export me
# ============================================================================


gLiveABC = LiveUpdate_ABCBourse()

#registerLiveConnector('EURONEXT','PAR',QList.any,QTag.differed,gLiveABC,bDefault=False)
#registerLiveConnector('ALTERNEXT','PAR',QList.any,QTag.differed,gLiveABC,bDefault=False)
#registerLiveConnector('PARIS MARCHE LIBRE','PAR',QList.any,QTag.differed,gLiveABC,bDefault=False)

# ============================================================================
# Test ME
#
# ============================================================================

def test(ticker):
    if gLiveABC.iscacheddataenoughfreshq():
        data = gLiveABC.getcacheddata(ticker)
        if data:
            debug(data)
        else:
            debug("nodata")

    elif gLiveABC.connect():
        state = gLiveABC.getstate()
        if state:
            debug("state=u".format(state))

            quote = quotes.lookupTicker(ticker=ticker, market='EURONEXT')
            data = gLiveABC.getdata(quote)
            if data is not None:
                if data:
                    info(data)
                else:
                    debug("nodata")
            else:
                print("getdata() failure :-(")
        else:
            print("getstate() failure :-(")

        gLiveABC.disconnect()
    else:
        print("connect() failure :-(")

if __name__ == '__main__':
    setLevel(logging.INFO)

    print(u'live {}'.format(date.today()))
    test('OSI')
    test('EADT')
    gLiveABC.cacheddatanotfresh()
    test('EADT')

# ============================================================================
# That's all folks !
# ============================================================================
