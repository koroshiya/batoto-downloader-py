#!/usr/bin/env python2.7

from __future__ import unicode_literals
import sys
import wx
from URLParser import URLParser
import os
from os.path import expanduser, isfile, isdir, join
from threading import Thread
from LoginDialog import LoginDialog
import ConfigParser

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

SETTING_ORDER_NEW = 680
SETTING_ORDER_OLD = 681
SETTING_ORDER_MENU = 682
SETTING_ZIP_ENABLED = 684
SETTING_ZIP_DISABLED = 685
SETTING_ZIP_MENU = 686
SETTING_RSS_FRAME = 687
SETTING_LANGUAGE_FRAME = 688
SETTING_PROXY = 689
SETTING_LOGIN = 690
SETTING_DOWNLOAD_DIR = 691

HOME_DIR = expanduser("~")
if os.name == 'nt':
	HOME_DIR = join(HOME_DIR, "Documents")
SAVE_FILE = join(HOME_DIR, "batotolist.txt")
SETTINGS_FILE = join(HOME_DIR, "BatotoConfig.cfg")
SECTION = 'Settings'

WIDTH_MIN = 500
WIDTH_INITIAL = 500
HEIGHT_MIN = 400
HEIGHT_INITIAL = 400

class BatotoThread(Thread):
	
	def __init__(self, pType, lines, frame, order=True):
		Thread.__init__(self)
		self.pType = pType
		self.lines = lines
		self.parser = URLParser(frame.config.get(SECTION, 'proxy'))
		self.frame = frame
		self.order = order
		self.isZip = frame.menuItemSettingsZipTrue.IsChecked()
		self.language = frame.config.get(SECTION, 'language')
		self.downloadDir = frame.config.get(SECTION, 'downloadDir')
		self.cookie = frame.LoadCookiesFromFile()
		self.start() #start automatically
	
	def run(self):
		wx.CallAfter(self.frame.SetLocked, True)
		if self.pType == 0:
			for line in self.lines:
				if self.parser.cancel:
					break
				elif self.order:
					self.ParseFirstThread(line)
				else:
					self.ParseLastThread(line)
		elif self.pType == 1:
			self.ParseLastThread(self.lines)
		else:
			self.ParseFirstThread(self.lines)
		wx.CallAfter(self.frame.SetLocked, False)
		if self.parser.cancel:
			wx.CallAfter(self.frame.UiPrint, '')

	def ParseFirstThread(self, line):
		self.ParseLine(line)
		if not self.parser.cancel:
			wx.CallAfter(self.frame.UiClear, self.order)

	def ParseLastThread(self, line):
		self.ParseLine(line)
		if not self.parser.cancel:
			wx.CallAfter(self.frame.UiClear, self.order)

	def ParseLine(self, line):
		line = line.strip(' \t\n\r')
		if line.startswith("https://"):
			line = "http" + line[5:] #TODO: remove when HTTPS support is added for individual chapters
		if line and self.parser.testURL(line):
			dDir = self.downloadDir
			if not (len(dDir) > 0 and isdir(dDir) and os.access(dDir, os.W_OK | os.X_OK)):
				global HOME_DIR
				dDir = HOME_DIR
			self.parser.downloadFromURL(line, dDir, self.frame, self.isZip, self.language, self.cookie)

class BatotoFrame(wx.Frame):

	def __init__(self, *args, **kwargs):
		super(BatotoFrame, self).__init__(*args, **kwargs)

		self.Bind(wx.EVT_CLOSE, self.Exit)
		self.SetTitle("Batoto Downloader")
		self.SetIcon(wx.Icon('jr.png', wx.BITMAP_TYPE_PNG))
		self.SetSize((WIDTH_INITIAL,HEIGHT_INITIAL))
		self.SetMinSize((WIDTH_MIN,HEIGHT_MIN))
		self.InitUI()
		self.thread = None

	def InitUI(self):

		self.LoadSettingsFromFile()
		self.ConstructMenu()

		panel = wx.Panel(self)
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		fgs = wx.FlexGridSizer(2, 2, 9, 25)

		title = wx.StaticText(panel, label="URL:")

		self.inputText = wx.TextCtrl(panel)
		self.URLList = wx.TextCtrl(panel, style=wx.TE_MULTILINE|wx.TE_DONTWRAP)
		self.URLList.SetEditable(False)
		self.btnBox = self.ConstructButtons(panel)

		fgs.AddMany([(title), (self.inputText, 1, wx.EXPAND), self.btnBox, (self.URLList, 2, wx.EXPAND)])

		fgs.AddGrowableRow(1, 1)
		fgs.AddGrowableCol(1, 1)

		hbox.Add(fgs, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
		panel.SetSizer(hbox)

		self.LoadListFromFile()
		self.Show(True)

	def ConstructMenu(self):

		menubar = wx.MenuBar()
		menuFile = wx.Menu()
		menuParse = wx.Menu()
		menuClear = wx.Menu()
		menuSettings = wx.Menu()

		menuItemImport = wx.MenuItem(menuFile, FILE_IMPORT, '&Import\tCtrl+I')
		menuItemExport = wx.MenuItem(menuFile, FILE_EXPORT, '&Export\tCtrl+E')
		menuItemSave = wx.MenuItem(menuFile, FILE_SAVE, '&Save\tCtrl+S')
		menuItemQuit = wx.MenuItem(menuFile, FILE_CLOSE, '&Quit\tCtrl+Q')

		menuItemParseFirst = wx.MenuItem(menuParse, FILE_PARSE_FIRST, 'Parse &First')
		menuItemParseLast = wx.MenuItem(menuParse, FILE_PARSE_LAST, 'Parse &Last')
		menuItemParseAll = wx.MenuItem(menuParse, FILE_PARSE_ALL, 'Parse &All')

		menuItemClearFirst = wx.MenuItem(menuClear, FILE_CLEAR_FIRST, 'Clear &First')
		menuItemClearLast = wx.MenuItem(menuClear, FILE_CLEAR_LAST, 'Clear &Last')
		menuItemClearAll = wx.MenuItem(menuClear, FILE_CLEAR_ALL, 'Clear &All')
		
		menuSettingsOrder = wx.Menu()
		self.menuItemSettingsOrderNew = menuSettingsOrder.AppendRadioItem(SETTING_ORDER_NEW, 'Newest First')
		self.menuItemSettingsOrderOld = menuSettingsOrder.AppendRadioItem(SETTING_ORDER_OLD, 'Oldest First')
		
		menuSettingsZip = wx.Menu()
		self.menuItemSettingsZipFalse = menuSettingsZip.AppendRadioItem(SETTING_ZIP_DISABLED, 'Disabled')
		self.menuItemSettingsZipTrue = menuSettingsZip.AppendRadioItem(SETTING_ZIP_ENABLED, 'Enabled')

		menuItemRSSDialog = wx.MenuItem(menuSettings, SETTING_RSS_FRAME, '&RSS Settings')
		menuItemLanguageDialog = wx.MenuItem(menuSettings, SETTING_LANGUAGE_FRAME, '&Language Settings')
		menuItemDownloadDirectory = wx.MenuItem(menuSettings, SETTING_DOWNLOAD_DIR, '&Download Directory')
		menuItemProxyDialog = wx.MenuItem(menuSettings, SETTING_PROXY, '&HTTP Proxy')
		menuItemLoginDialog = wx.MenuItem(menuSettings, SETTING_LOGIN, '&Login Credentials')

		#menuItemOpen.SetBitmap(wx.Bitmap('file.png'))
		#RSSDialog

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
		
		menuSettings.AppendMenu(SETTING_ORDER_MENU, '&Parse All Order', menuSettingsOrder)
		menuSettings.AppendMenu(SETTING_ZIP_MENU, '&Zip Chapters', menuSettingsZip)
		menuSettings.AppendItem(menuItemRSSDialog)
		menuSettings.AppendItem(menuItemLanguageDialog)
		menuSettings.AppendItem(menuItemDownloadDirectory)
		menuSettings.AppendItem(menuItemProxyDialog)
		#menuSettings.AppendItem(menuItemLoginDialog) #TODO: enable when logins are needed

		menubar.Append(menuFile, '&File')
		menubar.Append(menuParse, '&Parse')
		menubar.Append(menuClear, '&Clear')
		menubar.Append(menuSettings, '&Settings')

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

		self.Bind(wx.EVT_MENU, self.showRSSDialog, id=SETTING_RSS_FRAME)
		self.Bind(wx.EVT_MENU, self.showLanguageDialog, id=SETTING_LANGUAGE_FRAME)
		self.Bind(wx.EVT_MENU, self.showDownloadDirDialog, id=SETTING_DOWNLOAD_DIR)
		self.Bind(wx.EVT_MENU, self.showProxyDialog, id=SETTING_PROXY)
		self.Bind(wx.EVT_MENU, self.showLoginDialog, id=SETTING_LOGIN)

		self.statusbar = self.CreateStatusBar()
		self.SetMenuBar(menubar)

		###Load settings###
		
		if self.config.getboolean(SECTION, 'orderOldFirst') == True:
			menuSettingsOrder.Check(SETTING_ORDER_OLD, True)
		else:
			menuSettingsOrder.Check(SETTING_ORDER_NEW, True)

		if self.config.getboolean(SECTION, 'zip') == True:
			menuSettingsZip.Check(SETTING_ZIP_ENABLED, True)
		else:
			menuSettingsZip.Check(SETTING_ZIP_DISABLED, True)

	def ConstructButtons(self, panel):
		btnBox = wx.BoxSizer(wx.VERTICAL)
		self.btn1 = wx.Button(panel, label='Add URL')
		self.btn2 = wx.Button(panel, label='Parse First')
		self.btn3 = wx.Button(panel, label='Parse Last')
		self.btn4 = wx.Button(panel, label='Parse All')
		self.btn5 = wx.Button(panel, label='Clear First')
		self.btn6 = wx.Button(panel, label='Clear Last')
		self.btn7 = wx.Button(panel, label='Clear All')
		self.btn8 = wx.Button(panel, label='Cancel')
		self.btn9 = wx.Button(panel, label='Check RSS Feed')
		self.btn1.Bind(wx.EVT_BUTTON, self.AddURL)
		self.btn2.Bind(wx.EVT_BUTTON, self.ParseFirst)
		self.btn3.Bind(wx.EVT_BUTTON, self.ParseLast)
		self.btn4.Bind(wx.EVT_BUTTON, self.ParseAll)
		self.btn5.Bind(wx.EVT_BUTTON, self.ClearFirst)
		self.btn6.Bind(wx.EVT_BUTTON, self.ClearLast)
		self.btn7.Bind(wx.EVT_BUTTON, self.ClearAll)
		self.btn8.Bind(wx.EVT_BUTTON, self.Cancel)
		self.btn8.Disable()
		self.btn9.Bind(wx.EVT_BUTTON, self.CheckForUpdates)
		btnBox.AddMany([(self.btn1, 1, wx.EXPAND), (self.btn2, 1, wx.EXPAND), (self.btn3, 1, wx.EXPAND), (self.btn4, 1, wx.EXPAND), (self.btn5, 1, wx.EXPAND), (self.btn6, 1, wx.EXPAND), (self.btn7, 1, wx.EXPAND), (self.btn8, 1, wx.EXPAND), (self.btn9, 1, wx.EXPAND)])
		return btnBox

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
		self.SaveConfig()

	def Exit(self, e):
		self.SaveConfig()
		wx.Exit()

	def AddURL(self, e):

		originalLine = line = self.inputText.GetLineText(0)
		validStartUrls = ["http://www.", "https://www.", "http://", "https://", "www."]

		for url in validStartUrls:
			if line.startswith(url):
				line = line[len(url):]
				url = "bato.to/"

				if line.startswith(url):
					line = line[len(url):]
					validSubdirs = ["reader#", "comic/"]

					for subdir in validSubdirs:
						if line.startswith(subdir):
							self.inputText.Clear()
							self.DirectlyAddURL(originalLine)
							self.Save(e)
							break

				break

	def DirectlyAddURL(self, line):
		if (len(line) >= 20): #At least the length of http://bato.to/comic/
			if (len(self.URLList.GetLineText(0)) > 0):
				self.URLList.AppendText("\n")
			self.URLList.AppendText(line)
	
	def ParseFirst(self, e):
		totalLines = self.UiGetNumberOfLines()
		if (totalLines > 0):
			line = self.URLList.GetLineText(0)
			language = self.config.get(SECTION, 'language')
			if self.loginIfNeeded():
				self.thread = BatotoThread(2, line, self)

	def ParseLast(self, e):
		totalLines = self.UiGetNumberOfLines()
		if totalLines > 0:
			line = self.URLList.GetLineText(totalLines - 1)
			language = self.config.get(SECTION, 'language')
			if self.loginIfNeeded():
				self.thread = BatotoThread(1, line, self, False)

	def ParseAll(self, e):
		totalLines = self.UiGetNumberOfLines()
		if (totalLines > 0):
			lines = []
			oldOrder = self.menuItemSettingsOrderOld.IsChecked()
			language = self.config.get(SECTION, 'language')

			if oldOrder:
				count = 0
				while count < totalLines:
					lines.append(self.URLList.GetLineText(count))
					count += 1
			else:
				count = totalLines - 1
				while count >= 0:
					lines.append(self.URLList.GetLineText(count))
					count -= 1
			
			if self.loginIfNeeded():
				self.thread = BatotoThread(0, lines, self, not oldOrder)

	def Cancel(self, e):
		if self.thread != None:
			self.thread.parser.Cancel(True)
			self.btn8.Disable()
	
	def EnableCancel(self, enable):
		if enable:
			self.btn8.Enable()
		else:
			self.btn8.Disable()

	def ClearFirst(self, e):
		end = self.URLList.GetLineLength(0) + 1
		self.URLList.Remove(0,end)
		self.Save(e)

	def ClearLast(self, e):
		totalLines = self.UiGetNumberOfLines()
		if totalLines < 2:
			self.ClearAll(e)
		else:
			length = self.URLList.GetLineLength(totalLines - 1) + 1
			end = self.URLList.GetLastPosition()
			start = end - length
			self.URLList.Remove(start,end)
			self.Save(e)

	def ClearAll(self, e):
		self.URLList.Clear()
		self.Save(e)

	def LoadListFromFile(self):
		if isfile(SAVE_FILE):
			self.URLList.LoadFile(SAVE_FILE)
			os.remove(SAVE_FILE)

		url = self.config.get(SECTION, 'urls')
		if len(url) > 0:
			self.DirectlyAddURL(url)

	def LoadCookiesFromFile(self):
		return {'cookie': self.config.get(SECTION, 'cookie')}

	def LoadSettingsFromFile(self):
		self.config = ConfigParser.RawConfigParser({
			'orderOldFirst':'False',
			'zip':'False',
			'urls':'',
			'rss':'',
			'rssDate':'',
			'language':'English',
			'proxy':'',
			'cookie':'',
			'username':'',
			'password':'',
			'downloadDir':''
		})

		if isfile(SETTINGS_FILE):
			self.config.read(SETTINGS_FILE)
		else:
			self.config.add_section(SECTION)

	def SaveConfig(self):

		arr = self.UiGetList()
		oldFirst = str(self.menuItemSettingsOrderOld.IsChecked())
		zipEnabled = str(self.menuItemSettingsZipTrue.IsChecked())

		self.config.set(SECTION, 'urls', arr)
		self.config.set(SECTION, 'orderOldFirst', oldFirst)
		self.config.set(SECTION, 'zip', zipEnabled)

		with open(SETTINGS_FILE, 'wb') as configfile:
			self.config.write(configfile)

	def SetLocked(self, lock):
		btns = [self.btn1, self.btn2, self.btn3, self.btn4,
				self.btn5, self.btn6, self.btn7, self.btn9]
		if lock:
			for btn in btns:
				btn.Disable()
			self.btn8.Enable()
		else:
			for btn in btns:
				btn.Enable()
			self.btn8.Disable()
			self.thread.parser.Cancel(False)
	
	def UiPrint(self, text):
		self.statusbar.SetStatusText(text)
	
	def UiClear(self, first):
		if first:
			self.ClearFirst(None)
		else:
			self.ClearLast(None)

	def UiGetLine(self, lineNum):
		return self.URLList.GetLineText(lineNum)

	def UiGetNumberOfLines(self):
		if self.URLList.GetValue() == '':
			return 0
		else:
			return self.URLList.GetNumberOfLines()

	def UiGetList(self):
		arr = ''
		if self.URLList.GetValue() != '':
			n = self.URLList.GetNumberOfLines()
			for i in xrange(0, n):
				arr += self.UiGetLine(i) + '\n'
			if len(arr) > 0:
				arr = arr[:-1] #remove final newline
		return arr

	def showRSSDialog(self, e):
		dlg = wx.TextEntryDialog(self,
			'Enter Batoto RSS feed URL.\n'+
			'You can get this URL by logging onto Batoto and going to: https://bato.to/myfollows\n'+
			'Copy the link address of the RSS feed and paste it here.\n'+
			'It will look like: https://bato.to/myfollows_rss?secret=randomText&l=English\n'+
			'where randomText is a mix of numbers and letters, and English is your desired language',
			defaultValue=self.config.get(SECTION, 'rss'))
		dlg.ShowModal()
		result = dlg.GetValue()
		dlg.Destroy()
		
		if result is not False:
			self.config.set(SECTION, 'rss', result)

	def showLanguageDialog(self, e):
		dlg = wx.TextEntryDialog(self,
			'Enter language for Batoto full-series downloads.\n'+
			'The language should match one of those in the "Language Settings" panel on Batoto\'s home page.\n'+
			'This is case-sensitive. eg. "French" will work, "french" will not.',
			defaultValue=self.config.get(SECTION, 'language'))
		dlg.ShowModal()
		result = dlg.GetValue()
		dlg.Destroy()
		
		if result is not False:
			self.config.set(SECTION, 'language', result)

	def showDownloadDirDialog(self, e):
		dlg = wx.DirDialog(self,
			'Select a writable directory in which to store Batoto downloads.',
			self.config.get(SECTION, 'downloadDir'),
			wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
		dlg.ShowModal()
		result = dlg.GetPath()
		dlg.Destroy()
		
		if result is not False and isdir(result) and os.access(result, os.W_OK | os.X_OK):
			self.config.set(SECTION, 'downloadDir', result)

	def showProxyDialog(self, e):
		dlg = wx.TextEntryDialog(self,
			'HTTP proxy for all downloads.\n'+
			'Proxy format: http://ip:port\n'+
			'eg. http://192.168.1.112:8118',
			defaultValue=self.config.get(SECTION, 'proxy'))
		dlg.ShowModal()
		result = dlg.GetValue()
		dlg.Destroy()
		
		if result is not False:
			self.config.set(SECTION, 'proxy', result)

	def showLoginDialog(self, e):
		dlg = LoginDialog(self, self.config.get(SECTION, 'username'), self.config.get(SECTION, 'password'))
		res = dlg.ShowModal()
		if res == wx.ID_OK:
			self.config.set(SECTION, 'username', dlg.username.GetValue())
			self.config.set(SECTION, 'password', dlg.password.GetValue())
		dlg.Destroy()

	def loginIfNeeded(self):

		return True #Skip login check for the time being; necessity hasn't yet arisen

		reason = ''
		loginNeeded = False
		parser = URLParser(self.config.get(SECTION, 'proxy'))
		username = self.config.get(SECTION, 'username')
		password = self.config.get(SECTION, 'password')

		if len(username) == 0 or len(password) == 0:
			reason = 'Username and password cannot be empty.\n' + \
					'Go to Settings -> Login Credentials'
		else:
			expires = parser.getCookie(self.config.get(SECTION, 'cookie'), 'expires')
			if not expires or parser.minutesUntil(expires) <= 10: #If invalid cookie, or about to expire
				loginNeeded = True

		if loginNeeded:
			busy = wx.BusyInfo("Attempting login...")
			args = parser.login(username, password)
			del busy

			if args:
				self.config.set(SECTION, 'cookie', args['cookie'])
				self.SaveConfig()
			else:
				reason = 'Login failed.\n' + \
							'Please try logging in via a web browser to ensure that ' + \
							'the username/password combination is correct, your network ' + \
							'allows you to connect to Batoto, there are no connectivity ' + \
							'issues on Batoto\'s end, etc.'

		if len(reason) > 0:
			self.ShowMessage("Login Error", reason)
			return False
		else:
			return True

	def CheckForUpdates(self, e):
		url = self.config.get(SECTION, 'rss')
		if url[0:30] == 'https://bato.to/myfollows_rss?' or url[0:29] == 'http://bato.to/myfollows_rss?':
			date = self.config.get(SECTION, 'rssDate')

			parser = URLParser(self.config.get(SECTION, 'proxy'))
			busy = wx.BusyInfo("Checking for updates...")
			args = parser.getUpdates(url, date)
			del busy

			if args[0]:
				self.config.set(SECTION, 'rssDate', args[1])
				if len(args[2]) > 0:
					self.DirectlyAddURL(args[2])
			else:
				self.ShowMessage(args[1])
		else:
			self.ShowMessage(
				'Invalid or missing rss feed.\n'+
				'Go to "Settings > RSS Settings" for instructions\n'+
				'on how to find and enter an RSS feed with your\n'+
				'followed series on Batoto.',
				'Invalid RSS'
			)

	def ShowMessage(self, msg, title):
		wx.MessageBox(msg, title, wx.OK | wx.ICON_INFORMATION)
