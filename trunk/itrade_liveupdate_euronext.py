#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_liveupdate_euronext.py
#
# Description: Live update quotes from euronext.com : EURONEXT and ALTERNEXT
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
# 2005-06-10    dgil  Wrote it from scratch

NOT WORKING YET :-(

# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import re
import thread
import time
import urllib

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_quotes import *
from itrade_import import registerLiveConnector

# ============================================================================
# LiveUpdate_Euronext()
#
#  Euronext returns all the quotes then we have to extract only the quote
#  we want to return :-(
#  design idea : if the quote is requested within the same second, use a
#  cached data to extract !
# ============================================================================

class LiveUpdate_Euronext(object):
    def __init__(self,market='euronext'):
        debug('LiveUpdate_Euronext:__init__')
        self.m_connected = False
        self.m_data = None
        self.m_clock = {}
        self.m_dcmpd = {}
        self.m_lastclock = "::"
        self.m_livelock = thread.allocate_lock()
        self.m_market = market
        if self.m_market=='euronext':
            self.m_url = "http://www.euronext.com/tradercenter/priceslists/trapridownload/0,4499,1732_338638,00.html?belongsToList=market_14&resultsTitle=All%20Euronext%20-%20Eurolist%20by%20Euronext&eligibilityList=&economicGroupList=&sectorList=&branchList="
        elif self.m_market=='alternext':
            self.m_url = "http://www.euronext.com/tradercenter/priceslists/trapridownload/0,4499,1732_338638,00.html?belongsToList=market_15&resultsTitle=All%20Euronext%20-%20Eurolist%20by%20Euronext&eligibilityList=&economicGroupList=&sectorList=&branchList="

    # ---[ reentrant ] ---
    def acquire(self):
        # not reentrant because of global states : m_viewstate/m_data
        self.m_livelock.acquire()

    def release(self):
        self.m_livelock.release()

    # ---[ properties ] ---

    def name(self):
        return self.m_market

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


    def getdata(self,quote):
        self.m_connected = False
        debug("LiveUpdate_Euronext:getdata quote:%s market:%s" % (quote,self.m_market))

        try:
            f = urllib.urlopen(self.m_url)
        except:
            debug('LiveUpdate_Euronext:unable to connect :-(')
            return None

        # returns the data
        data = f.read()
        self.m_datatime = datetime.today()

        # __x
        self.m_lastclock = "%d:%02d" % (self.m_datatime.hour,self.m_datatime.minute)

        debug('!!! datatime = %s clock=%s' % (self.m_datatime,self.m_lastclock))

        lines = self.splitLines(data)

        for line in lines:
            data = string.split (line, ';')
            if len(data)==11:
                # ISIN;DATE;OPEN;HIGH;LOW;CLOSE;VOLUME
                self.m_dcmpd[data[1]] = data[1],data[9],
                self.m_clock[data[1]] = data[9]

        # extract the quote we are looking for
        return self.getcacheddata(quote)

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
        isin = quote.isin()
        if not self.m_dcmpd.has_key(isin):
            return None

        # ISIN;DATE;OPEN;HIGH;LOW;CLOSE;VOLUME
        data = (
          isin,
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

    def iscacheddataenoughfreshq(self):
        if self.m_data==None:
            #print
            debug('iscacheddataenoughfreshq : no cache !')
            return False
        if not self.m_datatime:
            debug('iscacheddataenoughfreshq : no data time !')
            return False
        delta = timedelta(0,itrade_config.cachedDataFreshDelay)
        newtime = self.m_datatime + delta
        if (datetime.today()>newtime):
            debug('datatime = %s  currentdatatime = %s  newtime = %s delta = %s : False' %(self.m_datatime,datetime.today(),newtime,delta))
            return False
        debug('datatime = %s  currentdatatime = %s  newtime = %s delta = %s : True' %(self.m_datatime,datetime.today(),newtime,delta))
        return True

    def cacheddatanotfresh(self):
        self.m_data = None

    # ---[ notebook of order ] ---

    def hasNotebook(self):
        return False

    # ---[ status of quote ] ---

    def hasStatus(self):
        return itrade_config.isConnected()

    def currentStatus(self,quote):
        #
        isin = quote.isin()
        if not self.m_dcmpd.has_key(isin):
            # no data for this quote !
            return "UNKNOWN","::","0.00","0.00","::"

        st = 'OK'
        cl = '::'
        return st,cl,"-","-",self.m_clock[isin]

    def currentTrades(self,quote):
        # clock,volume,value
        return None

    def currentMeans(self,quote):
        # means: sell,buy,last
        return "-","-","-"

    def currentClock(self,quote=None):
        if quote==None:
            return self.m_lastclock

        isin = quote.isin()
        if not self.m_clock.has_key(isin):
            # no data for this quote !
            return "::"
        else:
            return self.m_clock[isin]

# ============================================================================
# Export me
# ============================================================================

try:
    ignore(gLiveEuronext)
    ignore(gLiveAlternext)
except NameError:
    gLiveEuronext = LiveUpdate_Euronext('euronext')
    gLiveAlternext = LiveUpdate_Euronext('alternext')

registerLiveConnector('EURONEXT',gLiveEuronext)
registerLiveConnector('EURONEXT_differed',gLiveEuronext)

registerLiveConnector('ALTERNEXT',gLiveAlternext)
registerLiveConnector('ALTERNEXT_differed',gLiveAlternext)

# ============================================================================
# Test ME
#
# ============================================================================

def test(ticker):
    if gLiveEuronext.iscacheddataenoughfreshq():
        data = gLiveEuronext.getcacheddataByTicker(ticker)
        if data:
            debug(data)
        else:
            debug("nodata")

    elif gLiveEuronext.connect():

        state = gLiveEuronext.getstate()
        if state:
            debug("state=%s" % (state))

            data = gLiveEuronext.getdataByTicker(ticker)
            if data!=None:
                if data:
                    info(data)
                else:
                    debug("nodata")
            else:
                print "getdata() failure :-("
        else:
            print "getstate() failure :-("

        gLiveEuronext.disconnect()
    else:
        print "connect() failure :-("

if __name__=='__main__':
    setLevel(logging.INFO)

    print 'live %s' % date.today()
    test('OSI')
    test('EADT')
    gLiveEuronext.cacheddatanotfresh()
    test('EADT')

# ============================================================================
# That's all folks !
# ============================================================================
