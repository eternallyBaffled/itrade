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
# 2006-02-2x    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import re
import string

from pytz import timezone

# iTrade system
from itrade_logging import *
from itrade_local import message
import itrade_csv
from itrade_defs import *
from itrade_connection import ITradeConnection
import itrade_config

# ============================================================================
# ISIN -> MARKET
# ============================================================================

isin_market = {
    'fr': 'EURONEXT',
    'nl': 'EURONEXT',
    'be': 'EURONEXT',
    'pt': 'EURONEXT',
    'qs': 'EURONEXT',
    'it': 'EURONEXT',
    'uk': 'LSE SETS',
    'us': 'NASDAQ',
    'au': 'ASX',
    'ca': 'TORONTO EXCHANGE',
    'ch': 'SWISS EXCHANGE',
    'it': 'MILAN EXCHANGE',
    'ie': 'IRISH EXCHANGE',
    'es': 'MADRID EXCHANGE',
    'de': 'FRANKFURT EXCHANGE',
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
# MARKET -> Default INDICE
# ============================================================================

market_indice = {
    'EURONEXT': 'FR0003502079',
    'ALTERNEXT': 'QS0011040902',
    'PARIS MARCHE LIBRE': 'FR0003500008',
    'BRUXELLES MARCHE LIBRE': 'BE0389555039',
    'NASDAQ': 'US6289081050',
    'NYSE': 'US2605661048',
    'AMEX': 'US6488151084',
    'OTCBB': 'US6488151084',
    'LSE SETS': 'US2605661048',
    'LSE SETSmm': 'US2605661048',
    'LSE SEAQ': 'US2605661048',
    'ASX': 'US2605661048',
    'TORONTO EXCHANGE': 'US2605661048',
    'TORONTO VENTURE': 'US2605661048',
    'MILAN EXCHANGE': 'IT0003137749',
    'SWISS EXCHANGE': 'CH0009980894',
    'IRISH EXCHANGE': 'IE0001477250',
    'MADRID EXCHANGE': 'ES0SI0000005',
    'FRANKFURT EXCHANGE': 'DE0008469008',
    }

def getDefaultIndice(market):
    if market_indice.has_key(market):
        return market_indice[market]
    else:
        # default to CAC
        return 'FR0003500008'

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
    'LSE SETS': 'GBP',
    'LSE SETSmm': 'GBP',
    'LSE SEAQ': 'GBP',
    'ASX': 'AUD',
    'TORONTO EXCHANGE': 'CAD',
    'TORONTO VENTURE': 'CAD',
    'MILAN EXCHANGE': 'EUR',
    'SWISS EXCHANGE': 'CHF',
    'IRISH EXCHANGE': 'EUR',
    'MADRID EXCHANGE': 'EUR',
    'FRANKFURT EXCHANGE': 'EUR',
    }

def market2currency(market):
    if market_currency.has_key(market):
        return market_currency[market]
    else:
        # default to EURO
        return 'EUR'

# ============================================================================
# list_of_markets
# ============================================================================

_lom = {
    'EURONEXT' : False,
    'ALTERNEXT': False,
    'PARIS MARCHE LIBRE': False,
    'BRUXELLES MARCHE LIBRE': False,
    'LSE SETS': False,
    'LSE SETSmm': False,
    'LSE SEAQ': False,
    'NASDAQ': False,
    'NYSE': False,
    'AMEX': False,
    'OTCBB': False,
    'ASX': False,
    'TORONTO EXCHANGE': False,
    'TORONTO VENTURE': False,
    'MILAN EXCHANGE': False,
    'SWISS EXCHANGE': False,
    'IRISH EXCHANGE': False,
    'MADRID EXCHANGE': False,
    'FRANKFURT EXCHANGE': False,
    }

def set_market_loaded(market,set=True):
    if _lom.has_key(market):
        _lom[market] = set
    if itrade_config.verbose:
        print 'Load market %s' % market

def unload_markets():
    for market in _lom.keys():
        _lom[market] = False

def is_market_loaded(market):
    if _lom.has_key(market):
        return _lom[market]
    else:
        return False

def list_of_markets(ifLoaded=False,bFilterMode=False):
    lom = []
    if bFilterMode:
        lom.append(message('all_markets'))
    keys = _lom.keys()
    keys.sort()
    for market in keys:
        if not ifLoaded or _lom[market]:
            lom.append(market)
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
            if place=='LIS': return 'PT'
            return 'FR'
        if market=='PARIS MARCHE LIBRE':
            return 'FR'
        if market=='BRUXELLES MARCHE LIBRE':
            return 'BE'
        if market=='LSE SETS' or market=='LSE SETSmm' or market=='LSE SEAQ':
            return 'GB'
        if market=='NASDAQ':
            return 'US'
        if market=='AMEX':
            return 'US'
        if market=='NYSE':
            return 'US'
        if market=='OTCBB':
            return 'US'
        if market=='ASX':
            return 'AU'
        if market=='TORONTO EXCHANGE' or market=='TORONTO VENTURE':
            return 'CA'
        if market=='SWISS EXCHANGE':
            return 'CH'
        if market=='MILAN EXCHANGE':
            return 'IT'
        if market=='IRISH EXCHANGE':
            return 'IE'
        if market=='MADRID EXCHANGE':
            return 'ES'
        if market=='FRANKFURT EXCHANGE':
            return 'DE'
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
        lop.append('BRU')
        lop.append('AMS')
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
    if market=='LSE SETS':
        lop.append('LON')
    if market=='LSE SETSmm':
        lop.append('LON')
    if market=='LSE SEAQ':
        lop.append('LON')
    if market=='ASX':
        lop.append('SYD')
    if market=='TORONTO EXCHANGE' or market=='TORONTO VENTURE':
        lop.append('TOR')
    if market=='SWISS EXCHANGE':
        lop.append('XSWX')
        lop.append('XVTX')
    if market=='MILAN EXCHANGE':
        lop.append('MIL')
    if market=='IRISH EXCHANGE':
        lop.append('DUB')
    if market=='MADRID EXCHANGE':
        lop.append('MAD')
    if market=='FRANKFURT EXCHANGE':
        lop.append('FRA')
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
    'LSE SETS': 'LON',
    'LSE SETSmm': 'LON',
    'LSE SEAQ': 'LON',
    'ASX': 'SYD',
    'TORONTO EXCHANGE': 'TOR',
    'TORONTO VENTURE': 'TOR',
    'MILAN EXCHANGE': 'MIL',
    'SWISS EXCHANGE': 'XVTX',
    'IRISH EXCHANGE': 'DUB',
    'MADRID EXCHANGE': 'MAD',
    'FRANKFURT EXCHANGE': 'FRA',
    }

def market2place(market):
    if market_place.has_key(market):
        return market_place[market]
    else:
        # default to PARIS
        return 'PAR'

# ============================================================================
# convertMarketTimeToPlaceTime
#
#   mtime = HH:MM:ss
#   zone = timezone for the data of the connector (see pytz for all_timezones)
#   place = place of the market
# ============================================================================

place_timezone = {
    "PAR":  "Europe/Paris",
    "BRU":  "Europe/Brussels",
    "MAD":  "Europe/Madrid",
    "AMS":  "Europe/Amsterdam",
    "LON":  "Europe/London",
    "NYC":  "America/New_York",
    "SYD":  "Australia/Sydney",
    "DUB":  "Europe/Dublin",
    "FRA":  "Europe/Berlin",
    "TOR":  "America/Toronto",
    "LIS":  "Europe/Lisbon",
    "MIL":  "Europe/Rome",
    "XSWX": "Europe/Zurich",
    "XVTX": "Europe/Zurich",
    }

def convertConnectorTimeToPlaceTime(mdatetime,zone,place):
    #fmt = '%Y-%m-%d %H:%M:%S %Z%z'

    market_tz = timezone(zone)
    place_tz  = timezone(place_timezone[place])

    market_dt = market_tz.localize(mdatetime)
    #print '*** market time:',market_dt.strftime(fmt)
    place_dt  = place_tz.normalize(market_dt.astimezone(place_tz))
    #print '*** place time:',place_dt.strftime(fmt)

    return place_dt

# ============================================================================
# yahooTicker
# ============================================================================

yahoo_suffix = {
    'EURONEXT.PAR': '.PA',
    'EURONEXT.AMS': '.AS',
    'ALTERNEXT.PAR': '.PA',
    'PARIS MARCHE LIBRE.PAR': '.PA',
    'OTCBB.NYC': '.OB',
    'LSE SETS.LON': '.L',
    'LSE SETSmm.LON': '.L',
    'LSE SEAQ.LON': '.L',
    'ASX.SYD': '.AX',
    'TORONTO EXCHANGE.TOR': '.TO',
    'TORONTO VENTURE.TOR': '.V',
    'MILAN EXCHANGE.MIL': '.MI',
    'SWISS EXCHANGE.XSWX': '.SW',
    'SWISS EXCHANGE.XVTX': '.VX',
    'IRISH EXCHANGE.DUB': '.IR',
    'MADRID EXCHANGE.MAD': '.MC',
    'FRANKFURT EXCHANGE.FRA': '.F',
    }

yahoo_map_tickers = {}

def yahooTicker(ticker,market,place):
    # special case for US markets
    if ticker[0:1] == '^':
        return ticker

    pticker = ticker

    # special case for TORONTO
    if market=='TORONTO EXCHANGE' or market=='TORONTO VENTURE':
        s = ticker.split('-')
        if len(s)==3:
            ticker = s[0]+'-'+s[1]+s[2]

    # special case for AMEX
    if market=="AMEX":
        s = ticker.split('.')
        if len(s)==2:
            ticker = s[0]+'-'+s[1]
            if s[1]=="W":
                ticker = ticker + "T"
        else:
            s = ticker.split('-')
            if len(s)==2:
                ticker= s[0]+'-P'+s[1]

    if pticker!=ticker and itrade_config.verbose:
        print 'convert to Yahoo ticker %s -> %s' % (pticker,ticker)

    # build the ticker using the suffix
    key = market + '.' + place
    if yahoo_suffix.has_key(key):
        sticker = ticker + yahoo_suffix[key]
    else:
        sticker = ticker

    # check if we need to translate to something different !
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
# yahooUrl
#
# some marketplaces seems to use various URL from Yahoo website :-(
# ============================================================================

def yahooUrl(market,live):
    if live:
        if market in ['TORONTO VENTURE','TORONTO EXCHANGE']:
            url = "http://download.finance.yahoo.com/d/quotes.csv"
        else:
            url = "http://quote.yahoo.com/download/quotes.csv"
    else:
        if market in ['TORONTO VENTURE','TORONTO EXCHANGE']:
            url = 'http://download.finance.yahoo.com/d/quotes.csv'
        else:
            url = 'http://ichart.finance.yahoo.com/table.csv'

    return url

# ============================================================================
# euronext_IntrusmentId()
# ============================================================================

def euronext_InstrumentId(quote):

    deprecated

    #
    if quote.list()==QLIST_INDICES:
        urlid = 'http://www.euronext.com/quicksearch/resultquicksearchindices-7000-EN.html?matchpattern=%s&fromsearchbox=true&path=/quicksearch&searchTarget=quote'
    else:
        urlid = 'http://www.euronext.com/quicksearch/resultquicksearch-2986-EN.html?matchpattern=%s&fromsearchbox=true&path=/quicksearch&searchTarget=quote'

    connection = ITradeConnection(cookies = None,
                               proxy = itrade_config.proxyHostname,
                               proxyAuth = itrade_config.proxyAuthentication,
                               connectionTimeout = itrade_config.connectionTimeout
                               )

    # get instrument ID
    IdInstrument = quote.get_pluginID()
    if IdInstrument == None:

        try:
            f = open(os.path.join(itrade_config.dirCacheData,'%s.id' % quote.key()),'r')
            IdInstrument = f.read().strip()
            f.close()
            #print "euronext_InstrumentId: get id from file for %s " % quote.isin()
        except IOError:
            #print "euronext_InstrumentId: can't get id file for %s " % quote.isin()
            pass

        if IdInstrument == None:
            url = urlid % quote.isin()

            if itrade_config.verbose:
                print "euronext_InstrumentId: urlID=%s " % url

            try:
                buf=connection.getDataFromUrl(url)
            except:
                print 'euronext_InstrumentId: %s exception error' % url
                return None
            sid = re.search("selectedMep=%d&amp;idInstrument=\d*&amp;isinCode=%s" % (euronext_place2mep(quote.place()),quote.isin()),buf,re.IGNORECASE|re.MULTILINE)
            if sid:
                sid = buf[sid.start():sid.end()]
                #print'seq-1 found:',sid
                sexch = re.search("&amp;isinCode",sid,re.IGNORECASE|re.MULTILINE)
                if sexch:
                    IdInstrument = sid[31:sexch.start()]
                    #print 'seq-2 found:',IdInstrument
                else:
                    print 'euronext_InstrumentId: seq-2 not found : &amp;isinCode'
            else:
                print 'euronext_InstrumentId: seq-1 not found : selectedMep=%d&amp;idInstrument=\d*&amp;isinCode=%s' % (euronext_place2mep(quote.place()),quote.isin())
                #print buf
                #exit(0)

        if IdInstrument == None:
            print "euronext_InstrumentId:can't get IdInstrument for %s " % quote.isin()
            return None
        else:
            if itrade_config.verbose:
                print "euronext_InstrumentId: IdInstrument for %s is %s" % (quote.isin(),IdInstrument)
            quote.set_pluginID(IdInstrument)
            try:
                f = open(os.path.join(itrade_config.dirCacheData,'%s.id' % quote.key()),'w')
                f.write('%s' % IdInstrument)
                f.close()
            except IOError:
                #print "euronext_InstrumentId: can't write id file for %s " % quote.isin()
                pass

    return IdInstrument

# ============================================================================
# That's all folks !
# ============================================================================
