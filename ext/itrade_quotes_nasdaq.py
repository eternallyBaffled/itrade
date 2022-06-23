#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_nasdaq.py
#
# Description: List of quotes from http://www.nasdaq.com : NYSE, NASDAQ, AMEX
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
# 2005-06-12    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from __future__ import absolute_import
import logging
import six.moves.urllib.request, six.moves.urllib.parse, six.moves.urllib.error
import csv

# iTrade system
import itrade_config
from itrade_logging import setLevel, debug
from itrade_defs import QList, QTag
from itrade_ext import gListSymbolRegistry
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_NASDAQ()
# ============================================================================


def Import_ListOfQuotes_NASDAQ(quotes, market='NASDAQ', dlg=None, x=0):
    if itrade_config.verbose:
        print(u'Update {} list of symbols'.format(market))
    connection = ITradeConnection(cookies=None,
                               proxy=itrade_config.proxyHostname,
                               proxyAuth=itrade_config.proxyAuthentication,
                               connectionTimeout=itrade_config.connectionTimeout
                               )
    if market == 'NYSE':
        url = 'https://www.nasdaq.com/screening/companies-by-industry.aspx?&exchange=nyse&render=download'
    elif market == 'NASDAQ':
        url = 'https://www.nasdaq.com/screening/companies-by-industry.aspx?&exchange=nasdaq&render=download'
    elif market == 'AMEX':
        url = 'https://www.nasdaq.com/screening/companies-by-name.aspx?&exchange=amex&render=download'
    else:
        return False

    try:
        data = six.moves.urllib.request.urlopen(url)
        #data=connection.getDataFromUrl(url)
    except Exception:
        debug('Import_ListOfQuotes_NASDAQ:unable to connect :-(')
        return False

    reader = csv.reader(data, delimiter=',')
    count = -1
    isin = ''

    # returns the data

    for line in reader:
        count = count+1
        if count > 0:
            name = line[1]
            name = name.strip()
            name =name.replace(',','').replace('&quot;','"').replace('&#39;',"'")
            ticker = line[0]
            ticker = ticker.strip()
            ticker = ticker.replace('/','-').replace('^','-P')
            quotes.addQuote(isin=isin, name=name, ticker=ticker, market=market, currency='USD', place='NYC', country='US')
    if itrade_config.verbose:
        print(u'Imported {:d} lines from NASDAQ data.'.format(count))

    return True

# ============================================================================
# Export me
# ============================================================================
gListSymbolRegistry.register('NASDAQ', 'NYC', QList.any, QTag.list, Import_ListOfQuotes_NASDAQ)
gListSymbolRegistry.register('AMEX', 'NYC', QList.any, QTag.list, Import_ListOfQuotes_NASDAQ)
gListSymbolRegistry.register('NYSE', 'NYC', QList.any, QTag.list, Import_ListOfQuotes_NASDAQ)

# ============================================================================
# Test ME
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_NASDAQ(quotes, 'NASDAQ')
    Import_ListOfQuotes_NASDAQ(quotes, 'NYSE')
    Import_ListOfQuotes_NASDAQ(quotes, 'AMEX')
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
