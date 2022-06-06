#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxlive.py
#
# Description: wxPython Live
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is Gilles Dumortier.
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
# 2006-01-2x    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
import logging
import time
import thread
import random

# iTrade system
import itrade_config
from itrade_logging import setLevel, info
from itrade_local import message
import itrade_import
import itrade_currency

# wxPython system
if not itrade_config.nowxversion:
    import itrade_wxversion
import wx
import wx.lib.newevent

# ============================================================================
# Creates a new Event class and a EVT binder function
# ============================================================================

(UpdateLiveEvent,EVT_UPDATE_LIVE) = wx.lib.newevent.NewEvent()
(UpdateLiveCurrencyEvent,EVT_UPDATE_LIVECURRENCY) = wx.lib.newevent.NewEvent()

# ============================================================================
# UpdateLiveThread
# ============================================================================

class UpdateLiveThread(object):
    def __init__(self, win, quote, sleeptime, param=None):
        self.m_win = win
        self.m_quote = quote
        self.m_keepGoing = False
        self.m_running = False
        self.m_sleeptime = sleeptime
        self.m_param = param
        # if itrade_config.verbose:
        #    print('UpdateLiveThread::__init__(): %s %f %s' % (quote,sleeptime,param))

    def Start(self):
        self.m_keepGoing = True
        self.m_running = True
        thread.start_new_thread(self.Run, (self.m_param,))
        # if itrade_config.verbose:
        #    print('UpdateLiveThread::Start(): %s %f %s' % (self.m_quote,self.m_sleeptime,self.m_param))

    def Stop(self):
        self.m_keepGoing = False
        # if itrade_config.verbose:
        #    print('UpdateLiveThread::Stop(): %s %f %s' % (self.m_quote,self.m_sleeptime,self.m_param))

    def IsRunning(self):
        return self.m_running

    def Run(self, p):
        # initial delay is random
        time.sleep(random.randint(0, self.m_sleeptime))

        while self.m_keepGoing:
            # if itrade_config.verbose:
            #    print('UpdateLiveThread::Run(): %s %f %s' % (self.m_quote,self.m_sleeptime,self.m_param))

            # update live information
            itrade_import.liveupdate_from_internet(self.m_quote)
            if self.m_keepGoing:
                evt = UpdateLiveEvent(quote=self.m_quote, param=p)
                if self.m_win:
                    wx.PostEvent(self.m_win, evt)

            if self.m_keepGoing:
                time.sleep(self.m_sleeptime)

        self.m_running = False

# ============================================================================
# iTrade_wxLiveMixin
# ============================================================================

class iTrade_wxLiveMixin(object):
    def __init__(self):
        self.m_threads = {}

    def registerLive(self, quote, sleeptime, param=None):
        self.m_threads[quote.key()] = UpdateLiveThread(self, quote, sleeptime, param)

    def unregisterLive(self, quote=None):
        if quote:
            key = quote.key()
            if key in self.m_threads:
                del self.m_threads[key]
        else:
            self.m_threads = {}

    def startLive(self, quote=None):
        if quote:
            # start live only for one quote
            key = quote.key()
            if key in self.m_threads:
                # if itrade_config.verbose:
                #    print('wxLiveMixin::startLive : %s' % key)
                t = self.m_threads[key]
                if not t.IsRunning():
                    t.Start()
            else:
                if itrade_config.verbose:
                    print('wxLiveMixin::startLive : {} UNKNOWN KEY'.format(key))
        else:
            # if itrade_config.verbose:
            #    print('wxLiveMixin::startLive : {:d} threads'.format(len(self.m_threads.values())))
            # start live for all registered quotes
            for t in self.m_threads.values():
                if not t.IsRunning():
                    t.Start()

    def isRunning(self, quote):
        key = quote.key()
        if key in self.m_threads:
            return self.m_threads[key].IsRunning()
        else:
            return False

    def stopLive(self, quote=None, bBusy=False):
        if quote:
            # stop live only for one quote
            key = quote.key()
            if key in self.m_threads:
                # if itrade_config.verbose:
                #    print('wxLiveMixin::stopLive : %s' % key)
                t = self.m_threads[key]
                if t.IsRunning():
                    t.Stop()
            else:
                if itrade_config.verbose:
                    print('wxLiveMixin::stopLive : {} UNKNOWN KEY'.format(key))
        else:
            # if itrade_config.verbose:
            #    print('wxLiveMixin::stopLive : {:d} threads ---['.format(len(self.m_threads.values())))
            if len(self.m_threads.values()):
                # stop live for all registered quotes
                if bBusy:
                    busy = wx.BusyInfo(message('live_busy'))
                    wx.Yield()

                for t in self.m_threads.values():
                    if t.IsRunning():
                        t.Stop()

                if bBusy:
                    running = 1
                    while running:
                        running = 0

                        for t in self.m_threads.values():
                            running = running + t.IsRunning()

                        time.sleep(0.1)
            # if itrade_config.verbose:
            #    print('] --- stopLive')

# ============================================================================
# UpdateLiveCurrencyThread
# ============================================================================

class UpdateLiveCurrencyThread(object):
    def __init__(self, win, key, sleeptime, param=None):
        self.m_win = win
        self.m_key = key
        self.m_curTo = key[:3]
        self.m_curFrom = key[3:]
        self.m_keepGoing = False
        self.m_running = False
        self.m_sleeptime = sleeptime
        self.m_param = param
        # if itrade_config.verbose:
        #    print('UpdateLiveCurrencyThread::__init__(): %s %f %s' % (key,sleeptime,param))

    def Start(self):
        self.m_keepGoing = True
        self.m_running = True
        thread.start_new_thread(self.Run, (self.m_param,))
        # if itrade_config.verbose:
        #    print('UpdateLiveCurrencyThread::Start(): %s %f %s' % (self.m_key,self.m_sleeptime,self.m_param))

    def Stop(self):
        self.m_keepGoing = False
        # if itrade_config.verbose:
        #    print('UpdateLiveCurrencyThread::Stop(): %s %f %s' % (self.m_key,self.m_sleeptime,self.m_param))

    def IsRunning(self):
        return self.m_running

    def Run(self, p):
        # initial delay is random
        time.sleep(random.randint(0, self.m_sleeptime))

        while self.m_keepGoing:
            # if itrade_config.verbose:
            #    print('UpdateLiveCurrencyThread::Run(): %s %f %s' % (self.m_key,self.m_sleeptime,self.m_param))

            # update live information
            itrade_currency.currencies.get(self.m_curTo, self.m_curFrom)
            if self.m_keepGoing:
                evt = UpdateLiveCurrencyEvent(key=self.m_key, param=p)
                if self.m_win:
                    wx.PostEvent(self.m_win, evt)

            if self.m_keepGoing:
                time.sleep(self.m_sleeptime)

        self.m_running = False

# ============================================================================
# iTrade_wxLiveCurrencyMixin
# ============================================================================

class iTrade_wxLiveCurrencyMixin(object):
    def __init__(self):
        self.m_threads = {}

    def registerLiveCurrency(self, key, sleeptime, param=None):
        self.m_threads[key] = UpdateLiveCurrencyThread(self, key, sleeptime, param)

    def unregisterLiveCurrency(self, key=None):
        if key:
            if key in self.m_threads:
                del self.m_threads[key]
        else:
            self.m_threads = {}

    def startLiveCurrency(self, key=None):
        if key:
            # start live only for one currency
            if key in self.m_threads:
                # if itrade_config.verbose:
                #    print('startLive Currency : %s' % key)
                t = self.m_threads[key]
                if not t.IsRunning():
                    t.Start()
            else:
                if itrade_config.verbose:
                    print('startLive Currency : {} UNKNOWN KEY'.format(key))
        else:
            # if itrade_config.verbose:
            #    print('startLive Currency : {:d} threads'.format(len(self.m_threads.values())))

            # start live for all registered currencies
            for t in self.m_threads.values():
                if not t.IsRunning():
                    t.Start()

    def isRunningCurrency(self, key):
        if key in self.m_threads:
            return self.m_threads[key].IsRunning()
        else:
            return False

    def stopLiveCurrency(self, key=None, bBusy=False):
        if key:
            # stop live only for one currency
            if key in self.m_threads:
                # if itrade_config.verbose:
                #    print('stopLive Currency : %s' % key)
                t = self.m_threads[key]
                if t.IsRunning():
                    t.Stop()
            else:
                if itrade_config.verbose:
                    print('stopLive Currency : {} UNKNOWN KEY'.format(key))
        else:
            # if itrade_config.verbose:
            #    print('stopLive Currency : {:d} threads ---['.format(len(self.m_threads.values())))

            if len(self.m_threads.values()):
                # stop live for all registered currencies
                if bBusy:
                    busy = wx.BusyInfo(message('live_busy'))
                    wx.Yield()

                for t in self.m_threads.values():
                    if t.IsRunning():
                        t.Stop()

                if bBusy:
                    running = 1
                    while running:
                        running = 0

                        for t in self.m_threads.values():
                            running = running + t.IsRunning()

                        time.sleep(0.1)
            # if itrade_config.verbose:
            #    print('] --- stopLive Currency')

# ============================================================================
# iTrade_wxLive
#
# ============================================================================

NBLINES = 7
LTLINES = 7

cNEUTRAL = wx.Colour(170,170,255)
cPOSITIF = wx.Colour(51,255,51)
cNEGATIF = wx.Colour(255,51,51)

class iTrade_wxLive(wx.Panel):
    def __init__(self, parent, wn, quote):
        #debug('iTrade_wxLive::__init__')
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.m_parent = wn
        self.m_quote = quote
        self.m_live = quote.liveconnector()

        self.m_font = wx.Font(8, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.SetFont(font=self.m_font)

        # column mapping
        #    nb  qt  ach  ven  qt   nb   hou  qte price clock
        X = (10, 60, 130, 190, 250, 320, 380, 450, 520,  380)
        W = (50, 70,  60,  60,  70,  50,  70,  70,  60,   70)

        # notebook
        title = wx.StaticText(self, wx.ID_ANY, message('live_notebook'), wx.Point(X[0],5), wx.Size(W[0]+W[1]+W[2]+W[3]+W[4]+W[5], 15), style=wx.ALIGN_CENTRE)
        title.SetBackgroundColour(colour='sea green')
        nb = wx.StaticText(self, wx.ID_ANY, message('live_number'), wx.Point(X[0],20), wx.Size(W[0], 15), style=wx.ALIGN_RIGHT)
        qte = wx.StaticText(self, wx.ID_ANY, message('live_qty'), wx.Point(X[1],20), wx.Size(W[1], 15), style=wx.ALIGN_RIGHT)
        price = wx.StaticText(self, wx.ID_ANY, message('live_buy'), wx.Point(X[2],20), wx.Size(W[2], 15), style=wx.ALIGN_RIGHT)
        price = wx.StaticText(self, wx.ID_ANY, message('live_sell'), wx.Point(X[3],20), wx.Size(W[3], 15), style=wx.ALIGN_RIGHT)
        qte = wx.StaticText(self, wx.ID_ANY, message('live_qty'), wx.Point(X[4],20), wx.Size(W[4], 15), style=wx.ALIGN_RIGHT)
        nb = wx.StaticText(self, wx.ID_ANY, message('live_number'), wx.Point(X[5],20), wx.Size(W[5], 15), style=wx.ALIGN_RIGHT)

        y = 35
        self.nba = {}
        self.qtea = {}
        self.pricea = {}
        self.pricev = {}
        self.qtev = {}
        self.nbv = {}
        for i in range(0,NBLINES):
            self.nba[i] = wx.StaticText(self, wx.ID_ANY, "-", wx.Point(X[0],y), wx.Size(W[0], 15), style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
            self.qtea[i] = wx.StaticText(self, wx.ID_ANY, "-", wx.Point(X[1],y), wx.Size(W[1], 15), style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
            self.pricea[i] = wx.StaticText(self, wx.ID_ANY, "-", wx.Point(X[2],y), wx.Size(W[2], 15), style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
            self.pricev[i] = wx.StaticText(self, wx.ID_ANY, "-", wx.Point(X[3],y), wx.Size(W[3], 15), style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
            self.qtev[i] = wx.StaticText(self, wx.ID_ANY, "-", wx.Point(X[4],y), wx.Size(W[4], 15), style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
            self.nbv[i] = wx.StaticText(self, wx.ID_ANY, "-", wx.Point(X[5],y), wx.Size(W[5], 15), style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
            y = y + 15

        fmp = wx.StaticText(self, wx.ID_ANY, message('live_FMP'), wx.Point(X[1],y), wx.Size(W[1], 15), style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
        self.fmpa = wx.StaticText(self, wx.ID_ANY, "-", wx.Point(X[2],y), wx.Size(W[2], 15), style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
        self.fmpv = wx.StaticText(self, wx.ID_ANY, "-", wx.Point(X[3],y), wx.Size(W[3], 15), style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)

        # last trades
        title = wx.StaticText(self, wx.ID_ANY, message('live_lasttrades'), wx.Point(X[6],5), wx.Size(W[6]+W[7]+W[8], 15), style=wx.ALIGN_CENTRE)
        title.SetBackgroundColour(colour='sea green')
        hours = wx.StaticText(self, wx.ID_ANY, message('live_hours'), wx.Point(X[6],20), wx.Size(W[6], 15), style=wx.ALIGN_RIGHT)
        qte = wx.StaticText(self, wx.ID_ANY, message('live_qty'), wx.Point(X[7],20), wx.Size(W[7], 15), style=wx.ALIGN_RIGHT)
        price = wx.StaticText(self, wx.ID_ANY, message('live_price'), wx.Point(X[8],20), wx.Size(W[8], 15), style=wx.ALIGN_RIGHT)

        y = 35
        self.qtelt = {}
        self.hourlt = {}
        self.pricelt = {}
        for i in range(0,LTLINES):
            self.hourlt[i] = wx.StaticText(self, wx.ID_ANY, "::", wx.Point(X[6],y), wx.Size(W[6], 15), style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
            self.qtelt[i] = wx.StaticText(self, wx.ID_ANY, "-", wx.Point(X[7],y), wx.Size(W[7], 15), style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
            self.pricelt[i] = wx.StaticText(self, wx.ID_ANY, "-", wx.Point(X[8],y), wx.Size(W[8], 15), style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
            y = y + 15

        cmp = wx.StaticText(self, wx.ID_ANY, message('live_CMP'), wx.Point(X[7],y), wx.Size(W[7], 15), style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
        self.cmplt = wx.StaticText(self, wx.ID_ANY, "-", wx.Point(X[8],y), wx.Size(W[8], 15), style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)

        self.m_sclock = wx.StaticText(self, wx.ID_ANY, " ", wx.Point(X[9],y), wx.Size(W[9], 15), style=wx.ALIGN_CENTRE|wx.ST_NO_AUTORESIZE)

        self.refresh()

    def refresh(self):
        if self.m_live.hasNotebook():
            nb = self.m_live.currentNotebook(self.m_quote)
            self.displayNotebook(nb)
        lt = self.m_live.currentTrades(self.m_quote)
        self.displayLastTrades(lt)
        m = self.m_live.currentMeans(self.m_quote)
        self.displayMeans(m)
        cl = self.m_live.currentClock(self.m_quote)
        self.displayDiode(cl)

    def InitPage(self):
        self.m_parent.startLive(self.m_quote)

    def DonePage(self):
        self.m_parent.stopLive(self.m_quote)

    def cell(self,ref,nvalue):
        c = ref.GetLabel()
        if c=="-":
            c = 0
        else:
            c = long(c)
        if c==nvalue:
            bg = wx.NullColour
        else:
            bg = cNEUTRAL
        ref.SetBackgroundColour(bg)
        ref.ClearBackground()
        if nvalue == 0:
            ref.SetLabel("-")
        else:
            ref.SetLabel("{:d}".format(nvalue))
        return bg

    def cells(self, ref, svalue):
        if ref.GetLabel() == svalue:
            bg = wx.NullColour
        else:
            bg = cNEUTRAL
        ref.SetBackgroundColour(bg)
        ref.ClearBackground()
        ref.SetLabel(svalue)
        return bg

    def cellfd(self,ref,nvalue):
        c1 = ref.GetLabel()
        if c1=='-':
            bg = wx.NullColour
        else:
            c1 = float(c1)
            if nvalue=='-':
                bg = wx.NullColour
            else:
                c2 = float(nvalue)
                if c2>c1:
                    bg = cPOSITIF
                elif c2<c1:
                    bg = cNEGATIF
                else:
                    bg = wx.NullColour
        return bg

    def setcell(self,ref,val,bg=wx.NullColour):
        ref.SetBackgroundColour(bg)
        ref.ClearBackground()
        ref.SetLabel(val)
        return bg

    def displayMeans(self,m):
        if m:
            bg = self.cellfd(self.fmpa,m[0])
            self.setcell(self.fmpa,m[0],bg)
            bg = self.cellfd(self.fmpv,m[1])
            self.setcell(self.fmpv,m[1],bg)
            bg = self.cellfd(self.cmplt,m[2])
            self.setcell(self.cmplt,m[2],bg)
        else:
            self.setcell(self.fmpa,"-")
            self.setcell(self.fmpv,"-")
            self.setcell(self.cmplt,"-")

    def displayNotebook(self,nb):
        if not nb:
            for i in range(0,NBLINES):
                self.setcell(self.nba[i],"-")
                self.setcell(self.nbv[i],"-")
                self.setcell(self.qtea[i],"-")
                self.setcell(self.qtev[i],"-")
                self.setcell(self.pricea[i],"-")
                self.setcell(self.pricev[i],"-")
        else:
            line = nb[0]
            i = 0
            for achat in line:
                self.cell(self.nba[i],achat[0])
                self.cell(self.qtea[i],achat[1])
                self.cells(self.pricea[i],achat[2])
                i = i + 1

            for i in range(i,NBLINES):
                self.setcell(self.nba[i],"-")
                self.setcell(self.qtea[i],"-")
                self.setcell(self.pricea[i],"-")

            line = nb[1]
            i = 0
            for vente in line:
                self.cell(self.nbv[i],vente[0])
                self.cell(self.qtev[i],vente[1])
                self.cells(self.pricev[i],vente[2])
                i = i + 1

            for i in range(i,NBLINES):
                self.setcell(self.nbv[i],"-")
                self.setcell(self.qtev[i],"-")
                self.setcell(self.pricev[i],"-")

    def displayDiode(self,clock):
        if clock=="::":
            self.setcell(self.m_sclock," ",cNEGATIF)
        else:
            if clock==self.m_sclock.GetLabel():
                self.setcell(self.m_sclock,clock)
            else:
                self.setcell(self.m_sclock,clock,cPOSITIF)

    def displayLastTrades(self,lt):
        if not lt:
            for i in range(0,LTLINES):
                self.setcell(self.hourlt[i],"::")
                self.setcell(self.qtelt[i],"-")
                self.setcell(self.pricelt[i],"-")
        else:
            i = 0
            ssi = self.foundIndex(lt)
            for trade in lt:
                if i>ssi:
                    bg = wx.NullColour
                else:
                    bg = self.cellfd(self.pricelt[i],trade[2])
                if bg==wx.NullColour:
                    bg = self.cells(self.hourlt[i],trade[0])
                else:
                    self.setcell(self.hourlt[i], trade[0], bg)
                self.setcell(self.pricelt[i], trade[2], bg)
                self.setcell(self.qtelt[i], "{:d}".format(trade[1], bg))
                i = i + 1

            for i in range(i,LTLINES):
                self.setcell(self.hourlt[i],"")
                self.setcell(self.qtelt[i],"")
                self.setcell(self.pricelt[i],"")

    def foundIndex(self,lt):
        ssi = 0
        for trade in lt:
            if trade[0]==self.hourlt[ssi].GetLabel():
                if ("{:d}".format(trade[1]))==self.qtelt[ssi].GetLabel():
                    if trade[2]==self.pricelt[ssi].GetLabel():
                        return ssi
            ssi = ssi + 1
        return ssi


class WndTest(wx.Frame, iTrade_wxLiveMixin):
    def __init__(self, parent, quote):
        wx.Frame.__init__(self, parent=parent, id=wx.ID_ANY, title='WndTest', size=(600,190), style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        iTrade_wxLiveMixin.__init__(self)
        self.m_live = iTrade_wxLive(self, parent, quote)
        self.m_quote = quote
        self.registerLive(quote, itrade_config.refreshLive, quote.key())

        wx.EVT_CLOSE(self, self.OnCloseWindow)
        EVT_UPDATE_LIVE(self, self.OnLive)

        self.startLive()

    def OnLive(self, event):
        # print(event.param)
        self.m_live.refresh()
        self.m_live.Refresh(False)
        event.Skip()

    def OnCloseWindow(self, event):
        self.stopLive(bBusy=True)
        self.Destroy()

# ============================================================================
# Test me
# ============================================================================

def main():
    import os
    setLevel(logging.INFO)
    # load configuration
    import itrade_config
    itrade_config.set_application_root_folder(os.environ['itrade_path'])
    itrade_config.load_config()
    from itrade_local import gMessage
    gMessage.setLang('us')
    gMessage.load()
    # load extensions
    import itrade_ext
    itrade_ext.loadExtensions(itrade_config.fileExtData, itrade_config.dirExtData)
    # init modules
    from itrade_quotes import initQuotesModule, quotes
    initQuotesModule()
    ticker = 'GTO'
    quote = quotes.lookupTicker(ticker)
    info(u'{}: {}'.format(ticker, quote))
    app = wx.App(False)
    frame = WndTest(None, quote)
    if frame:
        frame.Show(show=True)
        app.MainLoop()


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
