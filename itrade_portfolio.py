#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_portfolio.py
#
# Description: Portfolio & Operations
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is Gilles Dumortier.
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
# 2004-02-20    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from __future__ import absolute_import
import datetime
import logging
import operator
import os

# iTrade system
import itrade_config
from itrade_logging import setLevel, debug, info
import itrade_datation
from itrade_quotes import quotes, QuoteType
from itrade_matrix import create_matrix
from itrade_local import message, gMessage
import itrade_csv
from itrade_currency import currency2symbol, currencies
from itrade_vat import country2vat
from itrade_login import gLoginRegistry
from itrade_market import getDefaultIndice

# ============================================================================
# Operation
#
#   TYPE:
#       A/B buy (trade)     i.e. accumulate (SRD/x)
#       R/S sell (trade)    i.e. reduce (SRD/x)
#       C   credit (cash)   i.e. deposit
#       D   debit (cash)    i.e. withdrawal
#       F   fee (cash)
#       I   interest (cash)
#       X   split (divisor)
#       Y   detachment of coupon (cash on trade) - non-taxable
#       Z   dividend (cash on trade) - taxable
#       L   liquidation     i.e. SRD
#       Q   dividend with shares
#       W   register shares
#
# ============================================================================

OPERATION_BUY       = 'B'
OPERATION_BUY_SRD   = 'A'
OPERATION_SELL      = 'S'
OPERATION_SELL_SRD  = 'R'
OPERATION_CREDIT    = 'C'
OPERATION_DEBIT     = 'D'
OPERATION_FEE       = 'F'
OPERATION_INTEREST  = 'I'
OPERATION_SPLIT     = 'X'
OPERATION_DETACHMENT = 'Y'
OPERATION_DIVIDEND  = 'Z'
OPERATION_LIQUIDATION = 'L'
OPERATION_QUOTE = 'Q'
OPERATION_REGISTER = 'W'


operation_cash = {
    OPERATION_BUY       : False,
    OPERATION_BUY_SRD   : False,
    OPERATION_SELL      : False,
    OPERATION_SELL_SRD  : False,
    OPERATION_CREDIT    : True,
    OPERATION_DEBIT     : True,
    OPERATION_FEE       : False,
    OPERATION_INTEREST  : False,
    OPERATION_SPLIT     : False,
    OPERATION_DETACHMENT: False,
    OPERATION_DIVIDEND  : False,
    OPERATION_LIQUIDATION : False,
    OPERATION_REGISTER : False,
    OPERATION_QUOTE : False
}

operation_quote = {
    OPERATION_BUY       : True,
    OPERATION_BUY_SRD   : True,
    OPERATION_SELL      : True,
    OPERATION_SELL_SRD  : True,
    OPERATION_CREDIT    : False,
    OPERATION_DEBIT     : False,
    OPERATION_FEE       : False,
    OPERATION_INTEREST  : False,
    OPERATION_SPLIT     : True,
    OPERATION_DETACHMENT: True,
    OPERATION_DIVIDEND  : True,
    OPERATION_LIQUIDATION  : True,
    OPERATION_REGISTER  : True,
    OPERATION_QUOTE     : True
}

operation_number = {
    OPERATION_BUY       : True,
    OPERATION_BUY_SRD   : True,
    OPERATION_SELL      : True,
    OPERATION_SELL_SRD  : True,
    OPERATION_CREDIT    : False,
    OPERATION_DEBIT     : False,
    OPERATION_FEE       : False,
    OPERATION_INTEREST  : False,
    OPERATION_SPLIT     : False,
    OPERATION_DETACHMENT: False,
    OPERATION_DIVIDEND  : False,
    OPERATION_LIQUIDATION  : True,
    OPERATION_REGISTER  : True,
    OPERATION_QUOTE     : True,
}

operation_sign = {
    OPERATION_BUY       : '-',
    OPERATION_BUY_SRD   : '-',
    OPERATION_SELL      : '+',
    OPERATION_SELL_SRD  : '+',
    OPERATION_CREDIT    : '+',
    OPERATION_DEBIT     : '-',
    OPERATION_FEE       : '-',
    OPERATION_INTEREST  : '+',
    OPERATION_SPLIT     : ' ',
    OPERATION_DETACHMENT: '+',
    OPERATION_DIVIDEND  : '+',
    OPERATION_LIQUIDATION  : '+',
    OPERATION_REGISTER  : '~',
    OPERATION_QUOTE     : ' '
}

operation_srd = {
    OPERATION_BUY       : False,
    OPERATION_BUY_SRD   : True,
    OPERATION_SELL      : False,
    OPERATION_SELL_SRD  : True,
    OPERATION_CREDIT    : False,
    OPERATION_DEBIT     : False,
    OPERATION_FEE       : False,
    OPERATION_INTEREST  : False,
    OPERATION_SPLIT     : False,
    OPERATION_DETACHMENT: False,
    OPERATION_DIVIDEND  : False,
    OPERATION_LIQUIDATION  : True,
    OPERATION_REGISTER  : False,
    OPERATION_QUOTE     : False
}

operation_incl_taxes = {
    OPERATION_BUY       : True,
    OPERATION_BUY_SRD   : True,
    OPERATION_SELL      : True,
    OPERATION_SELL_SRD  : True,
    OPERATION_CREDIT    : True,
    OPERATION_DEBIT     : True,
    OPERATION_FEE       : True,
    OPERATION_INTEREST  : True,
    OPERATION_SPLIT     : True,
    OPERATION_DETACHMENT: True,
    OPERATION_DIVIDEND  : True,
    OPERATION_LIQUIDATION  : False,
    OPERATION_REGISTER  : False,
    OPERATION_QUOTE     : True
}


def create_operation(operation_type, d, m, value, expenses, number, vat, ref):
    if operation_type == OPERATION_BUY:
        return OperationBuy(d=d, m=m, v=value, e=expenses, n=number, vat=vat, ref=ref)
    if operation_type == OPERATION_BUY_SRD:
        return OperationBuySrd(d=d, m=m, v=value, e=expenses, n=number, vat=vat, ref=ref)
    if operation_type == OPERATION_SELL:
        return OperationSell(d=d, m=m, v=value, e=expenses, n=number, vat=vat, ref=ref)
    if operation_type == OPERATION_SELL_SRD:
        return OperationSellSrd(d=d, m=m, v=value, e=expenses, n=number, vat=vat, ref=ref)
    if operation_type == OPERATION_CREDIT:
        return OperationCredit(d=d, m=m, v=value, e=expenses, n=number, vat=vat, ref=ref)
    if operation_type == OPERATION_DEBIT:
        return OperationDebit(d=d, m=m, v=value, e=expenses, n=number, vat=vat, ref=ref)
    if operation_type == OPERATION_FEE:
        return OperationFee(d=d, m=m, v=value, e=expenses, n=number, vat=vat, ref=ref)
    if operation_type == OPERATION_INTEREST:
        return OperationInterest(d=d, m=m, v=value, e=expenses, n=number, vat=vat, ref=ref)
    if operation_type == OPERATION_SPLIT:
        return OperationSplit(d=d, m=m, v=value, e=expenses, n=number, vat=vat, ref=ref)
    if operation_type == OPERATION_DETACHMENT:
        return OperationDetachment(d=d, m=m, v=value, e=expenses, n=number, vat=vat, ref=ref)
    if operation_type == OPERATION_DIVIDEND:
        return OperationDividend(d=d, m=m, v=value, e=expenses, n=number, vat=vat, ref=ref)
    if operation_type == OPERATION_LIQUIDATION:
        return OperationLiquidation(d=d, m=m, v=value, e=expenses, n=number, vat=vat, ref=ref)
    if operation_type == OPERATION_QUOTE:
        return OperationQuote(d=d, m=m, v=value, e=expenses, n=number, vat=vat, ref=ref)
    if operation_type == OPERATION_REGISTER:
        return OperationRegister(d=d, m=m, v=value, e=expenses, n=number, vat=vat, ref=ref)
    raise TypeError("invalid operation_type parameter")


class Operation(object):
    def __init__(self, d, m, v, e, n, vat, ref):
        # decode the datetime (string) to convert to datetime
        if isinstance(d, datetime.datetime):
            self.m_datetime = d
        else:
            debug('Operation::__init__():{}'.format(d))
            try:
                self.m_datetime = datetime.datetime.strptime(d, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                try:
                    self.m_datetime = datetime.datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    self.m_datetime = datetime.datetime.strptime(d, '%Y-%m-%d')

        self.m_value = float(v)
        self.m_number = int(n)
        self.m_expenses = float(e)
        self.m_vat = float(vat)
        self.m_ref = ref

        # support key or name or bad value
        if self.isQuote():
            # m : could be isin (old format) or key (new format)
            self.m_quote = quotes.lookupKey(m)
            if not self.m_quote:
                self.m_quote = quotes.lookupTicker(ticker=m)
                if self.m_quote:
                    self.m_name = self.m_quote.name()
                else:
                    lst = quotes.lookupISIN(m)
                    if len(lst) > 0:
                        self.m_quote = lst[0]
                        self.m_name = self.m_quote.name()
                    else:
                        # bad name : keep it :-(
                        self.m_name = m
            else:
                self.m_name = self.m_quote.name()
        else:
            # not a quote : keep the label
            self.m_quote = None
            self.m_name = m

        # print(u'Operation(): quote={} name={}'.format(self.m_quote, self.m_name))

    def __repr__(self):
        name = self.m_name
        if self.m_quote:
            name = self.m_quote.key()
        return u'{};{};{};{:f};{:f};{:d};{:f}'.format(self.m_datetime, self.type(), name, self.m_value, self.m_expenses, self.m_number, self.m_vat)

    def ref(self):
        return self.m_ref

    def type(self):
        raise NotImplementedError("Please Implement this method")

    def apply(self, d=None):
        raise NotImplementedError("Please Implement this method")

    def undo(self, d=None):
        raise NotImplementedError("Please Implement this method")

    def nv_value(self):
        return self.m_value

    def sv_value(self):
        return u'{:.2f}'.format(self.nv_value())

    def nv_expenses(self):
        return self.m_expenses

    def sv_expenses(self):
        return u'{:.2f}'.format(self.nv_expenses())

    def nv_vat(self):
        return self.m_vat

    def sv_vat(self):
        return u'{:.2f}'.format(self.nv_vat())

    def nv_number(self):
        return operation_number.get(self.type(), 0)

    def sv_number(self):
        return u'{:6d}'.format(self.nv_number())

    def isSRD(self):
        return operation_srd.get(self.type(), False)

    def name(self):
        if self.m_name:
            return self.m_name
        return ""

    def datetime(self):
        return self.m_datetime

    def date(self):
        return self.m_datetime.date()

    def time(self):
        return self.m_datetime.time()

    def sv_date(self):
        return self.date().strftime('%x')

    def quote(self):
        if self.isQuote():
            return self.m_quote
        else:
            raise TypeError("quote(): operation::type() shall be S or B or Y or Z")

    def operation(self):
        return u'? ({})'.format(self.type())

    def isCash(self):
        return operation_cash.get(self.type(), self.isQuote())

    def isQuote(self):
        return operation_quote.get(self.type(), False)

    def sign(self):
        return operation_sign.get(self.type(), '?')

    def description(self):
        if self.isQuote():
            ticker = u'?'
            if self.m_quote:
                ticker = self.m_quote.ticker()
            return u'{} ({})'.format(self.name(), ticker)
        else:
            return self.name()

    def nv_pvalue(self):
        if self.m_quote:
            if self.type() == OPERATION_SELL:
                return self.m_value - (self.m_quote.nv_pru(QuoteType.cash) * self.m_number)
            if self.type() == OPERATION_SELL_SRD:
                return self.m_value - (self.m_quote.nv_pru(QuoteType.credit) * self.m_number)
        return 0

    def sv_pvalue(self):
        return u'{:.2f}'.format(self.nv_pvalue())

    def compute(self, portfolio, cd):
        raise TypeError("computeOperations(): self::type() unknown %s", self.type())


class OperationBuy(Operation):

    def __init__(self, d, m, v, e, n, vat, ref):
        super(OperationBuy, self).__init__(d, m, v, e, n, vat, ref)

    def type(self):
        return OPERATION_BUY

    def operation(self):
        return message('Portfolio_buy')

    def apply(self, d=None):
        if self.m_quote:
            debug(u'buy {}'.format(self.m_quote))
            self.m_quote.buy(self.m_number, self.m_value, QuoteType.cash)

    def undo(self, d=None):
        if self.m_quote:
            debug(u'undo-buy {}'.format(self.m_quote))
            self.m_quote.sell(self.m_number, QuoteType.cash)

    def compute(self, portfolio, cd):
        debug(u'buy {}/{} : {:d} for {:f}'.format(self.name(), self.quote(), self.nv_number(),
                                                  self.nv_value()))
        portfolio.m_cCash -= self.nv_value()
        if portfolio.sameyear(self, cd):
            portfolio.m_cExpenses += self.nv_expenses()


class OperationBuySrd(Operation):

    def __init__(self, d, m, v, e, n, vat, ref):
        super(OperationBuySrd, self).__init__(d, m, v, e, n, vat, ref)

    def type(self):
        return OPERATION_BUY_SRD

    def operation(self):
        return message('Portfolio_buy_srd')

    def apply(self, d=None):
        if self.m_quote:
            debug(u'buy SRD {}'.format(self.m_quote))
            self.m_quote.buy(self.m_number, self.m_value, QuoteType.credit)

    def undo(self, d=None):
        if self.m_quote:
            debug(u'undo-buy SRD {}'.format(self.m_quote))
            self.m_quote.sell(self.m_number, QuoteType.credit)

    def compute(self, portfolio, cd):
            debug(u'buy SRD {}/{} : {:d} for {:f}'.format(self.name(), self.quote(), self.nv_number(),
                                                          self.nv_value()))
            portfolio.m_cCredit = portfolio.m_cCredit + self.nv_value()
            if portfolio.sameyear(self, cd):
                portfolio.m_cExpenses = portfolio.m_cExpenses + self.nv_expenses()


class OperationSell(Operation):

    def __init__(self, d, m, v, e, n, vat, ref):
        super(OperationSell, self).__init__(d, m, v, e, n, vat, ref)

    def type(self):
        return OPERATION_SELL

    def operation(self):
        return message('Portfolio_sell')

    def apply(self, d=None):
        if self.m_quote:
            debug(u'sell {}'.format(self.m_quote))
            max = self.m_quote.nv_number(QuoteType.cash)
            if self.m_number > max:
                self.m_number = max
            self.m_quote.sell(self.m_number, QuoteType.cash)

    def undo(self, d=None):
        if self.m_quote:
            debug(u'undo-sell {}'.format(self.m_quote))
            self.m_quote.buy(self.m_number, self.m_value, QuoteType.cash)

    def compute(self, portfolio, cd):
        debug(u'sell {}/{} : {:d} for {:f}'.format(self.name(), self.quote(), self.nv_number(),
                                                   self.nv_value()))
        portfolio.m_cCash = portfolio.m_cCash + self.nv_value()
        if portfolio.sameyear(self, cd):
            portfolio.m_cExpenses = portfolio.m_cExpenses + self.nv_expenses()
            portfolio.m_cTransfer = portfolio.m_cTransfer + self.nv_value() + self.nv_expenses()
            portfolio.m_cTaxable = portfolio.m_cTaxable + self.nv_pvalue()
            portfolio.m_cAppreciation = portfolio.m_cAppreciation + self.nv_pvalue()


class OperationSellSrd(Operation):

    def __init__(self, d, m, v, e, n, vat, ref):
        super(OperationSellSrd, self).__init__(d, m, v, e, n, vat, ref)

    def type(self):
        return OPERATION_SELL_SRD

    def operation(self):
        return message('Portfolio_sell_srd')

    def apply(self, d=None):
        if self.m_quote:
            debug(u'sell SRD {}'.format(self.m_quote))
            max = self.m_quote.nv_number(QuoteType.credit)
            if self.m_number > max:
                self.m_number = max
            self.m_quote.sell(self.m_number, QuoteType.credit)

    def undo(self, d=None):
        if self.m_quote:
            debug(u'undo-sell SRD {}'.format(self.m_quote))
            self.m_quote.buy(self.m_number, self.m_value, QuoteType.credit)

    def compute(self, portfolio, cd):
        debug(u'sell SRD {}/{} : {:d} for {:f}'.format(self.name(), self.quote(), self.nv_number(),
                                                       self.nv_value()))
        portfolio.m_cCredit = portfolio.m_cCredit - self.nv_value()
        if portfolio.sameyear(self, cd):
            portfolio.m_cExpenses = portfolio.m_cExpenses + self.nv_expenses()
            portfolio.m_cTransfer = portfolio.m_cTransfer + self.nv_value() + self.nv_expenses()


class OperationCredit(Operation):

    def __init__(self, d, m, v, e, n, vat, ref):
        super(OperationCredit, self).__init__(d, m, v, e, n, vat, ref)

    def type(self):
        return OPERATION_CREDIT

    def operation(self):
        return message('Portfolio_credit')

    def apply(self, d=None):
        pass

    def undo(self, d=None):
        pass

    def compute(self, portfolio, cd):
        debug(u'credit {} : + {:f}'.format(self.name(), self.nv_value()))
        portfolio.m_cCash = portfolio.m_cCash + self.nv_value()
        portfolio.m_cInvest = portfolio.m_cInvest + self.nv_value()
        if portfolio.sameyear(self, cd):
            portfolio.m_cExpenses = portfolio.m_cExpenses + self.nv_expenses()


class OperationDebit(Operation):

    def __init__(self, d, m, v, e, n, vat, ref):
        super(OperationDebit, self).__init__(d, m, v, e, n, vat, ref)

    def type(self):
        return OPERATION_DEBIT

    def operation(self):
        return message('Portfolio_debit')

    def apply(self, d=None):
        pass

    def undo(self, d=None):
        pass

    def compute(self, portfolio, cd):
        debug(u'debit {} : - {:f}'.format(self.name(), self.nv_value()))
        portfolio.m_cCash = portfolio.m_cCash - self.nv_value()
        # __x portfolio.m_cInvest = portfolio.m_cInvest - self.nv_value()
        if portfolio.sameyear(self, cd):
            portfolio.m_cExpenses = portfolio.m_cExpenses + self.nv_expenses()


class OperationFee(Operation):

    def __init__(self, d, m, v, e, n, vat, ref):
        super(OperationFee, self).__init__(d, m, v, e, n, vat, ref)

    def type(self):
        return OPERATION_FEE

    def operation(self):
        return message('Portfolio_fee')

    def apply(self, d=None):
        pass

    def undo(self, d=None):
        pass

    def compute(self, portfolio, cd):
        debug(u'fee {}: {:f}'.format(self.name(), self.nv_value()))
        portfolio.m_cCash = portfolio.m_cCash - self.nv_value()
        if portfolio.sameyear(self, cd):
            portfolio.m_cExpenses = portfolio.m_cExpenses + self.nv_expenses()


class OperationInterest(Operation):

    def __init__(self, d, m, v, e, n, vat, ref):
        super(OperationInterest, self).__init__(d, m, v, e, n, vat, ref)

    def type(self):
        return OPERATION_INTEREST

    def operation(self):
        return message('Portfolio_interest')

    def apply(self, d=None):
        pass

    def undo(self, d=None):
        pass

    def compute(self, portfolio, cd):
        debug(u'interest {} : {:f}'.format(self.name(), self.nv_value()))
        portfolio.m_cCash = portfolio.m_cCash + self.nv_value()
        if portfolio.sameyear(self, cd):
            portfolio.m_cExpenses = portfolio.m_cExpenses + self.nv_expenses()
            # portfolio.m_cTaxable = portfolio.m_cTaxable + self.nv_value()
            portfolio.m_cAppreciation = portfolio.m_cAppreciation + self.nv_value()


class OperationSplit(Operation):

    def __init__(self, d, m, v, e, n, vat, ref):
        super(OperationSplit, self).__init__(d, m, v, e, n, vat, ref)

    def type(self):
        return OPERATION_SPLIT

    def operation(self):
        return message('Portfolio_split')

    def apply(self, d=None):
        pass

    def undo(self, d=None):
        pass

    def compute(self, portfolio, cd):
        pass


class OperationDetachment(Operation):
    # return of capital?

    def __init__(self, d, m, v, e, n, vat, ref):
        super(OperationDetachment, self).__init__(d, m, v, e, n, vat, ref)

    def type(self):
        return OPERATION_DETACHMENT

    def operation(self):
        return message('Portfolio_detachment')

    def apply(self, d=None):
        if self.m_quote:
            debug(u'detachment {} / {:f}'.format(self.m_quote, self.m_value))
            self.m_quote.buy(0, -self.m_value, QuoteType.cash)

    def undo(self, d=None):
        if self.m_quote:
            debug(u'undo-detachment {}'.format(self.m_quote))
            self.m_quote.buy(0, self.m_value, QuoteType.cash)

    def compute(self, portfolio, cd):
        debug(u'detach {}/{} : {:f}'.format(self.name(), self.quote(), self.nv_value()))
        portfolio.m_cCash = portfolio.m_cCash + self.nv_value()
        if portfolio.sameyear(self, cd):
            portfolio.m_cExpenses = portfolio.m_cExpenses + self.nv_expenses()
            # portfolio.m_cTaxable = portfolio.m_cTaxable + self.nv_value()
            portfolio.m_cAppreciation = portfolio.m_cAppreciation + self.nv_value()


class OperationDividend(Operation):

    def __init__(self, d, m, v, e, n, vat, ref):
        super(OperationDividend, self).__init__(d, m, v, e, n, vat, ref)

    def type(self):
        return OPERATION_DIVIDEND

    def operation(self):
        return message('Portfolio_dividend')

    def apply(self, d=None):
        pass

    def undo(self, d=None):
        pass

    def compute(self, portfolio, cd):
        debug(u'dividend {}/{} : {:f}'.format(self.name(), self.quote(), self.nv_value()))
        portfolio.m_cCash = portfolio.m_cCash + self.nv_value()
        if portfolio.sameyear(self, cd):
            portfolio.m_cExpenses = portfolio.m_cExpenses + self.nv_expenses()
            portfolio.m_cTaxable = portfolio.m_cTaxable + self.nv_value()
            portfolio.m_cAppreciation = portfolio.m_cAppreciation + self.nv_value()


class OperationLiquidation(Operation):

    def __init__(self, d, m, v, e, n, vat, ref):
        super(OperationLiquidation, self).__init__(d, m, v, e, n, vat, ref)

    def type(self):
        return OPERATION_LIQUIDATION

    def operation(self):
        return message('Portfolio_liquidation')

    def apply(self, d=None):
        if self.m_quote:
            debug(u'liquidation {} / {:f}'.format(self.m_quote, self.m_value))
            self.m_quote.transfertTo(self.m_number, self.m_expenses, QuoteType.cash)

    def undo(self, d=None):
        if self.m_quote:
            debug(u'undo-liquidation {} / {:d}'.format(self.m_quote))
            self.m_quote.transfertTo(self.m_number, self.m_expenses, QuoteType.credit)

    def compute(self, portfolio, cd):
        debug(u'liquidation {}: {:f}'.format(self.name(), self.nv_value()))
        portfolio.m_cCash = portfolio.m_cCash + self.nv_value()
        portfolio.m_cCredit = portfolio.m_cCredit + (self.nv_value() + self.nv_expenses())
        if portfolio.sameyear(self, cd):
            portfolio.m_cExpenses = portfolio.m_cExpenses + self.nv_expenses()
            portfolio.m_cTaxable = portfolio.m_cTaxable + self.nv_value()
            portfolio.m_cAppreciation = portfolio.m_cAppreciation + self.nv_value()
            quote = self.quote()
            if quote:
                pv = self.nv_number() * quote.nv_pru(QuoteType.credit)
                portfolio.m_cTaxable = portfolio.m_cTaxable + pv
                portfolio.m_cAppreciation = portfolio.m_cAppreciation + pv


class OperationQuote(Operation):

    def __init__(self, d, m, v, e, n, vat, ref):
        super(OperationQuote, self).__init__(d, m, v, e, n, vat, ref)

    def type(self):
        return OPERATION_QUOTE

    def operation(self):
        return message('Portfolio_quote')

    def apply(self, d=None):
        if self.m_quote:
            debug(u'dividend/shares {}'.format(self.m_quote))
            self.m_quote.buy(self.m_number, 0.0, QuoteType.cash)

    def undo(self, d=None):
        if self.m_quote:
            debug(u'undo-dividend/share {}'.format(self.m_quote))
            self.m_quote.sell(self.m_number, QuoteType.cash)

    def compute(self, portfolio, cd):
        debug(u'dividend/share {}/{} : {:f}'.format(self.name(), self.quote(), self.nv_value()))


class OperationRegister(Operation):

    def __init__(self, d, m, v, e, n, vat, ref):
        super(OperationRegister, self).__init__(d, m, v, e, n, vat, ref)

    def type(self):
        return OPERATION_REGISTER

    def operation(self):
        return message('Portfolio_register')

    def apply(self, d=None):
        if self.m_quote:
            debug(u'register/shares {}'.format(self.m_quote))
            self.m_quote.buy(self.m_number, self.m_value, QuoteType.cash)

    def undo(self, d=None):
        if self.m_quote:
            debug(u'undo-register {}'.format(self.m_quote))
            self.m_quote.sell(self.m_number, QuoteType.cash)

    def compute(self, portfolio, cd):
        debug(u'register/share {}/{} : {:f}'.format(self.name(), self.quote(), self.nv_value()))
        portfolio.m_cInvest = portfolio.m_cInvest + self.nv_value()


def isOperationTypeAQuote(type):
    if type in operation_quote:
        return operation_quote[type]
    else:
        return False


def isOperationTypeIncludeTaxes(type):
    return operation_incl_taxes.get(type, True)

def isOperationTypeHasShareNumber(type):
    if type in operation_number:
        return operation_number[type]
    else:
        return False

def signOfOperationType(type):
    if type in operation_sign:
        return operation_sign[type]
    else:
        return ' '

# ============================================================================
# Operations : list of Operation
# ============================================================================
#
# CSV File format :
#
#   DATE;TYPE;NAME;VALUE;EXPENSES;NUMBER;VAT
#
#   TYPE: see OPERATION_xx
#
# ============================================================================

class Operations(object):
    def __init__(self, portfolio):
        debug(u'Operations:__init__({})'.format(portfolio))
        self.m_operations = {}
        self.m_ref = 0
        self.m_portfolio = portfolio
        self.default_operations_file = os.path.join(itrade_config.dirUserData, 'default.operations.txt')

    def list(self):
        return sorted(list(self.m_operations.values()), key=operator.methodcaller('datetime'))

    def load(self, infile=None):
        infile = itrade_csv.read(infile, self.default_operations_file)
        # scan each line to read each trade
        for line in infile:
            item = itrade_csv.parse(line, 7)
            if item:
                self.add(item, False)

    def save(self, outfile=None):
        itrade_csv.write(outfile, self.default_operations_file, self.list())

    def add(self, item, bApply):
        debug(u'Operations::add() before: 0:{} , 1:{} , 2:{} , 3:{} , 4:{} , 5:{}'.format(item[0], item[1], item[2], item[3], item[4], item[5]))
        vat = self.item_vat(item)
        op = create_operation(operation_type=item[1], d=item[0], m=item[2], value=item[3], expenses=item[4], number=item[5], vat=vat, ref=self.m_ref)
        self.m_operations[self.m_ref] = op
        if bApply:
            op.apply()
        debug(u'Operations::add() after: {}'.format(self.m_operations))
        self.m_ref = self.m_ref + 1
        return op.ref()

    def item_vat(self, item):
        if len(item) >= 7:
            vat = item[6]
        else:
            vat = self.m_portfolio.vat()
        return vat

    def remove(self, ref, bUndo):
        if bUndo:
            self.m_operations[ref].undo()
        del self.m_operations[ref]

    def get(self, ref):
        return self.m_operations[ref]

# ============================================================================
# Portfolio
# ============================================================================
#
#   filename
#   name            name displayed for the user
#   accountref      account reference number
#   market          principal market traded by this portfolio
# ============================================================================


class Portfolio(object):
    def __init__(self, filename='default', name='<Portfolio>', accountref='000000000', market='EURONEXT', currency='EUR', vat=1.0, term=3, risk=5, indice='FR0003500008'):
        debug(u'Portfolio::__init__ fn={} name={} account={}'.format(filename, name, accountref))

        self.m_filename = filename
        self.m_name = name
        self.m_accountref = accountref
        self.m_market = market
        self.m_currency = currency
        self.m_vat = vat
        self.m_term = term
        self.m_risk = risk
        self.m_indice = indice
        self._init_()

    # portfolio name
    def name(self):
        return self.m_name

    # market name ('EURONEXT')
    def market(self):
        return self.m_market

    # currency code (i.e. EUR)
    def currency(self):
        return self.m_currency

    # main indice (CAC40 : FR0003500008)
    def indice(self):
        return self.m_indice

    # vat (i.e. 1.196 for France)
    def vat(self):
        return self.m_vat

    # investment term period (in month)
    def term(self):
        return self.m_term

    # risk level (integer xx%) per line of investment
    def risk(self):
        return self.m_risk

    # symbol for the currency in use
    def currency_symbol(self):
        return currency2symbol(self.m_currency)

    def __repr__(self):
        return u'{};{};{};{};{};{:f};{:d};{:d};{}'.format(self.m_filename, self.m_name, self.m_accountref, self.m_market, self.m_currency, self.m_vat, self.m_term, self.m_risk, self.m_indice)

    def filenamepath(self, portfn, fn):
        return os.path.join(itrade_config.dirUserData, u'{}.{}.txt'.format(portfn, fn))

    def filepath(self, fn):
        return os.path.join(itrade_config.dirUserData, u'{}.{}.txt'.format(self.filename(), fn))

    def filename(self):
        return self.m_filename

    def key(self):
        return self.m_filename.lower()

    def accountref(self):
        return self.m_accountref

    def operations(self):
        return self.m_operations

    # ---[ initialise internal structure ]-------------------------------------

    def _init_(self):
        self.m_operations = Operations(self)
        # __fee self.m_fees = Fees(self)

        # indexed by gCal index
        self.m_inDate = {}          # date
        self.m_inCash = {}          # cash available
        self.m_inCredit = {}        # credit available (SRD)
        self.m_inBuy = {}           # buy
        self.m_inValue = {}         # value available (not including cash)
        self.m_inInvest = {}        # cash investment cumulation
        self.m_inExpenses = {}      # expenses cumulation
        self.m_inTransfer = {}      # transfer cumulation

        # first cell
        self.m_inDate[0] = itrade_datation.gCal.date(0)
        self.m_inCash[0] = 0.0
        self.m_inCredit[0] = 0.0
        self.m_inBuy[0] = 0.0
        self.m_inValue[0] = 0.0
        self.m_inInvest[0] = 0.0
        self.m_inExpenses[0] = 0.0
        self.m_inTransfer[0] = 0.0

        # cumulated value
        self.reset()

    # ---[ reset some fields before calculation ]------------------------------

    def reset(self):
        self.m_cCash = 0.0
        self.m_cCredit = 0.0
        self.m_cDIRBuy = 0.0
        self.m_cSRDBuy = 0.0
        self.m_cDIRValue = 0.0
        self.m_cSRDValue = 0.0
        self.m_cInvest = 0.0

        # year dependent
        self.m_cExpenses = 0.0
        self.m_cTransfer = 0.0
        self.m_cTaxable = 0.0
        self.m_cAppreciation = 0.0

    # ---[ reinit the portfolio, associated services and quotes ]---------------

    def reinit(self):
        debug(u'Portfolio::{}::reinit'.format(self.name()))
        self.logoutFromServices()
        quotes.reinit()
        self._init_()

    # ---[ File management for the portfolio ]----------------------------------

    def remove(self):
        """
        remove all files used by the portfolio
        """
        self.remove_file('operations')
        self.remove_file('matrix')
        self.remove_file('fees')
        self.remove_file('stops')

    def remove_file(self, file_type):
        fn = self.filepath(file_type)
        try:
            os.remove(fn)
        except OSError:
            pass

    def rename(self, nname):
        """
        rename all files used by the portfolio
        """
        fn = self.filepath('operations')
        nfn = self.filenamepath(nname, 'operations')
        try:
            os.rename(fn, nfn)
        except OSError:
            pass
        fn = self.filepath('matrix')
        nfn = self.filenamepath(nname, 'matrix')
        try:
            os.rename(fn, nfn)
        except OSError:
            pass
        fn = self.filepath('fees')
        nfn = self.filenamepath(nname, 'fees')
        try:
            os.rename(fn, nfn)
        except OSError:
            pass
        fn = self.filepath('stops')
        nfn = self.filenamepath(nname, 'stops')
        try:
            os.rename(fn, nfn)
        except OSError:
            pass
        self.m_filename = nname

    # ---[ load, save and apply Rules ] ---------------------------------------
    """# __fee
    def loadFeesRules(self):
        fn = self.filepath('fees')
        self.m_fees.load(fn)

    def saveFeesRules(self):
        fn = self.filepath('fees')
        self.m_fees.save(fn)

    def applyFeeRules(self, v, all=True):
        fee = 0.0
        for eachFee in self.m_fees.list():
            fee = fee + eachFee.nv_fee(v)
            if fee and all:
                # first rule apply -> return fee
                return fee
        # no rule apply -> no fee
        return fee
     """
    # ---[ load, save stops ] -------------------------------------------------

    def loadStops(self):
        fn = self.filepath('stops')
        quotes.loadStops(fn)

    def saveStops(self):
        fn = self.filepath('stops')
        quotes.saveStops(fn)

    # ---[ load, save global properties ] -------------------------------------

    def loadProperties(self):
        quotes.loadProperties()

    def saveProperties(self):
        quotes.saveProperties()

    # ---[ load, save and apply Operations ] ----------------------------------

    def loadOperations(self):
        fn = self.filepath('operations')
        self.m_operations.load(fn)

    def saveOperations(self):
        fn = self.filepath('operations')
        self.m_operations.save(fn)

    def applyOperations(self, d=None):
        debug(u'applyOperations date<={}'.format(d))
        for operation in self.m_operations.list():
            debug(u'applyOperations: {}'.format(operation))
            if d is None or d >= operation.date():
                operation.apply(d)
            else:
                info(u'ignore {}'.format(operation.name()))

    # --- [ manage login to services ] ----------------------------------------

    def loginToServices(self, quote=None):
        def login(quote):
            name = quote.liveconnector(bForceLive=True).name()
            #print('loginToServices:', quote.ticker(), name)
            if name not in maperr:
                con = gLoginRegistry.get(name)
                if con and not con.logged():
                    print('login to service :', name)
                    maperr[name] = con.login()

        if itrade_config.isConnected():
            # temp map
            maperr = {}

            # log to service
            if quote:
                login(quote)
            else:
                for eachQuote in quotes.list():
                    if eachQuote.isMatrix():
                        login(eachQuote)

    def logoutFromServices(self):
        if itrade_config.isConnected():
            # temp map
            maperr = {}

            # log to service
            for quote in quotes.list():
                if quote.isMatrix():
                    name = quote.liveconnector().name()
                    if name not in maperr:
                        con = gLoginRegistry.get(name)
                        if con and con.logged():
                            print('logout from service :', name)
                            maperr[name] = con.logout()

    # --- [ manage multi-currency on the portfolio ] --------------------------

    def setupCurrencies(self):
        currencies.reset()
        for eachQuote in quotes.list():
            if eachQuote.isMatrix():
                currencies.inuse(self.m_currency, eachQuote.currency(), bInUse=True)

    def is_multicurrencies(self):
        for eachQuote in quotes.list():
            if eachQuote.isMatrix():
                if eachQuote.currency() != self.m_currency:
                    return True
        return False

    # --- [ compute the operations ] ------------------------------------------

    def sameyear(self, op, cd=None):
        if cd is None:
            cd = datetime.date.today().year
        if cd == op.date().year:
            return True
        else:
            return False

    def computeOperations(self, cd=None):
        self.reset()
        for operation in self.m_operations.list():
            operation.compute(self, cd)

    # --- [ compute the value ] -----------------------------------------------

    def computeValue(self):
        self.m_cDIRValue = 0.0
        self.m_cSRDValue = 0.0
        for eachQuote in quotes.list():
            if eachQuote.isTraded():
                self.m_cDIRValue = self.m_cDIRValue + eachQuote.nv_pv(self.m_currency, QuoteType.cash)
                self.m_cSRDValue = self.m_cSRDValue + eachQuote.nv_pv(self.m_currency, QuoteType.credit)

    def computeBuy(self):
        self.m_cDIRBuy = 0.0
        self.m_cSRDBuy = 0.0
        for eachQuote in quotes.list():
            if eachQuote.isTraded():
                self.m_cDIRBuy = self.m_cDIRBuy + eachQuote.nv_pr(QuoteType.cash)
                self.m_cSRDBuy = self.m_cSRDBuy + eachQuote.nv_pr(QuoteType.credit)

    # --- [ operations API ] --------------------------------------------------

    def addOperation(self, item):
        self.m_operations.add(item, True)

    def delOperation(self, ref):
        self.m_operations.remove(ref, True)

    def getOperation(self, ref):
        return self.m_operations.get(ref)

    # --- [ value API ] -------------------------------------------------------

    def nv_cash(self, currency=None):
        retval = self.m_cCash
        if currency:
            retval = currencies.convert(curTo=currency, curFrom=self.m_currency, Value=retval)
        return retval

    def nv_credit(self, currency=None):
        retval = self.m_cCredit
        if currency:
            retval = currencies.convert(curTo=currency, curFrom=self.m_currency, Value=retval)
        return retval

    def nv_invest(self):
        return self.m_cInvest

    def nv_value(self, box=QuoteType.both):
        # __x compute it !
        self.computeValue()
        if box == QuoteType.cash:
            return self.m_cDIRValue
        if box == QuoteType.credit:
            return self.m_cSRDValue
        else:
            return self.m_cDIRValue + self.m_cSRDValue

    def nv_buy(self, box=QuoteType.both):
        # __x compute it !
        self.computeBuy()
        if box == QuoteType.cash:
            return self.m_cDIRBuy
        if box == QuoteType.credit:
            return self.m_cSRDBuy
        else:
            return self.m_cDIRBuy + self.m_cSRDBuy

    def nv_expenses(self):
        return self.m_cExpenses

    def nv_transfer(self):
        return self.m_cTransfer

    def nv_taxable(self):
        if self.m_cTaxable < 0.0:
            return 0.0
        return self.m_cTaxable

    def nv_appreciation(self):
        return self.m_cAppreciation

    def nv_taxes(self):
        if self.nv_transfer() < itrade_config.taxesThreshold:
            return 0.0
        else:
            return self.nv_taxable() * itrade_config.taxesPercent

    def nv_perf(self, box=QuoteType.both):
        #info(u'nv_perf={:f}'.format(self.nv_value(box) - self.nv_buy(box)))
        return self.nv_value(box) - self.nv_buy(box)

    def nv_perfPercent(self, box=QuoteType.both):
        n = self.nv_value(box)
        b = self.nv_buy(box)
        if n == 0.0 or b == 0.0:
            return 0.0
        return ((n*100.0) / b) - 100

    def nv_totalValue(self):
        return self.nv_value() + self.nv_cash() - self.m_cCredit

    def nv_perfTotal(self):
        return self.nv_totalValue() - self.nv_invest()

    def nv_perfTotalPercent(self):
        n = self.nv_totalValue()
        i = self.nv_invest()
        if n == 0.0 or i == 0.0:
            return 0.0
        return ((n*100.0) / i) - 100

    def nv_percentCash(self, box=QuoteType.both):
        total = self.nv_value(box) + self.nv_cash()
        if total == 0.0:
            return 0.0
        else:
            return (total-self.nv_value(box))/total*100.0

    def nv_percentQuotes(self, box=QuoteType.both):
        total = self.nv_value(box) + self.nv_cash()
        if total == 0.0:
            return 0.0
        else:
            return (total-self.nv_cash())/total*100.0

    # --- [ string API ] ------------------------------------------------------

    def sv_cash(self, currency=None, fmt="{:.2f}", bDispCurrency=False):
        if bDispCurrency:
            sc = ' ' + self.currency_symbol() + ' '
        else:
            sc = ''
        fmt = fmt + u"{}"
        return fmt.format(self.nv_cash(), sc)

    def sv_credit(self, currency=None, fmt="{:.2f}", bDispCurrency=False):
        if bDispCurrency:
            sc = ' ' + self.currency_symbol() + ' '
        else:
            sc = ''
        fmt = fmt + u"{}"
        return fmt.format(self.nv_credit(), sc)

    def sv_taxes(self, fmt="{:.2f}", bDispCurrency=False):
        if bDispCurrency:
            sc = ' ' + self.currency_symbol() + ' '
        else:
            sc = ''
        fmt = fmt + u"{}"
        return fmt.format(self.nv_taxes(), sc)

    def sv_expenses(self, fmt="{:.2f}", bDispCurrency=False):
        if bDispCurrency:
            sc = ' ' + self.currency_symbol() + ' '
        else:
            sc = ''
        fmt = fmt + u"{}"
        return fmt.format(self.nv_expenses(), sc)

    def sv_transfer(self, fmt="{:.2f}", bDispCurrency=False):
        if bDispCurrency:
            sc = ' ' + self.currency_symbol() + ' '
        else:
            sc = ''
        fmt = fmt + u"{}"
        return fmt.format(self.nv_transfer(), sc)

    def sv_taxable(self, fmt="{:.2f}", bDispCurrency=False):
        if bDispCurrency:
            sc = ' ' + self.currency_symbol() + ' '
        else:
            sc = ''
        fmt = fmt + u"{}"
        return fmt.format(self.nv_taxable(), sc)

    def sv_appreciation(self, fmt="{:.2f}", bDispCurrency=False):
        if bDispCurrency:
            sc = ' ' + self.currency_symbol() + ' '
        else:
            sc = ''
        fmt = fmt + u"{}"
        return fmt.format(self.nv_appreciation(), sc)

    def sv_invest(self, fmt=u"{:.2f}", bDispCurrency=False):
        if bDispCurrency:
            sc = ' ' + self.currency_symbol() + ' '
        else:
            sc = ''
        fmt = fmt + u"{}"
        return fmt.format(self.nv_invest(), sc)

    def sv_value(self, box=QuoteType.both, fmt="{:.2f}", bDispCurrency=False):
        if bDispCurrency:
            sc = ' '+self.currency_symbol()+' '
        else:
            sc = ''
        fmt = fmt + u"{}"
        return fmt.format(self.nv_value(box), sc)

    def sv_buy(self, box=QuoteType.both, fmt="{:.2f}", bDispCurrency=False):
        if bDispCurrency:
            sc = ' ' + self.currency_symbol() + ' '
        else:
            sc = ''
        fmt = fmt + u"{}"
        return fmt.format(self.nv_buy(box), sc)

    def sv_perf(self, box=QuoteType.both, fmt="{:.2f}", bDispCurrency=False):
        if bDispCurrency:
            sc = ' ' + self.currency_symbol() + ' '
        else:
            sc = ''
        fmt = fmt + u"{}"
        return fmt.format(self.nv_perf(box), sc)

    def sv_perfPercent(self, box=QuoteType.both, fmt="{:3.2f} %"):
        return fmt.format(self.nv_perfPercent(box))

    def sv_percentCash(self, box=QuoteType.both, fmt="{:3.2f} %"):
        return fmt.format(self.nv_percentCash(box))

    def sv_percentQuotes(self, box=QuoteType.both, fmt="{:3.2f} %"):
        return fmt.format(self.nv_percentQuotes(box))

    def sv_totalValue(self, fmt="{:.2f}", bDispCurrency=False):
        if bDispCurrency:
            sc = ' ' + self.currency_symbol() + ' '
        else:
            sc = ''
        fmt = fmt + u"{}"
        return fmt.format(self.nv_totalValue(), sc)

    def sv_perfTotal(self, fmt="{:.2f}", bDispCurrency=False):
        if bDispCurrency:
            sc = ' ' + self.currency_symbol() + ' '
        else:
            sc = ''
        fmt = fmt + u"{}"
        return fmt.format(self.nv_perfTotal(), sc)

    def sv_perfTotalPercent(self, fmt="{:3.2f} %"):
        return fmt.format(self.nv_perfTotalPercent())

# ============================================================================
# Portfolios
# ============================================================================
#
# usrdata/portfolio.txt CSV File format :
#   filename;username;accountref
# ============================================================================


class Portfolios(object):
    def __init__(self):
        debug('Portfolios:__init__')
        self._init_()

    def _init_(self):
        self.m_portfolios = {}

    def reinit(self):
        debug('Portfolios::reinit')
        for eachPortfolio in self.list():
            eachPortfolio.reinit()

    def list(self):
        items = list(self.m_portfolios.values())
        items.sort(key=Portfolio.key)
        return items

    def existPortfolio(self, fn):
        return fn in self.m_portfolios

    def delPortfolio(self, filename):
        if filename not in self.m_portfolios:
            return False
        else:
            debug('Portfolios::delPortfolio(): {}'.format(self.m_portfolios[filename]))
            self.m_portfolios[filename].remove()
            del self.m_portfolios[filename]
            return True

    def addPortfolio(self, filename, name, accountref, market, currency, vat, term, risk, indice):
        if filename in self.m_portfolios:
            return None
        else:
            self.m_portfolios[filename] = Portfolio(filename, name, accountref, market, currency, vat, term, risk, indice)
            debug('Portfolios::addPortfolio(): {}'.format(self.m_portfolios[filename]))
            return self.m_portfolios[filename]

    def editPortfolio(self, filename, name, accountref, market, currency, vat, term, risk, indice):
        if filename not in self.m_portfolios:
            return None
        else:
            del self.m_portfolios[filename]
            self.m_portfolios[filename] = Portfolio(filename, name, accountref, market, currency, vat, term, risk, indice)
            debug(u'Portfolios::editPortfolio(): {}'.format(self.m_portfolios[filename]))
            return self.m_portfolios[filename]

    def renamePortfolio(self, filename, newfilename):
        if filename not in self.m_portfolios:
            return None
        else:
            self.m_portfolios[filename].rename(newfilename)
            self.m_portfolios[newfilename] = self.m_portfolios[filename]
            del self.m_portfolios[filename]
            debug(u'Portfolios::renamePortfolio(): {} -> {}'.format(filename, newfilename))
            return self.m_portfolios[newfilename]

    def portfolio(self, fn):
        return self.m_portfolios.get(fn, None)

    def load(self, fn=None):
        debug('Portfolios:load()')

        # open and read the file to load these quotes information
        infile = itrade_csv.read(fn, os.path.join(itrade_config.dirUserData, 'portfolio.txt'))
        # scan each line to read each portfolio
        for eachLine in infile:
            item = itrade_csv.parse(eachLine, 6)
            if item:
                # info('{} :: {}'.format(eachLine, item))
                vat = country2vat(gMessage.getLang())
                if len(item) >= 5:
                    currency = item[4]
                    if len(item) >= 6:
                        vat = float(item[5])
                    else:
                        vat = 1.0
                    if len(item) >= 8:
                        term = int(item[6])
                        risk = int(item[7])
                    else:
                        term = 3
                        risk = 5
                    if len(item) >= 9:
                        indice = item[8]
                    else:
                        indice = getDefaultIndice(item[3])
                else:
                    currency = 'EUR'
                self.addPortfolio(item[0], item[1], item[2], item[3], currency, vat, term, risk, indice)

    def save(self, fn=None):
        debug('Portfolios:save()')

        # open and write the file with these quotes information
        itrade_csv.write(fn, os.path.join(itrade_config.dirUserData, 'portfolio.txt'), list(self.m_portfolios.values()))

# ============================================================================
# loadPortfolio
#
#   fn    filename reference
# ============================================================================


class currentCell(object):
    def __init__(self, f):
        self.f = f

    def __repr__(self):
        return '{}'.format(self.f)


def loadPortfolio(fn=None):
    # default portfolio reference
    if fn is None:
        defref = itrade_csv.read(None, os.path.join(itrade_config.dirUserData, 'default.txt'))
        if defref:
            item = itrade_csv.parse(defref[0], 1)
            fn = item[0]
        else:
            fn = 'default'
    debug('loadPortfolio %s', fn)

    # create the portfolio
    portfolios.reinit()
    p = portfolios.portfolio(fn)
    if p is None:
        # portfolio does not exist !
        print(u"Portfolio '{}' does not exist ... create it".format(fn))
        p = portfolios.addPortfolio(fn, fn, 'noref', 'EURONEXT', 'EUR', country2vat('fr'), 3, 5, getDefaultIndice('EURONEXT'))
        portfolios.save()

    # load properties
    p.loadProperties()

    # load stops
    p.loadStops()

    # load transactions then apply them
    p.loadOperations()
    p.applyOperations()

    # load fees rules
    # __fee p.loadFeesRules()

    # save current file
    scf = {}
    scf[0] = currentCell(fn)
    itrade_csv.write(None, os.path.join(itrade_config.dirUserData, 'default.txt'), list(scf.values()))

    # return the portfolio
    return p

# ============================================================================
# newPortfolio
#
#   fn    filename reference (shall be unique)
# ============================================================================


def newPortfolio(fn=None):
    debug('newPortfolio %s',  fn)

    # create the portfolio
    portfolios.reinit()
    p = portfolios.portfolio(fn)

    # save current file
    scf = {}
    scf[0] = currentCell(fn)
    itrade_csv.write(None, os.path.join(itrade_config.dirUserData, 'default.txt'), list(scf.values()))

    # return the portfolio
    return p

# ============================================================================
# CommandLine : -e / evaluate portfolio
# ============================================================================


def cmdline_evaluatePortfolio(year=2006):
    print('--- load current portfolio ---')
    p = loadPortfolio()
    print(u'... {}:{}:{} '.format(p.filename(), p.name(), p.accountref()))

    print('--- build a matrix -----------')
#    m = create_matrix(p.filename(), p)
    m = create_matrix(p.filename())

    print('--- liveupdate this matrix ---')
    m.update()
    m.saveTrades()

    print('--- evaluation ---------------')
    p.computeOperations(year)
    print(u' cumul. investment  : {:.2f}'.format(p.nv_invest()))
    print()
    print(u' total buy          : {:.2f}'.format(p.nv_buy(QuoteType.cash)))
    print(u' evaluation quotes  : {:.2f} ({:2.2f}% of portfolio)'.format(p.nv_value(QuoteType.cash), p.nv_percentQuotes(QuoteType.cash)))
    print(u' evaluation cash    : {:.2f} ({:2.2f}% of portfolio)'.format(p.nv_cash(), p.nv_percentCash(QuoteType.cash)))
    print(u' performance        : {:.2f} ({:2.2f}%)'.format(p.nv_perf(QuoteType.cash), p.nv_perfPercent(QuoteType.cash)))
    print()
    print(u' total credit (SRD) : {:.2f} (=={:.2f})'.format(p.nv_credit(), p.nv_buy(QuoteType.credit)))
    print(u' evaluation quotes  : {:.2f} ({:2.2f}% of portfolio)'.format(p.nv_value(QuoteType.credit), p.nv_percentQuotes(QuoteType.credit)))
    print(u' evaluation cash    : {:.2f} ({:2.2f}% of portfolio)'.format(p.nv_cash(), p.nv_percentCash(QuoteType.credit)))
    print(u' performance        : {:.2f} ({:2.2f}%)'.format(p.nv_perf(QuoteType.credit), p.nv_perfPercent(QuoteType.credit)))
    print()
    print(u' expenses (VAT, ...): {:.2f}'.format(p.nv_expenses()))
    print(u' total of transfers : {:.2f}'.format(p.nv_transfer()))
    print(u' appreciation       : {:.2f}'.format(p.nv_appreciation()))
    print(u' taxable amount     : {:.2f}'.format(p.nv_taxable()))
    print(u' amount of taxes    : {:.2f}'.format(p.nv_taxes()))
    print()
    print(u' evaluation total   : {:.2f} '.format(p.nv_totalValue()))
    print(u' global performance : {:.2f} ({:2.2f}%)'.format(p.nv_perfTotal(), p.nv_perfTotalPercent()))

    return p, m

# ============================================================================
# Export
# ============================================================================

portfolios = Portfolios()

# ============================================================================
# initPortfolioModule()
# ============================================================================

def initPortfolioModule():
    portfolios.load()

# ============================================================================
# Test
# ============================================================================

def main():
    setLevel(logging.INFO)
    itrade_config.app_header()
    initPortfolioModule()
    cmdline_evaluatePortfolio(2012)


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
