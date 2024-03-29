#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxlistquote.py
#
# Description: wxPython list quote management
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
# 2005-05-29    dgil  from itrade_wxquote.py
# 2006-1x-xx    dgil  downloading of quotes + user quotes + advanced search
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from __future__ import absolute_import
import os
import logging

# iTrade system
import itrade_config

# wxPython system
if not itrade_config.nowxversion:
    import itrade_wxversion
import wx
import wx.lib.mixins.listctrl as wxl

# iTrade system
from itrade_logging import setLevel, debug
from itrade_quotes import quotes, quote_reference
from itrade_local import message
from itrade_market import list_of_markets, compute_country, market2place, list_of_places, market2currency, isin2market
from itrade_currency import list_of_currencies
from itrade_isin import checkISIN
from itrade_defs import QList, QTag
from itrade_ext import gListSymbolRegistry

from itrade_wxmixin import iTradeSelectorListCtrl
from itrade_wxpropquote import open_iTradeQuoteProperty

from itrade_wxutil import iTradeInformation, iTradeError, iTradeYesNo

# ============================================================================
# iTradeQuoteListDialog
# ============================================================================

QLIST_MODIFY = 0
QLIST_ADD = 1
QLIST_DELETE = 2

class iTradeQuoteListDialog(wx.Dialog):
    def __init__(self, parent, quote, qmode):
        # context help
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)

        # pre-init
        self.qmode = qmode

        self.m_parent = parent

        if quote:
            self.m_isin = quote.isin()
            self.m_ticker = quote.ticker()
            self.m_name = quote.name()
            self.m_market = quote.market()
            self.m_place = quote.place()
            self.m_currency = quote.currency()
            self.m_country = quote.country()
        else:
            self.m_isin = ''
            self.m_ticker = ''
            self.m_name = ''
            self.m_place = 'PAR'
            self.m_market = 'EURONEXT'
            self.m_currency = 'EUR'
            self.m_country = 'FR'

        if qmode == QLIST_MODIFY:
            self.tt = message('listquote_modify_title').format(quote.key())
            tb = message('listquote_edit')
        elif qmode == QLIST_ADD:
            self.tt = message('listquote_new_title')
            tb = message('listquote_new')
        elif qmode == QLIST_DELETE:
            self.tt = message('listquote_delete_title').format(quote.key())
            tb = message('listquote_delete')
        else:
            self.tt = '??'
            tb = '??'

        # post-init
        pre.Create(parent, wx.ID_ANY, self.tt, size=(420, 420))
        self.PostCreate(pre)

        sizer = wx.BoxSizer(wx.VERTICAL)

        # isin
        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, wx.ID_ANY, message('prop_isin'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.editISIN = wx.TextCtrl(self, wx.ID_ANY, self.m_isin, size=wx.Size(180, -1), style=wx.TE_LEFT)
        wx.EVT_TEXT(self, self.editISIN.GetId(), self.OnISINEdited)
        box.Add(self.editISIN, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # ticker and name
        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, wx.ID_ANY, message('prop_ticker'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.editTicker = wx.TextCtrl(self, wx.ID_ANY, self.m_ticker, size=wx.Size(60, -1), style=wx.TE_LEFT)
        box.Add(self.editTicker, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        label = wx.StaticText(self, wx.ID_ANY, message('prop_name'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.editName = wx.TextCtrl(self, wx.ID_ANY, self.m_name, size=wx.Size(210, -1), style=wx.TE_LEFT)
        box.Add(self.editName, 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # market
        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, wx.ID_ANY, message('prop_market'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.editMarket = wx.ComboBox(self, wx.ID_ANY, "", size=wx.Size(200, -1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
        box.Add(self.editMarket, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_COMBOBOX(self, self.editMarket.GetId(), self.OnMarket)

        idx = wx.NOT_FOUND
        for count, eachCtrl in enumerate(list_of_markets(ifLoaded=True)):
            self.editMarket.Append(eachCtrl, eachCtrl)
            if eachCtrl == self.m_market:
                idx = count

        self.editMarket.SetSelection(n=idx)

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # separator
        box = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # country & place & currency
        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, wx.ID_ANY, message('prop_country'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.dispCountry = wx.StaticText(self, wx.ID_ANY, self.m_country)
        box.Add(self.dispCountry, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        label = wx.StaticText(self, wx.ID_ANY, message('prop_place'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.editPlace = wx.ComboBox(self, wx.ID_ANY, "", size=wx.Size(60, -1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
        box.Add(self.editPlace, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_COMBOBOX(self, self.editPlace.GetId(), self.OnPlace)
        self.fillPlaces()

        label = wx.StaticText(self, wx.ID_ANY, message('prop_currency'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.editCurrency = wx.ComboBox(self, wx.ID_ANY, "", size=wx.Size(80, -1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
        box.Add(self.editCurrency, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_COMBOBOX(self, self.editCurrency.GetId(), self.OnCurrency)

        idx = wx.NOT_FOUND
        for count, eachCtrl in enumerate(list_of_currencies()):
            # print eachCtrl
            self.editCurrency.Append(eachCtrl, eachCtrl)
            if eachCtrl == self.m_currency:
                idx = count

        self.editCurrency.SetSelection(n=idx)

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # buttons
        box = wx.BoxSizer(wx.HORIZONTAL)

        # context help
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)
            box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        # OK
        btn = wx.Button(self, wx.ID_OK, tb)
        btn.SetDefault()
        btn.SetHelpText(text=message('ok_desc'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnValid)

        # CANCEL
        btn = wx.Button(self, wx.ID_CANCEL, message('cancel'))
        btn.SetHelpText(text=message('cancel_desc'))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)

        sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        wx.EVT_SIZE(self, self.OnSize)

        self.checkEnability()
        self.SetAutoLayout(autoLayout=True)
        self.SetSizerAndFit(sizer=sizer)
        self.Layout()

    def OnSize(self, event):
        w, h = self.GetClientSizeTuple()

    def OnCancel(self, event):
        self.aRet = None
        self.EndModal(wx.ID_CANCEL)

    def OnValid(self, event):
        if self.Validate() and self.TransferDataFromWindow():
            # get fields
            self.m_isin = self.editISIN.GetValue()
            self.m_name = self.editName.GetValue()
            self.m_ticker = self.editTicker.GetValue()
            self.m_market = self.editMarket.GetValue()
            self.m_country = self.dispCountry.GetValue()
            self.m_currency = self.editCurrency.GetValue()
            self.m_place = self.editPlace.GetValue()

            # check isin ?
            if self.qmode == QLIST_ADD:
                # check validity
                if self.m_isin != '':
                    if not checkISIN(self.m_isin):
                        # __x with wx.MessageDialog(self, message('invalid_isin').format(self.m_isin), self.tt, wx.OK | wx.ICON_ERROR) as dlg:
                        # __x   idRet = dlg.ShowModal()
                        iTradeError(self, message('invalid_isin').format(self.m_isin), self.tt)
                        self.editISIN.SetFocus()
                        return

                # check uniqueness
                ref = quote_reference(self.m_isin, self.m_ticker, self.m_market, self.m_place)
                if quotes.lookupKey(ref):
                    # __x with wx.MessageDialog(self, message('listquote_duplicate_ref').format(ref), self.tt, wx.OK | wx.ICON_ERROR) as dlg:
                    # __x   idRet = dlg.ShowModal()
                    iTradeError(self, message('listquote_duplicate_ref').format(ref), self.tt)
                    return

            # isin,name,ticker,market,currency,place,country
            self.aRet = (self.m_isin, self.m_name, self.m_ticker, self.m_market, self.m_currency, self.m_place, self.m_country)
            self.EndModal(wx.ID_OK)

    def checkEnability(self):
        if self.qmode == QLIST_DELETE:
            self.editISIN.Enable(enable=False)
            self.editTicker.Enable(enable=False)
            self.editName.Enable(enable=False)
            self.editMarket.Enable(enable=False)
            self.editPlace.Enable(enable=False)
            self.editCurrency.Enable(enable=False)
        elif self.qmode == QLIST_ADD:
            self.editISIN.Enable(enable=True)
            self.editTicker.Enable(enable=True)
            self.editName.Enable(enable=True)
            self.editMarket.Enable(enable=True)
            self.editPlace.Enable(enable=True)
            self.editCurrency.Enable(enable=True)
        elif self.qmode == QLIST_MODIFY:
            self.editISIN.Enable(enable=False)
            self.editTicker.Enable(enable=False)
            self.editName.Enable(enable=True)
            self.editMarket.Enable(enable=False)
            self.editPlace.Enable(enable=True)
            self.editCurrency.Enable(enable=True)

    def OnMarket(self, evt):
        t = self.editMarket.GetClientData(self.editMarket.GetSelection())
        debug("OnMarket {}".format(t))
        if self.m_market != t:
            self.m_market = t
            self.m_place = market2place(t)
            self.m_country = compute_country(self.m_isin, self.m_market, self.m_place)
            self.fillPlaces()
            self.refreshPage(evt)

    def OnCurrency(self, evt):
        t = self.editCurrency.GetClientData(self.editCurrency.GetSelection())
        debug("OnCurrency {}".format(t))
        self.m_currency = t

    def OnPlace(self, evt):
        t = self.editPlace.GetClientData(self.editPlace.GetSelection())
        debug("OnPlace {}".format(t))
        self.m_place = t

    def refreshPage(self, evt):
        self.editPlace.SetValue(value=self.m_place)
        self.editCurrency.SetValue(value=self.m_currency)
        self.m_country = compute_country(self.m_isin, self.m_market, self.m_place)
        self.dispCountry.SetValue(self.m_country)

    def OnISINEdited(self, event):
        self.m_isin = event.GetString()
        if len(self.m_isin) > 1:
            market = isin2market(self.m_isin)
            # print 'market: ',market
            if market:
                self.m_market = market
                self.m_place = market2place(market)
                self.m_currency = market2currency(market)
                self.refreshPage(event)

    def fillPlaces(self):
        self.editPlace.Clear()
        idx = wx.NOT_FOUND
        for count, eachCtrl in enumerate(list_of_places(self.m_market)):
            # print eachCtrl
            self.editPlace.Append(eachCtrl, eachCtrl)
            if eachCtrl == self.m_place:
                idx = count

        self.editPlace.SetSelection(n=idx)

# ============================================================================
# iTradeQuoteList
# ============================================================================

IDC_ISIN = 0
IDC_TICKER = 1
IDC_NAME = 2
IDC_PLACE = 3
IDC_MARKET = 4
IDC_LIVE = 5
IDC_IMPORT = 6

import wx.lib.newevent
(PostInitEvent, EVT_POSTINIT) = wx.lib.newevent.NewEvent()

class iTradeQuoteListCtrlDialog(wx.Dialog, wxl.ColumnSorterMixin):
    def __init__(self, parent, market):
        # context help
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        title = message('quote_list_title')
        pre.Create(parent, wx.ID_ANY, title, size=(590, 460))
        self.PostCreate(pre)

        self.m_parent = parent
        self.m_dirty = False

        self.m_market = market
        self.m_qlist = QList.system

        self.m_imagelist = wx.ImageList(16, 16)
        self.sm_q = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'quote.png')))
        self.sm_i = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'invalid.png')))
        self.sm_up = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'sm_up.png')))
        self.sm_dn = self.m_imagelist.Add(wx.Bitmap(os.path.join(itrade_config.dirRes, 'sm_down.png')))

        self.m_list = iTradeSelectorListCtrl(self, wx.ID_ANY,
                                 style=wx.LC_REPORT | wx.SUNKEN_BORDER,
                                 size=(570, 380)
                                 )
        self.m_list.SetImageList(self.m_imagelist, wx.IMAGE_LIST_SMALL)

        # Now that the list exists, we can initialise the other base class,
        # see wxPython/lib/mixins/listctrl.py
        wxl.ColumnSorterMixin.__init__(self, 7)

        wx.EVT_LIST_COL_CLICK(self, self.m_list.GetId(), self.OnColClick)
        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_LIST_ITEM_ACTIVATED(self, self.m_list.GetId(), self.OnItemActivated)
        wx.EVT_LIST_ITEM_SELECTED(self, self.m_list.GetId(), self.OnItemSelected)

        sizer = wx.BoxSizer(wx.VERTICAL)

        # market selection
        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, wx.ID_ANY, message('quote_select_market'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.wxMarketCtrl = wx.ComboBox(self, wx.ID_ANY, "", size=wx.Size(200, -1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
        box.Add(self.wxMarketCtrl, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_COMBOBOX(self, self.wxMarketCtrl.GetId(), self.OnMarket)

        idx = wx.NOT_FOUND
        for count, eachCtrl in enumerate(list_of_markets(bFilterMode=True)):
            self.wxMarketCtrl.Append(eachCtrl, eachCtrl)
            if eachCtrl == self.m_market:
                idx = count

        self.wxMarketCtrl.SetSelection(n=idx)

        # list selection
        label = wx.StaticText(self, wx.ID_ANY, message('quote_select_list'))
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.wxQListCtrl = wx.ComboBox(self, wx.ID_ANY, "", size=wx.Size(140, -1), style=wx.CB_DROPDOWN|wx.CB_READONLY)
        box.Add(self.wxQListCtrl, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_COMBOBOX(self, self.wxQListCtrl.GetId(), self.OnQuoteList)

        self.wxQListCtrl.Append(message('quote_select_alllist'), QList.all)
        self.wxQListCtrl.Append(message('quote_select_syslist'), QList.system)
        self.wxQListCtrl.Append(message('quote_select_usrlist'), QList.user)
        self.wxQListCtrl.Append(message('quote_select_indiceslist'), QList.indices)
        self.wxQListCtrl.Append(message('quote_select_trackerslist'), QList.trackers)
        self.wxQListCtrl.Append(message('quote_select_bondslist'), QList.bonds)
        self.wxQListCtrl.SetSelection(n=self.m_qlist.value)

        self.wxCount = wx.StaticText(self, wx.ID_ANY, '--')
        box.Add(self.wxCount, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        box.Add(self.m_list, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        box2 = wx.BoxSizer(wx.VERTICAL)

        self.wxNEW = wx.Button(self, wx.ID_NEW, message('listquote_new'))
        self.wxNEW.SetHelpText(text=message('listquote_new_desc'))
        box2.Add(self.wxNEW, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, wx.ID_NEW, self.OnNewQuote)

        self.wxPROP = wx.Button(self, wx.ID_PROPERTIES, message('listquote_edit'))
        self.wxPROP.SetHelpText(text=message('listquote_edit_desc'))
        box2.Add(self.wxPROP, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, wx.ID_PROPERTIES, self.OnEditQuote)

        self.wxDELETE = wx.Button(self, wx.ID_DELETE, message('listquote_delete'))
        self.wxDELETE.SetHelpText(text=message('listquote_delete_desc'))
        box2.Add(self.wxDELETE, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, wx.ID_DELETE, self.OnDeleteQuote)

        box.Add(box2, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        # context help
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)
            box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        # CANCEL
        btn = wx.Button(self, wx.ID_CANCEL, message('close'))
        btn.SetHelpText(text=message('close_desc'))
        wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        # SAVE
        btn.SetDefault()
        self.wxSAVE = wx.Button(self, wx.ID_APPLY, message('listquote_save'))
        self.wxSAVE.SetHelpText(text=message('listquote_save_desc'))
        box.Add(self.wxSAVE, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, wx.ID_APPLY, self.OnSave)

        # DOWNLOAD
        self.wxOK = wx.Button(self, wx.ID_OK, '')
        self.wxOK.SetHelpText(text='')
        box.Add(self.wxOK, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, wx.ID_OK, self.OnDownload)

        # CLEAR
        self.wxCLEAR = wx.Button(self, wx.ID_CLEAR, '')
        self.wxCLEAR.SetHelpText(text='')
        box.Add(self.wxCLEAR, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON(self, wx.ID_CLEAR, self.OnClear)

        sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetAutoLayout(autoLayout=True)
        self.SetSizerAndFit(sizer)

        EVT_POSTINIT(self, self.OnPostInit)
        wx.PostEvent(self, PostInitEvent())

    # --- [ window management ] -------------------------------------

    def OnPostInit(self, event):
        quotes.loadMarket(self.m_market)
        self.checkEnablity()
        # fill the list
        self.PopulateList()

    def OnMarket(self, evt):
        idx = self.wxMarketCtrl.GetSelection()
        if idx == wx.NOT_FOUND:
            self.m_market = None

            # be sure every supported market is loaded !
            for market in list_of_markets():
                quotes.loadMarket(market)
        else:
            self.m_market = self.wxMarketCtrl.GetClientData(idx)
            quotes.loadMarket(self.m_market)

        self.PopulateList()
        self.checkEnablity()
        self.m_list.SetFocus()

    def OnQuoteList(self, evt):
        idx = self.wxQListCtrl.GetSelection()
        self.m_qlist = idx
        self.PopulateList()
        self.checkEnablity()
        self.m_list.SetFocus()

    def checkEnablity(self):
        if self.m_qlist == QList.indices or self.m_qlist == QList.trackers or self.m_qlist == QList.bonds:
            self.wxOK.Enable(enable=False)
            self.wxNEW.Enable(enable=False)
            # self.wxPROP.Enable(enable=False)
            self.wxDELETE.Enable(enable=False)
            self.wxCLEAR.Enable(enable=False)
            self.wxSAVE.Enable(enable=False)
        else:
            if self.m_qlist == QList.user:
                self.wxOK.Enable(enable=False)
                self.wxNEW.Enable(enable=True)
                # self.wxPROP.Enable(enable=True)
                self.wxDELETE.Enable(enable=True)
            else:
                self.wxOK.Enable(enable=True)
                self.wxNEW.Enable(enable=False)
                # self.wxPROP.Enable(enable=False)
                self.wxDELETE.Enable(enable=False)

            if self.m_qlist == QList.all:
                self.wxCLEAR.Enable(enable=False)
            else:
                self.wxCLEAR.Enable(enable=True)

        if self.m_market is None:
            self.wxOK.SetLabel(label=message('download_symbols_alllists'))
            self.wxOK.SetHelpText(text=message('download_symbols_alldesc'))

            self.wxCLEAR.SetLabel(label=message('clear_symbols_alllists'))
            self.wxCLEAR.SetHelpText(text=message('clear_symbols_alldesc'))
        else:
            self.wxOK.SetLabel(label=message('download_symbols_onelist'))
            self.wxOK.SetHelpText(text=message('download_symbols_onedesc'))

            self.wxCLEAR.SetLabel(label=message('clear_symbols_onelist'))
            self.wxCLEAR.SetHelpText(text=message('clear_symbols_onedesc'))

        self.Layout()

    def PopulateList(self, curquote=None):
        wx.SetCursor(wx.HOURGLASS_CURSOR)

        self.m_list.ClearAll()

        # but since we want images on the column header we have to do it the hard way:
        self.m_list.InsertColumn(IDC_ISIN, message('isin'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_TICKER, message('ticker'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_NAME, message('name'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_PLACE, message('place'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_MARKET, message('market'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_LIVE, message('clive'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)
        self.m_list.InsertColumn(IDC_IMPORT, message('cimport'), wx.LIST_FORMAT_LEFT, wx.LIST_AUTOSIZE)

        self.currentItem = -1

        self.itemDataMap = {}
        self.itemQuoteMap = {}
        self.itemLineMap = {}

        for count, eachQuote in enumerate(quotes.list()):
            if self.m_qlist == QList.all or self.m_qlist == eachQuote.list():
                self.itemDataMap[count] = (eachQuote.isin(), eachQuote.ticker(), eachQuote.name(), eachQuote.place(), eachQuote.market(), eachQuote.liveconnector().name(), eachQuote.importconnector().name())
                self.itemQuoteMap[count] = eachQuote

        line = 0
        curline = -1
        for key, data in self.itemDataMap.items():
            if self.m_market is None or (self.m_market == data[4]):
                if data[0] != '':
                    self.m_list.InsertImageStringItem(line, data[0], self.sm_q)
                else:
                    self.m_list.InsertImageStringItem(line, data[0], self.sm_i)
                self.m_list.SetStringItem(line, IDC_TICKER, data[1])
                self.m_list.SetStringItem(line, IDC_NAME, data[2])
                self.m_list.SetStringItem(line, IDC_PLACE, data[3])
                self.m_list.SetStringItem(line, IDC_MARKET, data[4])
                self.m_list.SetStringItem(line, IDC_LIVE, data[5])
                self.m_list.SetStringItem(line, IDC_IMPORT, data[6])
                self.m_list.SetItemData(line, key)
                self.itemLineMap[data[1]] = line
                if self.itemQuoteMap[key] == curquote:
                    curline = line
                line += 1

        self.m_list.SetColumnWidth(IDC_ISIN, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_TICKER, wx.LIST_AUTOSIZE_USEHEADER)
        self.m_list.SetColumnWidth(IDC_NAME, 16*10)
        self.m_list.SetColumnWidth(IDC_PLACE, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_MARKET, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_LIVE, wx.LIST_AUTOSIZE)
        self.m_list.SetColumnWidth(IDC_IMPORT, wx.LIST_AUTOSIZE)

        if curline != -1:
            self.SetCurrentItem(curline)

        if line == 0:
            self.wxCount.SetLabel(label=message('listquote_items_zero'))
        elif line == 1:
            self.wxCount.SetLabel(label=message('listquote_items_one'))
        else:
            self.wxCount.SetLabel(label=message('listquote_items_n').format(line))

        wx.SetCursor(wx.STANDARD_CURSOR)

    def OnSize(self, event):
        w, h = self.GetClientSizeTuple()
        self.m_list.SetDimensions(0, 0, w, h)

    def SetCurrentItem(self, line=None):
        if self.currentItem >= 0:
            self.m_list.SetItemState(self.currentItem, 0, wx.LIST_STATE_SELECTED)
        if line:
            self.currentItem = line
        if self.currentItem >= 0:
            self.m_list.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
            self.m_list.EnsureVisible(self.currentItem)

    # --- [ wxl.ColumnSorterMixin management ] -------------------------------------

    # Used by the wxl.ColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.m_list

    # Used by the wxl.ColumnSorterMixin, see wxPython/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)

    def getQuoteOnTheLine(self, x):
        if x >= 0:
            key = self.m_list.GetItemData(x)
            quote = self.itemQuoteMap[key]
            return quote
        else:
            return None

    # --- [ OnQuote handlers management ] --------------------------------

    def OnNewQuote(self, event):
        debug(u"OnNewQuote currentItem={:d}".format(self.currentItem))
        aRet = edit_iTradeQuoteList(self, None, QLIST_ADD)
        if aRet:
            debug(u'OnNewQuote: {}'.format(aRet[0]))
            quotes.addQuote(aRet[0], aRet[1], aRet[2], aRet[3], aRet[4], aRet[5], aRet[6], list=QList.user, debug=True)
            self.m_dirty = True
            self.PopulateList()

    def OnDeleteQuote(self, event):
        quote = self.getQuoteOnTheLine(self.currentItem)
        debug(u"OnDeleteQuote currentItem={:d} quote={}".format(self.currentItem, quote))
        if quote:
            aRet = edit_iTradeQuoteList(self, quote, QLIST_DELETE)
            if aRet:
                debug(u'OnDeleteQuote: {}'.format(aRet[0]))
                quotes.removeQuote(quote.key())
                self.m_dirty = True
                self.PopulateList()

    def OnEditQuote(self, event):
        quote = self.getQuoteOnTheLine(self.currentItem)
        debug("OnEditQuote currentItem={:d} quote={}".format(self.currentItem, quote))
        if quote:
            aRet = open_iTradeQuoteProperty(self, quote, bDialog=True)

            # aRet = edit_iTradeQuoteList(self,quote,QLIST_MODIFY)
            if aRet:
                # debug('OnEditQuote: {}'.format(aRet[0]))
                # quotes.removeQuote(quote.key())
                # quotes.addQuote(aRet[0],aRet[1],aRet[2],aRet[3],aRet[4],aRet[5],aRet[6],list=QList.user,debug=True)
                # self.m_dirty = True
                self.PopulateList(quote)

    # --- [ On handlers management ] -------------------------------------

    def OnColClick(self, event):
        debug("OnColClick: {:d}".format(event.GetColumn()))

    def OnItemActivated(self, event):
        self.currentItem = event.m_itemIndex

    def OnItemSelected(self, event):
        self.currentItem = event.m_itemIndex
        event.Skip()

    def OnDownload(self, event):
        x = 0
        if self.m_market is None:
            lst = list_of_markets()
            max = len(lst)+1
            keepGoing = True

            dlg = wx.ProgressDialog(message('download_symbols_alllists'), "", max, self, wx.PD_CAN_ABORT | wx.PD_APP_MODAL)
            for x, market in enumerate(lst):
                if keepGoing:
                    keepGoing = dlg.Update(x, market)
                    fn = gListSymbolRegistry.get(market, QList.any, QTag.list)
                    if fn:
                        fn(quotes, market, dlg, x)
                    else:
                        print('ListSymbolConnector for {} not found !'.format(market))
        else:
            dlg = wx.ProgressDialog(message('download_symbols_onelist'), "", 2, self, wx.PD_CAN_ABORT | wx.PD_APP_MODAL)
            dlg.Update(0, self.m_market)
            fn = gListSymbolRegistry.get(self.m_market, QList.any, QTag.list)
            if fn:
                fn(quotes, self.m_market, dlg, x)
            else:
                print('ListSymbolConnector for {} not found !'.format(self.m_market))

        dlg.Update(x, message('save'))
        self.m_dirty = True
        if dlg:
            dlg.Destroy()
        self.PopulateList()

    def OnSave(self, event):
        self.m_dirty = False
        quotes.saveListOfQuotes()
        # __x with wx.MessageDialog(self, message('listquote_saved'), message('listquote_save_desc'), wx.OK | wx.OK | wx.ICON_INFORMATION) as dlg:
        # __x   dlg.ShowModal()
        iTradeInformation(self, message('listquote_saved'), message('listquote_save_desc'))

    def OnClear(self, event):
        if self.m_market is None:
            market = message('all_markets')
            txt = message('clear_symbols_alldesc')
        else:
            market = self.m_market
            txt = message('clear_symbols_onedesc')
        # __x with wx.MessageDialog(self, message('listquote_clear_confirm').format(market,txt), message('listquote_clear_confirm_title'), wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION) as dlg:
        # __x   idRet = dlg.ShowModal()
        idRet = iTradeYesNo(self, message('listquote_clear_confirm').format(market, txt), message('listquote_clear_confirm_title'))
        if idRet == wx.ID_YES:
            wx.SetCursor(wx.HOURGLASS_CURSOR)
            quotes.removeQuotes(self.m_market, self.m_qlist)
            self.m_dirty = True
            self.PopulateList()
        else:
            return

    def OnCancel(self, event):
        if self.m_dirty:
            # __x with wx.MessageDialog(self, message('listquote_dirty_save'), message('listquote_save_desc'), wx.CANCEL | wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION) as dlg:
            # __x   idRet = dlg.ShowModal()
            idRet = iTradeYesNo(self, message('listquote_dirty_save'), message('listquote_save_desc'), bCanCancel=True)
            if idRet == wx.ID_YES:
                self.OnSave(None)
                res = True
            elif idRet == wx.ID_NO:
                # __x with wx.MessageDialog(self, message('listquote_nodirty_save'), message('listquote_save_desc'), wx.OK | wx.ICON_INFORMATION) as dlg:
                # __x   dlg.ShowModal()
                iTradeInformation(self, message('listquote_nodirty_save'), message('listquote_save_desc'))
                res = True
            else:
                res = False
        else:
            res = True
        if res:
            self.EndModal(wx.ID_CANCEL)

# ============================================================================
# list_iTradeQuote
#
#   win     parent window
# ============================================================================

def list_iTradeQuote(win, market=None):
    dlg = iTradeQuoteListCtrlDialog(win, market)
    dlg.CentreOnParent()
    dlg.ShowModal()
    dlg.Destroy()

# ============================================================================
# edit_iTradeQuoteList()
#
#   quote   quote to edit
#   qmode   quote list mode (modify,add,delete)
# ============================================================================

def edit_iTradeQuoteList(win, quote, qmode):
    with iTradeQuoteListDialog(win, quote, qmode) as dlg:
        if dlg.ShowModal() == wx.ID_OK:
            aRet = dlg.aRet
        else:
            aRet = None
    return aRet

# ============================================================================
# Test me
# ============================================================================

def main():
    setLevel(logging.INFO)
    app = wx.App()
    # from itrade_local import setLang, gMessage
    # setLang('us')
    # gMessage.load()
    list_iTradeQuote(None)


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
