#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_ie.py
#
# Description: List of quotes from ise.ie : IRISH EXCHANGE
#
# Developed for iTrade code (http://itrade.sourceforge.net).
#
# Original template for "plug-in" to iTrade is	from Gilles Dumortier.
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
import re

# iTrade system
import itrade_config
from itrade_logging import setLevel, debug
from itrade_defs import QList, QTag
from itrade_ext import gListSymbolRegistry
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_IE()
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


def Import_ListOfQuotes_IE(quotes, market='IRISH EXCHANGE', dlg=None, x=0):
    if itrade_config.verbose:
        print(u'Update {} list of symbols'.format(market))
    connection = ITradeConnection(proxy=itrade_config.proxyHostname,
                                  proxyAuth=itrade_config.proxyAuthentication,
                                  connectionTimeout=itrade_config.connectionTimeout
                                 )

    if market == 'IRISH EXCHANGE':
        url = "https://www.ise.ie/Prices,-Indices-Stats/Equity-Market-Data/Instrument-Identifiers/?list=full&type=SEDOL&exportTo=text"
    else:
        return False

    try:
        data=connection.getDataFromUrl(url)
    except Exception:
        debug('Import_ListOfQuotes_IE:unable to connect :-(')
        return False

    # returns the data
    lines = splitLines(data)

    count = 0
    nlines = 0

    sedol = ''
    isin = ''
    name = ''
    inst = ''
    tick = ''

    for line in lines[1:]:
        # extract data
        sp1 = re.search(r'<td class="equityName">', line, re.IGNORECASE|re.MULTILINE)
        if sp1:
            sp1 = sp1.end()
            sp2 = re.search(r'</td>', line[sp1:], re.IGNORECASE|re.MULTILINE)
            if sp2:
                sp2 = sp2.start()
                data = line[sp1:]
                data = data[:sp2]
                data = data.strip()
                data = data.upper()

                # fill the next field
                if sedol == '':
                    sedol = data
                elif isin == '':
                    isin = data
                elif name == '':
                    name = data
                elif inst == '':
                    inst = data
                else:
                    tick = data

                    # ok to proceed
                    name = name.replace('&AMP;', '&')
                    name = name.replace(',', ' ')

                    if inst[0:3] == 'ORD':  # only want ordinary shares
                        quotes.addQuote(isin=isin, name=name,
                        ticker=tick, market='IRISH EXCHANGE', currency='EUR', place='DUB', country='IE')
                        count = count + 1

                    # reset for next value
                    sedol = ''
                    isin = ''
                    name = ''
                    inst = ''
                    tick = ''
                    nlines = nlines + 1
    if itrade_config.verbose:
        print(u'Imported {:d}/{:d} lines from IRISH EXCHANGE data.'.format(count, nlines))

    return True

# ============================================================================
# Export me
# ============================================================================

gListSymbolRegistry.register('IRISH EXCHANGE', 'DUB', QList.any, QTag.list, Import_ListOfQuotes_IE)

# ============================================================================
# Test ME
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_IE(quotes)
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
