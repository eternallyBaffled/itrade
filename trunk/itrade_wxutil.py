#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxutil.py
#
# Description: wxPython utilities, incl. matplotlib func support
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is Gilles Dumortier.
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
# 2005-10-26    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import re
import string
from types import *
import operator

# itrade system
from itrade_logging import *
from itrade_local import message

# wxPython system
import itrade_wxversion
import wx
import wx.html
import wx.lib.wxpTag

# iTrade wxpython
from itrade_wxhtml import wxUrlClickHtmlWindow,EVT_HTML_URL_CLICK

# matplotlib system
import matplotlib
matplotlib.use('WXAgg')
matplotlib.rcParams['numerix'] = 'numpy'

# matplotlib helpers
from matplotlib.colors import colorConverter

# ============================================================================
# MatplotColorToRGB()
#
# convert a MatplotColor to a RGB tuple used by wxPython
#
#      b  : blue
#      g  : green
#      r  : red
#      c  : cyan
#      m  : magenta
#      y  : yellow
#      k  : black
#      w  : white
#
# For a greater range of colors, you have two options.  You can specify
# the color using an html hex string, as in
#
#     color = '#eeefff'
#
# or you can pass an R,G,B tuple, where each of R,G,B are in the range
# [0,1].
#
# Finally, legal html names for colors, like 'red', 'burlywood' and
# 'chartreuse' are supported.
#
# ============================================================================

def MatplotColorToRGB(colorname='k'):
    r,g,b = colorConverter.to_rgb(colorname)

    return wx.Colour(int(r*255),int(g*255),int(b*255))

# ============================================================================
# FontFromSize
#   1 : small
#   2 : regular
#   3 : big
#
# Porting note : adjust this function to the platform ?? __x
# ============================================================================

def FontFromSize(size):
    if size==2:
        return wx.Font(10, wx.SWISS , wx.NORMAL, wx.NORMAL)
    elif size==3:
        return wx.Font(12, wx.SWISS , wx.NORMAL, wx.NORMAL)
    else:
        return wx.Font(7, wx.SWISS , wx.NORMAL, wx.NORMAL)

# ============================================================================
# wx.MessageDialog()
#
#   parent          Parent window
#   msg             Message to show on the dialog
#   caption         The dialog caption
#   style           A dialog style (bitlist) containing flags chosen from :
#      wxOK                 Show an OK button.
#      wxCANCEL             Show a Cancel button.
#      wxYES_NO             Show Yes and No buttons.
#      wxYES_DEFAULT        Used with wxYES_NO, makes Yes button the default -
#                           which is the default behaviour.
#      wxNO_DEFAULT         Used with wxYES_NO, makes No button the default.
#      wxICON_EXCLAMATION   Shows an exclamation mark icon.
#      wxICON_HAND          Shows an error icon.
#      wxICON_ERROR         Shows an error icon - the same as wxICON_HAND.
#      wxICON_QUESTION      Shows a question mark icon.
#      wxICON_INFORMATION   Shows an information (i) icon.
#      wxSTAY_ON_TOP        The message box stays on top of all other window,
#                           even those of the other applications (Win only).
#   pos             Dialog position. Not Windows
#
# ============================================================================

def Button(label,id,makedefault=0):
    return [(label,id,makedefault)]

def OKButton(makedefault=1):
    return Button(message('ok'),`wx.ID_OK`,makedefault)

def CancelButton(makedefault=0):
    return Button(message('cancel'),`wx.ID_CANCEL`,makedefault)

def ApplyButton(makedefault=0):
    return Button(message('valid'),`wx.ID_APPLY`,makedefault)

def YesButton(makedefault=1):
    return Button(message('yes'),`wx.ID_YES`,makedefault)

def NoButton(makedefault=0):
    return Button(message('no'),`wx.ID_NO`,makedefault)

# ============================================================================
# generate HTML for buttons
# ============================================================================

def _tupn(tup,n):
    if type(tup) == TupleType:
        try:
            return tup[n]
        except IndexError:
            return None
    else:
        if n == 0:
            return tup
        else:
            return None

DefaultButtonString = '''\
<wxp class="%s" module="%s">
    <param name="label" value="%s">
    <param name="id"    value="%s">
</wxp>'''

class Default_wxButton(wx.Button):
    def __init__(self,*args,**kwargs):
        apply(wx.Button.__init__, (self,) + args,kwargs)
        self.SetDefault()

def HTMLforSingleButton(label,id=None,makedefault=0):
    if id is None:
        return label
    else:
        if makedefault == 1:
            defaultstring1 = "Default_wxButton"
            defaultstring2 = "itrade_wxutil"
        else:
            defaultstring1 = "Button"
            defaultstring2 = "wx"
        return DefaultButtonString % (defaultstring1,defaultstring2,label,id)

def HTMLforButtons (buttons,betweenbuttons=""):
    def rn(n):
        return lambda tup,n=n: _tupn(tup,n)
    return string.join (map (HTMLforSingleButton,map(rn(0),buttons),map(rn(1),buttons),map(rn(2),buttons)),betweenbuttons)

# ============================================================================
# HTMLDialog
#
# Adapted (by dgil) to iTrade from HTMLDialog.py (by Chris Fama)
#
#    use:
#        dlg = HTMLDialog(parent,OPTIONS)
#    [or
#        dlg = HTMLDialog(parent)
#        ...........
#        dlg.SetContents(OPTIONS)
#     ]
#        ......
#        dlg.ShowModal() **OR** dlg.Show()
#        ..........>
#        dlg.Destroy () # if modal...........
#
#        OPTIONS (with defaults) from
#                     name="",
#                     buttons=OKButton(makedefault=1),
#                     text="",
#                     namefmt="<h1>%s</h1>",
#                     caption=None,
#                     betweenbuttons="",
#                     size=None,
#                     defaultsize=(420,380),
#                     image=None,
#                     imagedir="",
#                     imageurl="",
#                     link_regexp=re.compile("</a>",re.IGNORECASE),
#                     bgcolor=None,
#                     fgcolor=None,
#                     boxcolor='#458154'
#
#    "text" is the HTML to display in the box
#
#    "buttons" is a sequence of -
#        ("label",*"id") specifications for buttons, or "HTML code".
#
#    e.g.,
#        HTMLDialog(.......,
#                   buttons=OKButton(makedefault=1) + \
#                           CancelButton () +\
#                           ApplyButton () +\
#                           [" or be <i>brave</i> and "] +\
#                           Button("Exit now",`exitID`),
#                   .........)
#    [this is equivalent to
#        HTMLDialog(.......,
#                   buttons=[("OK",`wxID_OK`,1),
#                            ("Cancel",`wxID_CANCEL),
#                            ("Apply",`wxID_APPLY`),
#                            " or be <i>brave</i> and ",
#                            ("Exit now",`exitID`)],
#                   .........)
#     .
#
#    "image", if specified, is the filename of an image file to be displayed
#    to the left of the name;
#    ***       wxImage_AddHandler(wxGIFHandler()) is called if needed;
#              other handlers MAY be necessary. ***
#
#    "boxcolor" is used for the interior colour of the box containing the name
#    or "image" image file.  Both of these, if specified, should be HTML colour
#    specifications [i.e., '#RRGGBB', where RR is the hexadecimal value of the
#    red component of the colour, etc.
#
#    If "size" is unspecified or None, the size of the dialog is chosen so
#    as to be as small as possible without needing a vertical scrollbar,
#    while having the same aspect ratio as the display (see wxDisplaySize);
#    if this is not possible, then "defaultsize" is used.
#
# ============================================================================

class HTMLDialog(wx.Dialog):
    def __init__(self,
                 parent,
                 size=None,
                 defaultsize=(420, 380),
                 name="",
                 caption=None,
                 **kwargs):

        # be sure to have a caption
        if caption is None:
            caption = name
        kwargs['name'] = name

        # use defaultsize if no size
        if size is None:
            size = defaultsize
        else:
            kwargs['size'] = size
        kwargs['defaultsize'] = defaultsize

        # init
        wx.Dialog.__init__(self, parent, -1, caption, style = wx.TAB_TRAVERSAL | wx.DEFAULT_DIALOG_STYLE, size = size)

        # container
        self.m_html = wxUrlClickHtmlWindow(self, -1, style = wx.CLIP_CHILDREN | wx.html.HW_NO_SELECTION | wx.TAB_TRAVERSAL)
        EVT_HTML_URL_CLICK(self.m_html, self.OnLinkClick)

        # set the content
        apply(self.SetContents,(),kwargs)

        # layout the content
        self.SetAutoLayout(True)

        lc = wx.LayoutConstraints()
        lc.top.SameAs(self, wx.Top, 5)
        lc.left.SameAs(self, wx.Left, 5)
        lc.bottom.SameAs(self, wx.Bottom, 5)
        lc.right.SameAs(self, wx.Right, 5)
        self.m_html.SetConstraints(lc)
        self.Layout()

        self.GetDefaultItem().SetFocus()

        # from wxWindows docs: This function (wxWindow::OnCharHook) is
        # only relevant to top-level windows (frames and dialogs), and
        # under Windows only. Under GTK the normal EVT_CHAR_ event has
        # the functionality, i.e. you can intercepts it and if you
        # don't call wxEvent::Skip the window won't get the event.

        if sys.platform not in ["windows","nt"]:
            wx.EVT_CHAR_HOOK(self,self.OnCharHook)
        else:
            wx.EVT_CHAR(self,self.OnCharHook)

    def OnLinkClick(self, event):
        clicked = event.linkinfo[0]
        self.gotoInternetUrl(clicked)

    def gotoInternetUrl(self, url):
        try:
            import webbrowser
        except ImportError:
            iTradeInformation(message('about_url') % url)
        else:
            webbrowser.open(url)

    def OnCharHook(self,event):
        if event.KeyCode in (wx.WXK_RETURN,wx.WXK_SPACE) :
            for id in (wx.ID_YES,wx.ID_NO,wx.ID_OK):
                wnd = self.m_html.FindWindowById(id)
                if wnd:
                    tlw = wx.GetTopLevelParent(wnd)
                    if tlw.GetDefaultItem()==wnd:
                        wnd.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED,id))
                        break

        elif event.KeyCode == wx.WXK_ESCAPE:
            if self.m_html.FindWindowById(wx.ID_CANCEL):
                self.m_html.FindWindowById(wx.ID_CANCEL).ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED,wx.ID_CANCEL))
            else:
                if self.IsModal() == False:
                    self.Show(False)
                else:
                    self.EndModal(wx.ID_CANCEL)
        else:
            event.Skip()

    DefaultHTML = '''\
            <html>
            <body %s %s>
            <center>
            <table cellpadding="5" bgcolor="%s" width="100%%">
              <tr>
                %s
                <td align="center">
                %s
                </td>
              </tr>
            </table>
            <p>%s</p>
            </body>
            </html>
            '''

    ImageHTML='''\
        <td align="left">
          <a href="%s"><img src="%s" align=top width=%d
               height=%d alt="%s" border=0></a>
        </td>'''

    def SetContents(self,
                    name="",
                    buttons=OKButton(makedefault=1),
                    text="",
                    namefmt="<h1>%s</h1>",
                    betweenbuttons="&nbsp;",
                    link_regexp=re.compile("</a>",re.IGNORECASE),
                    defaultsize=(420, 380),
                    image = None,
                    imagedir = "res",
                    imageurl = "",
                    size = None,
                    fgcolor = None,
                    bgcolor = None,
                    boxcolor="#458154"):

        # always one button : OK
        if buttons is None:
            buttons = OKButton()

        # dialog name with format
        name = namefmt % name

        # some image ?
        if image:
            if not width:
                width = 100
            if not height:
                height = width
            imstr1 = self.ImageHTML % (imageurl,os.path.join(imagedir,image),width,height,"['%s']" % image)
        else:
            imstr1 = ""

        if (image and string.lower(image[-4:]) == '.gif'):
            wx.Image_AddHandler(wx.GIFHandler())
        if (image and string.lower(image[-4:]) == '.png'):
            wx.Image_AddHandler(wx.PNGHandler())

        imstr2 = ""
        ci = ""

        # colors
        if fgcolor is not None:
            colourstring1 = 'fgcolor="%s"' % fgcolor
        else:
            colourstring1 = ""

        if bgcolor is not None:
            colourstring2 = 'bgcolor="%s"' % bgcolor
        else:
            colourstring2 = ""

        # buttons
        self.registerButtons(buttons)
        buttonstring = HTMLforButtons(buttons,betweenbuttons=betweenbuttons)

        # set final content
        self.theHTMLpage = (self.DefaultHTML
                            % (colourstring1,colourstring2,
                               boxcolor,
                               imstr1,
                               text,
                               buttonstring)
                             )

        self.m_html.SetPage(self.theHTMLpage)

        # size
        #if size is None:
        #    # now try to `shrink' dialog, only so far as no scrollbar nec.,,
        #    # mantaining aspect ratio of display.
        #    w = 320
        #    ds = wx.DisplaySize()
        #    c = self.m_html.GetInternalRepresentation()
        #    while w < ds[0]:
        #        c.Layout(w)
        #        if c.GetHeight() < (w+20) * ds[1]/ds[0] - 50:
        #            self.m_html.SetSize(wx.Size(w,int ((w) * ds[1]/ds[0])))
        #            self.SetSize(wx.Size(w+20,int ((w+0) * ds[1]/ds[0])))
        #            break
        #        w = w + 20
        #    else:
        #        self.SetSize(wx.Size(defaultsize))
        #        self.m_html.SetSize(wx.Size (map(operator.sub,defaultsize,(10,10))))
        #else:
        #    self.SetSize(wx.Size(size))
        #    self.m_html.SetSize(wx.Size (map(operator.sub,size,(10,10))))

        if size is None:
            w,h = defaultsize
        else:
            w,h = size

        c = self.m_html.GetInternalRepresentation()
        c.Layout(w-10)
        self.SetSize(wx.Size(c.GetWidth()+10,c.GetHeight()+45))

        # layout everything
        self.Layout()
        self.CentreOnParent(wx.BOTH)

    def registerButtons(self,buttons):
        for button in buttons:
            label,id,default = button
            wx.EVT_BUTTON(self, int(id), self.OnButton)

    def OnButton(self,event):
        if self.Validate() and self.TransferDataFromWindow():
            if self.IsModal():
                self.EndModal(event.GetId())
            else:
                self.SetReturnCode(event.GetId());
                self.Show(False)

# ============================================================================
# iTradeInformation()
#
#   parent          Parent window
#   text            Message to show on the dialog
#   caption         The dialog caption
# use : wxOK + wxICON_INFORMATION
# ============================================================================

def iTradeInformation(parent,text,caption=message('info_caption')):
    dlg = HTMLDialog(parent=parent,caption=caption,text=text,buttons=OKButton(makedefault=1))
    idRet = dlg.ShowModal()
    dlg.Destroy()
    return idRet

# ============================================================================
# iTradeError()
#
#   parent          Parent window
#   text            Message to show on the dialog
#   caption         The dialog caption
# use : wxOK + wxICON_ERROR
# ============================================================================

def iTradeError(parent,text,caption=message('alert_caption')):
    dlg = HTMLDialog(parent=parent,caption=caption,text=text,buttons=OKButton(makedefault=1))
    idRet = dlg.ShowModal()
    dlg.Destroy()
    return idRet

# ============================================================================
# iTradeYesNo()
#
#   parent          Parent window
#   text            Message to show on the dialog
#   caption         The dialog caption
#   bCanCancel      yes/no
#   bYesDefault     yes/no
# use : wxYES_NO + { wxCANCEL) + wxICON_QUESTION
# ============================================================================

def iTradeYesNo(parent,text,caption,bCanCancel=False,bYesDefault=True):
    buttons = YesButton(makedefault=bYesDefault)+NoButton(makedefault=not bYesDefault)
    if bCanCancel:
        buttons = buttons+CancelButton(makedefault=0)
    dlg = HTMLDialog(parent=parent,caption=caption,text=text,buttons=buttons)

    idRet = dlg.ShowModal()
    dlg.Destroy()
    return idRet

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    app = wx.PySimpleApp()

    iRet = iTradeYesNo(None,"message","caption")
    if iRet == wx.ID_YES:
        iRet = iTradeYesNo(None,"message","caption",bCanCancel=True,bYesDefault=False)
        if iRet == wx.ID_YES:
            iTradeInformation(None,"confirmation message")
        elif iRet == wx.ID_NO:
            iTradeInformation(None,"unconfirmation message")
        else:
            iTradeInformation(None,"cancellation message")
    else:
        iTradeError(None,"test aborted message")

# ============================================================================
# That's all folks !
# ============================================================================
