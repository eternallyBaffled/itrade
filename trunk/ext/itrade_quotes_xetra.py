#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_xetra.py
#
# Description: List of quotes from deutsche-boerse.com: XETRA
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# Original template for "plug-in" to iTrade is from Gilles Dumortier.
# New code for XETRA is from Michel Legrand.
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
# 2007-12-18    ml    Wrote it from template
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import re
import thread
import time
import string

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_defs import *
from itrade_ext import *
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_Xetra()
#
# ============================================================================

def Import_ListOfQuotes_Xetra(quotes,market='FRANKFURT EXCHANGE',dlg=None,x=0):
    print 'Update %s list of symbols' % market
    connection=ITradeConnection(cookies=None,
                                proxy=itrade_config.proxyHostname,
                                proxyAuth=itrade_config.proxyAuthentication)

    if market=='FRANKFURT EXCHANGE':
        url = "http://info.xetra.de/download_xetrawerte.txt"
    else:
        return False

    def splitLines(buf):
        lines = string.split(buf, '\n')
        lines = filter(lambda x:x, lines)
        def removeCarriage(s):
            if s[-1]=='\r':
                return s[:-1]
            else:
                return s
        lines = [removeCarriage(l) for l in lines]
        return lines

    #info('Import_ListOfQuotes_Xetra:connect %s to %s' % (market,url))

    try:
        data=connection.getDataFromUrl(url)
    except:
        debug('Import_ListOfQuotes_Xetra:unable to connect :-(')
        return False

    # returns the data
    lines = splitLines(data)
    n = 0

    for line in lines[2:]:
        data = string.split (line, ';')    # ; delimited

        if len(data) >5:
            if data[6] in ('GER0','GER1','GER2','DAX1','MDAX1','SDX1','TDX1'):
                quotes.addQuote(isin=data[1],name=data[0].replace(',',' '),ticker=data[3],\
                    market='FRANKFURT EXCHANGE',currency='EUR',place='FRA',country='DE')
                n = n + 1

    print 'Imported %d/%d lines from %s data.' % (n,len(lines),'Xetra')

    return True

# ============================================================================
# Export me
# ============================================================================

registerListSymbolConnector('FRANKFURT EXCHANGE','FRA',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_Xetra)

# ============================================================================
# Test ME
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_Xetra(quotes,'FRA')
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
