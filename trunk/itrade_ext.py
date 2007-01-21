#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_ext.py
#
# Description: Extensions and Plugins
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
# 2007-01-21    dgil  Wrote it from scratch (inspired from leoPlugins.py)
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import glob
import os
import re
import imp

# iTrade system
from itrade_logging import *
import itrade_config
from itrade_market import market2place

# ============================================================================
# globals
# ============================================================================

loadedModules = {}  # keys are module names, values are modules ref

# ============================================================================
# LIST
# ============================================================================

QLIST_ALL      = 0
QLIST_ANY      = 0
QLIST_SYSTEM   = 1
QLIST_USER     = 2
QLIST_INDICES  = 3
QLIST_TRACKERS = 4

# ============================================================================
# TAG : Kind Of Service
# ============================================================================

QTAG_ANY = 0
QTAG_LIVE = 1
QTAG_DIFFERED = 2
QTAG_IMPORT = 3
QTAG_LIST = 4

# ============================================================================
# ConnectorRegistry
# ============================================================================

class ConnectorRegistry(object):
    def __init__(self):
        self.m_conn = []

    def register(self,market,place,qlist,qtag,connector,bDefault=True):
        self.m_conn.append((market,place,bDefault,connector,qlist,qtag))
        #print 'Register %s for market :' % self, market,' qlist:',qlist,' qtag:',qtag
        return True

    def get(self,market,qlist,qtag,place=None,name=None):
        if place==None:
            place = market2place(market)
        if name:
            for amarket,aplace,adefault,aconnector,aqlist,aqtag in self.m_conn:
                #print amarket,aqlist,aqtag,aplace,aconnector.name(),adefault
                if market==amarket and place==aplace and aconnector.name()==name and (aqlist==QLIST_ANY or aqlist==qlist) and (qtag==QTAG_ANY or aqtag==qtag):
                    return aconnector
        else:
            for amarket,aplace,adefault,aconnector,aqlist,aqtag in self.m_conn:
                if market==amarket and place==aplace and (aqlist==QLIST_ANY or qlist==aqlist) and adefault and (qtag==QTAG_ANY or aqtag==qtag):
                    return aconnector
        return None

    def list(self,market,qlist,place):
        lst = []
        for amarket,aplace,adefault,aconnector,aqlist,aqtag in self.m_conn:
            if amarket==market and aplace==place and (aqlist==QLIST_ANY or aqlist==qlist):
                lst.append((aconnector.name(),amarket,aplace,adefault,aconnector,aqlist,aqtag))
        return lst

# ============================================================================
# Export Live and Import Registries
# ============================================================================

try:
    ignore(gLiveRegistry)
except NameError:
    gLiveRegistry = ConnectorRegistry()

registerLiveConnector = gLiveRegistry.register
getLiveConnector = gLiveRegistry.get
listLiveConnector = gLiveRegistry.list

def getDefaultLiveConnector(market,list,place=None):
    if itrade_config.isDiffered():
        # force differed connector
        ret = getLiveConnector(market,list,QTAG_DIFFERED,place)
    else:
        # try live connector
        ret = getLiveConnector(market,list,QTAG_LIVE,place)
        if ret==None:
            # no live connector : fall-back to differed connector
            ret = getLiveConnector(market,list,QTAG_DIFFERED,place)
    if ret==None:
        print 'No default connector %s for market :' % self,market,' qlist:',qlist
    return ret

try:
    ignore(gImportRegistry)
except NameError:
    gImportRegistry = ConnectorRegistry()

registerImportConnector = gImportRegistry.register
getImportConnector = gImportRegistry.get
listImportConnector = gImportRegistry.list

# ============================================================================
# Export ListSymbol Registry
# ============================================================================

try:
    ignore(gListSymbolRegistry)
except NameError:
    gListSymbolRegistry = ConnectorRegistry()

registerListSymbolConnector = gListSymbolRegistry.register
getListSymbolConnector = gListSymbolRegistry.get
listListSymbolConnector = gListSymbolRegistry.list

# ============================================================================
# loadExtensions()
#
# load all enabled extensions from the extension folder
# ============================================================================

def loadExtensions():

    # file to manage list of extensions
    extFile = os.path.join(itrade_config.dirExtData,"extensions.txt")
    if not os.path.exists(extFile):
        print 'Load extensions: extensions.txt file not found !'
        return False

    # list of potential files to load
    files = glob.glob(os.path.join(itrade_config.dirExtData,"*.py"))
    if not files:
        print 'Load extensions: no extension file found !'
        return False

    # list of enabled / disabled Files
    enabledFiles = []
    disabledFiles = []

    try:
        ext = open(extFile)
        lines = ext.readlines()
        ext.close()
    except IOError:
        print "Load extensions: can't open %s file !" % extFile

    for s in lines:
        #print s
        s = s.strip()
        if s and s[0] == '#':
            s = s[1:].strip()
            if s and s.find(' ') == -1 and s[-3:] == '.py':
                # file commented -> disabled
                path = os.path.join(itrade_config.dirExtData,s)
                if path not in enabledFiles and path not in disabledFiles:
                    disabledFiles.append(path)
        else:
            if s and s.find(' ') == -1 and s[-3:] == '.py':
                path = os.path.join(itrade_config.dirExtData,s)
                if path not in enabledFiles and path not in disabledFiles:
                    #print 'add:',path
                    enabledFiles.append(path)

    # load extensions in the order they appear in the enabledFiles list
    if files and enabledFiles:
        for f in enabledFiles:
            if f in files:
                loadOneExtension(f)

    return True

def loadOneExtension(ext):

    global loadedModules,loadingModuleNameStack

    # extract module name
    if ext[-3:] == ".py":
        moduleName = ext[:-3]
    else:
        moduleName = ext
    moduleName = os.path.basename(moduleName)

    # check module not loaded
    if isLoaded(moduleName):
        module = loadedModules.get(moduleName)
        print 'Extension %s already loaded' % moduleName
        return module

    # import the module
    module = importFromPath (moduleName,itrade_config.dirExtData)

    # return the moduler reference
    if not module:
        print "Can't load %s" % moduleName
    else:
        print 'Load %s' % moduleName

    return module

def isLoaded (name):
    return name in loadedModules

def importFromPath(moduleName,path):

    module = sys.modules.get(moduleName)
    if not module:
        #
        f = None

        # find the module
        data = imp.find_module(moduleName,[path])
        if data:
            # import the module
            f,path,desc = data
            module = imp.load_module(moduleName,f,path,desc)
            if module:
                loadedModules[moduleName] = module

        if f: f.close()

    return module

# ============================================================================
# Test Extensions
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    loadExtensions()

# ============================================================================
# That's all folks !
# ============================================================================