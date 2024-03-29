"""
A collection of modules for collecting, analyzing and plotting
financial data.   User contributions welcome!

"""
# flake8: noqa
#from __future__ import division
from __future__ import absolute_import
import os
import time
import warnings
from six.moves.urllib.request import urlopen

from hashlib import md5

import datetime

import numpy as np

from matplotlib import verbose, get_configdir
from matplotlib.dates import date2num
from matplotlib.cbook import Bunch
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.colors import colorConverter
from matplotlib.lines import Line2D, TICKLEFT, TICKRIGHT
from matplotlib.patches import Rectangle
from matplotlib.transforms import Affine2D
from six.moves import map
from six.moves import range
from six.moves import zip



configdir = get_configdir()
cachedir = os.path.join(configdir, 'finance.cache')


def parse_yahoo_historical(fh, asobject=False, adjusted=True):
    """
    Parse the historical data in file handle fh from yahoo finance and return
    results as a list of

    d, open, close, high, low, volume

    where d is a floating point representation of date, as returned by date2num

    if adjust=True, use adjusted prices
    """
    results = []

    lines = fh.readlines()

    datefmt = None

    for line in lines[1:]:
        vals = line.split(',')

        if len(vals)!=7: continue
        datestr = vals[0]
        if datefmt is None:
            try:
                datefmt = '%Y-%m-%d'
                dt = datetime.date(*time.strptime(datestr, datefmt)[:3])
            except ValueError:
                datefmt = '%d-%b-%y'  # Old Yahoo--cached file?
        dt = datetime.date(*time.strptime(datestr, datefmt)[:3])
        d = date2num(dt)
        open, high, low, close = [float(val) for val in vals[1:5]]
        volume = int(vals[5])
        if adjusted:
            aclose = float(vals[6])
            m = aclose/close
            open *= m
            high *= m
            low *= m
            close = aclose

        results.append((d, open, close, high, low, volume))
    results.reverse()
    if asobject:
        if len(results) == 0:
            return None
        else:
            date, open, close, high, low, volume = list(map(np.asarray, list(zip(*results))))
        return Bunch(date=date, open=open, close=close, high=high, low=low, volume=volume)
    else:
        return results

def fetch_historical_yahoo(ticker, date1, date2, cachename=None):
    """
    Fetch historical data for ticker between date1 and date2.  date1 and
    date2 are datetime instances

    Ex:
    fh = fetch_historical_yahoo('^GSPC', d1, d2)

    cachename is the name of the local file cache.  If None, will
    default to the md5 hash or the url (which incorporates the ticker
    and date range)

    a file handle is returned
    """

    ticker = ticker.upper()

    d1 = (date1.month-1, date1.day, date1.year)
    d2 = (date2.month-1, date2.day, date2.year)

    urlFmt = u'https://table.finance.yahoo.com/table.csv?a={:d}&b={:d}&c={:d}&d={:d}&e={:d}&f={:d}&s={}&y=0&g=d&ignore=.csv'

    url = urlFmt.format(d1[0], d1[1], d1[2], d2[0], d2[1], d2[2], ticker)

    if cachename is None:
        cachename = os.path.join(cachedir, md5(url).hexdigest())
    if os.path.exists(cachename):
        fh = open(cachename)
        verbose.report(u'Using cachefile {} for {}'.format(cachename, ticker))
    else:
        if not os.path.isdir(cachedir):
            os.mkdir(cachedir)
        urlfh = urlopen(url)

        with open(cachename, 'w') as fh:
            fh.write(urlfh.read())
        verbose.report(u'Saved {} data to cache file {}'.format(ticker, cachename))
        fh = open(cachename, 'r')

    return fh


def quotes_historical_yahoo(ticker, date1, date2, asobject=False, adjusted=True, cachename=None):
    """
    Get historical data for ticker between date1 and date2.  date1 and
    date2 are datetime instances

    results are a list of tuples

      (d, open, close, high, low, volume)

    where d is a floating poing representation of date, as returned by date2num

    if asobject is True, the return val is an object with attrs date,
    open, close, high, low, volume, which are equal length arrays

    if adjust=True, use adjusted prices

    Ex:
    sp = f.quotes_historical_yahoo('^GSPC', d1, d2, asobject=True, adjusted=True)
    returns = (sp.open[1:] - sp.open[:-1])/sp.open[1:]
    [n,bins,patches] = hist(returns, 100)
    mu = mean(returns)
    sigma = std(returns)
    x = normpdf(bins, mu, sigma)
    plot(bins, x, color='red', lw=2)

    cachename is the name of the local file cache.  If None, will
    default to the md5 hash or the url (which incorporates the ticker
    and date range)
    """

    ret = None
    try:
        with fetch_historical_yahoo(ticker, date1, date2, cachename) as fh:
            ret = parse_yahoo_historical(fh, asobject, adjusted)
    except IOError as exc:
        warnings.warn('urlopen() failure\n\n' + exc.strerror[1])

    return ret


def plot_day_summary(ax, quotes, ticksize=3, colorup='k', colordown='r'):
    """
    quotes is a list of (time, open, close, high, low, ...) tuples

    Represent the time, open, close, high, low as a vertical line
    ranging from low to high.  The left tick is the open and the right
    tick is the close.

    time must be in float date format - see date2num

    ax          : an Axes instance to plot to
    ticksize    : open/close tick marker in points
    colorup     : the color of the lines where close >= open
    colordown   : the color of the lines where close <  open
    return value is a list of lines added
    """

    lines = []
    for q in quotes:
        t, open, close, high, low = q[:5]

        if close >= open:
            color = colorup
        else:
            color = colordown

        vline = Line2D(
            xdata=(t, t), ydata=(low, high),
            color=color,
            antialiased=False,   # no need to antialias vert lines
            )

        oline = Line2D(
            xdata=(t, t), ydata=(open, open),
            color=color,
            antialiased=False,
            marker=TICKLEFT,
            markersize=ticksize,
            )

        cline = Line2D(
            xdata=(t, t), ydata=(close, close),
            color=color,
            antialiased=False,
            markersize=ticksize,
            marker=TICKRIGHT)

        lines.extend((vline, oline, cline))
        ax.add_line(vline)
        ax.add_line(oline)
        ax.add_line(cline)


    ax.autoscale_view()

    return lines


def candlestick(ax, quotes, width=0.2, colorup='k', colordown='r', alpha=1.0):
    """
    quotes is a list of (time, open, close, high, low, ...)  tuples.
    As long as the first 5 elements of the tuples are these values,
    the tuple can be as long as you want (eg it may store volume).

    time must be in float days format - see date2num

    Plot the time, open, close, high, low as a vertical line ranging
    from low to high.  Use a rectangular bar to represent the
    open-close span.  If close >= open, use colorup to color the bar,
    otherwise use colordown

    ax          : an Axes instance to plot to
    width       : fraction of a day for the rectangle width
    colorup     : the color of the rectangle where close >= open
    colordown   : the color of the rectangle where close <  open
    alpha       : the rectangle alpha level

    return value is lines, patches where lines is a list of lines
    added and patches is a list of the rectangle patches added
    """

    OFFSET = width/2.0

    lines = []
    patches = []
    for q in quotes:
        t, open, close, high, low = q[:5]

        if close>=open :
            color = colorup
            lower = open
            height = close-open
        else           :
            color = colordown
            lower = close
            height = open-close

        vline = Line2D(
            xdata=(t, t), ydata=(low, high),
            color='k',
            linewidth=0.5,
            antialiased=True,
            )

        rect = Rectangle(
            xy    = (t-OFFSET, lower),
            width = width,
            height = height,
            facecolor = color,
            edgecolor = color,
            )
        rect.set_alpha(alpha)


        lines.append(vline)
        patches.append(rect)
        ax.add_line(vline)
        ax.add_patch(rect)
    ax.autoscale_view()

    return lines, patches


def plot_day_summary2(ax, opens, closes, highs, lows, ticksize=4, colorup='k', colordown='r'):
    """
    Represent the time, open, close, high, low as a vertical line
    ranging from low to high.  The left tick is the open and the right
    tick is the close.

    ax          : an Axes instance to plot to
    ticksize    : size of open and close ticks in points
    colorup     : the color of the lines where close >= open
    colordown   : the color of the lines where close <  open

    return value is a list of lines added
    """

    # note this code assumes if any value open, close, low, high is
    # missing they all are missing

    rangeSegments = [ ((i, low), (i, high)) for i, low, high in zip(range(len(lows)), lows, highs) if low != -1 ]

    # the ticks will be from ticksize to 0 in points at the origin, and
    # we'll translate these to the i, close location
    openSegments = [ ((-ticksize, 0), (0, 0)) ]

    # the ticks will be from 0 to ticksize in points at the origin, and
    # we'll translate these to the i, close location
    closeSegments = [ ((0, 0), (ticksize, 0)) ]


    offsetsOpen = [ (i, open) for i, open in zip(range(len(opens)), opens) if open != -1 ]

    offsetsClose = [ (i, close) for i, close in zip(range(len(closes)), closes) if close != -1 ]


    scale = ax.figure.dpi * (1.0/72.0)

    tickTransform = Affine2D().scale(scale, 0.0)

    r,g,b = colorConverter.to_rgb(colorup)
    colorup = r,g,b,1
    r,g,b = colorConverter.to_rgb(colordown)
    colordown = r,g,b,1
    colord = { True : colorup,
               False : colordown,
               }
    colors = [colord[open<close] for open, close in zip(opens, closes) if open!=-1 and close !=-1]

    if len(rangeSegments) != len(offsetsOpen):
        raise TypeError("Expected lists of equal length.")
    if len(offsetsOpen) != len(offsetsClose):
        raise TypeError("Expected lists of equal length.")
    if len(offsetsClose) != len(colors):
        raise TypeError("Expected lists of equal length.")

    useAA = 0,   # use tuple here
    if ticksize > 1:
        lw = 0.5,   # and here
    else:
        lw = 0.2,

    rangeCollection = LineCollection(rangeSegments,
                                     colors=colors,
                                     linewidths=lw,
                                     antialiaseds=useAA,
                                     )

    openCollection = LineCollection(openSegments,
                                    colors=colors,
                                    antialiaseds=useAA,
                                    linewidths=lw,
                                    offsets=offsetsOpen,
                                    transOffset=ax.transData,
                                   )
    openCollection.set_transform(tickTransform)

    closeCollection = LineCollection(closeSegments,
                                     colors=colors,
                                     antialiaseds=useAA,
                                     linewidths=lw,
                                     offsets=offsetsClose,
                                     transOffset=ax.transData,
                                     )
    closeCollection.set_transform(tickTransform)

    minx, maxx = (0, len(rangeSegments))
    miny = min([low for low in lows if low !=-1])
    maxy = max([high for high in highs if high != -1])
    corners = (minx, miny), (maxx, maxy)
    ax.update_datalim(corners)
    ax.autoscale_view()

    # add these last
    ax.add_collection(rangeCollection)
    ax.add_collection(openCollection)
    ax.add_collection(closeCollection)
    return rangeCollection, openCollection, closeCollection


def plot_day_summary3(ax, closes, ticksize=4, color='k'):
    """
    Represent the time, open, close, high, low as a vertical line
    ranging from low to high.  The left tick is the open and the right
    tick is the close.

    ax          : an Axes instance to plot to
    ticksize    : size of open and close ticks in points
    color       : the color of the lines

    return value is a list of lines added
    """

    rangeSegments = []
    pfrom = (0, closes[0])
    for i in range(0, len(closes)):
        if closes[i] >= 0.0:
            pto = (i, closes[i])
            rangeSegments.append((pfrom, pto))
            pfrom = pto

    r, g, b = colorConverter.to_rgb(color)
    color = r, g, b, 1

    useAA = 0,   # use tuple here
    if ticksize > 1:
        lw = 0.5,   # and here
    else:
        lw = 0.2,

    rangeCollection = LineCollection(rangeSegments,
                                     colors=color,
                                     linewidths=lw,
                                     antialiaseds=useAA,
                                     )

    minx, maxx = (0, len(rangeSegments))
    miny = min([low for low in closes if low !=-1])
    maxy = max([high for high in closes if high != -1])
    corners = (minx, miny), (maxx, maxy)
    ax.update_datalim(corners)
    ax.autoscale_view()

    # add these last
    ax.add_collection(rangeCollection)
    return rangeCollection


def candlestick2(ax, opens, closes, highs, lows, width=0.6, colorup='k', colordown='r', alpha=0.75):
    """
    Represent the open, close as a bar line and high low range as a
    vertical line.


    ax          : an Axes instance to plot to
    width       : fraction of a day for the rectangle width
    colorup     : the color of the lines where close >= open
    colordown   : the color of the lines where close <  open
    alpha       : bar transparency

    return value is lineCollection, barCollection
    """

    # note this code assumes if any value open, close, low, high is
    # missing they all are missing

    delta = width/2.
    barVerts = [ ( (i-delta, open), (i-delta, close), (i+delta, close), (i+delta, open) ) for i, open, close in zip(range(len(opens)), opens, closes) if open != -1 and close!=-1 ]

    rangeSegments1 = [ ((i, low), (i, min(close,open))) for i, low, close, open in zip(range(len(lows)), lows, closes, opens) if low != -1 ]
    rangeSegments2 = [ ((i, max(close,open)), (i, high)) for i, high, close, open in zip(range(len(lows)), highs, closes, opens) if high != -1 ]

    r,g,b = colorConverter.to_rgb(colorup)
    colorup = r,g,b,alpha
    r,g,b = colorConverter.to_rgb(colordown)
    colordown = r,g,b,alpha
    colord = { True : colorup,
               False : colordown,
               }
    colors = [colord[open<=close] for open, close in zip(opens, closes) if open!=-1 and close !=-1]

    if len(barVerts) != len(rangeSegments1):
        raise TypeError("Expected lists of equal length.")
    if len(barVerts) != len(rangeSegments2):
        raise TypeError("Expected lists of equal length.")

    useAA = 0,  # use tuple here
    lw = 0.5,   # and here
    rangeCollection1 = LineCollection(rangeSegments1,
                                     colors       = ( (0,0,0,1), ),
                                     linewidths   = lw,
                                     antialiaseds = useAA,
                                     )

    rangeCollection2 = LineCollection(rangeSegments2,
                                     colors       = ( (0,0,0,1), ),
                                     linewidths   = lw,
                                     antialiaseds = useAA,
                                     )

    barCollection = PolyCollection(barVerts,
                                   facecolors   = colors,
                                   edgecolors   = ( (0,0,0,1), ),
                                   antialiaseds = useAA,
                                   linewidths   = lw,
                                   )

    minx, maxx = (0, len(rangeSegments1))
    miny = min([low for low in lows if low !=-1])
    maxy = max([high for high in highs if high != -1])

    corners = (minx, miny), (maxx, maxy)
    ax.update_datalim(corners)
    ax.autoscale_view()

    # add these last
    ax.add_collection(barCollection)
    ax.add_collection(rangeCollection1)
    ax.add_collection(rangeCollection2)
    return rangeCollection1, rangeCollection2, barCollection


def volume_overlay(ax, closes, volumes, colorup='k', colordown='r', width=0.7, alpha=1.0):
    """
    Add a volume overlay to the current axes.  The closes are used to
    determine the color of the bar.  -1 is missing.  If a value is
    missing on one it must be missing on all

    ax          : an Axes instance to plot to
    width       : fraction of a day for the rectangle width
    colorup     : the color of the lines where close >= previous close
    colordown   : the color of the lines where close <  previous close
    alpha       : bar transparency

    nb: first point is not displayed - it is used only for choosing the
    right color

    """

    # Make sure we always have a previous close (carry over last close)
    pcloses = np.array(closes[:-1])
    last = 0
    for i in range(0,len(pcloses)):
        if pcloses[i] == -1:
            pcloses[i] = last
        else:
            last = pcloses[i]
    # Skip first point
    ccloses = closes[1:]
    cvolumes = volumes[1:]

    r,g,b = colorConverter.to_rgb(colorup)
    colorup = r,g,b,alpha
    r,g,b = colorConverter.to_rgb(colordown)
    colordown = r,g,b,alpha
    colord = { True : colorup,
               False : colordown,
               }
    colors = [colord[pclose<=close] for pclose, close, v in zip(pcloses, ccloses, cvolumes) if close !=-1 and v >= 0]

    delta = width/2.
    bars = [ ( (i-delta, 0), (i-delta, v), (i+delta, v), (i+delta, 0)) for i, v in enumerate(cvolumes) if v >= 0 ]

    if len(bars) != len(colors):
        raise TypeError("Expected lists of equal length.")

    useAA = 0,  # use tuple here
    lw = 0.5,   # and here
    barCollection = PolyCollection(bars,
                                   facecolors   = colors,
                                   edgecolors   = ( (0,0,0,1), ),
                                   antialiaseds = useAA,
                                   linewidths   = lw,
                                   )

    corners = (0, 0), (len(bars), max(cvolumes))
    ax.update_datalim(corners)
    ax.autoscale_view()

    # add these last
    ax.add_collection(barCollection)
    return barCollection


def volume_overlay3(ax, quotes, colorup='k', colordown='r', width=4, alpha=1.0):
    """
    Add a volume overlay to the current axes.  quotes is a list of (d,
    open, close, high, low, volume) and close-open is used to
    determine the color of the bar

    kwarg
    width       : the bar width in points
    colorup     : the color of the lines where close1 >= close0
    colordown   : the color of the lines where close1 <  close0
    alpha       : bar transparency
    """

    r, g, b = colorConverter.to_rgb(colorup)
    colorup = r, g, b, alpha
    r, g, b = colorConverter.to_rgb(colordown)
    colordown = r, g, b, alpha
    colord = {
        True: colorup,
        False: colordown,
    }

    dates, opens, closes, highs, lows, volumes = list(zip(*quotes))
    colors = [colord[close1>=close0] for close0, close1 in zip(closes[:-1], closes[1:]) if close0!=-1 and close1 !=-1]
    colors.insert(0, colord[closes[0]>=opens[0]])

    right = width/2.0
    left = -width/2.0


    bars = [ ( (left, 0), (left, volume), (right, volume), (right, 0)) for d, open, close, high, low, volume in quotes]

    sx = ax.figure.dpi * (1.0/72.0)  # scale for points
    sy = ax.bbox.height / ax.viewLim.height

    barTransform = Affine2D().scale(sx,sy)

    dates = [d for d, open, close, high, low, volume in quotes]
    offsetsBars = [(d, 0) for d in dates]

    useAA = 0,  # use tuple here
    lw = 0.5,   # and here
    barCollection = PolyCollection(bars,
                                   facecolors   = colors,
                                   edgecolors   = ( (0,0,0,1), ),
                                   antialiaseds = useAA,
                                   linewidths   = lw,
                                   offsets      = offsetsBars,
                                   transOffset  = ax.transData,
                                   )
    barCollection.set_transform(barTransform)

    minpy, maxx = (min(dates), max(dates))
    miny = 0
    maxy = max([volume for d, open, close, high, low, volume in quotes])
    corners = (minpy, miny), (maxx, maxy)
    ax.update_datalim(corners)
    #print 'datalim', ax.dataLim.get_bounds()
    #print 'viewlim', ax.viewLim.get_bounds()

    ax.add_collection(barCollection)
    ax.autoscale_view()

    return barCollection


def index_bar(ax, vals, facecolor='b', edgecolor='k', width=4, alpha=1.0, ):
    """
    Add a bar collection graph with height vals (-1 is missing).

    ax          : an Axes instance to plot to
    width       : the bar width in points
    alpha       : bar transparency
    """

    facecolors = (colorConverter.to_rgba(facecolor, alpha),)
    edgecolors = (colorConverter.to_rgba(edgecolor, alpha),)

    right = width/2.0
    left = -width/2.0

    bars = [ ( (left, 0), (left, v), (right, v), (right, 0)) for v in vals if v != -1 ]

    sx = ax.figure.dpi * (1.0/72.0)  # scale for points
    sy = ax.bbox.height / ax.viewLim.height

    barTransform = Affine2D().scale(sx,sy)

    offsetsBars = [ (i, 0) for i,v in enumerate(vals) if v != -1 ]

    barCollection = PolyCollection(bars,
                                   facecolors   = facecolors,
                                   edgecolors   = edgecolors,
                                   antialiaseds = (0,),
                                   linewidths   = (0.5,),
                                   offsets      = offsetsBars,
                                   transOffset  = ax.transData,
                                   )

    minx, maxx = (0, len(offsetsBars))
    miny = 0
    maxy = max([v for v in vals if v!=-1])
    corners = (minx, miny), (maxx, maxy)
    ax.update_datalim(corners)
    ax.autoscale_view()

    # add these last
    ax.add_collection(barCollection)
    return barCollection
