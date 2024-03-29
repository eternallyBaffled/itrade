#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_milan.py
#
# Description: List of quotes from http://www.borsaitaliana.it/
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is Gilles Dumortier.
# New code for Milan is from Michel Legrand.

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
from itrade_logging import setLevel, info
from itrade_defs import QList, QTag
from itrade_ext import gListSymbolRegistry
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_MIL()
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


def Import_ListOfQuotes_MIL(quotes, market='MILAN EXCHANGE', dlg=None, x=0):
    if itrade_config.verbose:
        print(u'Update {} list of symbols'.format(market))
    connection = ITradeConnection(proxy=itrade_config.proxyHostname,
                                  proxyAuth=itrade_config.proxyAuthentication,
                                  connectionTimeout=itrade_config.connectionTimeout
                                 )

    if market == 'MILAN EXCHANGE':
        url = u"https://www.borsaitaliana.it/bitApp/listino?main_list=1&sub_list=1&service=Results&search=nome&lang=it&target=null&nome="
    else:
        return False

    info(u'Import_ListOfQuotes_{}:connect to {}'.format(market, url))

    req = six.moves.urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.5) Gecko/20041202 Firefox/1.0')

    try:
        with closing(six.moves.urllib.request.urlopen(req)) as f:
            data = f.read()
    except Exception:
        info(u'Import_ListOfQuotes_{}:unable to connect :-('.format(market))
        return False

    # returns the data
    lines = splitLines(data)

    n = 0

    for line in lines:
        if line.find('a href="/bitApp/listino?target=null&lang=it&service=Detail&from=search&main_list=1&') != -1:
            finalurl = 'https://www.borsaitaliana.it'+line[line.index('/'):line.index('" class="table">')]

            req = six.moves.urllib.request.Request(finalurl)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.5) Gecko/20041202 Firefox/1.0')
            try:
                with closing(six.moves.urllib.request.urlopen(req)) as f:
                    datas = f.read()
            except Exception:
                info(u'Import_ListOfQuotes_ISIN_TICKER_NAME_{}:unable to connect :-('.format(market))
                return False

            finaldatas = splitLines(datas)
            for nline in finaldatas:
                if nline.find('<b>Denominazione<b>') != -1:
                    name = nline[nline.index('"right">')+8:nline.index('</td></tr>')]
                if nline.find('<b>Codice Isin<b>') != -1:
                    isin = nline[nline.index('"right">')+8:nline.index('</td></tr>')]
                if nline.find('<b>Codice Alfanumerico<b>') != -1:
                    ticker = nline[nline.index('"right">')+8:nline.index('</td></tr>')]

                    n = n + 1
                    dlg.Update(x, u'BORSA ITALIANA : {:d} /~350'.format(n))

                    quotes.addQuote(isin=isin, name=name,
                        ticker=ticker, market=market,
                        currency='EUR', place='MIL', country='IT')
    if itrade_config.verbose:
        print(u'Imported {:d} lines from {} data.'.format(n, market))

    return True

# ============================================================================
# Export me
# ============================================================================
gListSymbolRegistry.register('MILAN EXCHANGE', 'MIL', QList.any, QTag.list, Import_ListOfQuotes_MIL)
# ============================================================================
# Test ME
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes
    Import_ListOfQuotes_MIL(quotes)
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
