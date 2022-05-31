#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_swx.py
#
# Description: List of quotes from swx.com : SWISS MARKET
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is Gilles Dumortier.
# New code for SWX is from Michel Legrand.
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
# 2007-04-14    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
import logging

# iTrade system
import itrade_config
from itrade_logging import setLevel, info
from itrade_defs import QList, QTag
from itrade_ext import gListSymbolRegistry
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_SWX()
# ============================================================================
def removeCarriage(s):
    if s[-1] == '\r':
        return s[:-1]
    else:
        return s


def splitLines(buf):
    lines = buf.split('\n')
    lines = filter(lambda x: x, lines)

    lines = [removeCarriage(l) for l in lines]
    return lines


def Import_ListOfQuotes_SWX(quotes, market='SWISS EXCHANGE', dlg=None, x=0):
    if itrade_config.verbose:
        print(u'Update {} list of symbols'.format(market))
    connection = ITradeConnection(cookies=None,
                               proxy=itrade_config.proxyHostname,
                               proxyAuth=itrade_config.proxyAuthentication,
                               connectionTimeout=itrade_config.connectionTimeout
                               )
    if market == 'SWISS EXCHANGE':
        url = 'https://www.six-swiss-exchange.com/shares/companies/download/issuers_all_fr.csv'
        try:
            data = connection.getDataFromUrl(url)
        except Exception:
            info(u'Import_ListOfQuotes_SWX_{}:unable to get file name :-('.format(market))
            return False
    else:
        return False

    # returns the data
    lines = splitLines(data)
    n = 0
    isin = ''
    for n, line in enumerate(lines[1:]):
        line = line.replace('!', ' ')
        line = line.replace(',', ' ')
        line = line.replace('à', 'a')
        line = line.replace('ä', 'a')
        line = line.replace('â', 'a')
        line = line.replace('ö', 'o')
        line = line.replace('ü', 'u')
        line = line.replace('é', 'e')
        line = line.replace('è', 'e')
        line = line.replace('+', ' ')

        data = line.split(';')  # csv line
        name = data[0].strip()
        ticker = data[1].strip()
        country = data[3].strip()
        currency = data[4].strip()
        exchange = data[5].strip()

        quotes.addQuote(isin=isin, name=name, ticker=ticker, market='SWISS EXCHANGE',
                    currency=currency, place=exchange, country=country)
    if itrade_config.verbose:
        print(u'Imported {:d} lines from {}'.format(n, market))

    return True

# ============================================================================
# Export me
# ============================================================================

gListSymbolRegistry.register('SWISS EXCHANGE', 'XSWX', QList.any, QTag.list, Import_ListOfQuotes_SWX)
gListSymbolRegistry.register('SWISS EXCHANGE', 'XVTX', QList.any, QTag.list, Import_ListOfQuotes_SWX)

# ============================================================================
# Test ME
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_SWX(quotes, 'XSWX')
    Import_ListOfQuotes_SWX(quotes, 'XVTX')
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
