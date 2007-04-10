#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxabout.py
#
# Description: wxPython About box
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is	Gilles Dumortier.
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
# 2005-04-02    dgil  Wrote it from scratch
# 2007-01-29    dgil  Use Boa inspired code to have a better About Box
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging

# wxPython system
import itrade_wxversion
import wx
import wx.html
import wx.lib.wxpTag

# iTrade system
from itrade_logging import *
from itrade_local import message
from itrade_wxhtml import wxUrlClickHtmlWindow,EVT_HTML_URL_CLICK

# ============================================================================
# about_html
# ============================================================================

about_html = '''
<html>
<body bgcolor="#C5C1C4">
<center>
<table cellpadding="5" bgcolor="#FFFFFF" width="100%%">
  <tr>
    <td align="center">
      <br><img src="%s"><br>
      <font color="#006600" size="+4"><b>iTrade</b></font><br>
      <strong>%s %s - %s</strong>
      %s
    </td>
  </tr>
</table>
%s
</body>
</html>
'''

about_text = '''
<p>Trading and Charting software written in <b>Python</b> and <b>wxPython</b>
</p>
<p><a href="iTrade">%s</a><br><br>
<b>&copy; %s</b> and <a href="Authors">Authors</a> (<a href="Mail">dgil@ieee.org</a>)<br><br>
<a href="Credits">Credits</a>
</p>

<p>This pre-alpha software shows off some of the capabilities
of <b>iTrade</b>.  Select items from the menu or list control,
sit back and enjoy.  Be sure to take a peek at the source code for each
demo item so you can learn how to help us on this project.
</p>
<p>
<font size="-1"><b>iTrade</b> is published under the terms of the %s license.
Please see <i><a href="LICENSE">LICENSE</a></i> file for more information.</font>
</p>

<hr>
<wxp module="wx" class="Button">
  <param name="label" value="Okay">
  <param name="id"    value="ID_OK">
</wxp>
</center>
'''

# ============================================================================
# credits_html
# ============================================================================

credits_html = '''
<html>
<body bgcolor="#4488FF">
<center>
<table bgcolor="#FFFFFF" width="100%%">
  <tr>
    <td align="center"><h3>Credits</h3>

<p><b>the iTrade Team</b><br>
<p>Gilles Dumortier (dgil@ieee.org) : Lead Developer</p>
<p>Michel Legrand (ml.legrand@free.fr) : Testing & Docs</p>
<br>
<p><b>Many thanks to</b><br>
<p>Peter Mills (peter_m_mills@bigpond.com) : ASE</p>
<p>Olivier Jacq (olivier.jacq@online.fr) : Linux feedback & Docs</p>
<br>
<p><b>Translations</b><br>
<p>Catherine Pedrosa and Guilherme (guigui) : Portuguese</p>
<br>
<p><b>iTrade is built on:</b><br>
<a href="Python">Python</a>&nbsp;
<a href="wxPython">wxPython</a>&nbsp;
<a href="NumPy">NumPy</a>&nbsp;
<a href="Matplotlib">Matplotlib</a>&nbsp;
</p>
<p>
<a href="Back">Back</a><br>
    </td>
  </tr>
</table>
</body>
</html>
'''

# ============================================================================
# license_html
# ============================================================================

license_html = '''
<html>
<body bgcolor="#4488FF">
<center>
<table bgcolor="#FFFFFF" width="100%%">
  <tr>
    <td align="left">
      <p>
      <a href="Back">Back</a>
        <br><br>
      <font size="-2">
               %s
      </font>
      <p>
      <a href="Back">Back</a><br>
    </td>
  </tr>
</table>
</body>
</html>
'''

# ============================================================================
# About box
# ============================================================================

wxID_ABOUTBOX = wx.NewId()

class iTradeAboutBox(wx.Dialog):

    border = 7

    def __init__(self, prnt):
        wx.Dialog.__init__(self, size=wx.Size(480, 525), pos=(-1, -1),
              id = wxID_ABOUTBOX, title = message('about_title'), parent=prnt,
              name = 'AboutBox', style = wx.DEFAULT_DIALOG_STYLE)

        self.blackback = wx.Window(self, -1, pos=(0, 0),
              size=self.GetClientSize(), style=wx.CLIP_CHILDREN)
        self.blackback.SetBackgroundColour(wx.BLACK)

        self.m_html = wxUrlClickHtmlWindow(self.blackback, -1, style = wx.CLIP_CHILDREN | wx.html.HW_NO_SELECTION)
        EVT_HTML_URL_CLICK(self.m_html, self.OnLinkClick)

        self.setPage()
        self.blackback.SetAutoLayout(True)

        # adjust constraints
        lc = wx.LayoutConstraints()
        lc.top.SameAs(self.blackback, wx.Top, self.border)
        lc.left.SameAs(self.blackback, wx.Left, self.border)
        lc.bottom.SameAs(self.blackback, wx.Bottom, self.border)
        lc.right.SameAs(self.blackback, wx.Right, self.border)
        self.m_html.SetConstraints(lc)

        # layout everything
        self.blackback.Layout()
        self.Center(wx.BOTH)

        #
        self.SetAcceleratorTable(wx.AcceleratorTable([(0, wx.WXK_ESCAPE, wx.ID_OK)]))

    def gotoInternetUrl(self, url):
        try:
            import webbrowser
        except ImportError:
            wx.MessageBox(message('about_url') % url)
        else:
            webbrowser.open(url)

    def OnLinkClick(self, event):
        clicked = event.linkinfo[0]
        if clicked == 'Credits':
            self.m_html.SetPage(credits_html)
        elif clicked == 'Back':
            self.setPage()
        elif clicked == 'iTrade':
            self.gotoInternetUrl(itrade_config.softwareWebsite)
        elif clicked == 'Authors':
            self.gotoInternetUrl(itrade_config.softwareWebsite+'contact.htm')
        elif clicked == 'Python':
            self.gotoInternetUrl('http://www.python.org')
        elif clicked == 'wxPython':
            self.gotoInternetUrl('http://wxpython.org')
        elif clicked == 'NumPy':
            self.gotoInternetUrl('http://numpy.sourceforge.net')
        elif clicked == 'Matplotlib':
            self.gotoInternetUrl('http://matplotlib.sourceforge.net')
        elif clicked == 'Mail':
            self.gotoInternetUrl('mailto:dgil@ieee.org')
        elif clicked == 'LICENSE':
            f = open('LICENSE','r')
            lines = f.readlines()
            s = ''
            for l in lines:
                s = s + l + '<br>'
            self.m_html.SetPage(license_html % s)
            f.close()

    def setPage(self):
        self.m_html.SetPage(about_html % (
              os.path.join(itrade_config.resDir, 'itrade.png'), itrade_config.softwareVersionName, itrade_config.softwareStatus, itrade_config.softwareVersion,
              '', about_text % (itrade_config.softwareWebsite, itrade_config.softwareCopyright,itrade_config.softwareLicense)
              ))

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    app = wx.PySimpleApp()
    dlg = iTradeAboutBox(None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()

# ============================================================================
# That's all folks !
# ============================================================================
