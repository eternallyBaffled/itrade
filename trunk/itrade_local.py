#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
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

# iTrade system
from itrade_logging import *
import itrade_csv

# ============================================================================
# Supported languages
# ============================================================================

nl_supported = {
    'fr': "Français",
    'en': 'English',
    'us': 'English'
    }

nl_posix = {
    'fr': 'fr_FR',
    'en': 'en_US',
    'us': 'en_US'
    }

nl_autodetect = {
    'fr_FR': 'fr',
    'en_US': 'en',
    'English_United States': 'en'
    }

nl_convert = {
    'en':   'us'
    }

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

    def load(self,fn=None):
        if self.m_llang.has_key(self.m_lang):
            warning('lang %s already loaded !' % self.m_lang)
            return

        infile = itrade_csv.read(fn,os.path.join(itrade_config.dirSysData,'%s.messages.txt'%self.m_lang))
        if infile:
            # store filename used for messaging
            if fn:
                self.m_llang[self.m_lang] = fn
            else:
                self.m_llang[self.m_lang] = os.path.join(itrade_config.dirSysData,'%s.messages.txt'%self.m_lang)

            # scan each line to read each trade
            for eachLine in infile:
                item = itrade_csv.parse(eachLine,2)
                if item:
                    self.addMsg(item)

            # info
            print 'Language Pack %s : %s' % (self.m_lang,self.m_llang[self.m_lang])
        else:
            print 'No Language Pack for %s !' % self.m_lang
            raise('lang %s not found !' % self.m_lang)

    def setLocale(self,lang=None):
        # try to setup the C runtime (_locale)
        if lang==None:
            lang = self.m_lang
            info('setLocale(): default to %s' % lang)
        else:
            info('setLocale(): set to %s' % lang)

        if sys.platform == 'darwin':
            # do nothing :-( (locale support on MacOSX is minimal)
            pass
        elif sys.platform.startswith("win"):
            try:
                locale.setlocale(locale.LC_ALL, lang)
            except locale.Error:
                print 'setlocale %s : %s' % (lang,'')
        else:
            try:
                locale.setlocale(locale.LC_ALL, nl_posix[lang])
            except locale.Error:
                print 'setlocale %s : %s' % (nl_posix[lang],'')

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
        if self.m_llang.has_key(self.m_lang):
            return self.m_llang[self.m_lang]
        else:
            return None

    def langSupported(self,l):
        if nl_supported.has_key(l):
            if nl_convert.has_key(l):
                return nl_convert[l]
            else:
                return l
        else:
            print "setlocale '%s' : unsupported language - default to french" % l
            return 'fr'

    def getLangDesc(self):
        if self.isLangSupported(l):
            return nl_supported[l]
        else:
            return '? %s' % self.m_lang

    def addMsg(self,m):
        if len(m)<>2:
            # well formed ?
            return
        key = '%s%s' % (self.m_lang,m[0])
        if self.m_msg.has_key(key):
            raise('addMsg:: key %s already exist' % key)
        self.m_msg[key] = m[1]

    def getMsg(self,ref):
        if not self.m_lang:
            # package not initialized :-(
            lang = gMessage.getAutoDetectedLang('us')
            gMessage.setLang(lang)
        if len(self.m_msg)==0:
            gMessage.load()

        key = '%s%s' % (self.m_lang,ref)
        if self.m_msg.has_key(key):
            return self.m_msg[key]
        else:
            return '?%s:%s?' % (self.m_lang,ref)

    def getAutoDetectedLang(self,dl='us'):
        # set the default locale
        locale.setlocale(locale.LC_ALL,'')
        # get the current locale encoding and codepage
        enc,cp = locale.getlocale(locale.LC_ALL)

        # check if encoding known
        if nl_autodetect.has_key(enc):
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
getLangDesc = gMessage.getLangDesc
setLocale = gMessage.setLocale
getLocale = gMessage.getLocale

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    print 'default (detection): ',gMessage.getAutoDetectedLang()

    setLang('us')
    gMessage.load()
    print 'pack us: %s' % gMessage.getLangFile()
    setLang('fr')
    gMessage.load()
    print 'pack fr: %s' % gMessage.getLangFile()
    setLang('en')
    gMessage.load()
    print 'pack en: %s' % gMessage.getLangFile()
    print

    setLang('fr')
    print 'fr:', message('test')
    setLang('en')
    print 'en:', message('test')
    setLang('us')
    print 'us:', message('test')
    setLang('ar')
    print 'ar:', message('test')

    print
    setLang('fr')
    print 'fr (unknown message):', message('toto')

    print
    setLang('fr')
    print getLocale()
    setLang('en')
    print getLocale()

# ============================================================================
# That's all folks !
# ============================================================================
# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
