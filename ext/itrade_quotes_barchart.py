#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_barchart.py
#
# Description: List of quotes from barchart.com :  NYSE, NASDAQ, AMEX, OTCBB,
# TORONTO (TSE and TSX)
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
# 2006-10-25    dgil  Wrote it from scratch
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
from itrade_logging import setLevel
from itrade_defs import QList, QTag
from itrade_ext import gListSymbolRegistry
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_BARCHART()
# ============================================================================


def Import_ListOfQuotes_BARCHART(quotes, market='TOTRONTO EXCHANGE', dlg=None, x=0):
    if itrade_config.verbose:
        print(u'Update {} list of symbols'.format(market))
    connection = ITradeConnection(proxy=itrade_config.proxyHostname,
                                  proxyAuth=itrade_config.proxyAuthentication,
                                  connectionTimeout=itrade_config.connectionTimeout
                                 )

    if market == 'TORONTO EXCHANGE' or market == 'TORONTO VENTURE':
        url = u'https://www.barchart.com/lookup.php?field=name&string={}&search=begins&type[]=CAN&_dtp1=0'

        m_currency = 'CAD'
        m_place = 'TOR'
        m_country = 'CA'
        if market == 'TORONTO EXCHANGE':
            exchange = 'TSX<'
        else:
            exchange = 'TSX-V<'
    else:
        return False

    def splitLines(buf):
        lines = buf.split('<tr id="dt1_')
        lines = [x for x in lines if x]
        def removeCarriage(s):
            if s[-1] == '\r':
                return s[:-1]
            else:
                return s
        lines = [removeCarriage(l) for l in lines]
        return lines

    def import_letter(letter, dlg, x):
        if dlg:
            dlg.Update(x, u"{}:'{}'".format(market, letter))

        try:
            req = six.moves.urllib.request.Request(url=url.format(letter))
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.5) Gecko/20041202 Firefox/1.0')

            with closing(six.moves.urllib.request.urlopen(req)) as f:
                data = f.read()
        except Exception:
            print('Import_ListOfQuotes_BARCHART:unable to connect to', url.format(letter))
            return False

            # returns the data

        lines = splitLines(data)

        count = 0

        for line in lines:
            if exchange in line and 'nowrap' in line:
                ticker = line[:line.index('" class="">')]
                if not '-DB' in ticker:  # ignore DEBit
                    ticker = ticker[:-3]

                    name = line[line.index('/quotes/'):line.index('</a>')]
                    name = name[name.index('">')+2:]


                    quotes.addQuote(isin='', name=name, ticker=ticker, market=market, currency=m_currency, place=m_place, country=m_country)
                    count = count + 1

        if itrade_config.verbose:
            print(u'Imported {:d} lines from BARCHART(letter={})'.format(count, letter))

    #import_letter('1',dlg,x-1)
    #import_letter('2',dlg,x)
    #import_letter('3',dlg,x-1)
    #import_letter('4',dlg,x)
    #import_letter('5',dlg,x-1)
    #import_letter('6',dlg,x)
    #import_letter('7',dlg,x-1)
    #import_letter('8',dlg,x)
    #mport_letter('9',dlg,x-1)
    import_letter('A',dlg,x)
    import_letter('B',dlg,x-1)
    import_letter('C',dlg,x)
    import_letter('D',dlg,x-1)
    import_letter('E',dlg,x)
    import_letter('F',dlg,x-1)
    import_letter('G',dlg,x)
    import_letter('H',dlg,x-1)
    import_letter('I',dlg,x)
    import_letter('J',dlg,x-1)
    import_letter('K',dlg,x)
    import_letter('L',dlg,x-1)
    import_letter('M',dlg,x)
    import_letter('N',dlg,x-1)
    import_letter('O',dlg,x)
    import_letter('P',dlg,x-1)
    import_letter('Q',dlg,x)
    import_letter('R',dlg,x-1)
    import_letter('S',dlg,x)
    import_letter('T',dlg,x-1)
    import_letter('U',dlg,x)
    import_letter('V',dlg,x-1)
    import_letter('W',dlg,x)
    import_letter('X',dlg,x-1)
    import_letter('Y',dlg,x)
    import_letter('Z',dlg,x-1)

    return True

# ============================================================================
# Export me
# ============================================================================

gListSymbolRegistry.register('TORONTO EXCHANGE','TOR',QList.any,QTag.list,Import_ListOfQuotes_BARCHART)
gListSymbolRegistry.register('TORONTO VENTURE','TOR',QList.any,QTag.list,Import_ListOfQuotes_BARCHART)

# ============================================================================
# Test ME
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_BARCHART(quotes,'TORONTO EXCHANGE')
    Import_ListOfQuotes_BARCHART(quotes,'TORONTO VENTURE')
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
