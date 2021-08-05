#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_candle.py
#
# Description: basic candle management
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
# 2005-04-24    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from enum import Enum
import logging

# iTrade system
from itrade_logging import setLevel

# ============================================================================
# Threshold : Default parameters
#
# by design, threshold are compared with strict comparator operators
#
# threshold unity is the percent (%)
# ============================================================================

threshold_volume_week_lowlow = 70/100
threshold_volume_week_low = 50/100
threshold_volume_week_high = 70/100
threshold_volume_week_highhigh = 150/100

threshold_doji = 0.003
threshold_tombo = 0.003
threshold_tohba = 0.003

# ============================================================================
# Volume indicators
# ============================================================================

CANDLE_VOLUME_LOWLOW   = 0
CANDLE_VOLUME_LOW      = 1
CANDLE_VOLUME_AVERAGE  = 2
CANDLE_VOLUME_HIGH     = 3
CANDLE_VOLUME_HIGHHIGH = 4

CANDLE_NBDAYS_AVERAGE_WEEK = 5

CANDLE_VOLUME_TREND_NOTREND = 0
CANDLE_VOLUME_TREND_GROW = 1
CANDLE_VOLUME_TREND_xx = 2

# ============================================================================
# Basic Candle Type
# ============================================================================
class CandleType(Enum):
    unknown = "unknown"
    notype = "no type"
    doji = "doji"
    juji = "long-legged doji"
    tombo = "dragonfly doji"
    tohba = "gravestone doji"
    flatfix = "flat fix"
    marubozu_white = "white marubozu"
    marubozu_black = "black marubozu"
    marubozu_white_close = "closing white marubozu"
    marubozu_black_open = "opening black marubozu"
    marubozu_white_open = "opening white marubozu"
    marubozu_black_close = "closing black marubozu"


# ============================================================================
# Candle color()
# ============================================================================

CANDLE_WHITE = 1
CANDLE_BLACK = 0

# ============================================================================
# caracterisation : candle numerical to reference
# ============================================================================

CANDLE_BODYLONG = 1
CANDLE_BODYVERYLONG = 2
CANDLE_BODYSHORT = 3
CANDLE_BODYDOJI = 4
CANDLE_SHADOWLONG = 5
CANDLE_SHADOWVERYLONG = 6
CANDLE_SHADOWSHORT = 7
CANDLE_SHADOWVERYSHORT = 8

# ============================================================================
# candle range()
# ============================================================================

CANDLE_BODY = 1
CANDLE_HIGHLOW = 2
CANDLE_UPPERSHADOW = 3
CANDLE_LOWERSHADOW = 4
CANDLE_SHADOWS = 5

# ============================================================================
# __x
#  shadow average
#  body average
#  for a given period
#
#  reference is computed against average values
# ============================================================================

# ============================================================================
# volume_indicator_from_average()
# Given the average of volume, returns volume indicator
#
#   nbdays_average  number of days of the volume average
#   volume_average  volume average
#   volume          current volume
#
#   returns the volume indicator from the current volume using average infos
#
# __x first release : do not take into account the number of days of the
# volume average calculation
# ============================================================================

def volume_indicator_from_average(nbdays_average,volume_average,volume):
    if nbdays_average==CANDLE_NBDAYS_AVERAGE_WEEK:
        if volume < (volume_average*(1-threshold_volume_week_lowlow)):
            return CANDLE_VOLUME_LOWLOW
        elif volume < (volume_average*(1-threshold_volume_week_low)):
            return CANDLE_VOLUME_LOW
        elif volume > (volume_average*(1+threshold_volume_week_highhigh)):
            return CANDLE_VOLUME_HIGHHIGH
        elif volume > (volume_average*(1+threshold_volume_week_high)):
            return CANDLE_VOLUME_HIGH
        else:
            return CANDLE_VOLUME_AVERAGE
        pass
    return CANDLE_VOLUME_AVERAGE

# ============================================================================
# volume_indicator_2string()
#
# __x first release : do not take into account the number of days of the
# volume average calculation
# ============================================================================

def volume_indicator_2string(nbdays_average,vi):
    if nbdays_average==CANDLE_NBDAYS_AVERAGE_WEEK:
        if vi==CANDLE_VOLUME_LOWLOW:
            return "Volumes decreased of more than 70% in one week"
        elif vi==CANDLE_VOLUME_LOW:
            return "Volumes decreased of more than 50% in one week"
        elif vi==CANDLE_VOLUME_AVERAGE:
            return "No observation on volumes"
        elif vi==CANDLE_VOLUME_HIGH:
            return "Volumes increased of more than 70% in one week"
        elif vi==CANDLE_VOLUME_HIGHHIGH:
            return "Volumes increased of more than 150% in one week"

    return "invalid volume indicator"

# ============================================================================
# Candle
#
#   open        value at market open
#   close       value at market close
#   high        highest value during the market
#   low         lowest value during the market
#   volind      volume indicator (CANDLE_VOLUME_x)
#   voltrend    volume trend (CANDLE_VOLUME_TREND_x)
# ============================================================================


class Candle(object):
    """
    >>> from itrade_candle import Candle
    >>> c = Candle(10.0, 11.0, 9.0, 10.0)
    >>> print('candle: %s - %s = doji' % (c, c.type()))
    candle: doji - CandleType.doji = doji
    >>> c = Candle(11.0, 11.0, 9.0, 11.0)
    >>> print('candle: %s - %s = dragonfly doji' % (c, c.type()))
    candle: dragonfly doji - CandleType.tombo = dragonfly doji
    >>> c = Candle(9.0, 11.0, 9.0, 9.0)
    >>> print('candle: %s - %s = gravestone doji' % (c, c.type()))
    candle: gravestone doji - CandleType.tohba = gravestone doji
    """
    def __init__(self,open,high,low,close,volind=CANDLE_VOLUME_AVERAGE,voltrend=CANDLE_VOLUME_TREND_NOTREND):
        self.hi = high
        self.lo = low
        self.op = open
        self.cl = close
        self.vi = volind
        self.vt = voltrend
        self.m_type = CandleType.unknown
        self.computeType()

    def type(self):
        return self.m_type

    def __str__(self):
        return self.m_type.value

    def color(self):
        if self.cl >= self.op:
            return CANDLE_WHITE
        else:
            return CANDLE_BLACK

    def body(self):
        return abs(self.cl - self.op)

    def highlow(self):
        return self.hi - self.lo

    def uppershadow(self):
        if self.color() == CANDLE_WHITE:
            return abs(self.hi-self.cl)
        else:
            return abs(self.hi-self.op)

    def lowershadow(self):
        if self.color() == CANDLE_WHITE:
            return abs(self.lo-self.op)
        else:
            return abs(self.lo-self.cl)

    def range(self,range_type):
        if range_type == CANDLE_BODY:
            return self.body()
        elif range_type == CANDLE_HIGHLOW:
            return self.highlow()
        elif range_type == CANDLE_UPPERSHADOW:
            return self.uppershadow()
        elif range_type == CANDLE_LOWERSHADOW:
            return self.lowershadow()
        elif range_type == CANDLE_SHADOWS:
            return self.uppershadow() + self.lowershadow()
        else:
            raise TypeError("invalid range_type parameter")

    def computeType(self):
        if self.hi == self.lo:
            self.m_type = CandleType.flatfix
        elif (self.hi == self.cl) and (self.lo == self.op): # closing = high and opening = low
            self.m_type = CandleType.marubozu_white
        elif (self.lo == self.cl) and (self.hi == self.op): # closing = low and opening = high
            self.m_type = CandleType.marubozu_black
        elif abs(1-(self.op/self.cl))<threshold_doji:  # closing == opening
            self.m_type = CandleType.doji
            #print 'dragon ? %f/%f=%f %f %f' %(self.hi,self.cl,self.hi/self.cl,abs(1-(self.hi/self.cl)),threshold_tombo)
            #print 'gravestone ? %f/%f=%f %f %f' %(self.cl,self.lo,self.cl/self.lo,abs(1-(self.cl/self.lo)),threshold_tohba)
            if abs(1-(self.hi/self.cl))<threshold_tombo:  # closing == opening == high
                self.m_type = CandleType.tombo
            elif abs(1-(self.cl/self.lo))<threshold_tohba:  # closing == opening == low
                self.m_type = CandleType.tohba
        else:
            self.m_type = CandleType.notype


# ============================================================================
# That's all folks !
# ============================================================================
