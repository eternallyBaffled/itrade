#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_market.py
#
# Description: Market management
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
# 2006-02-2x    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging

# iTrade system
from itrade_logging import *
from itrade_local import message
import itrade_csv

# ============================================================================
# ISIN -> MARKET
# ============================================================================

isin_market = {
    'fr': 'EURONEXT',
    'nl': 'EURONEXT',
    'be': 'EURONEXT',
    'es': 'EURONEXT',
    'qs': 'EURONEXT',
    'uk': 'LSE',
    'us': 'NASDAQ'
    }

def isin2market(isin):
    if isin:
        cp = isin[0:2].lower()
        if isin_market.has_key(cp):
            return isin_market[cp]
        else:
            # don't know !
            return None
    else:
        # default to EURONEXT !
        return 'EURONEXT'

# ============================================================================
# MARKET -> CURRENCY
# ============================================================================

market_currency = {
    'EURONEXT': 'EUR',
    'ALTERNEXT': 'EUR',
    'PARIS MARCHE LIBRE': 'EUR',
    'BRUXELLES MARCHE LIBRE': 'EUR',
    'NASDAQ': 'USD',
    'NYSE': 'USD',
    'AMEX': 'USD',
    'OTCBB': 'USD',
    'LSE': 'GBP',
    }

def market2currency(market):
    if market_currency.has_key(market):
        return market_currency[market]
    else:
        # default to EURO
        return 'EUR'

def list_of_markets(bFilterMode=False):
    lom = []
    if bFilterMode:
        lom.append(message('all_markets'))
    lom.append('EURONEXT')
    lom.append('ALTERNEXT')
    lom.append('PARIS MARCHE LIBRE')
    lom.append('BRUXELLES MARCHE LIBRE')
    lom.append('LSE')
    lom.append('NASDAQ')
    lom.append('NYSE')
    lom.append('AMEX')
    lom.append('OTCBB')
    return lom

# ============================================================================
# use isin / market / place to found the country
# ============================================================================

def compute_country(isin,market,place):
    if isin:
        cp = isin[0:2].upper()
        if cp=='QS':
            return 'FR'
        else:
            return cp
    else:
        if market=='EURONEXT' or market=='ALTERNEXT':
            if place=='PAR': return 'FR'
            if place=='BRU': return 'BE'
            if place=='AMS': return 'NL'
            if place=='LIS': return 'ES'
            return 'FR'
        if market=='PARIS MARCHE LIBRE':
            return 'FR'
        if market=='BRUXELLES MARCHE LIBRE':
            return 'BE'
        if market=='LSE':
            return 'GB'
        if market=='NASDAQ':
            return 'US'
        if market=='AMEX':
            return 'US'
        if market=='NYSE':
            return 'US'
        if market=='OTCBB':
            return 'US'
    return '??'

# ============================================================================
# list_of_places
# ============================================================================

def list_of_places(market):
    lop = []
    if market=='EURONEXT':
        lop.append('PAR')
        lop.append('BRU')
        lop.append('AMS')
        lop.append('LIS')
    if market=='ALTERNEXT':
        lop.append('PAR')
    if market=='PARIS MARCHE LIBRE':
        lop.append('PAR')
    if market=='BRUXELLES MARCHE LIBRE':
        lop.append('BRU')
    if market=='NASDAQ':
        lop.append('NYC')
    if market=='AMEX':
        lop.append('NYC')
    if market=='NYSE':
        lop.append('NYC')
    if market=='OTCBB':
        lop.append('NYC')
    if market=='LSE':
        lop.append('LON')
    return lop

# ============================================================================
# market2place
# ============================================================================

market_place = {
    'EURONEXT': 'PAR',
    'ALTERNEXT': 'PAR',
    'PARIS MARCHE LIBRE': 'PAR',
    'BRUXELLES MARCHE LIBRE': 'BRU',
    'NASDAQ': 'NYC',
    'NYSE': 'NYC',
    'AMEX': 'NYC',
    'OTCBB': 'NYC',
    'LSE': 'LON',
    }

def market2place(market):
    if market_place.has_key(market):
        return market_place[market]
    else:
        # default to PARIS
        return 'PAR'

# ============================================================================
# yahooTicker
# ============================================================================

yahoo_suffix = {
    'EURONEXT.PAR': '.PA',
    'EURONEXT.AMS': '.AS',
    'ALTERNEXT.PAR': '.PA',
    'PARIS MARCHE LIBRE.PAR': '.PA',
    'OTCBB.NYC': '.OB',
    'LSE.LON': '.L',
    }

yahoo_map_tickers = {}

def yahooTicker(ticker,market,place):
    key = market + '.' + place
    if yahoo_suffix.has_key(key):
        sticker = ticker + yahoo_suffix[key]
    else:
        sticker = ticker

    if yahoo_map_tickers.has_key(sticker):
        return yahoo_map_tickers[sticker]

    return sticker

infile = itrade_csv.read(None,os.path.join(itrade_config.dirSysData,'yahoo_tickers.txt'))
if infile:
    # scan each line to read each quote
    for eachLine in infile:
        item = itrade_csv.parse(eachLine,2)
        if item:
            yahoo_map_tickers[item[0]] = item[1].strip().upper()

# ============================================================================
# euronext_place2mep
# ============================================================================

euronext_place = {
    'PAR' : 1,
    'AMS' : 2,
    'BRU' : 3,
    'LIS' : 5
    }

def euronext_place2mep(place):
    if euronext_place.has_key(place):
        return euronext_place[place]
    else:
        # default to PARIS
        return 1

# ============================================================================
# That's all folks !
# ============================================================================
