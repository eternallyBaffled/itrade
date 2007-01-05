#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_login_boursorama.py
#
# Description: Login to boursorama service
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
# 2007-01-05    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import re
import os
import mimetypes
import cookielib
import urllib
import urllib2

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_login import *
from itrade_local import message

# ============================================================================
# Login_boursorama()
#
#   login(user,passwd)
#       store cookie after login
#
#   logout()
#       nop
#
# ============================================================================

class Login_boursorama(object):
    def __init__(self):
        debug('LiveUpdate_boursorama:__init__')
        self.m_default_host = "www.boursorama.fr"
        self.m_cookie_url =  "https://www.boursorama.fr/logunique.phtml"
        self.m_login_url   =  "https://www.boursorama.com/connexion.phtml"
        self.m_trader_url = ""
        self.m_logged = False

        debug('Boursorama login (%s) - ready to run' % self.m_default_host)

    # ---[ properties ] ---

    def name(self):
        return 'boursorama'

    def desc(self):
        return message('login_boursorama_desc')

    # ---[ userinfo ] ---
    def saveUserInfo(self,u,p):
        f = open(os.path.join(itrade_config.dirUserData,'boursorama_userinfo.txt'),'w')
        s = u + ',' + p
        f.write(s)
        f.close()

    def loadUserInfo(self):
        try:
            f = open(os.path.join(itrade_config.dirUserData,'boursorama_userinfo.txt'),'r')
        except IOError:
            return None,None
        s = f.read().strip()
        f.close()
        v = s.split(',')
        if len(v)==2:
            return v[0],v[1]
        return None,None

    # ---[ login ] ---

    def login(self,u=None,p=None):
        # load username / password (if required)
        if u==None or p==None:
            u,p = self.loadUserInfo()
            if u==None or p==None:
                print 'login: userinfo are invalid - please reenter Access Information'
                return False
        #print 'log:',u,p

        self.m_logged = False

        # Load Cookie file
        cj = cookielib.LWPCookieJar()
        COOKIEFILE = os.path.join(itrade_config.dirUserData,'boursorama_live.lwp')
        if os.path.isfile(COOKIEFILE):
            cj.load(COOKIEFILE)

        # Opener with cookie management
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(opener)

        headers = {
                    "Connection":"keep-alive",
                    "Accept":"text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2",
                    "Host":self.m_default_host,
                    "User-Agent":"Mozilla/4.0 (Windows XP 5.1) Java/1.5.0_06",
                    "Pragma":"no-cache",
                    "Cache-Control":"no-cache",
                    "Content-Type":"application/x-www-form-urlencoded"
                    }

        # GET COOKIE
        try:
            req = urllib2.Request(self.m_cookie_url,None,headers)
            handle = urllib2.urlopen(req)
        except IOError,e:
            if hasattr(e,'code'):
                print 'Login_fortuneo:POST cookie failure %s - error code %s' % (self.m_cookie_url,e.code)
            elif hasattr(e, 'reason'):
                print 'Login_fortuneo:POST cookie failure %s - reason %s' % (self.m_cookie_url,e.reason)
            else:
                print 'Login_fortuneo:POST cookie failure %s - unknown reason' % (self.m_cookie_url)
            return False

        print 'These are the cookies we have received so far :'
        for index, cookie in enumerate(cj):
            print index, '  :  ', cookie
        cj.save(COOKIEFILE)

        # LOGIN
        params = "login=%s&password=%s&redirect=&org=/index.phtml?\r\n" % (u,p)

        try:
            req = urllib2.Request(self.m_login_url,params,headers)
            handle = urllib2.urlopen(req)
        except IOError,e:
            if hasattr(e,'code'):
                print 'Login_fortuneo:POST login failure %s - error code %s' % (self.m_login_url,e.code)
            elif hasattr(e, 'reason'):
                print 'Login_fortuneo:POST login failure %s - reason %s' % (self.m_login_url,e.reason)
            else:
                print 'Login_fortuneo:POST login failure %s - unknown reason' % (self.m_login_url)
            return False

        buf = handle.read()
        print buf

        cj.save(COOKIEFILE)
        self.m_logged = True

        return True

    def logout(self):
        self.m_logged = False
        return True

    def logged(self):
        return self.m_logged

# ============================================================================
# Export me
# ============================================================================

try:
    ignore(gLoginBoursorama)
except NameError:
    gLoginBoursorama = Login_boursorama()

registerLoginConnector(gLoginBoursorama.name(),gLoginBoursorama)

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    gLoginBoursorama.login('','')
    gLoginBoursorama.logout()

# ============================================================================
# That's all folks !
# ============================================================================
