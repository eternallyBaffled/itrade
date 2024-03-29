#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_asx.py
#
# Description: List of quotes from http://www.asx.com.au
# ASX - Australian Stock Exchange
#
# Developed for iTrade code (http://itrade.sourceforge.net).
#
# Original template for "plug-in" to iTrade is	from Gilles Dumortier.
# New code for ASX is from Peter Mills and others.
#
# Portions created by the Initial Developer are Copyright (C) 2006-2008 the
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
# 2006-12-30    PeterMills  Initial version
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
# Import_ListOfQuotes_ASX()
#
# ============================================================================


def Import_ListOfQuotes_ASX(quotes, market='ASX', dlg=None, x=0):
    print(u'Update {} list of symbols'.format(market))
    connection = ITradeConnection(proxy=itrade_config.proxyHostname,
                                  proxyAuth=itrade_config.proxyAuthentication,
                                  connectionTimeout=itrade_config.connectionTimeout
                                 )

    if market == 'ASX':
        url = "https://www.asx.com.au/asx/research/ASXListedCompanies.csv"
        n = 0
    else:
        return False

    def splitLines(buf):
        lines = buf.split('\n')
        lines = [x for x in lines if x]

        def removeCarriage(s):
            if s[-1] == '\r':
                return s[:-1]
            else:
                return s
        lines = [removeCarriage(l) for l in lines]
        return lines
    try:
        data = connection.getDataFromUrl(url)
    except Exception:
        debug('Import_ListOfQuotes_ASX:unable to connect :-(')
        return False

    # returns the data
    lines = splitLines(data)
    isin = ''
    for line in lines[3:]:
        line = line.replace('"', '')
        data = line.split(',')
        name = data[0]
        ticker = data[1]
        quotes.addQuote(isin=isin, name=name,
                ticker=ticker, market='ASX', currency='AUD', place='SYD', country='AU')

        n = n + 1

    if itrade_config.verbose:
        print(u'Imported {:d} lines from {} data.'.format(n, market))

    return True
# ============================================================================
# Export me
# ============================================================================

gListSymbolRegistry.register('ASX','SYD',QList.any,QTag.list,Import_ListOfQuotes_ASX)

# ============================================================================
# Test ME
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_ASX(quotes)

    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
