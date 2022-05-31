#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_madrid.py
#
# Description: List of quotes from http://www.bolsamadrid.es
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is Gilles Dumortier.
# New code for Bolsa de Madrid is from Michel Legrand.

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
import os
import logging
import urllib
import pyPdf

# iTrade system
import itrade_config
from itrade_logging import setLevel, info
from itrade_defs import QList, QTag
from itrade_ext import gListSymbolRegistry
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_MADRID()
# ============================================================================

def Import_ListOfQuotes_MADRID(quotes, market='MADRID EXCHANGE', dlg=None, x=0):
    if itrade_config.verbose:
        print(u'Update {} list of symbols'.format(market))
    connection = ITradeConnection(cookies=None,
                               proxy=itrade_config.proxyHostname,
                               proxyAuth=itrade_config.proxyAuthentication,
                               connectionTimeout=itrade_config.connectionTimeout
                               )

    if market == 'MADRID EXCHANGE':
        url = 'https://www.bolsamadrid.es/docs/SBolsas/InformesSB/listadodevalores.pdf'
    else:
        return False

    def splitLines(buf):
        lines = buf.split(cr)
        lines = filter(lambda x: x, lines)
        def removeCarriage(s):
            if s[-1] == '\r':
                return s[:-1]
            else:
                return s
        lines = [removeCarriage(l) for l in lines]
        return lines

    info(u'Import_ListOfQuotes_MADRID_{}:connect to {}'.format(market, url))

    f = 'listadodevalores.pdf'
    n = 0

    try:
        urllib.urlretrieve(url, f)
    except Exception:
        info(u'Import_ListOfQuotes_MADRID_{}:unable to connect :-('.format(market))
        return False

    # returns the data

    source = open(f, 'rb')
    pdf = pyPdf.PdfFileReader(source)

    for page in pdf.pages:
        data = page.extractText()
        data = data[data.find('DecimalsFixing')+15:]
        cr = data[:8]
        lines = splitLines(data)

        for line in lines:
            if 'Sociedad de Bolsas' in line:
                pass
            else:
                line = line[:line.find('<')]
                line = line[:line.find('0,0')]
                ticker = line[:8].strip()
                if 'BBVA' in ticker and len(ticker) == 5:
                    pass
                else:
                    ticker = ticker.replace('.', '-')

                isin = line[8:21]
                name = line[21:].strip()
                if not 'LYX' in name and not 'TRACKERS' in name:
                    name = name.encode('cp1252')
                    name = name.replace(',', ' ')
                    name = name.replace('Ó', 'O')
                    name = name.replace('Ñ', 'N')
                    name = name.replace('Ç', 'C')

                    #print isin,name,ticker,market

                    quotes.addQuote(isin=isin, name=name,
                                ticker=ticker, market=market,
                                currency='EUR', place='MAD', country='ES')
                    n = n + 1
    if itrade_config.verbose:
        print(u'Imported {:d} lines from {}'.format(n, market))
    source.close()
    os.remove(f)
    return True

# ============================================================================
# Export me
# ============================================================================

gListSymbolRegistry.register('MADRID EXCHANGE', 'MAD', QList.any, QTag.list, Import_ListOfQuotes_MADRID)

# ============================================================================
# Test ME
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_MADRID(quotes, 'MADRID EXCHANGE')

    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
