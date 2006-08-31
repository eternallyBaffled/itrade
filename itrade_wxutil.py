#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxutil.py
#
# Description: wxPython utilities, incl. matplotlib func support
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is Gilles Dumortier.
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
# 2005-10-26    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging

# itrade system
from itrade_logging import *

# wxPython system
import itrade_wxversion
from wxPython.wx import *

# matplotlib system
import matplotlib
matplotlib.use('WXAgg')
matplotlib.rcParams['numerix'] = 'numpy'

# matplotlib helpers
from matplotlib.colors import colorConverter

# ============================================================================
# wxMatplotColorToRGB()
#
# convert a MatplotColor to a RGB tuple used by wxPython
#
#      b  : blue
#      g  : green
#      r  : red
#      c  : cyan
#      m  : magenta
#      y  : yellow
#      k  : black
#      w  : white
#
# For a greater range of colors, you have two options.  You can specify
# the color using an html hex string, as in
#
#     color = '#eeefff'
#
# or you can pass an R,G,B tuple, where each of R,G,B are in the range
# [0,1].
#
# Finally, legal html names for colors, like 'red', 'burlywood' and
# 'chartreuse' are supported.
#
# ============================================================================

def wxMatplotColorToRGB(colorname='k'):
    r,g,b = colorConverter.to_rgb(colorname)

    return wxColour(int(r*255),int(g*255),int(b*255))

# ============================================================================
# wxFontFromSize
#   1 : small
#   2 : regular
#   3 : big
#
# Porting note : adjust this function to the platform ?? __x
# ============================================================================

def wxFontFromSize(size):
    if size==2:
        return wxFont(10, wxSWISS , wxNORMAL, wxNORMAL)
    elif size==3:
        return wxFont(12, wxSWISS , wxNORMAL, wxNORMAL)
    else:
        return wxFont(7, wxSWISS , wxNORMAL, wxNORMAL)

# ============================================================================
# That's all folks !
# ============================================================================
