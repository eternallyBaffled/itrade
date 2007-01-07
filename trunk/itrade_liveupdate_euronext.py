#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_liveupdate_euronext.py
#
# Description: Live update quotes from euronext.com : EURONEXT, ALTERNEXT,
# MARCHE LIBRE (PARIS & BRUXELLES)
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
# 2005-06-10    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import re
import string
import urllib
import thread
from datetime import *

# iTrade system
from itrade_logging import *
from itrade_quotes import *
from itrade_datation import Datation,jjmmaa2yyyymmdd
from itrade_import import *
from itrade_market import euronext_place2mep,euronext_InstrumentId

# ============================================================================
# LiveUpdate_Euronext()
#
#  Euronext returns all the quotes then we have to extract only the quote
#  we want to return :-(
#  design idea : if the quote is requested within the same second, use a
#  cached data to extract !
# ============================================================================

class LiveUpdate_Euronext(object):
    def __init__(self,market='EURONEXT'):
        debug('LiveUpdate_Euronext:__init__')
        self.m_connected = False
        self.m_data = None
        self.m_clock = {}
        self.m_dcmpd = {}
        self.m_lastclock = "::"
        self.m_livelock = thread.allocate_lock()
        self.m_market = market
        self.m_url = 'http://www.euronext.com/tools/datacentre/dataCentreDownloadExcell/0,5822,1732_2276422,00.html'

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

    def euronextDate(self,date):
        sp = string.split(date,' ')
        #print 'euronextDate:',sp

        # Date part is easy
        sdate = jjmmaa2yyyymmdd(sp[0])

        if len(sp)==1:
            return sdate,"00:00"
        return sdate,sp[1]

    def convertClock(self,clock):
        min = clock[-2:]
        hour = clock[:-3]
        val = (int(hour)*60) + int(min)
        #print 'clock:',clock,hour,min,val
        if val>self.m_lastclock:
            self.m_lastclock = val
        return "%d:%02d" % (val/60,val%60)

    def parseFValue(self,d):
        val = string.split(d,',')
        ret = ''
        for val in val:
            ret = ret+val
        return string.atof(ret)

    def parseLValue(self,d):
        if d=='-': return 0
        val = string.split(d,',')
        ret = ''
        for val in val:
            ret = ret+val
        return string.atol(ret)

    def getdata(self,quote):
        self.m_connected = False
        debug("LiveUpdate_Euronext:getdata quote:%s market:%s" % (quote,self.m_market))

        IdInstrument = euronext_InstrumentId(quote)
        if IdInstrument == None: return None

        query = (
            ('idInstrument', IdInstrument),
            ('isinCode', quote.isin()),
            ('indexCompo', ''),
            ('opening', 'on'),
            ('high', 'on'),
            ('low', 'on'),
            ('closing', 'on'),
            ('volume', 'on'),
            ('typeDownload', '3'),
            ('format', ''),
        )
        query = map(lambda (var, val): '%s=%s' % (var, str(val)), query)
        query = string.join(query, '&')
        url = self.m_url + '?' + query

        debug("LiveUpdate_Euronext:getdata: url=%s ",url)
        try:
            f = urllib.urlopen(url)
        except:
            debug('LiveUpdate_Euronext:unable to connect :-(')
            return None

        # pull data
        buf = f.read()
        lines = self.splitLines(buf)
        data = ''

        for eachLine in lines:
            sdata = string.split (eachLine, '\t')
            #print sdata,len(sdata)
            if len(sdata)==34:
                if (sdata[1]<>"ISIN") and (sdata[10]!='-'):
                    c_datetime = datetime.today()
                    c_date = "%04d%02d%02d" % (c_datetime.year,c_datetime.month,c_datetime.day)
                    #print 'Today is :', c_date

                    sdate,sclock = self.euronextDate(sdata[10])

                    # be sure not an oldest day !
                    if (quote.list() == QLIST_INDICES or sdata[8]<>'-'):

                        if (c_date==sdate):
                            key = quote.key()
                            self.m_dcmpd[key] = sdate
                            self.m_clock[key] = self.convertClock(sclock)

                            # __x
                            self.m_lastclock = sclock

                        #
                        open = self.parseFValue(sdata[15])
                        high = self.parseFValue(sdata[16])
                        low = self.parseFValue(sdata[18])
                        value = self.parseFValue(sdata[7])
                        volume = self.parseLValue(sdata[8])

                        # ISIN;DATE;OPEN;HIGH;LOW;CLOSE;VOLUME
                        data = (
                          quote.key(),
                          sdate,
                          open,
                          high,
                          low,
                          value,
                          volume
                        )
                        data = map(lambda (val): '%s' % str(val), data)
                        data = string.join(data, ';')

                        return data
                else:
                    #print sdata
                    pass

        return None

    # ---[ cache management on data ] ---

    def getcacheddata(self,quote):
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

    def currentStatus(self,quote):
        #
        key = quote.key()
        if not self.m_dcmpd.has_key(key):
            # no data for this quote !
            return "UNKNOWN","::","0.00","0.00","::"

        st = 'OK'
        cl = '::'
        return st,cl,"-","-",self.m_clock[key]

    def currentTrades(self,quote):
        # clock,volume,value
        return None

    def currentMeans(self,quote):
        # means: sell,buy,last
        return "-","-","-"

    def currentClock(self,quote=None):
        if quote==None:
            return self.m_lastclock

        key = quote.key()
        if not self.m_clock.has_key(key):
            # no data for this quote !
            return "::"
        else:
            return self.m_clock[key]

# ============================================================================
# Export me
# ============================================================================

try:
    ignore(gLiveEuronext)
    ignore(gLiveAlternext)
except NameError:
    gLiveEuronext = LiveUpdate_Euronext('euronext')
    gLiveAlternext = LiveUpdate_Euronext('alternext')

registerLiveConnector('EURONEXT','PAR',QLIST_ANY,QTAG_DIFFERED,gLiveEuronext,bDefault=False)
registerLiveConnector('EURONEXT','BRU',QLIST_ANY,QTAG_DIFFERED,gLiveEuronext,bDefault=True)
registerLiveConnector('EURONEXT','AMS',QLIST_ANY,QTAG_DIFFERED,gLiveEuronext,bDefault=True)
registerLiveConnector('EURONEXT','LIS',QLIST_ANY,QTAG_DIFFERED,gLiveEuronext,bDefault=True)

registerLiveConnector('ALTERNEXT','PAR',QLIST_ANY,QTAG_DIFFERED,gLiveAlternext,bDefault=False)
registerLiveConnector('ALTERNEXT','BRU',QLIST_ANY,QTAG_DIFFERED,gLiveAlternext,bDefault=True)
registerLiveConnector('ALTERNEXT','AMS',QLIST_ANY,QTAG_DIFFERED,gLiveAlternext,bDefault=True)

registerLiveConnector('PARIS MARCHE LIBRE','PAR',QLIST_ANY,QTAG_DIFFERED,gLiveEuronext,bDefault=False)
registerLiveConnector('BRUXELLES MARCHE LIBRE','BRU',QLIST_ANY,QTAG_DIFFERED,gLiveEuronext,bDefault=True)

# ============================================================================
# Test ME
#
# ============================================================================

def test(ticker):
    if gLiveEuronext.iscacheddataenoughfreshq():
        data = gLiveEuronext.getcacheddata(ticker)
        if data:
            debug(data)
        else:
            debug("nodata")

    elif gLiveEuronext.connect():

        state = gLiveEuronext.getstate()
        if state:
            debug("state=%s" % (state))

            quote = quotes.lookupTicker(ticker,'EURONEXT')
            data = gLiveEuronext.getdata(quote)
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
    test('GTO')
    gLiveEuronext.cacheddatanotfresh()
    test('GTO')

# ============================================================================
# That's all folks !
# ============================================================================
