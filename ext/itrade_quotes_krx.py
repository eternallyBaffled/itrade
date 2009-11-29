#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_krx.py
#
# Description: List of quotes from http://eng.krx.co.kr/: KOREA STOCK EXCHANGE - KOREA KOSDAQ EXCHANGE
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is Gilles Dumortier.
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
from itrade_logging import *
from itrade_defs import *
from itrade_ext import *
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_KRX()
#
# ============================================================================

def Import_ListOfQuotes_KRX(quotes,market='KOREA STOCK EXCHANGE',dlg=None,x=0):
    print 'Update %s list of symbols' % market
    connection = ITradeConnection(cookies = None,
                               proxy = itrade_config.proxyHostname,
                               proxyAuth = itrade_config.proxyAuthentication,
                               connectionTimeout = itrade_config.connectionTimeout
                               )


    if market=='KOREA STOCK EXCHANGE':
        url = 'http://eng.krx.co.kr/anylogic/process//mki/com/itemSearch.xml?&word=&mkt_typ=S&mnu_typ=&charOrder=&market_gubun=kospiVal'
        place = 'KRX'
    elif market=='KOREA KOSDAQ EXCHANGE':
        url = 'http://eng.krx.co.kr/anylogic/process//mki/com/itemSearch.xml?&word=&mkt_typ=S&mnu_typ=&charOrder=&market_gubun=kosdaqVal'
        place = 'KOS'
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

    info('Import_ListOfQuotes_KRX_%s:connect to %s' % (market,url))

    try:
        data = connection.getDataFromUrl(url)
    except:
        info('Import_ListOfQuotes_KRX_%s:unable to connect :-(' % market)
        return False
    
    # returns the data
    lines = splitLines(data)
    n = 0

    print 'Import_ListOfQuotes_KRX_%s:' % market

    for line in lines:
        if line.find('<result><isu_cd>')<> -1:
            n = n + 1

            isin = line[line.index('<result><isu_cd>')+16:line.index('</isu_cd><shrt_isu_cd>A')]
        
            ticker = line[line.index('</isu_cd><shrt_isu_cd>A')+23:line.index('</shrt_isu_cd><isu_nm>')]
        
            name = line[line.index('</shrt_isu_cd><isu_nm>')+22:line.index('</isu_nm></result>')]
            if name.find('<![CDATA[')<> -1:
                name = name[9:-3]
            name = name.replace(',',' ')
            name = name.upper()

            # ok to proceed
   
            quotes.addQuote(isin = isin,name = name,ticker = ticker,\
            market = market,currency = 'KRW',place = place, country = 'KR')
            
    print 'Imported %d lines from %s data.' % (n,market)

    return True

# ============================================================================
# Export me
# ============================================================================

registerListSymbolConnector('KOREA STOCK EXCHANGE','KRX',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_KRX)
registerListSymbolConnector('KOREA KOSDAQ EXCHANGE','KOS',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_KRX)

# ============================================================================
# Test ME
# ============================================================================

if __name__=='__main__':

    setLevel(logging.INFO)

    from itrade_quotes import quotes
    
    Import_ListOfQuotes_LSE(quotes,'KOREA STOCK EXCHANGE')
    Import_ListOfQuotes_LSE(quotes,'KOREA KOSDAQ EXCHANGE')
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
