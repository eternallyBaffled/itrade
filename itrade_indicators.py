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
# 2007-01-23    dgil  Wrote it from scratch
# ============================================================================


from __future__ import absolute_import
class BasicIndicator(object):
    def __init__(self, name):
        self.m_name = name

    def name(self):
        return self.m_name

# ============================================================================
# Test Indicators
# ============================================================================

def main():
    import logging
    import itrade_logging
    import itrade_config
    import itrade_ext

    itrade_config.app_header()
    itrade_logging.setLevel(logging.INFO)
    itrade_ext.loadExtensions(itrade_config.fileIndData, itrade_config.dirIndData)


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
