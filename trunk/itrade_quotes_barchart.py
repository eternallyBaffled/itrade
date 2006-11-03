#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_barchart.py
#
# Description: List of quotes from barchart.com : NASDAQ, AMEX, OTCBB
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
# 2006-10-25    dgil  Wrote it from scratch
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
from itrade_isin import filterName
from itrade_import import registerListSymbolConnector

# ============================================================================
# Import_ListOfQuotes_BARCHART()
#
# ============================================================================

global barchart_data
barchart_data = None

def Import_ListOfQuotes_BARCHART(quotes,market='NASDAQ'):
    global barchart_data
    print 'Update %s list of symbols' % market

    if market=='NASDAQ' or market=='AMEX' or market=='OTCBB':
        url = "http://www2.barchart.com/lookup.asp?name=A&opt1=0&start=all&type=&search_usstocks=1"
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

    if not barchart_data:
        # read file (for debugging) or get file from network
        try:
            fn = open('barchart.htm','r')
        except IOError:
            # can't open the file (existing ?)
            fn = None

        if not fn:
            try:
                fn = urllib.urlopen(url)
            except:
                debug('Import_ListOfQuotes_BARCHART:unable to connect :-(')
                return False

        # returns the data
        barchart_data = fn.read()

    #
    lines = splitLines(barchart_data)
    count = 0
    ticker = ''
    name = ''
    exchange = ''

    for line in lines:
        # Typical lines :
        # <TD class=bcText><a href="http://quote.barchart.com/quote.asp?sym=ONJP&code=BSTK" class=bcMLink>1 900 JACKPOT INC</a></TD>
        # <TD class=bcText align=right><a href="http://quote.barchart.com/quote.asp?sym=ONJP&code=BSTK" class=bcMLink>ONJP</a></TD>
        # <TD class=bcText align=right> OTCBB </TD>

        scode = re.search('align=right',line,re.IGNORECASE|re.MULTILINE)
        if scode:
            scode = scode.end()
            sexch = re.search(' </td>',line[scode+2:],re.IGNORECASE|re.MULTILINE)
            if sexch:
                sexch = sexch.start()
                data = line[scode+2:]
                data = data[:sexch]
                exchange = data.upper()

        sstart = re.search('class=bcMLink>',line,re.IGNORECASE|re.MULTILINE)
        if sstart:
            sstart = sstart.end()
            send = re.search('</a></td>',line[sstart:],re.IGNORECASE|re.MULTILINE)
            if send:
                send = send.start()
                data = line[sstart:]
                data = data[:send]

                if scode:
                    ticker = data.upper()
                else:
                    name = data

        if name!='' and ticker!='' and exchange!='':
            name = filterName(name)
            if exchange==market:
                quotes.addQuote(isin='',name=name,ticker=ticker,market=exchange,currency='USD',place='NYC',country='US')
                count = count + 1

            # reset everything
            name = ''
            ticker = ''
            exchange = ''

    print 'Imported %d lines from BARCHART data.' % count

    return True

# ============================================================================
# Export me
# ============================================================================

registerListSymbolConnector('NASDAQ','NYC',Import_ListOfQuotes_BARCHART)
registerListSymbolConnector('AMEX','NYC',Import_ListOfQuotes_BARCHART)
registerListSymbolConnector('OTCBB','NYC',Import_ListOfQuotes_BARCHART)

# ============================================================================
# Test ME
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_BARCHART(quotes,'NASDAQ')
    Import_ListOfQuotes_BARCHART(quotes,'AMEX')
    Import_ListOfQuotes_BARCHART(quotes,'OTCBB')
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
