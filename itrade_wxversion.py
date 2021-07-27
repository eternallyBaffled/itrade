#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxversion.py
#
# Description: Manage wxVersion
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
# 2006-01-01    dgil  Wrote it from scratch
# 2006-11-18    dgil  Experiment unicode version of wxPython
# 2007-01-21    dgil  Switch definitively to unicode version of wxPython
# ============================================================================

# wxPython system
from __future__ import print_function
import wxversion

# iTrade system
import itrade_config


def resolve_wxversion():
    if itrade_config.verbose:
        print('wxPython Installed :', wxversion.getInstalled())

    # unicode is default after 2.8
    wxversion.select(["2.8-unicode","2.9","3.0"], optionsRequired=True)

# ============================================================================
# During import
# ============================================================================

if not itrade_config.main_is_frozen():
    resolve_wxversion()
