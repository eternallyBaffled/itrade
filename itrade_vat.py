#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_vat.py
#
# Description: VAT & TAXES (per country, per exchange, per broker, ...)
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
# 2006-12-07    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================


# ============================================================================
# COUNTRY -> default VAT
# ============================================================================

cp_vat = {
    'fr': 1.196,
    'nl': 1.0,
    'be': 1.0,
    'es': 1.0,
    'qs': 1.0,
    'uk': 1.0,
    'us': 1.0
    }


def country2vat(cp):
    if cp in cp_vat:
        return cp_vat[cp]
    else:
        # don't know !
        return 1.0

# ============================================================================
# That's all folks !
# ============================================================================
