#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_bombay.py
#
# Description: List of quotes from http://www.bseindia.com
#
# Developed for iTrade code (http://itrade.sourceforge.net).
#
# Original template for "plug-in" to iTrade is from Gilles Dumortier.
# New code for BSE is from Michel Legrand.
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
# Import_ListOfQuotes_BOMBAY()
# ============================================================================
def removeCarriage(s):
    if s[-1] == '\r':
        return s[:-1]
    else:
        return s

def splitLines(buf):
    lines = buf.split('\r\n')
    lines = [x for x in lines if x]

    lines = [removeCarriage(l) for l in lines]
    return lines


def Import_ListOfQuotes_BSE(quotes, market='BOMBAY EXCHANGE', dlg=None, x=0):
    if itrade_config.verbose:
        print(u'Update {} list of symbols'.format(market))
    connection=ITradeConnection(proxy=itrade_config.proxyHostname,
                                proxyAuth=itrade_config.proxyAuthentication)

    if market == 'BOMBAY EXCHANGE':
        starturl = 'https://test.bseindia.com/scripsearch/scrips.aspx?myScrip='
        #endurl = '&flag=sr'
    else:
        return False

    select_alpha = ['20MICRONS','3IINFOTECH','3MINDIA','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
    n = 0
    isin = ''

    for letter in select_alpha:
        url = starturl + letter

        try:
            data = connection.getDataFromUrl(url)
        except Exception:
            debug('Import_ListOfQuotes_BSE unable to connect :-(')
            return False
        # returns the data
        lines = splitLines(data)

        for line in lines:
            if '<td align="center"><font color="#0089CF">' in line:
            #if '<td align="center" style="color:#0089CF;">' in line:
                #scrip_cd = line[(line.find('"#0089CF">')+10):(line.find ('</font></td><td'))]
                name = line[(line.find('#">')+3):(line.find ('</a></td><td'))]
                name = name.upper()
                ticker = line[(line.find('<u>')+3):(line.find ('</u>'))]

                if 'FUND' in name or 'MATURITY' in name:
                    pass
                if '>#<' in line or '>@</' in line:
                    #Suspended due to penal reasons
                    #Suspended due to procedural reasons
                    pass
                else:
                    #print name,ticker
                    n = n + 1
                    #Partial activation of the Progressbar
                    dlg.Update(x, u'B S E : {} /~3800'.format(n))

                    quotes.addQuote(isin=isin, name=name,
                        ticker=ticker, market='BOMBAY EXCHANGE', currency='INR', place='BSE', country='IN')

    if itrade_config.verbose:
        print(u'Imported {:d} lines from BOMBAY EXCHANGE'.format(n))

    return True

# ============================================================================
# Export me
# ============================================================================

gListSymbolRegistry.register('BOMBAY EXCHANGE', 'BSE', QList.any, QTag.list, Import_ListOfQuotes_BSE)

# ============================================================================
# Test ME
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_BSE(quotes)
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
