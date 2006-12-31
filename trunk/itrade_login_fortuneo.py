#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_login_fortuneo.py
#
# Description: Login to fortuneo service
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
# 2006-12-31    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
#import re
#import string
#import thread
#import datetime
#import os
#import socket
import httplib
import mimetypes

# iTrade system
#import itrade_config
from itrade_logging import *
#from itrade_quotes import *
from itrade_login import *

# ============================================================================
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/146306/index_txt
# ============================================================================

def post_multipart(host, selector, fields, files):
    """
    Post fields and files to an http host as multipart/form-data.
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return the server's response page.
    """
    content_type, body = encode_multipart_formdata(fields, files)
    h = httplib.HTTP(host)
    h.putrequest('POST', selector)
    h.putheader('content-type', content_type)
    h.putheader('content-length', str(len(body)))
    h.endheaders()
    h.send(body)
    errcode, errmsg, headers = h.getreply()
    print errcode, errmsg, headers
    return h.file.read()

def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

# ============================================================================
# Login_fortuneo()
#
# ============================================================================

class Login_fortuneo(object):
    def __init__(self):
        debug('LiveUpdate_fortuneo:__init__')
        self.m_default_host = "www.fortuneo.fr"
        self.m_default_url = "/cgi-bin/webact/WebBank/scripts/FRT5.2/loginFRT.jsp"
        self.m_logged = False

        debug('Fortuneo login (%s) - ready to run' % self.m_default_host)

    # ---[ properties ] ---

    def name(self):
        return 'fortuneo'

    # ---[ login ] ---

    def login(self,user,passwd):
        self.m_conn = httplib.HTTPSConnection(self.m_default_host,443)
        if self.m_conn == None:
            print 'login: not connected on %s' % self.m_default_host
            return False

        self.m_logged = False

        params = "sourceB2B=FTO&username=%s&password=%s&pageAccueil=synthese\r\n" % (user,passwd)

        headers = {
                    "Connection":"keep-alive",
                    "Accept":"text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2",
                    "Host":self.m_default_host,
                    "User-Agent":"Mozilla/4.0 (Windows XP 5.1) Java/1.5.0_06",
                    "Pragma":"no-cache",
                    "Cache-Control":"no-cache",
                    "Content-Type":"application/x-www-form-urlencoded"
                    }


        # POST quote request
        try:
            self.m_conn.request("POST", self.m_default_url, params, headers)
            flux = self.m_conn.getresponse()
        except:
            info('Login_fortuneo:POST failure')
            return None

        if flux.status != 200:
            info('Login_fortuneo: status==%d!=200 reason:%s' % (flux.status,flux.reason))
            return None

        print flux.read()
        # __x OK ! GOOD ! BV_SessionID and BV_EngineID could be extracted

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
    ignore(gLoginFortuneo)
except NameError:
    gLoginFortuneo = Login_fortuneo()

registerLoginConnector(gLoginFortuneo.name(),gLoginFortuneo)

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    gLoginFortuneo.login('DEMO6C23NH6','e109')
    gLoginFortuneo.logout()

# ============================================================================
# That's all folks !
# ============================================================================
