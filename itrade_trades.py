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
# 2004-01-08    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from __future__ import absolute_import
from datetime import date
from math import pow, sqrt
import logging
import os

# numpy
from numpy import array

# iTrade system
import itrade_config
from itrade_logging import setLevel, info, debug
import itrade_csv
from itrade_datation import gCal, Datation
from itrade_candle import Candle, CANDLE_VOLUME_AVERAGE, CANDLE_VOLUME_TREND_NOTREND
from six.moves import range

# ============================================================================
# Trade
# ============================================================================

class Trade(object):
    def __init__(self, trades, d, open, high, low, close, volume, idx):
        if d[4] == '-':
            debug(u'Trade::__init__():{}: {:d} {:d} {:d}'.format(d, int(d[0:4]), int(d[5:7]), int(d[8:10])))
            self.m_date = date(int(d[0:4]), int(d[5:7]), int(d[8:10]))
        else:
            debug(u'Trade::__init__():{}: {:d} {:d} {:d}'.format(d, int(d[0:4]), int(d[4:6]), int(d[6:8])))
            self.m_date = date(int(d[0:4]), int(d[4:6]), int(d[6:8]))
        self.m_open = float(open)
        if self.m_open < 0.0:
            self.m_open = 0.0
        self.m_close = float(close)
        if self.m_close < 0.0:
            self.m_close = 0.0
        self.m_low = float(low)
        if self.m_low < 0.0:
            self.m_low = 0.0
        self.m_high = float(high)
        if self.m_high < 0.0:
            self.m_high = 0.0
        self.m_volume = int(volume)
        if self.m_volume < 0:
            self.m_volume = 0
        self.m_trades = trades
        self.m_index = idx

    def __repr__(self):
        return u'{};{};{:f};{:f};{:f};{:f};{:d}'.format(self.m_trades.quote().key(),self.m_date, self.m_open, self.m_high, self.m_low, self.m_close, self.m_volume)

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
# create_array() - function helper
# ============================================================================

def create_array(defval):
    n = gCal.lastindex()+1
    a = array([defval]*n)
    return a

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
        debug(u'Trades:__init__({})'.format(quote))
        self.m_quote = quote
        self._init_()

    def _init_(self):
        self.m_dirty = False
        self.m_trades = {}
        self.m_candles = {}
        self.m_firsttrade = None
        self.m_lasttrade = None
        self.m_lastimport = None

        #self.m_date = {}
        self.m_inOpen = create_array(-1.0)
        self.m_inClose = create_array(-1.0)
        self.m_inLow = create_array(-1.0)
        self.m_inHigh = create_array(-1.0)
        self.m_inVol = create_array(int(-1))
        self.m_ma20 = create_array(-1.0)
        self.m_ma50 = create_array(-1.0)
        self.m_ma100 = create_array(-1.0)
        self.m_ma150 = create_array(-1.0)
        self.m_vma15 = create_array(-1.0)
        self.m_ovb = create_array(int(0))
        self.m_rsi14 = create_array(-1.0)

        self.m_stoK = create_array(-1.0)
        self.m_stoD = create_array(-1.0)

        self.m_bollUp = create_array(-1.0)
        self.m_bollM = create_array(-1.0)
        self.m_bollDn = create_array(-1.0)

        self.m_candles = {}

    def quote(self):
        return self.m_quote

    def trades(self, newerfirst=True):
        items = list(self.m_trades.values())
        items.sort(key=Trade.date, reverse=newerfirst)
        return items
        #return self.m_trades

    def candles(self):
        return self.m_candles

    def reset(self, infile=None):
        self._init_()
        if not infile:
            idfile = os.path.join(itrade_config.dirCacheData, u'{}.id'.format(self.m_quote.key()))
            try:
                os.remove(idfile)
            except OSError:
                pass
            infile = os.path.join(itrade_config.dirCacheData, u'{}.txt'.format(self.m_quote.key()))
        try:
            os.remove(infile)
        except OSError:
            pass

    def load(self, infile=None):
        infile = itrade_csv.read(infile, os.path.join(itrade_config.dirCacheData, u'{}.txt'.format(self.m_quote.key())))
        #print 'Trades:load::',infile
        # scan each line to read each trade
        debug(u'Trades::load {} {}'.format(self.m_quote.ticker(), self.m_quote.key()))
        for eachLine in infile:
            item = itrade_csv.parse(eachLine, 7)
            if item:
                if (item[0]==self.m_quote.key()) or (item[0]==self.m_quote.isin() and item[0]!=''):
                    #print item
                    debug(u'Trades::load {} on {}'.format(item[5], item[1]))
                    self.add(item, bImporting=True)

    def imp(self, data, bLive):
        #debug(u'Trades::imp {} : {} : bLive={}'.format(self.m_quote.ticker(), data, bLive))
        #print(data)
        if data:
            # scan each line to read each trade
            for eachLine in data:
                item = itrade_csv.parse(eachLine, 7)
                if item:
                    if (item[0]==self.m_quote.key()) or (item[0]==self.m_quote.isin() and item[0]!=''):
                        #print item
                        self.add(item, bImporting=not bLive)

    def save(self, outfile=None):
        #debug(u'Trades::save {} {}'.format(self.m_quote.ticker(), self.m_quote.key()))
        if list(self.m_trades.keys()):
            # do not save today trade
            ajd = date.today()
            if ajd in self.m_trades:
                tr = self.m_trades[ajd]
                del self.m_trades[ajd]
                if itrade_config.verbose:
                    info(u'Do not save ajd={}:{}'.format(ajd, tr))
            else:
                tr = None

            # save all trades (except today)
            itrade_csv.write(outfile, os.path.join(itrade_config.dirCacheData, u'{}.txt'.format(self.m_quote.key())), list(self.m_trades.values()))
            self.m_dirty = False

            # restore today trade
            if tr:
                self.m_trades[ajd] = tr

    def add(self, item, bImporting):
        debug(u'Trades::add() before: {} : bImporting={}'.format(item, bImporting))

        idx = gCal.index(Datation(item[1]).date())
        if idx == -1:
            debug(u'invalid date in: {}'.format(item))
            # __x need to save file
            self.m_dirty = True
            return False

        tr = Trade(self, item[1], item[2], item[3], item[4], item[5], item[6], idx)

        # NB: replace existing date ('cause live update)
        self.m_trades[tr.date()] = tr
        self.m_inOpen[idx] = tr.nv_open()
        self.m_inClose[idx] = tr.nv_close()
        self.m_inLow[idx] = tr.nv_low()
        self.m_inHigh[idx] = tr.nv_high()
        self.m_inVol[idx] = tr.nv_volume()
        #self.m_date[idx] = tr.date()

        #if not bImporting:
        #    print u'lasttrade: {}   new trade : {}'.format(self.m_lasttrade.date(), tr.date())

        # update firt and last trade
        if self.m_firsttrade is None:
            self.m_firsttrade = tr
            self.m_lasttrade = tr
        if tr.date()<=self.m_firsttrade.date():
            self.m_firsttrade = tr
        if tr.date()>=self.m_lasttrade.date():
            self.m_lasttrade = tr

        # update last import
        if bImporting:
            if self.m_lastimport is None:
                self.m_lastimport = tr
            if tr.date() >= self.m_lastimport.date():
                self.m_lastimport = tr

        #debug(u'Trades::add() after: {}'.format(tr))
        return True

    def lastimport(self):
        return self.m_lastimport

    def lasttrade(self):
        return self.m_lasttrade

    def prevtrade(self, d=None):
        if d is None:
            tc = self.m_lasttrade
        else:
            if d in self.m_trades:
                tc = self.m_trades[d]
            else:
                return None
        if tc:
            idx = tc.index()
            while idx > 0:
                idx = idx - 1
                if self.m_inClose[idx] >= 0.0:
                    return self.m_trades[gCal.date(idx)]
        return None

    def firsttrade(self):
        return self.m_firsttrade

    def trade(self, d):
        if d in self.m_trades:
            return self.m_trades[d]
        else:
            info(u'trades:trade() not found: {}'.format(d))
            return None

    def has_trade(self,idx):
        return self.m_inClose[idx] >= 0.0

    def ma(self,period,idx):
        """ temp """
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
        """ temp """
        if period==15:
            return self.vma15(idx)
        else:
            return None

    def ma20(self,idx):
        if not isinstance(idx,int):
            idx = gCal.index(idx)
        if self.m_ma20[idx]<0.0:
            self.compute_ma20(idx)
        return self.m_ma20[idx]

    def ma50(self,idx):
        if not isinstance(idx,int):
            idx = gCal.index(idx)
        if self.m_ma50[idx]<0.0:
            self.compute_ma50(idx)
        return self.m_ma50[idx]

    def ma100(self,idx):
        if not isinstance(idx,int):
            idx = gCal.index(idx)
        if self.m_ma100[idx]<0.0:
            self.compute_ma100(idx)
        return self.m_ma100[idx]

    def ma150(self,idx):
        if not isinstance(idx,int):
            idx = gCal.index(idx)
        if self.m_ma150[idx]<0.0:
            self.compute_ma150(idx)
        return self.m_ma150[idx]

    def rsi(self,period,idx):
        """ temp """
        if period==14:
            return self.rsi14(idx)
        else:
            return None

    def rsi14(self,idx):
        if not isinstance(idx,int):
            idx = gCal.index(idx)
        if self.m_rsi14[idx]<0.0:
            self.compute_rsi14(idx)
        return self.m_rsi14[idx]

    def stoK(self,idx):
        if not isinstance(idx,int):
            idx = gCal.index(idx)
        if self.m_stoK[idx]<0.0:
            self.compute_stoK(idx)
        return self.m_stoK[idx]

    def stoD(self,idx):
        if not isinstance(idx,int):
            idx = gCal.index(idx)
        if self.m_stoD[idx]<0.0:
            self.compute_stoD(idx)
        return self.m_stoD[idx]

    def vma15(self,idx):
        if not isinstance(idx,int):
            idx = gCal.index(idx)
        if self.m_vma15[idx]<0.0:
            self.compute_vma15(idx)
        return self.m_vma15[idx]

    def bollinger(self,idx,band=1):
        if not isinstance(idx,int):
            idx = gCal.index(idx)
        if self.m_bollM[idx]<0.0:
            self.compute_bollinger(idx)
        if band==0:
            return self.m_bollDn[idx]
        elif band==1:
            return self.m_bollM[idx]
        else:
            return self.m_bollUp[idx]

    def ovb(self,idx):
        if not isinstance(idx,int):
            idx = gCal.index(idx)
        return self.m_ovb[idx]

    def close(self,idx):
        if not isinstance(idx,int):
            idx = gCal.index(idx)
        while idx>=0 and self.m_inClose[idx]<0.0:
            # seek existing previous close !
            idx = idx - 1
        if idx < 0:
            return 0.0
        return self.m_inClose[idx]

    def candle(self, d):
        if d in self.m_candles:
            return self.m_candles[d]
        else:
            print(u'trades:candle() not found: {}'.format(d))
            return None

    def compute(self, d=None):
        # default date == last trade
        if d is None:
            if not self.m_lasttrade:
                print(u'{} : no trade'.format(self.m_quote.key()))
                return
            d = self.m_lasttrade.date()

        # trade
        tr = self.trade(d)
        if tr is None:
            print('bug bug')
            return False

        # create candle
        ca = Candle(tr.nv_open(), tr.nv_high(), tr.nv_low(), tr.nv_close(), CANDLE_VOLUME_AVERAGE, CANDLE_VOLUME_TREND_NOTREND)
        self.m_candles[tr.date()] = ca

        # get index given date
        idx = tr.index()

        # compute mm
        self.compute_ma20(idx)
        self.compute_ma50(idx)
        self.compute_ma100(idx)
        self.compute_ma150(idx)
        self.compute_rsi14(idx)

        # compute stochastic (14 days)
        self.compute_stoD(idx)

        # volumes indicators
        self.compute_vma15(idx)
        self.compute_ovb()

        return True

    def compute_ma150(self, i):
        #debug(u'{}: compute MA150 [{:d}]'.format(self.m_quote.ticker(), i))
        s = 0.0
        n = 0
        j = i
        while n < 150 and j >= 0:
            if self.m_inClose[j] >= 0.0:
                s = s + self.m_inClose[j]
                n = n + 1
            j = j - 1
        if n > 0:
            self.m_ma150[i] = s/float(n)
        else:
            self.m_ma150[i] = -1.0

    def compute_ma100(self, i):
        #debug(u'{}: compute MA100 [{:d}]'.formmat(self.m_quote.ticker(), i))
        s = 0.0
        n = 0
        j = i
        while n < 100 and j >= 0:
            if self.m_inClose[j] >= 0.0:
                s = s + self.m_inClose[j]
                n = n + 1
            j = j - 1
        if n > 0:
            self.m_ma100[i] = s/float(n)
        else:
            self.m_ma100[i] = -1.0

    def compute_ma50(self, i):
        #debug('%s: compute MA50 [%d]' % (self.m_quote.ticker(),i))
        s = 0.0
        n = 0
        j = i
        while n < 50 and j >= 0:
            if self.m_inClose[j] >= 0.0:
                s = s + self.m_inClose[j]
                n = n + 1
            j = j - 1
        if n > 0:
            self.m_ma50[i] = s/float(n)
        else:
            self.m_ma50[i] = -1.0

    def compute_ma20(self, i):
        #debug('%s: compute MA20 [%d]' % (self.m_quote.ticker(),i))
        s = 0.0
        n = 0
        j = i
        while n < 20 and j >= 0:
            if self.m_inClose[j] >= 0.0:
                s = s + self.m_inClose[j]
                n = n + 1
            j = j - 1
        if n>0:
            self.m_ma20[i] = s/float(n)
        else:
            self.m_ma20[i] = -1.0

    def compute_rsi14(self, i):
        #debug('%s: compute RSI14 [%d]' % (self.m_quote.ticker(),i))
        h = 0.0
        b = 0.0
        n = 14*10
        if i < n:
            n=i
        while n >= 0:
            if self.m_inClose[i-n]>=0.0:
                t = self.m_inClose[i-n] - self.close(i-n-1)
                th = 0.0
                tb = 0.0
                if t>0:
                    th = t
                if t<0:
                    tb = abs(t)

                b = ((13.0*b) + tb) / 14.0
                h = ((13.0*h) + th) / 14.0

            n = n - 1
        if b == 0.0:
            self.m_rsi14[i] = 100.0
        else:
            self.m_rsi14[i] = 100.0 - (100.0/(1.0+(h / b)))

    def compute_minmax(self, i, period):
        l = 9999999.0
        h = 0.0
        n = 0
        j = i
        while n < period and j >= 0:
            if self.m_inHigh[j] > h:
                h = self.m_inHigh[j]

            if self.m_inLow[j] < l:
                l = self.m_inLow[j]

            n = n + 1
            j = j - 1
        return l, h

    def compute_stoK(self, i):
        #debug('%s: compute STO K [%d]' % (self.m_quote.ticker(),i))
        mc = (self.close(i) + self.close(i-1) + self.close(i-2))/3
        l1, h1 = self.compute_minmax(i, 14)
        l2, h2 = self.compute_minmax(i-1, 14)
        l3, h3 = self.compute_minmax(i-2, 14)
        ml = (l1 + l2 + l3) / 3
        mh = (h1 + h2 + h3) / 3

        t = ((mc - ml) / (mh - ml)) * 100.0
        if t < 0.0:
            t = 0.0
        if t > 100.0:
            t = 100.0
        self.m_stoK[i] = t

    def compute_stoD(self, i):
        #debug('%s: compute STO D [%d]' % (self.m_quote.ticker(),i))
        s = 0.0
        n = 0
        j = i
        while n<5 and j >= 0:
            s = s + self.stoK(j)
            n = n + 1
            j = j - 1
        if n>0:
            self.m_stoD[i] = s/float(n)
        else:
            self.m_stoD[i] = -1

    def compute_vma15(self, i):
        #debug(<'%s: compute VMA15 [%d]' % (self.m_quote.ticker(),i))
        s = int(0)
        n = 0
        j = i
        while n < 15 and j >= 0:
            if self.m_inClose[j] >= 0.0:
                s = s + self.m_inVol[j]
                n = n + 1
            j = j - 1
        if n>0:
            self.m_vma15[i] = float(s/n)
        else:
            self.m_vma15[i] = -1

    def compute_ovb(self):
        ovb = int(0)
        for j in range(gCal.lastindex()+1):
            if self.m_inClose[j] >= 0.0:
                pc = self.close(j-1)
                if self.m_inClose[j] >= pc:
                    ovb = ovb + int(self.m_inVol[j])
                else:
                    ovb = ovb - int(self.m_inVol[j])

            self.m_ovb[j] = ovb

    def compute_bollinger(self, i):
        #debug('%s: compute BOLLINGER n=20,d=2 [%d,%d]' % (self.m_quote.ticker(),i-20+1,i+1))
        sm = 0.0
        ecart = 0.0
        n = 0
        j = i
        while n < 20 and j >= 0:
            if self.m_inClose[j] >= 0.0:
                sm = sm + self.m_inClose[j]
                n = n + 1
            j = j - 1

        if n > 0:
            # calculate MA20(i)
            self.m_bollM[i] = float(sm/n)

            # calculate MA plus 2 standard deviations
            n = 0
            j = i
            while n < 20 and j >= 0:
                if self.m_inClose[j] >= 0.0:
                    ecart = ecart + pow(self.m_inClose[j] - self.m_bollM[i],2)
                    n = n + 1
                j = j - 1

            ecart = 2*sqrt(float(ecart)/n)
            self.m_bollUp[i] = self.m_bollM[i] + ecart
            self.m_bollDn[i] = self.m_bollM[i] - ecart
        else:
            self.m_bollM[i] = -1.0
            self.m_bollUp[i] = -1.0
            self.m_bollDn[i] = -1.0

# ============================================================================
# Test
# ============================================================================

def main():
    setLevel(logging.INFO)
    itrade_config.app_header()
    # load extensions
    import itrade_ext
    itrade_ext.loadExtensions(itrade_config.fileExtData, itrade_config.dirExtData)
    from itrade_quotes import quotes, initQuotesModule
    initQuotesModule()
    quotes.loadMarket('EURONEXT')
    quotes.loadMarket('NASDAQ')
    quote = quotes.lookupTicker(ticker='AAPL', market='NASDAQ')
    info(u'test1 {}'.format(quote))
    quote = quotes.lookupTicker(ticker='OSI', market='EURONEXT')
    info(u'test2 {}'.format(quote))
    trades = Trades(quote)
    trades.load('import/Cortal-2005-01-07.txt')
    trades.load('import/Cortal-2005-01-14.txt')
    trades.load('import/Cortal-2005-01-21.txt')
    info(u'test3 {}'.format(trades.trade(date(2005, 1, 4))))


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
