#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_news_balo.py
#
# Description: News from balo.com
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
# 2005-12-xx    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from __future__ import absolute_import
import logging
import re
import datetime

# iTrade system
import itrade_config
from itrade_logging import setLevel, debug, info
from itrade_local import message
from itrade_connection import ITradeConnection

# ============================================================================
#
# ============================================================================

class _Feed(object):
    pass

# ============================================================================
# News_Balo()
#
# Obvious Hack : read the information page, extract information and create a
# feed compatible with RSS News.
#
# ============================================================================

class News_Balo(object):
    def __init__(self):
        debug('News_Balo:__init__')
        self.m_feed = None
        self.m_url = None
        self.m_quote = None
        self.m_baseurl = "balo.journal-officiel.gouv.fr"

        self.m_connection = ITradeConnection(proxy=itrade_config.proxyHostname,
                               proxyAuth=itrade_config.proxyAuthentication,
                               connectionTimeout=itrade_config.connectionTimeout
                               )

    # ---[ protected interface ] ---

    def getURL(self):
        return self.m_url

    def getQuote(self):
        return self.m_quote

    def getFeed(self):
        return self.m_feed

    def splitLines(self,buf):
        p = re.compile(r"\d\d/\d\d/\d\d\d\d</td>[ \t\n\r]*<td></td>[ \t\n\r]*.*</td>", re.IGNORECASE|re.MULTILINE)
        return p.findall(buf)

    def feed(self,url):
        self.m_url = url
        self.m_feed = _Feed()
        self.m_feed.entries = []
        self.m_feed.feed = _Feed()
        self.m_feed.feed.title = 'Balo'
        news_link_url = '' #placeholder, needs research for actual url

        info('Balo News refresh %s',self.m_url)
        try:
            buf=self.m_connection.getDataFromUrl(self.m_url)
        except Exception:
            debug('News_Balo:unable to connect :-(')
            return None

        iter = self.splitLines(buf)

        for eachLine in iter:
            sdate = eachLine[0:10]
            sdate = datetime.datetime(int(sdate[6:10]),int(sdate[3:5]),int(sdate[0:2])).strftime('%a, %d %b %Y')
            snum = re.search(r'news=\d*', eachLine, re.IGNORECASE|re.MULTILINE)
            if snum:
                snum = snum.group()[5:]
            stitle = re.search(r'<a.*>.*</a>', eachLine, re.IGNORECASE|re.MULTILINE)
            if stitle:
                stitle = stitle.group()
                stitle = re.search(r'>.*<', stitle, re.IGNORECASE|re.MULTILINE)
                if stitle:
                    stitle = stitle.group()[1:-1]

                    entry = _Feed()
                    entry.link = news_link_url.format(snum)
                    entry.title = stitle
                    entry.date = sdate
                    entry.summary = ""
                    print('{}: {}'.format(sdate, stitle))
                    self.m_feed.entries.append(entry)

        return self.m_feed

    def goto(self,html,url):
        if html:
            html.paint0()
        info('goto %s',url)
        try:
            buf=self.m_connection.getDataFromUrl(url)
        except Exception:
            debug('News_Balo:unable to connect :-(')
            if html:
                html.paint_NC()
            else:
                print('unable to connect')
            return

        #print buf

        title = re.search(r'<tr>[ \t\n\r]+<td.*</td>[ \t\n\r]+</tr>', buf, re.IGNORECASE|re.MULTILINE|re.DOTALL)
        if title:
            title = title.group()
        else:
            title = ''

        buf = re.search(r'<tr>[ \t\n\r]*<td>.*</table>', buf, re.IGNORECASE|re.MULTILINE|re.DOTALL)
        if buf:
            buf = buf.group()[:-8]
            page = '<html><meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"><body>' + "<br><a href=':back'>{}</a><H3>".format(message('backtolist')) + title + "</H3>" + buf + "<br><br><a href=':back'>{}</a>".format(message('backtolist')) + "</body></html>"

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
        self.m_quote = quote
        if lang is None:
            lang = self.m_quote.country()

        return self.feed(self.m_baseurl)

# ============================================================================
# Export me
# ============================================================================


gNewsBalo = News_Balo()

# ============================================================================
# Test me
# ============================================================================

def main():
    setLevel(logging.INFO)
    itrade_config.app_header()
    from itrade_quotes import quotes
    quote = quotes.lookupTicker(ticker='RIB')
    if quote:
        gNewsBalo.feedQuote(quote)
    # gNewsBalo.goto(None,"http://www.boursorama.com/infos/imprimer_news.phtml?news=3020909")


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
