#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_buenos-aires.py
#
# Description: List of quotes from
#   http://www.bolsar.com/NET/Research/Especies/Acciones.aspx
#
# Developed for iTrade code (http://itrade.sourceforge.net).
#
# Original template for "plug-in" to iTrade is from Gilles Dumortier.
# New code for BUE is from Michel Legrand.
#
# Portions created by the Initial Developer are Copyright (C) 2007-2008 the
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
# 2007-12-28    dgil  Wrote it from template
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from __future__ import absolute_import
import logging
import six.moves.urllib.request, six.moves.urllib.parse, six.moves.urllib.error
from contextlib import closing

# iTrade system
import itrade_config
from itrade_logging import setLevel, debug
from itrade_defs import QList, QTag
from itrade_ext import gListSymbolRegistry
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_BUE()
# ============================================================================


def Import_ListOfQuotes_BUE(quotes, market='BUENOS AIRES EXCHANGE', dlg=None, x=0):
    if itrade_config.verbose:
        print(u'Update {} list of symbols'.format(market))
    connection = ITradeConnection(proxy=itrade_config.proxyHostname,
                                  proxyAuth=itrade_config.proxyAuthentication)

    if market == 'BUENOS AIRES EXCHANGE':
        url = 'https://www.bolsar.com/NET/Research/Especies/Acciones.aspx'
    else:
        return False

    try:
        with closing(six.moves.urllib.request.urlopen(url)) as data:
            nlines = 0
            i = 0
            n = 0
            ch_ticker = '		<td Class="Oscuro"><A href="/NET/Research/Especies/Acciones.aspx?especie='
            ch_name = '		<td><A class="LinkAzul" href="../sociedades/fichaTecnica.aspx?emisor='

            #typical lines:
                    #<tr Class="Claro">
            #		<td Class="Oscuro"><A href="/NET/Research/Especies/Acciones.aspx?especie=4">ACIN</a></td>
            #		<td>Ordinarias Escriturales &quot;B&quot; (1 Voto)</td>
            #		<td>ARP008791179</td>
            #		<td><A class="LinkAzul" href="../sociedades/fichaTecnica.aspx?emisor=2">ACINDAR S.A.</a></td>

            for line in data:
                if ch_ticker in line:
                    i = 1
                    ticker = line[len(ch_ticker):]
                    ticker = ticker[ticker.index('">')+2 : ticker.index('</a></td>')]
                    #print ticker
                elif i == 1:
                    n= n + 1
                    if n == 2:
                        isin = line[line.index('<td>')+4:line.index('</td>')]
                        #print isin
                    if n == 3:
                        name = line[len(ch_name):]
                        name = name[name.index('">')+2:name.index('</a></td>')]

                        name = name.decode('utf-8').encode('cp1252')

                        name = name.replace(' S.A.','')
                        name = name.replace(' S. A.','')
                        name = name.replace(',','')

                        name = name.replace('�','i') #�
                        name = name.replace('�','i') #�
                        name = name.replace('�','o') #�
                        name = name.replace('�','a') #�
                        name = name.replace('�','n') #�

                        name = name.upper()
                        i = 0
                        n = 0

                        # ok to proceed
                        if isin != '':
                            quotes.addQuote(isin=isin, name=name,
                                ticker=ticker, market='BUENOS AIRES EXCHANGE', currency='ARS', place='BUE', country='AR')
                            nlines = nlines + 1
            if itrade_config.verbose:
                print(u'Imported {:d} lines from BUENOS AIRES EXCHANGE data.'.format(nlines))
    except Exception:
        debug('Import_ListOfQuotes_BUE unable to connect :-(')
        return False
    return True

# ============================================================================
# Export me
# ============================================================================

gListSymbolRegistry.register('BUENOS AIRES EXCHANGE', 'BUE', QList.any, QTag.list, Import_ListOfQuotes_BUE)

# ============================================================================
# Test ME
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_BUE(quotes)
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
