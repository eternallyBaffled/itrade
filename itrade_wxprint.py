#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_wxprint.py
#
# Description: wxPython Printing Back-End
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
# 2007-01-27    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging

# wxPython system
import itrade_wxversion
import wx

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_local import message,getLang

# ============================================================================

class MyPrintout(wx.Printout):
    def __init__(self, canvas):
        wx.Printout.__init__(self)
        self.canvas = canvas

    def OnBeginDocument(self, start, end):
        info("MyPrintout.OnBeginDocument\n")
        return super(MyPrintout, self).OnBeginDocument(start, end)

    def OnEndDocument(self):
        info("MyPrintout.OnEndDocument\n")
        super(MyPrintout, self).OnEndDocument()

    def OnBeginPrinting(self):
        info("MyPrintout.OnBeginPrinting\n")
        super(MyPrintout, self).OnBeginPrinting()

    def OnEndPrinting(self):
        info("MyPrintout.OnEndPrinting\n")
        super(MyPrintout, self).OnEndPrinting()

    def OnPreparePrinting(self):
        info("MyPrintout.OnPreparePrinting\n")
        super(MyPrintout, self).OnPreparePrinting()

    def HasPage(self, page):
        info("MyPrintout.HasPage: %d\n" % page)
        if page <= 2:
            return True
        else:
            return False

    def GetPageInfo(self):
        info("MyPrintout.GetPageInfo\n")
        return (1, 2, 1, 2)

    def OnPrintPage(self, page):
        info("MyPrintout.OnPrintPage: %d\n" % page)
        dc = self.GetDC()

        #-------------------------------------------
        # One possible method of setting scaling factors...

        maxX = self.canvas.getWidth()
        maxY = self.canvas.getHeight()

        # Let's have at least 50 device units margin
        marginX = 50
        marginY = 50

        # Add the margin to the graphic size
        maxX = maxX + (2 * marginX)
        maxY = maxY + (2 * marginY)

        # Get the size of the DC in pixels
        (w, h) = dc.GetSizeTuple()

        # Calculate a suitable scaling factor
        scaleX = float(w) / maxX
        scaleY = float(h) / maxY

        # Use x or y scaling factor, whichever fits on the DC
        actualScale = min(scaleX, scaleY)

        # Calculate the position on the DC for centering the graphic
        posX = (w - (self.canvas.getWidth() * actualScale)) / 2.0
        posY = (h - (self.canvas.getHeight() * actualScale)) / 2.0

        # Set the scale and origin
        dc.SetUserScale(actualScale, actualScale)
        dc.SetDeviceOrigin(int(posX), int(posY))

        #-------------------------------------------

        self.canvas.DoDrawing(dc, True)
        dc.DrawText("Page: %d" % page, marginX/2, maxY-marginY)

        return True

# ============================================================================
# iTrade_wxPrintPanel
#
#   m_parent        parent panel or frame or window
#   m_pd            PrintData
# ============================================================================

class iTrade_wxPrintPanel(object):
    def __init__(self, parent , po, orientation = wx.PORTRAIT):
        self.m_parent = parent

        self.m_pd = wx.PrintData()
        if getLang()=='us':
            self.m_pd.SetPaperId(wx.PAPER_LETTER)
        else:
            self.m_pd.SetPaperId(wx.PAPER_A4)

        self.m_pd.SetOrientation(orientation)

        self.m_pd.SetPrintMode(wx.PRINT_MODE_PRINTER)

        self.m_po = po

    def OnPageSetup(self, evt):
        psdd = wx.PageSetupDialogData(self.m_pd)
        psdd.CalculatePaperSizeFromId()

        dlg = wx.PageSetupDialog(self, psdd)
        dlg.ShowModal()

        # this makes a copy of the wx.PrintData instead of just saving
        # a reference to the one inside the PrintDialogData that will
        # be destroyed when the dialog is destroyed
        self.m_pd = wx.PrintData( dlg.GetPageSetupData().GetPrintData() )

        dlg.Destroy()

    def OnPrintPreview(self, event):
        data = wx.PrintDialogData(self.m_pd)
        printout = self.m_po(self.canvas)
        printout2 = self.m_po(self.canvas)
        self.preview = wx.PrintPreview(printout, printout2, data)

        if not self.preview.Ok():
            info("Houston, we have a problem...\n")
            return

        pfrm = wx.PreviewFrame(self.preview, self.m_parent, "This is a print preview")

        pfrm.Initialize()
        pfrm.SetPosition(self.m_parent.GetPosition())
        pfrm.SetSize(self.m_parent.GetSize())
        pfrm.Show(True)

    def OnDoPrint(self, event):
        pdd = wx.PrintDialogData(m_pd)
        pdd.SetToPage(2)
        printer = wx.Printer(pdd)
        printout = self.m_po(self.canvas)

        if not printer.Print(self.m_parent, printout, True):
            wx.MessageBox("There was a problem printing.\nPerhaps your current printer is not set correctly?", "Printing", wx.OK)
        else:
            self.m_pd = wx.PrintData( printer.GetPrintDialogData().GetPrintData() )
        printout.Destroy()


# ============================================================================
# Test me
# ============================================================================

class MyTestPanel(wx.Panel,iTrade_wxPrintPanel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, wx.DefaultPosition, wx.DefaultSize)
        iTrade_wxPrintPanel.__init__(self,parent,MyPrintout)

        self.box = wx.BoxSizer(wx.VERTICAL)

        self.canvas = None#ScrolledWindow.MyCanvas(self)
        #self.box.Add(self.canvas, 1, wx.GROW)

        subbox = wx.BoxSizer(wx.HORIZONTAL)
        btn = wx.Button(self, -1, "Page Setup")
        self.Bind(wx.EVT_BUTTON, self.OnPageSetup, btn)
        subbox.Add(btn, 1, wx.GROW | wx.ALL, 2)

        btn = wx.Button(self, -1, "Print Preview")
        self.Bind(wx.EVT_BUTTON, self.OnPrintPreview, btn)
        subbox.Add(btn, 1, wx.GROW | wx.ALL, 2)

        btn = wx.Button(self, -1, "Print")
        self.Bind(wx.EVT_BUTTON, self.OnDoPrint, btn)
        subbox.Add(btn, 1, wx.GROW | wx.ALL, 2)

        self.box.Add(subbox, 0, wx.GROW)

        self.SetAutoLayout(True)
        self.SetSizer(self.box)

class MyTestFrame(wx.Frame):

    def __init__(self, parent, id):
        wx.Frame.__init__(self, parent, id, "iTrade Print and Preview Module", wx.Point(10,10), wx.Size(400, 400))
        self.panel = MyTestPanel(self)

        wx.EVT_CLOSE(self, self.OnCloseWindow)

    def OnCloseWindow(self, event):
        self.Destroy()

class MyTestApp(wx.App):

    def OnInit(self):
        frame = MyTestFrame(None, -1)
        frame.Show(True)
        self.SetTopWindow(frame)
        return True

if __name__=='__main__':
    setLevel(logging.INFO)

    app = MyTestApp(0)
    app.MainLoop()

# ============================================================================
# That's all folks !
# ============================================================================
