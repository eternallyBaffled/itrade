#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_otcbb.py
#
# Description: List of quotes from otcbb.com
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

# iTrade system
import itrade_config
from itrade_logging import setLevel, debug
from itrade_defs import QList, QTag
from itrade_ext import gListSymbolRegistry
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_OTCBB()
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


def Import_ListOfQuotes_OTCBB(quotes, market='OTCBB', dlg=None, x=0):
    if itrade_config.verbose:
        print(u'Update {} list of symbols'.format(market))
    connection = ITradeConnection(proxy=itrade_config.proxyHostname,
                                  proxyAuth=itrade_config.proxyAuthentication,
                                  connectionTimeout=itrade_config.connectionTimeout
                                 )
    if market == 'OTCBB':
        url = 'https://www.otcbb.com/dynamic/tradingdata/download/allotcbb.txt'
    else:
        return False

    try:
        data=connection.getDataFromUrl(url)
    except Exception:
        debug('Import_ListOfQuotes_OTCBB:unable to connect :-(')
        return False

    # returns the data
    lines = splitLines(data)
    count = 0
    isin = ''
    for line in lines[1:]:
        if '|' in line:
            data = line.split('|')
            if data[3] == 'ACTIVE':
                count = count + 1
                name = data[2]
                name = name.strip()
                name = name.replace(',', '')
                ticker = data[0]
                quotes.addQuote(isin=isin, name=name, ticker=ticker, market='OTCBB', currency='USD', place='NYC', country='US')
    if itrade_config.verbose:
        print(u'Imported {:d} lines from OTCBB data.'.format(count))

    return True

# ============================================================================
# Export me
# ============================================================================

gListSymbolRegistry.register('OTCBB', 'NYC', QList.any, QTag.list, Import_ListOfQuotes_OTCBB)

# ============================================================================
# Test ME
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_OTCBB(quotes)
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
