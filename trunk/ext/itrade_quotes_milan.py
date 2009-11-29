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
# Import_ListOfQuotes_LSE()
#
# ============================================================================

def Import_ListOfQuotes_MIL(quotes,market='MILAN EXCHANGE',dlg=None,x=0):
    print 'Update %s list of symbols' % market
    connection = ITradeConnection(cookies = None,
                               proxy = itrade_config.proxyHostname,
                               proxyAuth = itrade_config.proxyAuthentication,
                               connectionTimeout = itrade_config.connectionTimeout
                               )

    import xlrd

    if market=='MILAN EXCHANGE':
        url = 'http://www.borsaitaliana.it/documenti/rubriche/borsainforma/ems.xls'
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

    info('Import_ListOfQuotes_MIL_%s:connect to %s' % (market,url))

    try:
        data = connection.getDataFromUrl(url)
    except:
        info('Import_ListOfQuotes_MIL_%s:unable to connect :-(' % market)
        return False



    # returns the data
    book = itrade_excel.open_excel(file=None,content=data)
    sh = book.sheet_by_index(0)
    n = 0
    count = 0
    indice = {}

    print 'Import_ListOfQuotes_MIL_%s:' % market,'book',book,'sheet',sh,'nrows=',sh.nrows

    for line in range(sh.nrows):
        if sh.cell_type(line,1) != xlrd.XL_CELL_EMPTY:
            if n==0:
                for i in range(sh.ncols):
                    val = sh.cell_value(line,i)
                    indice[val] = i

                    # be sure we have detected the title
                    if val == 'ISIN_CODE': n = n + 1

                if n==1:
                    if itrade_config.verbose: print 'Indice:',indice

                    iISIN = indice['ISIN_CODE']
                    iName = indice['SHARE_NAME']
                    iTicker = indice['LOCAL_TIDM']
                    n = n +1
            else:
                isin = sh.cell_value(line,iISIN)
                ticker = sh.cell_value(line,iTicker)
                name = sh.cell_value(line,iName)
                
                name = name.encode('cp1252')
                
                if name <> '':
                    quotes.addQuote(isin=isin,name=name, \
                        ticker=ticker,market=market,\
                        currency='EUR',place='MIL',country='IT')
                    count = count + 1

    print 'Imported %d/%d lines from %s data.' % (count,sh.nrows,market)

    return True

# ============================================================================
# Export me
# ============================================================================

if itrade_excel.canReadExcel:
    registerListSymbolConnector('MILAN EXCHANGE','MIL',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_MIL)

# ============================================================================
# Test ME
# ============================================================================

if __name__=='__main__':

    setLevel(logging.INFO)

    from itrade_quotes import quotes

    if itrade_excel.canReadExcel:
        Import_ListOfQuotes_LSE(quotes,'MILAN EXCHANGE')
        
        quotes.saveListOfQuotes()
    else:
        print 'XLRD package not installed :-('

# ============================================================================
# That's all folks !
# ============================================================================
