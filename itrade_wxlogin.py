#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxlogin.py
#
# Description: wxPython Login UI
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
# 2006-12-31    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from __future__ import absolute_import
import logging

# iTrade system
import itrade_config

# wxPython system
if not itrade_config.nowxversion:
    import itrade_wxversion
import wx

# iTrade system
from itrade_logging import setLevel
from itrade_local import message

# iTrade wxPython system
from itrade_wxutil import iTradeInformation, iTradeError

# ============================================================================
# iTradeLoginDialog
#
# ============================================================================

class iTradeLoginDialog(wx.Dialog):
    def __init__(self, parent, username, password, connector):
        # context help
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        pre.Create(parent, wx.ID_ANY, message('login_title') + ' - ' + connector.name(), size=(420, 420))
        self.PostCreate(pre)

        self.m_username = username
        self.m_password = password
        self.m_connector = connector

        wx.EVT_SIZE(self, self.OnSize)

        sizer = wx.BoxSizer(wx.VERTICAL)

        # info
        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, wx.ID_ANY, connector.desc())
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # username
        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, wx.ID_ANY, message('login_username'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.wxUsernameCtrl = wx.TextCtrl(self, wx.ID_ANY, self.m_username, size=(180,-1))
        box.Add(self.wxUsernameCtrl, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # password
        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, wx.ID_ANY, message('login_password'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.wxPasswordCtrl = wx.TextCtrl(self, wx.ID_ANY, self.m_password, size=(180,-1))
        box.Add(self.wxPasswordCtrl, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # OK and Cancel
        box = wx.BoxSizer(wx.HORIZONTAL)

        # context help
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)
            box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        # OK
        btn = wx.Button(self, wx.ID_OK, message('login_set'))
        btn.SetDefault()
        btn.SetHelpText(text=message('login_setdesc'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnValid)

        # TEST
        btn = wx.Button(self, wx.ID_REFRESH, message('login_test'))
        btn.SetHelpText(text=message('login_testdesc'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, wx.ID_REFRESH, self.OnTest)

        # CANCEL
        btn = wx.Button(self, wx.ID_CANCEL, message('cancel'))
        btn.SetHelpText(text=message('cancel_desc'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetAutoLayout(autoLayout=True)
        self.SetSizerAndFit(sizer)

    def OnSize(self, event):
        event.Skip(False)

    def OnValid(self,event):
        self.m_username = self.wxUsernameCtrl.GetValue().strip()
        self.m_password = self.wxPasswordCtrl.GetValue().strip()
        self.EndModal(wx.ID_OK)

    def OnTest(self,event):
        u = self.wxUsernameCtrl.GetValue().strip()
        p = self.wxPasswordCtrl.GetValue().strip()
        ret = self.m_connector.login(u,p)
        self.m_connector.logout()
        if ret:
            #__xdlg = wx.MessageDialog(self, message('login_test_ok'), message('login_testdesc') + ' - ' + self.m_connector.name(), wx.OK | wx.ICON_INFORMATION)
            iTradeInformation(self, message('login_test_ok'), message('login_testdesc') + ' - ' + self.m_connector.name())
        else:
            #__xdlg = wx.MessageDialog(self, message('login_test_nok'), message('login_testdesc') + ' - ' + self.m_connector.name(), wx.OK | wx.ICON_INFORMATION)
            iTradeError(self, message('login_test_nok'), message('login_testdesc') + ' - ' + self.m_connector.name())
        #__xdlg.ShowModal()
        #__xdlg.Destroy()

# ============================================================================
# login_UI
#
# ============================================================================


def login_UI(win, username, password, connector):
    if username is None:
        username = ''
    if password is None:
        password = ''

    dlg = iTradeLoginDialog(parent=win, username=username, password=password, connector=connector)
    if dlg.ShowModal() == wx.ID_OK:
        username = dlg.m_username
        password = dlg.m_password
    dlg.Destroy()
    return username, password

# ============================================================================
# Test me
# ============================================================================

def main():
    setLevel(logging.INFO)
    app = wx.App()
    from itrade_local import gMessage
    gMessage.setLang('us')
    gMessage.load()
    provider = wx.SimpleHelpProvider()
    wx.HelpProvider_Set(provider)
    u = 'user'
    p = 'passwd'
    from ext.itrade_login_fortuneo import gLoginFortuneo
    u, p = login_UI(None, u, p, gLoginFortuneo)
    print(u, p)


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
