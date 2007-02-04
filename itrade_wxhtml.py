#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxhtml.py
#
# Description: wxPython HTML window
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is	Gilles Dumortier.
#
# Portions created by the Initial Developer are Copyright (C) 2004-2007 the
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
# 2005-09-1x    dgil  Wrote it from scratch
# 2007-01-2x    dgil  Change the way OnLinkClick handler is managed
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import os
import logging
import webbrowser
import time

# wxPython system
import itrade_wxversion
import wx
import wx.html as wxhtml

# iTrade system
from itrade_logging import *
from itrade_local import message

# iTrade system
from itrade_logging import *
from itrade_news import gNews

# ============================================================================
# wxUrlClickHtmlWindow
#
# HTML window that generates and OnLinkClicked event
# Use this to avoid having to override HtmlWindow
# ============================================================================

wxEVT_HTML_URL_CLICK = wx.NewId()
EVT_HTML_URL_CLICK = wx.PyEventBinder(wxEVT_HTML_URL_CLICK)

class wxHtmlWindowUrlClick(wx.PyEvent):
    def __init__(self, linkinfo):
        wx.PyEvent.__init__(self)
        self.SetEventType(wxEVT_HTML_URL_CLICK)
        self.linkinfo = (linkinfo.GetHref(), linkinfo.GetTarget())

class wxUrlClickHtmlWindow(wxhtml.HtmlWindow):

    # __init__ ?
    #if "gtk2" in wx.PlatformInfo:
    #    self.NormalizeFontSizes()

    def OnLinkClicked(self, linkinfo):
        wx.PostEvent(self, wxHtmlWindowUrlClick(linkinfo))

# ============================================================================
# iTradeHtmlPanel
#
# trap the link :
#   launch external browser
# ============================================================================

class iTradeHtmlPanel(wx.Panel):
    def __init__(self, parent,id, url=None):
        wx.Panel.__init__(self, parent, id, size = (800,600), style = wx.TAB_TRAVERSAL|wx.CLIP_CHILDREN|wx.NO_FULL_REPAINT_ON_RESIZE)
        self.url = url
        self.m_parent = parent

        self.m_html = wxUrlClickHtmlWindow(self, -1)
        EVT_HTML_URL_CLICK(self.m_html, self.OnLinkClick)

        wx.EVT_SIZE(self, self.OnSize)

    # ---[ Default OnLinkClick handler ] --------------------------------------

    def OnLinkClick(self, event):
        info('OnLinkClick: %s\n' % event.linkinfo[0])
        clicked = event.linkinfo[0]

        # launch external browser
        webbrowser.open(clicked)

    # ---[ Window Management ] ------------------------------------------------

    def OnSize(self, evt):
        self.m_html.SetSize(self.GetSizeTuple())

    def paint0(self):
        self.m_html.SetPage('<html><meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"><body>')
        self.m_html.AppendToPage("<head>%s</head>" % message('html_connecting'))
        self.m_html.AppendToPage("</body></html>")

    def refresh(self):
        if self.url:
            self.paint0()
            info('iTradeHtmlPanel::url=%s',self.url)
            self.m_html.LoadPage(self.url)

    def InitPage(self):
        self.refresh()

    def DonePage(self):
        pass

# ============================================================================
# iTradeRSSPanel
#
# trap the link :
#   detect ':back', ... in a news
#   launch external browser
#   or
#   render page on the internal browser
# ============================================================================

class iTradeRSSPanel(wx.Panel):
    def __init__(self, parent, id, quote):
        wx.Panel.__init__(self, parent, id, size = (800,600), style=wx.TAB_TRAVERSAL|wx.CLIP_CHILDREN|wx.NO_FULL_REPAINT_ON_RESIZE)
        self.m_quote = quote

        self.m_html = wxUrlClickHtmlWindow(self, -1)
        EVT_HTML_URL_CLICK(self.m_html, self.OnLinkClick)

        self.m_feed = None
        self.m_content = ''

        wx.EVT_SIZE(self, self.OnSize)

    # ---[ Default OnLinkClick handler ] --------------------------------------

    def OnLinkClick(self, event):
        info('iTradeRSSPanel:OnLinkClick: %s\n' % event.linkinfo[0])
        clicked = event.linkinfo[0]

        if clicked == ':back':
            # special case : return to the list
            self.OnBack()
            return

        elif clicked == ':scan':
            # special case : return to the list
            self.OnScan()
            return

        elif clicked == ':clear':
            # special case : return to the list
            self.OnClear()
            return

        # render the page on the HTML object
        gNews.goto(self,clicked)

    # ---[ HeaderPage / AppendToPage / TrailerPage must use buffered content ]---

    def HeaderPage(self):
        self.m_content = ""
        self.m_html.SetPage('<html><meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"><body>')
        self.m_html.AppendToPage("<a href=':scan'>%s</a> " % message('rss_scan'))
        self.m_html.AppendToPage("<a href=':clear'>%s</a>" % message('rss_clear'))

    def AppendToPage(self,content):
        #print 'AppendToPage:',self.m_content,content
        self.m_content = self.m_content + content
        self.m_content = self.m_content + '\n'
        self.m_html.AppendToPage(content)

    def TrailerPage(self):
        self.m_html.AppendToPage("</html></body>")

    def SetPageWithoutCache(self,content):
        self.m_html.SetPage(content)

    # ---[ cache management ]---

    def emptyPage(self):
        # generate default content
        self.HeaderPage()
        self.TrailerPage()

        # save it
        self.saveCache()

    def deleteCache(self):
        fn = os.path.join(itrade_config.dirCacheData,'%s.htm' % self.m_quote.key())
        info('deleteCache(%s)' % fn)
        try:
            os.remove(fn)
        except OSError:
            pass

    def loadCache(self):
        fn = os.path.join(itrade_config.dirCacheData,'%s.htm' % self.m_quote.key())
        if os.path.exists(fn):
            try:
                f = open(fn,'r')
                txt = f.read()
            except IOError:
                self.emptyPage()
                info('loadCache(%s) : IOError -> empty page' % fn)
                return
            self.HeaderPage()
            self.AppendToPage(txt)
            self.TrailerPage()
            info('loadCache(%s) : OK' % fn)
        else:
            self.emptyPage()
            info('loadCache(%s) : no cache -> empty page' % fn)

    def saveCache(self):
        fn = os.path.join(itrade_config.dirCacheData,'%s.htm' % self.m_quote.key())

        # open the file
        try:
            f = open(fn,'w')
        except IOError:
            # can't open the file (existing ?)
            info('saveCache(%s) : IOError :-(' % fn)
            return False

        f.write(self.m_content)

        # close the file
        f.close()

        info('saveCache(%s) : OK' % fn)

    # ---[ Window Management ]-------------------------------------------------

    def OnSize(self, evt):
        self.m_html.SetSize(self.GetSizeTuple())

    def refresh(self):
        self.buildPage()

    def InitPage(self):
        self.refresh()

    def DonePage(self):
        pass

    # ---[ display content ]---

    def paint0(self):
        self.HeaderPage()
        self.AppendToPage("<head>%s</head>" % message('html_connecting'))
        self.TrailerPage()

    def paint_NC(self):
        self.HeaderPage()
        self.AppendToPage("<head>%s</head>" % message('html_noconnect'))
        self.TrailerPage()

    def buildPage(self):
        if self.m_feed and self.m_feed.entries:
            info('Feed %s',self.m_feed.feed.title)
            self.HeaderPage()

            self.AppendToPage("<head>%s</head><p>" % self.m_feed.feed.title)

            for eachEntry in self.m_feed.entries:
                self.AppendToPage("%s : <a href='%s'>%s</a><p>" % (time.strftime('%x',eachEntry.date),eachEntry.link,eachEntry.title))

            self.TrailerPage()
            self.saveCache()
        else:
            self.loadCache()

    # ---[ Commands ]---

    def OnScan(self):
        info('OnScan')
        self.m_feed = gNews.feedQuote(self.m_quote)
        self.buildPage()

    def OnClear(self):
        info('OnClear')
        self.deleteCache()
        self.emptyPage()

    def OnBack(self):
        info('OnClear')
        self.buildPage()

# ============================================================================
# iTradeLaunchBrowser
# ============================================================================

def iTradeLaunchBrowser(url,new=False):
    webbrowser.open(url,new,autoraise=True)

# ============================================================================
# That's all folks !
# ============================================================================
