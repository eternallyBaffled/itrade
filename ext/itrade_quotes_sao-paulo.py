#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_sao-paulo.py
#
# Description: List of quotes from http://www.bovespa.com.br/
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# Original template for "plug-in" to iTrade is from Gilles Dumortier.
# New code for BOVESPA is from Michel Legrand.

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
import logging
import urllib
import zipfile
import os

# iTrade system
import itrade_config
from itrade_logging import setLevel, debug, info
from itrade_defs import QList, QTag
from itrade_ext import gListSymbolRegistry
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_SAO()
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


def Import_ListOfQuotes_SAO(quotes, market='SAO PAULO EXCHANGE', dlg=None, x=0):
    if itrade_config.verbose:
        print(u'Update {} list of symbols'.format(market))
    connection = ITradeConnection(cookies=None,
                                proxy=itrade_config.proxyHostname,
                                proxyAuth=itrade_config.proxyAuthentication)

    if market == 'SAO PAULO EXCHANGE':
        url ='https://www.bmfbovespa.com.br/suplemento/ExecutaAcaoDownload.asp?arquivo=Securities_Traded.zip'
        currency = 'BRL'
        place = 'SAO'
        country = 'BR'
    else:
        return False

    info(u'Import_ListOfQuotes_BOVESPA_{}:connect to {}'.format(market, url))

    try:
        urllib.urlretrieve(url, 'Securities_Traded.zip')
        zfile = zipfile.ZipFile('Securities_Traded.zip')
        data = zfile.read('SECURITIES_TRADED.TXT')
    except Exception:
        debug('Import_ListOfQuotes_BOVESPA:unable to connect :-(')
        return False

    # returns the data

    lines = splitLines(data)

    n = 0

    for line in lines:
        record_type = line[0:2]
        if record_type == '01':
            name = line[6:66]
            short_name = line[66:78]
            short_name = short_name.strip()

        elif record_type == '02':
            ticker = line[2:14]
            ticker = ticker.strip()
            bdi_code = line[18:21]
            isin = line[81:93]
            market_code = line[108:111]
            specific_code = line[133:136]
            specific_code = specific_code.strip()
            if bdi_code == '002':
                n = n + 1
                quotes.addQuote(isin=isin, name=short_name+'-'+specific_code, ticker=ticker, market=market, currency=currency, place=place, country=country)
    if itrade_config.verbose:
        print(u'Imported {:d} lines from {} data.'.format(n, market))

    zfile.close()
    os.remove('Securities_Traded.zip')

    return True

# ============================================================================
# Export me
# ============================================================================

gListSymbolRegistry.register('SAO PAULO EXCHANGE', 'SAO', QList.any, QTag.list, Import_ListOfQuotes_SAO)

# ============================================================================
# Test ME
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_SAO(quotes, 'SAO PAULO EXCHANGE')
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
