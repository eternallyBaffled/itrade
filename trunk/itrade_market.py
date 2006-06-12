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

# ============================================================================
# ISIN -> MARKET
# ============================================================================

isin_market = {
    'fr': 'EURONEXT',
    'nl': 'EURONEXT',
    'be': 'EURONEXT',
    'uk': 'LSE',
    'us': 'NASDAQ'
    }

def isin2market(isin):
    cp = isin[0:2].lower()
    if isin_market.has_key(cp):
        return isin_market[cp]
    else:
        # default to EURONEXT !
        return 'EURONEXT'

# ============================================================================
# MARKET -> CURRENCY
# ============================================================================

market_currency = {
    'EURONEXT': 'EUR',
    'ALTERNEXT': 'EUR',
    'NASDAQ': 'USD',
    'NYSE': 'USD',
    'AMEX': 'USD',
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
    lom.append('LSE')
    lom.append('NASDAQ')
    lom.append('NYSE')
    lom.append('AMEX')
    return lom

# ============================================================================
# That's all folks !
# ============================================================================
# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
