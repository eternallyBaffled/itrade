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
# Portions created by the Initial Developer are Copyright (C) 2004-2008 the
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
# 2005-10-26    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from __future__ import absolute_import
import logging
import re
import os
import sys

# itrade system
from itrade_logging import setLevel
from itrade_local import message
import itrade_config
from six.moves import map

# wxPython system
if not itrade_config.nowxversion:
    import itrade_wxversion
import wx
import wx.html
import wx.lib.wxpTag
# import sized_controls from wx.lib for wxPython version >= 2.8.8.0 (from wxaddons otherwise)
import wx.lib.sized_controls as sc

# matplotlib helpers
from matplotlib.colors import colorConverter

# iTrade wxpython
from itrade_wxhtml import wxUrlClickHtmlWindow, EVT_HTML_URL_CLICK


def matplot_color_to_wxcolor(colorname='k'):
    """
    convert a MatplotColor to an RGB tuple used by wxPython

         b  : blue
         g  : green
         r  : red
         c  : cyan
         m  : magenta
         y  : yellow
         k  : black
         w  : white

    For a greater range of colors, you have two options.  You can specify
    the color using an html hex string, as in

        color = '#eeefff'

    or you can pass an R,G,B tuple, where each of R,G,B are in the range
    [0,1].

    Finally, legal html names for colors, like 'red', 'burlywood' and
    'chartreuse' are supported.

    :param colorname:
    :return: The corresponding wxColour object.
    """
    r, g, b = colorConverter.to_rgb(colorname)

    return wx.Colour(int(r*255), int(g*255), int(b*255))

# ============================================================================
# FontFromSize
#   1 : small
#   2 : regular
#   3 : big
#
# Porting note : adjust this function to the platform ?? __x
# ============================================================================

def FontFromSize(size):
    if size == 2:
        return wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
    elif size == 3:
        return wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
    else:
        return wx.Font(7, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

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

def Button(label, id, makedefault=0):
    return [(label, id, makedefault)]

def OKButton(makedefault=1):
    return Button(label=message('ok'), id=wx.ID_OK, makedefault=makedefault)

def CancelButton(makedefault=0):
    return Button(label=message('cancel'), id=wx.ID_CANCEL, makedefault=makedefault)

def ApplyButton(makedefault=0):
    return Button(label=message('valid'), id=wx.ID_APPLY, makedefault=makedefault)

def YesButton(makedefault=1):
    return Button(label=message('yes'), id=wx.ID_YES, makedefault=makedefault)

def NoButton(makedefault=0):
    return Button(label=message('no'), id=wx.ID_NO, makedefault=makedefault)

# ============================================================================
# generate HTML for buttons
# ============================================================================


def _tupn(tup, n):
    if isinstance(tup, tuple):
        try:
            return tup[n]
        except IndexError:
            return None
    else:
        if n == 0:
            return tup
        else:
            return None


class Default_wxButton(wx.Button):
    def __init__(self, *args, **kwargs):
        wx.Button.__init__(self, *args, **kwargs)
        self.SetDefault()


DefaultButtonString = u'''
<wxp class="{}" module="{}">
    <param name="label" value="{}">
    <param name="id"    value="{}">
</wxp>'''


def HTMLforSingleButton(label, id=None, makedefault=0):
    if id is None:
        return label
    else:
        if makedefault == 1:
            defaultstring1 = "Default_wxButton"
            defaultstring2 = "itrade_wxutil"
        else:
            defaultstring1 = "Button"
            defaultstring2 = "wx"
        return DefaultButtonString.format(defaultstring1, defaultstring2, label, id)


def HTMLforButtons(buttons, betweenbuttons=""):
    def rn(n):
        return lambda tup, n=n: _tupn(tup, n)
    return betweenbuttons.join(map(HTMLforSingleButton, list(map(rn(0), buttons)), list(map(rn(1), buttons)), list(map(rn(2), buttons))))

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
#                     namefmt="<h1>{}</h1>",
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
#                   buttons=OKButton(makedefault=1) +
#                           CancelButton () +
#                           ApplyButton () +
#                           [" or be <i>brave</i> and "] +
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
                 *args, **kwargs):

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
        wx.Dialog.__init__(self, parent=parent, id=wx.ID_ANY, title=caption, size=size, style=wx.TAB_TRAVERSAL|wx.DEFAULT_DIALOG_STYLE, *args, **kwargs)

        # container
        self.m_html = wxUrlClickHtmlWindow(self, id=wx.ID_ANY, style=wx.CLIP_CHILDREN | wx.html.HW_SCROLLBAR_NEVER | wx.TAB_TRAVERSAL)
        EVT_HTML_URL_CLICK(self.m_html, self.OnLinkClick)

        # set the content
        self.SetContents(*(), **kwargs)

        # layout the content
        self.SetAutoLayout(autoLayout=True)

        lc = wx.LayoutConstraints()
        lc.top.SameAs(self, wx.Top, 5)
        lc.left.SameAs(self, wx.Left, 5)
        lc.bottom.SameAs(self, wx.Bottom, 5)
        lc.right.SameAs(self, wx.Right, 5)
        self.m_html.SetConstraints(constraints=lc)
        self.Layout()

        self.GetDefaultItem().SetFocus()

        # from wxWindows docs: This function (wxWindow::OnCharHook) is
        # only relevant to top-level windows (frames and dialogs), and
        # under Windows only. Under GTK the normal EVT_CHAR_ event has
        # the functionality, i.e. you can intercept it and if you
        # don't call wxEvent::Skip the window won't get the event.

        if sys.platform not in ["windows", "nt"]:
            wx.EVT_CHAR_HOOK(self, self.OnCharHook)
        else:
            wx.EVT_CHAR(self, self.OnCharHook)

    def OnLinkClick(self, event):
        clicked = event.linkinfo[0]
        self.gotoInternetUrl(clicked)

    def gotoInternetUrl(self, url):
        try:
            import webbrowser
        except ImportError:
            iTradeInformation(parent=self, text=message('about_url').format(url))
        else:
            webbrowser.open(url)

    def OnCharHook(self, event):
        if event.KeyCode in (wx.WXK_RETURN, wx.WXK_SPACE):
            for id in (wx.ID_YES, wx.ID_NO, wx.ID_OK):
                wnd = self.m_html.FindWindowById(id)
                if wnd:
                    tlw = wx.GetTopLevelParent(wnd)
                    if tlw.GetDefaultItem() == wnd:
                        wnd.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, id))
                        break

        elif event.KeyCode == wx.WXK_ESCAPE:
            if self.m_html.FindWindowById(wx.ID_CANCEL):
                self.m_html.FindWindowById(wx.ID_CANCEL).ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, wx.ID_CANCEL))
            else:
                if self.IsModal():
                    self.EndModal(wx.ID_CANCEL)
                else:
                    self.Show(show=False)
        else:
            event.Skip()

    DefaultHTML = u'''
            <html>
            <body {} {}>
            <center>
            <table cellpadding="5" bgcolor="{}" width="100%%">
              <tr>
                <td align="left">
                {}
                {}
                </td>
              </tr>
            </table>
            <p>{}</p>
            </body>
            </html>
            '''

    ImageHTML = u'''
          <a href="{}"><img src="{}" align=top alt="{}" border=0></a>&nbsp;
            '''

    def SetContents(self,
                    name="",
                    buttons=None,
                    text="",
                    namefmt="<h1>{}</h1>",
                    betweenbuttons="&nbsp;",
                    link_regexp=re.compile("</a>", re.IGNORECASE),
                    defaultsize=(420, 380),
                    image=None,
                    imagedir="res",
                    imageurl="",
                    size=None,
                    fgcolor="#000000",
                    bgcolor="#EEEEEE",
                    boxcolor="#EEEEEE"):

        # always one button : OK
        if buttons is None:
            buttons = OKButton(makedefault=1)

        # dialog name with format
        name = namefmt.format(name)

        # some image ?
        if image:
            imstr1 = self.ImageHTML.format(imageurl, os.path.join(imagedir, image), u"['{}']".format(image))
        else:
            imstr1 = ""

        # colors
        if fgcolor is not None:
            colourstring1 = u'fgcolor="{}"'.format(fgcolor)
        else:
            colourstring1 = ""

        if bgcolor is not None:
            colourstring2 = u'bgcolor="{}"'.format(bgcolor)
        else:
            colourstring2 = ""

        # buttons
        self.registerButtons(buttons)
        buttonstring = HTMLforButtons(buttons, betweenbuttons=betweenbuttons)

        # set final content
        the_html_page = (self.DefaultHTML.format(colourstring1, colourstring2,
                                                 boxcolor,
                                                 imstr1,
                                                 text,
                                                 buttonstring)
                        )

        self.m_html.SetPage(the_html_page)

        if size is None:
            w, h = defaultsize
        else:
            w, h = size

        c = self.m_html.GetInternalRepresentation()
        c.Layout(w-10)
        self.SetSize(size=(c.GetWidth()+10, c.GetHeight()+35))

        # layout everything
        self.Layout()
        self.CentreOnParent(wx.BOTH)

    def registerButtons(self, buttons):
        for button in buttons:
            label, id, default = button
            wx.EVT_BUTTON(self, int(id), self.OnButton)

    def OnButton(self, event):
        if self.Validate() and self.TransferDataFromWindow():
            if self.IsModal():
                self.EndModal(event.GetId())
            else:
                self.SetReturnCode(returnCode=event.GetId())
                self.Show(show=False)


class iTradeSizedDialog(sc.SizedDialog):
    def __init__(self, *args, **kwargs):
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        pre.Create(*args, **kwargs)
        self.PostCreate(pre)

        self.borderLen = 12
        self.mainPanel = sc.SizedPanel(self, id=wx.ID_ANY)

        mysizer = wx.BoxSizer(wx.VERTICAL)
        mysizer.Add(self.mainPanel, 1, wx.EXPAND | wx.ALL, self.GetDialogBorder())
        self.SetSizer(sizer=mysizer)

        self.SetAutoLayout(autoLayout=True)

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
    def __init__(self, parent, caption, text, size=(420, 380), style=wx.OK | wx.YES_DEFAULT):
        iTradeSizedDialog.__init__(self, parent, wx.ID_ANY, caption, size=size, style=wx.DEFAULT_DIALOG_STYLE)

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
        pane = sc.SizedPanel(container, wx.ID_ANY)
        pane.SetSizerType("horizontal")
        pane.SetSizerProps(expand=True)

        if image:
            image = wx.Bitmap(image)
            if image:
                bmp = wx.StaticBitmap(parent=pane, id=wx.ID_ANY, bitmap=image)
                bmp.SetSizerProps(valign='center')

        if len(text) > 96:
            h = 48
        else:
            h = 32
        txt = wx.StaticText(parent=pane, id=wx.ID_ANY, label=text, size=(260,h))
        txt.SetFont(font=wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        txt.SetSizerProps(expand=True, valign='center', halign='center')

        # Last Row : OK, ..., Cancel
        btnpane = sc.SizedPanel(container, wx.ID_ANY)
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
            btn.SetHelpText(text=message('ok_desc'))
            wx.EVT_BUTTON(self, wx.ID_OK, self.OnOK)

        # YES
        if style & wx.YES == wx.YES:
            btn = wx.Button(btnpane, wx.ID_YES, message('yes'))
            if style & wx.YES_DEFAULT == wx.YES_DEFAULT:
                btn.SetDefault()
            #btn.SetHelpText(message('yes_desc'))
            wx.EVT_BUTTON(self, wx.ID_YES, self.OnYES)

        # NO
        if style & wx.NO == wx.NO:
            btn = wx.Button(btnpane, wx.ID_NO, message('no'))
            if style & wx.NO_DEFAULT == wx.NO_DEFAULT:
                btn.SetDefault()
            #btn.SetHelpText(message('no_desc'))
            wx.EVT_BUTTON(self, wx.ID_NO, self.OnNO)

        # CANCEL
        if style & wx.CANCEL == wx.CANCEL:
            btn = wx.Button(parent=btnpane, id=wx.ID_CANCEL, label=message('cancel'))
            btn.SetHelpText(text=message('cancel_desc'))
            wx.EVT_BUTTON(self, wx.ID_CANCEL, self.OnCancel)

        # a little trick to make sure that you can't resize the dialog to
        # less screen space than the controls need
        self.Fit()
        self.SetMinSize(minSize=self.GetSize())

    def OnOK(self, evt):
        self.EndModal(wx.ID_OK)

    def OnYES(self, evt):
        self.EndModal(wx.ID_YES)

    def OnNO(self, evt):
        self.EndModal(wx.ID_NO)

    def OnCancel(self, evt):
        self.EndModal(wx.ID_CANCEL)

# ============================================================================
# iTradeInformation()
#
#   parent          Parent window
#   text            Message to show on the dialog
#   caption         The dialog caption
# use : wxOK + wxICON_INFORMATION
# ============================================================================


def iTradeInformation(parent, text, caption=message('info_caption')):
    #dlg = HTMLDialog(parent=parent, caption=caption, text=text, buttons=OKButton(makedefault=1), image="box_info.png")
    with iTradeDialog(parent=parent, caption=caption, text=text, style=wx.OK|wx.ICON_INFORMATION) as dlg:
        idRet = dlg.CentreOnParent()
        idRet = dlg.ShowModal()
    return idRet

# ============================================================================
# iTradeError()
#
#   parent          Parent window
#   text            Message to show on the dialog
#   caption         The dialog caption
# use : wxOK + wxICON_ERROR
# ============================================================================

def iTradeError(parent, text, caption=message('alert_caption')):
    #dlg = HTMLDialog(parent=parent, caption=caption, text=text, buttons=OKButton(makedefault=1), image="box_alert.png")
    with iTradeDialog(parent=parent, caption=caption, text=text, style=wx.OK|wx.ICON_ERROR) as dlg:
        idRet = dlg.CentreOnParent()
        idRet = dlg.ShowModal()
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


def iTradeYesNo(parent, text, caption, bCanCancel=False, bYesDefault=True):
    #buttons = YesButton(makedefault=bYesDefault)+NoButton(makedefault=not bYesDefault)
    #if bCanCancel:
    #    buttons = buttons+CancelButton(makedefault=0)
    #dlg = HTMLDialog(parent=parent, caption=caption, text=text, buttons=buttons, image="box_yesno.png")

    style = wx.YES_NO | wx.ICON_QUESTION
    if bCanCancel:
        style = style | wx.CANCEL
    if bYesDefault:
        style = style | wx.YES_DEFAULT
    else:
        style = style | wx.NO_DEFAULT

    with iTradeDialog(parent=parent, caption=caption, text=text, style=style) as dlg:
        idRet = dlg.CentreOnParent()
        idRet = dlg.ShowModal()
    return idRet

# ============================================================================
# Test me
# ============================================================================


def main():
    setLevel(logging.INFO)
    app = wx.App(False)
    iRet = iTradeYesNo(None, "message without cancel and default to Yes", "caption")
    if iRet == wx.ID_YES:
        iRet = iTradeYesNo(None, "message with cancel and default to No", "caption", bCanCancel=True, bYesDefault=False)
        if iRet == wx.ID_YES:
            iTradeInformation(None, message('portfolio_exist_info').format("message with some accents in French ... àéè"))
        elif iRet == wx.ID_NO:
            iTradeInformation(None, "unconfirmation message")
        else:
            iTradeInformation(None,
                              "cancellation message .............................. very long ........................... message ........... at least three (3) lines !!!!!!!!!!!")
    else:
        iTradeError(None, "test aborted message")


if __name__ == '__main__':
    main()

# ============================================================================
# That's all folks !
# ============================================================================
