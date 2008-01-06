#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_currency.py
#
# Description: Currency management
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
# 2006-04-1x    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import string

# iTrade system
from itrade_logging import *
import itrade_csv
from itrade_local import message
from itrade_connection import ITradeConnection
import itrade_config

# ============================================================================
# currency <-> symbol conversion
#
#   currency2symbol
# ============================================================================

currencies_CUR = {
    'EUR' : u'\u20AC', #" '€',
    'USD' : u'\u0024', # '$'
    'CAD' : u'\u0024', # '$'
    'JPY' : u'\u00A5', # '¥',
    'GBP' : u'\u00A3', # '£',
    'GBX' : u'\u0070', # 'p',
    'AUD' : u'\u0024', # '$'
    'CHF' : u'\u0046', # 'F'
    'N/A' : u'\u0020', # ' '
    }

def currency2symbol(cur):
    if currencies_CUR.has_key(cur):
        return currencies_CUR[cur]
    else:
        return cur

def list_of_currencies():
    return ('EUR','USD','JPY','GBP','GBX','AUD','CAD','CHF')

# ============================================================================
# Build list of supported currencies
# ============================================================================

def buildListOfSupportedCurrencies():
    lst = []
    for eachCur1 in currencies_CUR.keys():
        for eachCur2 in currencies_CUR.keys():
            lst.append((eachCur1,eachCur2))
    return lst

# ============================================================================
# Currencies
# ============================================================================
#
# CSV File format :
#   TO;FROM;RATE
# ============================================================================

class Currencies(object):
    def __init__(self):
        # url
        self.m_url = 'http://finance.yahoo.com/d/quotes.csv?s=%s%s=X&f=s4l1t1c1ghov&e=.csv'

        self.m_connection = None

        # to-from
        self.m_currencies = {}
        self.m_list = buildListOfSupportedCurrencies()
        for eachCur in self.m_list:
            curTo,curFrom = eachCur
            self.update(curTo,curFrom,1.0)

    def list(self):
        return self.m_list

    # ---[ Load / Save cache file ] ---

    def update(self,curTo,curFrom,rate):
        if curFrom == 'N/A' or curTo == 'N/A':
            return rate
        if curTo <> curFrom:
            key = self.key(curTo,curFrom)
            if self.m_currencies.has_key(key):
                used,oldrate = self.m_currencies[key]
            else:
                used = False
            self.m_currencies[key] = (used,rate)
        return rate

    def load(self,fn=None):
        # open and read the file to load these currencies information
        infile = itrade_csv.read(fn,os.path.join(itrade_config.dirCacheData,'currencies.txt'))
        if infile:
            # scan each line to read each rate
            for eachLine in infile:
                item = itrade_csv.parse(eachLine,3)
                if item:
                    # debug('%s ::: %s' % (eachLine,item))
                    self.update(item[0],item[1],float(item[2]))

    def save(self,fn=None):
        # generate list of strings TO;FROM;RATE
        curs = []
        for eachCurrency in self.m_currencies:
            used,rate = self.m_currencies[eachCurrency]
            curs.append("%s;%s;%.8f"%(eachCurrency[:3],eachCurrency[3:],rate))

        # open and write the file with these currencies information
        itrade_csv.write(fn,os.path.join(itrade_config.dirCacheData,'currencies.txt'),curs)

    # ---[ Convert ] ---

    def key(self,curTo,curFrom):
        return curTo.upper() + curFrom.upper()

    def rate(self,curTo,curFrom):
        if curFrom == 'N/A' or curTo == 'N/A':
            return 1.0
        if curTo == curFrom:
            return 1.0
        key = self.key(curTo,curFrom)
        if self.m_currencies.has_key(key):
            used,rate = self.m_currencies[key]
            return rate
        else:
            return 1.0

    def convert(self,curTo,curFrom,Value):
        rate = self.rate(curTo,curFrom)
        #print 'convert: value:%f from:%s to:%s rate=%f retval=%f' % (Value,curFrom,curTo,rate,Value*rate)
        return Value * rate

    # ---[ Currency in use or not ? ] ---

    def used(self,curTo,curFrom):
        if curFrom == 'N/A' or curTo == 'N/A':
            return False
        if curTo == curFrom:
            return True
        key = self.key(curTo,curFrom)
        if self.m_currencies.has_key(key):
            used,rate = self.m_currencies[key]
            #print 'used >>> currency : ',key,' inUse: ',used,' rate: ',rate
            return used
        else:
            return False

    def inuse(self,curTo,curFrom,bInUse):
        if curFrom == 'N/A' or curTo == 'N/A':
            return
        if curTo == curFrom:
            return
        key = self.key(curTo,curFrom)
        if self.m_currencies.has_key(key):
            used,rate = self.m_currencies[key]
            self.m_currencies[key] = (bInUse,rate)
            #print 'inuse >>> currency : ',key,' inUse: ',bInUse,' rate: ',rate

    def reset(self):
        #print '>>> currency reset'
        for key in self.m_currencies.keys():
            used,rate = self.m_currencies[key]
            self.m_currencies[key] = (False,rate)

    # ---[ Get Last Trade from network ] ---

    _s1 = { "GBX": "GBP", }
    _s2 = { "GBX": 100.0, }

    def get(self,curTo,curFrom):
        if not itrade_config.isConnected():
            return None

        if curFrom == 'N/A' or curTo == 'N/A':
            return None

        if self.m_connection==None:
            self.m_connection = ITradeConnection(cookies = None,
                               proxy = itrade_config.proxyHostname,
                               proxyAuth = itrade_config.proxyAuthentication,
                               connectionTimeout = itrade_config.connectionTimeout
                               )
            #print "**** Create Currency Connection"

        # pence
        if curFrom in self._s1.keys():
            a = self._s1[curFrom]
        else:
            a = curFrom
        if curTo in self._s1.keys():
            b = self._s1[curTo]
        else:
            b = curTo

        # get data
        url = self.m_url % (a,b)
        try:
            buf = self.m_connection.getDataFromUrl(url)
        except:
            return None

        # extract data
        #print url,buf
        sdata = string.split(buf, ',')
        f = float(sdata[1])

        # pence
        if curFrom in self._s2.keys():
            f = f / self._s2[curFrom]
        if curTo in self._s2.keys():
            f = f * self._s2[curTo]

        #print 'get: %s %s rate = %.4f' %(curTo,curFrom,float(sdata[1]))
        return self.update(curTo,curFrom,f)

    def getlasttrade(self,bAllEvenNotInUse=False):
        if not itrade_config.isConnected():
            return
        for eachCurrency in self.m_currencies:
            curTo = eachCurrency[:3]
            curFrom = eachCurrency[3:]
            if bAllEvenNotInUse or self.used(curTo,curFrom):
                self.get(curTo,curFrom)
        self.save()

# ============================================================================
# Export
# ============================================================================

try:
    ignore(currencies)
except NameError:
    currencies = Currencies()

currencies.load()

convert = currencies.convert

# ============================================================================
# Test
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    print 'From cache file : '
    print '1 EUR = %.2f EUR' % convert('EUR','EUR',1)
    print '1 EUR = %.2f USD' % convert('USD','EUR',1)
    print '1 USD = %.2f EUR' % convert('EUR','USD',1)

    print 'Currencies get last trade ...'
    currencies.inuse('USD','EUR',True)
    currencies.inuse('GBX','EUR',True)
    currencies.inuse('GBP','EUR',True)
    currencies.inuse('USD','AUD',True)
    currencies.getlasttrade()

    print 'From updated cache file : '
    print '1 EUR = %.2f EUR' % convert('EUR','EUR',1)
    print '1 EUR = %.2f USD' % convert('USD','EUR',1)
    print '1 EUR = %.2f GBP' % convert('GBP','EUR',1)
    print '1 EUR = %.2f GBX' % convert('GBX','EUR',1)
    print '1 USD = %.2f EUR' % convert('EUR','USD',1)
    print '1 USD = %.2f AUD' % convert('AUD','USD',1)

    #print 'EUR = %s',currency2symbol('EUR')

# ============================================================================
# That's all folks !
# ============================================================================
