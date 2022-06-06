#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_local.py
#
# Description: Locales
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
# 2005-10-09    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
import logging
import locale
import sys
import time
import os

# iTrade system
import itrade_config
import itrade_csv

# ============================================================================
# Supported languages
# ============================================================================

nl_supported = {
    'fr': u'Français',
    'pt': u'Portuguese',
    'de': u'Deutsch',
    'it': u"Italian",
    'en': u'English',
    'us': u'English'
    }

nl_posix = {
    'fr': 'fr_FR',
    'pt': 'pt_PT',
    'de': 'de_DE',
    'it': 'it_IT',
    'en': 'en_US',
    'us': 'en_US',
    }

nl_autodetect = {
    'fr_FR': 'fr',
    'pt_PT': 'pt',
    'de_DE': 'de',
    'it_IT': 'it',
    'en_US': 'en',
    'English_United States': 'en'
    }

nl_convert = {
    'en': 'us'
    }

# ============================================================================
# getGroupChar
# ============================================================================

nl_groupsep = {
    'fr': ' ',
    'pt': ' ',
    'de': ' ',
    'it': ' ',
    'en': ',',
    'us': ','
    }

def getGroupChar():
    ll = gMessage.getLang()
    if ll in nl_groupsep:
        return nl_groupsep[ll]
    else:
        return ' '

# ============================================================================
# getDecimalChar
# ============================================================================

nl_decsep = {
    'fr': ',',
    'pt': ',',
    'de': ',',
    'it': ',',
    'en': '.',
    'us': '.'
    }

def getDecimalChar():
    ll = gMessage.getLang()
    if ll in nl_decsep:
        return nl_decsep[ll]
    else:
        return '.'

# ============================================================================
# getShortDateFmt
# ============================================================================

nl_shortdatefmt = {
    'fr': '%d.%m',
    'pt': '%d.%m',
    'de': '%d.%m',
    'it': '%d.%m',
    'en': '%m.%d',
    'us': '%m.%d'
    }

def getShortDateFmt():
    ll = gMessage.getLang()
    if ll in nl_shortdatefmt:
        return nl_shortdatefmt[ll]
    else:
        return '%d.%m'

# ============================================================================
# LocalMessages
#
# file format :
#
#   <ref>;<message>
#
# ============================================================================

class LocalMessages(object):
    def __init__(self):
        self.m_msg = {}
        self.m_llang = {}
        self.m_lang = None

    def load(self, fn=None):
        if self.m_lang in self.m_llang:
            logging.warning(u'lang {} already loaded !'.format(self.m_lang))
            return

        if fn is None:
            fn = os.path.join(itrade_config.dirSysData, u'{}.messages.txt'.format(self.m_lang))
        infile = itrade_csv.read(fn, fn)
        if infile:
            # store filename used for messaging
            self.m_llang[self.m_lang] = fn

            # scan each line to read each trade
            for eachLine in infile:
                item = itrade_csv.parse(eachLine.decode("utf-8"), 2)
                if item:
                    self.addMsg(item)
            print(u'Language Pack {} : {}'.format(self.m_lang, self.m_llang[self.m_lang]))
        else:
            print(u'No Language Pack for {} !'.format(self.m_lang))
            # raise Exception(u'lang {} not found !'.format(self.m_lang))

    def setLocale(self, lang=None):
        # try to set up the C runtime (_locale)
        if lang is None:
            lang = self.m_lang
            logging.debug(u'setLocale(): default to {}'.format(lang))
        else:
            logging.debug(u'setLocale(): set to {}'.format(lang))

        if sys.platform == 'darwin':
            # do nothing :-( (locale support on MacOSX is minimal)
            pass
        elif sys.platform.startswith("win"):
            try:
                locale.setlocale(locale.LC_ALL, lang)
            except locale.Error:
                print(u'setlocale {} : {}'.format(lang, 'locale unknown in this windows configuration ?'))
        else:
            try:
                locale.setlocale(locale.LC_ALL, nl_posix[lang])
            except locale.Error:
                print(u'setlocale {} : {}'.format(nl_posix[lang], 'locale unknown in this configuration ?'))

        # strptime is bugged :
        # first call will reset the TimeRE cache but continue using the previous TimeRE (bad lang) :-( !
        # obhack: call strptime to reset the cache, next call will use the right object
        time.strptime('10', '%H')
        # NB: %H will be cached with the bad lang ; it is not important at all because %H is not localized

    def getLocale(self):
        lang, cp = locale.getlocale()
        return lang

    def setLang(self, l=None):
        if l:
            self.m_lang = self.langSupported(l)
        else:
            # default to French
            self.m_lang = 'fr'

        # try to set up the C runtime (_locale)
        self.setLocale()

    def getLang(self):
        return self.m_lang

    def getLangFile(self):
        if self.m_lang in self.m_llang:
            return self.m_llang[self.m_lang]
        else:
            return None

    def langSupported(self, l):
        if l in nl_supported:
            if l in nl_convert:
                return nl_convert[l]
            else:
                return l
        else:
            print(u"setlocale '{}' : unsupported language - default to french".format(l))
            return 'fr'

    def addMsg(self, m):
        if len(m) != 2:
            # well-formed ?
            return
        key = u'{}{}'.format(self.m_lang, m[0])
        if key in self.m_msg:
            raise Exception(u'addMsg:: key %s already exist')
        self.m_msg[key] = m[1]

    def getMsg(self, ref):
        if not self.m_lang:
            # package not initialized :-(
            lang = gMessage.getAutoDetectedLang('us')
            # print('getMsg: need to setLang :',lang," during ref:",ref)
            gMessage.setLang(lang)
        if len(self.m_msg) == 0:
            # print('getMsg: need to load lang pack :',lang)
            gMessage.load()

        key = '{}{}'.format(self.m_lang, ref)
        if key in self.m_msg:
            return self.m_msg[key]
        else:
            return '?{}:{}?'.format(self.m_lang, ref)

    def getAutoDetectedLang(self, dl='us'):
        # set the default locale
        locale.setlocale(locale.LC_ALL, '')
        # get the current locale encoding and codepage
        enc, cp = locale.getlocale()

        # check if encoding known
        if enc in nl_autodetect:
            return nl_autodetect[enc]
        else:
            # return the default lang provided by the caller
            return dl

# ============================================================================
# Install the Local system
# ============================================================================


gMessage = LocalMessages()

message = gMessage.getMsg

# ============================================================================
# Test me
# ============================================================================

def main():
    import itrade_logging
    itrade_config.app_header()
    itrade_logging.setLevel(logging.INFO)
    print(u'default (detection): {}'.format(gMessage.getAutoDetectedLang()))
    gMessage.setLang('us')
    print(u'pack us: {}'.format(gMessage.getLangFile()))
    gMessage.setLang('fr')
    gMessage.load()
    print(u'pack fr: {}'.format(gMessage.getLangFile()))
    gMessage.setLang('en')
    gMessage.load()
    print(u'pack en: {}'.format(gMessage.getLangFile()))
    gMessage.setLang('pt')
    gMessage.load()
    print(u'pack pt: {}'.format(gMessage.getLangFile()))
    gMessage.setLang('de')
    gMessage.load()
    print(u'pack de: {}'.format(gMessage.getLangFile()))
    gMessage.setLang('it')
    gMessage.load()
    print(u'pack it: {}'.format(gMessage.getLangFile()))
    print()
    gMessage.setLang('fr')
    print(u'fr:', message('test'))
    gMessage.setLang('en')
    print(u'en:', message('test'))
    gMessage.setLang('us')
    print(u'us:', message('test'))
    gMessage.setLang('pt')
    print(u'pt:', message('test'))
    gMessage.setLang('de')
    print(u'de:', message('test'))
    gMessage.setLang('it')
    print(u'it:', message('test'))
    gMessage.setLang('ar')
    print(u'ar:', message('test'))
    print()
    gMessage.setLang('fr')
    print(u'fr (unknown message):', message('toto'))
    print(u'fr (accents message):', message('portfolio_exist_info'))
    print()
    import datetime
    gMessage.setLang('fr')
    print(u'6 décembre 2005 en francais ({}) : '.format(gMessage.getLocale()),
          datetime.datetime(2005, 12, 6, 12, 13, 14).strftime(' %x '))
    gMessage.setLang('en')
    print(u'6th december 2005 in english ({}) : '.format(gMessage.getLocale()),
          datetime.datetime(2005, 12, 6, 12, 13, 14).strftime(' %x '))
    gMessage.setLang('pt')
    print(u'6th december 2005 in portuguese ({}) : '.format(gMessage.getLocale()),
          datetime.datetime(2005, 12, 6, 12, 13, 14).strftime(' %x '))
    gMessage.setLang('de')
    print(u'6th december 2005 in deutch ({}) : '.format(gMessage.getLocale()),
          datetime.datetime(2005, 12, 6, 12, 13, 14).strftime(' %x '))
    gMessage.setLang('it')
    print(u'6 dicembre 2005 in italian ({}) : '.format(gMessage.getLocale()),
          datetime.datetime(2005, 12, 6, 12, 13, 14).strftime(' %x '))
    gMessage.setLang()
    print(u'6th december 2005 in default lang ({}) : '.format(gMessage.getLocale()),
          datetime.datetime(2005, 12, 6, 12, 13, 14).strftime(' %x '))


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
