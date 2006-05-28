#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_datation.py
# Version      : $Id: itrade_datation.py,v 1.18 2006/04/17 17:21:22 dgil Exp $
#
# Description: Datation
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
# 2005-01-09    dgil  Wrote it from scratch
# 2005-08-15    dgil  Add indexation system (trade can be referenced by index
#                     or by date)
# ============================================================================

# ============================================================================
# Version management
# ============================================================================

__revision__ = "$Id: itrade_datation.py,v 1.18 2006/04/17 17:21:22 dgil Exp $"
__author__ = "Gilles Dumortier (dgil@ieee.org)"
__version__ = "0.4"
__status__ = "alpha"
__cvsversion__ = "$Revision: 1.18 $"[11:-2]
__date__ = "$Date: 2006/04/17 17:21:22 $"[7:-2]
__copyright__ = "Copyright (c) 2004-2006 Gilles Dumortier"
__license__ = "GPL"
__credits__ = """ """

# ============================================================================
# Imports
# ============================================================================

# python system
from datetime import *
import time
import logging
import string

# iTrade system
from itrade_logging import *
import itrade_csv

# ============================================================================
# some convertion
# ============================================================================

MONTH2NUM = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
  'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

Y2KCUTOFF = 60

def yy2yyyy(yy):
    yy = int(yy) % 100
    if yy<Y2KCUTOFF:
        return `yy+2000`
    else:
        return `yy+1900`

def dd_mmm_yy2yyyymmdd(d):
    d = string.split(d, '-')
    day = '%02d' % int(d[0])
    month = '%02d' % MONTH2NUM[d[1]]
    year = yy2yyyy(d[2])
    return year + month + day

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

    def isopen(self,d,market=None):
        if type(d)==type('') or isinstance(d,date):
            d = Datation(d)
        if not isinstance(d,Datation):
            raise TypeError("parameter shall be date, Datation or string object")

        debug('isopen %s ? %s ' % (d,self.m_closed))

        # is it saturday or sunday ?
        if d.weekday()>=SATURDAY:
            return False

        # key
        k = self.key(d,market)
        debug('isopen %s k=%s: ? ' % (d,k))

        # is it a special day ?
        if self.m_closed.has_key(k):
            return False

        # market should be opened !
        return True

    def issrd(self,d,market=None):
        if type(d)==type('') or isinstance(d,date):
            d = Datation(d)
        if not isinstance(d,Datation):
            raise TypeError("parameter shall be date, Datation or string object")

        debug('issrd %s ? %s ' % (d,self.m_srd))

        # is it saturday or sunday ?
        if d.weekday()>=SATURDAY:
            return False

        # key
        k = self.key(d,market)
        debug('issrd %s k=%s: ? ' % (d,k))

        # is it a SRD day ?
        if self.m_srd.has_key(k):
            return True

        # normal day
        return False

    def srd(self,d,market=None):
        if type(d)==type('') or isinstance(d,date):
            d = Datation(d)
        if not isinstance(d,Datation):
            raise TypeError("parameter shall be date, Datation or string object")

        # key
        k = self.key(d,market)

        # is it a SRD day ?
        if self.m_srd.has_key(k):
            return self.m_srd[k]
        return None

    # --- [ key management ] --------------------------------------

    def key(self,d,market=None):
        # default Market Entry Place
        if market==None:
            market = 'EURONEXT'

        # key : date + market
        return  '%s%s' % (market,d)

    # --- [ file management ] -------------------------------------

    def addClosed(self,d,market=None,title=None):
        # default Market Entry Place
        if market==None:
            market = 'EURONEXT'

        # normalize the date notation !
        d = Datation(d)

        # key
        k = self.key(d,market)

        if self.m_closed.has_key(k):
            debug('Calendar::addClosed(): %s k=%s: %s - already !' % (d,k,self.m_closed[k]));
            return False
        else:
            # add it in the closed list
            self.m_closed[k] = (market,title)
            debug('Calendar::addClosed(): %s k=%s: %s - added' % (d,k,self.m_closed[k]));
            return True

    def addSRD(self,d,market=None,title=None):
        # default Market Entry Place
        if market==None:
            market = 'EURONEXT'

        # normalize the date notation !
        d = Datation(d)

        # key
        k = self.key(d,market)

        if self.m_srd.has_key(k):
            debug('Calendar::addSRD(): %s k=%s: %s - already !' % (d,k,self.m_srd[k]));
            return False
        else:
            # add it in the srd list
            self.m_srd[k] = (market,title)
            debug('Calendar::addSRD(): %s k=%s: %s - added' % (d,k,self.m_srd[k]));
            return True

    def load(self,fn=None):
        # open and read the file to load these closure information
        infile = itrade_csv.read(fn,os.path.join(itrade_config.dirSysData,'closed.txt'))
        if infile:
            # scan each line to read each quote
            for eachLine in infile:
                item = itrade_csv.parse(eachLine,3)
                if item:
                    if len(item)>2:
                        self.addClosed(item[0],item[1],item[2])
                    else:
                        info("can't import item=%s" % item)

        # open and read the file to load these SRD information
        infile = itrade_csv.read(fn,os.path.join(itrade_config.dirSysData,'srd.txt'))
        if infile:
            # scan each line to read each quote
            for eachLine in infile:
                item = itrade_csv.parse(eachLine,3)
                if item:
                    if len(item)>2:
                        self.addSRD(item[0],item[1],item[2])
                    else:
                        info("can't import item=%s" % item)

    # --- [ index management ] ------------------------------------

    def indexme(self):
        self.m_maxidx = 0
        year = date.today().year - itrade_config.numTradeYears + 1
        num = (itrade_config.numTradeYears * (12*31)) + 5
        while num > 0:
            #print '--- index datation --%d--' % year
            month = 1
            while month <= 12 and num>0:
                #print '--- index datation --%d--' % month
                day = 1
                while day <= 31 and num>0:
                    #print '--- index datation --%d--' % day
                    try:
                        d = date(year,month,day)
                        #d = Datation(d)
                        if d.weekday()<SATURDAY:
                        #if self.isopen(d):
                            #print 'num=%d - index %s = %d' % (num,d,self.m_maxidx)
                            self.m_index[d] = self.m_maxidx
                            self.m_date[self.m_maxidx] = d
                            self.m_maxidx = self.m_maxidx + 1
                        else:
                            #print 'num=%d - index %s = closed' % (num,d)
                            pass
                    except ValueError:
                        pass
                    day = day + 1
                    num = num - 1
                month = month + 1
            year = year + 1

    def index(self,_date):
        if self.m_index.has_key(_date):
            return self.m_index[_date]
        else:
            return -1

    def date(self,_index):
        if self.m_date.has_key(_index):
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
# this object encapsulate a date object with the following properties :
# - really read only object
# - constructed by a date object or a string
# - use calendar singleton object with prev / next
# ============================================================================

class Datation(object):
    def __init__(self,d):
        #debug('Datation::__init__():%s: instance=%s' %(d,type(d)))
        if isinstance(d,date):
            self.m_date = d
        else:
            if d[4]=='-':
                debug('Datation::__init__():%s: %d %d %d' % (d,long(d[0:4]),long(d[5:7]),long(d[8:10])));
                self.m_date = date(long(d[0:4]),long(d[5:7]),long(d[8:10]))
            else:
                debug('Datation::__init__():%s: %d %d %d' % (d,long(d[0:4]),long(d[4:6]),long(d[6:8])));
                self.m_date = date(long(d[0:4]),long(d[4:6]),long(d[6:8]))

    def __str__(self):
        return '%4.4d%2.2d%2.2d' % (self.m_date.year,self.m_date.month,self.m_date.day)

    def __repr__(self):
        return '%4.4d-%2.2d-%2.2d' % (self.m_date.year,self.m_date.month,self.m_date.day)

    def __hash__(self):
        return self.m_date.toordinal()

    def year(self):
        return self.m_date.year

    def month(self):
        return self.m_date.month

    def day(self):
        return self.m_date.day

    def weekday(self):
        return self.m_date.weekday()

    def date(self):
        return self.m_date

    def nextopen(self,market=None):
        ndate = self.m_date + timedelta(1)
        while not gCal.isopen(ndate,market):
            ndate = ndate + timedelta(1)
        return Datation(ndate)

    def prevopen(self,market=None):
        ndate = self.m_date - timedelta(1)
        while not gCal.isopen(ndate,market):
            ndate = ndate - timedelta(1)
        return Datation(ndate)

    def nearopen(self,market=None):
        ndate = self.m_date
        while not gCal.isopen(ndate,market):
            ndate = ndate - timedelta(1)
        return Datation(ndate)

    def index(self):
        return gCal.index(self.m_date)

# ============================================================================
# Install the Calendar system
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

try:
    ignore(gCal)
except NameError:
    gCal = Calendar()

# ============================================================================
# Test
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    info('test0 1==%s' % gCal.add('2004-12-31'));
    info('test0 0==%s' % gCal.add('20041231'));

    info('test1 0==%s' % gCal.isopen('2005-01-01'));
    info('test2 0==%s' % gCal.isopen('20050101'));
    info('test3 1==%s' % gCal.isopen('20050104'));

    info('test4 0==%s' % gCal.isopen('20041231'));      # closed in default market (PAR)
    info('test4 1==%s' % gCal.isopen('20041231','TOK'));# but open in other market

    info('test5 20050104==%s' % Datation('20050104'));
    info('test6 20050105==%s' % Datation('20050104').nextopen());
    info('test7 20050103==%s' % Datation('20050104').prevopen());
    info('test8 20041230==%s' % Datation('20050103').prevopen());
    info('test9 20041230==%s' % Datation('20041231').prevopen());

    info('test10 20040130>20040101 == %s' % (Datation('20040130')>Datation('20040101')))
    info('test10 20040101>20040130 == %s' % (Datation('20040101')>Datation('20040130')))
    info('test10 20040227>20040101 == %s' % (Datation('20040227')>Datation('20040101')))
    info('test10 20040101>20040227 == %s' % (Datation('20040101')>Datation('20040227')))

    info('test11 20050814 index is %d == -1' % (Datation('20050814').index()))
    info('test11 20050815 index is %d != -1' % (Datation('20050815').index()))
    info('test11 20050816 index is %d != -1' % (Datation('20050816').index()))
    info('test11 20051231 index is %d == -1' % (Datation('20051231').index()))
    info('test11 20060101 index is %d == -1' % (Datation('20060101').index()))
    info('test11 20060102 index is %d != -1' % (Datation('20060102').index()))

    print 'lastindex = %d' % gCal.lastindex()

    ts = '20050816'
    dt = datetime(*time.strptime(ts.strip('"'), '%Y%m%d')[:6])
    print '%s = %s' % (ts,dt)

    ts = '2005-08-16'
    dt = datetime(*time.strptime(ts.strip('"'), '%Y-%m-%d')[:6])
    print '%s = %s' % (ts,dt)

# ============================================================================
# That's all folks !
# ============================================================================
# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
