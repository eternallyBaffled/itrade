#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_nze.py
#
# Description: List of quotes from http://www.nzx.com/
#
# Developed for iTrade code (http://itrade.sourceforge.net).
#
# Original template for "plug-in" to iTrade is	from Gilles Dumortier.
# New code for NZE is from Michel Legrand.

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
import logging
import re
import thread
import time
import string
import urllib

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_defs import *
from itrade_ext import *
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_NZE()
#
# ============================================================================


def Import_ListOfQuotes_NZE(quotes,market='NEW ZEALAND EXCHANGE',dlg=None,x=0):
    print 'Update %s list of symbols' % market
    connection=ITradeConnection(cookies=None,
                                proxy=itrade_config.proxyHostname,
                                proxyAuth=itrade_config.proxyAuthentication)
    
    if market=='NEW ZEALAND EXCHANGE':

        url = 'http://www.nzx.com/markets/all-securities/NZSX/pricebysecurity/'

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
        debug('Import_ListOfQuotes_NZE unable to connect :-(')
        return False

    # returns the data
    lines = splitLines(data)
    nlines = 0

    n = 0

    symbol_list = []

    debline = '/markets/NZSX/'

    for line in lines[200:]:

        if debline in line:
            ticker = line[(line.find('/markets/NZSX/')+14): line.find('</a></div></td>')]
            ticker = ticker[(ticker.find('">')+2):]

            symbol_list.append(ticker)
            n = n + 1

    # extract names and isin codes

    i=1

    for symbol in symbol_list:
        
        urlsymbol = 'http://www.nzx.com/markets/NZSX/'+symbol

        source = urllib.urlopen(urlsymbol)
        data=source.readlines()

        for line in data[200:]:
            if ')</h2>' in line:
                name = line[(line.find('>')+1): (line.find('(')-1)]

            if i == 0:
                
                nlines = nlines + 1
                
                #Partial activation of the Progressbar
                
                dlg.Update(x,'%s : %s / %s'%('NZSX wait ~ 7mn',nlines,n))
               
                i = 1
                isin = line[(line.find('">')+2): line.find('</div></td>')]

                # ok to proceed
                # print isin,name,symbol        
                quotes.addQuote(isin=isin,name=name, \
                ticker=symbol,market='NEW ZEALAND EXCHANGE',currency='NZD',place='NZE',country='NZ')
                break
                source.close()
           
            if 'ISIN' in line:
                i = 1 - i

    print 'Imported %d lines from NEW ZEALAND EXCHANGE data.' % (nlines)

    return True

# ============================================================================
# Export me
# ============================================================================

registerListSymbolConnector('NEW ZEALAND EXCHANGE','NZE',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_NZE)

# ============================================================================
# Test ME
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_NZE(quotes,'NEW ZEALAND EXCHANGE')
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
