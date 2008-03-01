#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_bombay.py
#
# Description: List of quotes from http://www.bseindia.com
#
# Developed for iTrade code (http://itrade.sourceforge.net).
#
# Original template for "plug-in" to iTrade is from Gilles Dumortier.
# New code for BSE is from Michel Legrand.
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
import urllib

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_defs import *
from itrade_ext import *
from itrade_connection import ITradeConnection

# ============================================================================
# Import_ListOfQuotes_BOMBAY()
#
# ============================================================================


def Import_ListOfQuotes_BSE(quotes,market='BOMBAY EXCHANGE',dlg=None,x=0):
    print 'Update %s list of symbols' % market
    connection=ITradeConnection(cookies=None,
                                proxy=itrade_config.proxyHostname,
                                proxyAuth=itrade_config.proxyAuthentication)
    if market=='BOMBAY EXCHANGE':
        beginurl = 'http://www.bseindia.com/datalibrary/disp.asp?flag='
        midurl = '&select_alp='
        endurl = '&curpage='

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

    # symbol list of bombay exchange

    group = ['A','B1','B2','S','T','TS'] #['Z'] no quote in group Z with yahoo
    select_alpha = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','[0-9]']

    nlines = 0
    currentpage = 1


    for groupLetter in group:
        n = 0
        if groupLetter == 'Z': beginurl = 'http://www.bseindia.com/about/datal/disp.asp?';groupLetter='';midurl='select_alp='

        for letter in select_alpha:
            next_page = 0
            count = 0

            while next_page == 0:

                url = beginurl+groupLetter+midurl+letter
                if currentpage>1: url=url+endurl+str(currentpage)

                print
                print 'Import List of Compagnies Group-%s , Letter %s, Page %s' % (groupLetter,letter,currentpage)
                print

                try:
                    source = urllib.urlopen(url)
                except:
                    debug('Import_ListOfQuotes_BSE unable to connect :-(')

                data = source.read()
                data = data.replace('scripcd=','scripcd=\n')

                # returns the data
                lines = splitLines(data)

                for line in lines[1:]:
                    count = count + 1
                    if line.find('href=..') and len(line)>50:
                        ticker = line[:line.index('>')]
                        name = line[len(ticker)+1:line.index('<')]

                        # build isin group
                        n = n + 1
                        newisin = str(n)
                        if len(newisin) == 1: falseisin = groupLetter+'-000000000'+newisin
                        if len(newisin) == 2: falseisin = groupLetter+'-00000000'+newisin
                        if len(newisin) == 3: falseisin = groupLetter+'-0000000'+newisin
                        if len(newisin) == 4: falseisin = groupLetter+'-000000'+newisin
                        if len(groupLetter) == 2: falseisin = falseisin[:3]+falseisin[4:]
                        #fileticker.write(falseisin+';'+name+';'+ticker+endLine+'\n')

                        # ok to proceed
                        falseisin = ''
                        quotes.addQuote(isin=falseisin,name=name, \
                        ticker=ticker,market='BOMBAY EXCHANGE',currency='INR',place='BSE',country='IN')

                        nlines = nlines + 1

                        print name,ticker

                    if line.find('Next')<>-1:
                        next_page = 0
                        count = count + 1
                        currentpage = currentpage + 1
                    else:
                        count=0

                source.close()

                if count == 0: next_page = 1;currentpage = 1






    print 'Imported %d lines from BOMBAY EXCHANGE data.' % (nlines)

    return True

# ============================================================================
# Export me
# ============================================================================

registerListSymbolConnector('BOMBAY EXCHANGE','BSE',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_BSE)

# ============================================================================
# Test ME
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_BSE(quotes,'BOMBAY EXCHANGE')
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
