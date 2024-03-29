#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_alerts_srd.py
#
# Description: Alerts SRD plugin
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
# 2006-02-12    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from __future__ import absolute_import
from datetime import date
import logging

# iTrade system
from itrade_logging import setLevel
from itrade_alerts import alerts, ALERT_TYPE_INFO_SRD
from itrade_datation import gCal, Datation
from six.moves import range

# ============================================================================
# Alerts_SRD
# ============================================================================

class Alerts_SRD(object):
    def __init__(self):
        pass

    def scan(self, dlg, x):
        print(u'SRD::scan(): dlg,x = {},{:d}'.format(dlg, x))

        ajd = date.today()
        for nb in range(21):
            if gCal.issrd(ajd):
                dummy, desc = gCal.srd(ajd)
                print(u"{}".format(ajd), ': SRD :', desc)
                alerts.newAlert(ALERT_TYPE_INFO_SRD, 'SRD', u"{}".format(ajd), desc, None, None, '')

            # next open day ...
            ajd = Datation(ajd).nextopen('EURONEXT').date()

# ============================================================================
# Export me
# ============================================================================


gAlertsSRD = Alerts_SRD()

alerts.register('SRD', gAlertsSRD)

# ============================================================================
# Test me
# ============================================================================

def main():
    import itrade_config
    setLevel(logging.INFO)
    itrade_config.app_header()
    gAlertsSRD.scan(None, 0)


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
