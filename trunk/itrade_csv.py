#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_csv.py
#
# Description: CSV facilities
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
# 2004-01-08    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import os
import sys
import types
import logging

# iTrade system
from itrade_logging import *

# ============================================================================
# CSV
# ============================================================================

class CSV(object):
    def __init__(self):
        pass

    def read(self,fn,fd):
        # open the file
        try:
            if fn:
                f = open(fn,'r')
            else:
                f = open(fd,'r')
        except IOError:
            # can't open the file (existing ?)
            return None

        # convert lines to list
        infile = f.readlines()

        # close the file
        f.close()

        # return the lines
        return infile

    def parse(self,line,maxn):
        #debug('CSV::parse() before :%s' % line);
        line = line.strip()
        line = line.split(';')
        #debug('CSV::parse() after :%s' % line);
        return line

    def write(self,fn,fd,lines):
        # open the file
        try:
            if fn:
                f = open(fn,'w')
            else:
                f = open(fd,'w')
        except IOError:
            # can't open the file (existing ?)
            return None

        # write each lines
        for eachItem in lines:
            txt = eachItem.__repr__()
            #print txt[0],txt[-1],'>>>',txt
            if txt[0]=="'" and txt[-1]=="'":
                txt = txt[1:-1]
            f.write( txt + '\n')

        # close the file
        f.close()

# ============================================================================
# Install the CSV system
# ============================================================================

try:
    ignore(csv)
except NameError:
    csv = CSV()

read = csv.read
parse = csv.parse
write = csv.write

# ============================================================================
# That's all folks !
# ============================================================================
