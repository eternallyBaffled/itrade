#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_brokers.py
#
# Description: Brokers
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
# 2007-02-21    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import os

import itrade_config
import itrade_csv
from itrade_logging import setLevel, debug

# ============================================================================
# FeeRule
#
# ============================================================================

class FeeRule(object):
    def __init__(self,vfee,vmin,vmax,ref,bPercent=False):
        debug('FeeRule::__init__(): vfee=%.2f vmin=%.2f vmax=%.2f bPercent=%s' %(vfee,vmin,vmax,bPercent))
        self.m_fee = vfee
        self.m_min = vmin
        self.m_max = vmax
        self.m_bPercent = bPercent
        self.m_ref = ref

    def __repr__(self):
        if self.m_bPercent:
            return '%.2f%%;%.2f;%.2f' % (self.m_fee, self.m_min, self.m_max)
        else:
            return '%.2f;%.2f;%.2f' % (self.m_fee, self.m_min, self.m_max)

    def ref(self):
        return self.m_ref

    def nv_fee(self,v):
        if (v>=self.m_min) and (v<=self.m_max):
            if self.m_bPercent:
                return (v*self.m_fee)/100.0
            else:
                return self.m_fee
        else:
            return None

    def sv_fee(self,v):
        n = self.nv_fee(v)
        if n:
            if self.m_bPercent:
                return "%3.2f %%" % (n*100.0)
            else:
                return "%.2f" % n
        else:
            return None

# ============================================================================
# Fees : list of FeeRule
# ============================================================================

class Fees(object):
    def __init__(self,portfolio):
        debug('Fees:__init__(%s)' % portfolio)
        self.m_fees = []
        self.m_portfolio = portfolio
        self.m_ref = 0

    def portfolio(self):
        return self.m_portfolio

    def list(self):
        return self.m_fees.values()

    def load(self,infile=None):
        infile = itrade_csv.read(infile,os.path.join(itrade_config.dirUserData,'default.fees.txt'))
        if infile:
            # scan each line to read each trade
            for eachLine in infile:
                item = itrade_csv.parse(eachLine,3)
                if item:
                    self.addRule(item[0],item[1],item[2])

    def save(self,outfile=None):
        itrade_csv.write(outfile,os.path.join(itrade_config.dirUserData,'default.fees.txt'),self.m_operations.values())

    def addRule(self,sfee,smin,smax):
        debug('Fees::add() before: 0:%s , 1:%s , 2:%s' % (sfee,smin,smax))
        #info('Fees::add() before: %s' % item)
        if sfee[-1:]=='%':
            bPercent = True
            vfee = float(sfee[:-1])
        else:
            bPercent = False
            vfee = float(sfee)
        vmin = float(smin)
        vmax = float(smax)
        fee = FeeRule(vfee,vmin,vmax,self.m_ref,bPercent)
        self.m_fees.append(fee)
        self.m_ref = self.m_ref + 1
        debug('Fees::add() ref=%d after: %s' % (self.m_ref,self.m_fees))
        return self.m_ref

    def removeRule(self,ref):
        del self.m_fees[ref]
        self.m_ref = self.m_ref - 1

    def getRule(self,ref):
        return self.m_fees[ref]

# ============================================================================
# Test
# ============================================================================

def main():
    from itrade_logging import setLevel
    setLevel(logging.INFO)
    itrade_config.app_header()


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
