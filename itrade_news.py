#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_news.py
#
# Description: News Aggregator
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
import logging
import re
import webbrowser

# iTrade system
from itrade_logging import setLevel, debug

# News feed
from itrade_news_google import gNewsGoogle
from itrade_news_boursorama import gNewsBoursorama

# ============================================================================
# News()
#
#   entry
#       link
#       title
#       date
#       summary
#       source      = (google,boursorama,balo,...)
#
#   callback : object to receive notifications during aggregation
#
# ============================================================================

class News(object):
    def __init__(self):
        debug('News:__init__')
        self.m_cb = None

    def setCallback(self,callback):
        self.m_cb = callback

    def feedQuote(self,quote,lang=None):
        if lang is None:
            lang = quote.country()
        print('feedQuote: lang=%s' % lang)

        # __x very temporary : need to aggregate news from various sources
        #                      using callback to notify the progress
        if lang.upper()=='FR':
            return gNewsBoursorama.feedQuote(quote,lang)
        else:
            return gNewsGoogle.feedQuote(quote,lang)

    def goto(self,parent,url):
        # url is : <service>::<url>
        # __x parent shall be self.m_cb !
        pos = re.search(r'::', url)
        if pos:
            service = url[:pos.start()]
            link = url[pos.end():]
            if service=='boursorama':
                gNewsBoursorama.goto(parent,link)
            elif service=='google':
                gNewsGoogle.goto(parent,link)
            else:
                webbrowser.open(link)

# ============================================================================
# Export me
# ============================================================================


gNews = News()

# ============================================================================
# Test me
# ============================================================================

def main():
    setLevel(logging.INFO)
    import itrade_config
    itrade_config.app_header()

    class cb(object):
        pass

    gNews.setCallback(cb)
    from itrade_quotes import quotes
    quote = quotes.lookupTicker('RIB')
    print(gNews.feedQuote(quote, 'fr'))


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
