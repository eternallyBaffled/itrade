#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxmixin.py
#
# Description: wxPython MixIn classes
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
# 2005-10-17    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import os
import logging
import pprint

# wxPython system
import itrade_wxversion
from wxPython.wx import *
from wxPython.lib.mixins.listctrl import wxColumnSorterMixin, wxListCtrlAutoWidthMixin

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_local import message

# ============================================================================
# iTrade_wxFrame
#
# Supports :
# - parental filiation
# - focus management
# ============================================================================

class iTrade_wxFrame(object):
    def __init__(self, parent, name, hasStatusBar=True):
        self.m_parent = parent
        self.m_name = name
        self.SetAutoLayout(True)
        self._config = {}

        # icon
        self.SetIcon(wxIcon("res/itrade.ico",wxBITMAP_TYPE_ICO))

        # focus
        self.m_hasFocus = True
        EVT_ACTIVATE(self,self._OnActivate)

        # size and position
        EVT_ICONIZE(self,self._OnMinimize)

        # need to save
        self.m_needToSave = False

        # a Statusbar in the bottom of the window
        if hasStatusBar:
            self.CreateStatusBar()

        # restore position/size/...
        self.loadConfig()

    def getParent(self):
        return self.m_parent

    def _OnActivate(self,event):
        debug('_OnActivate %d',event.GetActive())
        self.m_hasFocus = event.GetActive()
        event.Skip(False)

    def hasFocus(self):
        return self.m_hasFocus

    def isDirty(self):
        return self.m_needToSave

    def clearDirty(self):
        self.m_needToSave = False

    def setDirty(self):
        self.m_needToSave = True

    def manageDirty(self,msg,fnt='exit'):
        ret = True
        if fnt=='close':
            msg2 = message('mixin_close')
        elif fnt=='exit':
            msg2 = message('mixin_exit')
        elif fnt=='open':
            msg2 = message('mixin_open')
        if self.isDirty():
            # __x wxCANCEL : user parameter
            dlg = wxMessageDialog(self, msg, msg2, wxCANCEL | wxYES_NO | wxYES_DEFAULT | wxICON_QUESTION)
            idRet = dlg.ShowModal()
            if idRet == wxID_YES:
                self.OnSave(None)
            elif idRet == wxID_NO:
                # do not reenter
                self.clearDirty()
            elif idRet == wxID_CANCEL:
                # do not touch dirty flag !
                ret = False
            dlg.Destroy()
        return ret

    def onEraseBackground(self, evt):
        # this is supposed to prevent redraw flicker on some X servers...
        pass

    def GetRestoredPosition(self):
        if self.IsIconized():
            return self._restoredPosition
        else:
            return self.GetPositionTuple()

    def GetRestoredSize(self):
        if self.IsIconized():
            return self._restoredSize
        else:
            return self.GetSizeTuple()

    def _OnMinimize(self, event):
        if event.Iconized() and self.GetPositionTuple() != (-32000, -32000):
            self._restoredPosition = self.GetPositionTuple()
            self._restoredSize = self.GetSizeTuple()
        event.Skip(False)

    def loadConfig(self):
        if self.m_name:
            try:
                self._config = itrade_config.readThenEvalFile(os.path.join(itrade_config.dirCacheData,'%s.win'%self.m_name))
                if self._config != {}:
                    if 'position' in self._config:
                        self.SetPosition(self._config['position'])
                    if 'size' in self._config:
                        self.SetSize(self._config['size'])
            except:
                self._config = {}

    def saveConfig(self):
        if self.m_name:
            self._config['position'] = self.GetRestoredPosition()
            self._config['size'] = self.GetRestoredSize()
            try:
                path = os.path.join(itrade_config.dirCacheData,'%s.win' % self.m_name)
                info('saveConfig: %s' % path)
                f = open(path, "w")
                pprint.pprint(self._config, f)
                f.close()
            except:
                # argh
                pass

# ============================================================================
# iTradeSelectorListCtrl
#
# ListCtrl with sorting columns
# ============================================================================

class iTradeSelectorListCtrl(wxListCtrl, wxListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wxDefaultPosition,
                 size=wxDefaultSize, style=0):
        wxListCtrl.__init__(self, parent, ID, pos, size, style)
        wxListCtrlAutoWidthMixin.__init__(self)

# ============================================================================
# That's all folks !
# ============================================================================
# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
