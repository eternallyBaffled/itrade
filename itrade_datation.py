#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_datation.py
#
# Description: Datation
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
# 2005-01-09    dgil  Wrote it from scratch
# 2005-08-15    dgil  Add indexation system (trade can be referenced by index
#                     or by date)
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from __future__ import absolute_import
from datetime import datetime, timedelta, date
import time
import logging
import re

# iTrade system
import itrade_config
from itrade_logging import setLevel, info, debug
from itrade_local import getShortDateFmt
import itrade_csv

# ============================================================================
# some patterns for date
# ============================================================================

re_p3_1 = re.compile(r'\d\d\d\d-\d\d-\d\d')
re_p3_2 = re.compile(r'\d\d\d\d/\d\d/\d\d')
re_p4_1 = re.compile(r'\d\d-\d\d-\d\d')
re_p4_2 = re.compile(r'\d\d-\d\d-\d\d\d\d')
re_p4_3 = re.compile(r'\d\d/\d\d/\d\d')
re_p4_4 = re.compile(r'\d\d/\d\d/\d\d\d\d')

# ============================================================================
# some convertion
# ============================================================================

MONTH2NUM = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
  'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

Y2KCUTOFF = 60

def yy2yyyy(yy):
    yy = int(yy) % 100
    if yy<Y2KCUTOFF:
        return repr(yy+2000)
    else:
        return repr(yy+1900)

def dd_mmm_yy2yyyymmdd(d):
    d = d.split('-')
    day = '{:02d}'.format(int(d[0]))
    month = '{:02d}'.format(MONTH2NUM[d[1]])
    year = yy2yyyy(d[2])
    return year + month + day

def jjmmaa2yyyymmdd(d):
    d = d.split('/')
    day = '{:02d}'.format(int(d[0]))
    month = '{:02d}'.format(int(d[1]))
    year = yy2yyyy(d[2])
    return year + month + day

# ============================================================================
# date2str
# ============================================================================

def date2str(dt,bDisplayShort):
    if dt:
        if bDisplayShort:
            return dt.strftime(getShortDateFmt())
        else:
            return dt.strftime('%x')
    return ''

# ============================================================================
# Calendar
#
# singleton object to manage market day closed
# ============================================================================

MONDAY = 0
TUESDAY = 1
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SATURDAY = 5
SUNDAY = 6


class Calendar(object):
    def __init__(self):
        self.m_closed = {}
        self.m_index = {}
        self.m_date = {}
        self.m_srd = {}
        self.m_maxidx = 0
        self.load()
        self.indexme()

    # --- [ properties ] --------------------------------------

    def isopen(self, d, market=None):
        if type(d) == type('') or isinstance(d, date):
            d = Datation(d)
        if not isinstance(d, Datation):
            raise TypeError("parameter shall be date, Datation or string object")

        if d.is_weekend():
            return False

        k = self.key(d, market)
        debug('isopen {} k={}: ? '.format(d, k))

        # is it a special day ?
        if k in self.m_closed:
            return False

        # market should be opened !
        return True

    def issrd(self,d,market=None):
        if type(d)==type('') or isinstance(d,date):
            d = Datation(d)
        if not isinstance(d, Datation):
            raise TypeError("parameter shall be date, Datation or string object")

        debug('issrd {} ? {} '.format(d, self.m_srd))

        if d.is_weekend():
            return False

        k = self.key(d, market)
        debug('issrd {} k={}: ? '.format(d, k))

        # is it an SRD day ?
        if k in self.m_srd:
            return True

        # normal day
        return False

    def srd(self, d, market=None):
        if type(d)==type('') or isinstance(d,date):
            d = Datation(d)
        if not isinstance(d, Datation):
            raise TypeError("parameter shall be date, Datation or string object")

        k = self.key(d, market)

        # is it an SRD day ?
        return self.m_srd.get(k)

    # --- [ key management ] --------------------------------------

    def key(self,d,market=None):
        # default Market Entry Place
        if market is None:
            market = 'EURONEXT'

        # key : date + market
        return u'{}{}'.format(market, d)

    # --- [ file management ] -------------------------------------

    def addClosed(self, d, market=None, title=None):
        # default Market Entry Place
        if market is None:
            market = 'EURONEXT'

        # normalize the date notation !
        d = Datation(d)
        k = self.key(d, market)

        if k in self.m_closed:
            debug('Calendar::addClosed(): {} k={}: {} - already !'.format(d, k, self.m_closed[k]))
            return False
        else:
            # add it in the closed list
            self.m_closed[k] = (market, title)
            debug('Calendar::addClosed(): {} k={}: {} - added'.format(d, k, self.m_closed[k]))
            return True

    def addSRD(self, d, market=None, title=None):
        # default Market Entry Place
        if market is None:
            market = 'EURONEXT'

        # normalize the date notation !
        d = Datation(d)
        k = self.key(d,market)

        if k in self.m_srd:
            debug('Calendar::addSRD(): {} k={}: {} - already !'.format(d, k, self.m_srd[k]))
            return False
        else:
            # add it in the srd list
            self.m_srd[k] = (market,title)
            debug('Calendar::addSRD(): {} k={}: {} - added'.format(d, k, self.m_srd[k]))
            return True

    def load_closure(self, fn=None):
        # open and read the file to load the closure information
        #        infile = itrade_csv.read(fn, os.path.join(itrade_config.dirSysData, 'closed.txt'))
        infile = itrade_csv.read(fn, itrade_config.default_closure_file())
        # scan each line to read each quote
        for eachLine in infile:
            item = itrade_csv.parse(eachLine, 3)
            if item:
                if len(item) > 2:
                    self.addClosed(item[0], item[1], item[2])
                else:
                    info("can't import item={}".format(item))

    def load_srd(self, fn=None):
        # open and read the file to load the SRD information
#        infile = itrade_csv.read(fn, os.path.join(itrade_config.dirSysData, 'srd.txt'))
        infile = itrade_csv.read(fn, itrade_config.default_srd_file())
        # scan each line to read each quote
        for eachLine in infile:
            item = itrade_csv.parse(eachLine, 3)
            if item:
                if len(item) > 2:
                    self.addSRD(item[0], item[1], item[2])
                else:
                    info("can't import item={}".format(item))

    def load(self):
        self.load_closure()
        self.load_srd()

    # --- [ index management ] ------------------------------------

    def indexme(self):
        self.m_maxidx = 0
        year = date.today().year - itrade_config.numTradeYears + 1
        num = (itrade_config.numTradeYears * (12*31)) + 5
        while num > 0:
            # print('--- index datation --{:d}--'.format(year))
            month = 1
            while month <= 12 and num > 0:
                # print('--- index datation --{:d}--'.format(month))
                day = 1
                while day <= 31 and num > 0:
                    # print('--- index datation --{:d}--'.format(day))
                    try:
                        d = date(year, month, day)
                        #d = Datation(d)
                        if d.weekday() < SATURDAY:
                        #if self.isopen(d):
                            # print('num={:d} - index {} = {:d}'.format(num, d, self.m_maxidx))
                            self.m_index[d] = self.m_maxidx
                            self.m_date[self.m_maxidx] = d
                            self.m_maxidx = self.m_maxidx + 1
                        else:
                            # print('num={:d} - index {} = closed'.format(num, d))
                            pass
                    except ValueError:
                        pass
                    day = day + 1
                    num = num - 1
                month = month + 1
            year = year + 1

    def index(self, _date):
        if _date in self.m_index:
            return self.m_index[_date]
        else:
            return -1

    def date(self, _index):
        if _index in self.m_date:
            return self.m_date[_index]
        else:
            return None

    def lastindex(self):
        return self.m_maxidx - 1

    def lastdate(self):
        return self.date(self.lastindex())

# ============================================================================
# Datation
#
# this object encapsulates a date object with the following properties :
# - really read only object
# - constructed by a date object or a string
# - use calendar singleton object with prev / next
# ============================================================================

class Datation(object):
    def __init__(self, d):
        #debug('Datation::__init__():{}: instance={}'.format(d, type(d)))
        if isinstance(d, date):
            self.m_date = d
        else:
            if d[4] == '-':
                #debug('Datation::__init__():{}: {:d} {:d} {:d}'.format(d, int(d[0:4]), int(d[5:7]), int(d[8:10])))
                self.m_date = date(int(d[0:4]), int(d[5:7]), int(d[8:10]))
            else:
                #debug('Datation::__init__():{}: {:d} {:d} {:d}'.format(d, int(d[0:4]), int(d[4:6]), int(d[6:8])))
                self.m_date = date(int(d[0:4]), int(d[4:6]), int(d[6:8]))

    def __str__(self):
        return '{:4d}{:2d}{:2d}'.format(self.m_date.year, self.m_date.month, self.m_date.day)

    def __repr__(self):
        return '{:4d}-{:2d}-{:2d}'.format(self.m_date.year, self.m_date.month, self.m_date.day)

    def __hash__(self):
        return self.m_date.toordinal()

    def __gt__(self, other):
        return self.m_date > other.m_date

    def year(self):
        return self.m_date.year

    def month(self):
        return self.m_date.month

    def day(self):
        return self.m_date.day

    def _weekday(self):
        return self.m_date.weekday()

    def is_weekend(self):
        return self._weekday() >= SATURDAY

    def date(self):
        return self.m_date

    def nextopen(self, market=None):
        ndate = self.m_date + timedelta(1)
        while not gCal.isopen(ndate, market):
            ndate = ndate + timedelta(1)
        return Datation(ndate)

    def prevopen(self, market=None):
        ndate = self.m_date - timedelta(1)
        while not gCal.isopen(ndate, market):
            ndate = ndate - timedelta(1)
        return Datation(ndate)

    def nearopen(self, market=None):
        ndate = self.m_date
        while not gCal.isopen(ndate, market):
            ndate = ndate - timedelta(1)
        return Datation(ndate)

    def index(self):
        return gCal.index(self.m_date)

# ============================================================================
# Install the Calendar system
# ============================================================================


gCal = Calendar()

# ============================================================================
# Test
# ============================================================================

def main():
    setLevel(logging.INFO)
    itrade_config.app_header()
    info('test0 1=={}'.format(gCal.addClosed('2010-12-31')))
    info('test0 0=={}'.format(gCal.addClosed('20101231')))
    info('test1 0=={}'.format(gCal.isopen('2011-01-01')))
    info('test2 0=={}'.format(gCal.isopen('20110101')))
    info('test3 1=={}'.format(gCal.isopen('20110104')))
    info('test4 0=={}'.format(gCal.isopen('20101231')))  # closed in default market (PAR)
    info('test4 1=={}'.format(gCal.isopen('20101231', 'TOK')))  # but open in other market
    info('test5 20110104=={}'.format(Datation('20110104')))
    info('test6 20110105=={}'.format(Datation('20110104').nextopen()))
    info('test7 20110103=={}'.format(Datation('20110104').prevopen()))
    info('test8 20101230=={}'.format(Datation('20110103').prevopen()))
    info('test9 20101230=={}'.format(Datation('20101231').prevopen()))
    info('test10 20100130>20100101 == {}'.format(Datation('20100130') > Datation('20100101')))
    info('test10 20100101>20100130 == {}'.format(Datation('20100101') > Datation('20100130')))
    info('test10 20100227>20100101 == {}'.format(Datation('20100227') > Datation('20100101')))
    info('test10 20100101>20100227 == {}'.format(Datation('20100101') > Datation('20100227')))
    info('test11 20110814 index is {:d} == -1'.format(Datation('20110814').index()))
    info('test11 20110815 index is {:d} != -1'.format(Datation('20110815').index()))
    info('test11 20110816 index is {:d} != -1'.format(Datation('20110816').index()))
    info('test11 20111231 index is {:d} == -1'.format(Datation('20111231').index()))
    info('test11 20110102 index is {:d} == -1'.format(Datation('20110102').index()))
    info('test11 20110103 index is {:d} != -1'.format(Datation('20110103').index()))
    print('lastindex = {:d}, lastdate = {}'.format(gCal.lastindex(), gCal.lastdate()))
    ts = '20050816'
    dt = datetime(*time.strptime(ts.strip('"'), '%Y%m%d')[:6])
    print('{} = {}'.format(ts, dt))
    ts = '2005-08-16'
    dt = datetime(*time.strptime(ts.strip('"'), '%Y-%m-%d')[:6])
    print('{} = {}'.format(ts, dt))


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
