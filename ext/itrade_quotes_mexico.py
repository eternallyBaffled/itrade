#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_mexico.py
#
# Description: List of quotes from http://www.bmv.com.mx
#
# Developed for iTrade code (http://itrade.sourceforge.net).
#
# Original template for "plug-in" to iTrade is	from Gilles Dumortier.
# New code for BMV is from Michel Legrand.

# Portions created by the Initial Developer are Copyright (C) 2007-2008 the
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
# 2007-12-28    dgil  Wrote it from template
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import print_function
from __future__ import absolute_import
import logging
import six.moves.http_client
import six.moves.urllib.request, six.moves.urllib.error, six.moves.urllib.parse
import six.moves.http_cookiejar

# iTrade system
import itrade_config
from itrade_logging import setLevel, debug
from itrade_defs import QList, QTag
from itrade_ext import gListSymbolRegistry
from itrade_connection import ITradeConnection
from six.moves import range

# ============================================================================
# Import_ListOfQuotes_MEX()
# ============================================================================
def removeCarriage(s):
    if s[-1] == '\r':
        return s[:-1]
    else:
        return s


def splitLines(buf):
    lines = buf.split('\n')
    lines = [x for x in lines if x]

    lines = [removeCarriage(l) for l in lines]
    return lines


def Import_ListOfQuotes_MEX(quotes, market='MEXICO EXCHANGE', dlg=None, x=0):
    print(u'Update {} list of symbols'.format(market))
    connection = ITradeConnection(proxy=itrade_config.proxyHostname,
                                  proxyAuth=itrade_config.proxyAuthentication)

    if market == 'MEXICO EXCHANGE':
        url = 'https://www.bmv.com.mx/wb3/wb/BMV/BMV_busqueda_de_valores/_rid/222/_mto/3/_url/BMVAPP/componenteSelectorInput.jsf?st=1'
    else:
        return False

    try:
        data = connection.getDataFromUrl(url)
    except Exception:
        debug('Import_ListOfQuotes_MEX unable to connect :-(')
        return False

    cj = None

    urlopen = six.moves.urllib.request.urlopen
    Request = six.moves.urllib.request.Request
    cj = six.moves.http_cookiejar.LWPCookieJar()
    opener = six.moves.urllib.request.build_opener(six.moves.urllib.request.HTTPCookieProcessor(cj))
    six.moves.urllib.request.install_opener(opener)

    url = 'https://www.bmv.com.mx/wb3/wb/BMV/BMV_busqueda_de_valores/_rid/222/_mto/3/_url/BMVAPP/componenteSelectorInput.jsf?st=1'

    req = Request(url)
    handle = urlopen(req)

    cj = str(cj)
    cookie = cj[cj.find('JSESSIONID'):cj.find(' for www.bmv.com.mx/>')]

    host = 'www.bmv.com.mx'
    url = '/wb3/wb/BMV/BMV_componente_selector_de_valores/_rid/199/_mto/3/_url/BMVAPP/componenteSelectorBusqueda.jsf?st=1'

    headers = { "Host": host
                , "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.9.0.3)Gecko/2008092417 Firefox/3.0.3"
                , "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                , "Accept-Language": "fr"
                , "Accept-Encoding": "gzip,deflate"
                , "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7"
                , "Keep-Alive":300
                , "Connection": "keep-alive"
                , "Referer": "https://www.bmv.com.mx/wb3/wb/BMV/BMV_busqueda_de_valores/_rid/222/_mto/3/_url/BMVAPP/componenteSelectorInput.jsf?st=1"
                , "Cookie": cookie
               }

    conn = six.moves.http_client.HTTPConnection(host, 80)
    conn.request("GET", url, None, headers)
    response = conn.getresponse()
    #print response.status, response.reason

    url = '/wb3/wb/BMV/BMV_componente_selector_de_valores/_rid/199/_mto/3/_url/BMVAPP/componenteSelectorBusqueda.jsf'

    countname = 0
    countserie = 0
    for page in range(28):
        indice = str(page)
        previouspage = str(page-1)
        endpage = '27'

        if page == 0:
            params = 'tab1%3AformaListaEmisoras%3AletraActual=&tab1%3AformaListaEmisoras%3AtipoActual=1&tab1%3AformaListaEmisoras%3AsectorActualKey=0%2C0%2C0%2C0&tab1%3AformaListaEmisoras%3AbotonSubmit=Buscar+un+valor&tab1%3AformaListaEmisoras=tab1%3AformaLista'
        else:
            params = 'tab1%3AformaListaPaginas=tab1%3AformaListaPaginas&indice='+indice+'&tab1%3AformaListaPaginas%3A_idcl=tab1%3AformaListaPaginas%3Apagina%3A'+previouspage+'%3A_id85'

        headers = { "Host": host
                     , "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.9.0.3)Gecko/2008092417 Firefox/3.0.3"
                     , "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                     , "Accept-Language": "fr"
                     , "Accept-Encoding": "gzip,deflate"
                     , "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7"
                     , "Keep-Alive":300
                     , "Connection": "keep-alive"
                     , "Referer": "https://www.bmv.com.mx/wb3/wb/BMV/BMV_componente_selector_de_valores/_rid/199/_mto/3/_url/BMVAPP/componenteSelectorBusqueda.jsf?st=1"
                     , "Cookie": cookie
                     , "Content-Type": "application/x-www-form-urlencoded"
                     , "Content-Length": len(params)
                    }

        conn = six.moves.http_client.HTTPConnection(host, 80)
        conn.request("POST", url, params, headers)

        response = conn.getresponse()
        #print response.status, response.reason

        if page > 0:
            #Partial activation of the Progressbar
            x = x + 0.07
            dlg.Update(x, u'{} : {} / {}'.format(market, indice, endpage))

            startch = '<tr class="Tabla1_Renglon_'
            endch = '</tr><input type="hidden"'

            # returns the data
            data = response.read()

            if data.find(startch):
                a = data.find(startch)
                dataline = data[a:data.index(endch,a)]
                dataline = dataline.replace('</tr>','')
                dataline = dataline.replace('<tr>','')
                dataline = dataline.replace('<tbody>','')
                dataline = dataline.replace('</tbody>','')
                dataline = dataline.replace('</table>','')

            lines = splitLines(dataline)

            lineticker ='text-align: left;">'
            linename = 'margin-right:5px;">'
            lineserie = 'text-valign:bottom;">'

            for line in lines:
                if lineticker in line:
                    ticker = line[line.index(lineticker)+19:line.index('</span>')]
                if linename in line:
                    name = line[line.index(linename)+19:line.index('</span>')]
                    name = name.replace('&Oacute;','O') # �
                    name = name.replace('&Ntilde;','N') # �
                    name = name.replace('&Eacute;','E') # �
                    name = name.replace('&amp;','&')
                    name = name.replace(',','')
                    name = name.replace('  ',' ')
                    countname = countname + 1

                if lineserie in line:
                    serie = line[line.index(lineserie)+21:line.index('</span>')]
                    if serie != 'Series':
                        newticker = ticker + serie
                        if serie == '*':
                            newticker = ticker
                        newticker = newticker.replace('&amp;', '&')
                        countserie = countserie + 1

                        quotes.addQuote(isin='', name=name, ticker=newticker, market='MEXICO EXCHANGE', currency='MXN', place='MEX', country='MX')

    print(u'Imported {:d} quotes with {:d} different tickers from MEXICO EXCHANGE data.'.format(countname, countserie))
    response.close()
    handle.close()

    return True

# ============================================================================
# Export me
# ============================================================================

gListSymbolRegistry.register('MEXICO EXCHANGE', 'MEX', QList.any, QTag.list, Import_ListOfQuotes_MEX)

# ============================================================================
# Test ME
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_MEX(quotes)
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
