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
# 2007-04-15    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
import logging

# iTrade system
import itrade_config
from itrade_local import message
from itrade_logging import setLevel

# wxPython system
if not itrade_config.nowxversion:
    import itrade_wxversion
import wx
from wx.lib import masked
# import sized_controls from wx.lib for wxPython version >= 2.8.8.0 (from wxaddons otherwise)
import wx.lib.sized_controls as sc

# iTrade system
from itrade_wxutil import iTradeSizedDialog

# ============================================================================
# iTradeConnectionDialog
# ============================================================================

class iTradeConnectionDialog(iTradeSizedDialog):
    def __init__(self, parent, server, auth, timeout, *args, **kwargs):
        iTradeSizedDialog.__init__(self, parent=parent, title=message('connection_title'),
                                   size=(420, 420), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, *args, **kwargs)
        if server != "":
            ip, self.m_port = server.split(':')
            a, b, c, d = ip.split('.')
            self.m_ip = u'{:3d}.{:3d}.{:3d}.{:3d}'.format(int(a), int(b), int(c), int(d))
            self.m_port = int(self.m_port)
        else:
            self.m_ip = "   .   .   .   "
            self.m_port = 0

        if auth != "":
            self.m_user, self.m_pwd = auth.split(':')
        else:
            self.m_user = ""
            self.m_pwd = ""
        self.m_timeout = timeout

        # container
        container = self.GetContentsPane()
        container.SetSizerType("vertical")

        # resizable pane
        pane = sc.SizedPanel(container, wx.ID_ANY)
        pane.SetSizerType("form")
        pane.SetSizerProps(expand=True)

        # Row 1 : server / proxy="172.30.0.3:8080"
        label = wx.StaticText(pane, wx.ID_ANY, message('proxy_server_ip'))
        label.SetSizerProps(valign='center')
        self.wxIPCtrl = masked.Ctrl(pane, wx.ID_ANY, controlType=masked.controlTypes.IPADDR, size=(120,-1))
        self.wxIPCtrl.SetValue(self.m_ip)

        label = wx.StaticText(pane, wx.ID_ANY, message('proxy_server_port'))
        label.SetSizerProps(valign='center')
        self.wxPortCtrl = masked.Ctrl(pane, integerWidth=4, fractionWidth=0, controlType=masked.controlTypes.NUMBER, allowNegative = False, groupDigits = False,size=(80,-1), selectOnEntry=True)
        self.wxPortCtrl.SetValue(self.m_port)

        # Row2 : auth = "user:password"
        label = wx.StaticText(pane, wx.ID_ANY, message('proxy_auth_user'))
        label.SetSizerProps(valign='center')
        self.wxUserCtrl = wx.TextCtrl(pane, wx.ID_ANY, self.m_user, size=(120,-1))
        #self.wxUserCtrl.SetSizerProps(expand=True)

        label = wx.StaticText(pane, wx.ID_ANY, message('proxy_auth_pwd'))
        label.SetSizerProps(valign='center')
        self.wxPwdCtrl = wx.TextCtrl(pane, wx.ID_ANY, self.m_pwd, size=(120,-1))
        #self.wxPwdCtrl.SetSizerProps(expand=True)

        # Row3 : timeout
        label = wx.StaticText(pane, wx.ID_ANY, message('connection_timeout'))
        label.SetSizerProps(valign='center')
        self.wxTimeoutCtrl = masked.Ctrl(pane, integerWidth=3, fractionWidth=0, controlType=masked.controlTypes.NUMBER, allowNegative = False, groupDigits = False,size=(80,-1), selectOnEntry=True)
        self.wxTimeoutCtrl.SetValue(self.m_timeout)
        #self.wxTimeoutCtrl.SetSizerProps(expand=False)

        # Last Row : OK and Cancel
        btnpane = sc.SizedPanel(container, wx.ID_ANY)
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

    def OnValid(self, event):
        self.m_ip = self.wxIPCtrl.GetValue().strip()
        self.m_port = self.wxPortCtrl.GetValue()
        self.m_user = self.wxUserCtrl.GetValue().strip()
        self.m_pwd = self.wxPwdCtrl.GetValue().strip()

        if self.m_user != '':
            self.m_auth = self.m_user + ":" + self.m_pwd
        else:
            self.m_auth = ""

        #print("*** ip:", self.m_ip, "port:", self.m_port)

        if self.m_ip != ".   .   ." and self.m_ip != "" and self.m_port > 0:
            a, b, c, d = self.m_ip.split('.')
            self.m_server = '{:d}.{:d}.{:d}.{:d}:{}'.format(int(a), int(b), int(c), int(d), self.m_port)
        else:
            self.m_server = ""

        self.m_timeout = self.wxTimeoutCtrl.GetValue()

        if itrade_config.verbose:
            print("*** Proxy server:", self.m_server, "- Proxy auth:", self.m_auth, "- Connection timeout:", self.m_timeout)
        self.EndModal(wx.ID_OK)

# ============================================================================
# connection_UI
# =======================================e=====================================


def connection_UI(win, server, auth, timeout=25):
    if server is None:
        server = ''
    if auth is None:
        auth = ''

    dlg = iTradeConnectionDialog(win, server, auth, timeout)
    if dlg.ShowModal() == wx.ID_OK:
        server = dlg.m_server
        auth = dlg.m_auth
        timeout = dlg.m_timeout
    dlg.Destroy()
    return server, auth, timeout

# ============================================================================
# Test me
# ============================================================================

def main():
    setLevel(logging.INFO)
    app = wx.App(False)
    from itrade_local import gMessage
    gMessage.setLang('us')
    gMessage.load()
    provider = wx.SimpleHelpProvider()
    wx.HelpProvider_Set(provider)
    # data to test
    s = 'proxy' # this is actually illegal
    s = '1.2.3.4:666'
    a = 'auth' # again illegal
    a = 'user:pwd'
    s, a, t = connection_UI(None, s, a)
    print(s, a, t)


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
