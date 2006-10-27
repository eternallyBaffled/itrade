#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_trades.py
#
# Description: Trades
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
from math import pow,sqrt
import logging

# iTrade system
from itrade_logging import *
import itrade_csv
import itrade_datation
from itrade_candle import *

# ============================================================================
# Trade
# ============================================================================

class Trade(object):
    def __init__(self,trades,d,open,high,low,close,volume,idx):
        if d[4]=='-':
            #debug('Trade::__init__():%s: %d %d %d' % (d,long(d[0:4]),long(d[5:7]),long(d[8:10])));
            self.m_date = date(long(d[0:4]),long(d[5:7]),long(d[8:10]))
        else:
            #debug('Trade::__init__():%s: %d %d %d' % (d,long(d[0:4]),long(d[4:6]),long(d[6:8])));
            self.m_date = date(long(d[0:4]),long(d[4:6]),long(d[6:8]))
        self.m_open = float(open)
        self.m_close = float(close)
        self.m_low = float(low)
        self.m_high = float(high)
        self.m_volume = long(volume)
        self.m_trades = trades
        self.m_index = idx

    def __repr__(self):
        return '%s;%s;%f;%f;%f;%f;%d' % (self.m_trades,self.m_date, self.m_open, self.m_high, self.m_low, self.m_close, self.m_volume)

    def date(self):
        return self.m_date

    def nv_open(self):
        return self.m_open

    def nv_close(self):
        return self.m_close

    def nv_low(self):
        return self.m_low

    def nv_high(self):
        return self.m_high

    def nv_volume(self):
        return self.m_volume

    def index(self):
        return self.m_index

# ============================================================================
# Trades
# ============================================================================
#
# CSV File format (EBP from boursorama) :
#
#   ISIN;DATE;OPEN;HIGH;LOW;CLOSE;VOLUME
# ============================================================================

class Trades(object):
    def __init__(self,quote):
        #debug('Trades:__init__(%s)' % quote)
        self.m_quote = quote
        self._init_()

    def _init_(self):
        self.m_dirty = False
        self.m_trades = {}
        self.m_candles = {}
        self.m_firsttrade = None
        self.m_lasttrade = None
        self.m_lastimport = None
        self.m_date = {}
        self.m_inOpen = {}
        self.m_inClose = {}
        self.m_inLow = {}
        self.m_inHigh = {}
        self.m_inVol = {}
        self.m_ma20 = {}
        self.m_ma50 = {}
        self.m_ma100 = {}
        self.m_ma150 = {}
        self.m_vma15 = {}
        self.m_ovb = {}

        self.m_bollUp = {}
        self.m_bollM = {}
        self.m_bollDn = {}

        self.m_candles = {}

    def quote(self):
        return self.m_quote

    def trades(self):
        return self.m_trades

    def candles(self):
        return self.m_candles

    def reset(self,infile=None):
        self._init_()
        if not infile:
            infile = os.path.join(itrade_config.dirCacheData,self.m_quote.isin())+'.txt'
        try:
            os.remove(infile)
        except OSError:
            pass

    def load(self,infile=None):
        infile = itrade_csv.read(infile,os.path.join(itrade_config.dirCacheData,self.m_quote.isin())+'.txt')
        #print infile
        if infile:
            # scan each line to read each trade
            #debug('Trades::load %s %s' % (self.m_quote.ticker(),self.m_quote.isin()))
            for eachLine in infile:
                item = itrade_csv.parse(eachLine,7)
                if item:
                    if (item[0]==self.m_quote.isin()):
                        #print item
                        self.add(item,bImporting=True);

    def imp(self,data,bLive):
        #debug('Trades::imp %s : %s : bLive=%s' % (self.m_quote.ticker(),data,bLive))
        data = data.split('\r\n')
        #print data
        if data:
            # scan each line to read each trade
            for eachLine in data:
                item = itrade_csv.parse(eachLine,7)
                if item:
                    if (item[0]==self.m_quote.isin()):
                        #print item
                        self.add(item,bImporting=not bLive);

    def save(self,outfile=None):
        #debug('Trades::save %s %s' % (self.m_quote.ticker(),self.m_quote.isin()))
        if self.m_trades.keys():
            # do not save today trade
            ajd = date.today()
            if self.m_trades.has_key(ajd):
                tr = self.m_trades[ajd]
                del self.m_trades[ajd]
                info('Do not save ajd=%s:%s' % (ajd,tr))
            else:
                tr = None

            # save all trades (except today)
            itrade_csv.write(outfile,os.path.join(itrade_config.dirCacheData,self.m_quote.isin())+'.txt',self.m_trades.values())
            self.m_dirty = False

            # restore today trade
            if tr:
                self.m_trades[ajd] = tr

    def add(self,item,bImporting):
        #debug('Trades::add() before: %s : bImporting=%s' % (item,bImporting));

        idx = itrade_datation.gCal.index(itrade_datation.Datation(item[1]).date())
        if idx==-1:
            #debug('invalid data: %s' % item)
            # __x need to save file
            self.m_dirty = True
            return False
        tr = Trade(item[0],item[1],item[2],item[3],item[4],item[5],item[6],idx)

        # NB: replace existing date ('cause live update)
        self.m_trades[tr.date()] = tr
        self.m_inOpen[idx] = tr.nv_open()
        self.m_inClose[idx] = tr.nv_close()
        self.m_inLow[idx] = tr.nv_low()
        self.m_inHigh[idx] = tr.nv_high()
        self.m_inVol[idx] = tr.nv_volume()
        self.m_date[idx] = tr.date()

        #if not bImporting:
        #    print 'lasttrade: %s   new trade : %s' %(self.m_lasttrade.date(),tr.date())

        # update firt and last trade
        if self.m_firsttrade==None:
            self.m_firsttrade = tr
            self.m_lasttrade = tr
        if tr.date()<=self.m_firsttrade.date():
            self.m_firsttrade = tr
        if tr.date()>=self.m_lasttrade.date():
            self.m_lasttrade = tr

        # update last import
        if bImporting:
            if self.m_lastimport==None:
                self.m_lastimport = tr
            if tr.date()>=self.m_lastimport.date():
                self.m_lastimport = tr

        #debug('Trades::add() after: %s' % tr);
        return True

    def lastimport(self):
        return self.m_lastimport

    def lasttrade(self):
        return self.m_lasttrade

    def prevtrade(self,d=None):
        if d==None:
            tc = self.m_lasttrade
        else:
            if self.m_trades.has_key(d):
                tc = self.m_trades[d]
            else:
                return None
        if tc:
            idx = tc.index()
            while idx > 0:
                idx = idx - 1
                if self.m_date.has_key(idx):
                    return self.m_trades[self.m_date[idx]]
        return None

    def firsttrade(self):
        return self.m_firsttrade

    def trade(self,d):
        if self.m_trades.has_key(d):
            return self.m_trades[d]
        else:
            #info('trades:trade() not found: %s' % d)
            return None

    def ma(self,period,idx):
        ''' temp '''
        if period==20:
            return self.ma20(idx)
        elif period==50:
            return self.ma50(idx)
        elif period==100:
            return self.ma100(idx)
        elif period==150:
            return self.ma150(idx)
        else:
            return None

    def vma(self,period,idx):
        ''' temp '''
        if period==15:
            return self.vma15(idx)
        else:
            return None

    def ma20(self,idx):
        if not isinstance(idx,int):
            idx = itrade_datation.gCal.index(idx)
        if not self.m_ma20.has_key(idx):
            self.compute_ma20(idx)
        return self.m_ma20[idx]

    def ma50(self,idx):
        if not isinstance(idx,int):
            idx = itrade_datation.gCal.index(idx)
        if not self.m_ma50.has_key(idx):
            self.compute_ma50(idx)
        return self.m_ma50[idx]

    def ma100(self,idx):
        if not isinstance(idx,int):
            idx = itrade_datation.gCal.index(idx)
        if not self.m_ma100.has_key(idx):
            self.compute_ma100(idx)
        return self.m_ma100[idx]

    def ma150(self,idx):
        if not isinstance(idx,int):
            idx = itrade_datation.gCal.index(idx)
        if not self.m_ma150.has_key(idx):
            self.compute_ma150(idx)
        return self.m_ma150[idx]

    def vma15(self,idx):
        if not isinstance(idx,int):
            idx = itrade_datation.gCal.index(idx)
        if not self.m_vma15.has_key(idx):
            self.compute_vma15(idx)
        return self.m_vma15[idx]

    def bollinger(self,idx,band=1):
        if not isinstance(idx,int):
            idx = itrade_datation.gCal.index(idx)
        if not self.m_bollM.has_key(idx):
            self.compute_bollinger(idx)
        if band==0:
            return self.m_bollDn[idx]
        elif band==1:
            return self.m_bollM[idx]
        else:
            return self.m_bollUp[idx]

    def ovb(self,idx):
        if not isinstance(idx,int):
            idx = itrade_datation.gCal.index(idx)
        if not self.m_ovb.has_key(idx):
            print idx,self.m_date[idx]
        #    self.compute_ovb(idx)
        return self.m_ovb[idx]

    def close(self,idx):
        if not isinstance(idx,int):
            idx = itrade_datation.gCal.index(idx)
        while idx>=0 and (not self.m_inClose.has_key(idx)):
            # seek existing previous close !
            idx = idx - 1
        if idx < 0:
            return 0.0
        return self.m_inClose[idx]

    def candle(self,d):
        if self.m_candles.has_key(d):
            return self.m_candles[d]
        else:
            print 'trades:candle() not found: %s' % d
            return None

    def compute(self,d=None):
        # default date == last trade
        if d==None:
            if not self.m_lasttrade:
                print '%s : no trade' % self.m_quote.isin()
                return
            d = self.m_lasttrade.date()

        # trade
        tr = self.trade(d)
        if tr==None:
            print 'bug bug'
            return False

        # create candle
        ca = Candle(tr.nv_open(),tr.nv_high(),tr.nv_low(),tr.nv_close(),CANDLE_VOLUME_AVERAGE,CANDLE_VOLUME_TREND_NOTREND)
        self.m_candles[tr.date()] = ca

        # get index given date
        idx = tr.index()

        # compute mm
        self.compute_ma20(idx)
        self.compute_ma50(idx)
        self.compute_ma100(idx)
        self.compute_ma150(idx)

        # volumes indicators
        self.compute_vma15(idx)
        self.compute_ovb()

        return True

    def compute_ma150(self,i):
        debug('%s: compute MA150 [%d,%d]' % (self.m_quote.ticker(),i-150+1,i+1))
        s = 0
        n = 0
        for j in range(i-150+1,i+1):
            if self.m_inClose.has_key(j):
                s = s + self.m_inClose[j]
                n = n + 1
        if n>0:
            self.m_ma150[i] = float(s/n)
        else:
            self.m_ma150[i] = None

    def compute_ma100(self,i):
        debug('%s: compute MA100 [%d,%d]' % (self.m_quote.ticker(),i-100+1,i+1))
        s = 0
        n = 0
        for j in range(i-100+1,i+1):
            if self.m_inClose.has_key(j):
                s = s + self.m_inClose[j]
                n = n + 1
        if n>0:
            self.m_ma100[i] = float(s/n)
        else:
            self.m_ma100[i] = None

    def compute_ma50(self,i):
        debug('%s: compute MA50 [%d,%d]' % (self.m_quote.ticker(),i-50+1,i+1))
        s = 0
        n = 0
        for j in range(i-50+1,i+1):
            if self.m_inClose.has_key(j):
                s = s + self.m_inClose[j]
                n = n + 1
        if n>0:
            self.m_ma50[i] = float(s/n)
        else:
            self.m_ma50[i] = None

    def compute_ma20(self,i):
        debug('%s: compute MA20 [%d,%d]' % (self.m_quote.ticker(),i-20+1,i+1))
        s = 0
        n = 0
        for j in range(i-20+1,i+1):
            if self.m_inClose.has_key(j):
                s = s + self.m_inClose[j]
                n = n + 1
        if n>0:
            self.m_ma20[i] = float(s/n)
        else:
            self.m_ma20[i] = None

    def compute_vma15(self,i):
        debug('%s: compute VMA15 [%d,%d]' % (self.m_quote.ticker(),i-15+1,i+1))
        s = long(0)
        n = 0
        for j in range(i-15+1,i+1):
            if self.m_inVol.has_key(j):
                s = s + self.m_inVol[j]
                n = n + 1
        if n>0:
            self.m_vma15[i] = float(s/n)
        else:
            self.m_vma15[i] = None

    def compute_ovb(self):
        ovb = long(0)
        for j in range(0,itrade_datation.gCal.lastindex()+1):
            if self.m_inVol.has_key(j):
                pc = self.close(j-1)
                if self.m_inClose[j]>=pc:
                    ovb = ovb + long(self.m_inVol[j])
                else:
                    ovb = ovb - long(self.m_inVol[j])

            self.m_ovb[j] = ovb

    def compute_bollinger(self,i):
        debug('%s: compute BOLLINGER n=20,d=2 [%d,%d]' % (self.m_quote.ticker(),i-20+1,i+1))
        sm = 0
        ecart = 0
        n = 0
        for j in range(i-20+1,i+1):
            if self.m_inClose.has_key(j):
                sm = sm + self.m_inClose[j]
                n = n + 1
        if n>0:
            # calculate MA20(i)
            self.m_bollM[i] = float(sm/n)

            # calculate MA plus 2 standard deviations
            for j in range(i-20+1,i+1):
                if self.m_inClose.has_key(j):
                    ecart = ecart + pow(self.m_inClose[j] - self.m_bollM[i],2)

            ecart = 2*sqrt(float(ecart)/n)
            self.m_bollUp[i] = self.m_bollM[i] + ecart
            self.m_bollDn[i] = self.m_bollM[i] - ecart
        else:
            self.m_bollM[i] = None
            self.m_bollUp[i] = None
            self.m_bollDn[i] = None

# ============================================================================
# Test
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    quote = quotes.lookupISIN('FR0000072621');
    info('test1 %s' % quote );

    quote = quotes.lookupISIN('US0378331005');
    info('test2 %s' % quote );

    trade = Trades(quote)
    trade.load('import/Cortal-2005-01-07.txt')
    trade.load('import/Cortal-2005-01-14.txt')
    trade.load('import/Cortal-2005-01-21.txt')

    info('test3 %s' % trade.trade('20050104'));

# ============================================================================
# That's all folks !
# ============================================================================