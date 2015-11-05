#!/usr/bin/env python2.7

import wx

class LoginDialog(wx.Dialog):
    
    def __init__(self, parent, username, password, *args, **kw):
        super(LoginDialog, self).__init__(parent, *args, **kw) 
        
        self.InitUI(username, password)
        self.SetSize((300, 120))
        self.SetTitle("Batoto Login Credentials")
        
    def InitUI(self, user, passwd):

        USERNAME = 1
        PASSWORD = 2

        pnl = wx.Panel(self)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        fgs = wx.FlexGridSizer(3, 2, 9, 25)

        ul = wx.StaticBox(pnl, label='Username:')
        self.username = wx.TextCtrl(pnl, id=USERNAME, value=user)

        pl = wx.StaticBox(pnl, label='Password:')
        self.password = wx.TextCtrl(pnl, id=PASSWORD, value=passwd)

        cancel = wx.Button(pnl, label='Cancel')
        save = wx.Button(pnl, wx.ID_OK, label='Save')

        cancel.Bind(wx.EVT_BUTTON, self.Cancel)

        fgs.AddMany([
            ul, (self.username, 1, wx.EXPAND),
            pl, (self.password, 2, wx.EXPAND),
            (cancel, 3, wx.EXPAND), (save, 4, wx.EXPAND)
        ])
        fgs.AddGrowableCol(0, 1)
        fgs.AddGrowableCol(1, 1)

        hbox.Add(fgs, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
        pnl.SetSizer(hbox)
        
    def Cancel(self, e):
        
        self.Destroy()