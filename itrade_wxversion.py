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
# 2006-11-18    dgil  Experiment unicode version of wxPython
# ============================================================================

# ============================================================================
# wxPython version required : 2.7.x
# ============================================================================

WXVERSION_MAJOR     = 2
WXVERSION_MINOR     = 7

# ============================================================================
# Imports
# ============================================================================

# python system
import re

# wxPython system
import wxversion

# iTrade system
from itrade_config import main_is_frozen,unicode
from itrade_local import message,setLang

# ============================================================================
# resolve_wxversion
# ============================================================================

def resolve_wxversion():
    if unicode:
        patt = "%d\.%d[0-9\-\.A-Za-z]*-unicode"
        patts = "-unicode"
        msgs = message('wxversion_msgu')
    else:
        patt = "%d\.%d[0-9\-\.A-Za-z]*-ansi"
        patts = "-ansi"
        msgs = message('wxversion_msga')

    versions = wxversion.getInstalled()
    print 'wxPython Installed (%s) :' % patts,versions

    # need to select the first one with 'ansi'
    for eachVersion in versions:
        m = re.search( patt % (WXVERSION_MAJOR,WXVERSION_MINOR), eachVersion)
        if m:
            print 'wxPython Selected  :',eachVersion
            wxversion.select(eachVersion)
            return

        if WXVERSION_MINOR > 0:
            m = re.search( patt % (WXVERSION_MAJOR,WXVERSION_MINOR-1), eachVersion)
            if m:
                print 'wxPython Selected  :',eachVersion,' (deprecated version - think to update)'
                wxversion.select(eachVersion)
                return

    # no compatible version :-( : try to select an ansi release
    bAnsi = False
    for eachVersion in versions:
        m = re.search(patts, eachVersion)
        if m:
            print 'wxPython Selected  :',eachVersion
            wxversion.select(eachVersion)
            bAnsi = True
            break

    if not bAnsi:
        # only unicode release :-( => use US lang
        setLang('us')

    import sys, wx, webbrowser
    app = wx.PySimpleApp()
    wx.MessageBox(msgs % (WXVERSION_MAJOR,WXVERSION_MINOR), message('wxversion_title'))
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