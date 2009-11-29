#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_madrid.py
#
# Description: List of quotes from http://www.bolsamadrid.es
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is Gilles Dumortier.
# New code for Bolsa Madrid is from Michel Legrand.

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
# Import_ListOfQuotes_MADRID()
#
# ============================================================================

def Import_ListOfQuotes_MADRID(quotes,market='MADRID EXCHANGE',dlg=None,x=0):
    print 'Update %s list of symbols' % market
    connection = ITradeConnection(cookies = None,
                               proxy = itrade_config.proxyHostname,
                               proxyAuth = itrade_config.proxyAuthentication,
                               connectionTimeout = itrade_config.connectionTimeout
                               )

    if market=='MADRID EXCHANGE':
        url = 'http://www.bolsamadrid.es/ing/empresas/empresas_alf.xls'# is actually tab delimited
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

    info('Import_ListOfQuotes_MADRID_%s:connect to %s' % (market,url))

    try:
        data = connection.getDataFromUrl(url)
    except:
        info('Import_ListOfQuotes_MADRID_%s:unable to connect :-(' % market)
        return False


    # returns the data
    lines = splitLines(data)
    count = 0
    ch = 'Ticker:</b></font>&nbsp;'
    ticker=''

    for line in lines[2:]:
        data = string.split (line, '\t')    # tab delimited
        if data[5] == 'Continuous Market':
            isin=data[2].strip()
            name=data[1].replace(',',' ').replace('ñ','n')

            url2 = 'http://www.bolsamadrid.es/comun/fichaemp/fichavalor.asp?isin='+isin+'&id=ing'
            try:
                dataticker = connection.getDataFromUrl(url2)
            except:
                info('Import_ListOfQuotes_MADRID_%s:unable to connect :-(' % market)
                return False

            linesticker = splitLines(dataticker)

            for lineticker in linesticker:
                
                if 'Ticker' in lineticker:
                    
                    pos= lineticker.find(ch)+ len(ch)
                    ticker = lineticker[pos:lineticker.index(' &nbsp',pos)]
                    count = count + 1
                    break
                
            #Partial activation of the Progressbar
            dlg.Update(x,'MADRID : %s /~130'%count)
                   
            quotes.addQuote(isin=isin,name=name, \
                ticker=ticker,market=market,\
                currency='EUR',place='MAD',country='ES')
            
            ticker = ''
    print 'Imported %d lines from %s' % (count,market)

    return True

# ============================================================================
# Export me
# ============================================================================

registerListSymbolConnector('MADRID EXCHANGE','MAD',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_MADRID)

# ============================================================================
# Test ME
# ============================================================================

if __name__=='__main__':

    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_MADRID(quotes,'MADRID EXCHANGE')
        
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
