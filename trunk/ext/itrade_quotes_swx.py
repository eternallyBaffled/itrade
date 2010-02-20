#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_swx.py
#
# Description: List of quotes from swx.com : SWISS MARKET
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is Gilles Dumortier.
# New code for SWX is from Michel Legrand.
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
# 2007-04-14    dgil  Wrote it from scratch
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
import itrade_csv
from itrade_logging import *
from itrade_defs import *
from itrade_ext import *
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_SWX()
#
# ============================================================================

def Import_ListOfQuotes_SWX(quotes,market='SWISS EXCHANGE',dlg=None,x=0):
    print 'Update %s list of symbols' % market
    connection = ITradeConnection(cookies = None,
                               proxy = itrade_config.proxyHostname,
                               proxyAuth = itrade_config.proxyAuthentication,
                               connectionTimeout = itrade_config.connectionTimeout
                               )
    if market=='SWISS EXCHANGE':    
        # find url to update list
        ch = 'a href="/data/market/statistics/swiss_blue_chip_shares_'
        
        try:
            url = connection.getDataFromUrl('http://www.six-swiss-exchange.com/shares/explorer/download/download_en.html')
        except:
            info('Import_ListOfQuotes_SWX_%s:unable to get file name :-(' % market)
            return False

        if url.find(ch):
            date = url.find(ch)+len(ch)
            date = url[date:url.index('.csv',date)]
        else:
            info('Import_ListOfQuotes_SWX_%s:unable to get Date :-(' % market)
            return False

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

    select_shares = ['swiss_blue_chip_shares_','mid_and_small_caps_swiss_shares_','foreign_shares_']
    count = 0
    for type_shares in select_shares:
        
        url = 'http://www.six-swiss-exchange.com/data/market/statistics/' + type_shares + date + '.csv'

        info('Import_ListOfQuotes_SWX:connect to %s' % url)

        try:
            data=connection.getDataFromUrl(url)
        except:
            info('Import_ListOfQuotes_SWX:unable to connect :-(')
            return False

        # returns the data
        lines = splitLines(data)
        n = 0
        indice = {}

        for line in lines:
            item = itrade_csv.parse(line,7)
            if len(item)>2:
                if n==0:
                    i = 0
                    for ind in item:
                        indice[ind] = i
                        i = i + 1

                    iISIN = indice['ISIN']
                    iName = indice['ShortName']
                    iCurrency = indice['TradingBaseCurrency']
                    iExchange = indice['Exchange']
                    iCountry = indice['GeographicalAreaCode']
                    iTicker = indice['ValorSymbol']
                    n = 1
                else:
                    quotes.addQuote(isin=item[iISIN],name=item[iName].replace(',',' '), ticker=item[iTicker],market='SWISS EXCHANGE',\
                        currency=item[iCurrency],place=item[iExchange],country=item[iCountry])
                    count = count + 1

    print 'Imported %d lines from %s data.' % (count,market)

    return True

# ============================================================================
# Export me
# ============================================================================

registerListSymbolConnector('SWISS EXCHANGE','XSWX',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_SWX)
registerListSymbolConnector('SWISS EXCHANGE','XVTX',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_SWX)

# ============================================================================
# Test ME
# ============================================================================

if __name__=='__main__':

    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_SWX(quotes,'XSWX')
    Import_ListOfQuotes_SWX(quotes,'XVTX')
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
