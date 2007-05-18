#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
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
import wxaddons.sized_controls as sc

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
        self.m_html = wxUrlClickHtmlWindow(self, -1, style = wx.CLIP_CHILDREN | wx.html.HW_SCROLLBAR_NEVER | wx.TAB_TRAVERSAL)
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
                <td align="left">
                %s
                %s
                </td>
              </tr>
            </table>
            <p>%s</p>
            </body>
            </html>
            '''

    ImageHTML='''\
          <a href="%s"><img src="%s" align=top alt="%s" border=0></a>&nbsp;
            '''

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
                    fgcolor = "#000000",
                    bgcolor = "#EEEEEE",
                    boxcolor= "#EEEEEE"):

        # always one button : OK
        if buttons is None:
            buttons = OKButton()

        # dialog name with format
        name = namefmt % name

        # some image ?
        if image:
            imstr1 = self.ImageHTML % (imageurl,os.path.join(imagedir,image),"['%s']" % image)
        else:
            imstr1 = ""

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

        if size is None:
            w,h = defaultsize
        else:
            w,h = size

        c = self.m_html.GetInternalRepresentation()
        c.Layout(w-10)
        self.SetSize(wx.Size(c.GetWidth()+10,c.GetHeight()+35))

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
# iTradeSizedDialog
# ============================================================================

class iTradeSizedDialog(sc.SizedDialog):
    def __init__(self, *args, **kwargs):
        # context help
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        pre.Create(*args, **kwargs)
        self.PostCreate(pre)

        self.borderLen = 12
        self.mainPanel = sc.SizedPanel(self, -1)

        mysizer = wx.BoxSizer(wx.VERTICAL)
        mysizer.Add(self.mainPanel, 1, wx.EXPAND | wx.ALL, self.GetDialogBorder())
        self.SetSizer(mysizer)

        self.SetAutoLayout(True)

# ============================================================================
# iTradeDialog()
#
#   style
#       wx.OK
#       or wx.YES_NO
#
#       wx.YES_DEFAULT
#       wx.NO_DEFAULT
#
#       wx.HELP
#
#       wx.CANCEL
#
#       wx.ICON_INFORMATION
#       or wx.ICON_ERROR
#       or wx.ICON_QUESTION
# ============================================================================

class iTradeDialog(iTradeSizedDialog):
    def __init__(self,parent,caption,text,size=(420, 380),style=wx.OK | wx.YES_DEFAULT):
        iTradeSizedDialog.__init__(self,parent,-1,caption,size,style=wx.DEFAULT_DIALOG_STYLE)

        image = None
        if style & wx.ICON_INFORMATION == wx.ICON_INFORMATION:
            image = os.path.join(itrade_config.dirRes, "box_info.png")
        if style & wx.ICON_ERROR == wx.ICON_ERROR:
            image = os.path.join(itrade_config.dirRes, "box_alert.png")
        if style & wx.ICON_QUESTION == wx.ICON_QUESTION:
            image = os.path.join(itrade_config.dirRes, "box_yesno.png")

        # container
        container = self.GetContentsPane()
        container.SetSizerType("vertical")

        # First Row : image + text
        pane = sc.SizedPanel(container, -1)
        pane.SetSizerType("horizontal")
        pane.SetSizerProps(expand=True)

        if image:
            image = wx.Bitmap(image)
            if image:
                bmp = wx.StaticBitmap(pane, -1, image)
                bmp.SetSizerProps(valign='center')

        if len(text)>96:
            h = 48
        else:
            h = 32
        txt = wx.StaticText(pane, -1, text, size=(260,h))
        txt.SetSizerProps(expand=True,valign='center',halign='center')

        # Last Row : OK, ..., Cancel
        btnpane = sc.SizedPanel(container, -1)
        btnpane.SetSizerType("horizontal")
        btnpane.SetSizerProps(halign='center')

        # context help
        if style & wx.HELP == wx.HELP:
            if wx.Platform != "__WXMSW__":
                btn = wx.ContextHelpButton(btnpane)

        # OK
        if style & wx.OK == wx.OK:
            btn = wx.Button(btnpane, wx.ID_OK, message('ok'))
            btn.SetDefault()
            btn.SetHelpText(message('ok_desc'))
            wx.EVT_BUTTON(self, wx.ID_OK, self.OnOK)

        # YES
        if style & wx.YES == wx.YES:
            btn = wx.Button(btnpane, wx.ID_YES, message('yes'))
            if style & wx.YES_DEFAULT == wx.YES_DEFAULT: btn.SetDefault()
            #btn.SetHelpText(message('yes_desc'))
            wx.EVT_BUTTON(self, wx.ID_YES, self.OnYES)

        # NO
        if style & wx.NO == wx.NO:
            btn = wx.Button(btnpane, wx.ID_NO, message('no'))
            if style & wx.NO_DEFAULT == wx.NO_DEFAULT: btn.SetDefault()
            #btn.SetHelpText(message('no_desc'))
            wx.EVT_BUTTON(self, wx.ID_NO, self.OnNO)

        # CANCEL
        if style & wx.CANCEL == wx.CANCEL:
            btn = wx.Button(btnpane, wx.ID_CANCEL, message('cancel'))
            btn.SetHelpText(message('cancel_desc'))
            wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)

        # a little trick to make sure that you can't resize the dialog to
        # less screen space than the controls need
        self.Fit()
        self.SetMinSize(self.GetSize())

    def OnOK(self,evt):
        self.EndModal(wx.ID_OK)

    def OnYES(self,evt):
        self.EndModal(wx.ID_YES)

    def OnNO(self,evt):
        self.EndModal(wx.ID_NO)

    def OnCancel(self,evt):
        self.EndModal(wx.ID_CANCEL)

# ============================================================================
# iTradeInformation()
#
#   parent          Parent window
#   text            Message to show on the dialog
#   caption         The dialog caption
# use : wxOK + wxICON_INFORMATION
# ============================================================================

def iTradeInformation(parent,text,caption=message('info_caption')):
    #dlg = HTMLDialog(parent=parent,caption=caption,text=text,buttons=OKButton(makedefault=1),image="box_info.png")
    dlg = iTradeDialog(parent=parent,caption=caption,text=text,style=wx.OK|wx.ICON_INFORMATION)
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
    #dlg = HTMLDialog(parent=parent,caption=caption,text=text,buttons=OKButton(makedefault=1),image="box_alert.png")
    dlg = iTradeDialog(parent=parent,caption=caption,text=text,style=wx.OK|wx.ICON_ERROR)
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
    #buttons = YesButton(makedefault=bYesDefault)+NoButton(makedefault=not bYesDefault)
    #if bCanCancel:
    #    buttons = buttons+CancelButton(makedefault=0)
    #dlg = HTMLDialog(parent=parent,caption=caption,text=text,buttons=buttons,image="box_yesno.png")

    style = wx.YES_NO | wx.ICON_QUESTION
    if bCanCancel:
        style = style | wx.CANCEL
    if bYesDefault:
        style = style | wx.YES_DEFAULT
    else:
        style = style | wx.NO_DEFAULT

    dlg = iTradeDialog(parent=parent,caption=caption,text=text,style=style)
    idRet = dlg.ShowModal()
    dlg.Destroy()
    return idRet

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    app = wx.PySimpleApp()

    iRet = iTradeYesNo(None,"message without cancel and default to Yes","caption")
    if iRet == wx.ID_YES:
        iRet = iTradeYesNo(None,"message with cancel and default to No","caption",bCanCancel=True,bYesDefault=False)
        if iRet == wx.ID_YES:
            iTradeInformation(None,message('portfolio_exist_info')% "message with some accents in French ... àéè")
        elif iRet == wx.ID_NO:
            iTradeInformation(None,"unconfirmation message")
        else:
            iTradeInformation(None,"cancellation message .............................. very long ........................... message ........... at least three (3) lines !!!!!!!!!!!")
    else:
        iTradeError(None,"test aborted message")

# ============================================================================
# That's all folks !
# ============================================================================
