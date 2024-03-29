#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_shenzhen.py
#
# Description: List of quotes from http://www.szse.cn/main/en/
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# Original template for "plug-in" to iTrade is from Gilles Dumortier.
# New code for SHE is from Michel Legrand.
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

# iTrade system
import itrade_config
from itrade_logging import setLevel, info
from itrade_defs import QList, QTag
from itrade_ext import gListSymbolRegistry
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_SHE()
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


def Import_ListOfQuotes_SHE(quotes, market='SHENZHEN EXCHANGE', dlg=None, x=0):
    if itrade_config.verbose:
        print(u'Update {} list of symbols'.format(market))
    connection = ITradeConnection(proxy=itrade_config.proxyHostname,
                                  proxyAuth=itrade_config.proxyAuthentication)

    if market == 'SHENZHEN EXCHANGE':
        url = 'https://www.szse.cn/szseWeb/FrontController.szse?ACTIONID=8&CATALOGID=1693&TABKEY=tab1&ENCODE=1'
    else:
        return False

    info(u'Import_ListOfQuotes_SHE_%s:connect to {}'.format(market, url))

    try:
        data = connection.getDataFromUrl(url)
    except Exception:
        info(u'Import_ListOfQuotes_SHE_{}:unable to connect :-('.format(market))
        return False

    data = data.replace("style='mso-number-format:\@' align='center' >", '\n')

    # returns the data
    lines = splitLines(data)

    currency = 'CNY'
    nlines = 0
    #print u'Import_ListOfQuotes_SHE_{}:'.format(market), 'book', book, 'sheet', sh, 'nrows=', sh.nrows

    for line in lines[2:]:
        if line.find("</td><td  class='cls-data-td'  align='left' >"):
            ticker = line[:line.index('<')]

            name = line[51:line.index('<', 51)]
            name = name.replace(',', ' ')

            if name[-2:] == '-B':
                currency = 'HKD'
                name = name[:-2]
            else:
                currency = 'CNY'

            if ticker == '000517':
                name = 'RONGAN PROPERTY CO'
            if ticker == '000529':
                name = 'GUANGDONG MEIYA'
            if ticker == '000650':
                name = 'RHENE PHARMACY CO'
            quotes.addQuote(isin='', name=name, ticker=ticker, market='SHENZHEN EXCHANGE', currency=currency, place='SHE', country='CN')
            nlines = nlines + 1

    if itrade_config.verbose:
        print(u'Imported {:d} lines from {} data.'.format(nlines, market))

    return True

# ============================================================================
# Export me
# ============================================================================

gListSymbolRegistry.register('SHENZHEN EXCHANGE', 'SHE', QList.any, QTag.list, Import_ListOfQuotes_SHE)

# ============================================================================
# Test ME
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_SHE(quotes, 'SHE')

    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
