#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxversion.py
# Version      : $Id: itrade_wxversion.py,v 1.3 2006/02/12 10:40:26 dgil Exp $
#
# Description: Manage wxVersion
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
# 2006-01-01    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Version management
# ============================================================================

__revision__ = "$Id: itrade_wxversion.py,v 1.3 2006/02/12 10:40:26 dgil Exp $"
__author__ = "Gilles Dumortier (dgil@ieee.org)"
__version__ = "0.4"
__status__ = "alpha"
__cvsversion__ = "$Revision: 1.3 $"[11:-2]
__date__ = "$Date: 2006/02/12 10:40:26 $"[7:-2]
__copyright__ = "Copyright (c) 2004-2006 Gilles Dumortier"
__license__ = "GPL"
__credits__ = """ """

# ============================================================================
# wxPython version required : 2.6.x
# ============================================================================

WXVERSION_MAJOR     = 2
WXVERSION_MINOR     = 6

# ============================================================================
# Imports
# ============================================================================

# python system
import re

# wxPython system
import wxversion

# iTrade system
from itrade_config import main_is_frozen
from itrade_local import message,setLang

# ============================================================================
# resolve_wxversion
# ============================================================================

def resolve_wxversion():
    versions = wxversion.getInstalled()
    print 'wxPython Installed :',versions

    # need to select the first one with 'ansi'
    for eachVersion in versions:
        m = re.search("%d\.%d[0-9\-\.A-Za-z]*-ansi" % (WXVERSION_MAJOR,WXVERSION_MINOR), eachVersion)
        if m:
            print 'wxPython Selected  :',eachVersion
            wxversion.select(eachVersion)
            return

    # no compatible version :-( : try to select an ansi release
    bAnsi = False
    for eachVersion in versions:
        m = re.search("-ansi", eachVersion)
        if m:
            print 'wxPython Selected  :',eachVersion
            wxversion.select(eachVersion)
            bAnsi = True

    if not bAnsi:
        # only unicode release :-( => use US lang
        setLang('us')

    import sys, wx, webbrowser
    app = wx.PySimpleApp()
    wx.MessageBox(message('wxversion_msg') % (WXVERSION_MAJOR,WXVERSION_MINOR), message('wxversion_title'))
    app.MainLoop()
    webbrowser.open("http://wxPython.org/")
    sys.exit()

# ============================================================================
# During import
# ============================================================================

if not main_is_frozen():
    resolve_wxversion()

# ============================================================================
# That's all folks !
# ============================================================================
# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
