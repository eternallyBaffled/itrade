#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_euronext.py
#
# Description: List of quotes from euronext.com : EURONEXT and ALTERNEXT
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
from itrade_quotes import quotes
from itrade_isin import checkISIN

# ============================================================================
# Import_ListOfQuotes_Euronext()
#
# ============================================================================

def Import_ListOfQuotes_Euronext(market='EURONEXT'):

    if market=='EURONEXT':
        url = "http://www.euronext.com/tradercenter/priceslists/trapridownload/0,4499,1732_338638,00.html?belongsToList=market_14&resultsTitle=All%20Euronext%20-%20Eurolist%20by%20Euronext&eligibilityList=&economicGroupList=&sectorList=&branchList="
    elif market=='ALTERNEXT':
        url = "http://www.euronext.com/tradercenter/priceslists/trapridownload/0,4499,1732_338638,00.html?belongsToList=market_15&resultsTitle=All%20Euronext%20-%20Eurolist%20by%20Euronext&eligibilityList=&economicGroupList=&sectorList=&branchList="
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

    for line in lines:
        data = string.split (line, ';')
        if len(data)==11:
            if data[1]!='ISIN':
                if checkISIN(data[1]):
                    if data[2]=='PAR' or data[2]=='BRU' or data[2]=='AMS' or data[2]=='LIS':
                        quotes.addQuote(isin=data[1],name=data[0],ticker=data[3],market=market,currency=data[5])
                    else:
                        print 'unknown EURONEXT place : ',data
                else:
                    print 'invalid ISIN : ',data

    return True

# ============================================================================
# Test ME
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    Import_ListOfQuotes_Euronext('EURONEXT')
    Import_ListOfQuotes_Euronext('ALTERNEXT')
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
