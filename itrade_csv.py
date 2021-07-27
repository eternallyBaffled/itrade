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
# 2004-01-08    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
#import logging

# ============================================================================
# CSV
# ============================================================================

from __future__ import print_function
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
        #logging.debug('CSV::parse() before :%s' % line);
        line = line.strip()
        if line == '':
            # skip blank lines
            return None
        line = line.split(';')
        #logging.debug('CSV::parse() after :%s' % line);
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
            print("can't open the file %s/%s (existing ?) for writing !" % (fn,fd))
            return None

        # write each lines
        for eachItem in lines:
            txt = eachItem.__repr__()
            #print txt[0],txt[-1],'>>>',txt
            if txt[:2] in ('u"', "u'"):
                txt = txt[1:]
            if txt[0]=="'" and txt[-1]=="'":
                txt = txt[1:-1]
            if txt[0]=='"' and txt[-1]=='"':
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
