#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_euronext.py
#
# Description: List of quotes from euronext.com : EURONEXT, ALTERNEXT and
# MARCHE LIBRE (PARIS & BRUXELLES)
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is	Gilles Dumortier.
#
# Portions created by the Initial Developer are Copyright (C) 2004-2006 the
# Initial Developer. All Rights Reserved.
#
# Contributor(s):
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
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
# 2005-06-11    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import re
import thread
import time
import urllib
import string

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_isin import checkISIN,filterName
from itrade_import import *

# ============================================================================
# Import_ListOfQuotes_Euronext()
#
# ============================================================================

def Import_ListOfQuotes_Euronext(quotes,market='EURONEXT'):
    print 'Update %s list of symbols' % market

    if market=='EURONEXT':
        url = "http://www.euronext.com/tradercenter/priceslists/trapridownload/0,4499,1732_338638,00.html?belongsToList=market_14&eligibilityList=&economicGroupList=&sectorList=&branchList="
    elif market=='ALTERNEXT':
        url = "http://www.euronext.com/tradercenter/priceslists/trapridownload/0,4499,1732_338638,00.html?belongsToList=market_15&eligibilityList=&economicGroupList=&sectorList=&branchList="
    elif market=='PARIS MARCHE LIBRE':
        url = "http://www.euronext.com/tradercenter/priceslists/trapridownload/0,4499,1732_338638,00.html?belongsToList=market_10&eligibilityList=&economicGroupList=&sectorList=&branchList="
    elif market=='BRUXELLES MARCHE LIBRE':
        url = "http://www.euronext.com/tradercenter/priceslists/trapridownload/0,4499,1732_338638,00.html?belongsToList=market_17&eligibilityList=&economicGroupList=&sectorList=&branchList="
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
        f = urllib.urlopen(url)
    except:
        debug('Import_ListOfQuotes_Euronext:unable to connect :-(')
        return False

    # returns the data
    data = f.read()
    lines = splitLines(data)
    count = 0

    for line in lines:
        data = string.split (line, ';')

        if len(data)==35:
            if data[1]!='ISIN':
                if checkISIN(data[1]):
                    if data[3]=='PAR' or data[3]=='BRU' or data[3]=='AMS' or data[3]=='LIS':
                        name = filterName(data[0])
                        quotes.addQuote(isin=data[1],name=name,ticker=data[4],market=market,currency=data[7],place=data[3],country=None)
                        count = count + 1
                    else:
                        print 'unknown ALTERNEXT place : ',data
                else:
                    print 'invalid ISIN : ',data

        if len(data)==34:
            if data[1]!='ISIN':
                if checkISIN(data[1]):
                    if data[3]=='PAR' or data[3]=='BRU' or data[3]=='AMS' or data[3]=='LIS':
                        name = filterName(data[0])
                        quotes.addQuote(isin=data[1],name=name,ticker=data[4],market=market,currency=data[6],place=data[3],country=None,debug=True)
                        count = count + 1
                    else:
                        print 'unknown EURONEXT place : ',data
                else:
                    print 'invalid ISIN : ',data

    print 'Imported %d/%d lines from %s data.' % (count,len(lines),market)

    return True

# ============================================================================
# Export me
# ============================================================================

registerListSymbolConnector('EURONEXT','PAR',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_Euronext)
registerListSymbolConnector('ALTERNEXT','PAR',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_Euronext)
registerListSymbolConnector('PARIS MARCHE LIBRE','PAR',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_Euronext)
registerListSymbolConnector('BRUXELLES MARCHE LIBRE','BRU',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_Euronext)

# ============================================================================
# Test ME
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_Euronext(quotes,'EURONEXT')
    Import_ListOfQuotes_Euronext(quotes,'ALTERNEXT')
    Import_ListOfQuotes_Euronext(quotes,'PARIS MARCHE LIBRE')
    Import_ListOfQuotes_Euronext(quotes,'BRUXELLES MARCHE LIBRE')
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
