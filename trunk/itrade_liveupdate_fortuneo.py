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
# decomp
# ============================================================================

def decomp(str):
    base         = 92
    baseT        = " !#$%&()*+,./0123456789:;<=?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~‘’¡¢£¤¥¦§¨©ª«¬­®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþ€"
    struct_trame = ";S;S;.;.;.;.;;;;.;.;;;;;.;.;;;;;.;.;;;;;.;.;;;;;.;.;;;.;.;;.;S;S;S;.;.;::;;.;::;;.;::;;.;::;;.;::;;.;"
    chaineDecompresse = ""

    C = {}

    for i in range(0,len(baseT)):
        C[ baseT[i]] = i

    i = 0
    l = 0

    #print 'len(str)=',len(str),'len(struct_trame)=',len(struct_trame)
    while len(str)>0 and l<len(struct_trame):
        i = 0
        #print 'str=',str,'l=',l,'i=',i,'decomp=',chaineDecompresse
        if struct_trame[l]== "S":
            while str[i]!= ";":
                chaineDecompresse = chaineDecompresse + str[i]
                i = i + 1

            i = i + 1

            l = l + 1

            chaineDecompresse = chaineDecompresse + ";"
        else:
            multiplicateur = 1
            res = 0
            end = False

            i = 0
            while (i<len(str)) and (not end):
                CH = str[i]
                if CH == '-':
                    chaineDecompresse = chaineDecompresse + '-'
                else:
                    if C[ CH ] < base:
                        res = res + (multiplicateur * C[ CH ])
                    else:
                        res = res + (multiplicateur * ( C[ CH ] - base ))
                        end = True
                    multiplicateur =  multiplicateur * base

                i = i + 1

            res = res - 10
            if (res < 10) and ( (struct_trame[l - 1]== ".") or (struct_trame[l - 1] == ":") ):
                res = "0" + ("%d"%res)
                chaineDecompresse = chaineDecompresse + res
            else:
                chaineDecompresse = chaineDecompresse + ("%d"%res)

            if struct_trame[l]== ".":
                chaineDecompresse = chaineDecompresse + "."
            else:
                if struct_trame[l]== ":":
                    chaineDecompresse = chaineDecompresse + ":"
                else:
                    chaineDecompresse = chaineDecompresse + ";"
        l = l + 1
        str = str[i:]
    return chaineDecompresse

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
        # __y params = urllib.urlencode({'subscriptions': '{FRANCE.PL025.BMG988431240.CSA_CRS_DERNIER,FRANCE.PL025.BMG988431240.CSA_VAR_VEILLE}','userinfo': self.m_blowfish,},True)
		# __y
        # __y self.m_url = 'http://' + self.m_default_host + '/streaming'
        # __y self.m_flux = urllib.urlopen(self.m_url, params)
        # __y if self.m_flux == None:
        # __y     print 'live: not connected on %s' % self.m_url
        # __y     return False
		# __y

        self.m_flux = httplib.HTTPConnection(self.m_default_host,80)
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
# __x         if quote:
            quote = None
            return self.getdata(quote)
# __x         return None

    def getdataByISIN(self,isin):
        quote = quotes.lookupISIN(isin)
        if quote:
            return self.getdata(quote)
        return None

    # ---[ code to check the clock ] ---
    def checkClock(self,clock,cac):
        if string.find(cac,"/")>=0 or string.find(cac,"::")>=0:
            print '>> cac >>> ',cac, '::: LIVE IS DEAD TODAY !'
            return False
        # __ local time :-(
        #hh = int(clock[:2])
        #mm = int(clock[3:5])
        #ss = int(clock[6:])
        #now = datetime.today()
        #fortuneo = datetime(now.year,now.month,now.day,hh,mm,ss)
        #delta = fortuneo - now
        #delta = ((delta.days*24*60) + (delta.seconds/60)) / 60
        #if (delta < -1) or (delta > 1):
        #    print fortuneo,' vs ',now, (' = %d hours ::: FORTUNEO IS DEAD TODAY !' % delta)
        #    return False
        return True

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

        params = "subscriptions={FRANCE.PL025.BMG988431240.CSA_CRS_DERNIER,FRANCE.PL025.BMG988431240.CSA_VAR_VEILLE}&userinfo=%s\r\n" % self.m_blowfish

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
        return None

        #info('getdata():\n%s\n--->' % data)

        try:
            data = data[string.find(data,"(")+1:string.rfind(data,")")]
            data = data.strip()
            url,compd,cac,clock = data.split('",')
        except:
            info('LiveUpdate_fortuneo: data is bad:%s' % data)
            return None

        # remove "
        url = url.strip()[1:]
        compd = compd.strip()[1:]
        cac = cac.strip()[1:]
        clock = clock.strip()[1:-1]

        #debug('getdata():\nurl=%s\ncompd=%s\ncac=%s\nclock=%s\n' % (url,compd,cac,clock))

        # decompress the data
        decompd = decomp(compd).split(';')
        debug('getdata():decomp=\n%s\n' % decompd)

        # extract values
        open = decompd[4]
        high = decompd[5]
        low = decompd[6]
        value = decompd[49]
        volume = decompd[7]

        #print '>>>',value,decompd[48],decompd[47]

        # store for later use
        isin = quote.isin()
        self.m_dcmpd[isin] = decompd
        self.m_clock[isin] = clock
        self.m_lastclock = clock

        # be sure fortuneo is working
        if not self.checkClock(clock,cac):
            return None

        self.m_connected = True

        # be sure market is open ...
        if value=='0.00' and decompd[48]=='0' and decompd[47]=='0:00:00':
            #print '>>>',value,decompd[48],decompd[47]
            #info('Quote closed')
            return None

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

    test('EADT')

# ============================================================================
# That's all folks !
# ============================================================================
