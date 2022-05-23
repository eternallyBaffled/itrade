#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_matrix.py
#
# Description: Matrix
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
# 2004-02-20    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
import logging
import os

# iTrade system
import itrade_config
from itrade_logging import setLevel, info, debug
from itrade_quotes import quotes, quote_reference
import itrade_csv

# ============================================================================
# TradingMatrix
#
# desc: quotes under monitoring or under trading
#
# ============================================================================

class TradingMatrix(object):
    def __init__(self):
        self._init_()

    def list(self):
        return self.m_quotes.values()

    def _init_(self):
        self.m_quotes = {}

    def reinit(self):
        self._init_()

    # load 'matrix.txt'
    def load(self, fn):
        infile = itrade_csv.read(None, os.path.join(itrade_config.dirUserData, u'{}.matrix.txt'.format(fn)))
        # scan each line to read each quote
        for eachLine in infile:
            item = itrade_csv.parse(eachLine, 1)
            if item:
                if len(item) > 4:
                    # print('addKey:new fmt: %s : %s : %s : %s '% (item[0],item[2],item[3],item[5]))
                    ref = None

                    # be sure the market is loaded
                    quotes.loadMarket(item[3])

                    if item[0] == '':
                        quote = quotes.lookupTicker(ticker=item[2], market=item[3], place=item[5])
                        if quote:
                            ref = quote.key()

                    if not ref:
                        ref = quote_reference(isin=item[0], ticker=item[2], market=item[3], place=item[5])

                    if not self.addKey(ref):
                        print(u'load (new format): {}/{} : quote not found in quotes list ! (ref={})'.format(item[0], item[2], ref))

                elif len(item) <= 4:
                    print('old matrix format : not supported anymore')

    # save 'matrix.txt'
    def save(self, fn):
        itrade_csv.write(None, os.path.join(itrade_config.dirUserData, u'%s.matrix.txt'.format(fn)), self.m_quotes.values())

    # save all trades of the matrix
    def saveTrades(self):
        for eachQuote in self.list():
            eachQuote.saveTrades()

    # load some trades on the matrix
    def loadTrades(self, fi=None):
        for eachQuote in self.list():
            eachQuote.loadTrades(fi)

    # flush historic caches on the matrix
    def flushTrades(self):
        for eachQuote in self.list():
            eachQuote.flushTrades()

    # flush historic caches on the matrix
    def flushNews(self):
        for eachQuote in self.list():
            eachQuote.flushNews()

    # flush everything
    def flushAll(self):
        self.flushTrades()
        self.flushNews()

    # (re-)build the matrix list using quotes (monitored or traded)
    def build(self):
        self.reinit()
        for eachQuote in quotes.list():
            if eachQuote.isMatrix():
                self.m_quotes[eachQuote.key()] = eachQuote
                debug('matrix:build: add %s',eachQuote.ticker())
            else:
                if eachQuote.key() in self.m_quotes:
                    del self.m_quotes[eachQuote.key()]
                    debug('matrix:build: remove %s',eachQuote.ticker())

    # update the matrix
    def update(self, fromdate=None, todate=None):
        for eachQuote in self.list():
            # update information
            if itrade_config.verbose:
                info(u'matrix::update: {} - {}'.format(eachQuote.key(), eachQuote.ticker()))
            eachQuote.update(fromdate,todate)

            # compute information
            if itrade_config.verbose:
                info(u'matrix::compute: {} - {}'.format(eachQuote.key(), eachQuote.ticker()))
            eachQuote.compute(todate)

    # add a quote in the matrix
    def addKey(self, i):
        q = quotes.lookupKey(i)
        # print(u'addKey: {} {}'.format(i, q))
        if q:
            debug(u'addKey: add %s', q.ticker())
            self.m_quotes[q.key()] = q
            debug(u'addKey: monitor {}'.format(i))
            q.monitorIt(True)
            return True
        else:
            return False

    # remove a quote in the matrix
    def removeKey(self, i):
        q = quotes.lookupKey(i)
        if q:
            debug('removeKey: add %s', q.ticker())
            del self.m_quotes[q.key()]
            debug(u'removeKey: un-monitor {}'.format(i))
            q.monitorIt(False)

# ============================================================================
# create_matrix
# ============================================================================

def create_matrix(fn='default', dp=None):
    m = TradingMatrix()
    m.load(fn)
    m.build()

    if dp:
        dp.setupCurrencies()
        dp.loginToServices()

    return m

# ============================================================================
# Test
# ============================================================================

def main():
    from itrade_portfolio import loadPortfolio

    setLevel(logging.INFO)
    itrade_config.app_header()

    print('--- load current portfolio ---')
    p = loadPortfolio()
    print(u'... {}:{}:{} '.format(p.filename(), p.name(), p.accountref()))

    print('--- build a matrix -----------')
    m = create_matrix(p.filename())

    print('--- liveupdate this matrix ---')
    m.update()

    print('--- save the matrix ----------')
    m.save(p.filename())

    eval = p.computeOperations()
    info(u'cash : {:f}'.format(p.nv_cash()))
    info(u'investment : {:f}'.format(p.nv_invest()))
#    info(u'evaluation : {:f}'.format(eval))


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
