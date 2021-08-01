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
# 2007-01-27    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging

# iTrade system
import itrade_config
from itrade_logging import setLevel, info
from itrade_local import message,getLang

# wxPython system
if not itrade_config.nowxversion:
    import itrade_wxversion
import wx

# matplotlib system
from matplotlib.backends.backend_wx import RendererWx

# ============================================================================
# CanvasPrintout
# ============================================================================

class CanvasPrintout(wx.Printout):
    def __init__(self, canvas):
        wx.Printout.__init__(self,title='Graph')
        self.canvas = canvas

        # width, in inches of output figure (approximate)
        self.width  = 5
        self.margin = 0.2

    def HasPage(self, page):
        #current only supports 1 page print
        return page == 1

    def GetPageInfo(self):
        return (1, 1, 1, 1)

    def OnPrintPage(self, page):
        self.canvas.draw()

        dc        = self.GetDC()
        (ppw,pph) = self.GetPPIPrinter()      # printer's pixels per in
        (pgw,pgh) = self.GetPageSizePixels()  # page size in pixels
        (dcw,dch) = dc.GetSize()
        (grw,grh) = self.canvas.GetSizeTuple()

        # save current figure dpi resolution and bg color,
        # so that we can temporarily set them to the dpi of
        # the printer, and the bg color to white
        bgcolor   = self.canvas.figure.get_facecolor()
        fig_dpi   = self.canvas.figure.dpi.get()

        # draw the bitmap, scaled appropriately
        vscale    = float(ppw) / fig_dpi

        # set figure resolution,bg color for printer
        self.canvas.figure.dpi.set(ppw)
        self.canvas.figure.set_facecolor('#FFFFFF')

        renderer  = RendererWx(self.canvas.bitmap, self.canvas.figure.dpi)
        self.canvas.figure.draw(renderer)
        self.canvas.bitmap.SetWidth(  int(self.canvas.bitmap.GetWidth() * vscale))
        self.canvas.bitmap.SetHeight( int(self.canvas.bitmap.GetHeight()* vscale))
        self.canvas.draw()

        # page may need additional scaling on preview
        page_scale = 1.0
        if self.IsPreview():   page_scale = float(dcw)/pgw

        # get margin in pixels = (margin in in) * (pixels/in)
        top_margin  = int(self.margin * pph * page_scale)
        left_margin = int(self.margin * ppw * page_scale)

        # set scale so that width of output is self.width inches
        # (assuming grw is size of graph in inches....)
        user_scale = (self.width * fig_dpi * page_scale)/float(grw)

        dc.SetDeviceOrigin(left_margin,top_margin)
        dc.SetUserScale(user_scale,user_scale)

        # this cute little number avoid API inconsistencies in wx
        try:
            dc.DrawBitmap(self.canvas.bitmap, 0, 0)
        except:
            try:
                dc.DrawBitmap(self.canvas.bitmap, (0, 0))
            except:
                pass
        self.canvas.m_parent.drawAllObjects(dc)

        # restore original figure  resolution
        self.canvas.figure.set_facecolor(bgcolor)
        self.canvas.figure.dpi.set(fig_dpi)
        # __x self.canvas.m_parent.draw()
        return True

# ============================================================================

class MyPrintout(wx.Printout):
    def __init__(self, canvas):
        wx.Printout.__init__(self)
        self.m_canvas = canvas

    def OnBeginDocument(self, start, end):
        info("MyPrintout.OnBeginDocument\n")
        self.base_OnBeginDocument(start,end)

    def OnEndDocument(self):
        info("MyPrintout.OnEndDocument\n")
        self.base_OnEndDocument()

    def OnBeginPrinting(self):
        info("MyPrintout.OnBeginPrinting\n")
        self.base_OnBeginPrinting()

    def OnEndPrinting(self):
        info("MyPrintout.OnEndPrinting\n")
        self.base_OnEndPrinting()

    def OnPreparePrinting(self):
        info("MyPrintout.OnPreparePrinting\n")
        self.base_OnPreparePrinting()

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

        width,height = self.m_canvas.GetSizeTuple()
        maxX,maxY = width,height

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
        posX = (w - (width * actualScale)) / 2.0
        posY = (h - (height * actualScale)) / 2.0

        # Set the scale and origin
        dc.SetUserScale(actualScale, actualScale)
        dc.SetDeviceOrigin(int(posX), int(posY))

        #-------------------------------------------
        pandc = self.m_canvas.GetDC()
        sz = pandc.GetSizeTuple()
        dc.Blit(0,0, sz[0], sz[1], 0, 0, pandc)

        #dc.DrawText(message('print_page') % page, marginX/2, maxY-marginY)

        return True

# ============================================================================
# iTrade_wxPanelPrint
#
#   m_parent        parent panel or frame or window
#   m_pd            PrintData
# ============================================================================

class iTrade_wxPanelPrint(object):
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
        dlg.CentreOnParent()
        dlg.ShowModal()

        # this makes a copy of the wx.PrintData instead of just saving
        # a reference to the one inside the PrintDialogData that will
        # be destroyed when the dialog is destroyed
        self.m_pd = wx.PrintData( dlg.GetPageSetupData().GetPrintData() )

        dlg.Destroy()

    def OnPrintPreview(self, event):
        data = wx.PrintDialogData(self.m_pd)
        printout = self.m_po(self.m_canvas)
        printout2 = self.m_po(self.m_canvas)
        self.preview = wx.PrintPreview(printout, printout2, data)

        if not self.preview.Ok():
            info("Houston, we have a problem...\n")
            return

        # be sure to have a Frame object
        frameInst = self
        while not isinstance(frameInst, wx.Frame):
            frameInst = frameInst.GetParent()

        # create the Frame for previewing
        pfrm = wx.PreviewFrame(self.preview, frameInst, message('print_preview'))

        pfrm.Initialize()
        pfrm.SetPosition(self.m_parent.GetPosition())
        pfrm.SetSize(self.m_parent.GetSize())
        pfrm.Show(True)

    def OnDoPrint(self, event):
        pdd = wx.PrintDialogData(self.m_pd)
        pdd.SetToPage(2)
        printer = wx.Printer(pdd)
        printout = self.m_po(self.m_canvas)

        if not printer.Print(self.m_parent, printout, True):
            #wx.MessageBox(message('print_errprinting'), message('print_printing'), wx.OK)
            pass
        else:
            self.m_pd = wx.PrintData( printer.GetPrintDialogData().GetPrintData() )
        printout.Destroy()


# ============================================================================
# Test me
# ============================================================================

class MyTestPanel(wx.Panel,iTrade_wxPanelPrint):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, wx.DefaultPosition, wx.DefaultSize)
        iTrade_wxPanelPrint.__init__(self,parent,MyPrintout)

        self.box = wx.BoxSizer(wx.VERTICAL)

        from itrade_wxhtml import iTradeHtmlPanel
        self.m_canvas = iTradeHtmlPanel(self,wx.NewId(),"https://www.google.fr")
        self.m_canvas.paint0()
        self.box.Add(self.m_canvas, 1, wx.GROW)

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

if __name__ == '__main__':
    setLevel(logging.INFO)

    app = MyTestApp(0)
    app.MainLoop()

# ============================================================================
# That's all folks !
# ============================================================================
