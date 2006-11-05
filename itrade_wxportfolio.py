#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxportfolio.py
#
# Description: wxPython portfolio screens (properties, selector)
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
# 2005-04-17    dgil  Wrote it from scratch
# 2006-01-1x    dgil  Move operations screen to itrade_wxoperations.py module
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging

# wxPython system
import itrade_wxversion
import wx
import wx.lib.mixins.listctrl as wxl

# iTrade system
from itrade_logging import *
from itrade_local import message
from itrade_quotes import *
from itrade_portfolio import *
from itrade_market import list_of_markets
from itrade_currency import list_of_currencies

import itrade_wxres
from itrade_wxmixin import iTradeSelectorListCtrl

# ============================================================================
# iTradePortfolioSelector
#
#   portfolio = current selected portfolio (if any)
#   operation = 'select','delete'
#   except_portfolio = filename of portfolio which can't be selected
# ============================================================================

class iTradePortfolioSelectorListCtrlDialog(wx.Dialog, wxl.ColumnSorterMixin):
    def __init__(self, parent, portfolio, operation, except_portfolio=None):
        # context help
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        pre.Create(parent, -1, message('portfolio_%s_title'%operation), size=(420, 420))
        self.PostCreate(pre)

        # init
        if portfolio:
            self.m_name = portfolio.filename()
            self.m_accountref = portfolio.accountref()
        else:
            self.m_name = ''
            self.m_accountref = ''
        self.m_except = except_portfolio

        tID = wx.NewId()
        self.m_imagelist = wx.ImageList(16,16)
        self.sm_q = self.m_imagelist.Add(wx.Bitmap('res/invalid.gif'))
        self.sm_up = self.m_imagelist.Add(wx.Bitmap('res/sm_up.gif'))
        self.sm_dn = self.m_imagelist.Add(wx.Bitmap('res/sm_down.gif'))

        self.m_list = iTradeSelectorListCtrl(self, tID,
                                 style = wx.LC_REPORT | wx.SUNKEN_BORDER,
                                 size=(400, 380)
                                 )
        self.m_list.SetImageList(self.m_imagelist, wx.IMAGE_LIST_SMALL)

        self.PopulateList()

        # Now that the list exists we can init the other base class,
        # see wxPython/lib/mixins/listctrl.py
        wxl.ColumnSorterMixin.__init__(self, 3)

        wx.EVT_LIST_COL_CLICK(self, tID, self.OnColClick)
        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_LIST_ITEM_ACTIVATED(self, tID, self.OnItemActivated)
        wx.EVT_LIST_ITEM_SELECTED(self, tID, self.OnItemSelected)

        sizer = wx.BoxSizer(wx.VERTICAL)

        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, message('portfolio_select_textfield'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.wxNameCtrl = wx.TextCtrl(self, -1, self.m_name, size=(80,-1))
        box.Add(self.wxNameCtrl, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        sizer.Add(self.m_list, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        if operation=='delete':
            msg = message('portfolio_properties_btndelete')
            msgdesc = message('portfolio_properties_btndeletedesc')
        elif operation=='select':
            msg = message('portfolio_properties_btnselect')
            msgdesc = message('portfolio_properties_btnselectdesc')
        else:
            msg = message('ok')
            msgdesc = message('ok_desc')

        box = wx.BoxSizer(wx.HORIZONTAL)

        # context help
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)
            box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        # OK
        btn = wx.Button(self, wx.ID_OK, msg)
        btn.SetDefault()
        btn.SetHelpText(msgdesc)
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnValid)

        # CANCEL
        btn = wx.Button(self, wx.ID_CANCEL, message('cancel'))
        btn.SetHelpText(message('cancel_desc'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetAutoLayout(True)
        self.SetSizerAndFit(sizer)
        self.wxNameCtrl.SetFocus()

    def PopulateList(self):
        self.m_list.ClearAll()

        # but since we want images on the column header we have to do it the hard way:
        info = wx.ListItem()
        info.m_mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT
        info.m_image = -1
        info.m_format = wx.LIST_FORMAT_LEFT
        info.m_text = message('portfolio_filename')
        self.m_list.InsertColumnInfo(0, info)

        info.m_format = wx.LIST_FORMAT_LEFT
        info.m_text = message('portfolio_name')
        self.m_list.InsertColumnInfo(1, info)

        info.m_format = wx.LIST_FORMAT_LEFT
        info.m_text = message('portfolio_accountref')
        self.m_list.InsertColumnInfo(2, info)

        x = 0
        self.currentItem = 0

        self.itemDataMap = {}
        for eachPortfolio in portfolios.list():
            if self.m_except<>eachPortfolio.filename():
                self.itemDataMap[x] = (eachPortfolio.filename(),eachPortfolio.name(),eachPortfolio.accountref())
                x = x + 1

        items = self.itemDataMap.items()
        for x in range(len(items)):
            key, data = items[x]
            self.m_list.InsertImageStringItem(x, data[0], self.sm_q)
            if data[0] == self.m_name:  # current selection
                self.currentItem = x
            self.m_list.SetStringItem(x, 1, data[1])
            self.m_list.SetStringItem(x, 2, data[2])
            self.m_list.SetItemData(x, key)

        self.m_list.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(2, wx.LIST_AUTOSIZE)
        self.m_list.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        self.m_list.EnsureVisible(self.currentItem)

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.m_list.SetDimensions(0, 0, w, h)

    # Used by the wxl.ColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.m_list

    # Used by the wxl.ColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)

    def OnColClick(self, event):
        debug("OnColClick: %d\n" % event.GetColumn())

    def OnItemActivated(self, event):
        self.currentItem = event.m_itemIndex
        debug("OnItemActivated: %s\nTopItem: %s" %
                           (self.m_list.GetItemText(self.currentItem), self.m_list.GetTopItem()))
        self.OnValid(event)

    def OnItemSelected(self, event):
        self.currentItem = event.m_itemIndex
        debug("OnItemSelected: %s\nTopItem: %s" %
                           (self.m_list.GetItemText(self.currentItem), self.m_list.GetTopItem()))
        portfolio = portfolios.portfolio(self.m_list.GetItemText(self.currentItem))
        self.wxNameCtrl.SetLabel(portfolio.filename())
        event.Skip()

    def OnValid(self,event):
        name = self.wxNameCtrl.GetLabel()
        portfolio = portfolios.portfolio(name)
        if not portfolio:
            portfolio = portfolios.portfolio(name.lower())

        if portfolio:
            self.portfolio = portfolio
            self.EndModal(wx.ID_OK)

# ============================================================================
# select_iTradePortfolio
#
# select a portfolio from the list of portfolios
# operation = 'select','delete'
# ============================================================================

def select_iTradePortfolio(win,dportfolio=None,operation='select'):
    if dportfolio:
        if not isinstance(dportfolio,Portfolio):
            dportfolio = portfolios.portfolio(dportfolio)
    if operation=='delete':
        # do not delete current selected !
        dlg = iTradePortfolioSelectorListCtrlDialog(win,None,operation,dportfolio.filename())
    else:
        dlg = iTradePortfolioSelectorListCtrlDialog(win,dportfolio,operation,None)
    if dlg.ShowModal()==wx.ID_OK:
        info('select_iTradePortfolio() : %s' % dlg.portfolio)
        portfolio = dlg.portfolio
    else:
        portfolio = None
    dlg.Destroy()

    return portfolio

# ============================================================================
# iTradePortfolioPropertiesDialog
#
#   operation   'edit','create','delete','rename'
# ============================================================================

class iTradePortfolioPropertiesDialog(wx.Dialog):
    def __init__(self, parent, portfolio, operation):
        # context help
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        pre.Create(parent, -1, message('portfolio_properties_%s'% operation), size=(420, 420))
        self.PostCreate(pre)

        if portfolio:
            self.m_filename = portfolio.filename()
            self.m_name = portfolio.name()
            self.m_accountref = portfolio.accountref()
            self.m_market = portfolio.market()
            self.m_currency = portfolio.currency()
            self.m_vat = portfolio.vat()
        else:
            self.m_filename = 'noname'
            self.m_name = ''
            self.m_accountref = ''
            self.m_market = 'EURONEXT'
            self.m_currency = 'EUR'
            self.m_vat = 1.196
        self.m_operation = operation

        wx.EVT_SIZE(self, self.OnSize)

        sizer = wx.BoxSizer(wx.VERTICAL)

        # filename
        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, message('portfolio_filename'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.wxFilenameCtrl = wx.TextCtrl(self, -1, self.m_filename, size=(120,-1))
        box.Add(self.wxFilenameCtrl, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # name
        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, message('portfolio_name'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.wxNameCtrl = wx.TextCtrl(self, -1, self.m_name, size=(180,-1))
        box.Add(self.wxNameCtrl, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # accountref
        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, message('portfolio_accountref'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.wxAccountRefCtrl = wx.TextCtrl(self, -1, self.m_accountref, size=(80,-1))
        box.Add(self.wxAccountRefCtrl, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # market
        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, message('portfolio_market'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.wxMarketCtrl = wx.ComboBox(self,-1, "", size=wx.Size(160,-1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
        box.Add(self.wxMarketCtrl, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_COMBOBOX(self,self.wxMarketCtrl.GetId(),self.OnMarket)

        count = 0
        for eachCtrl in list_of_markets():
            self.wxMarketCtrl.Append(eachCtrl,eachCtrl)
            if eachCtrl==self.m_market:
                idx = count
            count = count + 1

        self.wxMarketCtrl.SetSelection(idx)

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # currency
        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, message('portfolio_currency'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.wxCurrencyCtrl = wx.ComboBox(self,-1, "", size=wx.Size(80,-1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
        box.Add(self.wxCurrencyCtrl, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_COMBOBOX(self,self.wxCurrencyCtrl.GetId(),self.OnCurrency)

        count = 0
        for eachCtrl in list_of_currencies():
            #print eachCtrl
            self.wxCurrencyCtrl.Append(eachCtrl,eachCtrl)
            if eachCtrl==self.m_currency:
                idx = count
            count = count + 1

        self.wxCurrencyCtrl.SetSelection(idx)

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # OK and Cancel
        if operation=='create':
            msg = message('portfolio_properties_btncreate')
            msgdesc = message('portfolio_properties_btncreatedesc')
            fnt = self.OnValid
        elif operation=='delete':
            msg = message('portfolio_properties_btndelete')
            msgdesc = message('portfolio_properties_btndeletedesc')
            fnt = self.OnValid
        elif operation=='edit':
            msg = message('portfolio_properties_btnedit')
            msgdesc = message('portfolio_properties_btneditdesc')
            fnt = self.OnValid
        elif operation=='rename':
            msg = message('portfolio_properties_btnrename')
            msgdesc = message('portfolio_properties_btnrenamedesc')
            fnt = self.OnValid
        else:
            msg = message('ok')
            msgdesc = message('ok_desc')
            fnt = self.OnValid

        box = wx.BoxSizer(wx.HORIZONTAL)

        # context help
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)
            box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        # OK
        btn = wx.Button(self, wx.ID_OK, msg)
        btn.SetDefault()
        btn.SetHelpText(msgdesc)
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, wx.ID_OK, fnt)

        # CANCEL
        btn = wx.Button(self, wx.ID_CANCEL, message('cancel'))
        btn.SetHelpText(message('cancel_desc'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # enable some fields based on the operation
        if operation=='edit':
            # filename can't be changed
            self.wxFilenameCtrl.Enable(False)
            #self.wxNameCtrl.SetFocus()
        elif operation=='delete':
            # display only
            self.wxFilenameCtrl.Enable(False)
            self.wxNameCtrl.Enable(False)
            self.wxAccountRefCtrl.Enable(False)
            self.wxMarketCtrl.Enable(False)
            self.wxCurrencyCtrl.Enable(False)
            #self.btn.SetFocus()
        elif operation=='rename':
            # filename only
            self.wxNameCtrl.Enable(False)
            self.wxAccountRefCtrl.Enable(False)
            self.wxMarketCtrl.Enable(False)
            self.wxCurrencyCtrl.Enable(False)
            #self.btn.SetFocus()
        else:
            # everything is editable
            pass

        self.SetAutoLayout(True)
        self.SetSizerAndFit(sizer)

    def OnSize(self, event):
        event.Skip(False)

    def OnValid(self,event):
        self.m_filename = self.wxFilenameCtrl.GetLabel().lower().strip()
        if (self.m_operation=='create' or self.m_operation=='rename') and portfolios.existPortfolio(self.m_filename):
            self.wxFilenameCtrl.SetLabel('')
            self.wxFilenameCtrl.SetFocus()
            dlg = wx.MessageDialog(self, message('portfolio_exist_info')%self.m_filename, message('portfolio_exist_info_title'), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return
        self.m_name = self.wxNameCtrl.GetLabel().strip()
        self.m_accountref = self.wxAccountRefCtrl.GetLabel().strip()
        if self.m_operation=='delete':
            dlg = wx.MessageDialog(self, message('portfolio_delete_confirm')%self.m_name, message('portfolio_delete_confirm_title'), wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
            idRet = dlg.ShowModal()
            dlg.Destroy()
            if idRet == wx.ID_NO:
                return
        if self.m_operation=='rename':
            dlg = wx.MessageDialog(self, message('portfolio_rename_confirm')%self.m_filename, message('portfolio_rename_confirm_title'), wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
            idRet = dlg.ShowModal()
            dlg.Destroy()
            if idRet == wx.ID_NO:
                return
        self.EndModal(wx.ID_OK)

    def OnMarket(self,evt):
        t = self.wxMarketCtrl.GetClientData(self.wxMarketCtrl.GetSelection())
        debug("OnMarket %s" % t)
        self.m_market = t

    def OnCurrency(self,evt):
        t = self.wxCurrencyCtrl.GetClientData(self.wxCurrencyCtrl.GetSelection())
        debug("OnCurrency %s" % t)
        self.m_currency = t

# ============================================================================
# properties_iTradePortfolio
#
# select a portfolio from the list of portfolios
#   operation   'edit','create','delete','rename'
# ============================================================================

def properties_iTradePortfolio(win,portfolio,operation='create'):
    dlg = iTradePortfolioPropertiesDialog(win,portfolio,operation)
    retport = None
    if dlg.ShowModal()==wx.ID_OK:
        info('properties_iTradePortfolio(operation=%s) : %s' % (operation,dlg.m_name))
        if operation=='delete':
            if portfolios.delPortfolio(portfolio.filename()):
                portfolios.save()
                retport = None
        elif operation=='edit':
            if portfolios.editPortfolio(portfolio.filename(),dlg.m_name,dlg.m_accountref,dlg.m_market,dlg.m_currency,dlg.m_vat):
                portfolios.save()
                retport = portfolios.portfolio(portfolio.filename())
        elif operation=='create':
            if portfolios.addPortfolio(dlg.m_filename,dlg.m_name,dlg.m_accountref,dlg.m_market,dlg.m_currency,dlg.m_vat):
                portfolios.save()
                retport = loadPortfolio(dlg.m_filename)
        elif operation=='rename':
            if portfolios.renamePortfolio(portfolio.filename(),dlg.m_filename):
                portfolios.save()
                retport = loadPortfolio(dlg.m_filename)
    dlg.Destroy()
    return retport

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

    port = select_iTradePortfolio(None,'default','select')
    if port:
        port = loadPortfolio(port.filename())
        properties_iTradePortfolio(None,port,'edit')
        app.MainLoop()

# ============================================================================
# That's all folks !
# ============================================================================
