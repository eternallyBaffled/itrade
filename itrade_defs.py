#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_defs.py
#
# Description: Global Definitions
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
# 2007-04-13    dgil  Wrote it from scratch
# ============================================================================

from enum import Enum

class QList(Enum):
    all = 0
    any = 0
    system = 1
    user = 2
    indices = 3
    trackers = 4
    bonds = 5

# ============================================================================
# TAG : Kind Of Service
# ============================================================================

QTAG_ANY = 0
QTAG_LIVE = 1
QTAG_DIFFERED = 2
QTAG_IMPORT = 3
QTAG_LIST = 4

# ============================================================================
# That's all folks !
# ============================================================================
