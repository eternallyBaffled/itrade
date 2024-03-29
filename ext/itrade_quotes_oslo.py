#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_oslo.py
#
# Description: List of quotes from http://www.oslobors.no/
#
# Developed for iTrade code (http://itrade.sourceforge.net).
#
# Original template for "plug-in" to iTrade is from Gilles Dumortier.
# New code for OSLO is from Michel Legrand.
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

# iTrade system
import itrade_config
from itrade_logging import setLevel, debug
from itrade_defs import QList, QTag
from itrade_ext import gListSymbolRegistry
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_OSLO()
# ============================================================================
def removeCarriage(s):
    if s[-1] == '\r':
        return s[:-1]
    else:
        return s


def splitLines(buf):
    lines = buf.split('Overview?')
    lines = [x for x in lines if x]

    lines = [removeCarriage(l) for l in lines]
    return lines


def Import_ListOfQuotes_OSLO(quotes, market='OSLO EXCHANGE', dlg=None, x=0):
    if itrade_config.verbose:
        print(u'Update {} list of symbols'.format(market))
    connection = ITradeConnection(proxy=itrade_config.proxyHostname,
                                  proxyAuth=itrade_config.proxyAuthentication)

    if market == 'OSLO EXCHANGE':
        starturl = 'https://www.oslobors.no/markedsaktivitet/stockIsinList?newt_isinList-stock_exch=ose&newt_isinList-stock_sort=aLONG_NAME&newt_isinList-stock_page='
        endurl = '&newt__menuCtx=1.12'
    else:
        return False

    nlines = 0
    endpage = 8

    select_page = ['1', '2', '3', '4', '5', '6', '7', '8']

    for page in select_page:
        url = starturl + page + endurl

        try:
            data = connection.getDataFromUrl(url)
        except Exception:
            debug('Import_ListOfQuotes_OSLO:unable to connect :-(')
            return False

        # returns the data
        lines = splitLines(data)

        #typical line
        #newt__ticker=TFSO" title="">24Seven Technology Group</a></td><td class="c2">NO0010279474</td><td class="c3 o l">TFSO</td></tr><tr id="manamind_isinList__stock_table_table_r2" class="r2"><td class="c0 f"><div title="Aksjer p� Oslo B�rs"><img src="http://ose.asp.manamind.com/ob/images/markedssymbol-XOSL-tiny.png" width="8" height="8" /></div></td><td class="c1 o"><a href=

        for line in lines:
            if line.find('newt__ticker=') != -1:
                #partial activation of Progressbar
                dlg.Update(x, u'{} : {} / {}'.format(market, page, endpage))

                ticker = line[line.index('newt__ticker=')+13:line.index('" title="">')]

                if ticker == 'SAS+NOK':
                    ticker = 'SAS'

                name = line[line.index(' title="">')+10:line.index('</a></td><td')]

                name = name.replace('&amp;', '&')
                name = name.replace('�', 'o')
                name = name.replace('�', 'ae')
                name = name.replace('�', 'o')

                isin = line[line.index('class="c2">')+11:line.index('</td><td class="c3 o l">')]

                #ok to proceed

                quotes.addQuote(isin=isin, name=name,
                            ticker=ticker, market='OSLO EXCHANGE',
                            currency='NOK', place='OSL', country='NO')

                nlines = nlines + 1
    if itrade_config.verbose:
        print(u'Imported {:d} lines from OSLO EXCHANGE'.format(nlines))

    return True

# ============================================================================
# Export me
# ============================================================================

gListSymbolRegistry.register('OSLO EXCHANGE', 'OSL', QList.any, QTag.list, Import_ListOfQuotes_OSLO)

# ============================================================================
# Test ME
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_OSLO(quotes)
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
