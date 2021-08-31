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
from __future__ import print_function


def read_b(fn):
    try:
        f = open(fn, 'r')
    except IOError:
        return []

    with f:
        lines = f.readlines()
    return lines


def read(fn, fd):
    if fn:
        return read_b(fn)
    else:
        return read_b(fd)


def parser(line, separator=';'):
    # logging.debug(u'CSV::parse() before :{}'.format(line));
    line = line.strip()
    if line == '':
        return None
    line = line.split(separator)
    # logging.debug('CSV::parse() after :{}'.format(line));
    return line


def parse(line, maxn):
    return parser(line, ';')


def write_b(fn, lines):
    with open(fn, 'w') as f:
        for eachItem in lines:
            txt = eachItem.__repr__()
            # print(txt[0], txt[-1], '>>>', txt)
            if txt[:2] in ('u"', "u'"):
                txt = txt[1:]
            if txt[0] == "'" and txt[-1] == "'":
                txt = txt[1:-1]
            if txt[0] == '"' and txt[-1] == '"':
                txt = txt[1:-1]
            f.write(txt + '\n')


def write(fn, fd, lines):
    try:
        if fn:
            write_b(fn, lines)
        else:
            write_b(fd, lines)
    except IOError:
        print(u"Can't open the file {}/{} for writing!".format(fn, fd))
        return None


def main():
    from itrade_logging import setLevel
    import itrade_config
    import logging
    setLevel(logging.INFO)
    itrade_config.app_header()


if __name__ == '__main__':
    main()
# ============================================================================
# That's all folks !
# ============================================================================
