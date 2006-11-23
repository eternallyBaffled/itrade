#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_alerts.py
#
# Description: Alerts back-end
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
# 2005-10-20    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from datetime import *
import logging
import time

# iTrade system
from itrade_logging import *
from itrade_local import message
import itrade_csv

# ============================================================================
# Alert type
# ============================================================================

ALERT_TYPE_INFO_QUOTE = 0
ALERT_TYPE_INFO_SRD = 1

alert_type_desc = {
    ALERT_TYPE_INFO_QUOTE : 'alert_type_info_quote',
    ALERT_TYPE_INFO_SRD : 'alert_type_info_srd'
    }

# ============================================================================
# Alert state
# ============================================================================

ALERT_STATE_UNREAD = 0
ALERT_STATE_READ = 1
ALERT_STATE_ACKNOLEDGE = 2
ALERT_STATE_ARCHIVE = 3

# ============================================================================
# Alert
# ============================================================================

class Alert(object):
    def __init__(self,type,source,datation,title,desc,link,isin):
        self.m_type = type
        self.m_source = source
        self.m_datation = date(long(datation[0:4]),long(datation[5:7]),long(datation[8:10]))
        self.m_title = title
        self.m_desc = desc
        self.m_link = link
        self.m_isin = isin
        self.m_state = ALERT_STATE_UNREAD

    # ---[ properties ] -----------------------------------

    def reference(self):
        return '%d.%s.%s.%s."%s"' % (self.m_type, self.m_source, self.m_datation.strftime('%Y-%m-%d'), self.m_isin, self.m_title)

    def __repr__(self):
        return '%d;%s' % (self.m_state,self.reference())

    def desc(self):
        return self.m_desc

    def link(self):
        return self.m_link

    def source(self):
        return self.m_source

    def type(self):
        return self.m_type

    def type_desc(self):
        return message(alert_type_desc[self.m_type])

    def date(self):
        return self.m_datation

    def title(self):
        return self.m_title

    def isin(self):
        return self.m_isin

    # ---[ state ] ----------------------------------------

    def getstate(self):
        return self.m_state

    def setstate(self,state):
        self.m_state = state
        return self.m_state

# ============================================================================
# Alerts
#
# List of Alert object with filtering capabilities
#
# File format:
#   <ref>;<state>
# ============================================================================

class Alerts(object):
    def __init__(self):
        self._init_()

    def _init_(self):
        self.m_alerts = {}
        self.m_plugins = {}
        self.m_dirty = False

    def dirty(self):
        return self.m_dirty

    # ---[ alert ] ----------------------------------------

    def listAlerts(self):
        return self.m_alerts.values()

    def existAlert(self,ref):
        if self.m_alerts.has_key(ref):
            return self.m_alerts[ref]
        else:
            return None

    def newAlert(self,type,source,datation,title,desc,link,isin):
        alert = Alert(type,source,datation,title,desc,link,isin)
        ref = alert.reference()
        if self.existAlert(ref):
            return None
        else:
            self.m_alerts[ref] = alert
            self.m_dirty = True
            return alert

    def delAlert(self,ref):
        if self.existAlert(ref):
            del self.m_alerts[ref]
            self.m_dirty = True
            return True
        else:
            return False

    # ---[ file ] -----------------------------------------

    def saveFile(self,ref,ext,content):
        pass

    def readFile(self,ref,ext):
        fn = os.path.join(itrade_config.dirAlerts,'%s.%s' % (ref,ext))
        if os.path.exists(fn):
            try:
                f = open(fn,'r')
                txt = f.read()
            except IOError:
                return None
        else:
            return None
        return txt

    def addAlert(self,ref,state):
        if self.existAlert(ref):
            # known :-(
            info('Alerts::addAlert(): ref=%s already exists !' % (ref))
            return False
        else:
            # parse ref
            item = ref.split('.')
            if len(item)!=5:
                info('Alerts::addAlert(): ref=%s already exists !' % (ref))
                return False

            type,source,datation,isin,title = item
            type = int(type)
            title = title.strip('"')

            # read link & desc
            link = self.readFile(ref,'lnk')
            desc = self.readFile(ref,'txt')

            #print 'addAlert:',type,source,datation,isin,title

            # create alert
            alert = self.newAlert(type,source,datation,title,desc,link,isin)
            if alert:
                alert.setstate(state)

                # everything good
                return True
            else:
                # humm :-(
                return False

    def load(self,fn=None):
        # open and read the file to load these alerts information
        infile = itrade_csv.read(fn,os.path.join(itrade_config.dirUserData,'alerts.txt'))
        if infile:
            # scan each line to read each alert
            for eachLine in infile:
                item = itrade_csv.parse(eachLine,2)
                if item:
                    self.addAlert(item[1],int(item[0]))

    def save(self,fn=None):
        # open and write the file with these alerts information
        itrade_csv.write(fn,os.path.join(itrade_config.dirUserData,'alerts.txt'),self.m_alerts.values())

        for eachAlert in self.listAlerts():
            ref = eachAlert.reference()
            self.saveFile(ref,'lnk',eachAlert.link())
            self.saveFile(ref,'txt',eachAlert.desc())

        self.m_dirty = False

    # ---[ plugins ] ---------------------------------------

    def listPlugins(self):
        return self.m_plugins.values()

    def register(self,name,plugin):
        if self.m_plugins.has_key(name):
            warning("Alerts: can't register %s:%s : already registered !" % (name,plugin))
            return False
        self.m_plugins[name] = plugin
        debug('Alerts: register %s:%s : ok' % (name,plugin))
        return True

    def numOfPlugins(self):
        return len(self.m_plugins)

    # ---[ scan ] ------------------------------------------

    def scan(self,dlg=None):
        x = 0
        print 'Alerts: scan %d:%s' % (self.numOfPlugins(),self.listPlugins())

        for eachPlugin in self.listPlugins():
            print 'Alerts: scan %d' % x
            eachPlugin.scan(dlg,x)
            x = x + 1

    # ---[ filters ] ---------------------------------------

# ============================================================================
# Export singleton
# ============================================================================

try:
    ignore(alerts)
except NameError:
    alerts = Alerts()

registerAlertPlugin = alerts.register
newAlert = alerts.newAlert

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    alerts.load()
    alerts.newAlert(ALERT_TYPE_INFO_QUOTE,"boursorama","2006-02-12","Info sur FR0000044380","","","FR0000044380")
    alerts.save()

# ============================================================================
# That's all folks !
# ============================================================================
