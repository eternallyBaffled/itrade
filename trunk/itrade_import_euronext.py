#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_import_euronext.py
#
# Description: Import quotes from euronext.com
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
# 2006-11-01    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import re
import string
import urllib
from datetime import *

# iTrade system
from itrade_logging import *
from itrade_quotes import *
from itrade_datation import Datation,jjmmaa2yyyymmdd
from itrade_import import registerImportConnector
from itrade_market import euronext_place2mep

# ============================================================================
# Import_euronext()
#
# ============================================================================

class Import_euronext(object):
    def __init__(self):
        debug('Import_euronext:__init__')
        self.m_urlid = 'http://www.euronext.com/trader/summarizedmarket/0,5372,1732_6834,00.html?isinCode='
        self.m_url = 'http://www.euronext.com/tools/datacentre/dataCentreDownloadExcell/0,5822,1732_2276422,00.html'

    def name(self):
        return 'euronext'

    def interval_year(self):
        return 2

    def connect(self):
        return True

    def disconnect(self):
        pass

    def getstate(self):
        return True

    def parseDate(self,d):
        return (d.year, d.month, d.day)

    def parseFValue(self,d):
        val = string.split(d,',')
        ret = ''
        for val in val:
            ret = ret+val
        return string.atof(ret)

    def parseLValue(self,d):
        val = string.split(d,',')
        ret = ''
        for val in val:
            ret = ret+val
        return string.atol(ret)

    def splitLines(self,buf):
        lines = string.split(buf, '\n')
        lines = filter(lambda x:x, lines)
        def removeCarriage(s):
            if s[-1]=='\r':
                return s[:-1]
            else:
                return s
        lines = [removeCarriage(l) for l in lines]
        return lines

    def getdata(self,quote,datedebut=None,datefin=None):
        # get instrument ID
        IdInstrument = quote.get_pluginID()
        if IdInstrument==None:

            url = self.m_urlid+quote.isin()

            debug("Import_euronext:getdata: urlID=%s ",url)
            try:
                f = urllib.urlopen(url)
            except:
                debug('Import_euronext:unable to connect :-(')
                return None
            buf = f.read()
            sid = re.search("isinCode=%s&selectedMep=%d&idInstrument=" % (quote.isin(),euronext_place2mep(quote.place())),buf,re.IGNORECASE|re.MULTILINE)
            if sid:
                sid = sid.end()
                sexch = re.search("&quotes=stock",buf[sid:],re.IGNORECASE|re.MULTILINE)
                if sexch:
                    sexch = sexch.start()
                    data = buf[sid:]
                    IdInstrument = data[:sexch]

            if IdInstrument==None:
                print "Import_euronext:can't get IdInstrument for %s " % quote.isin()
                return None
            else:
                quote.set_pluginID(IdInstrument)

        # get historic data itself !
        if not datefin:
            datefin = date.today()

        if not datedebut:
            datedebut = date.today()

        if isinstance(datedebut,Datation):
            datedebut = datedebut.date()

        if isinstance(datefin,Datation):
            datefin = datefin.date()

        d1 = self.parseDate(datedebut)
        d2 = self.parseDate(datefin)

        debug("Import_euronext:getdata quote:%s begin:%s end:%s" % (quote,d1,d2))

        query = (
            ('idInstrument', IdInstrument),
            ('isinCode', quote.isin()),
            ('indexCompo', ''),
            ('opening', 'on'),
            ('high', 'on'),
            ('low', 'on'),
            ('closing', 'on'),
            ('volume', 'on'),
            ('dateFrom', '%02d/%02d/%04d' % (d1[2],d1[1],d1[0])),
            ('dateTo', '%02d/%02d/%04d' % (d2[2],d2[1],d2[0])),
            ('typeDownload', '2'),
            ('format', ''),
        )
        query = map(lambda (var, val): '%s=%s' % (var, str(val)), query)
        query = string.join(query, '&')
        url = self.m_url + '?' + query

        debug("Import_euronext:getdata: url=%s ",url)
        try:
            f = urllib.urlopen(url)
        except:
            debug('Import_euronext:unable to connect :-(')
            return None

        # pull data
        buf = f.read()
        lines = self.splitLines(buf)
        data = ''
        #print lines

        for eachLine in lines:
            sdata = string.split (eachLine, '\t')
            if len(sdata)==6:
                if (sdata[0]<>"Date"):
                    #print sdata
                    sdate = jjmmaa2yyyymmdd(sdata[0])
                    open = self.parseFValue(sdata[1])
                    high = self.parseFValue(sdata[2])
                    low = self.parseFValue(sdata[3])
                    value = self.parseFValue(sdata[4])
                    volume = self.parseLValue(sdata[5])

                    # encode in EBP format
                    # ISIN;DATE;OPEN;HIGH;LOW;CLOSE;VOLUME
                    line = (
                      quote.key(),
                      sdate,
                      open,
                      high,
                      low,
                      value,
                      volume
                    )
                    line = map(lambda (val): '%s' % str(val), line)
                    line = string.join(line, ';')
                    #print line

                    # append
                    data = data + line + '\r\n'
        return data

# ============================================================================
# Export me
# ============================================================================

try:
    ignore(gImportEuronext)
except NameError:
    gImportEuronext = Import_euronext()

registerImportConnector('EURONEXT','PAR',gImportEuronext,bDefault=True)
registerImportConnector('EURONEXT','BRU',gImportEuronext,bDefault=True)
registerImportConnector('EURONEXT','AMS',gImportEuronext,bDefault=True)
registerImportConnector('EURONEXT','LIS',gImportEuronext,bDefault=True)
registerImportConnector('ALTERNEXT','PAR',gImportEuronext,bDefault=True)
registerImportConnector('ALTERNEXT','BRU',gImportEuronext,bDefault=True)
registerImportConnector('PARIS MARCHE LIBRE','PAR',gImportEuronext,bDefault=True)
registerImportConnector('BRUXELLES MARCHE LIBRE','BRU',gImportEuronext,bDefault=True)

# ============================================================================
# Test ME
#
# ============================================================================

def test(ticker,d):
    if gImportEuronext.connect():

        state = gImportEuronext.getstate()
        if state:
            debug("state=%s" % (state))

            quote = quotes.lookupTicker(ticker)
            data = gImportEuronext.getdata(quote,d)
            if data!=None:
                if data:
                    debug(data)
                else:
                    debug("nodata")
            else:
                print "getdata() failure :-("
        else:
            print "getstate() failure :-("

        gImportEuronext.disconnect()
    else:
        print "connect() failure :-("

if __name__=='__main__':
    setLevel(logging.INFO)

    # never failed - fixed date
    print "15/03/2005"
    test('OSI',date(2005,03,15))

    # never failed except week-end
    print "yesterday-today :-("
    test('OSI',date.today()-timedelta(1))

    # always failed
    print "tomorrow :-)"
    test('OSI',date.today()+timedelta(1))


# ============================================================================
# That's all folks !
# ============================================================================
