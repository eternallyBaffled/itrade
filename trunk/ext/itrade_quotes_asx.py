#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_asx.py
#
# Description: List of quotes from http://www.asx.com.au
# ASX - Australian Stock Exchange
#
# Developed for iTrade code (http://itrade.sourceforge.net).
#
# Original template for "plug-in" to iTrade is	from Gilles Dumortier.
# New code for ASX is from Peter Mills.
#
# Portions created by the Initial Developer are Copyright (C) 2006-2008 the
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
# 2006-12-30    PeterMills  Initial version
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
import itrade_excel
from itrade_logging import *
from itrade_defs import *
from itrade_ext import *
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_ASX()
#
# ============================================================================

def Import_ListOfQuotes_ASX(quotes,market='ASX',dlg=None,x=0):
    print 'Update %s list of symbols' % market
    connection = ITradeConnection(cookies = None,
                               proxy = itrade_config.proxyHostname,
                               proxyAuth = itrade_config.proxyAuthentication,
                               connectionTimeout = itrade_config.connectionTimeout
                               )
    import xlrd

    if market=='ASX':
        url = "http://www.asx.com.au/documents/resources/ISIN.xls"
        n = 0
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

    try:
        data=connection.getDataFromUrl(url)
    except:
        debug('Import_ListOfQuotes_ASX:unable to connect :-(')
        return False

    # returns the data
    try:
        book = itrade_excel.open_excel(file=None,content=data)
        sh = book.sheet_by_index(0)

        for line in range(sh.nrows):
            if sh.cell_type(line,1) != xlrd.XL_CELL_EMPTY:

                if sh.cell_value(line,2)=='ORDINARY FULLY PAID':   # only want ordinary shares
                    isin = sh.cell_value(line,3)
                    name = sh.cell_value(line,1)
                    name = name.encode('cp1252') # must encode like that
                    name = name.replace(',',' ')
                    ticker = sh.cell_value(line,0)
                    quotes.addQuote(isin = isin,name = name, \
                    ticker = ticker,market='ASX',currency='AUD',place='SYD',country='AU')

                    n = n + 1
                    
    except:
        lines = splitLines(data)

        for line in lines[5:]:
            # skip header lines (PeterMills> 2007-06-22)
            data = string.split (line, '\t')    # tab delimited
            if data[2]=='ORDINARY FULLY PAID':  # only want ordinary shares
                isin=data[3]
                name=data[1].replace(',',' ')
                ticker=data[0]
                quotes.addQuote(isin = isin,name = name, \
                ticker = ticker,market='ASX',currency='AUD',place='SYD',country='AU')

                n = n + 1

    if itrade_config.verbose:
        print 'Imported %d lines from %s data.' % (n,market)

    return True
# ============================================================================
# Export me
# ============================================================================
if itrade_excel.canReadExcel:
    registerListSymbolConnector('ASX','SYD',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_ASX)

# ============================================================================
# Test ME
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes
    
    if itrade_excel.canReadExcel:
        Import_ListOfQuotes_ASX(quotes,'ASX')

        quotes.saveListOfQuotes()
    else:
        print 'XLRD package not installed :-('

# ============================================================================
# That's all folks !
# ============================================================================
