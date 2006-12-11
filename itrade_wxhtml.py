#!/usr/bin/env python
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
# 2005-09-1x    dgil  Wrote it from scratch
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
# iTradeHtmlWindow
#
# trap the link :
#   detect ':back', ... in a news
#   launch external browser
#   or
#   render page on the internal browser
# ============================================================================

class iTradeHtmlWindow(wxhtml.HtmlWindow):
    def __init__(self, parent, id, bUseFromFeed=False, size=None):
        wxhtml.HtmlWindow.__init__(self, parent, id, style = wx.NO_FULL_REPAINT_ON_RESIZE)
        self.m_bUseFromFeed = bUseFromFeed
        self.m_parent = parent
        if size:
            self.SetSize(size)

    def OnLinkClicked(self, linkinfo):
        info('OnLinkClicked: %s\n' % linkinfo.GetHref())

        if linkinfo.GetHref()==':back':
            # special case : return to the list
            self.m_parent.OnBack()
            return

        if linkinfo.GetHref()==':scan':
            # special case : return to the list
            self.m_parent.OnScan()
            return

        if linkinfo.GetHref()==':clear':
            # special case : return to the list
            self.m_parent.OnClear()
            return

        if not self.m_bUseFromFeed:
            # launch external browser
            webbrowser.open(linkinfo.GetHref())
        else:
            # used from feed : will render the page on the HTML object
            gNews.goto(self.m_parent,linkinfo.GetHref())

# ============================================================================
# iTradeHtmlPanel
# ============================================================================

class iTradeHtmlPanel(wx.Panel):
    def __init__(self, parent, id, url=None):
        wx.Panel.__init__(self, parent, id, size = (800,600), style = wx.TAB_TRAVERSAL|wx.CLIP_CHILDREN|wx.NO_FULL_REPAINT_ON_RESIZE)
        self.url = url
        self.html = iTradeHtmlWindow(self, -1)

        wx.EVT_SIZE(self, self.OnSize)

    def OnSize(self, evt):
        self.html.SetSize(self.GetSizeTuple())

    def paint0(self):
        self.html.SetPage('<html><meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"><body>')
        self.html.AppendToPage("<head>%s</head>" % message('html_connecting'))
        self.html.AppendToPage("</body></html>")

    def refresh(self):
        if self.url:
            self.paint0()
            info('iTradeHtmlPanel::url=%s',self.url)
            self.html.LoadPage(self.url)

# ============================================================================
# iTradeRSSPanel
# ============================================================================

class iTradeRSSPanel(wx.Panel):
    def __init__(self, parent, id, quote):
        wx.Panel.__init__(self, parent, id, size = (800,600), style=wx.TAB_TRAVERSAL|wx.CLIP_CHILDREN|wx.NO_FULL_REPAINT_ON_RESIZE)
        self.m_quote = quote
        self.m_html = iTradeHtmlWindow(self, -1, bUseFromFeed=True)
        self.m_feed = None
        self.m_content = ''
        wx.EVT_SIZE(self, self.OnSize)

    # ---[ HeaderPage / AppendToPage / TrailerPage must use buffered content ]---

    def HeaderPage(self):
        self.m_html.SetPage('<html><meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"><body>')
        self.m_html.AppendToPage("<a href=':scan'>%s</a> " % message('rss_scan'))
        self.m_html.AppendToPage("<a href=':clear'>%s</a>" % message('rss_clear'))

    def AppendToPage(self,content):
        self.m_content = self.m_content + content + '\n'
        self.m_html.AppendToPage(content)

    def TrailerPage(self):
        self.m_html.AppendToPage("</html></body>")

    def SetPageWithoutCache(self,content):
        self.m_html.SetPage(content)

    # ---[ cache management ]---

    def emptyPage(self):
        # generate default content
        self.HeaderPage()
        self.m_content = ""
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

    # ---[ window management ]---

    def OnSize(self, evt):
        self.m_html.SetSize(self.GetSizeTuple())

    def refresh(self):
        self.buildPage()

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
