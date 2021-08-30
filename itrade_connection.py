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
# The Initial Developer of the Original Code is Gilles Dumortier.
#
# Portions created by the Initial Developer are Copyright (C) 2004-2008 the
# Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   Sébastien Renard
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
import string
from gzip import GzipFile
from StringIO import StringIO
from threading import Lock
from urllib import urlencode

# iTrade system
import logging


class ITradeConnection(object):
    """Class designed to handle request in HTTP 1.1"""
    def __init__(self, cookies=None, proxy=None, proxyAuth=None, connectionTimeout=20):
        """@param cookies: cookie handler (instance of ITradeCookies class). If None, a private cookie
        handler is created.
        @param proxy: proxy host name or IP
        @param proxyAuth: authentication string for proxy in the form 'user:password'"""

        if cookies:
            self.m_cookies = cookies
        else:
            # No cookie handler given ? Create a new one private for this connection instance
            self.m_cookies = ITradeCookies()

        self.m_proxy = proxy

        # Set a default socket timeout to 20 second for all further connexions
        socket.setdefaulttimeout(connectionTimeout)

        if proxyAuth:
            self.m_proxyAuth = "".join(("Basic ", base64.encodestring(proxyAuth)))
        else:
            self.m_proxyAuth = None

        self.m_httpConnection = {}   # dict of httplib.HTTPConnection instances (key is host)
        self.m_httpsConnection = {}  # dict of httplib.HTTPSConnection instances (key is host)
        self.m_response = None       # HTTPResponse of last request
        self.m_responseData = ""     # Content of the http response
        self.m_duration = 0          # Duration of last request
        self.m_retrying = False      # Flag to indicate if we are retrying after connection failure
        self.m_locker = Lock()       # Lock to protect httplib strict cycle (get/response) in multithreading
        self.m_defaultHeader = {"acceptEncoding": "gzip, deflate",
                                "accept": "*/*",
                                "userAgent": "Mozilla/5.0 (compatible; iTrade)",
                                "Connection": "Keep-Alive"}  # Default HTTP header

    def getDataFromUrl(self, url, header=None, data=None):
        """Thread safe method to get data from an URL. See put() and getData() method for details"""
        with self.m_locker:
            self.put(url, header, data)
            result = self.getData()
        return result

    def put(self, url, header=None, data=None):
        """Put a request to url with data parameters (for POST request only).
        No data imply GET request
        @param url: a complete url like https://www.somehost.com/somepath/somepage
        @param header: addon headers for connection (optional, default is None)
        @param data: dictionary of parameters for POST (optional, default is None)"""

        # Parse URL
        (protocole, host, page, params, query, fragments) = urlparse.urlparse(url)

        # print "==>", currentThread().getName(), protocole, host, page, params, query, fragments
        try:
            # Prepare new header
            if header:
                next_header = dict(header)
            else:
                next_header = dict(self.m_defaultHeader)

            # Go through proxy if defined
            if self.m_proxy:
                host = self.m_proxy
                request = url
                if self.m_proxyAuth:
                    next_header["Proxy-Authorization"] = self.m_proxyAuth
            else:
                # Http request does not have host value for direct connection
                request = "{}?{}".format(page, query)

            if protocole.lower() == "http":
                if host in self.m_httpConnection:
                    # Reuse already opened connection
                    connection = self.m_httpConnection[host]
                else:
                    # Open a new one and save it
                    connection = httplib.HTTPConnection(host)
                    self.m_httpConnection[host] = connection
            else:
                if host in self.m_httpsConnection:
                    # Reuse already opened connection
                    connection = self.m_httpsConnection[host]
                else:
                    # Open a new one and save it
                    connection = httplib.HTTPSConnection(host)
                    self.m_httpsConnection[host] = connection

            # Add cookie
            if self.m_cookies:
                if self.m_cookies.get():
                    # print "use cookie"
                    next_header["Cookie"] = self.m_cookies.get()

            start = time.time()

            try:
                if data:
                    # Encode data and update header
                    data = urlencode(data)
                    next_header.update({'Content-Length': len(data),
                                        'Content-type': 'application/x-www-form-urlencoded'})
                    connection.request("POST", page, data, next_header)
                else:
                    # print "GET", request, next_header
                    connection.request("GET", request, None, next_header)

                self.response = connection.getresponse()

                if self.response:
                    if self.response.getheader('Content-Encoding') == 'gzip':
                        # print "==>", currentThread().getName(), "gzip response"
                        self.m_responseData = GzipFile(fileobj=StringIO(self.response.read())).read()
                    else:
                        ldata = self.response.getheader('content-length')
                        if ldata:
                            # some servers can return min,max or max,max
                            #  i.e. "http://www.nysedata.com/nysedata/asp/download.asp?s=txt&prod=symbols" is doing that !
                            ldata = string.split(ldata, ',')
                            if ldata and len(ldata) > 1:
                                ldata = int(ldata[0])
                                self.m_responseData = self.response.read(ldata)
                            else:
                                self.m_responseData = self.response.read()
                        else:
                            self.m_responseData = self.response.read()
                else:
                    # print "==>", currentThread().getName(), "empty response"
                    self.m_responseData = ""

                # Follow redirect if any with recursion
                if self.getStatus() in (301, 302):
                    url = urlparse.urljoin(url, self.response.getheader("location", ""))
                    self.put(url, next_header)

                self.m_duration = time.time() - start

                if self.getStatus() != 200:
                    msg = Exception("Receive bad answer from server (code {}) while requesting : {}".format(self.getStatus(), url))
                    # info(msg)
                    self.m_responseData = ""
                    self.clearConnection(protocole, host)
                    raise msg

                # Save cookie string
                for cookieHeader in self.response.msg.getallmatchingheaders("set-cookie"):
                    if cookieHeader and self.m_cookies:
                        if cookieHeader.count(";") >= 1 and cookieHeader.count(":") >= 1:
                            cookie_string = cookieHeader.split(":")[1]
                            cookie_string = cookie_string.split(";")[0]
                            self.m_cookies.set(cookie_string)
                        else:
                            logging.info("Strange cookie header ({}). Ignoring.".format(cookieHeader))

            except socket.timeout:
                msg = Exception("Connexion timeout while requesting the remote server : {}".format(url))
                logging.error(msg)
                self.m_responseData = ""
                self.clearConnection(protocole, host)
                raise msg

            except (socket.gaierror, httplib.CannotSendRequest, httplib.BadStatusLine) as e:
                self.clearConnection(protocole, host)
                if not self.m_retrying:
                    # Retry one time because this kind of error can be "normal"
                    # Eg. after a connection keep-alive timeout
                    # logging.debug("An error occurred while requesting the remote server : {}. Retrying".format(e))
                    self.m_retrying = True
                    self.put(url, header, data)  # Retrying one time
                    self.m_retrying = False
                else:
                    msg = Exception("An error occurred while requesting the remote server : {} (retry fail)".format(e))
                    logging.error(msg)
                    self.m_retrying = False
                    raise msg

        except Exception as e:
            self.clearConnections()  # Clean all connection
            msg = Exception("Unhandled exception on ITrade_Connexion ({})".format(e))
            logging.error(msg)
            raise msg

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
        return self.m_duration

    def clearConnection(self, protocole, host):
        """Clear connexion for given host and protocole
        @param protocole: protocole of connection to be cleared (http or https, not case sensitive)
        @param host: host of connection to be cleared"""
        if protocole.lower() == "http":
            del self.m_httpConnection[host]
        else:
            del self.m_httpsConnection[host]

    def clearConnections(self):
        """Clear all http and https connexion to start up on clean base"""
        logging.debug("Cleaning up http(s) connections")
        self.m_httpConnection = {}
        self.m_httpsConnection = {}

    def setProxy(self, proxy=None, proxy_auth=None):
        """Use the given proxy for connexions. All connexions will be cleared to use proxy at next connextion.
        This method is thread safe with getDataFromUrl()
        @param proxy: proxy hostname (IP:port). None means no proxy. Default is None
        @param proxy_auth: proxy authentication (user:password). None means no authentication. Default is None
        """
        with self.m_locker.acquire():
            self.m_proxy = proxy
            if proxy_auth:
                self.m_proxyAuth = ''.join(("Basic ", base64.encodestring(proxy_auth)))
            else:
                self.m_proxyAuth = None
            self.clearConnections()

    def setConnectionTimeout(self, connection_timeout):
        # Set a default socket timeout to 20 second for all further connexions
        socket.setdefaulttimeout(connection_timeout)


class ITradeCookies(object):
    """Simple cookie repository"""

    def __init__(self):
        self.m_locker = Lock()
        self.m_cookie = ""

    def set(self, cookie_string):
        """Set a new Cookie"""
        with self.m_locker.acquire():
            if self.m_cookie:
                self.m_cookie = '{};{}'.format(self.m_cookie, cookie_string)
            else:
                self.m_cookie = cookie_string
        logging.debug("now cookie is {}".format(self.m_cookie))

    def get(self):
        """get cookie string. If not, empty string is return"""
        return self.m_cookie


def main():
    import itrade_config
    from itrade_logging import setLevel
    setLevel(logging.INFO)
    itrade_config.app_header()


if __name__ == '__main__':
    main()
# ============================================================================
# That's all folks !
# ============================================================================
