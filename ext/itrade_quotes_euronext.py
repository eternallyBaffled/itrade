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
# 2005-06-11    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import string

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_isin import checkISIN,filterName
from itrade_defs import *
from itrade_ext import *
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_Euronext()
#
# ============================================================================

def Import_ListOfQuotes_Euronext(quotes,market='EURONEXT',dlg=None,x=0):
    print 'Update %s list of symbols' % market
    connection = ITradeConnection(cookies = None,
                               proxy = itrade_config.proxyHostname,
                               proxyAuth = itrade_config.proxyAuthentication,
                               connectionTimeout = max(45,itrade_config.connectionTimeout)
                               )

    cha = "7213"

    if market=='EURONEXT':
        url = "http://www.euronext.com/search/download/trapridownloadpopup.jcsv?pricesearchresults=actif&filter=1&lan=EN&belongsToList=market_EURLS&cha=%s&format=txt&formatDecimal=.&formatDate=dd/MM/yy" % cha
    elif market=='ALTERNEXT':
        url = "http://www.euronext.com/search/download/trapridownloadpopup.jcsv?pricesearchresults=actif&filter=1&lan=EN&belongsToList=market_ALTX&cha=%s&format=txt&formatDecimal=.&formatDate=dd/MM/yy" % cha
    elif market=='PARIS MARCHE LIBRE':
        url = "http://www.euronext.com/search/download/trapridownloadpopup.jcsv?pricesearchresults=actif&filter=1&lan=EN&belongsToList=market_MC&cha=%s&format=txt&formatDecimal=.&formatDate=dd/MM/yy" % cha
    elif market=='BRUXELLES MARCHE LIBRE':
        url = "http://www.euronext.com/search/download/trapridownloadpopup.jcsv?pricesearchresults=actif&filter=1&lan=EN&belongsToList=market_BRUMC&cha=%s&format=txt&formatDecimal=.&formatDate=dd/MM/yy" % cha
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
        debug('Import_ListOfQuotes_Euronext:unable to connect :-(')
        return False

    indice = {}
    """
    "Instrument's name";
    "ISIN";
    "Euronext code";
    "MEP";
    "Symbol";
    "ICB Sector (Level 4)";
    "Trading currency";
    "Last";
    "Volume";
    "D/D-1 (%)";
    "Date - time (CET)";
    "Turnover";
    "Total number of shares";
    "Capitalisation";
    "Trading mode";
    "Day First";
    "Day High";
    "Day High / Date - time (CET)";
    "Day Low";
    "Day Low / Date - time (CET)";
    "31-12/Change (%)";
    "31-12/High";
    "31-12/High/Date";
    "31-12/Low";
    "31-12/Low/Date";
    "52 weeks/Change (%)";
    "52 weeks/High";
    "52 weeks/High/Date";
    "52 weeks/Low";
    "52 weeks/Low/Date";
    "Suspended";
    "Suspended / Date - time (CET)";
    "Reserved";
    "Reserved / Date - time (CET)"
    """

    # returns the data
    lines = splitLines(data)
    count = 0

    for line in lines:
        data = string.split (line, ';')

        if len(data)>2:
            if not indice.has_key("ISIN"):
                i = 0
                for ind in data:
                    indice[ind] = i
                    i = i + 1

                iName = indice["Instrument's name"]
                iISIN = indice["ISIN"]
                iMEP = indice["MEP"]
                iTicker = indice["Symbol"]
                iCurr = indice["Trading currency"]

            else:
                if data[iISIN]!="ISIN":
                    if checkISIN(data[iISIN]):
                        if data[iMEP]=='PAR' or data[iMEP]=='BRU' or data[iMEP]=='AMS' or data[iMEP]=='LIS':
                            name = filterName(data[iName])
                            quotes.addQuote(isin=data[iISIN],name=name,ticker=data[iTicker],market=market,currency=data[iCurr],place=data[iMEP],country=None)
                            count = count + 1
                        else:
                            if itrade_config.verbose:
                                print 'unknown place :',data[iMEP],'>>>',data
                    else:
                        if itrade_config.verbose:
                            print 'invalid ISIN :',data[iISIN],'>>>',data

        else:
            print len(data),'>>>',data

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
