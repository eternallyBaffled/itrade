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
# Portions created by the Initial Developer are Copyright (C) 2004-2007 the
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
# 2006-11-18    dgil  Experiment unicode version of wxPython
# 2007-01-21    dgil  Switch definitively to unicode version of wxPython
# ============================================================================

# ============================================================================
# wxPython version required : 2.8.x, 2.7.x, 2.6.x
# ============================================================================

WXVERSION_MAJOR     = 2
WXVERSION_MINOR1    = 6
WXVERSION_MINOR2    = 8

# ============================================================================
# Imports
# ============================================================================

# python system
import re

# wxPython system
import wxversion

# iTrade system
from itrade_config import main_is_frozen,verbose
from itrade_local import message,setLang

# ============================================================================
# resolve_wxversion
# ============================================================================

def resolve_wxversion():
    patt = "%d\.%d[0-9\-\.A-Za-z]*-unicode"
    patts = "-unicode"

    versions = wxversion.getInstalled()
    if verbose:
        print 'wxPython Installed :',versions

    # need to select the more recent one with 'unicode'
    vSelected = None
    vSelectedMsg = ''
    for eachVersion in versions:
        for min in range(WXVERSION_MINOR1,WXVERSION_MINOR2+1):
            m = re.search( patt % (WXVERSION_MAJOR,min), eachVersion)
            if m:
                if min == WXVERSION_MINOR2:
                    vSelectedMsg = ''
                else:
                    vSelectedMsg = ' (deprecated version - think to update)'
                vSelected = eachVersion
                break
        if m:
            break

    if vSelected:
        print 'wxPython Selected  :',vSelected,vSelectedMsg
        wxversion.select(vSelected)
        return

    # no compatible version :-( : try to select any release
    bUnicode = False
    for eachVersion in versions:
        m = re.search(patts, eachVersion)
        if m:
            print 'wxPython Selected  :',eachVersion
            wxversion.select(eachVersion)
            bUnicode = True
            break

    if not bUnicode:
        # only ansi release :-( => use US lang
        setLang('us')

    import sys, wx, webbrowser
    app = wx.PySimpleApp()
    wx.MessageBox(message('wxversion_msg') % (WXVERSION_MAJOR,WXVERSION_MINOR2), message('wxversion_title'))
    app.MainLoop()
    webbrowser.open("http://wxpython.org/")
    sys.exit()

# ============================================================================
# During import
# ============================================================================

if not main_is_frozen():
    resolve_wxversion()

# ============================================================================
# That's all folks !
# ============================================================================
