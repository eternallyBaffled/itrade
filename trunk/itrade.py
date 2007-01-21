#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade.py
#
# Description: Main
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
# 2005-03-17    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import getopt
import sys

# iTrade system
import itrade_config
from itrade_local import *
from itrade_logging import *
setLevel(logging.INFO)
import itrade_quotes
import itrade_ext
import itrade_import
import itrade_portfolio
import itrade_matrix

# ============================================================================
# Usage
# ============================================================================

def usage():
    print "%s %s - %s version - %s" % (itrade_config.softwareName,itrade_config.softwareVersion,itrade_config.softwareLicense,itrade_config.softwareCopyright)
    print
    print "-h / --help  this help                                       "
    print "-v           verbose / debug mode                            "
    print "-e           connect live and display portfolio evaluation   "
    print "-i           connect and import a ticker (or isin)           "
    print "-d           disconnected (no live update / no network)      "
    print
    print "--file=<f>   import or export using a file (EBP file format) "
    print "--quote=<n>  select a quote by its isin                      "
    print "--ticker=<n> select a quote by its ticker                    "
    print
    print "--lang=<l>   select the language to be used (fr,us,...)      "
    print
    print "--user=<p>   select usrerdata/ specific folder               "
    print
    print "--nopsyco    do not use psyco                                "

# ============================================================================
# Main / Command line analysing
# ============================================================================

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "eho:vt:iq:f:l:du:", ["help", "output=", "ticker=", "quote=","file=","lang=","user=","nopsyco"])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)

    # default values
    output = None
    verbose = False
    quote = None
    file = None
    wx = True
    nopsyco = False

    vticker = None
    vquote  = None

    lang = gMessage.getAutoDetectedLang('us')
    for o, a in opts:

        if o == "-d":
            itrade_config.setDisconnected(True)

        if o == "-v":
            verbose = True
            wx = False

        if o == "-e":
            itrade_portfolio.cmdline_evaluatePortfolio()
            wx = False

        if o == "-i":
            if quote:
                if file:
                    itrade_import.cmdline_importQuoteFromFile(quote,file)
                else:
                    itrade_import.cmdline_importQuoteFromInternet(quote)
            else:
                matrix = itrade_matrix.createMatrix()
                if file:
                    itrade_import.cmdline_importMatrixFromFile(matrix,file)
                else:
                    itrade_import.cmdline_importMatrixFromInternet(matrix)
            wx = False

        if o == "-h" or o == "--help":
            usage()
            sys.exit()

        if o == "-o" or o == "--output":
            output = a

        if o == "-u" or o == "--user":
            itrade_config.dirUserData = a
            if not os.path.exists(itrade_config.dirUserData):
                print 'userdata folder %s not found !' % a
                sys.exit()

        if o  == "--nopsyco":
            nopsyco = True

        if o == "-f" or o == "--file":
            file = a

        if o == "-l" or o == "--lang":
            lang = a
            itrade_config.lang = 255

        if o == "-t" or o == "--ticker":
            vticker = a

        if o == "-q" or o == "--quote":
            vquote = a

    # Import Psyco if available
    if not nopsyco:
        try:
            import psyco
            psyco.full()
            print 'Psyco is running'
        except ImportError:
            print 'Psyco is not running (library not found)'
    else:
        print 'Psyco is not running (forced by command line)'

    # load configuration
    itrade_config.loadConfig()

    # load extensions
    itrade_ext.loadExtensions()

    # init modules
    itrade_quotes.initModule()
    itrade_portfolio.initModule()

    # use the correct pack language
    if itrade_config.lang == 255:
        gMessage.setLang(lang)
        gMessage.load()

    # commands
    if vticker:
        quote = itrade_quotes.quotes.lookupTicker(vticker)
        if not quote:
            print 'ticker %s not found !' % vticker
            sys.exit()

    if vquote:
        quote = itrade_quotes.quotes.lookupKey(vquote)
        if not quote:
            print 'quote %s not found ! format is : <ISINorTICKER>.<EXCHANGE>.<PLACE>' % vquote
            sys.exit()

    if wx:
        import itrade_wxmain
        itrade_wxmain.start_iTradeWindow()

    if verbose:
        if quote:
            portfolio = itrade_portfolio.loadPortfolio()
            quote.update()
            quote.compute()
            quote.printInfo()

    # save the user configuration
    # __x ? itrade_config.saveConfig()

# ============================================================================
# Launch me
# ============================================================================

if __name__ == "__main__":
    setLevel(logging.INFO)

    main()

# ============================================================================
# That's all folks !
# ============================================================================
