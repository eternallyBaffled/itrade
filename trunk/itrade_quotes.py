#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes.py
#
# Description: Quotes
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
# 2004-01-08    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from datetime import *
import logging

# iTrade system
from itrade_logging import *
from itrade_local import message,getLang,getNumSep
import itrade_csv
import itrade_trades
from itrade_import import *
from itrade_datation import *
from itrade_market import market2currency,isin2market
import itrade_currency

# ============================================================================
# color
# ============================================================================

QUOTE_RED = 0
QUOTE_GREEN = 1
QUOTE_NOCHANGE = 2
QUOTE_INVALID = 3

# ============================================================================
# type of quote : cash, SRD(credit) or both
# ============================================================================

QUOTE_NOTYPE    = 0
QUOTE_CASH      = 1
QUOTE_CREDIT    = 2
QUOTE_BOTH      = 3

# ============================================================================
# volume formatter
# ============================================================================

def fmtVolume(x):
    sep = getNumSep()
    val = '%d' % x
    ret = ''
    i   = len(val)
    n   = 0
    while i>0:
        n = n + 1
        i = i - 1
        ret = val[i] + ret
        if (n%3 == 0) and (i>0):
            ret = sep+ret
    return ret

# ============================================================================
# Quote
# ============================================================================

class Quote(object):
    def __init__(self,isin,name,ticker,market,currency,place):
        self.m_isin = isin
        self.m_place = place
        self.m_defaultname = name
        self.m_defaultticker = ticker
        self.m_daytrades = None
        self.m_weektrades = None
        self.m_monthtrades = None
        self.m_country = self.m_isin[0:2].lower()

        if not market:
            self.m_defaultmarket = isin2market(isin)
        else:
            self.m_defaultmarket = market
        self.m_defaultliveconnector = getLiveConnector(self.m_defaultmarket)
        self.m_defaultimportconnector = getImportConnector(self.m_defaultmarket)

        if not currency:
            self.m_currency = market2currency(self.m_market)
        else:
            self.m_currency = currency

        self._init_()

    # ---[ initialisation ]--------------------------------

    def _init_(self):
        # can be overloaded later ...
        # NB: PRU currency *is* portfolio currency
        self.m_DIR_number = 0
        self.m_DIR_pru = 0.0
        self.m_SRD_number = 0
        self.m_SRD_pru = 0.0
        self.m_SRD_accnum = 0
        self.m_SRD_prevacc = 0

        self.m_isTraded = False
        self.m_wasTraded = False
        self.m_isMonitored = False

        self.m_stoploss = 0.0
        self.m_stopwin = 0.0
        self.m_hasStops = False
        self.m_market = self.m_defaultmarket
        self.m_liveconnector = self.m_defaultliveconnector
        self.m_importconnector = self.m_defaultimportconnector
        self.m_name = self.m_defaultname
        self.m_ticker = self.m_defaultticker
        self.m_symbcurr = itrade_currency.currency2symbol(self.m_currency)

    def reinit(self):
        #info('%s::reinit' %(self.name()))
        self._init_()

    # ---[ properties ] -----------------------------------

    def type(self):
        n = QUOTE_NOTYPE
        if self.m_DIR_number > 0:
            n = n + QUOTE_CASH
        if self.m_SRD_number > 0:
            n = n + QUOTE_BOTH
        return n

    def __str__(self):
        return self.m_isin

    def __repr__(self):
        return '%s;%s;%s;%s;%s;%s' % (self.m_isin, self.m_name, self.m_ticker, self.m_market, self.m_currency, self.m_place)

    def __hash__(self):
        return self.m_isin

    def country(self):
        return self.m_country

    def currency(self):
        return self.m_currency

    def currency_symbol(self):
        return self.m_symbcurr

    def isin(self):
        return self.m_isin

    def place(self):
        return self.m_place

    def name(self):
        return self.m_name

    def default_name(self):
        return self.m_defaultname

    def set_name(self,name):
        self.m_name = name

    def ticker(self):
        return self.m_ticker

    def default_ticker(self):
        return self.m_defaultticker

    def set_ticker(self,ticker):
        self.m_ticker = ticker

    def nv_number(self,box=QUOTE_BOTH):
        if box==QUOTE_CASH:
            return self.m_DIR_number
        if box==QUOTE_CREDIT:
            return self.m_SRD_number
        else:
            return self.m_DIR_number + self.m_SRD_number

    def sv_number(self,box=QUOTE_BOTH):
        return fmtVolume(self.nv_number(box))

    def nv_pru(self,box=QUOTE_BOTH):
        # return PRU in the default currency (i.e. portfolio currency)
        if box==QUOTE_CASH:
            return self.m_DIR_pru
        elif box==QUOTE_CREDIT:
            return self.m_SRD_pru
        else:
            n = self.nv_number(QUOTE_BOTH)
            if n > 0:
                return (self.nv_pr(QUOTE_CASH) + self.nv_pr(QUOTE_CREDIT)) / n
            return 0.0

    def nv_pr(self,box=QUOTE_BOTH):
        # return PR in the default currency (i.e. portfolio currency)
        return self.nv_pru(box) * self.nv_number(box)

    def sv_pru(self,box=QUOTE_BOTH,fmt="%.3f"):
        # return PRU in the default currency (i.e. portfolio currency)
        return fmt % self.nv_pru(box)

    def sv_pr(self,box=QUOTE_BOTH,fmt="%.2f"):
        # return PR in the default currency (i.e. portfolio currency)
        return fmt % self.nv_pr(box)

    def nv_pv(self,currency,box=QUOTE_BOTH):
        # return PV in the requested currency
        # nv_close() returns value in market currency
        cl = self.nv_close()
        if cl:
            if box==QUOTE_CASH:
                retval = cl * self.m_DIR_number
            elif box==QUOTE_CREDIT:
                retval = cl * self.m_SRD_number
            else:
                retval = cl * (self.m_DIR_number + self.m_SRD_number)
        else:
            retval = 0.0
        if currency:
            retval = itrade_currency.convert(currency,self.m_currency,retval)
        return retval

    def sv_pv(self,currency,box=QUOTE_BOTH,fmt="%.2f"):
        # return PV in the requested currency
        return fmt % self.nv_pv(currency,box)

    def nv_profit(self,currency,box=QUOTE_BOTH):
        return self.nv_pv(currency,box)-self.nv_pr(box)

    def sv_profit(self,currency,box=QUOTE_BOTH,fmt="%.2f"):
        return fmt % self.nv_profit(currency,box)

    def nv_profitPercent(self,currency,box=QUOTE_BOTH):
        # profit performance should be calculated after conversion to the portfolio currency !
        pr = self.nv_pr(box)
        if pr>0:
            return self.nv_profit(currency,box)/self.nv_pr(box)*100
        else:
            return 0.0

    def sv_profitPercent(self,currency,box=QUOTE_BOTH):
        # profit performance should be calculated after conversion to the portfolio currency !
        if self.nv_pr(box)>0:
            return "%3.2f %%" % self.nv_profitPercent(currency,box)
        else:
            return "---.-- %"

    def isTraded(self):
        return self.m_isTraded

    def wasTraded(self):
        return self.m_wasTraded

    def isMonitored(self):
        return self.m_isMonitored

    def isMatrix(self):
        return self.m_isMonitored or self.m_isTraded
        #was: return self.m_isMonitored or self.m_isTraded or self.m_wasTraded

    def descr(self):
        return '%s (%s-%s)' % (self.m_name, self.m_isin, self.m_ticker)

    def trades(self):
        return self.m_daytrades

    # ---[ market & connectors ] -------------------------------------

    def market(self):
        return self.m_market

    def default_market(self):
        return self.m_defaultmarket

    def delay(self):
        return self.m_liveconnector.delay()

    def liveconnector(self):
        return self.m_liveconnector

    def importconnector(self):
        return self.m_importconnector

    def default_liveconnector(self):
        return self.m_defaultliveconnector

    def default_importconnector(self):
        return self.m_defaultimportconnector

    def set_market(self,market):
        # set market to use
        self.m_market = market
        # then get the connector for this market
        self.m_liveconnector = getLiveConnector(self.m_market)
        self.m_importconnector = getImportConnector(self.m_market)
        # then update currency on this market
        self.m_currency = market2currency(self.m_market)

    def set_liveconnector(self,name):
        conn = findLiveConnector(name)
        if conn:
            self.m_liveconnector = conn

    def set_importconnector(self,name):
        conn = findImportConnector(name)
        if conn:
            self.m_importconnector = conn

    # ---[ notebook of order ] ----------------------------

    def hasNotebook(self):
        return self.m_liveconnector.hasNotebook()

    def currentNotebook(self):
        if self.hasNotebook():
            return self.m_liveconnector.currentNotebook(self)
        else:
            return None

    # ---[ status ] ---------------------------------------

    def hasStatus(self):
        return self.m_liveconnector.hasStatus()

    def currentStatus(self):
        # current status (status,reopen,RB,RH,clock) could be :
        #   status = OK, CLOSED, SUSPEND, SUSPEND+, SUSPEND-, UNKNOWN
        #   clock = time string of status in local market time
        if self.hasStatus():
            # get the real status
            cs,r,rb,rh,cl = self.m_liveconnector.currentStatus(self)
            if cs=="OK" and not self.hasOpened():
                cs = "CLOSED"
            if cs=="UNKNOWN" and not self.isOpen():
                cs = "CLOSED"
            #print '>>> get real status : ',cs
            return (cs,r,rb,rh,cl)
        else:
            # generate a status
            if self.hasOpened():
                cs = "OK"
            else:
                cs = "CLOSED"
            #print '>>> generate a status : ', cs
            return (cs,"::","-","-","::")

    def sv_status(self):
        cs,r,rb,rh,cl = self.currentStatus()
        return cs

    def sv_clock(self):
        cs,r,rb,rh,cl = self.currentStatus()
        if cs=='CLOSED' or cl=="::":
            return ""
        return cl

    def sv_type_of_clock(self,bDisplayTime=False):
        if self.delay()==0:
            if bDisplayTime:
                return message('prop_islive')
            else:
                return message('prop_isslive')
        else:
            if bDisplayTime:
                return message('prop_isnotlive')%self.delay()
            else:
                return message('prop_isdiffered')

    def sv_reopen(self):
        cs,r,rb,rh,cl = self.currentStatus()
        if r=="::":
            return "-"
        return r

    def low_threshold(self):
        cs,r,rb,rh,cl = self.currentStatus()
        if rb<>"-":
            return float(rb)
        else:
            prev = self.nv_prevclose()
            if prev:
                # __x parameters given the market rules ...
                return prev - (0.1*prev)
            else:
                return 0.0

    def high_threshold(self):
        cs,r,rb,rh,cl = self.currentStatus()
        if rh<>"-":
            return float(rh)
        else:
            prev = self.nv_prevclose()
            if prev:
                # __x parameters given the market rules ...
                return prev + (0.1*prev)
            else:
                return 0.0

    def currentMeans(self):
        # means: sell,buy,last
        if self.hasStatus():
            return self.m_liveconnector.currentMeans(self)
        else:
            return "-","-","-"

    def sv_waq(self):
        # weighted average quotation
        s,b,l = self.currentMeans()
        return l

    # ---[ stops ] ----------------------------------------

    def setStops(self,loss,win):
        self.m_stoploss = float(loss)
        self.m_stopwin = float(win)
        info('%s::setStops %f %f' %(self.name(),self.m_stoploss,self.m_stopwin))
        self.m_hasStops = True

    def nv_stoploss(self):
        return self.m_stoploss

    def sv_stoploss(self):
        return "%.2f" % self.nv_stoploss()

    def nv_stopwin(self):
        return self.m_stopwin

    def sv_stopwin(self):
        return "%.2f" % self.nv_stopwin()

    def nv_riskmoney(self,currency):
        sl = itrade_currency.convert(currency,self.m_currency,self.nv_stoploss())
        x = (self.nv_pru()-sl)*self.nv_number()
        if x>0:
            return x
        else:
            return 0.0

    def sv_riskmoney(self,currency):
        return "%.2f" % self.nv_riskmoney(currency)

    def hasStops(self):
        return self.m_hasStops

    # ---[ load or import trades / date is unique key ] ---

    def loadTrades(self,fn=None):
        #debug('Quote:loadTrades %s' % self.ticker)
        if self.m_daytrades==None:
            self.m_daytrades = itrade_trades.Trades(self)
        self.m_daytrades.load(fn)

    def importTrades(self,data,bLive):
        #debug('Quote:importTrades %s %s bLive=%s' % (self.ticker,data,bLive))
        if self.m_daytrades==None:
            self.m_daytrades = itrade_trades.Trades(self)
        self.m_daytrades.imp(data,bLive)

    # ---[ save or export trades / date is unique key ] ---

    def saveTrades(self,fn=None):
        if self.m_daytrades==None:
            info('Quote:saveTrades %s - no daytrades !' % self.ticker())
            return
        info('Quote:saveTrades %s - save now !' % self.ticker())
        self.m_daytrades.save(fn)

    # ---[ update the quote from the network ] ---

    def update(self,fromdate=None,todate=None):
        #debug('update %s from:%s to:%s' % (self.ticker(),fromdate,todate))
        if self.m_daytrades==None:
            self.m_daytrades = itrade_trades.Trades(self)
            self.loadTrades()
        if fromdate==date.today() or fromdate==None:
            # import until 'yesterday' (be sure the day is or will open !)
            ajd = date.today()
            # if market is or will open:
            ajd = Datation(ajd).prevopen(self.m_market).date()
            #else:
            #   ajd = Datation(ajd).nearopen(self.m_market).date()

            # full importation ?
            tr = self.m_daytrades.lastimport()
            if tr==None:
                print '%s *** no trade at all ! : need to import ...' % self.ticker()
                if not cmdline_importQuoteFromInternet(self):
                    print 'error importing full data ...'
                    return False
            elif tr.date() != ajd:
                print '%s *** from = %s today = %s : need to import ...' % (self.ticker(),tr.date(),ajd)
                if not import_from_internet(self,tr.date(),ajd):
                    print 'error importing partial data ...'
                    return False
                self.saveTrades()

            # live update today
            if self.isOpen():
                print '%s / %s *** liveupdate today = %s ...' % (self.ticker(),self.market(),date.today())
                return liveupdate_from_internet(self)
            else:
                return True
        else:
            # history importation
            info('history importation for %s'%self.ticker())
            if import_from_internet(self,fromdate,todate):
                #self.saveTrades()
                return True
            else:
                return False

    # ---[ operations on the quote ] ---

    def buy(self,n,m,box):
        #info('buy: %s %d %f' % (self.ticker(),n,m))
        if box==QUOTE_CASH:
            if (self.m_DIR_number + n) > 0:
                self.m_DIR_pru = ((self.m_DIR_pru * self.m_DIR_number) + m) / (self.m_DIR_number + n)
            if self.m_DIR_pru < 0.0:
                self.m_DIR_pru = 0.0
            self.m_DIR_number = self.m_DIR_number + n
        elif box==QUOTE_CREDIT:
            if (self.m_SRD_number + n) > 0:
                self.m_SRD_pru = ((self.m_SRD_pru * self.m_SRD_number) + m) / (self.m_SRD_number + n)
            if self.m_SRD_pru < 0.0:
                self.m_SRD_pru = 0.0
            self.m_SRD_number = self.m_SRD_number + n
            self.m_SRD_accnum = max(self.m_SRD_accnum,self.m_SRD_number)
            #print 'set accnum = ',self.m_SRD_accnum
        self.m_isTraded = (self.m_DIR_number>0) or (self.m_SRD_number>0)

    def sell(self,n,box):
        #info('sell: %s %d' % (self.ticker(),n))
        if box==QUOTE_CASH:
            if self.m_DIR_number < n:
                raise("negative number of shares is not possible ...")
            self.m_DIR_number = self.m_DIR_number - n
            if self.m_DIR_number <=0 :
                self.m_wasTraded = True
        elif box==QUOTE_CREDIT:
            if self.m_SRD_number < n:
                raise("short unsupported yet ...")
            self.m_SRD_number = self.m_SRD_number - n
            if self.m_SRD_number <=0 :
                self.m_wasTraded = True
        self.m_isTraded = (self.m_DIR_number>0) or (self.m_SRD_number>0)

    def transfertTo(self,n,expenses,box):
        #info('transfert: %s %d' % (self.ticker(),n))
        if box==QUOTE_CASH:
            if self.m_SRD_number < n:
                raise("negative number of shares is not possible ...")
            price = (n * self.m_SRD_pru)
            if self.m_SRD_accnum > 0:
                #print 'n=',n,'get accnum = ',self.m_SRD_accnum
                price = price + (expenses*n/self.m_SRD_accnum)
            #print 'n=',n,'price = ',price
            self.sell(n,QUOTE_CREDIT)
            self.buy(n,price,QUOTE_CASH)
            self.m_SRD_prevacc = self.m_SRD_accnum
            self.m_SRD_accnum = self.m_SRD_number
            #print 'n=',n,'reinit accnum = ',self.m_SRD_accnum
        elif box==QUOTE_CREDIT:
            if self.m_DIR_number < n:
                raise("negative number of shares is not possible ...")
            price = (n * self.m_DIR_pru)
            if self.m_SRD_prevacc > 0:
                price = price - (expenses*n/self.m_SRD_prevacc)
            self.sell(n,QUOTE_CASH)
            self.buy(n,price,QUOTE_CREDIT)
            self.m_SRD_accnum = self.m_SRD_prevacc

    # ---[ current / live values on the quote ] ---

    def index(self,d=None):
        if d==None:
            tr = self.m_daytrades.lasttrade()
        else:
            tr = self.m_daytrades.trade(d)
        if tr:
            return tr.index()
        return -1

    def lastindex(self):
        tr = self.m_daytrades.lasttrade()
        if tr:
            return tr.index()
        return -1

    def nv_close(self,d=None):
        if d==None:
            tr = self.m_daytrades.lasttrade()
        else:
            tr = self.m_daytrades.trade(d)
        if tr:
            return tr.nv_close()
        return None

    def nv_open(self,d=None):
        if d==None:
            tr = self.m_daytrades.lasttrade()
        else:
            tr = self.m_daytrades.trade(d)
        if tr:
            return tr.nv_open()
        return None

    def nv_low(self,d=None):
        if d==None:
            tr = self.m_daytrades.lasttrade()
        else:
            tr = self.m_daytrades.trade(d)
        if tr:
            return tr.nv_low()
        return None

    def nv_high(self,d=None):
        if d==None:
            tr = self.m_daytrades.lasttrade()
        else:
            tr = self.m_daytrades.trade(d)
        if tr:
            return tr.nv_high()
        return None

    def nv_volume(self,d=None):
        if d==None:
            tr = self.m_daytrades.lasttrade()
        else:
            tr = self.m_daytrades.trade(d)
        if tr:
            return tr.nv_volume()
        return None

    def nv_prevclose(self,d=None):
        tc = self.m_daytrades.prevtrade(d)
        if tc:
            return tc.nv_close()
        return None

    def nv_unitvar(self,d=None):
        tc = self.nv_close(d)
        tp = self.nv_prevclose(d)
        if tc and tp:
            return tc - tp
        return None

    def nv_percent(self,d=None):
        tc = self.nv_close(d)
        tp = self.nv_prevclose(d)
        if tc and tp:
            return ((tc/tp)*100)-100
        return None

    # ---[ same current / live data on quote but string ] ------------------

    def sv_close(self,d=None,bDispCurrency=False):
        if bDispCurrency:
            sc = ' '+self.m_symbcurr+' '
        else:
            sc = ''
        x = self.nv_close(d)
        if x!=None:
            st,re,rb,rh,cl = self.currentStatus()
            if st=='OK':
                return "%3.2f%s" % (x,sc)
            elif st=='SUSPEND+':
                return "%3.2f%s(+)" % (x,sc)
            elif st=='SUSPEND-':
                return "%3.2f%s(-)" % (x,sc)
            elif st=='SUSPEND':
                return "%3.2f%s(s)" % (x,sc)
            elif st=='CLOSED':
                return "%3.2f%s(c)" % (x,sc)
            else:
                return "%3.2f%s(%s)" % (x,sc,st)
        return " ---.--%s" % sc

    def sv_open(self,d=None):
        x = self.nv_open(d)
        if x!=None:
            return "%3.2f" % x
        return " ---.-- "

    def sv_low(self,d=None):
        x = self.nv_low(d)
        if x!=None:
            return "%3.2f" % x
        return " ---.-- "

    def sv_high(self,d=None):
        x = self.nv_high(d)
        if x!=None:
            return "%3.2f" % x
        return " ---.-- "

    def sv_volume(self,d=None):
        x = self.nv_volume(d)
        if x!=None:
            return fmtVolume(x)
        return " ---------- "

    def sv_prevclose(self,d=None):
        x = self.nv_prevclose(d)
        if x!=None:
            return "%3.2f" % x
        return " ---.-- "

    def sv_percent(self,d=None):
        try:
            x = self.nv_percent(d)
        except:
            return " ---.-- %"

        if x!=None:
            if x>0:
                return "+%3.2f %%" % x
            else:
                return "%3.2f %%" % x
        return " ---.-- %"

    def sv_unitvar(self,d=None):
        x = self.nv_unitvar(d)
        if x!=None:
            return "%3.2f" % x
        return " ---.-- "

    # ---[ object value ] ---

    def ov_candle(self,d=None):
        if d==None:
            tr = self.m_daytrades.lasttrade()
        else:
            tr = self.m_daytrades.trade(d)
        if tr==None:
            return None
        d = Datation(tr.date()).date()
        tc = self.m_daytrades.candle(d)
        return tc

    def ov_pivots(self):
        tc = self.m_daytrades.lasttrade()
        if tc:
            #debug('ov_pivots(): tc=%s tc_date=%s ... need to get prev ...' % (tc,tc.date()))
            tc = self.m_daytrades.prevtrade()
        if tc:
            H = tc.nv_high()
            B = tc.nv_low()
            C = tc.nv_close()
            pivot = (H + B + C) / 3
            s1 = (2 * pivot) - H
            s2 = pivot - (H - B)
            r1 = (2 * pivot) - B
            r2 = pivot + (H - B)
            return (s2,s1,pivot,r1,r2)
        else:
            return None

    # ---[ market open/close ] ---

    def date(self,d=None):
        if d==None:
            tr = self.m_daytrades.lasttrade()
        else:
            tr = self.m_daytrades.trade(d)
        if tr:
            return tr.date()
        return None

    def sv_date(self,bDisplayShort=False):
        return date2str(self.date(),bDisplayShort)

    def hasOpened(self):
        if self.date() == date.today():
            #print '>>> hasOpened : True'
            return True
        else:
            #print '>>> hasOpened : False'
            return False

    def hasTraded(self):
        if self.isOpen():
            # today is open : check we have a known trade
            if self.date() == date.today():
                #print '>>> hasTraded : True'
                return True
            else:
                #print '>>> hasTraded : False'
                return False
        else:
            # today is closed : check previous open
            if self.m_daytrades.prevtrade():
                # a trade exists !
                return True
            else:
                # no trade
                return False

    def isOpen(self):
        return gCal.isopen(date.today(),self.m_market)

    # ---[ compute all the data ] ---

    def compute(self,todate=None):
        info('%s: compute [%s]' % (self.ticker(),todate))
        if self.m_daytrades!=None:
            self.m_daytrades.compute(todate)

    # ---[ Trends ] ---

    def colorTrend(self,d=None):
        if d==None:
            tc = self.m_daytrades.lasttrade()
            #print 'colorTrend: lastrade close : %.2f date : %s ' % (tc.nv_close(),tc.date())
        else:
            tc = self.m_daytrades.trade(d)
            #print 'colorTrend: specific close : %.2f date : %s ' % (tc.nv_close(),tc.date())
        tp = self.m_daytrades.prevtrade(d)
        if not tp:
            return QUOTE_INVALID
        #print 'colorTrend: previous close : %.2f date : %s ' % (tp.nv_close(),tp.date())
        if tc.nv_close()==tp.nv_close():
            #print 'colorTrend: no change '
            return QUOTE_NOCHANGE
        elif tc.nv_close()<tp.nv_close():
            #print 'colorTrend: RED '
            return QUOTE_RED
        else:
            #print 'colorTrend: GREEN '
            return QUOTE_GREEN

    def colorStop(self):
        cl = self.nv_close()
        if self.nv_number()==0:
            # no share on this quote : inside the target : BUY
            if (cl>=self.nv_stoploss()) and (cl<=self.nv_stopwin()):
                # must buy
                return QUOTE_GREEN
            else:
                # do nothing
                return QUOTE_NOCHANGE
        else:
            # some shares : outside the target : SELL
            if (cl<=self.nv_stoploss()) or (cl>=self.nv_stopwin()):
                # must sell
                return QUOTE_RED
            else:
                # do nothing
                return QUOTE_NOCHANGE

    # ---[ Indicators ] ---

    def nv_ma(self,period=20,d=None):
        if d==None:
            d = self.m_daytrades.lasttrade()
            if d:
                d = d.date()
            else:
                return None
        mm = self.m_daytrades.ma(period,d)
        return mm

    def sv_ma(self,period=20,d=None):
        x = self.nv_ma(period,d)
        if x!=None:
            return "%3.3f" % x
        return " ---.--- "

    def nv_vma(self,period=15,d=None):
        if d==None:
            if d:
                d = d.date()
            else:
                return None
        mm = self.m_daytrades.vma(period,d)
        return mm

    def sv_vma(self,period=15,d=None):
        x = self.nv_vma(period,d)
        if x!=None:
            return "%d" % x
        return " ---------- "

    def nv_ovb(self,d=None):
        if d==None:
            if d:
                d = d.date()
            else:
                return None
        mm = self.m_daytrades.ovb(d)
        return mm

    def sv_ovb(self,d=None):
        x = self.nv_ovb(d)
        if x!=None:
            return "%d" % x
        return " ---------- "

    # ---[ monitor a quote ] ---

    def monitorIt(self,t):
        self.m_isMonitored = t
        return self.m_isMonitored

    # ---[ Command line ] ---

    def printInfo(self):
        print '%s - %s - %s (market=%s)' % (self.isin(),self.ticker(),self.name(),self.market())
        print 'PRU DIR/SRD = %f / %f' % (self.m_DIR_pru,self.m_SRD_pru)
        print 'Cours = %f' % self.nv_close()
        print 'Nbre DIR/SRD/total = %d/%d/%d' % (self.nv_number(QUOTE_CASH),self.nv_number(QUOTE_CREDIT),self.nv_number(QUOTE_BOTH))
        print 'Gain DIR = %f' % ((self.nv_close()-self.m_DIR_pru)*self.nv_number(QUOTE_CASH))
        print 'Gain SRD = %f' % ((self.nv_close()-self.m_SRD_pru)*self.nv_number(QUOTE_CREDIT))
        print 'Candle = %s' % self.ov_candle()
        print 'StopLoss = %s' % self.sv_stoploss()
        print 'StopWin = %s' % self.sv_stopwin()

    # ---[ flush and reload ] ---

    def flushAndReload(self,dlg):
        if self.m_daytrades:
            self.m_daytrades.reset()
            self.m_daytrades = None
        cmdline_importQuoteFromInternet(self,dlg)
        self.compute()

    # ---[ Persistent Properties ] ------------------------

    def setProperty(self,prop,val):
        if prop=='name':
            self.set_name(val)
        elif prop=='ticker':
            self.set_ticker(val)
        elif prop=='live':
            self.set_liveconnector(val)
        elif prop=='import':
            self.set_importconnector(val)
        elif prop=='market':
            self.set_market(val)
        else:
            info('Quote::setProperty(%s): unknown property: %s' % (self.isin(),prop))

    def listProperties(self):
        prop = []
        if self.name()!=self.default_name():
            prop.append('%s;%s;%s' % (self.isin(),'name',self.name()))
        if self.ticker()!=self.default_ticker():
            prop.append('%s;%s;%s' % (self.isin(),'ticker',self.ticker()))
        if self.liveconnector()!=self.default_liveconnector():
            prop.append('%s;%s;%s' % (self.isin(),'live',self.liveconnector().name()))
        if self.importconnector()!=self.default_importconnector():
            prop.append('%s;%s;%s' % (self.isin(),'import',self.importconnector().name()))
        if self.market()!=self.default_market():
            prop.append('%s;%s;%s' % (self.isin(),'market',self.market()))
        return prop

# ============================================================================
# Quotes
# ============================================================================
#
# CSV File format :
#   ISIN;NAME;SICOVAM;TICKER
# ============================================================================

class Quotes(object):
    def __init__(self):
        #debug('Quotes:__init__')
        self._init_()

    def _init_(self):
        self.m_quotes = {}

    def reinit(self):
        info('Quotes::reinit')
        for eachQuote in self.list():
            eachQuote.reinit()

    def list(self):
        return self.m_quotes.values()

    # ---[ Properties ] ---

    def addProperty(self,isin,prop,val):
        if self.m_quotes.has_key(isin):
            self.m_quotes[isin].setProperty(prop,val)

    def loadProperties(self,fp=None):
        # open and read the file to load properties information
        infile = itrade_csv.read(fp,os.path.join(itrade_config.dirUserData,'default.properties.txt'))
        if infile:
            # scan each line to read each quote
            for eachLine in infile:
                item = itrade_csv.parse(eachLine,3)
                if item:
                    # debug('%s ::: %s' % (eachLine,item))
                    self.addProperty(item[0],item[1],item[2])

    def saveProperties(self,fp=None):
        props = []
        for eachQuote in self.list():
            prop = eachQuote.listProperties()
            if prop!=[]:
                props.append(*prop)
        itrade_csv.write(fp,os.path.join(itrade_config.dirUserData,'default.properties.txt'),props)

    # ---[ Stops ] ---

    def addStops(self,isin,loss,win):
        if self.m_quotes.has_key(isin):
            self.m_quotes[isin].setStops(loss,win)

    def loadStops(self,fs=None):
        # open and read the file to load stops information
        infile = itrade_csv.read(fs,os.path.join(itrade_config.dirUserData,'default.stops.txt'))
        if infile:
            # scan each line to read each quote
            for eachLine in infile:
                item = itrade_csv.parse(eachLine,3)
                if item:
                    # debug('%s ::: %s' % (eachLine,item))
                    self.addStops(item[0],item[1],item[2])

    # ---[ Quotes ] ---

    def addQuote(self,isin,name,ticker,market,currency,place):
        # patch for abcbourse.com quotes file :-( (SF bug 1291713)
        if isin[0:2].lower()=='us':
            lg = len(isin)
            if isin[lg-1:lg]=='u':
                isin = isin[:lg-1]

        if self.m_quotes.has_key(isin):
            # update quote
            #print '%r already exists' % self.m_quotes[isin]
            del self.m_quotes[isin]

        # new quote
        self.m_quotes[isin] = Quote(isin,name.upper(),ticker.upper(),market.upper(),currency.upper(),place.upper())
        #debug('Quotes::addQuote(): %s' % self.m_quotes[isin]);
        return True

    def _addLines(self,infile):
        # scan each line to read each quote
        for eachLine in infile:
            item = itrade_csv.parse(eachLine,6)
            if item and len(item)>=6:
                self.addQuote(item[0],item[1],item[2],item[3],item[4],item[5])

    def load(self,fn=None,fs=None):
        # open and read the file to load these quotes information
        infile = itrade_csv.read(fn,os.path.join(itrade_config.dirSysData,'quotes.txt'))
        if infile:
            self._addLines(infile)

        # them open and read user file
        infile = itrade_csv.read(fn,os.path.join(itrade_config.dirUserData,'quotes.txt'))
        if infile:
            self._addLines(infile)

    def saveListOfQuotes(self,fn=None):
        # __x sys vs usr file. How to discriminate ?
        #
        # open and write the file with these quotes information
        itrade_csv.write(fn,os.path.join(itrade_config.dirSysData,'quotes.txt'),self.m_quotes.values())

        print 'List of symbols saved.'

    # ---[ Lookup (optionaly, filter by market) ] ---

    def lookupISIN(self,isin):
        return self.m_quotes.get(isin,None)

    def lookupTicker(self,ticker,market=None):
        for eachVal in self.m_quotes.values():
            if eachVal.ticker() == ticker:
                if market==None or (market==eachVal.market()):
                    return eachVal
        return None

    def lookupName(self,name,market):
        for eachVal in self.m_quotes.values():
            if eachVal.name() == name:
                if market==None or (market==eachVal.market()):
                    return eachVal
        return None

    # ---[ Trades ] ---

    def loadTrades(self,fi=None):
        # read quotes data
        for eachKey in self.m_quotes.keys():
            self.m_quotes[eachKey].loadTrades(fi)

    def saveTrades(self,fe=None):
        # read quotes data
        for eachKey in self.m_quotes.keys():
            self.m_quotes[eachKey].saveTrades(fe)

# ============================================================================
# Export
# ============================================================================

try:
    ignore(quotes)
except NameError:
    quotes = Quotes()

quotes.load()

# ============================================================================
# Test
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    info('test1 %s' % quotes.lookupISIN('FR0000072621'));
    info('test2 %s' % quotes.lookupTicker('OSI').ticker());
    info('test3 %s' % quotes.lookupTicker('OSI').isin());
    info('test4 %s' % quotes.lookupTicker('OSI').name());
    info('test5 %s' % quotes.lookupTicker('OSI').descr());

    quote = quotes.lookupTicker('OSI')
    quote.loadTrades('import/Cortal-2005-01-07.txt')
    info('test6 %s' % quote.trades().trade('20050104'));

    quotes.loadTrades('import/Cortal-2005-01-07.txt')
    quotes.loadTrades('import/Cortal-2005-01-14.txt')
    quotes.loadTrades('import/Cortal-2005-01-21.txt')
    quote = quotes.lookupTicker('EADT')
    info('test7 %s' % quote.trades().trade('20050104'));

#    quotes.saveTrades()
#    quotes.saveListOfQuotes(os.path.join(itrade_config.dirSysData,'test.txt'))

    print fmtVolume(1)
    print fmtVolume(12)
    print fmtVolume(130)
    print fmtVolume(1400)
    print fmtVolume(15000)
    print fmtVolume(160000)
    print fmtVolume(1700000)
    print fmtVolume(18000000)

# ============================================================================
# That's all folks !
# ============================================================================
