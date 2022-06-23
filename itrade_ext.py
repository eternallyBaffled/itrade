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
# 2007-01-21    dgil  Wrote it from scratch (inspired from leoPlugins.py)
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from __future__ import absolute_import
import logging
import glob
import imp
import os
import sys
from collections import namedtuple

# iTrade system
from itrade_logging import setLevel
import itrade_config
from itrade_market import market2place
from itrade_login import gLoginRegistry
from itrade_defs import QList, QTag

# ============================================================================
# globals
# ============================================================================

loadedModules = {}  # keys are module names, values are modules ref

Connector = namedtuple('Connector', ['market', 'place', 'bDefault', 'connector', 'qlist', 'qtag'])


class ConnectorRegistry(object):
    def __init__(self):
        self.m_conn = []

    def register(self,market,place,qlist,qtag,connector,bDefault=True):
        self.m_conn.append((market,place,bDefault,connector,qlist,qtag))
        #print 'Register %s for market :' % self, market,' qlist:',qlist,' qtag:',qtag
        return True

    def get(self,market,qlist,qtag,place=None,name=None):
        if place is None:
            place = market2place(market)
        if name:
            for amarket,aplace,adefault,aconnector,aqlist,aqtag in self.m_conn:
                #print amarket,aqlist,aqtag,aplace,aconnector.name(),adefault
                if market==amarket and place==aplace and aconnector.name()==name and (aqlist==QList.any or aqlist==qlist) and (qtag==QTag.any or aqtag==qtag):
                    return aconnector
        else:
            for amarket,aplace,adefault,aconnector,aqlist,aqtag in self.m_conn:
                if market==amarket and place==aplace and (aqlist==QList.any or qlist==aqlist) and adefault and (qtag==QTag.any or aqtag==qtag):
                    return aconnector
        return None

    def list(self, market, qlist, place):
        lst = []
        for amarket,aplace,adefault,aconnector,aqlist,aqtag in self.m_conn:
            if amarket==market and aplace==place and (aqlist==QList.any or aqlist==qlist):
                lst.append((aconnector.name(),amarket,aplace,adefault,aconnector,aqlist,aqtag))
        return lst

# ============================================================================
# Export Live and Import Registries
# ============================================================================


gLiveRegistry = ConnectorRegistry()


def getDefaultLiveConnector(market, lst, place=None):
    # try live connector
    ret = gLiveRegistry.get(market, lst, QTag.live, place)
    if ret:
        # check live connector is logged
        if gLoginRegistry.logged(ret.name()):
            return ret

    # no live connector or not logged : fall-back to differed connector
    ret = gLiveRegistry.get(market, lst, QTag.differed, place)
    if ret is None:
        print(u'No default connector {} for market :'.format(market),' qlist:', lst)
    return ret


gImportRegistry = ConnectorRegistry()

# ============================================================================
# Export ListSymbol Registry
# ============================================================================


gListSymbolRegistry = ConnectorRegistry()

# ============================================================================
# loadExtensions()
#
# load all enabled extensions from the extension folder
#
#   file:   name of the file to manage the extension
#   folder: path of the folder to load the extension from
# ============================================================================


def loadExtensions(file, folder):
    # file to manage list of extensions
    extFile = os.path.join(folder, file)
    if not os.path.exists(extFile):
        print(u'Load ({}) : {} file not found !'.format(folder, file))
        return False

    # list of potential files to load
    files = glob.glob(os.path.join(folder, '*.py'))
    if not files:
        print(u'Load ({}) : no extension file found !'.format(folder))
        return False

    # list of enabled / disabled Files
    enabledFiles = []
    disabledFiles = []
    lines = []

    try:
        with open(extFile) as ext:
            lines = ext.readlines()
    except IOError:
        print(u"Load ({}) : can't open {} file !".format(folder, extFile))

    for s in lines:
        s = s.strip()
        if s and s[0] == '#':
            s = s[1:].strip()
            if s and s.find(' ') == -1 and s[-3:] == '.py':
                # file commented -> disabled
                path = os.path.join(folder,s)
                if path not in enabledFiles and path not in disabledFiles:
                    disabledFiles.append(path)
        else:
            if s and s.find(' ') == -1 and s[-3:] == '.py':
                path = os.path.join(folder,s)
                if path not in enabledFiles and path not in disabledFiles:
                    #print 'add:',path
                    enabledFiles.append(path)

    # load extensions in the order they appear in the enabledFiles list
    if files and enabledFiles:
        file_set = set(files)
        for f in enabledFiles:
            if f in file_set:
                loadOneExtension(f, folder)
    return True


def loadOneExtension(ext, folder):
    global loadedModules

    # extract module name
    if ext[-3:] == ".py":
        moduleName = ext[:-3]
    else:
        moduleName = ext
    moduleName = os.path.basename(moduleName)

    # check module not loaded
    if isLoaded(moduleName):
        module = loadedModules.get(moduleName)
        print(u'Extension ({}) {} already loaded'.format(folder, moduleName))
        return module

    # import the module
    module = importFromPath(moduleName, folder)

    # return the module reference
    if not module:
        print(u"Can't load ({}) {}".format(folder, moduleName))
    else:
        if itrade_config.verbose:
            print(u'Load ({}) {}'.format(folder, moduleName))
    return module


def isLoaded(name):
    return name in loadedModules


def importFromPath(module_name, path):
    module = sys.modules.get(module_name)
    if not module:
        f = None

        # find the module
        data = imp.find_module(module_name, [path])
        if data:
            # import the module
            f, path, desc = data

            module = imp.load_module(module_name, f, path, desc)
            if module:
                loadedModules[module_name] = module
        if f:
            f.close()
    return module

# ============================================================================
# Test Extensions
# ============================================================================

def main():
    setLevel(logging.INFO)
    itrade_config.app_header()
    loadExtensions(itrade_config.fileExtData, itrade_config.dirExtData)
    loadExtensions(itrade_config.fileIndData, itrade_config.dirIndData)


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
