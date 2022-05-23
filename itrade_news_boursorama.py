#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_news_boursorama.py
#
# Description: News from Boursorama.com
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
# 2005-10-23    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
import logging
import re
import time

# iTrade system
import itrade_config
from itrade_logging import setLevel, info, debug
from itrade_local import message
from itrade_connection import ITradeConnection

# ============================================================================
# Used to build a Feed entry
# ============================================================================

class _FeedEntry(object):
    pass

# ============================================================================
# News_Boursorama()
#
# Obvious Hack : read the information page, extract information and create a
# feed compatible with internal RSS News.
#
# ============================================================================

class News_Boursorama(object):
    def __init__(self):
        debug('News_Boursorama:__init__')
        self.m_feed = None
        self.m_url = None
        self.m_quote = None
        self.m_baseurl = {}
        self.m_host = "www.boursorama.com"
        self.m_conn = None

        self.m_baseurl[0] = "https://www.boursorama.com/infos/actualites/actu_societes_code.phtml?symbole=1rP%s"
        self.m_baseurl[1] = "https://www.boursorama.com/communique/communique_code.phtml?symbole=1rP%s"
        self.m_baseurl[2] = "https://www.boursorama.com/infos/calendrier_code.phtml?symbole=1rP%s"
        self.m_baseurl[3] = "https://www.boursorama.com/conseils/conseils_index_code.phtml?symbole=1rP%s"
        self.m_baselink = "https://www.boursorama.com/infos/imprimer_news.phtml?news=%s"

        self.m_connection = ITradeConnection(cookies = None,
                               proxy = itrade_config.proxyHostname,
                               proxyAuth = itrade_config.proxyAuthentication,
                               connectionTimeout = itrade_config.connectionTimeout
                               )

    # ---[ protected interface ] ---
    def getURL(self):
        return self.m_url

    def getFeed(self):
        return self.m_feed

    def getQuote(self):
        return self.m_quote

    def splitLines(self,buf):
        p = re.compile(r"\d\d/\d\d/\d\d\d\d</td>[ \t\n\r]*<td></td>[ \t\n\r]*.*</td>", re.IGNORECASE|re.MULTILINE)
        return p.findall(buf)

    def getdata(self,url):
        debug("News_Boursorama:getdata: url=%s ",url)
        try:
            buf = self.m_connection.getDataFromUrl(url)
        except Exception:
            debug('News_Boursorama:unable to connect :-(')
            return None

        buf = unicode(buf, 'iso-8859-1', 'strict')
        return buf

    def feed(self, url):
        self.m_url = url
        self.m_feed = _FeedEntry()
        self.m_feed.entries = []
        self.m_feed.feed = _FeedEntry()
        self.m_feed.feed.title = 'Boursorama: ' + self.m_quote.ticker()

        info('Boursorama News refresh %s',self.m_url)
        buf = self.getdata(url)

        iter = self.splitLines(buf)
        #print iter

        for eachLine in iter:
            sdate = time.strptime(eachLine[0:10], "%d/%m/%Y")
            #print '%s -> %s' % (eachLine[0:10],sdate)
            snum = re.search(r'news=\d*', eachLine, re.IGNORECASE|re.MULTILINE)
            if snum:
                snum = snum.group()[5:]
            stitle = re.search(r'<a.*>.*</a>', eachLine, re.IGNORECASE|re.MULTILINE)
            if stitle:
                stitle = stitle.group()
                stitle = re.search(r'>.*<', stitle, re.IGNORECASE|re.MULTILINE)
                if stitle:
                    stitle = stitle.group()[1:-1]

                    entry = _FeedEntry()
                    entry.link = u'boursorama::{}'.format(self.m_baselink) % snum
                    entry.title = stitle
                    entry.date = sdate
                    entry.summary = ""
                    entry.source = "boursorama"
                    self.m_feed.entries.append(entry)

        return self.m_feed

    def goto(self, html, url):
        if html:
            html.paint0()
        info('goto %s', url)

        buf = self.getdata(url)
        #print buf

        if not buf:
            if html:
                html.paint_NC()
            else:
                print('unable to connect')
            return

        title = re.search(r'<tr>[ \t\n\r]+<td.*</font></td>[ \t\n\r]+</tr>', buf, re.IGNORECASE|re.MULTILINE|re.DOTALL)
        if title:
            title = title.group()
        else:
            title = ''

        buf = re.search(r'<tr>[ \t\n\r]*<td>.*</table>', buf, re.IGNORECASE|re.MULTILINE|re.DOTALL)
        if buf:
            buf = buf.group()[:-8]
            #print '----------------('
            #print buf
            #print ')----------------'
            page = '<html><meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"><body>' + "<br><a href=':back'>%s</a><H3>" % message('backtolist') + title + "</H3>" + buf + "<br><br><a href=':back'>%s</a>" % message('backtolist')  + "</body></html>"

            if html:
                html.SetPageWithoutCache(page)
            else:
                print(page)
        else:
            if html:
                html.paint_NC()
            else:
                print('empty')

    # ---[ public interface ] ---
    def feedQuote(self, quote, lang=None, page=0):
        if quote is None:
            return
        self.m_quote = quote
        if lang is None:
            lang = self.m_quote.country()
        return self.feed(self.m_baseurl[page].format(self.m_quote.ticker()))

# ============================================================================
# Export me
# ============================================================================


gNewsBoursorama = News_Boursorama()

# ============================================================================
# Test me
# ============================================================================

def main():
    setLevel(logging.INFO)
    itrade_config.app_header()
    from itrade_quotes import quotes
    quote = quotes.lookupTicker('RIB')
    print(gNewsBoursorama.feedQuote(quote))
    gNewsBoursorama.goto(None, "https://www.boursorama.com/infos/imprimer_news.phtml?news=3020909")


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
