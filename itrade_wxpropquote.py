#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxpropquote.py
#
# Description: wxPython quote properties display
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
# 2006-11-02    dgil  Wrote it from itrade_wxquote.py
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import os
import logging
import datetime
import locale

# wxPython system
import itrade_wxversion
import wx

# iTrade system
from itrade_logging import *
from itrade_quotes import *
from itrade_local import message
from itrade_config import *
from itrade_import import *
from itrade_wxselectquote import select_iTradeQuote

# ============================================================================
# iTradeQuotePropertiesPanel
#
#   Properties of a quote : cache flush/reload, Short/Long Term, Fixing, ...
# ============================================================================

class iTradeQuotePropertiesPanel(wx.Window):

    def __init__(self,parent,id,quote):
        wx.Window.__init__(self, parent, id)
        self.m_id = id
        self.m_quote = quote
        self.m_parent = parent
        self.m_port = parent.portfolio()

        # vertical general layout
        self._sizer = wx.BoxSizer(wx.VERTICAL)

        # ---[ info : ISIN / Ticker / Name : <Rename> <Reload> ... ]---
        box = wx.StaticBox(self, -1, message('prop_reference'))
        thebox = wx.StaticBoxSizer(box,wx.VERTICAL)

        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, message('prop_ref'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        label = wx.StaticText(self, -1, self.m_quote.key())
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        label = wx.StaticText(self, -1, message('prop_isin'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        label = wx.StaticText(self, -1, self.m_quote.isin())
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        thebox.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, message('prop_ticker'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.editTicker = wx.TextCtrl(self, -1, self.m_quote.ticker(), size=wx.Size(80,-1), style = wx.TE_LEFT)
        box.Add(self.editTicker, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        label = wx.StaticText(self, -1, message('prop_name'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.editName = wx.TextCtrl(self, -1, self.m_quote.name(), size=wx.Size(210,-1), style = wx.TE_LEFT)
        box.Add(self.editName, 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5)

        thebox.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        nid = wx.NewId()
        btn = wx.Button(self, nid, message('prop_restore'))
        btn.SetHelpText(message('prop_desc_restore'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, nid, self.OnRestoreReference)

        nid = wx.NewId()
        btn = wx.Button(self, nid, message('prop_rename'))
        btn.SetHelpText(message('prop_desc_rename'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, nid, self.OnRename)

        nid = wx.NewId()
        btn = wx.Button(self, nid, message('prop_reload'))
        btn.SetHelpText(message('prop_desc_reload'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, nid, self.OnReload)

        nid = wx.NewId()
        btn = wx.Button(self, nid, message('prop_import'))
        btn.SetHelpText(message('prop_desc_import'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, nid, self.OnImport)

        nid = wx.NewId()
        btn = wx.Button(self, nid, message('prop_export'))
        btn.SetHelpText(message('prop_desc_export'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, nid, self.OnExport)

        thebox.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        self._sizer.AddSizer(thebox, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # ---[ market ]---
        box = wx.StaticBox(self, -1, message('prop_marketandconnector'))
        thebox = wx.StaticBoxSizer(box,wx.VERTICAL)

        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, message('prop_market'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        label = wx.StaticText(self, -1, self.m_quote.market())
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        label = wx.StaticText(self, -1, message('prop_country'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        label = wx.StaticText(self, -1, self.m_quote.country())
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        label = wx.StaticText(self, -1, message('prop_place'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        label = wx.StaticText(self, -1, self.m_quote.place())
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        label = wx.StaticText(self, -1, message('prop_currency'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        label = wx.StaticText(self, -1, self.m_quote.currency())
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        label = wx.StaticText(self, -1, message('prop_typeofclock'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.liveText = wx.StaticText(self, -1, self.m_quote.sv_type_of_clock(bDisplayTime=True))
        box.Add(self.liveText, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        thebox.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # ---[ Connectors ]---

        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, message('prop_liveconnector'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.editLiveConnector = wx.ComboBox(self,-1, "", size=wx.Size(120,-1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
        box.Add(self.editLiveConnector, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        label = wx.StaticText(self, -1, message('prop_impconnector'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.editImportConnector = wx.ComboBox(self,-1, "", size=wx.Size(120,-1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
        box.Add(self.editImportConnector, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        thebox.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.fillConnectors(bInit=True)

        # ---[ Restore/Set Market / Connectors Properties ]---

        box = wx.BoxSizer(wx.HORIZONTAL)

        nid = wx.NewId()
        btn = wx.Button(self, nid, message('prop_restore'))
        btn.SetHelpText(message('prop_desc_restore'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, nid, self.OnRestoreConnector)

        nid = wx.NewId()
        btn = wx.Button(self, nid, message('prop_set'))
        btn.SetHelpText(message('prop_desc_set'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, nid, self.OnSetConnector)

        thebox.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        self._sizer.AddSizer(thebox, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # ---[ Trading style ]---
        box = wx.StaticBox(self, -1, message('prop_tradingstyle'))
        thebox = wx.StaticBoxSizer(box,wx.VERTICAL)

        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, message('prop_term'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.editTerm = wx.TextCtrl(self, -1, '3', size=wx.Size(30,-1), style = wx.TE_LEFT)
        box.Add(self.editTerm, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        label = wx.StaticText(self, -1, message('prop_risk'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.editRisk = wx.TextCtrl(self, -1, '50', size=wx.Size(30,-1), style = wx.TE_LEFT)
        box.Add(self.editRisk, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        thebox.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        nid = wx.NewId()
        btn = wx.Button(self, nid, message('prop_restore'))
        btn.SetHelpText(message('prop_desc_restore'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, nid, self.OnRestoreTrading)

        nid = wx.NewId()
        btn = wx.Button(self, nid, message('prop_set'))
        btn.SetHelpText(message('prop_desc_set'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, nid, self.OnSetTrading)

        thebox.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        self._sizer.AddSizer(thebox, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # auto layout
        wx.EVT_SIZE(self, self.OnSize)
        self.SetSizerAndFit(self._sizer)

    def paint(self):
        self.SetSizerAndFit(self._sizer)
        self.Layout()

    def refresh(self):
        info('QuotePropertiesPanel::refresh %s' % self.m_quote.ticker())
        self.paint()

    def OnSize(self,event):
        debug('QuotePropertiesPanel::OnSize')
        self.paint()

    def OnReload(self,event):
        dlg = wx.ProgressDialog(message('main_refreshing'),"",1*itrade_config.numTradeYears,self,wx.PD_APP_MODAL)
        dlg.Update(0,self.m_quote.name())
        self.m_quote.flushAndReload(dlg)
        dlg.Destroy()

    def OnImport(self,event):
        dlg = wx.FileDialog(self.m_parent, message('import_from_file'), itrade_config.dirImport, "", "*.txt", wx.OPEN|wx.FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            dirname  = dlg.GetDirectory()
            filename = dlg.GetFilename()
            file = os.path.join(dirname,filename)

            info('Import file %s' % file)
            self.m_quote.loadTrades(file)
            self.m_quote.saveTrades()

            dlg2 = wx.MessageDialog(self, message('imported_from_file') % file, message('import_from_file'), wx.OK | wx.ICON_INFORMATION)
            dlg2.ShowModal()
            dlg2.Destroy()

        dlg.Destroy()

    def OnExport(self,event):
        dlg = wx.FileDialog(self.m_parent, message('export_to_file'), itrade_config.dirExport, "", "*.txt", wx.SAVE|wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            dirname  = dlg.GetDirectory()
            filename = dlg.GetFilename()
            file = os.path.join(dirname,filename)
            info('Export file %s' % file)

            self.m_quote.saveTrades(file)

            dlg2 = wx.MessageDialog(self, message('exported_to_file') % file, message('export_to_file'), wx.OK | wx.ICON_INFORMATION)
            dlg2.ShowModal()
            dlg2.Destroy()

            #
        dlg.Destroy()

    def saveThenDisplayReference(self):
        self.editTicker.SetLabel(self.m_quote.ticker())
        self.editName.SetLabel(self.m_quote.name())
        if self.m_port:
            self.m_port.saveProperties()

    def OnRestoreReference(self,event):
        # set default information for this value
        self.m_quote.set_name(self.m_quote.default_name())
        self.m_quote.set_ticker(self.m_quote.default_ticker())

        # then refresh the display
        self.saveThenDisplayReference()

    def OnRename(self,event):
        self.m_quote.set_name(self.editName.GetLabel())
        self.m_quote.set_ticker(self.editTicker.GetLabel().upper())

        # then refresh the display
        self.saveThenDisplayReference()

    def fillConnectors(self,bInit=False):
        count = 0
        idx = 0
        for aname,amarket,aplace,adefaut,aconnector,aqlist in listLiveConnector(self.m_quote.market(),self.m_quote.list(),self.m_quote.place()):
            if bInit: self.editLiveConnector.Append(aname,aname)
            if aname==self.m_quote.liveconnector().name():
                idx = count
            count = count + 1

        self.editLiveConnector.SetSelection(idx)

        count = 0
        idx = 0
        for aname,aplace,amarket,adefaut,aconnector,aqlist in listImportConnector(self.m_quote.market(),self.m_quote.list(),self.m_quote.place()):
            if bInit: self.editImportConnector.Append(aname,aname)
            if aname==self.m_quote.importconnector().name():
                idx = count
            count = count + 1

        self.editImportConnector.SetSelection(idx)

    def saveThenDisplayConnector(self):
        self.fillConnectors()
        if self.m_port:
            self.m_port.saveProperties()

    def OnRestoreConnector(self,event):
        # set default market for this value
        self.m_quote.restore_defaultconnectors()

        # then refresh the display
        self.saveThenDisplayConnector()

    def OnSetConnector(self,event):
        self.m_quote.set_liveconnector(self.editLiveConnector.GetLabel().lower())
        self.m_quote.set_importconnector(self.editImportConnector.GetLabel().lower())

        # then refresh the display
        self.saveThenDisplayConnector()

    def OnRestoreTrading(self,event):
        pass

    def OnSetTrading(self,event):
        pass

# ============================================================================
# iTradeQuotePropertyToolbar
#
# ============================================================================

class iTradeQuotePropertyToolbar(wx.ToolBar):

    def __init__(self,parent,id):
        wx.ToolBar.__init__(self,parent,id,size = (120,32), style = wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        self.m_parent = parent
        self.m_Throbber = None
        self._init_toolbar()

    def _init_toolbar(self):
        self._NTB2_EXIT = wx.NewId()
        self._NTB2_SELECT = wx.NewId()

        self.SetToolBitmapSize(wx.Size(24,24))
        self.AddSimpleTool(self._NTB2_EXIT, wx.ArtProvider.GetBitmap(wx.ART_CROSS_MARK, wx.ART_TOOLBAR),
                           message('main_close'), message('main_desc_close'))
        self.AddControl(wx.StaticLine(self, -1, size=(-1,23), style=wx.LI_VERTICAL))
        self.AddSimpleTool(self._NTB2_SELECT, wx.Bitmap('res/quotes.png'),
                           message('quote_select_title'), message('quote_select_title'))

        wx.EVT_TOOL(self, self._NTB2_EXIT, self.exit)
        wx.EVT_TOOL(self, self._NTB2_SELECT, self.select)
        self.Realize()

    def select(self,event):
        self.m_parent.OnSelectQuote(event)

    def exit(self,event):
        self.m_parent.OnExit(event)

# ============================================================================
# iTradeQuotePropertyWindow
#
# ============================================================================

class iTradeQuotePropertyWindow(wx.Frame):

    def __init__(self,parent,id,port,quote,dpage=1):
        self.m_id = wx.NewId()
        wx.Frame.__init__(self,None,self.m_id, size = ( 560,480), style= wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))
        self.m_quote = quote
        self.m_parent = parent
        self.m_port = port

        # fix title
        self.setTitle()

        # property panel
        self.m_propwindow = iTradeQuotePropertiesPanel(self,wx.NewId(),self.m_quote)

        # Toolbar
        self.m_toolbar = iTradeQuotePropertyToolbar(self, wx.NewId())

        wx.EVT_WINDOW_DESTROY(self, self.OnDestroy)
        wx.EVT_SIZE(self, self.OnSize)

    def portfolio(self):
        return self.m_port

    def OnSize(self, event):
        debug('QuotePropertyWindow::OnSize')
        w,h = self.GetClientSizeTuple()
        self.m_propwindow.SetDimensions(0, 32, w,h-32)
        self.m_toolbar.SetDimensions(0, 0, w, 32)
        self.setTitle()

    def setTitle(self):
        w,h = self.GetClientSizeTuple()
        self.SetTitle("%s %s - %s" % (message('quote_title'),self.m_quote.ticker(),self.m_quote.market()))

    def OnDestroy(self, evt):
        if self.m_parent and (self.m_id == evt.GetId()):
            self.m_parent.m_hProperty = None

    def OnSelectQuote(self,event,nquote=None):
        if not nquote:
            nquote = select_iTradeQuote(self,self.m_quote,filter=True,market=None)
        if nquote and nquote<>self.m_quote:
            info('SelectQuote: %s - %s' % (nquote.ticker(),nquote.key()))
            self.m_quote = nquote
            self.m_propwindow.Destroy()
            self.m_propwindow = iTradeQuotePropertiesPanel(self,wx.NewId(),self.m_quote)
            self.OnSize(None)

    def OnExit(self,event):
        self.Close()

# ============================================================================
# open_iTradeQuoteProperty
#
#   win     parent window
#   quote   Quote object or ISIN reference to view
# ============================================================================

def open_iTradeQuoteProperty(win,port,quote):
    if not isinstance(quote,Quote):
        quote = quotes.lookupKey(quote)
    if win and win.m_hProperty:
        # set focus
        win.m_hProperty.OnSelectQuote(None,quote)
        win.m_hProperty.SetFocus()
    else:
        frame = iTradeQuotePropertyWindow(win, -1,port,quote)
        if win:
            win.m_hProperty = frame
        frame.Show()

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    app = wx.PySimpleApp()

    from itrade_local import *
    setLang('us')
    gMessage.load()

    q = select_iTradeQuote(None,None,False)
    if q:
        open_iTradeQuoteProperty(None,None,q)
        app.MainLoop()

# ============================================================================
# That's all folks !
# ============================================================================