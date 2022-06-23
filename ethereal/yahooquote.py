#!/usr/bin/env python

##################################################
# Name:        pyQ - Python Quote Grabber
# Author:      Rimon Barr <barr@cs.cornell.edu>
# Start date:  10 January 2002
# Purpose:     Retrieve stock quote data in Python
# License:     GPL 2.0

##################################################
# Activity log:
#
# 10/01/02 - Initial release
# 14/10/02 - Yahoo changed url format
# 31/10/02 - More convenient programmatic interface and local caching
# 21/09/04 - Updated by Alberto Santini to accomodate Yahoo changes
# 27/01/05 - Updated by Alberto Santini to accomodate Yahoo changes

from __future__ import absolute_import
from __future__ import print_function
import os
import sys
import re
import traceback
import getopt
import six.moves.urllib.request
import six.moves.urllib.parse
import six.moves.urllib.error
import anydbm
import time

Y2KCUTOFF=60
__version__ = "0.5"
CACHE='stocks.db'
DEBUG = 1

def showVersion():
  print('pyQ v'+__version__+', by Rimon Barr:')
  print('Python Yahoo Quote fetching utility')

def showUsage():
  print()
  showVersion()
  print()
  print('Usage: pyQ [-i] [start_date [end_date]] ticker [ticker...]')
  print('       rimdu -h | -v')
  print()
  print('  -h, -?, --help      display this help information')
  print('  -v, --version       display version')
  print('  -i, --stdin         tickers fed on stdin, one per line')
  print()
  print('    date formats are yyyymmdd')
  print('    if enddate is omitted, it is assume to be the same as startdate')
  print('    if startdate is omitted, we use *current* stock tables')
  print('      and otherwise, use historical stock tables.')
  print('      (current stock tables will give previous close price before')
  print('       market closing time.)')
  print('    tickers are exactly what you would type at finance.yahoo.com')
  print('    output format: "ticker, date (yyyymmdd), open, high, low, close, vol"')
  print('  date formats are yyyymmdd')
  print('  tickers are exactly what you would type at finance.yahoo.com')
  print('  output format: ticker, date, open, high, low, close, volume')
  print()
  print('Send comments, suggestions and bug reports to <barr+pyq@cs.cornell.edu>.')
  print()

def usageError():
  print('rimdu: command syntax error')
  print('Try `rimdu --help\' for more information.')

def isInt(i):
  try:
    int(i)
    return 1
  except:
    return 0

def splitLines(buf):
  lines=buf.split('\n')
  lines=[x for x in lines if x]
  def removeCarriage(s):
    if s[-1]=='\r': return s[:-1]
    else: return s
  lines=[removeCarriage(l) for l in lines]
  return lines

def parseDate(d):
  '''convert yyyymmdd string to tuple (yyyy, mm, dd)'''
  return (d[:-4], d[-4:-2], d[-2:])

def yy2yyyy(yy):
  global Y2KCUTOFF;
  yy=int(yy) % 100
  if yy<Y2KCUTOFF: return repr(yy+2000)
  else: return repr(yy+1900)

# convert month to number
MONTH2NUM = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
  'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
def dd_mmm_yy2yyyymmdd(d):
  global MONTH2NUM
  d=d.split('-')
  day='%02d' % int(d[0])
  month='%02d' % MONTH2NUM[d[1]]
  year=yy2yyyy(d[2])
  return year+month+day

DAYSECS = 60 * 60 * 24
def allDates(d1,d2):
  '''Return all dates in ascending order. Inputs in yyyymmdd format'''
  if int(d1)>int(d2):
    raise 'd1 must be smaller than d2'
  d1 = time.mktime(time.strptime(d1, '%Y%m%d'))
  d2 = time.mktime(time.strptime(d2, '%Y%m%d'))+1
  dates = []
  while d1 < d2:
    dates.append(time.strftime('%Y%m%d', time.localtime(d1)))
    d1 = d1 + DAYSECS
  return dates

def aggDates(dates):
  '''Aggregate list of dates (yyyymmdd) in range pairs'''
  if not dates: return []
  aggs = []
  dates=[int(date) for date in dates]
  dates.sort()
  high=dates.pop(0)
  low=high
  for date in dates:
    if date==high+1: high=date
    else:
      aggs.append( (low, high) )
      high=date; low=high
  aggs.append( (low, high) )
  aggs = [ (str(low),str(high)) for (low, high) in aggs]
  return aggs

def getTicker(d1, d2, ticker):
  if DEBUG:
    print('Quering Yahoo!... for %s (%s-%s)' % (ticker, d1, d2))
  d1=parseDate(d1)
  d2=parseDate(d2)
  url='http://ichart.finance.yahoo.com/table.csv'
  query = (
    ('a', '%02d' % (int(d1[1])-1)),
    ('b', d1[2]),
    ('c', d1[0]),
    ('d', '%02d' % (int(d2[1])-1)),
    ('e', d2[2]),
    ('f', d2[0]),
    ('s', ticker),
    ('y', '0'),
    ('g', 'd'),
    ('ignore', '.csv'),
  )
  query = ['%s=%s' % (var_val[0], str(var_val[1])) for var_val in query]
  query = '&'.join(query)
  url=url+'?'+query
  f=six.moves.urllib.request.urlopen(url)
  buf=f.read()
  lines=splitLines(buf)
  if re.match('no prices', lines[0], re.I): return
  lines=lines[1:len(lines)]
  result = []
  def processLine(l, t=ticker):
    l=l.split(',')
    l[0]=dd_mmm_yy2yyyymmdd(l[0])
    l=[t]+l
    result.append(l)
  for l in lines:
    processLine(l)
  return result

def getCachedTicker(d1, d2, ticker, forcefailed):
  '''Get tickers, hopefully from cache.
    d1, d2 = yyyymmdd starting and ending
    ticker = symbol string
    forcefailed = integer for cachebehaviour
      =0 : do not retry failed data points
      >0 : retry failed data points n times
      -1 : retry failed data points, reset retry count
      -2 : ignore cache entirely, refresh ALL data points'''
  dates = allDates(d1, d2)
  # get from cache
  data = {}
  db = anydbm.open(CACHE, 'c')
  for d in dates:
    try: data[ (d, ticker) ] = db[ repr((d, ticker)) ]
    except KeyError: pass
  # forced failed
  if forcefailed:
    for k in data.keys():
      if (forcefailed==-2 or
          (forcefailed==-1 and type(eval(data[k]))==type(0)) or
          eval(data[k]) < forcefailed):
        del data[k]
  # compute missing
  cached = [d for d,ticker in data.keys()]
  missing = [d for d in dates if d not in cached]
  for d1, d2 in aggDates(missing):
    tmp = getTicker(d1, d2, ticker)
    for t in tmp:
      _, d, datum = t[0], t[1], t[2:]
      data[ (d, ticker) ] = db[ repr((d, ticker)) ] = repr(datum)
  # failed
  cached = [d for d,ticker in data.keys()]
  failed = [d for d in missing if d not in cached]
  for d in failed:
    try: times = eval(db[ repr((d, ticker)) ])
    except: times = 0
    if forcefailed<0: times = 1
    if times < forcefailed: times = times + 1
    data [ (d, ticker) ] = db[ repr((d, ticker)) ] = repr(times)
  # result
  result = []
  for d in dates:
    datum = eval(data[(d,ticker)])
    if type(datum) != type(0):
      result.append( [ticker, d] + datum )
  return result

def getTickers(d1, d2, tickers, forcefailed=0):
  '''Get tickers.
    d1, d2 = yyyymmdd starting and ending
    tickers = list of symbol strings
    forcefailed = integer for cachebehaviour
      =0 : do not retry failed data points
      >0 : retry failed data points n times
      -1 : retry failed data points, reset retry count
      -2 : ignore cache entirely, refresh ALL data points'''
  result = []
  for t in tickers:
    result = result + getCachedTicker(d1, d2, t, forcefailed)
  return result

def getTickersNowChunk(tickers):
  url='http://finance.yahoo.com/d/quotes.csv';
  tickers=''.join(tickers)
  query={ 's':tickers, 'f':'sohgpv', 'e':'.csv' }
  url=url+'?'+six.moves.urllib.parse.urlencode(query)
  f=six.moves.urllib.request.urlopen(url)
  buf=f.read()
  lines=splitLines(buf)
  result = []
  def processLine(l):
    l=l.split(',')
    l[0]=l[0][1:-1].lower()
    t=time.localtime()
    l.insert(1, '%4d%02d%02d' % (t[0], t[1], t[2]))
    result.append(l)
  for l in lines:
    processLine(l)
  return result

def getTickersNow(tickers):
  result = []
  while tickers:

    result = result + getTickersNowChunk(tickers[:150])
    tickers=tickers[150:]
  return result

def main():
  # parse options
  try:
    opts, args = getopt.getopt(sys.argv[1:], 'hv?i',
      ['help', 'version', 'stdin'])
  except getopt.GetoptError:
    usageError()
    return
  # process options
  stdin=0
  for o, a in opts:
    if o in ("-h", "--help", "-?"):
      showUsage()
      return
    if o in ("-v", "--version"):
      showVersion()
      return
    if o in ("-i", "--stdin"):
      stdin=1
  t=time.localtime()
  startdate='%4d%02d%02d' % (t[0], t[1], t[2])
  enddate=startdate
  today=1
  tickers=[]
  argpos=-1
  for a in args:
    argpos=argpos+1
    if argpos==0 and isInt(a):
      startdate=enddate=a
      today=0
      continue
    if argpos==1 and isInt(a):
      enddate=a
      if a=='0':
        enddate='%4d%02d%02d' % (t[0], t[1], t[2])
      continue
    tickers=tickers+[a]
  if stdin:
    tickers=tickers+splitLines(sys.stdin.read())
  if not len(tickers):
    showUsage()
    return
  if today:
    result = getTickersNow(tickers)
    for l in result:
      print(','.join(l))
  else:
    result = getTickers(startdate, enddate, tickers)
    for l in result:
      print(','.join(l))

try:
  if __name__=='__main__': main()
except KeyboardInterrupt:
  traceback.print_exc()
  print('Break!')
