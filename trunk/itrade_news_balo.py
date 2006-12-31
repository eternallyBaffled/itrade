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
# 2005-12-xx    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import re
import string
import urllib
import datetime
import webbrowser

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_local import message

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

    # ---[ protected interface ] ---

    def getURL(self):
        return self.m_url

    def getQuote(self):
        return self.m_quote

    def getFeed(self):
        return self.m_feed

    def splitLines(self,buf):
        p = re.compile("\d\d/\d\d/\d\d\d\d</td>[ \t\n\r]*<td></td>[ \t\n\r]*.*</td>",re.IGNORECASE|re.MULTILINE)
        return p.findall(buf)

    def feed(self,url):
        self.m_url = url
        self.m_feed = _Feed()
        self.m_feed.entries = []
        self.m_feed.feed = _Feed()
        self.m_feed.feed.title = 'Balo'

        info('Balo News refresh %s',self.m_url)
        try:
            f = urllib.urlopen(self.m_url)
        except:
            debug('News_Balo:unable to connect :-(')
            return None

        buf = f.read()
        iter = self.splitLines(buf)

        for eachLine in iter:
            sdate = eachLine[0:10]
            sdate = datetime.datetime(int(sdate[6:10]),int(sdate[3:5]),int(sdate[0:2])).strftime('%a, %d %b %Y')
            snum = re.search('news=\d*',eachLine,re.IGNORECASE|re.MULTILINE)
            if snum:
                snum = snum.group()[5:]
            stitle = re.search('<a.*>.*</a>',eachLine,re.IGNORECASE|re.MULTILINE)
            if stitle:
                stitle = stitle.group()
                stitle = re.search('>.*<',stitle,re.IGNORECASE|re.MULTILINE)
                if stitle:
                    stitle = stitle.group()[1:-1]

                    entry = _Feed()
                    entry.link = itrade_config.boursoNewsLinkxxxxxxxxxxxxxxxxUrl%snum
                    entry.title = stitle
                    entry.date = sdate
                    entry.summary = ""
                    print('%s: %s' % (sdate,stitle))
                    self.m_feed.entries.append(entry)

        return self.m_feed

    def goto(self,html,url):
        if html:
            html.paint0()
        info('goto %s',url)
        try:
            f = urllib.urlopen(url)
        except:
            debug('News_Balo:unable to connect :-(')
            if html:
                html.paint_NC()
            else:
                print 'unable to connect'
            return

        buf = f.read()
        #print buf

        title = re.search('<tr>[ \t\n\r]+<td.*</td>[ \t\n\r]+</tr>',buf,re.IGNORECASE|re.MULTILINE|re.DOTALL)
        if title:
            title = title.group()
        else:
            title = ''

        buf = re.search('<tr>[ \t\n\r]*<td>.*</table>',buf,re.IGNORECASE|re.MULTILINE|re.DOTALL)
        if buf:
            buf = buf.group()[:-8]
            page = '<html><meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"><body>' + "<br><a href=':back'>%s</a><H3>" % message('backtolist') + title + "</H3>" + buf + "<br><br><a href=':back'>%s</a>" % message('backtolist')  + "</body></html>"

            if html:
                html.SetPageWithoutCache(page)
            else:
                print page
        else:
            if html:
                html.paint_NC()
            else:
                print 'empty'

    # ---[ public interface ] ---
    def feedQuote(self,quote,lang=None,page=0):
        self.m_quote = quote
        if lang==None:
            lang = self.m_quote.country()

        return self.feed(self.m_baseurl)

# ============================================================================
# Export me
# ============================================================================

try:
    ignore(gNewsBalo)
except NameError:
    gNewsBalo = News_Balo()

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes
    quote = quotes.lookupTicker('RIB')
    gNewsBalo.feedQuote(quote)

    #gNewsBalo.goto(None,"http://www.boursorama.com/infos/imprimer_news.phtml?news=3020909")

# ============================================================================
# That's all folks !
# ============================================================================
