#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_parameters.py
#
# Description: Candle / Candlestick - Parameters
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

# iTrade system

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
# period : Default parameters
#
# period used to detect trend on specific data
# ============================================================================

candle_period_average = 20
volume_period_average = 20

# ============================================================================
# That's all folks !
# ============================================================================
