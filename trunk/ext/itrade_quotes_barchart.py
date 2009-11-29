#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_barchart.py
#
# Description: List of quotes from barchart.com :  NYSE, NASDAQ, AMEX, OTCBB,
# TORONTO (TSE and TSX)
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
import string

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_isin import filterName
from itrade_defs import *
from itrade_ext import *
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_BARCHART()
#
# ============================================================================

global barchart_data
barchart_data = {}

def Import_ListOfQuotes_BARCHART(quotes,market='NASDAQ',dlg=None,x=0):
    global barchart_data
    print 'Update %s list of symbols' % market
    connection = ITradeConnection(cookies = None,
                               proxy = itrade_config.proxyHostname,
                               proxyAuth = itrade_config.proxyAuthentication,
                               connectionTimeout = itrade_config.connectionTimeout
                               )

    if market=='NASDAQ' or market=='AMEX' or market=='OTCBB' or market == 'NYSE':
        url = "http://www2.barchart.com/lookup.asp?name=%s&opt1=1&start=all&type=&search_usstocks=1&search_usfunds=&search_canstocks="
        m_currency = 'USD'
        m_place = 'NYC'
        m_country = 'US'
    elif market=='TORONTO EXCHANGE' or market=='TORONTO VENTURE':
        url = "http://www2.barchart.com/lookup.asp?name=%s&opt1=1&start=all&type=&search_usstocks=&search_usfunds=&search_canstocks=1"
        m_currency = 'CAD'
        m_place = 'TOR'
        m_country = 'CA'
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

    def import_letter(letter,dlg,x):

        if dlg:
            dlg.Update(x,"BARCHART %s:'%s'"%(market,letter))
            print x,"BARCHART %s:'%s'"%(market,letter)

        if not barchart_data.has_key("%s.%s" % (letter,m_country)):
            # read file (for debugging) or get file from network
            try:
                fn = open('barchart%s.htm' % letter,'r')
            except IOError:
                # can't open the file (existing ?)
                fn = None

            if not fn:
                try:
                    data=connection.getDataFromUrl(url%letter)
                except:
                    print 'Import_ListOfQuotes_BARCHART:unable to connect to',url%letter
                    return False
            else:
                data=fn.read()

            # returns the data
            barchart_data["%s.%s" % (letter,m_country)] = data

        #
        lines = splitLines(barchart_data["%s.%s" % (letter,m_country)])
        ticker = ''
        name = ''
        exchange = ''
        count = 0

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
                #print '"',name, '" - "',ticker, '" - "',exchange,'"'
                name = filterName(name)

                if exchange=='TSX': exchange='TORONTO EXCHANGE'
                if exchange=='TSX.V' : exchange='TORONTO VENTURE'

                #print '"',name, '" - "',ticker, '" - "',exchange,'" market:',market

                ignore = False
                if exchange=='TORONTO EXCHANGE':
                    if ticker[0:4] == "ITT-" or ticker[0:4] == "IRT-": # ignore indices : managed by hand in symbols/indices.txt
                        ignore = True
                        #print 'ignore Index : "',name, '" - "',ticker, '" - "',exchange,'" market:',market

                    s = ticker.split('-')
                    if len(s)==3:
                        if s[1]=="DB" : # ignore DEBit
                            ignore = True
                            #print 'ignore Index : "',name, '" - "',ticker, '" - "',exchange,'" market:',market

                if not ignore and exchange==market:
                    if ticker[-3:]=='.TO' or ticker[-3:]=='.VN':
                        ticker = ticker[:-3]

                    quotes.addQuote(isin='',name=name,ticker=ticker,market=exchange,currency=m_currency,place=m_place,country=m_country)
                    count = count + 1

                # reset everything
                name = ''
                ticker = ''
                exchange = ''

        print 'Imported %d lines from BARCHART data (letter=%s)' % (count,letter)

    import_letter('1',dlg,x-1)
    import_letter('2',dlg,x)
    import_letter('3',dlg,x-1)
    import_letter('4',dlg,x)
    import_letter('5',dlg,x-1)
    import_letter('6',dlg,x)
    import_letter('7',dlg,x-1)
    import_letter('8',dlg,x)
    import_letter('9',dlg,x-1)
    import_letter('A',dlg,x)
    import_letter('B',dlg,x-1)
    import_letter('C',dlg,x)
    import_letter('D',dlg,x-1)
    import_letter('E',dlg,x)
    import_letter('F',dlg,x-1)
    import_letter('G',dlg,x)
    import_letter('H',dlg,x-1)
    import_letter('I',dlg,x)
    import_letter('J',dlg,x-1)
    import_letter('K',dlg,x)
    import_letter('L',dlg,x-1)
    import_letter('M',dlg,x)
    import_letter('N',dlg,x-1)
    import_letter('O',dlg,x)
    import_letter('P',dlg,x-1)
    import_letter('Q',dlg,x)
    import_letter('R',dlg,x-1)
    import_letter('S',dlg,x)
    import_letter('T',dlg,x-1)
    import_letter('U',dlg,x)
    import_letter('V',dlg,x-1)
    import_letter('W',dlg,x)
    import_letter('X',dlg,x-1)
    import_letter('Y',dlg,x)
    import_letter('Z',dlg,x-1)

    return True

# ============================================================================
# Export me
# ============================================================================

registerListSymbolConnector('NASDAQ','NYC',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_BARCHART)
registerListSymbolConnector('AMEX','NYC',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_BARCHART)
registerListSymbolConnector('OTCBB','NYC',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_BARCHART)
registerListSymbolConnector('NYSE','NYC',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_BARCHART)

registerListSymbolConnector('TORONTO EXCHANGE','TOR',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_BARCHART)
registerListSymbolConnector('TORONTO VENTURE','TOR',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_BARCHART)

# ============================================================================
# Test ME
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_BARCHART(quotes,'NASDAQ')
    Import_ListOfQuotes_BARCHART(quotes,'AMEX')
    Import_ListOfQuotes_BARCHART(quotes,'OTCBB')
    Import_ListOfQuotes_BARCHART(quotes,'NYSE')
    Import_ListOfQuotes_BARCHART(quotes,'TORONTO EXCHANGE')
    Import_ListOfQuotes_BARCHART(quotes,'TORONTO VENTURE')
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
