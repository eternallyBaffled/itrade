#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_oslo.py
#
# Description: List of quotes from http://www.oslobors.no/ob/vis_aksjer
#
# Developed for iTrade code (http://itrade.sourceforge.net).
#
# Original template for "plug-in" to iTrade is from Gilles Dumortier.
# New code for OSLO is from Michel Legrand.
#
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

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_defs import *
from itrade_ext import *
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_OSLO()
#
# ============================================================================

def Import_ListOfQuotes_OSLO(quotes,market='OSLO EXCHANGE',dlg=None,x=0):
    print 'Update %s list of symbols' % market
    connection=ITradeConnection(cookies=None,
                                proxy=itrade_config.proxyHostname,
                                proxyAuth=itrade_config.proxyAuthentication)

    if market=='OSLO EXCHANGE':
        url = "http://www.oslobors.no/ob/vis_aksjer"
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
        debug('Import_ListOfQuotes_OSLO:unable to connect :-(')
        return False

    # returns the data
    lines = splitLines(data)

    count = 0
    nlines = 0
    i = 1

    for line in lines:

        #typical lines:
        #<a href="/ob/aksje_kursutvikling?menu2show=1.1.2.1.&p_instrid=ticker.ose.ASC" target="_top">ABG Sundal Collier</a>
        #</p>
        #</td><td>
        #<p style="text-align:left;">NO0003021909</p>
        # extract data

        if i==1:
            ch ='<a href="/ob/aksje_kursutvikling?menu2show=1.1.2.1.&p_instrid=ticker.ose.'
            if ch == line[:len(ch)]:
                i = 1 - i
                ch = line.strip()
                ch = ch[73:-4]
                ticker = ch[:ch.index('"')]
                name = ch[ch.index('>')+1:]
                #print name,type(name)
                name = name.replace('&amp;','&')
                name = name.replace('&aelig;','ae')#Æ
                name = name.replace('&oslash;','o')#ø
                name = name.replace('&Oslash;','O')#Ø
                #name = name.upper()
                #print name

        elif i==0:
            ch ='<p style="text-align:left;">'
            if ch == line[:len(ch)]:
                i = 1 - i
                ch = line.strip()
                isin = ch[28:-4]
                #print isin

                # ok to proceed

                quotes.addQuote(isin=isin,name=name, \
                ticker=ticker,market='OSLO EXCHANGE',currency='NOK',place='OSL',country='NO')
                count = count + 1

                nlines = nlines + 1

    print 'Imported %d/%d lines from OSLO EXCHANGE data.' % (count,nlines)

    return True

# ============================================================================
# Export me
# ============================================================================

registerListSymbolConnector('OSLO EXCHANGE','OSL',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_OSLO)

# ============================================================================
# Test ME
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_OSLO(quotes,'OSLO EXCHANGE')
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
