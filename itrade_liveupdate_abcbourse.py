#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_liveupdate_abcbourse.py
# Version      : $Id: itrade_liveupdate_abcbourse.py,v 1.16 2006/01/28 12:27:43 dgil Exp $
#
# Description: Live update quotes from abcbourse.com
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
# 2005-03-25    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Version management
# ============================================================================

__revision__ = "$Id: itrade_liveupdate_abcbourse.py,v 1.16 2006/01/28 12:27:43 dgil Exp $"
__author__ = "Gilles Dumortier (dgil@ieee.org)"
__version__ = "0.4"
__status__ = "alpha"
__cvsversion__ = "$Revision: 1.16 $"[11:-2]
__date__ = "$Date: 2006/01/28 12:27:43 $"[7:-2]
__copyright__ = "Copyright (c) 2004-2006 Gilles Dumortier"
__license__ = "GPL"
__credits__ = """ """

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import re
import thread
import datetime

from urllib import *
from httplib import *

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_quotes import *
from itrade_import import registerLiveConnector

# ============================================================================
# LiveUpdate_ABCBourse()
#
#  abcbourse returns all the quotes then we have to extract only the quote
#  we want to return :-(
#  design idea : if the quote is requested within the same second, use a
#  cached data to extract !
# ============================================================================

class LiveUpdate_ABCBourse(object):
    def __init__(self):
        debug('LiveUpdate_ABCBourse:__init__')
        self.m_host = "download.abcbourse.com"
        self.m_conn = None
        self.m_url = "/telechargement_intraday.aspx"
        self.m_viewstate = None
        self.m_data = None
        self.m_clock = "::"
        self.m_livelock = thread.allocate_lock()

    # ---[ reentrant ] ---
    def acquire(self):
        # not reentrant because of global states : m_viewstate/m_data
        self.m_livelock.acquire()

    def release(self):
        self.m_livelock.release()

    # ---[ properties ] ---

    def name(self):
        return 'abcbourse'

    def delay(self):
        return 15

    # ---[ connexion ] ---

    def connect(self):
        debug('LiveUpdate_ABCBourse:connect to web site')
        try:
            self.m_conn = HTTPConnection(self.m_host,80)
        except:
            debug('LiveUpdate_ABCBourse:unable to connect :-(')
            return False
        return True

    def disconnect(self):
        if self.m_conn:
            self.m_conn.close()
        self.m_conn = None

    def alive(self):
        return self.m_data<>None

    # ---[ state ] ---

    def getstate(self):
        # check we have a connection
        if not self.m_conn:
            raise('LiveUpdate_ABCBourse:no connection')
            return None

        # init headers
        headers = { "Keep-Alive":300, "Accept-Charset:":"ISO-8859-1", "Accept-Language": "en-us,en", "Accept": "text/html,text/plain", "Connection": "keep-alive", "Host": self.m_host }

        # GET the main download page
        try:
            self.m_conn.request("GET", self.m_url, None, headers)
            response = self.m_conn.getresponse()
        except:
            debug('LiveUpdate_ABCBourse:GET failure')
            return None

        debug("status:%s reason:%s" %(response.status, response.reason))
        if response.status != 200:
            debug('LiveUpdate_ABCBourse:status!=200')
            return None

        # search for the ___VIEWSTATE variable
        data = response.read()
        m = re.search('name=\"__VIEWSTATE\"\s*value=\"\S+\"', data)
        if m==None:
            debug('LiveUpdate_ABCBourse:viewstate statement not found !')
            return None

        # extract the variable content
        m = m.group()[26:-1]
        self.m_viewstate = m

        return m

    # ---[ API to get data ] ---

    def getdataByQuote(self,quote):
        if quote:
            return self.getdata(quote)
        return None

    def getdataByTicker(self,ticker):
        quote = quotes.lookupTicker(ticker)
        if quote:
            return self.getdata(quote)
        return None

    def getdataByISIN(self,isin):
        quote = quotes.lookupISIN(isin)
        if quote:
            return self.getdata(quote)
        return None

    # ---[ code to get data ] ---

    def getdata(self,quote):
        # check we have a connection
        if not self.m_conn:
            raise('LiveUpdate_ABCBourse:no connection / missing connect() call !')
            return None
        # check we have a viewstate
        if not self.m_viewstate:
            raise('LiveUpdate_ABCBourse:no viewstate / missing getstate() call !')
            return None

        debug("LiveUpdate_ABCBourse:getdata quote:%s " % quote)

        # init params and headers
        params = urlencode({'f': 'ebp', '__VIEWSTATE': self.m_viewstate, 'm': 'complet', 'ImageButton1.x': 4, 'ImageButton1.y': 13 })
        debug(params)
        headers = { "Keep-Alive":300, "Accept-Charset:":"ISO-8859-1", "Accept-Language": "en-us,en", "Content-type": "application/x-www-form-urlencoded", "Accept": "text/html,text/plain", "Connection": "keep-alive", "Host": self.m_host  }

        # POST the request
        try:
            self.m_conn.request("POST", self.m_url, params, headers)
            response = self.m_conn.getresponse()
        except:
            debug('LiveUpdate_ABCBourse:POST failure')
            return None

        debug("status:%s reason:%s" %(response.status, response.reason))
        if response.status != 200:
            debug('LiveUpdate_ABCBourse:status!=200')
            return None

        # returns the data
        data = response.read()
        self.m_datatime = datetime.today()
        self.m_clock = "%s" % self.m_datatime

        debug('!!! datatime = %s clock=%s' % (self.m_datatime,self.m_clock))

        # detect EBP file then split by line
        if data[:8]!="30111998":
            self.m_data = ""
            return ""
        self.m_data = data[8:].split('\r\n')

        # extract the quote we are looking for
        return self.getcacheddata(quote)

    # ---[ cache management on data ] ---

    def getcacheddataByQuote(self,quote):
        if quote:
            return self.getcacheddata(quote)
        return None

    def getcacheddataByTicker(self,ticker):
        quote = quotes.lookupTicker(ticker)
        if quote:
            return self.getcacheddata(quote)
        return None

    def getcacheddataByISIN(self,isin):
        quote = quotes.lookupISIN(isin)
        if quote:
            return self.getcacheddata(quote)
        return None

    def getcacheddata(self,quote):
        debug('getcacheddata %s' % self.m_data)
        for eachLine in self.m_data:
            item = itrade_csv.parse(eachLine,7)
            if item:
                if (item[0]==quote.isin()):
                    #print item
                    # convert to string format :-(
                    return '%s;%s;%s;%s;%s;%s;%s' % (item[0],item[1],item[2],item[3],item[4],item[5],item[6])
        return ""

    def iscacheddataenoughfreshq(self):
        if self.m_data==None:
            #print
            debug('iscacheddataenoughfreshq : no cache !')
            return False
        if not self.m_datatime:
            debug('iscacheddataenoughfreshq : no data time !')
            return False
        delta = timedelta(0,itrade_config.cachedDataFreshDelay)
        newtime = self.m_datatime + delta
        if (datetime.today()>newtime):
            debug('datatime = %s  currentdatatime = %s  newtime = %s delta = %s : False' %(self.m_datatime,datetime.today(),newtime,delta))
            return False
        debug('datatime = %s  currentdatatime = %s  newtime = %s delta = %s : True' %(self.m_datatime,datetime.today(),newtime,delta))
        return True

    def cacheddatanotfresh(self):
        self.m_data = None

    # ---[ notebook of order ] ---

    def hasNotebook(self):
        return False

    # ---[ status of quote ] ---

    def hasStatus(self):
        return False

    def currentClock(self,quote=None):
        return self.m_clock

# ============================================================================
# Export me
# ============================================================================

try:
    ignore(gLiveABC)
except NameError:
    gLiveABC = LiveUpdate_ABCBourse()

registerLiveConnector('EURONEXT',gLiveABC)
registerLiveConnector('EURONEXT_differed',gLiveABC)

# ============================================================================
# Test ME
#
# ============================================================================

def test(ticker):
    if gLiveABC.iscacheddataenoughfreshq():
        data = gLiveABC.getcacheddataByTicker(ticker)
        if data:
            debug(data)
        else:
            debug("nodata")

    elif gLiveABC.connect():

        state = gLiveABC.getstate()
        if state:
            debug("state=%s" % (state))

            data = gLiveABC.getdataByTicker(ticker)
            if data!=None:
                if data:
                    info(data)
                else:
                    debug("nodata")
            else:
                print "getdata() failure :-("
        else:
            print "getstate() failure :-("

        gLiveABC.disconnect()
    else:
        print "connect() failure :-("

if __name__=='__main__':
    setLevel(logging.INFO)

    print 'live %s' % date.today()
    test('OSI')
    test('EADT')
    gLiveABC.cacheddatanotfresh()
    test('EADT')

# ============================================================================
# That's all folks !
# ============================================================================
# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
