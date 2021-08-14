#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes.py
#
# Description: Quotes
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
# 2004-01-08    dgil  Wrote it from scratch
# 2006-09-2x    dgil  New quote referencing
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function

from datetime import date
import logging
import os
import string
from enum import Enum
from decimal import Decimal

# iTrade system
import itrade_config
from itrade_logging import info, setLevel, debug
from itrade_local import message
import itrade_csv
import itrade_trades
from itrade_import import cmdline_importQuoteFromInternet, import_from_internet, liveupdate_from_internet
from itrade_defs import QList, QTag
from itrade_ext import getImportConnector, getLiveConnector, getDefaultLiveConnector
from itrade_datation import Datation, gCal, date2str
from itrade_market import market2currency, compute_country, market2place, list_of_markets, set_market_loaded, is_market_loaded
import itrade_currency


class QuoteColor(Enum):
    red = 0
    green = 1
    nochange = 2
    invalid = 3


class QuoteType(Enum):
    """type of quote : cash, SRD(credit) or both"""
    no_type = 0
    cash = 1
    credit = 2
    both = 3


# ============================================================================
# volume formatter
# ============================================================================

def _format_volume(x):
    """
    >>> print(_format_volume(1))
    1
    >>> print(_format_volume(12))
    12
    >>> print(_format_volume(130))
    130
    >>> print(_format_volume(1400))
    1 400
    >>> print(_format_volume(15000))
    15 000
    >>> print(_format_volume(160000))
    160 000
    >>> print(_format_volume(1700000))
    1 700 000
    >>> print(_format_volume(18000000))
    18 000 000
    """
    return '{0:n}'.format(Decimal(x))


class Volume(object):
    pass

# ============================================================================
# Quote referencing
# ============================================================================

def quote_reference(isin, ticker, market, place):
    global quote
    # print 'quote_reference: isin={} ticker={} market={} place={}'.format(isin, ticker, market, place)
    if isin and isin != '':
        if market is None or market == '':
            lst = quotes.lookupISIN(isin)
            if len(lst) > 0:
                quote = lst[0]
                market = quote.market()
                place = quote.place()
                return '{}.{}.{}'.format(isin, market, place)
        else:
            if place is None or place == '':
                lst = quotes.lookupISIN(isin, market)
                if len(lst) > 0:
                    quote = lst[0]
                    place = quote.place()
            return '{}.{}.{}'.format(isin, market, place)

    if market is None or market == '':
        quote = quotes.lookupTicker(ticker)
        if quote:
            market = quote.market()
            place = quote.place()
        else:
            market = '?'
            place = '?'

    return '{}.{}.{}'.format(ticker, market, place)

# ============================================================================
# Quote
# ============================================================================

class Quote(object):
    def __init__(self, key, isin, name, ticker, market, currency, place, country, list=QList.system):
        self.m_key = key
        self.m_isin = isin
        self.m_defaultname = name
        self.m_defaultticker = ticker
        self.m_list = list

        if not place:
            self.m_place = market2place(market)
        else:
            self.m_place = place

        if not country:
            self.m_country = compute_country(isin, market, place)
        else:
            self.m_country = country

        self.m_market = market

        self.m_userliveconnector = None

        self.m_defaultimportconnector = getImportConnector(self.m_market, self.m_list, QTag.imported, self.m_place)
        if self.m_defaultimportconnector is None:
            if itrade_config.verbose:
                print('no default import connector for {} (list:{})'.format(self, self.m_list.name))

        if self.m_list != QList.indices:
            if not currency:
                self.m_currency = market2currency(self.m_market)
            else:
                self.m_currency = currency
        else:
            self.m_currency = "N/A"

        # data for the connector plugin
        self.m_pluginId = None

        self._init_()

    # ---[ initialisation ]--------------------------------

    def _init_(self):
        # can be overloaded later ...
        # NB: PRU currency *is* portfolio currency
        self.m_DIR_number = 0
        self.m_DIR_pru = 0.0
        self.m_SRD_number = 0
        self.m_SRD_pru = 0.0
        self.m_SRD_accnum = 0
        self.m_SRD_prevacc = 0

        self.m_isTraded = False
        self.m_wasTraded = False
        self.m_isMonitored = False

        self.m_stoploss = 0.0
        self.m_stopwin = 0.0
        self.m_hasStops = False
        self.m_liveconnector = None
        self.m_importconnector = self.m_defaultimportconnector
        self.m_name = self.m_defaultname
        self.m_ticker = self.m_defaultticker
        self.m_symbcurr = itrade_currency.currency2symbol(self.m_currency)

        self.m_daytrades = None
        self.m_weektrades = None
        self.m_monthtrades = None

        self.m_percent = None
        self.m_prevclose = None

    def reinit(self):
        # info('{}::reinit'.format(self.name()))
        self._init_()

    # ---[ properties ] -----------------------------------

    def key(self):
        return self.m_key

    def type(self):
        n = QuoteType.no_type
        if self.m_DIR_number > 0:
            n += QuoteType.cash
        if self.m_SRD_number > 0:
            n += QuoteType.both
        return n

    def __str__(self):
        return self.m_key

    def __repr__(self):
        return '{};{};{};{};{};{};{}'.format(self.m_isin,
                                             self.m_name,
                                             self.m_ticker,
                                             self.m_market, self.m_currency, self.m_place, self.m_country)

    def __hash__(self):
        return self.m_key

    def country(self):
        return self.m_country

    def currency(self):
        return self.m_currency

    def currency_symbol(self):
        return self.m_symbcurr

    def isin(self):
        return self.m_isin

    def place(self):
        return self.m_place

    def list(self):
        return self.m_list

    def name(self):
        return self.m_name

    def default_name(self):
        return self.m_defaultname

    def set_name(self, name):
        self.m_name = name

    def ticker(self):
        return self.m_ticker

    def default_ticker(self):
        return self.m_defaultticker

    def set_ticker(self, ticker):
        self.m_ticker = ticker

    def nv_number(self, box=QuoteType.both):
        if box is QuoteType.cash:
            return self.m_DIR_number
        if box is QuoteType.credit:
            return self.m_SRD_number
        else:
            return self.m_DIR_number + self.m_SRD_number

    def sv_number(self, box=QuoteType.both):
        return _format_volume(self.nv_number(box))

    def nv_pru(self, box=QuoteType.both):
        # return PRU in the default currency (i.e. portfolio currency)
        if box is QuoteType.cash:
            return self.m_DIR_pru
        elif box is QuoteType.credit:
            return self.m_SRD_pru
        else:
            n = self.nv_number(QuoteType.both)
            if n > 0:
                return (self.nv_pr(QuoteType.cash) + self.nv_pr(QuoteType.credit)) / n
            return 0.0

    def nv_pr(self, box=QuoteType.both):
        # return PR in the default currency (i.e. portfolio currency)
        return self.nv_pru(box) * self.nv_number(box)

    def sv_pru(self, box=QuoteType.both, fmt="{:.3f}", bDispCurrency=False):
        # return PRU in the default currency (i.e. portfolio currency)
        if bDispCurrency:
            sc = ''.join((' ', self.m_symbcurr, ' '))
        else:
            sc = ''
        fmt = fmt + "{}"
        return fmt.format(self.nv_pru(box), sc)

    def sv_pr(self, box=QuoteType.both, fmt="{:.2f}", bDispCurrency=False):
        # return PR in the default currency (i.e. portfolio currency)
        if bDispCurrency:
            sc = ''.join((' ', self.m_symbcurr, ' '))
        else:
            sc = ''
        fmt = fmt + "{}"
        return fmt.format(self.nv_pr(box), sc)

    def nv_pv(self, currency, box=QuoteType.both):
        # return PV in the requested currency
        # nv_close() returns value in market currency
        cl = self.nv_close()
        if cl:
            if box == QuoteType.cash:
                retval = cl * self.m_DIR_number
            elif box == QuoteType.credit:
                retval = cl * self.m_SRD_number
            else:
                retval = cl * (self.m_DIR_number + self.m_SRD_number)
        else:
            retval = 0.0
        if currency:
            retval = itrade_currency.convert(currency, self.m_currency, retval)
        return retval

    def sv_pv(self, currency, box=QuoteType.both, fmt="{:.2f}"):
        # return PV in the requested currency
        return fmt.format(self.nv_pv(currency, box))

    def nv_profit(self, currency, box=QuoteType.both):
        return self.nv_pv(currency, box) - self.nv_pr(box)

    def sv_profit(self, currency, box=QuoteType.both, fmt="{:.2f}"):
        return fmt.format(self.nv_profit(currency, box))

    def nv_profitPercent(self, currency, box=QuoteType.both):
        # profit performance should be calculated after conversion to the portfolio currency !
        pr = self.nv_pr(box)
        if pr > 0:
            return self.nv_profit(currency, box) / self.nv_pr(box) * 100
        else:
            return 0.0

    def sv_profitPercent(self, currency, box=QuoteType.both):
        # profit performance should be calculated after conversion to the portfolio currency !
        if self.nv_pr(box) > 0:
            return "{:3.2f} %".format(self.nv_profitPercent(currency, box))
        else:
            return "---.-- %"

    def isTraded(self):
        return self.m_isTraded

    def wasTraded(self):
        return self.m_wasTraded

    def isMonitored(self):
        return self.m_isMonitored

    def isMatrix(self):
        return self.m_isMonitored or self.m_isTraded
        # was: return self.m_isMonitored or self.m_isTraded or self.m_wasTraded

    def descr(self):
        return '{} ({}-{})'.format(self.m_name, self.m_isin, self.m_ticker)

    def trades(self):
        return self.m_daytrades

    # ---[ market & connectors ] -------------------------------------

    def market(self):
        return self.m_market

    def delay(self):
        lc = self.liveconnector()
        if lc:
            return lc.delay()
        else:
            return 15

    def liveconnector(self, bForceLive=False, bDebug=False):
        if bForceLive:
            ret = getLiveConnector(self.m_market, self.m_list, QTag.live, self.m_place)
            if bDebug:
                print('liveconnector: for live connector {}'.format(ret))
            if ret:
                return ret

        if self.m_userliveconnector:
            # priority to connector selected by the user
            if bDebug:
                print('liveconnector: retuns userliveconnector {}'.format(self.m_userliveconnector))
            return self.m_userliveconnector

        if not self.m_liveconnector:
            self.m_liveconnector = getDefaultLiveConnector(self.m_market, self.m_list, self.m_place)
            if bDebug:
                print('liveconnector: get liveconnector {}'.format(self.m_liveconnector))
        if bDebug:
            print('liveconnector: retuns liveconnector {}'.format(self.m_liveconnector))
        return self.m_liveconnector

    def importconnector(self):
        return self.m_importconnector

    def user_liveconnector(self):
        if self.m_userliveconnector:
            return self.m_userliveconnector
        return self.m_liveconnector

    def default_importconnector(self):
        return self.m_defaultimportconnector

    def restore_defaultconnectors(self):
        self.m_userliveconnector = None
        # self.m_liveconnector = getDefaultLiveConnector(self.m_market, self.m_list, self.m_place)
        self.m_importconnector = getImportConnector(self.m_market, self.m_list, QTag.imported, self.m_place)
        self.m_pluginId = None

    def set_liveconnector(self, name):
        if itrade_config.verbose:
            print('set_liveconnector {}/{} for '.format(self.key(), self.name()),
                  self.m_market,
                  self.m_list,
                  QTag.any,
                  self.m_place,
                  name)
        conn = getLiveConnector(self.m_market, self.m_list, QTag.any, self.m_place, name)
        # if itrade_config.verbose:
        #     print(' returns', conn)
        if conn:
            self.m_userliveconnector = conn
            self.m_pluginId = None

    def set_importconnector(self, name):
        conn = getImportConnector(self.m_market, self.m_list, QTag.imported, self.m_place, name)
        if conn:
            self.m_importconnector = conn
            self.m_pluginId = None

    def get_pluginID(self):
        return self.m_pluginId

    def set_pluginID(self, id):
        self.m_pluginId = id
        return self.m_pluginId

    # ---[ notebook of order ] ----------------------------

    def hasNotebook(self):
        lc = self.liveconnector()
        if lc:
            return lc.hasNotebook()
        else:
            return False

    def currentNotebook(self):
        if self.hasNotebook():
            return self.liveconnector().currentNotebook(self)
        else:
            return None

    # ---[ status ] ---------------------------------------

    def hasStatus(self):
        lc = self.liveconnector()
        if lc:
            return lc.hasStatus()
        else:
            return False

    def currentStatus(self):
        # current status (status,reopen,RB,RH,clock) could be :
        #   status = OK, CLOSED, SUSPEND, SUSPEND+, SUSPEND-, UNKNOWN
        #   clock = time string of status in local market time
        if self.hasStatus():
            # get the real status
            cs, r, rb, rh, cl = self.liveconnector().currentStatus(self)
            if cs == "OK" and not self.hasOpened():
                cs = "CLOSED"
            if cs == "UNKNOWN" and not self.isOpen():
                cs = "CLOSED"
            # print('>>> get real status : ', cs)
            return (cs, r, rb, rh, cl)
        else:
            # generate a status
            if self.hasOpened():
                cs = "OK"
            else:
                cs = "CLOSED"
            # print('>>> generate a status : ', cs)
            return (cs, "::", "-", "-", "::")

    def sv_status(self):
        cs, r, rb, rh, cl = self.currentStatus()
        return cs

    def sv_clock(self):
        cs, r, rb, rh, cl = self.currentStatus()
        if cs == 'CLOSED' or cl == "::":
            return ""
        return cl

    def sv_type_of_clock(self, bDisplayTime=False):
        if self.delay() == 0:
            if bDisplayTime:
                return message('prop_islive')
            else:
                return message('prop_isslive')
        else:
            if bDisplayTime:
                return message('prop_isnotlive').format(self.delay())
            else:
                return message('prop_isdiffered')

    def sv_reopen(self):
        cs, r, rb, rh, cl = self.currentStatus()
        if r == "::":
            return "-"
        return r

    def low_threshold(self):
        cs, r, rb, rh, cl = self.currentStatus()
        if rb != "-":
            return float(rb)
        else:
            prev = self.nv_prevclose()
            if prev:
                # __x parameters given the market rules ...
                return prev - (0.1 * prev)
            else:
                return 0.0

    def high_threshold(self):
        cs, r, rb, rh, cl = self.currentStatus()
        if rh != "-":
            return float(rh)
        else:
            prev = self.nv_prevclose()
            if prev:
                # __x parameters given the market rules ...
                return prev + (0.1 * prev)
            else:
                return 0.0

    def currentMeans(self):
        # means: sell,buy,last
        if self.hasStatus():
            return self.liveconnector().currentMeans(self)
        else:
            return "-", "-", "-"

    def sv_waq(self):
        # weighted average quotation
        s, b, l = self.currentMeans()
        return l

    # ---[ stops ] ----------------------------------------

    def setStops(self, loss, win):
        # set the stops
        self.m_stoploss = float(loss)
        self.m_stopwin = float(win)
        if itrade_config.verbose:
            info('{}::setStops {} {}'.format(self.name(), self.m_stoploss, self.m_stopwin))
        self.m_hasStops = True

    def getStops(self):
        return '{};{};{}'.format(self.key(), self.sv_stoploss(), self.sv_stopwin())

    def clrStops(self):
        # clear (remove) the stops
        self.m_stoploss = 0.0
        self.m_stopwin = 0.0
        if itrade_config.verbose:
            info('{}::clrStops'.format(self.name()))
        self.m_hasStops = False

    def nv_stoploss(self):
        # return threshold low
        return self.m_stoploss

    def nv_stopwin(self):
        # return threshold high
        return self.m_stopwin

    def sv_stoploss(self, bDispCurrency=False):
        # return a string with optional currency
        if bDispCurrency:
            sc = ' ' + self.m_symbcurr + ' '
        else:
            sc = ''
        return "{:.2f}{}".format(self.nv_stoploss(), sc)

    def sv_stopwin(self, bDispCurrency=False):
        # return a string with optional currency
        if bDispCurrency:
            sc = ' ' + self.m_symbcurr + ' '
        else:
            sc = ''
        return "{:.2f}{}".format(self.nv_stopwin(), sc)

    def nv_riskmoney(self, currency):
        # calculate the money at risk
        sl = itrade_currency.convert(currency, self.m_currency, self.nv_stoploss())
        x = (self.nv_pru() - sl) * self.nv_number()
        if x > 0:
            return x
        else:
            return 0.0

    def sv_riskmoney(self, currency, CurrencySymbolToDisplay=None):
        # return a string with optional currency
        if CurrencySymbolToDisplay:
            sc = ' ' + CurrencySymbolToDisplay + ' '
        else:
            sc = ''
        return "{:.2f}{}".format(self.nv_riskmoney(currency), sc)

    def hasStops(self):
        # return True if the quote has threshold, False otherwise
        # getting API on stops can be called only if the quote has threshold
        return self.m_hasStops

    # ---[ load or import trades / date is unique key ] ---

    def loadTrades(self, fn=None):
        debug('Quote:loadTrades {}'.format(self.m_ticker))
        if self.m_daytrades is None:
            self.m_daytrades = itrade_trades.Trades(self)
        self.m_daytrades.load(fn)

    def importTrades(self, data, bLive):
        # debug('Quote:importTrades {} {} bLive={}'.format(self.ticker, data, bLive))
        if self.m_daytrades is None:
            self.m_daytrades = itrade_trades.Trades(self)

        data = data.split('\r\n')
        self.m_daytrades.imp(data, bLive)

        # only one line
        if bLive and len(data) >= 1:  # and self.list() == QList.indices:
            item = itrade_csv.parse(data[0], 9)
            if len(item) > 7:
                # percent is included !
                self.m_percent = string.atof(item[7])
            if len(item) > 8:
                # previous close is included !
                self.m_prevclose = string.atof(item[8])

    # ---[ save or export trades / date is unique key ] ---

    def saveTrades(self, fn=None):
        if self.m_daytrades is None:
            info('Quote:saveTrades {} - no daytrades !'.format(self.ticker()))
            return
        debug('Quote:saveTrades {} - save now !'.format(self.ticker()))
        self.m_daytrades.save(fn)

    # ---[ update the quote from the network ] ---

    def update(self, fromdate=None, todate=None):
        # debug('update {} from:{} to:{}'.format(self.ticker(), fromdate, todate))
        if self.m_daytrades is None:
            self.m_daytrades = itrade_trades.Trades(self)
            self.loadTrades()
        if fromdate == date.today() or fromdate is None:
            # import until 'yesterday' (be sure the day is or will open !)
            ajd = date.today()
            # if market is or will open:
            ajd = Datation(ajd).prevopen(self.m_market).date()
            # else:
            #   ajd = Datation(ajd).nearopen(self.m_market).date()

            # full importation ?
            tr = self.m_daytrades.lastimport()
            if tr is None:
                if itrade_config.verbose:
                    print('{} *** no trade at all ! : need to import ...'.format(self.key()))
                if not cmdline_importQuoteFromInternet(self):
                    print('error importing full data ...')
                    return False
            elif tr.date() != ajd:
                if itrade_config.verbose:
                    print('{} *** from = {} today = {} : need to import ...'.format(self.key(), tr.date(), ajd))
                if not import_from_internet(self, tr.date(), ajd):
                    print('error importing partial data ...')
                    return False
                self.saveTrades()

            # live update today
            if self.isOpen():
                if itrade_config.verbose:
                    print('{} / {} *** liveupdate today = {} ...'.format(self.key(), self.market(), date.today()))
                return liveupdate_from_internet(self)
            else:
                return True
        else:
            # history importation
            if itrade_config.verbose:
                print('history importation for {} '.format(self.key()))
            if import_from_internet(self, fromdate, todate):
                # self.saveTrades()
                return True
            else:
                return False

    # ---[ operations on the quote ] ---

    def buy(self, n, m, box):
        # info('buy: {} {:d} {:f}'.format(self.ticker(), n, m))
        if box == QuoteType.cash:
            if (self.m_DIR_number + n) > 0:
                self.m_DIR_pru = ((self.m_DIR_pru * self.m_DIR_number) + m) / (self.m_DIR_number + n)
            if self.m_DIR_pru < 0.0:
                self.m_DIR_pru = 0.0
            self.m_DIR_number = self.m_DIR_number + n
        elif box == QuoteType.credit:
            if (self.m_SRD_number + n) > 0:
                self.m_SRD_pru = ((self.m_SRD_pru * self.m_SRD_number) + m) / (self.m_SRD_number + n)
            if self.m_SRD_pru < 0.0:
                self.m_SRD_pru = 0.0
            self.m_SRD_number = self.m_SRD_number + n
            self.m_SRD_accnum = max(self.m_SRD_accnum, self.m_SRD_number)
            # print 'set accnum = ',self.m_SRD_accnum
        self.m_isTraded = (self.m_DIR_number > 0) or (self.m_SRD_number > 0)

    def sell(self, n, box):
        # info('sell: {} {:d}'.format(self.ticker(), n))
        if box == QuoteType.cash:
            if self.m_DIR_number < n:
                raise Exception("negative number of shares is not possible ...")
            self.m_DIR_number = self.m_DIR_number - n
            if self.m_DIR_number <= 0:
                self.m_wasTraded = True
        elif box == QuoteType.credit:
            if self.m_SRD_number < n:
                raise Exception("short unsupported yet ...")
            self.m_SRD_number = self.m_SRD_number - n
            if self.m_SRD_number <= 0:
                self.m_wasTraded = True
        self.m_isTraded = (self.m_DIR_number > 0) or (self.m_SRD_number > 0)

    def transfertTo(self, n, expenses, box):
        # info('transfert: {} {:d}'.format(self.ticker(), n))
        if box == QuoteType.cash:
            if self.m_SRD_number < n:
                raise Exception("negative number of shares is not possible ...")
            price = (n * self.m_SRD_pru)
            if self.m_SRD_accnum > 0:
                # print('n=', n, 'get accnum = ', self.m_SRD_accnum)
                price = price + (expenses*n/self.m_SRD_accnum)
            # print 'n=',n,'price = ',price
            self.sell(n, QuoteType.credit)
            self.buy(n, price, QuoteType.cash)
            self.m_SRD_prevacc = self.m_SRD_accnum
            self.m_SRD_accnum = self.m_SRD_number
            # print('n=', n, 'reinit accnum = ', self.m_SRD_accnum)
        elif box == QuoteType.credit:
            if self.m_DIR_number < n:
                raise Exception("negative number of shares is not possible ...")
            price = (n * self.m_DIR_pru)
            if self.m_SRD_prevacc > 0:
                price = price - (expenses*n/self.m_SRD_prevacc)
            self.sell(n, QuoteType.cash)
            self.buy(n, price, QuoteType.credit)
            self.m_SRD_accnum = self.m_SRD_prevacc

    # ---[ current / live values on the quote ] ---

    def index(self, d=None):
        if self.m_daytrades:
            if d is None:
                tr = self.m_daytrades.lasttrade()
            else:
                tr = self.m_daytrades.trade(d)
            if tr:
                return tr.index()
        return -1

    def lastindex(self):
        if self.m_daytrades:
            tr = self.m_daytrades.lasttrade()
            if tr:
                return tr.index()
        return -1

    def firstindex(self):
        if self.m_daytrades:
            tr = self.m_daytrades.firsttrade()
            if tr:
                return tr.index()
        return -1

    def nv_close(self, d=None):
        if self.m_daytrades:
            if d is None:
                tr = self.m_daytrades.lasttrade()
            else:
                tr = self.m_daytrades.trade(d)
            if tr:
                return tr.nv_close()
        return None

    def nv_open(self, d=None):
        if self.m_daytrades:
            if d is None:
                tr = self.m_daytrades.lasttrade()
            else:
                tr = self.m_daytrades.trade(d)
            if tr:
                return tr.nv_open()
        return None

    def nv_low(self, d=None):
        if self.m_daytrades:
            if d is None:
                tr = self.m_daytrades.lasttrade()
            else:
                tr = self.m_daytrades.trade(d)
            if tr:
                return tr.nv_low()
        return None

    def nv_high(self, d=None):
        if self.m_daytrades:
            if d is None:
                tr = self.m_daytrades.lasttrade()
            else:
                tr = self.m_daytrades.trade(d)
            if tr:
                return tr.nv_high()
        return None

    def nv_volume(self, d=None):
        if self.m_daytrades:
            if d is None:
                tr = self.m_daytrades.lasttrade()
            else:
                tr = self.m_daytrades.trade(d)
            if tr:
                return tr.nv_volume()
        return None

    def nv_prevclose(self, d=None):
        if self.m_prevclose is not None:
            # print('$$ {} nv_prevclose:'.format(self.ticker(), self.m_prevclose))
            return self.m_prevclose

        if self.m_daytrades:
            tc = self.m_daytrades.prevtrade(d)
            if tc:
                return tc.nv_close()
        return None

    def nv_unitvar(self, d=None):
        if self.m_daytrades:
            tc = self.nv_close(d)
            tp = self.nv_prevclose(d)
            if tc and tp:
                return tc - tp
        return None

    def nv_percent(self, d=None):
        if self.m_percent is not None:
            # print('$$ {} nv_percent:'.format(self.ticker(), self.m_percent))
            return self.m_percent

        if self.m_daytrades:
            tc = self.nv_close(d)
            tp = self.nv_prevclose(d)
            if tc and tp:
                return ((tc/tp)*100)-100
        return None

    # ---[ same current / live data on quote but string ] ------------------

    def sv_close(self, d=None, bDispCurrency=False):
        if bDispCurrency:
            sc = ' ' + self.m_symbcurr + ' '
        else:
            sc = ''
        x = self.nv_close(d)
        if x is not None:
            st, re, rb, rh, cl = self.currentStatus()
            if st == 'OK':
                return "{:3.3f}{}".format(x, sc)
            elif st == 'SUSPEND+':
                return "{:3.3f}{}(+)".format(x, sc)
            elif st == 'SUSPEND-':
                return "{:3.3f}{}(-)".format(x, sc)
            elif st == 'SUSPEND':
                return "{:3.3f}{}(s)".format(x, sc)
            elif st == 'CLOSED':
                return "{:3.3f}{}(c)".format(x, sc)
            else:
                return "{:3.3f}{}({})".format(x, sc, st)
        return " ---.---{}".format(sc)

    def sv_open(self, d=None):
        x = self.nv_open(d)
        if x is not None:
            return "{:3.3f}".format(x)
        return " ---.--- "

    def sv_low(self, d=None):
        x = self.nv_low(d)
        if x is not None:
            return "{:3.3f}".format(x)
        return " ---.--- "

    def sv_high(self, d=None):
        x = self.nv_high(d)
        if x is not None:
            return "{:3.3f}".format(x)
        return " ---.--- "

    def sv_volume(self, d=None):
        x = self.nv_volume(d)
        if x is not None:
            return _format_volume(x)
        return " ---------- "

    def sv_prevclose(self, d=None):
        x = self.nv_prevclose(d)
        if x is not None:
            return "{:3.3f}".format(x)
        return " ---.--- "

    def sv_percent(self, d=None):
        try:
            x = self.nv_percent(d)
        except:
            return " ---.-- %"

        if x is not None:
            if x > 0:
                return "+{:3.2f} %".format(x)
            else:
                return "{:3.2f} %".format(x)
        return " ---.-- %"

    def sv_unitvar(self, d=None):
        x = self.nv_unitvar(d)
        if x is not None:
            return "{:3.2f}".format(x)
        return " ---.-- "

    # ---[ object value ] ---

    def ov_candle(self, d=None):
        if self.m_daytrades:
            if d is None:
                tr = self.m_daytrades.lasttrade()
            else:
                tr = self.m_daytrades.trade(d)
            if tr is None:
                return None
            d = Datation(tr.date()).date()
            tc = self.m_daytrades.candle(d)
        else:
            tc = None
        return tc

    def ov_pivots(self):
        if self.m_daytrades:
            tc = self.m_daytrades.lasttrade()
            if tc:
                # debug('ov_pivots(): tc={} tc_date={} ... need to get prev ...'.format(tc, tc.date()))
                tc = self.m_daytrades.prevtrade()
            if tc:
                H = tc.nv_high()
                B = tc.nv_low()
                C = tc.nv_close()
                pivot = (H + B + C) / 3
                s1 = (2 * pivot) - H
                s2 = pivot - (H - B)
                r1 = (2 * pivot) - B
                r2 = pivot + (H - B)
                return (s2, s1, pivot, r1, r2)
        return (-1.0, -1.0, -1.0, -1.0, -1.0)

    def sv_pivots(self):
        if self.sv_status() == 'OK':
            s2, s1, pivot, r1, r2 = self.ov_pivots()
            if pivot != -1.0:
                cl = self.nv_close()
                if cl > r2:
                    return "R2+ ({:.2f})".format(r2)
                elif cl == r2:
                    return "R2= ({:.2f})".format(r2)
                elif cl > r1:
                    return "R1+ ({:.2f})".format(r1)
                elif cl == r1:
                    return "R1= ({:.2f})".format(r1)
                elif cl > pivot:
                    return "PI+ ({:.2f})".format(pivot)
                elif cl == pivot:
                    return "PI= ({:.2f})".format(pivot)
                elif cl > s1:
                    return "PI- ({:.2f})".format(pivot)
                elif cl == s1:
                    return "S1= ({:.2f})".format(s1)
                elif cl > s2:
                    return "S1- ({:.2f})".format(s1)
                elif cl == s2:
                    return "S2= ({:.2f})".format(s2)
                else:
                    return "S2- ({:.2f})".format(s2)
        return " --- (-.--) "

    # ---[ market open/close ] ---

    def date(self, d=None):
        if self.m_daytrades:
            if d is None:
                tr = self.m_daytrades.lasttrade()
            else:
                tr = self.m_daytrades.trade(d)
            if tr:
                return tr.date()
        return None

    def sv_date(self, bDisplayShort=False):
        return date2str(self.date(), bDisplayShort)

    def hasOpened(self):
        if self.date() == date.today():
            # print('>>> hasOpened : True')
            return True
        else:
            # print('>>> hasOpened : False')
            return False

    def hasTraded(self):
        if self.isOpen():
            # today is open : check we have a known trade
            if self.date() == date.today():
                # print('>>> hasTraded : True')
                return True
            else:
                # print('>>> hasTraded : False')
                return False
        else:
            # today is closed : check previous open
            if self.m_daytrades and self.m_daytrades.prevtrade():
                # a trade exists !
                return True
            else:
                # no trade
                return False

    def isOpen(self):
        return gCal.isopen(date.today(), self.m_market)

    # ---[ compute all the data ] ---

    def compute(self, todate=None):
        debug('{}: compute [{}]'.format(self.ticker(), todate))
        if self.m_daytrades:
            self.m_daytrades.compute(todate)

    # ---[ Trends ] ---

    def colorLine(self, d=None):
        if self.m_percent is None:
            if self.m_daytrades:
                tc = self.nv_close(d)
                tp = self.nv_prevclose(d)
                if tc and tp:
                    self.m_percent = ((tc/tp)*100)-100
                else:
                    return QuoteColor.invalid
            else:
                return QuoteColor.invalid

        if self.m_percent > 0:
            return QuoteColor.green
        elif self.m_percent < 0:
            return QuoteColor.red
        else:
            return QuoteColor.nochange

    def colorTrend(self, d=None):
        if self.m_daytrades:
            if d is None:
                tc = self.m_daytrades.lasttrade()
                # print('colorTrend: lasttrade close : {:.2f} date : {} '.format(tc.nv_close(), tc.date()))
            else:
                tc = self.m_daytrades.trade(d)
                # print('colorTrend: specific close : {:.2f} date : {} '.format(tc.nv_close(), tc.date()))

            tp = self.m_daytrades.prevtrade(d)
            if not tp:
                return QuoteColor.invalid

            if tc.nv_close() == tp.nv_close():
                return self.colorLine()
            elif tc.nv_close() < tp.nv_close():
                return self.colorLine()
            elif tc.nv_close() > tp.nv_close():
                return self.colorLine()
            else:
                return QuoteColor.invalid
        return QuoteColor.invalid

    def colorStop(self):
        cl = self.nv_close()
        if self.nv_number() == 0:
            # no share on this quote : inside the target : BUY
            if (cl >= self.nv_stoploss()) and (cl <= self.nv_stopwin()):
                # must buy
                return QuoteColor.green
            else:
                # do nothing
                return QuoteColor.nochange
        else:
            # some shares : outside the target : SELL
            if (cl <= self.nv_stoploss()) or (cl >= self.nv_stopwin()):
                # must sell
                return QuoteColor.red
            else:
                # do nothing
                return QuoteColor.nochange

    # ---[ Indicators ] ---

    def nv_ma(self, period=20, d=None):
        if d is None:
            d = self.m_daytrades.lasttrade()
            if d:
                d = d.date()
            else:
                return None
        mm = self.m_daytrades.ma(period, d)
        return mm

    def sv_ma(self, period=20, d=None):
        x = self.nv_ma(period, d)
        if x is not None:
            return "{:3.3f}".format(x)
        return " ---.--- "

    def nv_rsi(self, period=14, d=None):
        if d is None:
            d = self.m_daytrades.lasttrade()
            if d:
                d = d.date()
            else:
                return None
        rsi = self.m_daytrades.rsi(period, d)
        return rsi

    def sv_rsi(self, period=14, d=None):
        x = self.nv_rsi(period, d)
        if x is not None:
            return "{:3.3f}".format(x)
        return " ---.--- "

    def nv_stoK(self, d=None):
        if d is None:
            d = self.m_daytrades.lasttrade()
            if d:
                d = d.date()
            else:
                return None
        sto = self.m_daytrades.stoK(d)
        return sto

    def sv_stoK(self, d=None):
        x = self.nv_stoK(d)
        if x is not None:
            return "{:3.2f}".format(x)
        return " ---.-- "

    def nv_stoD(self, d=None):
        if d is None:
            d = self.m_daytrades.lasttrade()
            if d:
                d = d.date()
            else:
                return None
        sto = self.m_daytrades.stoD(d)
        return sto

    def sv_stoD(self, d=None):
        x = self.nv_stoD(d)
        if x is not None:
            return "{:3.2f}".format(x)
        return " ---.-- "

    def nv_vma(self, period=15, d=None):
        if d is None:
            if d:
                d = d.date()
            else:
                return None
        mm = self.m_daytrades.vma(period, d)
        return mm

    def sv_vma(self, period=15, d=None):
        x = self.nv_vma(period, d)
        if x is not None:
            return "{:d}".format(x)
        return " ---------- "

    def nv_ovb(self, d=None):
        if d is None:
            if d:
                d = d.date()
            else:
                return None
        mm = self.m_daytrades.ovb(d)
        return mm

    def sv_ovb(self, d=None):
        x = self.nv_ovb(d)
        if x is not None:
            return "{:d}".format(x)
        return " ---------- "

    # ---[ monitor a quote ] ---

    def monitorIt(self, t):
        self.m_isMonitored = t
        return self.m_isMonitored

    # ---[ Command line ] ---

    def printInfo(self):
        print('{} - {} - {} (market={})'.format(self.key(), self.ticker(), self.name(), self.market()))
        print('PRU DIR/SRD = {:f} / {:f}'.format(self.m_DIR_pru, self.m_SRD_pru))
        print('Cours = {:f}'.format(self.nv_close()))
        print('Nbre DIR/SRD/total = {:d}/{:d}/{:d}'.format(self.nv_number(QuoteType.cash),
                                                           self.nv_number(QuoteType.credit),
                                                           self.nv_number(QuoteType.both)))
        print('Gain DIR = {:f}'.format((self.nv_close()-self.m_DIR_pru)*self.nv_number(QuoteType.cash)))
        print('Gain SRD = {:f}'.format((self.nv_close()-self.m_SRD_pru)*self.nv_number(QuoteType.credit)))
        print('Candle = {}'.format(self.ov_candle()))
        print('StopLoss = {}'.format(self.sv_stoploss()))
        print('StopWin = {}'.format(self.sv_stopwin()))

    # ---[ flush and reload ] ---

    def flushAndReload(self, dlg):
        self.flushTrades()
        cmdline_importQuoteFromInternet(self, dlg)
        self.compute()

    def flushTrades(self):
        if self.m_daytrades:
            self.m_daytrades.reset()
            self.m_daytrades = None
        self.m_pluginId = None

    def flushNews(self):
        newsfile = os.path.join(itrade_config.dirCacheData, '{}.htm'.format(self.key()))
        try:
            os.remove(newsfile)
        except OSError:
            pass

    # ---[ Persistent Properties ] ------------------------

    def setProperty(self, prop, val):
        if prop == 'name':
            self.set_name(val)
        elif prop == 'ticker':
            self.set_ticker(val)
        elif prop == 'live':
            self.set_liveconnector(val)
        elif prop == 'import':
            self.set_importconnector(val)
        else:
            info('Quote::setProperty({}): unknown property: {}'.format(self.key(), prop))

    def listProperties(self):
        prop = []
        if self.name() != self.default_name():
            prop.append('{};{};{}'.format(self.key(), 'name', self.name()))
        if self.ticker() != self.default_ticker():
            prop.append('{};{};{}'.format(self.key(), 'ticker', self.ticker()))
        if self.m_userliveconnector and (self.m_userliveconnector != self.m_liveconnector):
            prop.append('{};{};{}'.format(self.key(), 'live', self.user_liveconnector().name()))
        if self.importconnector() != self.default_importconnector():
            prop.append('{};{};{}'.format(self.key(), 'import', self.importconnector().name()))
        return prop

# ============================================================================
# Quotes
# ============================================================================
#
# CSV File format :
#   ISIN;NAME;SICOVAM;TICKER
# ============================================================================

class Quotes(object):
    def __init__(self):
        # debug('Quotes:__init__')
        self._init_()

    def _init_(self):
        self.m_quotes = {}

    def reinit(self):
        debug('Quotes::reinit')
        for eachQuote in self.list():
            eachQuote.reinit()

    def list(self):
        items = self.m_quotes.values()
        items.sort(key=Quote.name)
        return items

    # ---[ Properties ] ---

    def addProperty(self, key, prop, val):
        quote = self.lookupKey(key)
        if quote:
            quote.setProperty(prop, val)

    def loadProperties(self):
        # open and read the file to load properties information
        infile = itrade_csv.read(None, os.path.join(itrade_config.dirUserData, 'properties.txt'))
        if infile:
            # scan each line to read each quote
            for eachLine in infile:
                item = itrade_csv.parse(eachLine, 3)
                if item:
                    # debug('{} ::: {}'.format(eachLine, item))
                    self.addProperty(item[0], item[1], item[2])

    def saveProperties(self):
        props = []
        for eachQuote in self.list():
            for eachProp in eachQuote.listProperties():
                # print(eachProp)
                props.append(eachProp)
        itrade_csv.write(None, os.path.join(itrade_config.dirUserData, 'properties.txt'), props)

    # ---[ Stops ] ---

    def addStops(self, key, loss, win):
        quote = self.lookupKey(key)
        if quote:
            quote.setStops(loss, win)

    def removeStops(self, key):
        quote = self.lookupKey(key)
        if quote:
            quote.clrStops()

    def loadStops(self, fs=None):
        # open and read the file to load stops information
        infile = itrade_csv.read(fs, os.path.join(itrade_config.dirUserData, 'default.stops.txt'))
        if infile:
            # scan each line to read each quote
            for eachLine in infile:
                item = itrade_csv.parse(eachLine, 3)
                if item:
                    # debug('{} ::: {}'.format(eachLine, item))
                    self.addStops(item[0], item[1], item[2])

    def saveStops(self, fp=None):
        stops = []
        for eachQuote in self.list():
            if eachQuote.hasStops():
                stops.append(eachQuote.getStops())
        itrade_csv.write(fp, os.path.join(itrade_config.dirUserData, 'default.stops.txt'), stops)

    # ---[ Quotes ] ---

    def addQuote(self, isin, name, ticker, market, currency, place, country=None, list=QList.system, debug=False):
        # right case
        if country:
            country = country.upper()
        if place:
            place = place.upper()

        # get a key and check strict duplicate (i.e. same key)
        key = quote_reference(isin, ticker, market, place)
        if key in self.m_quotes:
            if debug:
                print('{!r}/{} already exists - keep it (ignore {})'.format(self.m_quotes[key],
                                                                            self.m_quotes[key].ticker(),
                                                                            ticker))
            return True

        # depending on isin
        if isin is None or isin == '':
            # no isin : check if we have already this quote
            quote = None  # __perf: self.lookupTicker(ticker,market)
            if quote:
                if debug:
                    print('{!r} already exists - ignore'.format(self.m_quotes[key]))
                return True
        else:
            # isin : check if we can replace the same quote without isin
            key2 = quote_reference(None, ticker, market, place)
            if key2 in self.m_quotes:
                if debug:
                    print('{!r} already exists but without ISIN - replace'.format(self.m_quotes[key2]))
                del self.m_quotes[key2]

        # new quote
        self.m_quotes[key] = Quote(key,
                                   isin,
                                   name.upper(),
                                   ticker.upper(), market, currency.upper(), place, country, list)

        if debug:
            print('Add {} in quotes list'.format(self.m_quotes[key]))

        return True

    def _addLines(self, infile, list, debug):
        # scan each line to read each quote
        for eachLine in infile:
            item = itrade_csv.parse(eachLine, 7)
            if item and len(item) >= 7:
                self.addQuote(item[0], item[1], item[2], item[3], item[4], item[5], item[6], list, debug)

    # ---[ load list of quotes / indices / trackers / ... ] ---------------------------------------------------

    def loadMarket(self, market):
        # open and read the file to load these quotes information
        if not is_market_loaded(market):
            infile = itrade_csv.read(None, os.path.join(itrade_config.dirSymbData, 'quotes.{}.txt'.format(market)))
            if infile:
                self._addLines(infile, list=QList.system, debug=False)
            set_market_loaded(market)

    def load_list_from_csv(self, list_type, file_name):
        infile = itrade_csv.read(None, file_name)
        if infile:
            self._addLines(infile, list=list_type, debug=False)

    def loadListOfQuotes(self):
        self.load_list_from_csv(QList.indices, os.path.join(itrade_config.dirSymbData, 'indices.txt'))
        self.load_list_from_csv(QList.trackers, os.path.join(itrade_config.dirSymbData, 'trackers.txt'))
        self.load_list_from_csv(QList.bonds, os.path.join(itrade_config.dirSymbData, 'bonds.txt'))
        self.load_list_from_csv(QList.user, os.path.join(itrade_config.dirUserData, 'usrquotes.txt'))

    # ---[ save list of quotes / indices / trackers / ... ] ---------------------------------------------------

    def saveMarkets(self):
        for eachMarket in list_of_markets(ifLoaded=True):
            props = []
            for eachQuote in self.list():
                if eachQuote.list() == QList.system and eachQuote.market() == eachMarket:
                    props.append(eachQuote.__repr__())
            #
            # open and write the file with these quotes information
            itrade_csv.write(None, os.path.join(itrade_config.dirSymbData, 'quotes.{}.txt'.format(eachMarket)), props)
            print('System List of symbols {} saved.'.format(eachMarket))

    def saveListOfQuotes(self):
        # System list
        self.saveMarkets()

        # User list
        props = []
        for eachQuote in self.list():
            if eachQuote.list() == QList.user:
                props.append(eachQuote.__repr__())
        #
        # open and write the file with these quotes information
        itrade_csv.write(None, os.path.join(itrade_config.dirUserData, 'usrquotes.txt'), props)
        print('User List of symbols saved.')

    # ---[ removeQuotes from the list ] ---

    def removeQuote(self, key):
        if key in self.m_quotes:
            del self.m_quotes[key]
            return True
        return False

    def removeQuotes(self, market, list):
        for eachQuote in self.list():
            if list == eachQuote.list():
                if market is None or eachQuote.market() == market:
                    del self.m_quotes[eachQuote.key()]

    # ---[ Lookup (optionaly, filter by market) ] ---

    def lookupKey(self, key):
        if key is None:
            return None

        if key in self.m_quotes:
            return self.m_quotes[key]

        # key not found
        skey = key.split('.')
        if len(skey) == 3:
            # check the list of quotes for this market has been loaded
            market = skey[1]
            if not is_market_loaded(market):
                self.loadMarket(market)
                if key in self.m_quotes:
                    return self.m_quotes[key]

        # key really not found
        return None

    def lookupISIN(self, isin, market=None, place=None):
        # return list of
        ret = []
        for eachVal in self.m_quotes.values():
            if eachVal.isin() == isin:
                if (market is None or (market == eachVal.market())) and (place is None or (place == eachVal.place())):
                    ret.append(eachVal)
        return ret

    def lookupTicker(self, ticker, market=None, place=None):
        # return first one
        for eachVal in self.m_quotes.values():
            if (eachVal.ticker() == ticker)\
                    and (market is None or (market == eachVal.market()))\
                    and (place is None or (place == eachVal.place())):
                return eachVal
        return None

    def lookupPartialTicker(self, ticker, market=None, place=None):
        # return list of
        ret = []
        for eachVal in self.m_quotes.values():
            if (eachVal.ticker().find(ticker, 0) == 0)\
                    and (market is None or (market == eachVal.market()))\
                    and (place is None or (place == eachVal.place())):
                ret.append(eachVal)
        return ret

    def lookupName(self, name, market, place=None):
        for eachVal in self.m_quotes.values():
            if (eachVal.name() == name)\
                    and (market is None or (market == eachVal.market()))\
                    and (place is None or (place == eachVal.place())):
                return eachVal
        return None

    # ---[ Trades ] ---

    def loadTrades(self, fi=None):
        # read quotes data
        for eachKey in self.m_quotes.keys():
            self.m_quotes[eachKey].loadTrades(fi)

    def saveTrades(self, fe=None):
        # read quotes data
        for eachKey in self.m_quotes.keys():
            self.m_quotes[eachKey].saveTrades(fe)

# ============================================================================
# Export
# ============================================================================

quotes = Quotes()


# ============================================================================
# initQuotesModule()
# ============================================================================

def initQuotesModule():
    quotes.loadListOfQuotes()

# ============================================================================
# Test
# ============================================================================

def main():
    setLevel(logging.INFO)
    # load configuration
    itrade_config.ensure_setup()
    itrade_config.load_config()
    from itrade_local import setLang, gMessage
    setLang('us')
    gMessage.load()
    # load euronext extensions
    import itrade_ext
    itrade_ext.loadOneExtension('itrade_import_euronext.py', itrade_config.dirExtData)
    quotes.loadMarket('EURONEXT')
    info('test1 {}'.format(quotes.lookupISIN('FR0000072621')))
    quote = quotes.lookupTicker('OSI', 'EURONEXT')
    info('test2 {}'.format(quote.ticker()))
    info('test3a {}'.format(quote.isin()))
    info('test3b {}'.format(quote.key()))
    info('test4 {}'.format(quote.name()))
    info('test5 {}'.format(quote.descr()))
    quote = quotes.lookupTicker('OSI', 'EURONEXT')
    quote.loadTrades('import/Cortal-2005-01-07.txt')
    info('test6 {}'.format(quote.trades().trade(date(2005, 1, 4))))
    quote = quotes.lookupTicker('EADT', 'EURONEXT')
    quote.loadTrades('import/Cortal-2005-01-07.txt')
    quote.loadTrades('import/Cortal-2005-01-14.txt')
    quote.loadTrades('import/Cortal-2005-01-21.txt')
    info('test7 {}'.format(quote.trades().trade(date(2005, 1, 4))))
    #    quotes.saveTrades()
    quotes.saveListOfQuotes()


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
