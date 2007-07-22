#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxconnection.py
#
# Description: wxPython Connection Settings (Proxy)
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
# 2007-04-15    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging

# wxPython system
import itrade_wxversion
import wx
import wxaddons.sized_controls as sc

# iTrade system
from itrade_logging import *
from itrade_local import message

from itrade_wxutil import iTradeSizedDialog

# ============================================================================
# iTradeConnectionDialog
#
# ============================================================================

class iTradeConnectionDialog(iTradeSizedDialog):
    def __init__(self, parent, server, auth):
        iTradeSizedDialog.__init__(self,parent,-1,message('connection_title'),size=(420, 420),style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.m_server = server
        self.m_auth = auth

        # container
        container = self.GetContentsPane()
        container.SetSizerType("vertical")

        # resizable pane
        pane = sc.SizedPanel(container, -1)
        pane.SetSizerType("form")
        pane.SetSizerProps(expand=True)

        # Row 1 : server
        label = wx.StaticText(pane, -1, message('proxy_server'))
        label.SetSizerProps(valign='center')
        self.wxServerCtrl = wx.TextCtrl(pane, -1, self.m_server, size=(120,-1))
        self.wxServerCtrl.SetSizerProps(expand=True)

        # Row2 : auth
        label = wx.StaticText(pane, -1, message('proxy_auth'))
        label.SetSizerProps(valign='center')
        self.wxAuthCtrl = wx.TextCtrl(pane, -1, self.m_auth, size=(80,-1))
        self.wxAuthCtrl.SetSizerProps(expand=True)

        # Last Row : OK and Cancel
        btnpane = sc.SizedPanel(container, -1)
        btnpane.SetSizerType("horizontal")
        btnpane.SetSizerProps(expand=True)

        # context help
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(btnpane)

        # OK
        btn = wx.Button(btnpane, wx.ID_OK, message('valid'))
        btn.SetDefault()
        btn.SetHelpText(message('valid_desc'))
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnValid)

        # CANCEL
        btn = wx.Button(btnpane, wx.ID_CANCEL, message('cancel'))
        btn.SetHelpText(message('cancel_desc'))

        # a little trick to make sure that you can't resize the dialog to
        # less screen space than the controls need
        self.Fit()
        self.SetMinSize(self.GetSize())

    def OnValid(self,event):
        self.m_server = self.wxServerCtrl.GetLabel().strip()
        self.m_auth = self.wxAuthCtrl.GetLabel().strip()
        self.EndModal(wx.ID_OK)

# ============================================================================
# connection_UI
#
# ============================================================================

def connection_UI(win,server,auth):
    if server == None:
        server = ''
    if auth == None:
        auth = ''

    dlg = iTradeConnectionDialog(win,server,auth)
    if dlg.ShowModal()==wx.ID_OK:
        server = dlg.m_server
        auth = dlg.m_auth
    dlg.Destroy()
    return server,auth

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    app = wx.PySimpleApp()

    from itrade_local import *
    setLang('us')
    gMessage.load()

    provider = wx.SimpleHelpProvider()
    wx.HelpProvider_Set(provider)

    # data to test
    s = 'proxy'
    a = 'auth'

    s,a = connection_UI(None,s,a)
    print s,a

# ============================================================================
# That's all folks !
# ============================================================================
