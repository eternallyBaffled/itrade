#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade.py
# Version      : $Id: itrade.py,v 1.14 2006/01/20 18:46:14 dgil Exp $
#
# Description: Main
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
# 2005-03-17    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Version management
# ============================================================================

__revision__ = "$Id: itrade.py,v 1.14 2006/01/20 18:46:14 dgil Exp $"
__author__ = "Gilles Dumortier (dgil@ieee.org)"
__version__ = "0.4"
__status__ = "alpha"
__cvsversion__ = "$Revision: 1.14 $"[11:-2]
__date__ = "$Date: 2006/01/20 18:46:14 $"[7:-2]
__copyright__ = "Copyright (c) 2004-2006 Gilles Dumortier"
__license__ = "GPL"
__credits__ = """ """

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
from itrade_quotes import *
import itrade_import
import itrade_portfolio
import itrade_matrix
import itrade_wxmain

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

# ============================================================================
# Main / Command line analysing
# ============================================================================

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "eho:vt:iq:f:l:d", ["help", "output=", "ticker=", "quote=","file=","lang="])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)
    output = None
    verbose = False
    quote = None
    file = None
    wx = True
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
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-o", "--output"):
            output = a
        if o in ("-f", "--file"):
            file = a
        if o in ("-l", "--lang"):
            lang = a
        if o in ("-t", "--ticker"):
            quote = quotes.lookupTicker(a)
            if not quote:
                print 'quote %s not found !' % a
        if o in ("-q","--quote"):
            quote = quotes.lookupISIN(a)
            if not quote:
                print 'quote %s not found !' % a

    # use the correct pack language
    gMessage.setLang(lang)
    gMessage.load()

    if wx:
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
# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
