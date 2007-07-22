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
import wx
import wx.lib.mixins.listctrl as wxl

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_local import message

from itrade_wxutil import iTradeYesNo

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
        self.SetIcon(wx.Icon(os.path.join(itrade_config.dirRes, "itrade.ico"),wx.BITMAP_TYPE_ICO))

        # focus
        self.m_hasFocus = True
        wx.EVT_ACTIVATE(self,self._OnActivate)

        # size and position
        wx.EVT_ICONIZE(self,self._OnMinimize)

        # a Statusbar in the bottom of the window
        if hasStatusBar:
            self.CreateStatusBar()

        # restore position/size/...
        self.loadConfig()

    def getParent(self):
        return self.m_parent

    def _OnActivate(self,event):
        #debug('_OnActivate %d',event.GetActive())
        self.m_hasFocus = event.GetActive()
        if self.m_hasFocus and not self.IsIconized():
            self._restoredPosition = self.GetPositionTuple()
            self._restoredSize = self.GetSizeTuple()
        event.Skip(False)

    def hasFocus(self):
        return self.m_hasFocus

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
            if itrade_config.verbose: print 'iTrade_wxFrame::loadConfig',self.m_name
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
            if itrade_config.verbose: print 'iTrade_wxFrame::saveConfig',self.m_name
            self._config['position'] = self.GetRestoredPosition()
            self._config['size'] = self.GetRestoredSize()
            try:
                path = os.path.join(itrade_config.dirCacheData,'%s.win' % self.m_name)
                if itrade_config.verbose: print('saveConfig: %s %s' % (path,self._config))
                f = open(path, "w")
                pprint.pprint(self._config, f)
                f.close()
            except:
                # argh
                print 'saveConfig: argh'
                pass

# ============================================================================
# iTradeSelectorListCtrl
#
# ListCtrl with sorting columns
# ============================================================================

class iTradeSelectorListCtrl(wx.ListCtrl, wxl.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        wxl.ListCtrlAutoWidthMixin.__init__(self)

# ============================================================================
# That's all folks !
# ============================================================================
