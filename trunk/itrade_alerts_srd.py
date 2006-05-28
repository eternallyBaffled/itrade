#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_alerts_srd.py
# Version      : $Id: itrade_alerts_srd.py,v 1.2 2006/02/12 19:29:51 dgil Exp $
#
# Description: Alerts SRD plugin
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
# 2006-02-12    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Version management
# ============================================================================

__revision__ = "$Id: itrade_alerts_srd.py,v 1.2 2006/02/12 19:29:51 dgil Exp $"
__author__ = "Gilles Dumortier (dgil@ieee.org)"
__version__ = "0.4"
__status__ = "alpha"
__cvsversion__ = "$Revision: 1.2 $"[11:-2]
__date__ = "$Date: 2006/02/12 19:29:51 $"[7:-2]
__copyright__ = "Copyright (c) 2004-2006 Gilles Dumortier"
__license__ = "GPL"
__credits__ = """ """

# ============================================================================
# Imports
# ============================================================================

# python system
from datetime import *
import logging
import time

# iTrade system
from itrade_logging import *
from itrade_alerts import registerAlertPlugin,newAlert,ALERT_TYPE_INFO_SRD,ALERT_STATE_UNREAD
from itrade_datation import gCal,Datation

# ============================================================================
# Alerts_SRD
# ============================================================================

class Alerts_SRD(object):
    def __init__(self):
        pass

    def scan(self,dlg,x):
        print 'SRD::scan(): dlg,x = %s,%d' % (dlg,x)

        ajd = date.today()
        nb = 0
        while nb<21:
            if gCal.issrd(ajd):
                dummy,desc = gCal.srd(ajd)
                print "%s" % ajd,': SRD :',desc
                newAlert(ALERT_TYPE_INFO_SRD,'SRD',"%s" % ajd,desc,None,None,'')

            # next open day ...
            nb = nb + 1
            ajd = Datation(ajd).nextopen('EURONEXT').date()

# ============================================================================
# Export me
# ============================================================================

try:
    ignore(gAlertsSRD)
except NameError:
    gAlertsSRD = Alerts_SRD()

registerAlertPlugin('SRD',gAlertsSRD)

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    gAlertsSRD.scan(None,0)

# ============================================================================
# That's all folks !
# ============================================================================
# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
