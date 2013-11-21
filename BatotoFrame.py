#!/usr/bin/python2.7 -tt

import sys
if sys.version_info < (2, 7):
    print "Must use python 2.7 or greater\n"
    sys.exit()

try:
	import wx
except ImportError:
	print "You do not appear to have wxpython installed.\n"
	print "Without wxpython, this program cannot run.\n"
	print "You can download wxpython at: http://www.wxpython.org/download.php#stable \n"
	sys.exit()
from URLParser import URLParser
from os.path import expanduser
from os.path import isfile
from threading import Thread

FILE_IMPORT = 650
FILE_EXPORT = 651
FILE_SAVE = 661
FILE_CLOSE = 666

FILE_PARSE_FIRST = 662
FILE_PARSE_LAST = 663
FILE_PARSE_ALL = 664

FILE_CLEAR_FIRST = 668
FILE_CLEAR_LAST = 669
FILE_CLEAR_ALL = 670

HOME_DIR = expanduser("~")
SAVE_FILE = HOME_DIR + "/batotolist.txt"

WIDTH_MIN = 500
WIDTH_INITIAL = 500
HEIGHT_MIN = 400
HEIGHT_INITIAL = 400

class BatotoFrame(wx.Frame):

	def __init__(self, *args, **kwargs):
		super(BatotoFrame, self).__init__(*args, **kwargs)

		self.SetTitle("Batoto Downloader")
		self.SetIcon(wx.Icon('jr.png', wx.BITMAP_TYPE_PNG))
		self.SetSize((WIDTH_INITIAL,HEIGHT_INITIAL));
		self.SetMinSize((WIDTH_MIN,HEIGHT_MIN))
		self.InitUI()

	def InitUI(self):

		self.ConstructMenu();

		panel = wx.Panel(self)
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		fgs = wx.FlexGridSizer(2, 2, 9, 25)

		title = wx.StaticText(panel, label="URL:")

		self.inputText = wx.TextCtrl(panel)
		self.URLList = wx.TextCtrl(panel, style=wx.TE_MULTILINE|wx.TE_DONTWRAP)
		self.URLList.SetEditable(False);
		btnBox = self.ConstructButtons(panel)

		fgs.AddMany([(title), (self.inputText, 1, wx.EXPAND), btnBox, (self.URLList, 2, wx.EXPAND)])

		fgs.AddGrowableRow(1, 1)
		fgs.AddGrowableCol(1, 1)

		hbox.Add(fgs, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
		panel.SetSizer(hbox)

		self.LoadListFromFile()
		self.Show(True)

	def ConstructMenu(self):

		menubar = wx.MenuBar();
		menuFile = wx.Menu()
		menuParse = wx.Menu()
		menuClear = wx.Menu()

		menuItemImport = wx.MenuItem(menuFile, FILE_IMPORT, '&Import\tCtrl+I')
		menuItemExport = wx.MenuItem(menuFile, FILE_EXPORT, '&Export\tCtrl+E')
		menuItemSave = wx.MenuItem(menuFile, FILE_SAVE, '&Save\tCtrl+S')
		menuItemQuit = wx.MenuItem(menuFile, FILE_CLOSE, '&Quit\tStrl+Q')

		menuItemParseFirst = wx.MenuItem(menuParse, FILE_PARSE_FIRST, 'Parse &First')
		menuItemParseLast = wx.MenuItem(menuParse, FILE_PARSE_LAST, 'Parse &Last')
		menuItemParseAll = wx.MenuItem(menuParse, FILE_PARSE_ALL, 'Parse &All')

		menuItemClearFirst = wx.MenuItem(menuClear, FILE_CLEAR_FIRST, 'Clear &First')
		menuItemClearLast = wx.MenuItem(menuClear, FILE_CLEAR_LAST, 'Clear &Last')
		menuItemClearAll = wx.MenuItem(menuClear, FILE_CLEAR_ALL, 'Clear &All')

		#menuItemOpen.SetBitmap(wx.Bitmap('file.png'))

		menuFile.AppendItem(menuItemImport)
		menuFile.AppendItem(menuItemExport)
		menuFile.AppendSeparator()
		menuFile.AppendItem(menuItemSave)
		menuFile.AppendSeparator()
		menuFile.AppendItem(menuItemQuit)

		menuParse.AppendItem(menuItemParseFirst)
		menuParse.AppendItem(menuItemParseLast)
		menuParse.AppendItem(menuItemParseAll)

		menuClear.AppendItem(menuItemClearFirst)
		menuClear.AppendItem(menuItemClearLast)
		menuClear.AppendItem(menuItemClearAll)

		menubar.Append(menuFile, '&File')
		menubar.Append(menuParse, '&Parse')
		menubar.Append(menuClear, '&Clear')

		self.Bind(wx.EVT_MENU, self.Import, id=FILE_IMPORT)
		self.Bind(wx.EVT_MENU, self.Export, id=FILE_EXPORT)
		self.Bind(wx.EVT_MENU, self.Save, id=FILE_SAVE)
		self.Bind(wx.EVT_MENU, self.Exit, id=FILE_CLOSE)

		self.Bind(wx.EVT_MENU, self.ParseFirst, id=FILE_PARSE_FIRST)
		self.Bind(wx.EVT_MENU, self.ParseLast, id=FILE_PARSE_LAST)
		self.Bind(wx.EVT_MENU, self.ParseAll, id=FILE_PARSE_ALL)

		self.Bind(wx.EVT_MENU, self.ClearFirst, id=FILE_CLEAR_FIRST)
		self.Bind(wx.EVT_MENU, self.ClearLast, id=FILE_CLEAR_LAST)
		self.Bind(wx.EVT_MENU, self.ClearAll, id=FILE_CLEAR_ALL)

		self.statusbar = self.CreateStatusBar()
		self.SetMenuBar(menubar);

	def ConstructButtons(self, panel):
		btnBox = wx.BoxSizer(wx.VERTICAL)
		btn1 = wx.Button(panel, label='Add URL')
		btn2 = wx.Button(panel, label='Parse First')
		btn3 = wx.Button(panel, label='Parse Last')
		btn4 = wx.Button(panel, label='Parse All')
		btn5 = wx.Button(panel, label='Clear First')
		btn6 = wx.Button(panel, label='Clear Last')
		btn7 = wx.Button(panel, label='Clear All')
		btn1.Bind(wx.EVT_BUTTON, self.AddURL)
		btn2.Bind(wx.EVT_BUTTON, self.ParseFirst)
		btn3.Bind(wx.EVT_BUTTON, self.ParseLast)
		btn4.Bind(wx.EVT_BUTTON, self.ParseAll)
		btn5.Bind(wx.EVT_BUTTON, self.ClearFirst)
		btn6.Bind(wx.EVT_BUTTON, self.ClearLast)
		btn7.Bind(wx.EVT_BUTTON, self.ClearAll)
		btnBox.AddMany([(btn1, 1, wx.EXPAND), (btn2, 1, wx.EXPAND), (btn3, 1, wx.EXPAND), (btn4, 1, wx.EXPAND), (btn5, 1, wx.EXPAND), (btn6, 1, wx.EXPAND), (btn7, 1, wx.EXPAND)])
		return btnBox;

	def Import(self, e):
		openFileDialog = wx.FileDialog(self, "Open Text file", "", "", "Text files (*.txt)|*.txt", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
		
		if (openFileDialog.ShowModal() == wx.ID_CANCEL):
			return
		self.URLList.LoadFile(openFileDialog.GetPath())

	def Export(self, e):
		saveFileDialog = wx.FileDialog(self, "Save Text file", "", "", "Text file (*.txt)|*.txt", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
		
		if (saveFileDialog.ShowModal() == wx.ID_CANCEL):
			return
		try:
			self.URLList.SaveFile(saveFileDialog.GetPath())
		except Exception, e:
			wx.MessageDialog(None, 'Error saving file', 'Error', wx.OK | wx.ICON_ERROR).ShowModal()

	def Save(self, e):
		self.URLList.SaveFile(SAVE_FILE)

	def Exit(self, e):
		self.Close();

	def AddURL(self, e):
		line = self.inputText.GetLineText(0);
		if (line[:4] == "http" or line[:4] == "www."):
			self.inputText.Clear();
			self.DirectlyAddURL(line);
			self.Save(e);

	def DirectlyAddURL(self, line):
		if (len(self.URLList.GetLineText(0)) > 0):
			self.URLList.AppendText("\n");
		self.URLList.AppendText(line);

	def ParseFirst(self, e):
		line = self.URLList.GetLineText(0);
		if (len(line) > 0):
			Thread(target = self.ParseFirstThread(line, e)).start();

	def ParseFirstThread(self, line, e):
		self.ParseLine(line)
		self.ClearFirst(e);

	def ParseLast(self, e):
		totalLines = self.URLList.GetNumberOfLines()
		if totalLines < 2:
			self.ParseFirst(e);
		else:
			line = self.URLList.GetLineText(totalLines - 1);
			Thread(target = self.ParseLastThread(line, e)).start();

	def ParseLastThread(self, line, e):
		self.ParseLine(line);
		self.URLList.ClearLast(e);

	def ParseAll(self, e):
		totalLines = self.URLList.GetNumberOfLines()
		count = 0
		while (count < totalLines):
			self.ParseFirst(e)
			count += 1

	def ParseLine(self, line):
		self.SetLocked(True)
		parser = URLParser();
		if parser.testURL(line):
			parser.downloadFromURL(line, HOME_DIR, self.statusbar)
		self.SetLocked(False)

	def ClearFirst(self, e):
		end = self.URLList.GetLineLength(0) + 1;
		self.URLList.Remove(0,end)
		self.Save(e);

	def ClearLast(self, e):
		totalLines = self.URLList.GetNumberOfLines()
		if totalLines < 2:
			self.ClearAll(e);
		else:
			length = self.URLList.GetLineLength(totalLines - 1) + 1;
			end = self.URLList.GetLastPosition();
			start = end - length
			self.URLList.Remove(start,end)
			self.Save(e);

	def ClearAll(self, e):
		self.URLList.Clear();
		self.Save(e);

	def LoadListFromFile(self):
		if isfile(SAVE_FILE):
			self.URLList.LoadFile(SAVE_FILE)

	def SetLocked(self, lock):
		if lock:
			self.Disable()
		else:
			self.Enable()