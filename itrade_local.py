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
    'fr': "Français",
    'pt': "Portuguese",
    'de': "Deutsch",
    'it': "Italian",
    'en': 'English',
    'us': 'English'
    }

nl_posix = {
    'fr': 'fr_FR',
    'pt': 'pt_PT',
    'de': 'de_DE',
    'it': "it_IT",
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
    'en':   'us'
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
    ll = getLang()
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
    ll = getLang()
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
    ll = getLang()
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
            logging.warning('lang %s already loaded !' % self.m_lang)
            return

        if fn is None:
            fn = os.path.join(itrade_config.dir_sys_data(), '%s.messages.txt'%self.m_lang)
        infile = itrade_csv.read(fn)
        if infile:
            # store filename used for messaging
            self.m_llang[self.m_lang] = fn

            # scan each line to read each trade
            for eachLine in infile:
                item = itrade_csv.parse(eachLine.decode("utf-8"),2)
                if item:
                    self.addMsg(item)

            # info
            print 'Language Pack %s : %s' % (self.m_lang,self.m_llang[self.m_lang])
        else:
            print 'No Language Pack for %s !' % self.m_lang
            #raise('lang %s not found !' % self.m_lang)

    def setLocale(self,lang=None):
        # try to setup the C runtime (_locale)
        if lang is None:
            lang = self.m_lang
            logging.debug('setLocale(): default to %s' % lang)
        else:
            logging.debug('setLocale(): set to %s' % lang)

        if sys.platform == 'darwin':
            # do nothing :-( (locale support on MacOSX is minimal)
            pass
        elif sys.platform.startswith("win"):
            try:
                locale.setlocale(locale.LC_ALL, lang)
            except locale.Error:
                print 'setlocale %s : %s' % (lang,'locale unknown in this windows configuration ?')
        else:
            try:
                locale.setlocale(locale.LC_ALL, nl_posix[lang])
            except locale.Error:
                print 'setlocale %s : %s' % (nl_posix[lang],'locale unknown in this configuration ?')

        # strptime is bugged :
        # first call will reset the TimeRE cache but continue using the previous TimeRE (bad lang) :-( !
        # obhack: call strptime to reset the cache, next call will use the right object
        time.strptime('10','%H')
        # NB: %H will be cached with the bad lang ; it is not important at all because %H is not localized

    def getLocale(self):
        lang,cp = locale.getlocale(locale.LC_ALL)
        return lang

    def setLang(self,l=None):
        if l:
            self.m_lang = self.langSupported(l)
        else:
            # default to french !
            self.m_lang = 'fr'

        # try to setup the C runtime (_locale)
        self.setLocale()

    def getLang(self):
        return self.m_lang

    def getLangFile(self):
        if self.m_lang in self.m_llang:
            return self.m_llang[self.m_lang]
        else:
            return None

    def langSupported(self,l):
        if l in nl_supported:
            if l in nl_convert:
                return nl_convert[l]
            else:
                return l
        else:
            print "setlocale '%s' : unsupported language - default to french" % l
            return 'fr'

    def addMsg(self, m):
        if len(m) != 2:
            # well formed ?
            return
        key = u'%s%s' % (self.m_lang, m[0])
        if key in self.m_msg:
            raise('addMsg:: key %s already exist' % key)
        self.m_msg[key] = m[1]

    def getMsg(self,ref):
        if not self.m_lang:
            # package not initialized :-(
            lang = gMessage.getAutoDetectedLang('us')
            #print 'getMsg: need to setLang :',lang," during ref:",ref
            gMessage.setLang(lang)
        if len(self.m_msg)==0:
            #print 'getMsg: need to load lang pack :',lang
            gMessage.load()

        key = '%s%s' % (self.m_lang,ref)
        if key in self.m_msg:
            return self.m_msg[key]
        else:
            return '?%s:%s?' % (self.m_lang,ref)

    def getAutoDetectedLang(self,dl='us'):
        # set the default locale
        locale.setlocale(locale.LC_ALL,'')
        # get the current locale encoding and codepage
        enc,cp = locale.getlocale()

        # check if encoding known
        if enc in nl_autodetect:
            return nl_autodetect[enc]
        else:
            # return the default lang provided by the caller
            return dl

# ============================================================================
# Install the Local system
# ============================================================================

try:
    ignore(gMessage)
except NameError:
    gMessage = LocalMessages()

message = gMessage.getMsg
msg = gMessage.getMsg
setLang = gMessage.setLang
getLang = gMessage.getLang
setLocale = gMessage.setLocale
getLocale = gMessage.getLocale

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    import itrade_logging

    itrade_logging.setLevel(logging.INFO)

    print 'default (detection): ', gMessage.getAutoDetectedLang()

    setLang('us')
    gMessage.load()
    print 'pack us: %s' % gMessage.getLangFile()
    setLang('fr')
    gMessage.load()
    print 'pack fr: %s' % gMessage.getLangFile()
    setLang('en')
    gMessage.load()
    print 'pack en: %s' % gMessage.getLangFile()
    setLang('pt')
    gMessage.load()
    print 'pack pt: %s' % gMessage.getLangFile()
    setLang('de')
    gMessage.load()
    print 'pack de: %s' % gMessage.getLangFile()
    setLang('it')
    gMessage.load()
    print 'pack it: %s' % gMessage.getLangFile()
    print

    setLang('fr')
    print 'fr:', message('test')
    setLang('en')
    print 'en:', message('test')
    setLang('us')
    print 'us:', message('test')
    setLang('pt')
    print 'pt:', message('test')
    setLang('de')
    print 'de:', message('test')
    setLang('it')
    print 'it:', message('test')
    setLang('ar')
    print 'ar:', message('test')

    print
    setLang('fr')
    print 'fr (unknown message):', message('toto')
    print 'fr (accents message):', message('portfolio_exist_info')

    print
    import datetime
    setLang('fr')
    print '6 décembre 2005 en francais (%s) : ' % getLocale(),datetime.datetime(2005, 12, 6, 12, 13, 14).strftime(' %x ')
    setLang('en')
    print '6th december 2005 in english (%s) : ' % getLocale(),datetime.datetime(2005, 12, 6, 12, 13, 14).strftime(' %x ')
    setLang('pt')
    print '6th december 2005 in portuguese (%s) : ' % getLocale(),datetime.datetime(2005, 12, 6, 12, 13, 14).strftime(' %x ')
    setLang('de')
    print '6th december 2005 in deutch (%s) : ' % getLocale(),datetime.datetime(2005, 12, 6, 12, 13, 14).strftime(' %x ')
    setLang('it')
    print '6 dicembre 2005 in italian (%s) : ' % getLocale(),datetime.datetime(2005, 12, 6, 12, 13, 14).strftime(' %x ')
    setLang()
    print '6th december 2005 in default lang (%s) : ' % getLocale(),datetime.datetime(2005, 12, 6, 12, 13, 14).strftime(' %x ')

# ============================================================================
# That's all folks !
# ============================================================================
