#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_lse.py
#
# Description: List of quotes from http://www.londonstockexchange.com/en-gb/products/membershiptrading/tradingservices/: LSE MARKETS (SETS, SETSqx, SEAQ)
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is Gilles Dumortier.
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
# 2007-05-15    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from __future__ import absolute_import
import logging
import six.moves.urllib.request, six.moves.urllib.error, six.moves.urllib.parse
from contextlib import closing

# iTrade system
import itrade_config
import itrade_excel
from itrade_logging import setLevel, info
from itrade_defs import QList, QTag
from itrade_ext import gListSymbolRegistry
from itrade_connection import ITradeConnection
from six.moves import range

# ============================================================================
# Import_ListOfQuotes_LSE()
# ============================================================================
def removeCarriage(s):
    if s[-1] == '\r':
        return s[:-1]
    else:
        return s


def splitLines(buf):
    lines = buf.split('\n')
    lines = [x for x in lines if x]

    lines = [removeCarriage(l) for l in lines]
    return lines


def Import_ListOfQuotes_LSE(quotes, market='LSE SETS', dlg=None, x=0):
    if itrade_config.verbose:
        print(u'Update {} list of symbols'.format(market))
    connection = ITradeConnection(cookies=None,
                               proxy=itrade_config.proxyHostname,
                               proxyAuth=itrade_config.proxyAuthentication,
                               connectionTimeout=itrade_config.connectionTimeout
                               )

    import xlrd

    if market == 'LSE SETS':
        url = 'https://www.londonstockexchange.com/products-and-services/trading-services/sets/list-sets.xls'
    elif market == 'LSE SETSqx':
        url = 'https://www.londonstockexchange.com/products-and-services/trading-services/setsqx/ccp-securities.xls'
    elif market == 'LSE SEAQ':
        url = 'https://www.londonstockexchange.com/products-and-services/trading-services/seaq/list-seaq.xls'
    else:
        return False

    info(u'Import_ListOfQuotes_LSE_{}:connect to {}'.format(market, url))
    req = six.moves.urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.5) Gecko/20041202 Firefox/1.0')

    try:
        with closing(six.moves.urllib.request.urlopen(req)) as f:
            data = f.read()
    except Exception:
        info(u'Import_ListOfQuotes_LSE_{}:unable to connect :-('.format(market))
        return False

    # returns the data
    book = itrade_excel.open_excel(filename=None, content=data)
    sh = book.sheet_by_index(0)
    n = 0
    indice = {}

    #print u'Import_ListOfQuotes_LSE_{}:'.format(market), 'book', book, 'sheet', sh, 'nrows=', sh.nrows

    for line in range(sh.nrows):
        if sh.cell_type(line, 1) != xlrd.XL_CELL_EMPTY:
            if n == 0:
                for i in range(sh.ncols):
                    val = sh.cell_value(line,i)
                    indice[val] = i

                    # be sure we have detected the title
                    if val == 'ISIN': n = n + 1

                if n == 1:
                    #if itrade_config.verbose: print 'Indice:',indice

                    iISIN = indice['ISIN']
                    iName = indice['Short Name']
                    iCurrency = indice['Currency']
                    iCountry = indice['Country of Register']
                    iTicker = indice['Mnemonic']
            else:
                ticker = sh.cell_value(line, iTicker)
                if type(ticker) == float: ticker = u'{}'.format(ticker)
                if ticker[-1:] == '.':
                    ticker = ticker[:-1]

                name = sh.cell_value(line, iName).replace(',', ' ')
                name = name.encode('cp1252')
                name = name.replace('£',' ')
                name = name.replace('  ','')
                quotes.addQuote(isin=sh.cell_value(line, iISIN), name=name,
                    ticker=ticker, market=market,
                    currency=sh.cell_value(line,iCurrency), place='LON',
                    country=sh.cell_value(line,iCountry))
                n = n + 1
    if itrade_config.verbose:
        print(u'Imported {:d}/{:d} lines from {}'.format(n, sh.nrows, market))

    return True

# ============================================================================
# Export me
# ============================================================================

if itrade_excel.canReadExcel:
    gListSymbolRegistry.register('LSE SETS','LON',QList.any,QTag.list,Import_ListOfQuotes_LSE)
    gListSymbolRegistry.register('LSE SETSqx','LON',QList.any,QTag.list,Import_ListOfQuotes_LSE)
    gListSymbolRegistry.register('LSE SEAQ','LON',QList.any,QTag.list,Import_ListOfQuotes_LSE)

# ============================================================================
# Test ME
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    if itrade_excel.canReadExcel:
        Import_ListOfQuotes_LSE(quotes,'LSE SETS')
        Import_ListOfQuotes_LSE(quotes,'LSE SETSqx')
        Import_ListOfQuotes_LSE(quotes,'LSE SEAQ')

        quotes.saveListOfQuotes()
    else:
        print('XLRD package not installed :-(')

# ============================================================================
# That's all folks !
# ============================================================================
