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
from datetime import *
import logging

# iTrade system
from itrade_logging import *
import itrade_datation
from itrade_quotes import quotes,QUOTE_CASH,QUOTE_CREDIT,QUOTE_BOTH
from itrade_matrix import *
from itrade_local import message,getLang
import itrade_csv
from itrade_currency import currency2symbol,currencies,convert
from itrade_vat import country2vat
from itrade_login import getLoginConnector
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
#       Y   detachment of coupon (cash on trade) - non taxable
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
OPERATION_DETACHMENT= 'Y'
OPERATION_DIVIDEND  = 'Z'
OPERATION_LIQUIDATION  = 'L'
OPERATION_QUOTE = 'Q'
OPERATION_REGISTER = 'W'

operation_desc = {
    OPERATION_BUY       : 'Portfolio_buy',
    OPERATION_BUY_SRD   : 'Portfolio_buy_srd',
    OPERATION_SELL      : 'Portfolio_sell',
    OPERATION_SELL_SRD  : 'Portfolio_sell_srd',
    OPERATION_CREDIT    : 'Portfolio_credit',
    OPERATION_DEBIT     : 'Portfolio_debit',
    OPERATION_FEE       : 'Portfolio_fee',
    OPERATION_INTEREST  : 'Portfolio_interest',
    OPERATION_SPLIT     : 'Portfolio_split',
    OPERATION_DETACHMENT: 'Portfolio_detachment',
    OPERATION_DIVIDEND  : 'Portfolio_dividend',
    OPERATION_LIQUIDATION : 'Portfolio_liquidation',
    OPERATION_QUOTE     : 'Portfolio_quote',
    OPERATION_REGISTER  : 'Portfolio_register'
}

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

operation_apply = {
    OPERATION_BUY       : True,
    OPERATION_BUY_SRD   : True,
    OPERATION_SELL      : True,
    OPERATION_SELL_SRD  : True,
    OPERATION_CREDIT    : False,
    OPERATION_DEBIT     : False,
    OPERATION_FEE       : False,
    OPERATION_INTEREST  : False,
    OPERATION_SPLIT     : False,
    OPERATION_DETACHMENT: True,
    OPERATION_DIVIDEND  : False,
    OPERATION_LIQUIDATION  : True,
    OPERATION_REGISTER  : True,
    OPERATION_QUOTE     : True
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

class Operation(object):
    def __init__(self,d,t,m,v,e,n,vat,ref):

        # decode the date (string) to convert to date
        if isinstance(d,date):
            self.m_date = d
        elif d[4]=='-':
            debug('Operation::__init__():%s: %d %d %d' % (d,long(d[0:4]),long(d[5:7]),long(d[8:10])));
            self.m_date = date(long(d[0:4]),long(d[5:7]),long(d[8:10]))
        else:
            debug('Operation::__init__():%s: %d %d %d' % (d,long(d[0:4]),long(d[4:6]),long(d[6:8])));
            self.m_date = date(long(d[0:4]),long(d[4:6]),long(d[6:8]))

        self.m_type = t
        self.m_value = float(v)
        self.m_number = long(n)
        self.m_expenses = float(e)
        self.m_vat = float(vat)
        self.m_ref = ref

        # support key or name or bad value
        if self.isQuote():
            # m : could be isin (old format) or key (new format)
            self.m_quote = quotes.lookupKey(m)
            if not self.m_quote:
                self.m_quote = quotes.lookupTicker(m)
                if self.m_quote:
                    self.m_name = self.m_quote.name()
                else:
                    lst = quotes.lookupISIN(m)
                    if len(lst)>0:
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

        #print 'Operation(): quote=%s name=%s' % (self.m_quote,self.m_name)

    def __repr__(self):
        if self.m_quote:
            return '%s;%s;%s;%f;%f;%d;%f' % (self.m_date, self.m_type, self.m_quote.key(), self.m_value, self.m_expenses, self.m_number, self.m_vat)
        else:
            return '%s;%s;%s;%f;%f;%d;%f' % (self.m_date, self.m_type, self.m_name, self.m_value, self.m_expenses, self.m_number, self.m_vat)

    def ref(self):
        return self.m_ref

    def nv_value(self):
        return self.m_value

    def sv_value(self):
        return '%.2f' % self.nv_value()

    def nv_expenses(self):
        return self.m_expenses

    def sv_expenses(self):
        return '%.2f' % self.nv_expenses()

    def nv_vat(self):
        return self.m_vat

    def sv_vat(self):
        return '%.2f' % self.nv_vat()

    def nv_number(self):
        if operation_number.has_key(self.m_type) and operation_number[self.m_type]:
            return self.m_number
        else:
            return 0

    def sv_number(self):
        return '%6d' % self.nv_number()

    def type(self):
        return self.m_type

    def isSRD(self):
        if operation_srd.has_key(self.m_type):
            return operation_srd[self.m_type]
        else:
            return False

    def setType(self,nt):
        self.m_type = nt
        return self.m_type

    def name(self):
        if self.m_name: return self.m_name
        return ""

    def date(self):
        return self.m_date

    def sv_date(self):
        return self.date().strftime('%x')

    def setDate(self,nd):
        self.m_date = nd
        return self.m_date

    def quote(self):
        if self.isQuote():
            return self.m_quote
        else:
            raise TypeError("quote(): operation::type() shall be S or B or Y or Z")

    def operation(self):
        if operation_desc.has_key(self.m_type):
            return message(operation_desc[self.m_type])
        else:
            return '? (%s)' % self.m_type

    def isCash(self):
        if operation_cash.has_key(self.m_type):
            return operation_cash[self.m_type]
        return self.isQuote()

    def isQuote(self):
        if operation_quote.has_key(self.m_type):
            return operation_quote[self.m_type]
        else:
            return False

    def sign(self):
        if operation_sign.has_key(self.m_type):
            return operation_sign[self.m_type]
        else:
            return '?'

    def description(self):
        if self.isQuote():
            if self.m_quote:
                return '%s (%s)' % (self.name(),self.m_quote.ticker())
            else:
                return '%s (?)' % self.name()
        else:
            return self.name()

    def apply(self,d=None):
        if self.m_type == OPERATION_SELL:
            if self.m_quote:
                debug('sell %s' % self.m_quote)
                max = self.m_quote.nv_number(QUOTE_CASH)
                if self.m_number>max:
                    self.m_number = max
                self.m_quote.sell(self.m_number,QUOTE_CASH)
        elif self.m_type == OPERATION_BUY:
            if self.m_quote:
                debug('buy %s' % self.m_quote)
                self.m_quote.buy(self.m_number,self.m_value,QUOTE_CASH)
        elif self.m_type == OPERATION_SELL_SRD:
            if self.m_quote:
                debug('sell SRD %s' % self.m_quote)
                max = self.m_quote.nv_number(QUOTE_CREDIT)
                if self.m_number>max:
                    self.m_number = max
                self.m_quote.sell(self.m_number,QUOTE_CREDIT)
        elif self.m_type == OPERATION_BUY_SRD:
            if self.m_quote:
                debug('buy SRD %s' % self.m_quote)
                self.m_quote.buy(self.m_number,self.m_value,QUOTE_CREDIT)
        elif self.m_type == OPERATION_QUOTE:
            if self.m_quote:
                debug('dividend/shares %s' % self.m_quote)
                self.m_quote.buy(self.m_number,0.0,QUOTE_CASH)
        elif self.m_type == OPERATION_REGISTER:
            if self.m_quote:
                debug('register/shares %s' % self.m_quote)
                self.m_quote.buy(self.m_number,self.m_value,QUOTE_CASH)
        elif self.m_type == OPERATION_DETACHMENT:
            if self.m_quote:
                debug('detachment %s / %d' % (self.m_quote,self.m_value))
                self.m_quote.buy(0,-self.m_value,QUOTE_CASH)
        elif self.m_type == OPERATION_LIQUIDATION:
            if self.m_quote:
                debug('liquidation %s / %d' % (self.m_quote,self.m_value))
                self.m_quote.transfertTo(self.m_number,self.m_expenses,QUOTE_CASH)

    def undo(self,d=None):
        if self.m_type == OPERATION_SELL:
            if self.m_quote:
                debug('undo-sell %s' % self.m_quote)
                self.m_quote.buy(self.m_number,self.m_value,QUOTE_CASH)
        elif self.m_type == OPERATION_BUY:
            if self.m_quote:
                debug('undo-buy %s' % self.m_quote)
                self.m_quote.sell(self.m_number,QUOTE_CASH)
        elif self.m_type == OPERATION_QUOTE:
            if self.m_quote:
                debug('undo-dividend/share %s' % self.m_quote)
                self.m_quote.sell(self.m_number,QUOTE_CASH)
        elif self.m_type == OPERATION_REGISTER:
            if self.m_quote:
                debug('undo-register %s' % self.m_quote)
                self.m_quote.sell(self.m_number,QUOTE_CASH)
        elif self.m_type == OPERATION_BUY_SRD:
            if self.m_quote:
                debug('undo-buy SRD %s' % self.m_quote)
                self.m_quote.sell(self.m_number,QUOTE_CREDIT)
        elif self.m_type == OPERATION_SELL_SRD:
            if self.m_quote:
                debug('undo-sell SRD %s' % self.m_quote)
                self.m_quote.buy(self.m_number,self.m_value,QUOTE_CREDIT)
        elif self.m_type == OPERATION_DETACHMENT:
            if self.m_quote:
                debug('undo-detachment %s' % self.m_quote)
                self.m_quote.buy(0,self.m_value,QUOTE_CASH)
        elif self.m_type == OPERATION_LIQUIDATION:
            if self.m_quote:
                debug('undo-liquidation %s / %d' % self.m_quote)
                self.m_quote.transfertTo(self.m_number,self.m_expenses,QUOTE_CREDIT)

    def nv_pvalue(self):
        if self.m_quote:
            if self.m_type == OPERATION_SELL:
                    return self.m_value - (self.m_quote.nv_pru(QUOTE_CASH) * self.m_number)
            if self.m_type == OPERATION_SELL_SRD:
                    return self.m_value - (self.m_quote.nv_pru(QUOTE_CREDIT) * self.m_number)
        return 0

    def sv_pvalue(self):
        return '%.2f' % self.nv_pvalue()

def isOperationTypeAQuote(type):
    if operation_quote.has_key(type):
        return operation_quote[type]
    else:
        return False

def isOperationTypeIncludeTaxes(type):
    if operation_incl_taxes.has_key(type):
        return operation_incl_taxes[type]
    else:
        return True

def isOperationTypeHasShareNumber(type):
    if operation_number.has_key(type):
        return operation_number[type]
    else:
        return False

def signOfOperationType(type):
    if operation_sign.has_key(type):
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
    def __init__(self,portfolio):
        debug('Operations:__init__(%s)' % portfolio)
        self.m_operations = {}
        self.m_portfolio = portfolio
        self.m_ref = 0

    def portfolio(self):
        return self.m_portfolio

    def list(self):
        items = self.m_operations.values()
        nlist = [(x.date(), x) for x in items]
        nlist.sort()
        nlist = [val for (key, val) in nlist]
        #print nlist
        return nlist

    def load(self,infile=None):
        infile = itrade_csv.read(infile,os.path.join(itrade_config.dirUserData,'default.operations.txt'))
        if infile:
            # scan each line to read each trade
            for eachLine in infile:
                item = itrade_csv.parse(eachLine,7)
                if item:
                    self.add(item,False)

    def save(self,outfile=None):
        itrade_csv.write(outfile,os.path.join(itrade_config.dirUserData,'default.operations.txt'),self.m_operations.values())

    def add(self,item,bApply):
        debug('Operations::add() before: 0:%s , 1:%s , 2:%s , 3:%s , 4:%s , 5:%s' % (item[0],item[1],item[2],item[3],item[4],item[5]))
        ll = len(item)
        if ll>=7:
            vat = item[6]
        else:
            vat = self.m_portfolio.vat()
        op = Operation(item[0],item[1],item[2],item[3],item[4],item[5],vat,self.m_ref)
        self.m_operations[self.m_ref] = op
        if bApply:
            op.apply()
        debug('Operations::add() after: %s' % self.m_operations)
        self.m_ref = self.m_ref + 1
        return op.ref()

    def remove(self,ref,bUndo):
        if bUndo:
            self.m_operations[ref].undo()
        del self.m_operations[ref]

    def get(self,ref):
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

    def __init__(self,filename='default',name='<Portfolio>',accountref='000000000',market='EURONEXT',currency='EUR',vat=1.0,term=3,risk=5,indice='FR0003500008'):
        debug('Portfolio::__init__ fn=%s name=%s account=%s' % (filename,name,accountref))

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
        return '%s;%s;%s;%s;%s;%f;%d;%d;%s' % (self.m_filename,self.m_name,self.m_accountref,self.m_market,self.m_currency,self.m_vat,self.m_term,self.m_risk,self.m_indice)

    def filenamepath(self,portfn,fn):
        return os.path.join(itrade_config.dirUserData,'%s.%s.txt' % (portfn,fn))

    def filepath(self,fn):
        return os.path.join(itrade_config.dirUserData,'%s.%s.txt' % (self.filename(),fn))

    def filename(self):
        return self.m_filename

    def key(self):
        return self.m_filename.lower()

    def accountref(self):
        return self.m_accountref

    def operations(self):
        return self.m_operations

    def date(self):
        return self.m_date

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

    # ---[ reinit the porfolio, associated services and quotes ]---------------

    def reinit(self):
        debug('Portfolio::%s::reinit' %(self.name()))
        self.logoutFromServices()
        quotes.reinit()
        self._init_()

    # ---[ File management for the porfolio ]----------------------------------

    def remove(self):
        # remove all files used by the portfolio

        fn = self.filepath('operations')
        try:
            os.remove(fn)
        except OSError:
            pass
        fn = self.filepath('matrix')
        try:
            os.remove(fn)
        except OSError:
            pass
        fn = self.filepath('fees')
        try:
            os.remove(fn)
        except OSError:
            pass
        fn = self.filepath('stops')
        try:
            os.remove(fn)
        except OSError:
            pass

    def rename(self,nname):
        # rename all files used by the portfolio

        fn = self.filepath('operations')
        nfn = self.filenamepath(nname,'operations')
        try:
            os.rename(fn,nfn)
        except OSError:
            pass
        fn = self.filepath('matrix')
        nfn = self.filenamepath(nname,'matrix')
        try:
            os.rename(fn,nfn)
        except OSError:
            pass
        fn = self.filepath('fees')
        nfn = self.filenamepath(nname,'fees')
        try:
            os.rename(fn,nfn)
        except OSError:
            pass
        fn = self.filepath('stops')
        nfn = self.filenamepath(nname,'stops')
        try:
            os.rename(fn,nfn)
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

    def applyFeeRules(self,v,all=True):
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

    def applyOperations(self,d=None):
        debug('applyOperations date<=%s' % d)
        for eachOp in self.m_operations.list():
            debug('applyOperations: %s' % eachOp)
            if d==None or d>=eachOp.date():
                typ = eachOp.type()
                if operation_apply.has_key(typ) and operation_apply[typ]:
                    eachOp.apply(d)
            else:
                info('ignore %s' % (eachOp.name()))

    # --- [ manage login to services ] ----------------------------------------

    def loginToServices(self,quote=None):

        def login(quote):
            name = quote.liveconnector(bForceLive=True).name()
            #print 'loginToServices:',quote.ticker(),name
            if not maperr.has_key(name):
                con = getLoginConnector(name)
                if con:
                    if not con.logged():
                        print 'login to service :',name
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
            for eachQuote in quotes.list():
                if eachQuote.isMatrix():
                    name = eachQuote.liveconnector().name()
                    if not maperr.has_key(name):
                        con = getLoginConnector(name)
                        if con:
                            if con.logged():
                                print 'logout from service :',name
                                maperr[name] = con.logout()

    # --- [ manage multi-currency on the portfolio ] --------------------------

    def setupCurrencies(self):
        currencies.reset()
        for eachQuote in quotes.list():
            if eachQuote.isMatrix():
                currencies.inuse(self.m_currency,eachQuote.currency(),bInUse=True)

    def is_multicurrencies(self):
        for eachQuote in quotes.list():
            if eachQuote.isMatrix():
                if eachQuote.currency()!=self.m_currency:
                    return True
        return False

    # --- [ compute the operations ] ------------------------------------------

    def sameyear(self,op,cd=None):
        if cd==None:
            cd = date.today().year
        if cd == op.date().year:
            return True
        else:
            return False

    def computeOperations(self,cd=None):
        self.reset()
        for eachOp in self.m_operations.list():
            if eachOp.type() == OPERATION_CREDIT:
                debug('credit %s : + %f' % (eachOp.name(),eachOp.nv_value()))
                self.m_cCash = self.m_cCash + eachOp.nv_value()
                self.m_cInvest = self.m_cInvest + eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
            elif eachOp.type() == OPERATION_DEBIT:
                debug('debit %s : - %f' % (eachOp.name(),eachOp.nv_value()))
                self.m_cCash = self.m_cCash - eachOp.nv_value()
                # __x self.m_cInvest = self.m_cInvest - eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
            elif eachOp.type() == OPERATION_BUY:
                debug('buy %s/%s : %d for %f' % (eachOp.name(),eachOp.quote(),eachOp.nv_number(),eachOp.nv_value()))
                self.m_cCash = self.m_cCash - eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
            elif eachOp.type() == OPERATION_BUY_SRD:
                debug('buy SRD %s/%s : %d for %f' % (eachOp.name(),eachOp.quote(),eachOp.nv_number(),eachOp.nv_value()))
                self.m_cCredit = self.m_cCredit + eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
            elif eachOp.type() == OPERATION_SELL:
                debug('sell %s/%s : %d for %f' % (eachOp.name(),eachOp.quote(),eachOp.nv_number(),eachOp.nv_value()))
                self.m_cCash = self.m_cCash + eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
                    self.m_cTransfer = self.m_cTransfer + eachOp.nv_value() + eachOp.nv_expenses()
                    self.m_cTaxable = self.m_cTaxable + eachOp.nv_pvalue()
                    self.m_cAppreciation = self.m_cAppreciation + eachOp.nv_pvalue()
            elif eachOp.type() == OPERATION_SELL_SRD:
                debug('sell SRD %s/%s : %d for %f' % (eachOp.name(),eachOp.quote(),eachOp.nv_number(),eachOp.nv_value()))
                self.m_cCredit = self.m_cCredit - eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
                    self.m_cTransfer = self.m_cTransfer + eachOp.nv_value() + eachOp.nv_expenses()
            elif eachOp.type() == OPERATION_FEE:
                debug('fee %s: %f' % (eachOp.name(),eachOp.nv_value()))
                self.m_cCash = self.m_cCash - eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
            elif eachOp.type() == OPERATION_LIQUIDATION:
                debug('liquidation %s: %f' % (eachOp.name(),eachOp.nv_value()))
                self.m_cCash = self.m_cCash + eachOp.nv_value()
                self.m_cCredit = self.m_cCredit + (eachOp.nv_value() + eachOp.nv_expenses())
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
                    self.m_cTaxable = self.m_cTaxable + eachOp.nv_value()
                    self.m_cAppreciation = self.m_cAppreciation + eachOp.nv_value()
                    quote = eachOp.quote()
                    if quote:
                        pv = eachOp.nv_number() * quote.nv_pru(QUOTE_CREDIT)
                        self.m_cTaxable = self.m_cTaxable + pv
                        self.m_cAppreciation = self.m_cAppreciation + pv
            elif eachOp.type() == OPERATION_INTEREST:
                debug('interest %s : %f' % (eachOp.name(),eachOp.nv_value()))
                self.m_cCash = self.m_cCash + eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
                    #self.m_cTaxable = self.m_cTaxable + eachOp.nv_value()
                    self.m_cAppreciation = self.m_cAppreciation + eachOp.nv_value()
            elif eachOp.type() == OPERATION_DETACHMENT:
                debug('detach %s/%s : %f' % (eachOp.name(),eachOp.quote(),eachOp.nv_value()))
                self.m_cCash = self.m_cCash + eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
                    #self.m_cTaxable = self.m_cTaxable + eachOp.nv_value()
                    self.m_cAppreciation = self.m_cAppreciation + eachOp.nv_value()
            elif eachOp.type() == OPERATION_DIVIDEND:
                debug('dividend %s/%s : %f' % (eachOp.name(),eachOp.quote(),eachOp.nv_value()))
                self.m_cCash = self.m_cCash + eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
                    self.m_cTaxable = self.m_cTaxable + eachOp.nv_value()
                    self.m_cAppreciation = self.m_cAppreciation + eachOp.nv_value()
            elif eachOp.type() == OPERATION_QUOTE:
                debug('dividend/share %s/%s : %f' % (eachOp.name(),eachOp.quote(),eachOp.nv_value()))
                pass
            elif eachOp.type() == OPERATION_REGISTER:
                debug('register/share %s/%s : %f' % (eachOp.name(),eachOp.quote(),eachOp.nv_value()))
                self.m_cInvest = self.m_cInvest + eachOp.nv_value()
            else:
                raise TypeError("computeOperations(): operation::type() unknown %s",eachOp.type())

    # --- [ compute the value ] -----------------------------------------------

    def computeValue(self):
        self.m_cDIRValue = 0.0
        self.m_cSRDValue = 0.0
        for eachQuote in quotes.list():
            if eachQuote.isTraded():
                self.m_cDIRValue = self.m_cDIRValue + eachQuote.nv_pv(self.m_currency,QUOTE_CASH)
                self.m_cSRDValue = self.m_cSRDValue + eachQuote.nv_pv(self.m_currency,QUOTE_CREDIT)

    def computeBuy(self):
        self.m_cDIRBuy = 0.0
        self.m_cSRDBuy = 0.0
        for eachQuote in quotes.list():
            if eachQuote.isTraded():
                self.m_cDIRBuy = self.m_cDIRBuy + eachQuote.nv_pr(QUOTE_CASH)
                self.m_cSRDBuy = self.m_cSRDBuy + eachQuote.nv_pr(QUOTE_CREDIT)

    # --- [ operations API ] --------------------------------------------------

    def addOperation(self,item):
        self.m_operations.add(item,True)

    def delOperation(self,ref):
        self.m_operations.remove(ref,True)

    def getOperation(self,ref):
        return self.m_operations.get(ref)

    # --- [ value API ] -------------------------------------------------------

    def nv_cash(self,currency=None):
        retval = self.m_cCash
        if currency:
            retval = convert(currency,self.m_currency,retval)
        return retval

    def nv_credit(self,currency=None):
        retval = self.m_cCredit
        if currency:
            retval = convert(currency,self.m_currency,retval)
        return retval

    def nv_invest(self):
        return self.m_cInvest

    def nv_value(self,box=QUOTE_BOTH):
        # __x compute it !
        self.computeValue()
        if box==QUOTE_CASH:
            return self.m_cDIRValue
        if box==QUOTE_CREDIT:
            return self.m_cSRDValue
        else:
            return self.m_cDIRValue + self.m_cSRDValue

    def nv_buy(self,box=QUOTE_BOTH):
        # __x compute it !
        self.computeBuy()
        if box==QUOTE_CASH:
            return self.m_cDIRBuy
        if box==QUOTE_CREDIT:
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

    def nv_perf(self,box=QUOTE_BOTH):
        #info('nv_perf=%f'% (self.nv_value(box) - self.nv_buy(box)))
        return self.nv_value(box) - self.nv_buy(box)

    def nv_perfPercent(self,box=QUOTE_BOTH):
        n = self.nv_value(box)
        b = self.nv_buy(box)
        if n==0.0 or b==0.0:
            return 0.0
        return ((n*100.0) / b) - 100

    def nv_totalValue(self):
        return self.nv_value(QUOTE_BOTH) + self.nv_cash() - self.m_cCredit

    def nv_perfTotal(self):
        return self.nv_totalValue() - self.nv_invest()

    def nv_perfTotalPercent(self):
        n = self.nv_totalValue()
        i = self.nv_invest()
        if n==0.0 or i==0.0:
            return 0.0
        return ((n*100.0) / i) - 100

    def nv_percentCash(self,box=QUOTE_BOTH):
        total = self.nv_value(box) + self.nv_cash()
        if total==0.0:
            return 0.0
        else:
            return (total-self.nv_value(box))/total*100.0

    def nv_percentQuotes(self,box=QUOTE_BOTH):
        total = self.nv_value(box) + self.nv_cash()
        if total==0.0:
            return 0.0
        else:
            return (total-self.nv_cash())/total*100.0

    # --- [ string API ] ------------------------------------------------------

    def sv_cash(self,currency=None,fmt="%.2f",bDispCurrency=False):
        if bDispCurrency:
            sc = ' '+self.currency_symbol()+' '
        else:
            sc = ''
        fmt = fmt + "%s"
        return fmt % (self.nv_cash(),sc)

    def sv_credit(self,currency=None,fmt="%.2f",bDispCurrency=False):
        if bDispCurrency:
            sc = ' '+self.currency_symbol()+' '
        else:
            sc = ''
        fmt = fmt + "%s"
        return fmt % (self.nv_credit(),sc)

    def sv_taxes(self,fmt="%.2f",bDispCurrency=False):
        if bDispCurrency:
            sc = ' '+self.currency_symbol()+' '
        else:
            sc = ''
        fmt = fmt + "%s"
        return fmt % (self.nv_taxes(),sc)

    def sv_expenses(self,fmt="%.2f",bDispCurrency=False):
        if bDispCurrency:
            sc = ' '+self.currency_symbol()+' '
        else:
            sc = ''
        fmt = fmt + "%s"
        return fmt % (self.nv_expenses(),sc)

    def sv_transfer(self,fmt="%.2f",bDispCurrency=False):
        if bDispCurrency:
            sc = ' '+self.currency_symbol()+' '
        else:
            sc = ''
        fmt = fmt + "%s"
        return fmt % (self.nv_transfer(),sc)

    def sv_taxable(self,fmt="%.2f",bDispCurrency=False):
        if bDispCurrency:
            sc = ' '+self.currency_symbol()+' '
        else:
            sc = ''
        fmt = fmt + "%s"
        return fmt % (self.nv_taxable(),sc)

    def sv_appreciation(self,fmt="%.2f",bDispCurrency=False):
        if bDispCurrency:
            sc = ' '+self.currency_symbol()+' '
        else:
            sc = ''
        fmt = fmt + "%s"
        return fmt % (self.nv_appreciation(),sc)

    def sv_invest(self,fmt="%.2f",bDispCurrency=False):
        if bDispCurrency:
            sc = ' '+self.currency_symbol()+' '
        else:
            sc = ''
        fmt = fmt + "%s"
        return fmt % (self.nv_invest(),sc)

    def sv_value(self,box=QUOTE_BOTH,fmt="%.2f",bDispCurrency=False):
        if bDispCurrency:
            sc = ' '+self.currency_symbol()+' '
        else:
            sc = ''
        fmt = fmt + "%s"
        return fmt % (self.nv_value(box),sc)

    def sv_buy(self,box=QUOTE_BOTH,fmt="%.2f",bDispCurrency=False):
        if bDispCurrency:
            sc = ' '+self.currency_symbol()+' '
        else:
            sc = ''
        fmt = fmt + "%s"
        return fmt % (self.nv_buy(box),sc)

    def sv_perf(self,box=QUOTE_BOTH,fmt="%.2f",bDispCurrency=False):
        if bDispCurrency:
            sc = ' '+self.currency_symbol()+' '
        else:
            sc = ''
        fmt = fmt + "%s"
        return fmt % (self.nv_perf(box),sc)

    def sv_perfPercent(self,box=QUOTE_BOTH,fmt="%3.2f %%"):
        return fmt % self.nv_perfPercent(box)

    def sv_percentCash(self,box=QUOTE_BOTH,fmt="%3.2f %%"):
        return fmt % self.nv_percentCash(box)

    def sv_percentQuotes(self,box=QUOTE_BOTH,fmt="%3.2f %%"):
        return fmt % self.nv_percentQuotes(box)

    def sv_totalValue(self,fmt="%.2f",bDispCurrency=False):
        if bDispCurrency:
            sc = ' '+self.currency_symbol()+' '
        else:
            sc = ''
        fmt = fmt + "%s"
        return fmt % (self.nv_totalValue(),sc)

    def sv_perfTotal(self,fmt="%.2f",bDispCurrency=False):
        if bDispCurrency:
            sc = ' '+self.currency_symbol()+' '
        else:
            sc = ''
        fmt = fmt + "%s"
        return fmt % (self.nv_perfTotal(),sc)

    def sv_perfTotalPercent(self,fmt="%3.2f %%"):
        return fmt % self.nv_perfTotalPercent()

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
        #items = self.m_portfolios.values()
        #nlist = [(x.filename(), x) for x in items]
        #nlist.sort()
        #nlist = [val for (key, val) in nlist]
        ##print nlist
        #return nlist
        items = self.m_portfolios.values()
        items.sort(key=Portfolio.key)
        return items

    def existPortfolio(self,fn):
        return self.m_portfolios.has_key(fn)

    def delPortfolio(self,filename):
        if not self.m_portfolios.has_key(filename):
            return False
        else:
            debug('Portfolios::delPortfolio(): %s' % self.m_portfolios[filename])
            self.m_portfolios[filename].remove()
            del self.m_portfolios[filename]
            return True

    def addPortfolio(self,filename,name,accountref,market,currency,vat,term,risk,indice):
        if self.m_portfolios.has_key(filename):
            return None
        else:
            self.m_portfolios[filename] = Portfolio(filename,name,accountref,market,currency,vat,term,risk,indice)
            debug('Portfolios::addPortfolio(): %s' % self.m_portfolios[filename])
            return self.m_portfolios[filename]

    def editPortfolio(self,filename,name,accountref,market,currency,vat,term,risk,indice):
        if not self.m_portfolios.has_key(filename):
            return None
        else:
            del self.m_portfolios[filename]
            self.m_portfolios[filename] = Portfolio(filename,name,accountref,market,currency,vat,term,risk,indice)
            debug('Portfolios::editPortfolio(): %s' % self.m_portfolios[filename])
            return self.m_portfolios[filename]

    def renamePortfolio(self,filename,newfilename):
        if not self.m_portfolios.has_key(filename):
            return None
        else:
            self.m_portfolios[filename].rename(newfilename)
            self.m_portfolios[newfilename] = self.m_portfolios[filename]
            del self.m_portfolios[filename]
            debug('Portfolios::renamePortfolio(): %s -> %s' % (filename,newfilename))
            return self.m_portfolios[newfilename]

    def portfolio(self,fn):
        if self.m_portfolios.has_key(fn):
            return self.m_portfolios[fn]
        else:
            return None

    def load(self,fn=None):
        debug('Portfolios:load()')

        # open and read the file to load these quotes information
        infile = itrade_csv.read(fn,os.path.join(itrade_config.dirUserData,'portfolio.txt'))
        if infile:
            # scan each line to read each portfolio
            for eachLine in infile:
                item = itrade_csv.parse(eachLine,6)
                if item:
                    #info('%s :: %s' % (eachLine,item))
                    vat = country2vat(getLang())
                    if len(item)>=5:
                        currency = item[4]
                        if len(item)>=6:
                            vat = float(item[5])
                        else:
                            vat = 1.0
                        if len(item)>=8:
                            term = int(item[6])
                            risk = int(item[7])
                        else:
                            term = 3
                            risk = 5
                        if len(item)>=9:
                            indice = item[8]
                        else:
                            indice = getDefaultIndice(item[3])
                    else:
                        currency = 'EUR'
                    self.addPortfolio(item[0],item[1],item[2],item[3],currency,vat,term,risk,indice)

    def save(self,fn=None):
        debug('Portfolios:save()')

        # open and write the file with these quotes information
        itrade_csv.write(fn,os.path.join(itrade_config.dirUserData,'portfolio.txt'),self.m_portfolios.values())

# ============================================================================
# loadPortfolio
#
#   fn    filename reference
# ============================================================================

class currentCell(object):
    def __init__(self,f):
        self.f = f

    def __repr__(self):
        return '%s' % (self.f)

def loadPortfolio(fn=None):
    # default portfolio reference
    if fn==None:
        defref = itrade_csv.read(None,os.path.join(itrade_config.dirUserData,'default.txt'))
        if defref:
            item = itrade_csv.parse(defref[0],1)
            fn = item[0]
        else:
            fn = 'default'
    debug('loadPortfolio %s',fn)

    # create the porfolio
    portfolios.reinit()
    p = portfolios.portfolio(fn)
    if p==None:
        # portfolio does not exist !
        print "Portfolio '%s' does not exist ... create it" % fn
        p = portfolios.addPortfolio(fn,fn,'noref','EURONEXT','EUR',country2vat('fr'), 3, 5,getDefaultIndice('EURONEXT'))
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
    itrade_csv.write(None,os.path.join(itrade_config.dirUserData,'default.txt'),scf.values())

    # return the portfolio
    return p

# ============================================================================
# newPortfolio
#
#   fn    filename reference (shall be unique)
# ============================================================================

def newPortfolio(fn=None):
    debug('newPortfolio %s',fn)

    # create the porfolio
    portfolios.reinit()
    p = portfolios.portfolio(fn)
    if p==None:
        # portfolio does not exist !
        pass

    # save current file
    scf = {}
    scf[0] = currentCell(fn)
    itrade_csv.write(None,os.path.join(itrade_config.dirUserData,'default.txt'),scf.values())

    # return the portfolio
    return p

# ============================================================================
# CommandLine : -e / evaluate portfolio
# ============================================================================

def cmdline_evaluatePortfolio(year=2006):

    print '--- load current portfolio ---'
    p = loadPortfolio()
    print '... %s:%s:%s ' % (p.filename(),p.name(),p.accountref())

    print '--- build a matrix -----------'
    m = createMatrix(p.filename(),p)

    print '--- liveupdate this matrix ---'
    m.update()
    m.saveTrades()

    print '--- evaluation ---------------'
    p.computeOperations(year)
    print ' cumul. investment  : %.2f' % p.nv_invest()
    print
    print ' total buy          : %.2f' % p.nv_buy(QUOTE_CASH)
    print ' evaluation quotes  : %.2f (%2.2f%% of portfolio)' % (p.nv_value(QUOTE_CASH),p.nv_percentQuotes(QUOTE_CASH))
    print ' evaluation cash    : %.2f (%2.2f%% of portfolio)' % (p.nv_cash(),p.nv_percentCash(QUOTE_CASH))
    print ' performance        : %.2f (%2.2f%%)' % (p.nv_perf(QUOTE_CASH),p.nv_perfPercent(QUOTE_CASH))
    print
    print ' total credit (SRD) : %.2f (==%.2f)' % (p.nv_credit(),p.nv_buy(QUOTE_CREDIT))
    print ' evaluation quotes  : %.2f (%2.2f%% of portfolio)' % (p.nv_value(QUOTE_CREDIT),p.nv_percentQuotes(QUOTE_CREDIT))
    print ' evaluation cash    : %.2f (%2.2f%% of portfolio)' % (p.nv_cash(),p.nv_percentCash(QUOTE_CREDIT))
    print ' performance        : %.2f (%2.2f%%)' % (p.nv_perf(QUOTE_CREDIT),p.nv_perfPercent(QUOTE_CREDIT))
    print
    print ' expenses (VAT, ...): %.2f' % p.nv_expenses()
    print ' total of transfers : %.2f' % p.nv_transfer()
    print ' appreciation       : %.2f' % p.nv_appreciation()
    print ' taxable amount     : %.2f' % p.nv_taxable()
    print ' amount of taxes    : %.2f' % p.nv_taxes()
    print
    print ' evaluation total   : %.2f ' % p.nv_totalValue()
    print ' global performance : %.2f (%2.2f%%)' % (p.nv_perfTotal(),p.nv_perfTotalPercent())

    return (p,m)

# ============================================================================
# Export
# ============================================================================

try:
    ignore(portfolios)
except NameError:
    portfolios = Portfolios()

# ============================================================================
# initPortfolioModule()
# ============================================================================

def initPortfolioModule():
    portfolios.load()

# ============================================================================
# Test
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    initPortfolioModule()

    cmdline_evaluatePortfolio(2006)

# ============================================================================
# That's all folks !
# ============================================================================
