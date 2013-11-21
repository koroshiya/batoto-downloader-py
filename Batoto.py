#!/usr/bin/python2.7 -tt

import wx
import BatotoFrame

batoto = wx.App(False)

options = wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX
size = (500,400)
frame = wx.Frame(None, style=options, size=size)
f = BatotoFrame.BatotoFrame(frame);
f.SetMinSize((500,400))

batoto.MainLoop()