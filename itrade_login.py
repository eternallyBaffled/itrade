#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_login.py
#
# Description: Login to services
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
# 2006-12-31    dgil  Wrote it from scratch
# ============================================================================


class LoginRegistry(object):
    def __init__(self):
        self.m_log = []

    def register(self, name, connector):
        self.m_log.append((name, connector))
        return True

    def get(self, name):
        for aname, aconnector in self.m_log:
            if name == aname:
                return aconnector
        return None

    def list(self, name=None):
        lst = []
        for aname, aconnector in self.m_log:
            if name is None or (name == aname):
                lst.append((aconnector.name(), aconnector))
        return lst

    def logged(self, name):
        con = self.get(name)
        if con:
            return con.logged()
        else:
            # connector not found : no need to log !
            return True


# ============================================================================
# Export Login Registry
# ============================================================================
gLoginRegistry = LoginRegistry()

registerLoginConnector = gLoginRegistry.register
getLoginConnector = gLoginRegistry.get
listLoginConnector = gLoginRegistry.list
loggedLoginConnector = gLoginRegistry.logged

# ============================================================================
# That's all folks !
# ============================================================================
