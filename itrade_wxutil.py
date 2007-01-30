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
# 2005-10-26    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging

# itrade system
from itrade_logging import *
from itrade_local import message

# wxPython system
import itrade_wxversion
import wx

# matplotlib system
import matplotlib
matplotlib.use('WXAgg')
matplotlib.rcParams['numerix'] = 'numpy'

# matplotlib helpers
from matplotlib.colors import colorConverter

# ============================================================================
# MatplotColorToRGB()
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

def MatplotColorToRGB(colorname='k'):
    r,g,b = colorConverter.to_rgb(colorname)

    return wx.Colour(int(r*255),int(g*255),int(b*255))

# ============================================================================
# FontFromSize
#   1 : small
#   2 : regular
#   3 : big
#
# Porting note : adjust this function to the platform ?? __x
# ============================================================================

def FontFromSize(size):
    if size==2:
        return wx.Font(10, wx.SWISS , wx.NORMAL, wx.NORMAL)
    elif size==3:
        return wx.Font(12, wx.SWISS , wx.NORMAL, wx.NORMAL)
    else:
        return wx.Font(7, wx.SWISS , wx.NORMAL, wx.NORMAL)

# ============================================================================
# wx.MessageDialog()
#
#   parent          Parent window
#   message         Message to show on the dialog
#   caption         The dialog caption
#   style           A dialog style (bitlist) containing flags chosen from :
#      wxOK                 Show an OK button.
#      wxCANCEL             Show a Cancel button.
#      wxYES_NO             Show Yes and No buttons.
#      wxYES_DEFAULT        Used with wxYES_NO, makes Yes button the default -
#                           which is the default behaviour.
#      wxNO_DEFAULT         Used with wxYES_NO, makes No button the default.
#      wxICON_EXCLAMATION   Shows an exclamation mark icon.
#      wxICON_HAND          Shows an error icon.
#      wxICON_ERROR         Shows an error icon - the same as wxICON_HAND.
#      wxICON_QUESTION      Shows a question mark icon.
#      wxICON_INFORMATION   Shows an information (i) icon.
#      wxSTAY_ON_TOP        The message box stays on top of all other window,
#                           even those of the other applications (Win only).
#   pos             Dialog position. Not Windows
#
# ============================================================================

# ============================================================================
# iTradeInformation()
#
#   parent          Parent window
#   message         Message to show on the dialog
#   caption         The dialog caption
# use : wxOK + wxICON_INFORMATION
# ============================================================================

def iTradeInformation(parent,message,caption):
    dlg = wx.MessageDialog(parent, message, caption, wx.OK | wx.ICON_INFORMATION)
    idRet = dlg.ShowModal()
    dlg.Destroy()
    return idRet

# ============================================================================
# iTradeError()
#
#   parent          Parent window
#   message         Message to show on the dialog
#   caption         The dialog caption
# use : wxOK + wxICON_ERROR
# ============================================================================

def iTradeError(parent,message,caption):
    dlg = wx.MessageDialog(parent, message, caption, wx.OK | wx.ICON_ERROR)
    idRet = dlg.ShowModal()
    dlg.Destroy()
    return idRet

# ============================================================================
# iTradeYesNo()
#
#   parent          Parent window
#   message         Message to show on the dialog
#   caption         The dialog caption
#   bCanCancel      yes/no
#   bYesDefault     yes/no
# use : wxYES_NO + { wxCANCEL) + wxICON_QUESTION
# ============================================================================

def iTradeYesNo(parent,message,caption,bCanCancel=False,bYesDefault=True):
    style = wx.YES_NO | wx.ICON_QUESTION
    if bCanCancel:
        style = style | wx.CANCEL
    if bYesDefault:
        style = style | wx.YES_DEFAULT
    else:
        style = style | wx.NO_DEFAULT

    dlg = wx.MessageDialog(parent, message, caption, style)
    idRet = dlg.ShowModal()
    dlg.Destroy()
    return idRet

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    app = wx.PySimpleApp()

    iRet = iTradeYesNo(None,"message","caption")
    if iRet == wx.ID_YES:
        iRet = iTradeYesNo(None,"message","caption",bCanCancel=True,bYesDefault=False)
        if iRet == wx.ID_YES:
            iTradeInformation(None,"confirmation message","caption")
        elif iRet == wx.ID_NO:
            iTradeInformation(None,"unconfirmation message","caption")
        else:
            iTradeInformation(None,"cancellation message","caption")
    else:
        iTradeError(None,"test aborted message","caption")


# ============================================================================
# That's all folks !
# ============================================================================
