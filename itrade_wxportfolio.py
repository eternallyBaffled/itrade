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
# 2005-04-17    dgil  Wrote it from scratch
# 2006-01-1x    dgil  Move operations screen to itrade_wxoperations.py module
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
import logging
import os

# iTrade system
import itrade_config

# wxPython system
if not itrade_config.nowxversion:
    import itrade_wxversion
import wx
import wx.lib.mixins.listctrl as wxl
# import sized_controls from wx.lib for wxPython version >= 2.8.8.0 (from wxaddons otherwise)
import wx.lib.sized_controls as sc
from wx.lib import masked

# iTrade system
from itrade_defs import QList
from itrade_logging import setLevel, info, debug
from itrade_local import message, getGroupChar, getDecimalChar
from itrade_quotes import quotes
from itrade_portfolio import loadPortfolio, initPortfolioModule, portfolios, Portfolio
from itrade_market import list_of_markets, getDefaultIndice
from itrade_currency import list_of_currencies

import itrade_wxres
from itrade_wxmixin import iTradeSelectorListCtrl
from itrade_wxutil import iTradeError, iTradeYesNo, iTradeSizedDialog

# ============================================================================
# iTradePortfolioSelector
#
#   portfolio = current selected portfolio (if any)
#   operation = 'select','delete'
#   except_portfolio = filename of portfolio which can't be selected
# ============================================================================

class iTradePortfolioSelectorListCtrlDialog(iTradeSizedDialog, wxl.ColumnSorterMixin):
    def __init__(self, parent, portfolio, operation, except_portfolio=None):
        iTradeSizedDialog.__init__(self,parent, -1, message('portfolio_%s_title'%operation),
                        style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, size=(420, 420))

        # init
        if portfolio:
            self.m_name = portfolio.filename()
            self.m_accountref = portfolio.accountref()
        else:
            self.m_name = ''
            self.m_accountref = ''
        self.m_except = except_portfolio

        # container
        container = self.GetContentsPane()
        container.SetSizerType("vertical")

        # resizable pane
        pane = sc.SizedPanel(container, -1)
        pane.SetSizerType("form")
        pane.SetSizerProps(expand=True)

        # Row 1
        label = wx.StaticText(pane, -1, message('portfolio_select_textfield'))
        label.SetSizerProps(valign='center')
        self.wxNameCtrl = wx.TextCtrl(pane, -1, self.m_name, size=(80,-1))
        self.wxNameCtrl.SetSizerProps(expand=True)

        # Row 2 :
        tID = wx.NewId()
        self.m_imagelist = wx.ImageList(16,16)
        self.sm_q = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'quote.png')))
        self.sm_i = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'invalid.png')))
        self.sm_up = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'sm_up.png')))
        self.sm_dn = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'sm_down.png')))

        self.m_list = iTradeSelectorListCtrl(container, tID,
                                 style = wx.LC_REPORT | wx.SUNKEN_BORDER,
                                 size=(400, 380)
                                 )
        self.m_list.SetImageList(self.m_imagelist, wx.IMAGE_LIST_SMALL)
        self.m_list.SetSizerProps(expand=True)

        self.PopulateList()

        # Now that the list exists we can init the other base class,
        # see wxPython/lib/mixins/listctrl.py
        wxl.ColumnSorterMixin.__init__(self, 3)

        wx.EVT_LIST_COL_CLICK(self, tID, self.OnColClick)
        wx.EVT_LIST_ITEM_ACTIVATED(self, tID, self.OnItemActivated)
        wx.EVT_LIST_ITEM_SELECTED(self, tID, self.OnItemSelected)

        # Last Row : OK and Cancel
        btnpane = sc.SizedPanel(container, -1)
        btnpane.SetSizerType("horizontal")
        btnpane.SetSizerProps(expand=True)

        if operation=='delete':
            msg = message('portfolio_properties_btndelete')
            msgdesc = message('portfolio_properties_btndeletedesc')
        elif operation=='select':
            msg = message('portfolio_properties_btnselect')
            msgdesc = message('portfolio_properties_btnselectdesc')
        else:
            msg = message('valid')
            msgdesc = message('valid_desc')

        # context help
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(btnpane)

        # OK
        btn = wx.Button(btnpane, wx.ID_OK, msg)
        btn.SetDefault()
        btn.SetHelpText(msgdesc)
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnValid)

        # CANCEL
        btn = wx.Button(btnpane, wx.ID_CANCEL, message('cancel'))
        btn.SetHelpText(message('cancel_desc'))

        # a little trick to make sure that you can't resize the dialog to
        # less screen space than the controls need
        self.Fit()
        self.SetMinSize(self.GetSize())

        self.wxNameCtrl.SetFocus()

    def PopulateList(self):
        self.m_list.ClearAll()

        # but since we want images on the column header we have to do it the hard way:
        info = wx.ListItem()
        info.Mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT
        info.Image = -1
        info.Align = wx.LIST_FORMAT_LEFT
        info.Text = message('portfolio_list_filename')
        self.m_list.InsertColumnInfo(0, info)

        info.Align = wx.LIST_FORMAT_LEFT
        info.Text = message('portfolio_list_name')
        self.m_list.InsertColumnInfo(1, info)

        info.Align = wx.LIST_FORMAT_LEFT
        info.Text = message('portfolio_list_accountref')
        self.m_list.InsertColumnInfo(2, info)

        x = 0
        self.currentItem = -1

        self.itemDataMap = {}
        for eachPortfolio in portfolios.list():
            if self.m_except != eachPortfolio.filename():
                self.itemDataMap[x] = (eachPortfolio.filename(),eachPortfolio.name(),eachPortfolio.accountref())
                x = x + 1

        items = self.itemDataMap.items()
        for x in range(len(items)):
            key, data = items[x]
            if data[0]!='':
                self.m_list.InsertImageStringItem(x, data[0], self.sm_q)
            else:
                self.m_list.InsertImageStringItem(x, data[0], self.sm_i)
            if data[0] == self.m_name:  # current selection
                self.currentItem = x
            self.m_list.SetStringItem(x, 1, data[1])
            self.m_list.SetStringItem(x, 2, data[2])
            self.m_list.SetItemData(x, key)

        self.m_list.SetColumnWidth(0, wx.LIST_AUTOSIZE_USEHEADER)
        self.m_list.SetColumnWidth(1, wx.LIST_AUTOSIZE_USEHEADER)
        self.m_list.SetColumnWidth(2, wx.LIST_AUTOSIZE_USEHEADER)

        if self.currentItem>=0:
            self.m_list.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
            self.m_list.EnsureVisible(self.currentItem)

    #def OnSize(self, event):
    #    w,h = self.GetClientSizeTuple()
    #    self.m_list.SetDimensions(0, 0, w, h)

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
        #debug("OnItemActivated: %s\nTopItem: %s" % (self.m_list.GetItemText(self.currentItem), self.m_list.GetTopItem()))
        self.OnValid(event)

    def OnItemSelected(self, event):
        self.currentItem = event.m_itemIndex
        #debug("OnItemSelected: %s\nTopItem: %s" % (self.m_list.GetItemText(self.currentItem), self.m_list.GetTopItem()))
        portfolio = portfolios.portfolio(self.m_list.GetItemText(self.currentItem))
        self.wxNameCtrl.SetValue(portfolio.filename())
        event.Skip()

    def OnValid(self,event):
        name = self.wxNameCtrl.GetValue()
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
        if dlg.portfolio == dportfolio:
            info('select_iTradePortfolio() : %s is already the current portfolio' % dlg.portfolio)
        else:
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

class iTradePortfolioPropertiesDialog(iTradeSizedDialog):
    def __init__(self, parent, portfolio, operation):
        iTradeSizedDialog.__init__(self, None, -1, message('portfolio_properties_%s'% operation),
                        style=wx.DEFAULT_DIALOG_STYLE , size=(420, 420) )

        if portfolio:
            self.m_filename = portfolio.filename()
            self.m_name = portfolio.name()
            self.m_accountref = portfolio.accountref()
            self.m_market = portfolio.market()
            self.m_currency = portfolio.currency()
            self.m_vat = portfolio.vat()
            self.m_term = portfolio.term()
            self.m_risk = portfolio.risk()
            self.m_indice = portfolio.indice()
        else:
            self.m_filename = 'noname'
            self.m_name = ''
            self.m_accountref = ''
            self.m_market = 'EURONEXT'
            self.m_currency = 'EUR'
            self.m_vat = 1.196
            self.m_term = 3
            self.m_risk = 5
            self.m_indice = getDefaultIndice(self.m_market)
        self.m_operation = operation

        # container
        container = self.GetContentsPane()
        container.SetSizerType("vertical")

        # resizable pane
        pane = sc.SizedPanel(container, -1)
        pane.SetSizerType("form")
        pane.SetSizerProps(expand=True)

        # row1 : filename
        label = wx.StaticText(pane, -1, message('portfolio_filename'))
        label.SetSizerProps(valign='center')
        self.wxFilenameCtrl = wx.TextCtrl(pane, -1, self.m_filename, size=(120,-1))
        self.wxFilenameCtrl.SetSizerProps(expand=True)

        # row2 : name
        label = wx.StaticText(pane, -1, message('portfolio_name'))
        label.SetSizerProps(valign='center')
        self.wxNameCtrl = wx.TextCtrl(pane, -1, self.m_name, size=(180,-1))
        self.wxNameCtrl.SetSizerProps(expand=True)

        # row3 : accountref
        label = wx.StaticText(pane, -1, message('portfolio_accountref'))
        label.SetSizerProps(valign='center')

        self.wxAccountRefCtrl = wx.TextCtrl(pane, -1, self.m_accountref, size=(80,-1))
        self.wxAccountRefCtrl.SetSizerProps(expand=True)

        # row4 : market
        label = wx.StaticText(pane, -1, message('portfolio_market'))
        label.SetSizerProps(valign='center')

        self.wxMarketCtrl = wx.ComboBox(pane,-1, "", size=wx.Size(160,-1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
        wx.EVT_COMBOBOX(self,self.wxMarketCtrl.GetId(),self.OnMarket)

        idx = wx.NOT_FOUND
        for count, eachCtrl in enumerate(list_of_markets()):
            self.wxMarketCtrl.Append(eachCtrl,eachCtrl)
            if eachCtrl==self.m_market:
                idx = count

        self.wxMarketCtrl.SetSelection(idx)

        # row5 : main indice
        label = wx.StaticText(pane, -1, message('portfolio_indicator'))
        label.SetSizerProps(valign='center')

        self.wxIndicatorCtrl = wx.ComboBox(pane,-1, "", size=wx.Size(160,-1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
        wx.EVT_COMBOBOX(self,self.wxIndicatorCtrl.GetId(),self.OnIndicator)

        count = 0
        idx = wx.NOT_FOUND
        for eachCtrl in quotes.list():
            if eachCtrl.list()==QList.indices:
                #self.wxIndicatorCtrl.Append(eachCtrl.name(),eachCtrl.isin())
                try:
                    self.wxIndicatorCtrl.Append(eachCtrl.name(),eachCtrl.isin())
                except:
                    print('eachCtrl:',eachCtrl)
                if eachCtrl.isin()==self.m_indice:
                    idx = count
                count = count + 1

        self.wxIndicatorCtrl.SetSelection(idx)

        # row6 : currency
        label = wx.StaticText(pane, -1, message('portfolio_currency'))
        label.SetSizerProps(valign='center')

        self.wxCurrencyCtrl = wx.ComboBox(pane,-1, "", size=wx.Size(80,-1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
        wx.EVT_COMBOBOX(self,self.wxCurrencyCtrl.GetId(),self.OnCurrency)

        idx = wx.NOT_FOUND
        for count, eachCtrl in enumerate(list_of_currencies()):
            #print eachCtrl
            self.wxCurrencyCtrl.Append(eachCtrl,eachCtrl)
            if eachCtrl==self.m_currency:
                idx = count

        self.wxCurrencyCtrl.SetSelection(idx)

        # row7 : default vat
        label = wx.StaticText(pane, -1, message('portfolio_vat'))
        label.SetSizerProps(valign='center')

        self.wxVATCtrl = masked.Ctrl(pane, integerWidth=5, fractionWidth=3, controlType=masked.controlTypes.NUMBER, allowNegative = False, groupChar=getGroupChar(), decimalChar=getDecimalChar() )
        self.wxVATCtrl.SetValue((self.m_vat-1)*100)

        # Row8 : trading style
        label = wx.StaticText(container, -1, message('prop_tradingstyle'))

        btnpane = sc.SizedPanel(container, -1, style = wx.RAISED_BORDER | wx.CAPTION | wx.TAB_TRAVERSAL|wx.CLIP_CHILDREN|wx.NO_FULL_REPAINT_ON_RESIZE)
        btnpane.SetSizerType("form")
        btnpane.SetSizerProps(expand=True)

        label = wx.StaticText(btnpane, -1, message('prop_term'))
        label.SetSizerProps(valign='center')

        self.wxTermCtrl = masked.Ctrl(btnpane, integerWidth=3, fractionWidth=0, controlType=masked.controlTypes.NUMBER, allowNegative = False, groupChar=getGroupChar(), decimalChar=getDecimalChar() )
        self.wxTermCtrl.SetValue(self.m_term)

        label = wx.StaticText(btnpane, -1, message('prop_risk'))
        label.SetSizerProps(valign='center')

        self.wxRiskCtrl = masked.Ctrl(btnpane, integerWidth=3, fractionWidth=0, controlType=masked.controlTypes.NUMBER, allowNegative = False, groupChar=getGroupChar(), decimalChar=getDecimalChar() )
        self.wxRiskCtrl.SetValue(self.m_risk)

        # row 9 : separator
        line = wx.StaticLine(container, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        line.SetSizerProps(expand=True)

        # Last Row : OK and Cancel
        btnpane = sc.SizedPanel(container, -1)
        btnpane.SetSizerType("horizontal")
        btnpane.SetSizerProps(expand=True)

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
            msg = message('valid')
            msgdesc = message('valid_desc')
            fnt = self.OnValid

        # context help
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(btnpane)

        # OK
        btn = wx.Button(btnpane, wx.ID_OK, msg)
        btn.SetDefault()
        btn.SetHelpText(msgdesc)
        wx.EVT_BUTTON(self, wx.ID_OK, fnt)

        # CANCEL
        btn = wx.Button(btnpane, wx.ID_CANCEL, message('cancel'))
        btn.SetHelpText(message('cancel_desc'))

        # enable some fields based on the operation
        if operation=='edit':
            # edit: filename, market and currency can't be changed
            self.wxFilenameCtrl.Enable(False)
            self.wxMarketCtrl.Enable(False)
            self.wxCurrencyCtrl.Enable(False)
            #self.wxNameCtrl.SetFocus()
        elif operation=='delete':
            # display only
            self.wxFilenameCtrl.Enable(False)
            self.wxNameCtrl.Enable(False)
            self.wxAccountRefCtrl.Enable(False)
            self.wxMarketCtrl.Enable(False)
            self.wxCurrencyCtrl.Enable(False)
            self.wxVATCtrl.Enable(False)
            self.wxTermCtrl.Enable(False)
            self.wxRiskCtrl.Enable(False)
            self.wxIndicatorCtrl.Enable(False)
            #self.btn.SetFocus()
        elif operation=='rename':
            # filename only
            self.wxNameCtrl.Enable(False)
            self.wxAccountRefCtrl.Enable(False)
            self.wxMarketCtrl.Enable(False)
            self.wxCurrencyCtrl.Enable(False)
            self.wxVATCtrl.Enable(False)
            self.wxTermCtrl.Enable(False)
            self.wxRiskCtrl.Enable(False)
            self.wxIndicatorCtrl.Enable(False)
            #self.btn.SetFocus()
        else:
            # everything is editable
            pass

        # a little trick to make sure that you can't resize the dialog to
        # less screen space than the controls need
        self.Fit()
        self.SetMinSize(self.GetSize())

    def OnValid(self,event):
        self.m_filename = self.wxFilenameCtrl.GetValue().lower().strip()
        self.m_vat = (self.wxVATCtrl.GetValue()/100) + 1
        self.m_term = self.wxTermCtrl.GetValue()
        self.m_risk = self.wxRiskCtrl.GetValue()

        if (self.m_operation=='create' or self.m_operation=='rename') and portfolios.existPortfolio(self.m_filename):
            self.wxFilenameCtrl.SetValue('')
            self.wxFilenameCtrl.SetFocus()
            iTradeError(self, message('portfolio_exist_info') % self.m_filename, message('portfolio_exist_info_title'))
            return

        self.m_name = self.wxNameCtrl.GetValue().strip()
        self.m_accountref = self.wxAccountRefCtrl.GetValue().strip()
        if self.m_operation=='delete':
            idRet = iTradeYesNo(self, message('portfolio_delete_confirm')%self.m_name, message('portfolio_delete_confirm_title'))
            if idRet == wx.ID_NO:
                return
        if self.m_operation=='rename':
            idRet = iTradeYesNo(self, message('portfolio_rename_confirm')%self.m_filename, message('portfolio_rename_confirm_title'))
            if idRet == wx.ID_NO:
                return
        self.EndModal(wx.ID_OK)

    def OnMarket(self,evt):
        t = self.wxMarketCtrl.GetClientData(self.wxMarketCtrl.GetSelection())
        debug("OnMarket %s" % t)
        self.m_market = t

    def OnIndicator(self,evt):
        t = self.wxIndicatorCtrl.GetClientData(self.wxIndicatorCtrl.GetSelection())
        info("OnIndicator %s" % t)
        self.m_indice = t

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
            if portfolios.editPortfolio(portfolio.filename(),dlg.m_name,dlg.m_accountref,dlg.m_market,dlg.m_currency,dlg.m_vat,dlg.m_term,dlg.m_risk,dlg.m_indice):
                portfolios.save()
                retport = portfolios.portfolio(portfolio.filename())
        elif operation=='create':
            if portfolios.addPortfolio(dlg.m_filename,dlg.m_name,dlg.m_accountref,dlg.m_market,dlg.m_currency,dlg.m_vat,dlg.m_term,dlg.m_risk,dlg.m_indice):
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

def main():
    setLevel(logging.INFO)
    app = wx.App(False)
    initPortfolioModule()
    from itrade_local import gMessage
    gMessage.setLang('us')
    gMessage.load()
    provider = wx.SimpleHelpProvider()
    wx.HelpProvider_Set(provider)
    port = select_iTradePortfolio(None, 'default', 'select')
    if port:
        port = loadPortfolio(port.filename())
        properties_iTradePortfolio(None, port, 'edit')
        app.MainLoop()


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
