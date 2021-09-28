#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_isin.py
#
# Description: ISIN - build & Verification (ISO 3166)
#              "modulus 10 double add double"
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
# 2006-06-11    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
from functools import partial

# iTrade system
from itrade_logging import setLevel, info


# ============================================================================
# checkISIN
# ============================================================================
def _is_odd(n):
    return n & 1

def _build_verif_code(code):
    myCode = _transcode_to_decimal(code)

    myTotal = 0
    for pos, char in enumerate(myCode, start=1):
        myInt = _do_something_with_char(char, pos%2==_is_odd(len(myCode)))
        myTotal = myTotal + myInt
    return (10 - (myTotal%10)) % 10


def _do_something_with_char(char, odd):
    if odd:
        myInt = int(char) * 2
#        print('myInt={:d}'.format(myInt))
    else:
        myInt = int(char)
#        print('myInt={:d}'.format(myInt))
    if myInt > 9:
        myInt = (myInt % 10) + (myInt // 10)
#            print('myInt-redux={:d}'.format(myInt))
    return myInt


def _transcode_to_decimal(code):
    """
    Takes a string with numbers and upper case characters from the roman alphabet and transforms it to one containing
    only number characters.
    """
#    print(u'_build_verif_code({})'.format(code))
    myCode = u''
    for myCar in code:
        myInt = char_to_number(myCar)
        myCode += u'{:d}'.format(myInt)
#    print('code={}'.format(code), 'len(myCode)={:d}'.format(len(myCode)), 'myCode={}'.format(myCode))
    return myCode


def char_to_number(myCar):
    if myCar.isnumeric():
        myInt = int(myCar)
    else:
        myInt = ord(myCar) - 55
    return myInt


def checkISIN(isin):
    isin = isin.strip().upper()
    if len(isin) != 12:
        print('length fails')
        return False

    temp_ck = isin[-1:]
    if not temp_ck.isnumeric():
        print('non-numeric check digit')
        return False

    check_digit = int(temp_ck)
    calculated_check_digit = _build_verif_code(isin[:-1])
#    print(calculated_check_digit)
    return check_digit == calculated_check_digit

# ============================================================================
# buildISIN
# ============================================================================

def buildISIN(country, code):
    code = u'{}{:0>{width}}'.format(country, code, width=11-len(country))
    return code + "{:d}".format(_build_verif_code(code))

# ============================================================================
# filterName
#
# remove any ';' character in the quote name
# ============================================================================

def filterName(name):
    while True:
        pos = name.find(';')
        if pos > -1:
            # print(pos, name)
            name = name[:pos] + name[pos+1:]
            # print(name)
        else:
            return name

# ============================================================================
# CINS numbers employ the same Issuer (6 characters)/Issue (2 character &
# check digit) concept espoused by the CUSIP Numbering System, which is
# described in detail on the  following page. It is important to note that
# the first position of a CINS code is always represented by an alpha
# character, signifying the Issuer's country code (domicile) or geographic
# region:
#
#   A = Austria         J = Japan           S = South Africa
#   B = Belgium         K = Denmark         T = Italy
#   C = Canada          L = Luxembourg      U = United States
#   D = Germany         M = Mid-East        V = Africa - Other
#   E = Spain           N = Netherlands     W = Sweden
#   F = France          P = South America   X= Europe-Other
#   G = United Kingdom  Q = Australia       Y = Asia
#   H = Switzerland     R = Norway
#
# The CUSIP number consists of nine characters: a base number of six
# characters known as the issuer number, (the 4th, 5th and/or 6th position may
# be alpha or numeric) and a two character suffix (either numeric or
# alphabetic or both) known as the issue number. The ninth character is a
# check digit
#
# The first issue number for an issuer's equity securities is 10
# ============================================================================

cusip_country = {
    'T' : 'IT',
    'L' : 'LU',
    'G' : 'UK',
    'F' : 'FR',
    'E' : 'ES',
    'D' : 'DE',
    'C' : 'CA',
    'B' : 'BE',
}


# ============================================================================
# Test
# ============================================================================

def main():
    import itrade_config
    setLevel(logging.INFO)
    itrade_config.app_header()
    info(u'test1 FR0000072621 : {}'.format(checkISIN(u'FR0000072621')))
    info(u'test1 FR0000072621 : {}'.format(buildISIN(u'FR', u'07262')))
    info(u'test2 FR0010209809 : {}'.format(checkISIN(u'FR0010209809')))
    info(u'test2 FR0010209809 : {}'.format(buildISIN(u'FR', u'1020980')))
    info(u'test3 FR0004154060 : {}'.format(checkISIN(u'FR0004154060')))
    info(u'test3 FR0004154060 : {}'.format(buildISIN(u'FR', u'000415406')))
    info(u'test4 ES0178430E18 : {}'.format(checkISIN(u'ES0178430E18')))
    info(u'test4 ES0178430E18 : {}'.format(buildISIN(u'ES', u'0178430E1')))
    info(u'test5 NSCFR0000TF6 : {}'.format(checkISIN(u'NSCFR0000TF6')))
    info(u'test4 NSCFR0000TF6 : {}'.format(buildISIN(u'NSCFR', u'TF')))


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
