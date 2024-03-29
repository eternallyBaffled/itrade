#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_euronext.py
#
# Description: List of quotes from euronext.com : EURONEXT, ALTERNEXT and
# MARCHE LIBRE (PARIS,AMSTERDAM,BRUXELLES,LISBONNE)
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
# 2005-06-11    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from __future__ import absolute_import
import logging
import six.moves.http_client
import six.moves.urllib.request, six.moves.urllib.error, six.moves.urllib.parse
import six.moves.http_cookiejar

# iTrade system
import itrade_config
from itrade_logging import setLevel, debug
from itrade_defs import QList, QTag
from itrade_ext import gListSymbolRegistry
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_Euronext()
#
# ============================================================================

def Import_ListOfQuotes_Euronext(quotes, market='EURONEXT', dlg=None, x=0):
    if itrade_config.verbose:
        print('Update {} list of symbols'.format(market))
    connection = ITradeConnection(proxy=itrade_config.proxyHostname,
                                  proxyAuth=itrade_config.proxyAuthentication,
                                  connectionTimeout=max(45, itrade_config.connectionTimeout)
                               )

    nyse_euronext_market = {
        #'Easynext Brussels': ('EURONEXT','BRU','BE'),
        #'Easynext Lisbon': ('EURONEXT','LIS','PT'),
        'Marché Libre Brussels': ('BRUXELLES MARCHE LIBRE','BRU','BE'),
        'Marché Libre Paris': ('PARIS MARCHE LIBRE','PAR','FR'),
        'NYSE Alternext Amsterdam': ('ALTERNEXT','AMS','NL'),
        'NYSE Alternext Brussels': ('ALTERNEXT','BRU','BE'),
        'NYSE Alternext Brussels,Paris': ('ALTERNEXT','BRU','BE'),
        'NYSE Alternext Lisbon': ('ALTERNEXT','LIS','PT'),
        'NYSE Alternext Paris': ('ALTERNEXT','PAR','FR'),
        'NYSE Alternext Paris,Brussels': ('ALTERNEXT','PAR','BE'),
        'NYSE Euronext Amsterdam': ('EURONEXT','AMS','NL'),
        'NYSE Euronext Amsterdam,Brussels': ('EURONEXT','AMS','NL'),
        'NYSE Euronext Amsterdam,Paris': ('EURONEXT','AMS','NL'),
        'NYSE Euronext Brussels': ('EURONEXT','BRU','BE'),
        'NYSE Euronext Brussels,Amsterdam': ('EURONEXT','BRU','BE'),
        'NYSE Euronext Brussels,Paris': ('EURONEXT','BRU','BE'),
        'NYSE Euronext Lisbon': ('EURONEXT','LIS','PT'),
        'NYSE Euronext Paris': ('EURONEXT','PAR','FR'),
        'NYSE Euronext Paris,Amsterdam': ('EURONEXT','PAR','FR'),
        'NYSE Euronext Paris,Amsterdam,Brussels': ('EURONEXT','PAR','FR'),
        'NYSE Euronext Paris,Brussels': ('EURONEXT','PAR','FR'),
        'NYSE Euronext Paris,London': ('EURONEXT','PAR','FR'),
        }

    if market == 'EURONEXT' or market == 'ALTERNEXT' or market == 'PARIS MARCHE LIBRE' or market == 'BRUXELLES MARCHE LIBRE':
        url = 'https://europeanequities.nyx.com/fr/popup/data/download?ml=nyx_pd_stocks&cmd=default&formKey=nyx_pd_filter_values%3Aa4eb918a59a5b507707ea20eb38f530f'
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
        host = "europeanequities.nyx.com"
        cj = None
        urlopen = six.moves.urllib.request.urlopen
        Request = six.moves.urllib.request.Request
        cj = six.moves.http_cookiejar.LWPCookieJar()
        opener = six.moves.urllib.request.build_opener(six.moves.urllib.request.HTTPCookieProcessor(cj))
        six.moves.urllib.request.install_opener(opener)
        req = Request(url)
        handle = urlopen(req)
        cj = str(cj)
        cookie = cj[cj.find('ZDEDebuggerPresent='):cj.find(' for europeanequities.nyx.com/>')]
    except Exception:
        debug('Import_ListOfQuotes_Euronext:unable to connect :-(')
        return False

    # init params and headers
    params = "format=2&layout=2&decimal_separator=1&date_format=1&op=Go&form_id=nyx_download_form"

    headers = { "Accept": "text/html,application/xhtml+xml,application/xml",
                    "accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
                    "Accept-Encoding": "gzip,deflate,sdch",
                    "Accept-Language": "fr-FR,fr;q=0.8,en-US;q=0.6,en;q=0.4",
                    "Cache-Control": "max-age=0",
                    "Connection": "keep-alive",
                    "Content-Length": len(params),
                    "Content-Type": "application/x-www-form-urlencoded",
                    "cookie": cookie,
                    "Host": "europeanequities.nyx.com",
                    "Origin": "https://europeanequities.nyx.com",
                    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
                    "Referer": "https://europeanequities.nyx.com/fr/popup/data/download?ml=nyx_pd_stocks&cmd=default&formKey=nyx_pd_filter_values%3Aa4eb918a59a5b507707ea20eb38f530f",
                    }

    try:
        # POST the request
        conn = six.moves.http_client.HTTPConnection(host, 80)
        conn.request("POST", url, params, headers)
        response = conn.getresponse()
        data = response.read()
    except Exception:
        debug('Import_ListOfQuotes_Euronext:unable to connect :-(')
        return False

    # returns the data

    lines = splitLines(data)

    count = 0
    for line in lines[5:]:
        data = line.replace('"', '')
        data = data.split(';')
        nysemarket = data[3]

        if nysemarket in nyse_euronext_market:
            if nyse_euronext_market[nysemarket][0] == market:
                name = data[0]
                isin = data[1]
                ticker = data[2]
                currency = data[4]
                place = nyse_euronext_market[nysemarket][1]

                count = count + 1
                quotes.addQuote(isin=isin, name=name, ticker=ticker, market=market, currency=currency, place=place, country=None)
        else:
            pass

    if itrade_config.verbose:
        print('Imported {:d}/{:d} lines from {}'.format(count, len(lines), market))

    return True

# ============================================================================
# Export me
# ============================================================================

gListSymbolRegistry.register('EURONEXT', 'PAR', QList.any, QTag.list, Import_ListOfQuotes_Euronext)
gListSymbolRegistry.register('EURONEXT', 'AMS', QList.any, QTag.list, Import_ListOfQuotes_Euronext)
gListSymbolRegistry.register('EURONEXT', 'BRU', QList.any, QTag.list, Import_ListOfQuotes_Euronext)
gListSymbolRegistry.register('EURONEXT', 'LIS', QList.any, QTag.list, Import_ListOfQuotes_Euronext)

gListSymbolRegistry.register('ALTERNEXT', 'PAR', QList.any, QTag.list, Import_ListOfQuotes_Euronext)
gListSymbolRegistry.register('ALTERNEXT', 'AMS', QList.any, QTag.list, Import_ListOfQuotes_Euronext)
gListSymbolRegistry.register('ALTERNEXT', 'BRU', QList.any, QTag.list, Import_ListOfQuotes_Euronext)
gListSymbolRegistry.register('ALTERNEXT', 'LIS', QList.any, QTag.list, Import_ListOfQuotes_Euronext)

gListSymbolRegistry.register('PARIS MARCHE LIBRE', 'PAR', QList.any, QTag.list, Import_ListOfQuotes_Euronext)
gListSymbolRegistry.register('BRUXELLES MARCHE LIBRE', 'BRU', QList.any, QTag.list, Import_ListOfQuotes_Euronext)

# ============================================================================
# Test ME
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_Euronext(quotes)
    Import_ListOfQuotes_Euronext(quotes, 'ALTERNEXT')
    Import_ListOfQuotes_Euronext(quotes, 'PARIS MARCHE LIBRE')
    Import_ListOfQuotes_Euronext(quotes, 'BRUXELLES MARCHE LIBRE')
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
