#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_nyse.py
#
# Description: List of quotes from nyse.com : NYSE
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is	Gilles Dumortier.
#
# Portions created by the Initial Developer are Copyright (C) 2004-2007 the
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
# 2005-06-12    dgil  Wrote it from scratch
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
from itrade_isin import buildISIN,extractCUSIP,filterName
from itrade_import import *

# ============================================================================
# Import_ListOfQuotes_NYSE()
#
# ============================================================================

def Import_ListOfQuotes_NYSE(quotes,market='NYSE'):
    print 'Update %s list of symbols' % market

    if market=='NYSE':
        url = "http://www.nysedata.com/nysedata/asp/download.asp?s=txt&prod=symbols"
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
        debug('Import_ListOfQuotes_NYSE:unable to connect :-(')
        return False

    # returns the data
    data = f.read()
    lines = splitLines(data)

    for line in lines:
        data = string.split (line, '|')
        if len(data)==5:
            country,issuer,issue = extractCUSIP(data[1])
            if issue=='10':
                #print data[1],country,issuer,issue,data[2]
                if country=='US':
                    isin = buildISIN(country,data[1])
                    name = filterName(data[2])
                    quotes.addQuote(isin=isin,name=name,ticker=data[0],market='NYSE',currency='USD',place='NYC',country='US')

    print 'Imported %d lines from NYSE data.' % len(lines)

    return True

# ============================================================================
# Export me
# ============================================================================

registerListSymbolConnector('NYSE','NYC',QLIST_ANY,QTAG_LIST,Import_ListOfQuotes_NYSE)

# ============================================================================
# Test ME
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_NYSE(quotes,'NYSE')
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
