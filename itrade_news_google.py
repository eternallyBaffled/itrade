#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_news_google.py
#
# Description: News from Google.com
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
import time
import webbrowser
import string

# iTrade system
from itrade_logging import setLevel, info, debug
from itrade_local import setLocale

# feedparser
import feedparser

# ============================================================================
# Used to build a Feed entry
# ============================================================================

class _FeedEntry(object):
    pass

# ============================================================================
# News_Google()
#
# Google RSS News : http://news.google.fr/news?hl=%s&ie=UTF-8&output=rss&q=%s
#   hl  language
#   q   company name
# ============================================================================

class News_Google(object):
    def __init__(self):
        debug('News_Google:__init__')
        self.m_feed = None
        self.m_url = None
        self.m_quote = None

        self.m_baseurl = "https://news.google.fr/news?hl=%s&ie=UTF-8&output=rss&q=%s&scoring=d"

    # ---[ protected interface ] ---
    def getURL(self):
        return self.m_url

    def getFeed(self):
        return self.m_feed

    def getQuote(self):
        return self.m_quote

    def feed(self,url):
        self.m_url = url
        info('RSS News refresh %s',self.m_url)
        self.m_feed = self.convert(feedparser.parse(self.m_url))
        return self.m_feed

    def convert(self,feed):
        # convert Google RSS to internal RSS
        if not feed:
            return None

        flux = _FeedEntry()
        flux.entries = []
        flux.feed = _FeedEntry()
        flux.feed.title = feed.feed.title

        # force local to 'en' : strptime() will work correctly
        setLocale('en')

        for eachEntry in feed.entries:
            entry = _FeedEntry()
            entry.link = "google::%s" % eachEntry.link
            entry.title = "%s" % eachEntry.title

            # convert datetime in the right locale
            entry.date = time.strptime(eachEntry.date, "%a, %d %b %Y %H:%M:%S %Z")
            print('%s: %s -> %s' % (entry.link,eachEntry.date,entry.date))

            entry.summary = eachEntry.summary
            entry.source = "google"
            flux.entries.append(entry)

        # restore locale
        setLocale()

        #info('Feed %s',flux.feed.title)
        return flux

    def goto(self,html,url):        # __x to be removed
        webbrowser.open(url)

    # ---[ public interface ] ---
    def feedQuote(self,quote,lang=None,page=0):
        self.m_quote = quote
        if lang is None:
            lang = self.m_quote.country()

        param = self.m_quote.name()+' '+self.m_quote.ticker()
        param = string.replace(param,' ','+')

        return self.feed(self.m_baseurl % (lang,param))

# ============================================================================
# Export me
# ============================================================================

try:
    ignore(gNewsGoogle)
except NameError:
    gNewsGoogle = News_Google()

# ============================================================================
# Test me
# ============================================================================

def main():
    global quote
    setLevel(logging.INFO)
    from itrade_local import setLang
    setLang('fr')
    from itrade_quotes import quotes
    quote = quotes.lookupTicker('AAPL')
    print(gNewsGoogle.feedQuote(quote))
    quote = quotes.lookupTicker('AXL')
    print(gNewsGoogle.feedQuote(quote))
    print(gNewsGoogle.feedQuote(quote, 'fr'))
    quote = quotes.lookupTicker('SAF')
    print(gNewsGoogle.feedQuote(quote))


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
