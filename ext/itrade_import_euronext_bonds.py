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
# New code for euronext_bonds is from Michel Legrand.
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
# 2006-11-01    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from __future__ import absolute_import
import logging
import time
import six.moves.urllib.request, six.moves.urllib.error, six.moves.urllib.parse
from contextlib import closing
from datetime import date, timedelta

# iTrade system
from itrade_logging import setLevel, debug
from itrade_quotes import quotes
from itrade_datation import Datation, jjmmaa2yyyymmdd
from itrade_defs import QList, QTag
from itrade_ext import gImportRegistry
from itrade_market import euronextmic
from itrade_connection import ITradeConnection
import itrade_config

# ============================================================================
# Import_euronext_bonds()
#
# ============================================================================

class Import_euronext_bonds(object):
    def __init__(self):
        debug('Import_euronext_bonds:__init__')
        self.m_url = 'https://bonds.nyx.com/en/popup/data/download?ml=nyx_pd_bonds&cmd=default&formKey=nyx_pd_filter_values%3Acddaabb01525e7a66f50cd7f51ece3dd'

        self.m_connection = ITradeConnection(cookies = None,
                                           proxy = itrade_config.proxyHostname,
                                           proxyAuth = itrade_config.proxyAuthentication,
                                           connectionTimeout = itrade_config.connectionTimeout
                                           )

    def name(self):
        return 'euronext_bonds'

    def interval_year(self):
        return 2

    def connect(self):
        return True

    def disconnect(self):
        pass

    def getstate(self):
        return True

    def parseDate(self, d):
        return (d.year, d.month, d.day)

    def parseFValue(self, d):
        val = d.split(',')
        ret = ''
        for val in val:
            ret = ret + val
        return float(ret)

    def parseLValue(self, d):
        if d == '-':
            return 0
        if ',' in d:
            s = ','
        else:
            s = '\xA0'
        val = d.split(s)
        ret = ''
        for val in val:
            ret = ret + val
        return int(ret)

    def splitLines(self, buf):
        lines = buf.split('\n')
        lines = [x for x in lines if x]
        def removeCarriage(s):
            if s[-1] == '\r':
                return s[:-1]
            else:
                return s
        lines = [removeCarriage(l) for l in lines]
        return lines

    def getdata(self, quote, datedebut=None, datefin=None):
        #IdInstrument = euronext_InstrumentId(quote)
        #if IdInstrument == None: return None

        # get historic data itself !
        if not datefin:
            datefin = date.today()

        if not datedebut:
            datedebut = date.today()

        if isinstance(datedebut, Datation):
            datedebut = datedebut.date()

        if isinstance(datefin, Datation):
            datefin = datefin.date()

        d1 = self.parseDate(datedebut)
        d2 = self.parseDate(datefin)

        mic = euronextmic(quote.market(), quote.place())

        format = '%Y-%m-%d %H:%M:%S'
        #origin = "1970-01-01 00:00:00"
        datefrom = str(datedebut) + " 02:00:00"
        dateto = str(datefin) + " 23:00:00"
        datefrom = time.mktime(time.strptime(datefrom, format))
        datefromurl = str(int(datefrom/100))+'00000'
        dateto = time.mktime(time.strptime(dateto, format))
        datefinurl = str(int(dateto)/100)+'00000'
        endurl = 'typefile=csv&layout=vertical&typedate=dmy&separator=comma&mic={}&isin={}&name=&namefile=Price_Data_Historical&from={}&to={}&adjusted=1&base=0'.format(mic, quote.isin(), datefromurl, datefinurl)

        debug(u"Import_euronext_bonds:getdata quote:{} begin:{} end:{}".format(quote, d1, d2))

        query = (
            ('typefile', 'csv'),
            ('layout', 'vertical'),
            ('typedate', 'dmy'),
            ('separator', 'comma'),
            ('mic', mic),
            ('isin', quote.isin()),
            ('name', ''),
            ('namefile', 'Price_Data_Historical'),
            ('from', datefromurl),
            ('to', datefinurl),
            ('adjusted', '1'),
            ('base', '0'),
        )

        query = [u'{}={}'.format(var_val[0], str(var_val[1])) for var_val in query]
        query = '&'.join(query)
        url = self.m_url + '?' + query
        #print(url)
        debug("Import_euronext_bonds:getdata: url=%s ",url)
        try:
            req = six.moves.urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.5) Gecko/20041202 Firefox/1.0')

            with closing(six.moves.urllib.request.urlopen(req)) as f:
                buf = f.read()

            #buf=self.m_connection.getDataFromUrl(url)
        except Exception:
            debug('Import_euronext_bonds:unable to connect :-(')
            return None

        # pull data
        lines = self.splitLines(buf)
        data = ''
        #print(lines)

        for eachLine in lines[4:]:
            eachLine = eachLine.replace('","', ';')
            eachLine = eachLine.replace('"', '')
            sdata = eachLine.split(';')

            if len(sdata) == 11:
                #print(sdata)
                #if (sdata[0] != "Date") and (quote.list() == QList.indices):
                sdate = jjmmaa2yyyymmdd(sdata[2])
                open = self.parseFValue(sdata[3].replace(',', '.'))
                print('open:',open)
                high = self.parseFValue(sdata[4].replace(',', '.'))
                low = self.parseFValue(sdata[5].replace(',', '.'))
                value = self.parseFValue(sdata[6].replace(',', '.'))
                volume = self.parseLValue(sdata[7])
                #print quote.key(),sdate,open,high,low,value,volume

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
                line = [str(val) for val in line]
                line = ';'.join(line)
                #print line

                # append
                data = data + line + '\r\n'
        return data

# ============================================================================
# Export me
# ============================================================================


gImportEuronext = Import_euronext_bonds()


gImportRegistry.register('EURONEXT', 'PAR', QList.bonds, QTag.imported, gImportEuronext, bDefault=True)
gImportRegistry.register('EURONEXT', 'BRU', QList.bonds, QTag.imported, gImportEuronext, bDefault=True)
gImportRegistry.register('EURONEXT', 'AMS', QList.bonds, QTag.imported, gImportEuronext, bDefault=True)
gImportRegistry.register('EURONEXT', 'LIS', QList.bonds, QTag.imported, gImportEuronext, bDefault=True)


# ============================================================================
# Test ME
#
# ============================================================================

def test(ticker, d):
    if gImportEuronext.connect():
        state = gImportEuronext.getstate()
        if state:
            debug(u"state={}".format(state))

            quote = quotes.lookupTicker(ticker=ticker, market='EURONEXT')
            data = gImportEuronext.getdata(quote, d)
            if data is not None:
                if data:
                    debug(data)
                else:
                    debug("nodata")
            else:
                print("getdata() failure :-(")
        else:
            print("getstate() failure :-(")

        gImportEuronext.disconnect()
    else:
        print("connect() failure :-(")

if __name__ == '__main__':
    setLevel(logging.INFO)

    quotes.loadMarket('EURONEXT')

    # never failed - fixed date
    print("15/03/2005")
    test('OSI', date(2005, 3, 15))

    # never failed except weekend
    print("yesterday-today :-(")
    test('OSI', date.today() - timedelta(1))

    # always failed
    print("tomorrow :-)")
    test('OSI', date.today() + timedelta(1))


# ============================================================================
# That's all folks !
# ============================================================================
