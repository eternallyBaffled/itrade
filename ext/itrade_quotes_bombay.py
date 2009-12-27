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
        starturl = 'http://test.bseindia.com/scripsearch/scrips.aspx?myScrip='
        endurl = '&flag=sr'
    else:

        return False

    def splitLines(buf):
        lines = string.split(buf, '/n')
        lines = filter(lambda x:x, lines)
        def removeCarriage(s):
            if s[-1]=='\r':
                return s[:-1]
            else:
                return s
        lines = [removeCarriage(l) for l in lines]
        return lines
    
    select_alpha = ['20MICRONS','3IINFOTECH','3MINDIA','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
    n = 0
    isin = ''


    for letter in select_alpha:
        
        url = starturl+letter+endurl

        try:
            data=connection.getDataFromUrl(url)
        except:
            debug('Import_ListOfQuotes_BSE unable to connect :-(')
            return False
        data = data.replace("cellpadding=0 width='100%'><tr><td class='tbmain'><a href=",'/n')
        # returns the data
        lines = splitLines(data)


        for line in lines:
            
            if 'scripcode=' in line:
                if '>#</td></tr>' in line or '>@</td></tr>' in line :
                    #Suspended due to penal reasons
                    #Suspended due to procedural reasons
                    
                    pass
                else :
                    #scrip_cd = line[(line.find("scripcode=")+10):(line.find ('"'))]
                    name = line[(line.find('>')+1):(line.find ('</a></td><td'))]

                    if 'Fund' in name or 'Maturity' in name :
                        pass
                    else :
                        ticker = line[(line.find('<u>')+3):(line.find ('</u>'))]
                        n = n + 1
                        
                        #Partial activation of the Progressbar
                        dlg.Update(x,'B S E : %s /~3400' %n)

                        quotes.addQuote(isin=isin,name=name, \
                            ticker=ticker,market='BOMBAY EXCHANGE',currency='INR',place='BSE',country='IN')

                    

    print 'Imported %d lines from BOMBAY EXCHANGE data.' %n

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
