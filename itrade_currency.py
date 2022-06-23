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
from __future__ import print_function

from __future__ import absolute_import
import itertools
import logging
import os

# iTrade system
import itrade_logging
import itrade_csv
from itrade_connection import ITradeConnection
import itrade_config

# ============================================================================
# currency <-> symbol conversion
#
#   currency2symbol
# ============================================================================

currencies_CUR = {
    'EUR': u'\u20AC',  # " '€',
    'USD': u'\u0024',  # '$'
    'CAD': u'\u0024',  # '$'
    'JPY': u'\u00A5',  # '¥',
    'GBP': u'\u00A3',  # '£',
    'GBX': u'\u0070',  # 'p',
    'AUD': u'\u0024',  # '$'
    'CHF': u'\u0046',  # 'F'
    'NOK': u'\u006B\u0072',  # 'Kr'
    'SEK': u'\u006B\u0072',  # 'Kr'
    'DKK': u'\u006B\u0072',  # 'Kr'
    'BRL': u'\u0052\u0024\u0020',  # 'R$'
    'HKD': u'\u0048\u004B\u0024',  # 'HK$'
    'CNY': u'\uFFE5',  # '¥'
    'INR': u'\u0930\u0941',  # ''
    'NZD': u'\u0024',  # '$'
    'ARS': u'\u0024',  # '$'
    'MXN': u'\u0024',  # '$'
    'SGD': u'\u0024',  # '$'
    'KRW': u'\uFFE6',  # 'w  u20A9 character not accepted'
    'TWD': u'\u004E\u0054\u0024',  # 'NT$'
    'N/A': u'\u0020',  # ' '
    }


def currency2symbol(cur):
    return currencies_CUR.get(cur, cur)


def list_of_currencies():
    return ['EUR', 'USD', 'JPY', 'GBP', 'GBX', 'AUD', 'CAD', 'CHF', 'NOK', 'SEK', 'DKK', 'BRL', 'HKD', 'CNY', 'INR', 'NZD', 'ARS', 'MXN', 'SGD', 'KRW', 'TWD']

# ============================================================================
# Build list of supported currencies
# ============================================================================

def buildListOfSupportedCurrencies():
    return itertools.product(currencies_CUR, repeat=2)

# ============================================================================
# Currencies
# ============================================================================
#
# CSV File format :
#   TO;FROM;RATE
# ============================================================================

class Currencies(object):
    def __init__(self):
        self.m_url = 'https://finance.yahoo.com/d/quotes.csv?s={}{}=X&f=s4l1t1c1ghov&e=.csv'
#'https://query1.finance.yahoo.com/v7/finance/download/EURUSD=X?period1=1622993794&period2=1654529794&interval=1d&events=history&includeAdjustedClose=true'
        self.m_connection = None

        # to-from
        self.m_currencies = {}
        self.m_list = buildListOfSupportedCurrencies()
        for curTo, curFrom in self.m_list:
            self.update(curTo, curFrom, 1.0)

    def list(self):
        return self.m_list

    # ---[ Load / Save cache file ] ---

    def update(self, curTo, curFrom, rate):
        if curFrom == 'N/A' or curTo == 'N/A':
            return rate
        if curTo == curFrom:
            return rate
        key = self._key(curTo, curFrom)
        used, _ = self.m_currencies.get(key, (False, rate))
        self.m_currencies[key] = (used, rate)
        return rate

    def load(self, fn=None):
        # open and read the file to load these currencies information
        infile = itrade_csv.read(fn, os.path.join(itrade_config.dirCacheData, 'currencies.txt'))
        # scan each line to read each rate
        for eachLine in infile:
            item = itrade_csv.parse(eachLine, 3)
            if item:
                # logging.debug('{} ::: {}'.format(eachLine, item))
                self.update(item[0], item[1], float(item[2]))

    def save(self, fn=None):
        # generate list of strings TO;FROM;RATE
        curs = []
        for eachCurrency, target in self.m_currencies.items():
            used, rate = target
            curs.append("{};{};{:.8f}".format(eachCurrency[:3], eachCurrency[3:], rate))

        # open and write the file with the currencies information
        itrade_csv.write(fn, os.path.join(itrade_config.dirCacheData, 'currencies.txt'), curs)

    # ---[ Convert ] ---

    def _key(self, curTo, curFrom):
        return curTo.upper() + curFrom.upper()

    def rate(self, curTo, curFrom):
        if curFrom == 'N/A' or curTo == 'N/A':
            return 1.0
        if curTo == curFrom:
            return 1.0
        key = self._key(curTo, curFrom)
        _, rate = self.m_currencies.get(key, (False, 1.0))
        return rate

    def convert(self, curTo, curFrom, Value):
        rate = self.rate(curTo, curFrom)
        # print('convert: value:{:f} from:{} to:{} rate={:f} retval={:f}'.format(Value, curFrom, curTo, rate, Value*rate))
        return Value * rate

    # ---[ Currency in use or not ? ] ---

    def used(self, curTo, curFrom):
        if curFrom == 'N/A' or curTo == 'N/A':
            return False
        if curTo == curFrom:
            return True
        key = self._key(curTo, curFrom)
        used, _ = self.m_currencies.get(key, (False, 1.0))
        return used

    def inuse(self, curTo, curFrom, bInUse):
        if curFrom == 'N/A' or curTo == 'N/A':
            return
        if curTo == curFrom:
            return
        key = self._key(curTo, curFrom)
        if key in self.m_currencies:
            used, rate = self.m_currencies[key]
            self.m_currencies[key] = (bInUse, rate)
            # print('inuse >>> currency : ', key, ' inUse: ', bInUse, ' rate: ', rate)

    def reset(self):
        # print('>>> currency reset')
        for key in self.m_currencies:
            used, rate = self.m_currencies[key]
            self.m_currencies[key] = (False, rate)

    def update_rate(self, dest_currency, org_currency):
        if not self.used(dest_currency, org_currency):
            self.inuse(dest_currency, org_currency, True)
            self.get(dest_currency, org_currency)

    # ---[ Get Last Trade from network ] ---

    _s1 = {"GBX": "GBP", }
    _s2 = {"GBX": 100.0, }

    def get(self, curTo, curFrom):
        if not itrade_config.isConnected():
            return None

        if curFrom == 'N/A' or curTo == 'N/A':
            return None

        if self.m_connection is None:
            self.m_connection = ITradeConnection(cookies=None,
                                                 proxy=itrade_config.proxyHostname,
                                                 proxyAuth=itrade_config.proxyAuthentication,
                                                 connectionTimeout=itrade_config.connectionTimeout
                                                 )
            # print("**** Create Currency Connection")

        # pence
        if curFrom in self._s1:
            a = self._s1[curFrom]
        else:
            a = curFrom
        if curTo in self._s1:
            b = self._s1[curTo]
        else:
            b = curTo

        # get data
        url = self.m_url.format(a, b)
        try:
            buf = self.m_connection.getDataFromUrl(url)
        except Exception:
            return None

        # extract data
        # print(url, buf)
        sdata = buf.split(',')
        f = float(sdata[1])

        # pence
        if curFrom in self._s2:
            f = f / self._s2[curFrom]
        if curTo in self._s2:
            f = f * self._s2[curTo]

        # print('get: {} {} rate = {:.4f}'.format(curTo, curFrom, float(sdata[1])))
        return self.update(curTo, curFrom, f)

    def getlasttrade(self, bAllEvenNotInUse=False):
        if not itrade_config.isConnected():
            return
        for eachCurrency in self.m_currencies:
            cur_to = eachCurrency[:3]
            cur_from = eachCurrency[3:]
            if bAllEvenNotInUse or self.used(cur_to, cur_from):
                self.get(cur_to, cur_from)
        self.save()

# ============================================================================
# Export
# ============================================================================

currencies = Currencies()

currencies.load()

# ============================================================================
# Test
# ============================================================================

def main():
    itrade_config.app_header()
    itrade_logging.setLevel(logging.DEBUG)
    print('From cache file : ')
    print('1 EUR = {:.2f} EUR'.format(currencies.convert('EUR', 'EUR', 1)))
    print('1 EUR = {:.2f} USD'.format(currencies.convert('USD', 'EUR', 1)))
    print('1 USD = {:.2f} EUR'.format(currencies.convert('EUR', 'USD', 1)))
    print('Currencies get last trade ...')
    currencies.inuse('USD', 'EUR', True)
    currencies.inuse('GBX', 'EUR', True)
    currencies.inuse('GBP', 'EUR', True)
    currencies.inuse('USD', 'AUD', True)
    currencies.getlasttrade()
    print('From updated cache file : ')
    print('1 EUR = {:.2f} EUR'.format(currencies.convert('EUR', 'EUR', 1)))
    print('1 EUR = {:.2f} USD'.format(currencies.convert('USD', 'EUR', 1)))
    print('1 EUR = {:.2f} GBP'.format(currencies.convert('GBP', 'EUR', 1)))
    print('1 EUR = {:.2f} GBX'.format(currencies.convert('GBX', 'EUR', 1)))
    print('1 USD = {:.2f} EUR'.format(currencies.convert('EUR', 'USD', 1)))
    print('1 USD = {:.2f} AUD'.format(currencies.convert('AUD', 'USD', 1)))
    # print('EUR = {}'.format(currency2symbol('EUR')))


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
