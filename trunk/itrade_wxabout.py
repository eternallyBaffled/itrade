#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxabout.py
#
# Description: wxPython About box
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
# 2005-04-02    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging

# wxPython system
import itrade_wxversion
import wx
import wx.html
import wx.lib.wxpTag

# iTrade system
from itrade_logging import *

# ============================================================================
# About box
# ============================================================================

class iTradeAboutBox(wx.Dialog):
    text = '''
<html>
<body bgcolor="#AC76DE">
<center><table bgcolor="#458154" width="100%%" cellspacing="0"
cellpadding="0" border="1">
<tr>
    <td align="center">
    <h2>iTrade</h2>
    Version %s - %s - %s<br>
    </td>
</tr>
</table>

<p><b>iTrade</b> is a Trading and Charting software written in Python.</p>

<p>This pre-alpha software shows off some of the capabilities
of <b>iTrade</b>.  Select items from the menu or list control,
sit back and enjoy.  Be sure to take a peek at the source code for each
demo item so you can learn how to help us (%s) on this project.</p>

<p><b>iTrade</b> is %s.</p>
<p><b>Credits:</b> %s</p>
<p>
<font size="-1"><b>iTrade</b> is published under the terms of the %s license. Please see <i>LICENSE</i> file for more information.</font>
</p>

<p><wxp module="wx" class="Button">
    <param name="label" value="Okay">
    <param name="id"    value="ID_OK">
</wxp></p>
</center>
</body>
</html>
'''
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, 'About iTrade',)
        html = wx.html.HtmlWindow(self, -1, size=(420, -1))
        html.SetPage(self.text % (itrade_config.softwareVersionName, itrade_config.softwareStatus,itrade_config.softwareVersion, itrade_config.softwareWebsite,itrade_config.softwareCopyright, itrade_config.softwareCredits,itrade_config.softwareLicense ))
        btn = html.FindWindowById(wx.ID_OK)
        btn.SetDefault()
        ir = html.GetInternalRepresentation()
        html.SetSize( (ir.GetWidth()+25, ir.GetHeight()+25) )
        self.SetClientSize(html.GetSize())
        self.CentreOnParent(wx.BOTH)

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    app = wx.PySimpleApp()
    dlg = iTradeAboutBox(None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()

# ============================================================================
# That's all folks !
# ============================================================================
# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
