#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_quotes_shangai.py
#
# Description: List of quotes from http://www.sse.com.cn/
#
# Developed for iTrade code (http://itrade.sourceforge.net).
#
# Original template for "plug-in" to iTrade is	from Gilles Dumortier.
# New code for SSE is from Michel Legrand.

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
import six.moves.urllib.request, six.moves.urllib.error, six.moves.urllib.parse
from contextlib import closing

# iTrade system
import itrade_config
from itrade_logging import setLevel, debug, info
from itrade_defs import QList, QTag
from itrade_ext import gListSymbolRegistry
from itrade_connection import ITradeConnection
from six.moves import range

# ============================================================================
# Import_ListOfQuotes_SHG()
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


def Import_ListOfQuotes_SHG(quotes, market='SHANGHAI EXCHANGE', dlg=None, x=0):
    if itrade_config.verbose:
        print(u'Update {} list of symbols'.format(market))
    connection = ITradeConnection(proxy=itrade_config.proxyHostname,
                                  proxyAuth=itrade_config.proxyAuthentication)

    # Download SSE A SHARE

    urlA = 'https://www.sse.com.cn/sseportal/webapp/datapresent/queryindexcnpe?indexCode=000002&CURSOR='
    ch = '<TD class=content bgColor=white><a href="/sseportal/webapp/datapresent/SSEQueryListCmpAct?reportName=QueryListCmpRpt&REPORTTYPE=GSZC&COMPANY_CODE='
    cursor = 1
    count = 0

    for cursor in range(1, 921, 20):
        url = urlA + str(cursor)

        info(u'Import_ListOfQuotes_SSE A SHARE:connect to {}'.format(url))
        req = six.moves.urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.5) Gecko/20041202 Firefox/1.0')

        try:
            with closing(six.moves.urllib.request.urlopen(req)) as f:
                data = f.read()

            #data=connection.getDataFromUrl(url)
        except Exception:
            print('Import_ListOfQuotes_SSE A SHARE:unable to connect to', url)
            return False

        lines = splitLines(data)

        for line in lines:
            if ch in line:
                ticker = line[(line.find(ch)+len(ch)): line.find('&PRODUCTID=')]
                name = line[(line.find('">')+2): line.find('</a>&nbsp;</TD>')]
                if ticker == '600717': name = 'TIANJIN PORT CO. LTD.'
                name = name.replace('&amp;', '&')
                name = name.replace('&amp;nbsp;', '& ')
                name = name.replace('&nbsp;', '')
                name = name.replace(',', ' ')
                name = name.replace(';', ' ')
                name = name.replace('��', '&')
                name = name.replace('��', '-')
                name = name.replace('��',' ')
                name = name.replace('��',' (')
                name = name.replace('��',' )')
                name = name.replace('��','')
                name = name.replace('��','')
                name = name.replace('��','\'')
                name = name.replace('��','')
                name = name.replace('��',' ')
                name = name.replace('  ',' ')
                name = name.replace('..','.')
                name = name.upper()
                name = name.replace('COMPANY','CO.')
                name = name.replace('LIMITED','LTD')
                name = name.replace('CORPORATION','CORP.')
                name = name.replace('DEVELOPMENT','DEV.')

                count = count + 1

                dlg.Update(x, u'SSE A SHARE: {} / ~1000'.format(cursor))

                quotes.addQuote(isin='', name=name,
                        ticker=ticker, market='SHANGHAI EXCHANGE',
                        currency='CNY', place='SHG', country='CN')

    # Download SSE B SHARE

    url = 'https://www.sse.com.cn/sseportal/en_us/ps/bshare/lccl.shtml'

    info(u'Import_ListOfQuotes_SSE B SHARE:connect to {}'.format(url))

    try:
        data = connection.getDataFromUrl(url)
    except Exception:
        debug('Import_ListOfQuotes_SSE B SHARE:unable to connect :-(')
        return False

    lines = splitLines(data)

    #typical lines

    #    <td class="table3" bgcolor="#dbedf8"  > SRB</td>
    #    <td class="table3" bgcolor="#dbedf8"  > 900907</td>

    #    <td class="table3" bgcolor="#dbedf8"  > Shanghai Rubber Belt&nbsp; Co., Ltd.</td>
    #    <td class="table3" bgcolor="#dbedf8"  > 19th Floor, 1600 Shiji Avenue, Shanghai</td>
    #    <td class="table3" bgcolor="#dbedf8"  > 200122</td>
    #  </tr>
    #  <tr>
    #   <td class="table3" bgcolor="white"  > SCAC B</td>

    #    <td class="table3" bgcolor="white"  > 900908</td>
    #    <td class="table3" bgcolor="white"  > Shanghai Chlor Alkali Chemical&nbsp;
    #      Co., Ltd.</td>
    #    <td class="table3" bgcolor="white"  > 17th Floor, 1271 Pudong Nan Road, Shanghai</td>
    #    <td class="table3" bgcolor="white"  > 200122</td>

    n = 1
    i = 0

    dlg.Update(x, 'SHANGHAI B SHARE')
    for line in lines:
        if '<td class="table_title2" bgcolor="#337fb2"  >Post Code</td>' in line : n = 0
        if n == 0:
            if ('<td class="table3" bgcolor="#dbedf8"  > ' in line or
               '<td class="table3" bgcolor="white"  > ' in line):
                i = i + 1
                ch = line[(line.find('>')+2):(line.find('</td>'))]
                if i == 2:
                    ticker = ch
                elif i == 3:
                    name = ch
                elif i == 5:
                    i = 0
                    name = name.replace('&nbsp;', '')
                    name = name.replace('&amp;', '&')
                    name = name.replace(',', '')

                    count = count + 1

                    quotes.addQuote(isin='', name=name,
                            ticker=ticker, market='SHANGHAI EXCHANGE',
                            currency='CNY', place='SHG', country='CN')
            elif i == 3:
                name = name + ' ' + line.strip()
                if name.find('</td>'):
                    name = name[:-5]

    if itrade_config.verbose:
        print(u'Imported {:d} lines from SHANGHAI EXCHANGE'.format(count))

    return True


# ============================================================================
# Export me
# ============================================================================

gListSymbolRegistry.register('SHANGHAI EXCHANGE', 'SHG', QList.any, QTag.list, Import_ListOfQuotes_SHG)

# ============================================================================
# Test ME
# ============================================================================

if __name__ == '__main__':
    setLevel(logging.INFO)

    from itrade_quotes import quotes

    Import_ListOfQuotes_SHG(quotes)
    quotes.saveListOfQuotes()

# ============================================================================
# That's all folks !
# ============================================================================
