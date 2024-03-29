#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_xetra.py
#
# Description: List of quotes from deutsche-boerse.com: XETRA
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# Original template for "plug-in" to iTrade is from Gilles Dumortier.
# New code for XETRA is from Michel Legrand.
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
# 2007-12-18    ml    Wrote it from template
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
# Import_ListOfQuotes_Xetra()
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


def Import_ListOfQuotes_Xetra(quotes, market='FRANKFURT EXCHANGE', dlg=None, x=0):
    if itrade_config.verbose:
        print(u'Update {} list of symbols'.format(market))
    connection = ITradeConnection(proxy=itrade_config.proxyHostname,
                                  proxyAuth=itrade_config.proxyAuthentication,
                                  connectionTimeout=itrade_config.connectionTimeout
                                 )

    if market == 'FRANKFURT EXCHANGE':
        url = 'https://deutsche-boerse.com/dbag/dispatch/en/xetraCSV/gdb_navigation/trading/20_tradable_instruments/900_tradable_instruments/100_xetra'
    else:
        return False

    try:
        data = connection.getDataFromUrl(url)
    except Exception:
        debug('Import_ListOfQuotes_Deutsche Borse AG :unable to connect :-(')
        return False

    # returns the data
    lines = splitLines(data)
    n = 0
    for line in lines[6:]:
        data = line.split(';')  # ; delimited

        if len(data) > 5:
            if data[8] == 'EQUITIES FFM2':
                if data[2][:2] == 'DE':
                    name = data[1].replace(',', '').replace('  ', '').replace (' -', '-').replace ('. ', '.').replace(' + ', '&').replace('+', '&')
                    quotes.addQuote(isin=data[2], name=name, ticker=data[5], market='FRANKFURT EXCHANGE', currency=data[73], place='FRA', country='DE')
                    n = n + 1
    if itrade_config.verbose:
        print(u'Imported {:d}/{:d} lines from {}'.format(n, len(lines), market))

    return True

# ============================================================================
# Export me
# ============================================================================

gListSymbolRegistry.register('FRANKFURT EXCHANGE', 'FRA', QList.any, QTag.list, Import_ListOfQuotes_Xetra)

# ============================================================================
# Test ME
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_Xetra(quotes, 'FRA')
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
