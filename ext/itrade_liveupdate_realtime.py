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
# New code for realtime is from Michel Legrand.

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
import logging
import re
import thread
import string
import time
import urllib

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_quotes import *
from itrade_defs import *
from itrade_ext import *
from itrade_market import yahooTicker,convertConnectorTimeToPlaceTime
from itrade_connection import ITradeConnection
from datetime import *
# ============================================================================
# LiveUpdate_RealTime()
#
# ============================================================================

class LiveUpdate_RealTime(object):
    def __init__(self,market = 'EURONEXT'):
        debug('LiveUpdate_RealTime:__init__')
        self.m_connected = False
        self.m_livelock = thread.allocate_lock()        
        self.m_conn = None
        self.m_clock = {}
        self.m_dcmpd = {}
        self.m_lastclock = 0
        self.m_lastdate = "20070101"
        self.m_market = market

        self.m_connection = ITradeConnection(cookies = None,
                                           proxy = itrade_config.proxyHostname,
                                           proxyAuth = itrade_config.proxyAuthentication,
                                           connectionTimeout = itrade_config.connectionTimeout
                                           )
        
        

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

    # ---[ connexion ] ---

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
    
    def splitLines(self,data):
        lines = string.split(data, '\n')
        lines = filter(lambda x:x, lines)
        def removeCarriage(s):
            if s[-1]=='\r':
                return s[:-1]
            else:
                return s
        lines = [removeCarriage(l) for l in lines]
        return lines

    def BoursoDate(self,date):
        sp = string.split(date,' ')
        # Date part is easy
        sdate = jjmmaa2yyyymmdd(sp[0])

        if len(sp)==1:
            return sdate,"00:00"
        return sdate,sp[1]
    
    
   
    def convertClock(self,place,clock,date):
        min = clock[3:5]
        hour = clock[:2]
        val = (int(hour)*60) + int(min)

        if val>self.m_lastclock and date>=self.m_lastdate:
            self.m_lastdate = date
            self.m_lastclock = val

        # convert from connector timezone to market place timezone
        mdatetime = datetime(int(date[0:4]),int(date[4:6]),int(date[6:8]),val/60,val%60)
        mdatetime = convertConnectorTimeToPlaceTime(mdatetime,self.timezone(),place)

        return "%d:%02d" % (mdatetime.hour,mdatetime.minute)

    

    def getdata(self,quote):
        debug("LiveUpdate_Bousorama:getdata quote:%s " % quote)
        self.m_connected = False
        ss = quote.ticker()
        ss = ss.lower()
        #if ss =='^FCHI': ss='CAC'
        if ss =='^FCHI': ss='FR0003500008'
        url = 'http://www.boursorama.com/recherche/index.phtml?search%5Bquery%5D='+ss+'&search%5Btype%5D=rapide&search%5Bcategorie%5D=STK&search%5Bbourse%5D=country%3A33'
        #url = 'http://www.boursorama.com/cours.phtml?symbole=1rP%s' %ss
        #url = 'http://www.boursorama.com/cours.phtml?symbole=1rP'+ss+'&search[query]='+ss
        
        try:
            data=self.m_connection.getDataFromUrl(url)
            data = data.replace('\t','')
            lines = self.splitLines(data)

            n = - 1
            for line in lines:
                n=n+1
                if 'Nyse Euronext - Données temps réel' in line:
                    line = lines[n]
                    
                    value = line[line.find('<strong>')+8:line.find('</strong>')].replace(' ','').replace('EUR','').replace('Pts','').replace('(s)','').replace('(c)','').replace('(h)','')
                    #print value  
                    line = lines[n+2]
                    percent = line[line.find('s">')+3:line.find('%</span></strong></li>')].replace(' ','')
                    #print percent
                    line = lines[n+3]
                    date_time = line[line.find('<li>')+4:line.find('</li>')]
                    date_time = date_time[:8]+' '+date_time[-8:]
                    #print date_time
                    line = lines[n+4]
                    volume = line[line.find('<li>')+4:line.find('</li>')].replace(' ','')
                    if 'M' in line : volume  = '0'
                    #print volume
                    line = lines[n+5]
                    open = line[line.find('<li>')+4:line.find('</li>')].replace(' ','')
                    #print open
                    line = lines[n+6]
                    high = line[line.find('<li>')+4:line.find('</li>')].replace(' ','')
                    #print high
                    line = lines[n+7]
                    low = line[line.find('<li>')+4:line.find('</li>')].replace(' ','')
                    #print low
                    line = lines[n+8]
                    previous = line[line.find('<li>')+4:line.find('</li>')].replace(' ','')
                    #print previous
                    c_datetime = datetime.today()
                    c_date = "%04d%02d%02d" % (c_datetime.year,c_datetime.month,c_datetime.day)
                        

                    sdate,sclock = self.BoursoDate(date_time)
                    if (c_date==sdate):
                        key = quote.key()
                        self.m_dcmpd[key] = sdate
                        self.m_clock[key] = self.convertClock(quote.place(),sclock,sdate)
                    data = ';'.join([quote.key(),sdate,open,high,low,value,volume,percent])

                    return data

        except:
            debug('LiveUpdate_Boursorama:unable to connect :-(')
            return None

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
        return False

    def currentNotebook(self,quote):
        key = quote.key()
        if not self.m_dcmpd.has_key(key):
            # no data for this quote !
            return [],[]
        d = self.m_dcmpd[key]

        buy = []
        #buy.append([0,0,'-'])

        sell = []
        #sell.append([0,0,'-'])

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
    ignore(gLiveABC)
except NameError:
    gLiveABC = LiveUpdate_RealTime()
registerLiveConnector('EURONEXT','PAR',QLIST_ANY,QTAG_LIVE,gLiveABC,bDefault=False)
registerLiveConnector('ALTERNEXT','PAR',QLIST_ANY,QTAG_LIVE,gLiveABC,bDefault=False)
registerLiveConnector('PARIS MARCHE LIBRE','PAR',QLIST_ANY,QTAG_LIVE,gLiveABC,bDefault=False)
registerLiveConnector('BRUXELLES MARCHE LIBRE','BRU',QLIST_ANY,QTAG_LIVE,gLiveABC,bDefault=False)

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
            debug("state=%s" % (state))

            quote = quotes.lookupTicker(ticker,'EURONEXT')
            data = gLiveABC.getdata(quote)
            if data!=None:
                if data:
                    info(data)
                else:
                    debug("nodata")
            else:
                print "getdata() failure :-("
        else:
            print "getstate() failure :-("

        gLiveABC.disconnect()
    else:
        print "connect() failure :-("

if __name__=='__main__':
    setLevel(logging.INFO)

    print 'live %s' % date.today()
    test('OSI')
    test('EADT')
    gLiveABC.cacheddatanotfresh()
    test('EADT')

# ============================================================================
# That's all folks !
# ============================================================================
