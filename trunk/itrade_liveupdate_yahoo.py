#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_liveupdate_yahoo.py
# Version      : $Id: itrade_liveupdate_yahoo.py,v 1.12 2006/04/20 05:40:36 dgil Exp $
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
# Version management
# ============================================================================

__revision__ = "$Id: itrade_liveupdate_yahoo.py,v 1.12 2006/04/20 05:40:36 dgil Exp $"
__author__ = "Gilles Dumortier (dgil@ieee.org)"
__version__ = "0.4"
__status__ = "alpha"
__cvsversion__ = "$Revision: 1.12 $"[11:-2]
__date__ = "$Date: 2006/04/20 05:40:36 $"[7:-2]
__copyright__ = "Copyright (c) 2004-2006 Gilles Dumortier"
__license__ = "GPL"
__credits__ = """Jonathan Corbet, corbet@eklektix.com for code snippet"""

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

# ============================================================================
# LiveUpdate_yahoo()
#
# ============================================================================

class LiveUpdate_yahoo(object):
    def __init__(self):
        debug('LiveUpdate_yahoo:__init__')
        self.m_url = "http://finance.yahoo.com/d/quotes.csv"
        self.m_connected = False
        self.m_livelock = thread.allocate_lock()
        self.m_clock = "::"

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

    # ---[ API to get data ] ---

    def getdataByQuote(self,quote):
        if quote:
            return self.getdata(quote)
        return None

    def getdataByTicker(self,ticker):
        quote = quotes.lookupTicker(ticker)
        if quote:
            return self.getdata(quote)
        return None

    def getdataByISIN(self,isin):
        quote = quotes.lookupISIN(isin)
        if quote:
            return self.getdata(quote)
        return None

    # ---[ code to get data ] ---

    def yahooDate (self,date):
        # Date part is easy.
        sdate = string.split (date[1:-1], '/')
        month = string.atoi (sdate[0])
        day = string.atoi (sdate[1])
        year = string.atoi (sdate[2])

        return "%4d%02d%02d" % (year,month,day)

    def getdata(self,quote):
        debug("LiveUpdate_yahoo:getdata quote:%s " % quote)
        self.m_connected = False

        query = (
          ('f', 'sl1d1t1c1ohgv'),
          ('s', quote.ticker()),
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

        # connexion / clock
        self.m_connected = True
        self.m_clock = sdata[2][1:-1] + " - " + sdata[3][1:-1]

        # start decoding
        symbol = sdata[0][1:-1]
        if symbol<>quote.ticker():
            info('invalid ticker : ask for %s and receive %s' % (symbol,quote.ticker()))
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
          quote.isin(),
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

    def getcacheddataByQuote(self,quote):
        if quote:
            return self.getcacheddata(quote)
        return None

    def getcacheddataByTicker(self,ticker):
        quote = quotes.lookupTicker(ticker)
        if quote:
            return self.getcacheddata(quote)
        return None

    def getcacheddataByISIN(self,isin):
        quote = quotes.lookupISIN(isin)
        if quote:
            return self.getcacheddata(quote)
        return None

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
        return False

    # ---[ status of quote ] ---

    def hasStatus(self):
        return False

    def currentClock(self,quote=None):
        return self.m_clock

# ============================================================================
# Export me
# ============================================================================

try:
    ignore(gLiveYahoo)
except NameError:
    gLiveYahoo = LiveUpdate_yahoo()

registerLiveConnector('NASDAQ',gLiveYahoo)
registerLiveConnector('NYSE',gLiveYahoo)

# ============================================================================
# Test ME
#
# ============================================================================

def test(ticker):
    if gLiveYahoo.iscacheddataenoughfreshq():
        data = gLiveYahoo.getcacheddataByTicker(ticker)
        if data:
            debug(data)
        else:
            debug("nodata")

    elif gLiveYahoo.connect():

        state = gLiveYahoo.getstate()
        if state:
            debug("state=%s" % (state))

            data = gLiveYahoo.getdataByTicker(ticker)
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
# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
