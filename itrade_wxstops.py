#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxstops.py
#
# Description: wxPython Stops management (add,edit,delete)
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
# 2007-02-03    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
import logging

# iTrade system
import itrade_config
from itrade_logging import setLevel
from itrade_quotes import quotes, Quote
from itrade_local import message, getGroupChar, getDecimalChar

# wxPython system
if not itrade_config.nowxversion:
    import itrade_wxversion
import wx
from wx.lib import masked

# iTrade wx system
from itrade_wxselectquote import select_iTradeQuote
from itrade_wxutil import iTradeYesNo


class iTradeStopsDialog(wx.Dialog):
    def __init__(self, parent, quote, bAdd=True):
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        if bAdd:
            title = message('stops_add_caption').format(quote.name())
        else:
            title = message('stops_edit_caption').format(quote.name())
        pre.Create(parent, wx.ID_ANY, title, size=(420, 420))
        self.PostCreate(pre)

        # init
        self.m_add = bAdd
        self.m_quote = quote
        self.m_parent = parent

        # sizers
        sizer = wx.BoxSizer(wx.VERTICAL)
        box = wx.BoxSizer(wx.HORIZONTAL)

        # current quote
        label = wx.StaticText(parent=self, id=wx.ID_ANY, label=quote.name())
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        label = wx.StaticText(parent=self, id=wx.ID_ANY, label=message('stops_last'))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        label = wx.StaticText(parent=self, id=wx.ID_ANY, label=quote.sv_close(bDispCurrency=True))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # Thresholds
        if quote.nv_number() == 0:
            msgb = message('stops_noshares_loss')
            msgh = message('stops_noshares_win')
        else:
            msgb = message('stops_shares_loss')
            msgh = message('stops_shares_win')

            box = wx.BoxSizer(wx.HORIZONTAL)

            label = wx.StaticText(parent=self,
                                  id=wx.ID_ANY,
                                  label=message('stops_portfolio').format(quote.nv_number(),
                                                                    quote.sv_pr(bDispCurrency=True)))
            box.Add(item=label, proportion=0, flag=wx.ALIGN_LEFT|wx.ALL, border=5)

            sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(parent=self, id=wx.ID_ANY, label=msgb)
        box.Add(label, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.ALL, 5)

        self.wxLoss = masked.Ctrl(self,
                                  integerWidth=6,
                                  fractionWidth=2,
                                  controlType=masked.controlTypes.NUMBER,
                                  allowNegative=False,
                                  groupChar=getGroupChar(),
                                  decimalChar=getDecimalChar())
        box.Add(item=self.wxLoss, proportion=0, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.ALL, border=5)
        if quote.hasStops():
            self.wxLoss.SetValue(quote.nv_stoploss())

        label = wx.StaticText(parent=self, id=wx.ID_ANY, label=quote.currency_symbol())
        box.Add(label, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(parent=self, id=wx.ID_ANY, label=msgh)
        box.Add(label, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.ALL, 5)

        self.wxWin = masked.Ctrl(self,
                                 integerWidth=6,
                                 fractionWidth=2,
                                 controlType=masked.controlTypes.NUMBER,
                                 allowNegative=False,
                                 groupChar=getGroupChar(),
                                 decimalChar=getDecimalChar())
        box.Add(self.wxWin, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.ALL, 5)
        if quote.hasStops():
            self.wxWin.SetValue(quote.nv_stopwin())

        label = wx.StaticText(parent=self, id=wx.ID_ANY, label=quote.currency_symbol())
        box.Add(label, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # Commands (OK / CANCEL / Help)
        box = wx.BoxSizer(wx.HORIZONTAL)

        # context help
        if wx.Platform != "__WXMSW__":
            btn = wx.ContextHelpButton(self)
            box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        # OK
        if bAdd:
            msg = message('stops_add')
            msgdesc = message('stops_add_desc')
        else:
            msg = message('stops_edit')
            msgdesc = message('stops_edit_desc')

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

    def OnValid(self, event):
        # get values
        loss = self.wxLoss.GetValue()
        win = self.wxWin.GetValue()

        # be sure to be in the right order !
        if loss > win:
            win, loss = loss, win

        # add the stops
        quotes.addStops(self.m_quote.key(), loss, win)

        # close modal box
        self.EndModal(wx.ID_OK)


def addOrEditStops_iTradeQuote(win, quote, market, bAdd=True):
    """

    :param win: parent window
    :param quote: Quote object or ISIN reference
    :param market:
    :param bAdd: Defaults to True. Indicates Add or Edit
    :return:
    """
    if not quote:
        print('addOrEditStops_iTradeQuote() : need to select a quote')
        # select one quote from the matrix list
        quote = select_iTradeQuote(win, quote, filter=True, market=market, filterEnabled=True)
        # cancel -> exit
        if not quote:
            return False
        # be sure Add or Edit
        bAdd = not quote.hasStops()

    # quote is a key reference : found the quote object
    if not isinstance(quote, Quote):
        quote = quotes.lookupKey(quote)

    # still a quote, open the dialog to manage the Stops
    if quote:
        print(u'addOrEditStops_iTradeQuote() : Add?({:d}) quote : {}'.format(bAdd, quote))

        with iTradeStopsDialog(win, quote, bAdd=bAdd) as dlg:
            id_ret = dlg.CentreOnParent()
            id_ret = dlg.ShowModal()
        if id_ret == wx.ID_OK:
            return quote
    return None


def removeStops_iTradeQuote(win, quote):
    """
    :param win: parent window
    :param quote: Quote object or ISIN reference
    :return:
    """
    if not isinstance(quote, Quote):
        quote = quotes.lookupKey(quote)
    if quote:
        if quote.hasStops():
            i_ret = iTradeYesNo(parent=win, text=message('stops_remove_text').format(quote.name()), caption=message('stops_remove_caption'))
            if i_ret == wx.ID_YES:
                quotes.removeStops(quote.key())
                return True
    return False


def main():
    setLevel(logging.INFO)
    app = wx.App(False)
#    from itrade_local import setLang, gMessage
#    setLang('us')
#    gMessage.load()
    itrade_config.verbose = False
    quotes.loadListOfQuotes()
    q = quotes.lookupTicker('SAF', 'EURONEXT')
    if q:
        addOrEditStops_iTradeQuote(win=None, quote=q, bAdd=(not q.hasStops()))
    else:
        print('quote not found')


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
