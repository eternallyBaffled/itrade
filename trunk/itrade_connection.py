#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_connection.py
#
# Description: http connection handling
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is    Gilles Dumortier.
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
# History       Rev      Description
# 2007-04-15    srenard  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import base64
import httplib
import urlparse
import socket
import time
from gzip import GzipFile
from StringIO import StringIO
from threading import Lock, currentThread

# iTrade system
from itrade_logging import *


# ============================================================================
# ITradeConnection()
# ============================================================================

class ITradeConnection(object):
    """Class designed to handle request in HTTP 1.1"""
    def __init__(self, cookies=None, proxy=None, proxyAuth=None):
        """@param cookies: cookie handler (instance of ITradeCookies class)
        @param proxy: proxy host name or IP
        @param proxyAuth: authentication string for proxy in the form 'user:password'"""

        self.m_cookies=cookies     
        self.m_proxy=proxy

        if proxyAuth:
            self.m_proxyAuth="Basic "+base64.encodestring("username:password")
        else:
            self.m_proxyAuth=None

        self.m_httpConnection={}   # dict of httplib.HTTPConnection instances (key is host)
        self.m_httpsConnection={}  # dict of httplib.HTTPSConnection instances (key is host)
        self.m_response=None       # HTTPResponse of last request
        self.m_responseData=""     # Content of the http response
        self.m_duration=0          # Duration of last request
        self.m_locker=Lock()       # Lock to protect httplib strict cycle (get/response) in multithreading
        self.m_defaultHeader={"acceptEncoding":"gzip, deflate",
                              "accept":"*/*",
                              "userAgent":"Mozilla/5.0 (compatible; iTrade)",
                              "Connection":"Keep-Alive"} # Default HTTP header
    
    def getDataFromUrl(self, url, header=None, data=None):
        """Thread safe method to get data from an URL. See put() and getData() method for details"""
        self.m_locker.acquire()
        try:
            self.put(url, header, data)
            result=self.getData()
        finally:
            self.m_locker.release()
        return result
        
    def put(self, url, header=None, data=None):
        """Put a request to url with data parameters (for POST request only).
        No data imply GET request
        @param url: a complete url like http://www.somehost.com/somepath/somepage
        @param header: addon headers for connection (optional, default is None)
        @param data: dictionary of parameters for POST (optional, default is None)"""
        
        
        # Parse URL
        (protocole, host, page, params, query, fragments)=urlparse.urlparse(url)

        debug("=====> getting %s from thread %s" % (url, currentThread().getName()))

        try:
            # Prepare new header
            nextHeader={}
            if header:
                nextHeader=dict(header)
            else:
                nextHeader=dict(self.m_defaultHeader)
            
            # Go through proxy if defined
            if self.m_proxy:
                host=self.m_proxy
                request=url
                if self.m_proxyAuth:
                    nextHeader["Proxy-Authorization"]=self.m_proxyAuth
            else:
                # Http request does not have host value for direct connection
                request="%s?%s" % (page, query)

            if protocole.lower()=="http":
                if self.m_httpConnection.has_key(host):
                    # Reuse already opened connection
                    connection=self.m_httpConnection[host]
                else:
                    # Open a new one and save it
                    connection=httplib.HTTPConnection(host)
                    self.m_httpConnection[host]=connection
            else:
                if self.m_httpsConnection.has_key(host):
                    # Reuse already opened connection
                    connection=self.m_httpsConnection[host]
                else:
                    # Open a new one and save it
                    connection=httplib.HTTPSConnection(host)
                    self.m_httpsConnection[host]=connection
    
            # Add cookie
            if self.m_cookies:
                nextHeader["Cookie"]=self.m_cookies.get()
    
            start=time.time()
    
            try:
                if data:
                    # Not tested
                    nextHeader.update({'Content-Length' : len(data), 
                                       'Content-type' : 'application/x-www-form-urlencoded'})
                    connection.request("POST", page, data, nextHeader)
                else:
                    connection.request("GET", request, None, nextHeader)
    
                self.response=connection.getresponse()
                if self.response:
                    if self.response.getheader('Content-Encoding') == 'gzip':
                        self.m_responseData=GzipFile(fileobj=StringIO(self.response.read())).read()
                    else:
                        debug("=========> non gzip response")
                        self.m_responseData=self.response.read()
                else:
                    self.m_responseData=""
                debug("========> reponse code : %s" % self.getStatus())
                #print "======= >response : %s" % self.m_responseData
    
                # Follow redirect if any with recursion
                if self.getStatus() in (301, 302):
                    url=urlparse.urljoin(url, self.response.getheader("location", ""))
                    self.put(url, nextHeader)
    
                self.duration=time.time()-start
    
                #Save cookie string
                cookieHeader=self.response.getheader('Set-Cookie')
                if  cookieHeader and self.m_cookies:
                    if cookieHeader.count(";")>=1:
                        cookieString=self.response.getheader('Set-Cookie').split(";")[0]
                        self.m_cookies.set(cookieString)
                    else:
                        debug("Strange cookie header (%s). Ignoring." % cookieHeader)
            except (socket.gaierror,httplib.CannotSendRequest) , e:
                exception("An error occurend while requesting the remote server : %s" % e)
        except Exception, e:
            exception("Unhandled exception on ITrade_Connexion (%s)" % e)

    def getData(self):
        """@return:  page source code (gunzip if needed) or binary data as a str"""
        return self.m_responseData
    
    def getStatus(self):
        """@return:  http status code of last request"""
        if self.response:
            return self.response.status
        else:
            return 0

    def getDuration(self):
        """@return:  last request duration in seconds"""
        return self.duration

# ============================================================================
# ITradeCookies
# ============================================================================

class ITradeCookies:
    """Simple cookie repository"""
    
    def __init__(self):
        self.m_locker=Lock()
        self.m_cookie=""
        
    def set(self, cookieString):
        """Set a new Cookie"""
        self.m_locker.acquire()
        try:
            if self.cookie:
                self.cookie='%s;%s' % (self.cookie, cookieString)
            else:
                self.cookie=cookieString
        finally:
            print "now cookie is %s" % self.cookie
            self.m_locker.release()
    
    def get(self):
        """get cookie string. If not, empty string is return"""
        return self.cookie

# ============================================================================
# That's all folks !
# ============================================================================
