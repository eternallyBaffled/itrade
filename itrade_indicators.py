#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_indicators.py
#
# Description: INDICATORS
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is	Gilles Dumortier.
#
# Portions created by the Initial Developer are Copyright (C) 2004-2007 the
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
# 2007-01-23    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging

# iTrade system
from itrade_logging import *
import itrade_config
from itrade_ext import loadExtensions

# ============================================================================
# BasicIndicator
# ============================================================================

class BasicIndicator:

    def __init__(self,name):
        self.m_name = name

    def name(self):
        return self.m_name

# ============================================================================
# Test Indicators
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    loadExtensions(itrade_config.fileIndData,itrade_config.dirIndData)

# ============================================================================
# That's all folks !
# ============================================================================
