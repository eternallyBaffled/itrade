#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_liveupdate_fortuneo.py
#
# Description: Live update quotes from fortuneo
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
# 2005-12-29    dgil  Wrote it from scratch
# 2006-05-0x    dgil  live.txt
# 2006-05-28    dgil  deprecated - live broken / access has been securized
#                     keep it for historical reason
#
# 2006-08-17    dgil  working on the new mechanism ...
# 2006-08-19    dgil  authentication is working !!!!!!
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import re
import string
import thread
import datetime
import os
import httplib

# iTrade system
# __x import itrade_config
# __x from itrade_logging import *
# __x from itrade_quotes import *
# __x from itrade_import import registerLiveConnector

# ============================================================================
# __x to be removed after iTrade final integration
# ============================================================================

def debug(a):
    print a

def info(a):
    print a

def setLevel(a):
    pass

# ============================================================================
# Flux to Place
# ============================================================================

flux_place = {
    "025" : "FRANCE.PL",
    "027" : "FRANCE.PL",
    "028" : "FRANCE.PL",
    "029" : "FRANCE.PL",
    "030" : "FRANCE.PL",
    "031" : "FRANCE.PL",
    "032" : "FRANCE.PL",
    "033" : "FRANCE.PL",
    "260" : "FRANCE.PL",
    "485" : "FRANCE.PL",

    "004" : "EUROPE1.PL",
    "011" : "EUROPE1.PL",
    "013" : "EUROPE1.PL",
    "014" : "EUROPE1.PL",
    "015" : "EUROPE1.PL",
    "016" : "EUROPE1.PL",
    "017" : "EUROPE1.PL",
    "018" : "EUROPE1.PL",
    "019" : "EUROPE1.PL",
    "022" : "EUROPE1.PL",
    "038" : "EUROPE1.PL",
    "046" : "EUROPE1.PL",
    "220" : "EUROPE1.PL",

    "036" : "EUROPE2.PL",
    "232" : "EUROPE2.PL",
    "361" : "EUROPE2.PL",
    "613" : "EUROPE2.PL",
    "615" : "EUROPE2.PL",

    "055" : "ESPAGNE.PL",
    "056" : "ESPAGNE.PL",
    "057" : "ESPAGNE.PL",
    "058" : "ESPAGNE.PL",
    "355" : "ESPAGNE.PL",

    "067" : "AMERIQUE1.PL",
    "130" : "AMERIQUE1.PL",

    "065" : "AMERIQUE2.PL",
    "066" : "AMERIQUE2.PL",
    "145" : "AMERIQUE2.PL",

    "012" : "RESTEDUMONDE.PL",
    "040" : "RESTEDUMONDE.PL",
    "048" : "RESTEDUMONDE.PL",
    "050" : "RESTEDUMONDE.PL",
    "051" : "RESTEDUMONDE.PL",
    "053" : "RESTEDUMONDE.PL",
    "061" : "RESTEDUMONDE.PL",
    "072" : "RESTEDUMONDE.PL",
    "083" : "RESTEDUMONDE.PL",
    "103" : "RESTEDUMONDE.PL",
    "104" : "RESTEDUMONDE.PL",
    "106" : "RESTEDUMONDE.PL",
    "111" : "RESTEDUMONDE.PL",
    "120" : "RESTEDUMONDE.PL",
    "152" : "RESTEDUMONDE.PL",
    "241" : "RESTEDUMONDE.PL",
    "244" : "RESTEDUMONDE.PL",
    "249" : "RESTEDUMONDE.PL",
    "267" : "RESTEDUMONDE.PL",
    "373" : "RESTEDUMONDE.PL",
    "428" : "RESTEDUMONDE.PL",
    "498" : "RESTEDUMONDE.PL"
}

def flux2place(flux):
    if flux_place.has_key(flux):
        return flux_place[flux]
    else:
        # default
        return 'FRANCE.PL'

# ============================================================================
# subscriptions
#
# FR0003500008 : CAC40 indice
# ============================================================================

full_subscriptions = (
    "CSA_CRS_DERNIER",
    "CSA_VAR_VEILLE",
    "CSA_CRS_PREMIER",
    "CSA_CRS_HAUT",
    "CSA_CRS_BAS",
    "CSA_VOL_JOUR",
    "CSA_NBL_DEM1",
    "CSA_VOL_DEM1",
    "CSA_CRS_DEM1",
    "CSA_CRS_OFF1",
    "CSA_VOL_OFF1",
    "CSA_NBL_OFF1",
    "CSA_NBL_DEM2",
    "CSA_VOL_DEM2",
    "CSA_CRS_DEM2",
    "CSA_CRS_OFF2",
    "CSA_VOL_OFF2",
    "CSA_NBL_OFF2",
    "CSA_NBL_DEM3",
    "CSA_VOL_DEM3",
    "CSA_CRS_DEM3",
    "CSA_CRS_OFF3",
    "CSA_VOL_OFF3",
    "CSA_NBL_OFF3",
    "CSA_NBL_DEM4",
    "CSA_VOL_DEM4",
    "CSA_CRS_DEM4",
    "CSA_CRS_OFF4",
    "CSA_VOL_OFF4",
    "CSA_NBL_OFF4",
    "CSA_NBL_DEM5",
    "CSA_VOL_DEM5",
    "CSA_CRS_DEM5",
    "CSA_CRS_OFF5",
    "CSA_VOL_OFF5",
    "CSA_NBL_OFF5",

    "CSA_FMP_DEM",
    "CSA_FMP_OFF",

    "CSA_HD_COURS",
    "CSA_VOL_DERNIER",
    "CSA_H_TRANS_2",
    "CSA_VOL_TRANS_2",
    "CSA_CRS_TRANS_2",
    "CSA_H_TRANS_3",
    "CSA_VOL_TRANS_3",
    "CSA_CRS_TRANS_3",
    "CSA_H_TRANS_4",
    "CSA_VOL_TRANS_4",
    "CSA_CRS_TRANS_4",
    "CSA_H_TRANS_5",
    "CSA_VOL_TRANS_5",
    "CSA_CRS_TRANS_5",

    "CSA_CRS_CMP",
    "CSA_IND_ETAT",
    "CSA_H_REPRIS_COT",
    "CSA_RESERV_HAUT",
    "CSA_RESERV_BAS"
    )

def isin2sub(isin,sub):
    return "FRANCE.PL025.%s.%s" % (isin.strip().upper(),sub.strip().upper())
    #return "FRANCE.PL025.%s.%s" %(isin,sub)

def isin2subscriptions(isin):
    str = ""
    for each in full_subscriptions:
        if str!="":
            str = str+","
        str = str + isin2sub(isin,each)
    return str

# ============================================================================
#
# ============================================================================

def convert(n,v,s):
    n = int(n)
    v = int(v)
    if s=='-2.00':
        s = 'ATP'
    if s=='0.00':
        if v>0:
            s = 'APM'
        else:
            s = '-'
    return n,v,s

# ============================================================================
# LiveUpdate_fortuneo()
#
# ============================================================================

class LiveUpdate_fortuneo(object):
    def __init__(self):
        debug('LiveUpdate_fortuneo:__init__')
        self.m_flux = None
        self.m_default_host = "streaming.fortuneo.fr"
        self.m_url = None
        self.m_connected = False

        self.m_blowfish = '437a80b2720feb61e32252c688831e5e28ca2bb84dfafe06a243b2aadbe610c984d57f79f3d334f30d264263654dbf30'

        # __x
        self.m_livelock = thread.allocate_lock()
        self.m_dcmpd = {}
        self.m_clock = {}
        self.m_lastclock = "::"

    # ---[ reentrant ] ---
    def acquire(self):
        self.m_livelock.acquire()

    def release(self):
        self.m_livelock.release()

    # ---[ properties ] ---

    def name(self):
        return 'fortuneo'

    def delay(self):
        return 0

    # ---[ connexion ] ---

    def connect(self):
        self.m_flux = httplib.HTTPConnection(self.m_default_host,80)
        if self.m_flux == None:
            print 'live: not connected on %s' % self.m_url
            return False

        print 'live: connected on %s' % self.m_flux
        return True

    def disconnect(self):
        if self.m_flux:
            self.m_flux.close()
        self.m_flux = None
        self.m_connected = False

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
# __x         quote = quotes.lookupTicker(ticker)
        quote = ticker
        if quote:
            return self.getdata(quote)
        return None

    def getdataByISIN(self,isin):
        quote = quotes.lookupISIN(isin)
        if quote:
            return self.getdata(quote)
        return None

    # ---[ code to get data ] ---

    def getdata(self,quote):
        self.m_connected = False

        # check we have a connection
        if not self.m_flux:
            raise('LiveUpdate_fortuneo:no connection / missing connect() call !')
            return None

        debug("LiveUpdate_fortuneo:getdata quote:%s " % quote)

        # init params and headers
        headers = {
                    "Content-Type":"application/x-www-form-urlencoded",
                    "Connection":"keep-alive",
                    "Accept":"text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2",
                    "Host":self.m_default_host,
                    "User-Agent":"Mozilla/4.0 (Windows)",
                    "Pragma":"no-cache",
                    "Cache-Control":"no-cache"
                    }

        params = "subscriptions={%s}&userinfo=%s\r\n" % (isin2subscriptions(quote),self.m_blowfish)

        # POST quote request
        try:
            self.m_flux.request("POST", "/streaming", params, headers)
            response = self.m_flux.getresponse()
        except:
            info('LiveUpdate_fortuneo:POST failure')
            return None

        if response.status != 200:
            info('LiveUpdate_fortuneo: status==%d!=200 reason:%s' % (response.status,response.reason))
            return None

        print 'cool: status==%d==200 reason:%s headers:%s msg:%s' % (response.status,response.reason,response.getheaders(),response.msg)

        # returns the data
        data = response.read(5)

        print 'returns:',data

        # __x OK : start decoding the octet-stream

        return None

        # __x ...

        # ISIN;DATE;OPEN;HIGH;LOW;CLOSE;VOLUME
        data = (
          isin,
          date.today(),
          open,
          high,
          low,
          value,
          volume
        )
        data = map(lambda (val): '%s' % str(val), data)
        data = string.join(data, ';')
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
        return True

    def currentNotebook(self,quote):
        #
        isin = quote.isin()
        if not self.m_dcmpd.has_key(isin):
            # no data for this quote !
            return [],[]
        d = self.m_dcmpd[isin]

        #
        buy = []
        if d[8]<>"0":
            buy.append(convert(d[8],d[9],d[10]))
            if d[14]<>"0":
                buy.append(convert(d[14],d[15],d[16]))
                if d[20]<>"0":
                    buy.append(convert(d[20],d[21],d[22]))
                    if d[26]<>"0":
                        buy.append(convert(d[26],d[27],d[28]))
                        if d[32]<>"0":
                            buy.append(convert(d[32],d[33],d[34]))

        sell = []
        if d[13]<>"0":
            sell.append(convert(d[13],d[12],d[11]))
            if d[19]<>"0":
                sell.append(convert(d[19],d[18],d[17]))
                if d[25]<>"0":
                    sell.append(convert(d[25],d[24],d[23]))
                    if d[31]<>"0":
                        sell.append(convert(d[31],d[30],d[29]))
                        if d[37]<>"0":
                            sell.append(convert(d[37],d[36],d[35]))

        return buy,sell

    def currentClock(self,quote=None):
        if quote==None:
            return self.m_lastclock
        #
        isin = quote.isin()
        if not self.m_clock.has_key(isin):
            # no data for this quote !
            return "::"
        else:
            return self.m_clock[isin]

    def currentTrades(self,quote):
        #
        isin = quote.isin()
        if not self.m_dcmpd.has_key(isin):
            # no data for this quote !
            return None
        d = self.m_dcmpd[isin]

        # clock,volume,value
        last = []
        if d[47]<>"0:00:00":
            last.append((d[47],int(d[48]),d[49]))
            if d[50]<>"0:00:00":
                last.append((d[50],int(d[51]),d[52]))
                if d[53]<>"0:00:00":
                    last.append((d[53],int(d[54]),d[55]))
                    if d[56]<>"0:00:00":
                        last.append((d[56],int(d[57]),d[58]))
                        if d[59]<>"0:00:00":
                            last.append((d[59],int(d[60]),d[61]))

        return last

    def currentMeans(self,quote):
        #
        isin = quote.isin()
        if not self.m_dcmpd.has_key(isin):
            # no data for this quote !
            return "-","-","-"
        d = self.m_dcmpd[isin]

        s = d[38]
        if s=='0.00':
            s = '-'

        b = d[39]
        if b=='0.00':
            b = '-'

        tcmp = float(d[7])
        if tcmp<=0.0:
            tcmp = 0.0
        else:
            tcmp = float(d[41])/tcmp

        if tcmp<=0.0:
            tcmp = '-'
        else:
            tcmp = "%.2f" % tcmp

        # means: sell,buy,last
        return s,b,tcmp

    def currentStatus(self,quote):
        #
        isin = quote.isin()
        if not self.m_dcmpd.has_key(isin):
            # no data for this quote !
            return "UNKNOWN","::","0.00","0.00","::"
        d = self.m_dcmpd[isin]

        st = d[43]
        if st==' ' or st=='':
            st = 'OK'
        elif st=='H':
            st = 'SUSPEND+'
        elif st=='B':
            st = 'SUSPEND-'
        elif st=='P':
            st = 'SUSPEND'
        elif st=='S':
            st = 'SUSPEND'

        cl = d[44]
        if cl=='':
            cl = "::"

        return st,cl,d[45],d[46],self.m_clock[isin]

    # ---[ status of quote ] ---

    def hasStatus(self):
        return itrade_config.isConnected()

# ============================================================================
# Export me
# ============================================================================

try:
    ignore(gLiveFortuneo)
except NameError:
    gLiveFortuneo = LiveUpdate_fortuneo()

# __x test the connection, and register only if working ...
# __x registerLiveConnector('EURONEXT',gLiveFortuneo)

# ============================================================================
# Test ME
#
# ============================================================================

def test(ticker):
    if gLiveFortuneo.iscacheddataenoughfreshq():
        data = gLiveFortuneo.getcacheddataByTicker(ticker)
        if data:
            debug(data)
        else:
            debug("nodata")

    elif gLiveFortuneo.connect():

        state = gLiveFortuneo.getstate()
        if state:
            debug("state=%s" % (state))

            data = gLiveFortuneo.getdataByTicker(ticker)
            if data:
                info(data)
            else:
                print "getdata() failure :-("
                debug("nodata")
            # __x quote = quotes.lookupTicker(ticker)
            # __x info(gLiveFortuneo.currentClock(quote))
            # __x info(gLiveFortuneo.currentNotebook(quote))
            # __x info(gLiveFortuneo.currentTrades(quote))
            # __x info(gLiveFortuneo.currentMeans(quote))
            # __x info(gLiveFortuneo.currentStatus(quote))
        else:
            print "getstate() failure :-("

        gLiveFortuneo.disconnect()
    else:
        print "connect() failure :-("

if __name__=='__main__':
    setLevel(logging.INFO)

    test('FR0000073272')

# ============================================================================
# That's all folks !
# ============================================================================
