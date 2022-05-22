#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_excel.py
#
# Description: Read excel data using XLRD package (optional)
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
# 2007-05-15    dgil  Wrote it from scratch
# ============================================================================


# TODO: review remarks
# 1: xlrd is now in requirements.txt, so installation from pypi is automatic
# 2: canReadExcel requires users of this module to test for the functionality.
#    Unpythonic, handle it transparently here.

from __future__ import print_function
canReadExcel = True

xlrd_url = 'https://pypi.org/project/xlrd/'

try:
    import xlrd
except ImportError:
    canReadExcel = False
    print('XLRD package ({}) not installed.'.format(xlrd_url))


def open_excel(filename, content):
    book = xlrd.open_workbook(filename=filename, file_contents=content)
    return book

# ============================================================================
# That's all folks !
# ============================================================================
