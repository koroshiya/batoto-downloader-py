#!/usr/bin/python2.7 -tt

import sys
if sys.version_info < (2, 7):
    raise "must use python 2.7 or greater"

import wx
import BatotoFrame

batoto = wx.App(False)

options = wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX
frame = wx.Frame(None, style=options)
f = BatotoFrame.BatotoFrame(frame);

batoto.MainLoop()