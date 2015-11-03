#!/usr/bin/python2.7 -tt

from __future__ import unicode_literals
import sys
if sys.version_info < (2, 7):
	print "Must use python 2.7 or greater\n"
	sys.exit()

try:
	import wx
except ImportError:

	title = "wxPython not installed"
	msg = "Without wxpython, this program cannot run.\n" + \
			"You can download wxpython at: http://www.wxpython.org/download.php#stable \n"

	try:
		import Tkinter, tkMessageBox
		root = Tkinter.Tk()
		root.withdraw()
		tkMessageBox.showinfo(title, msg)
	except ImportError:
		print title + "\n"
		print msg + "\n"
	sys.exit()

import importlib
from distutils.version import LooseVersion

required_modules = [
	['lxml', '3.4.4', 'b3d362bac471172747cda3513238f115cbd6c5f8b8e6319bf6a97a7892724099', 'src/lxml', ''],
	['certifi', '2015.9.6.2', 'dc3a2b2d9d1033dbf27586366ae61b9d7c44d8c3a6f29694ffcbb0618ea7aea6', 'certifi', ''],
	['urllib3', '1.12', '0ea512776971fe4e76192600fe41e4e7ee96b4b9a5b15aefc1ac31d2a63872c6', 'urllib3', ''],
	['pyOpenSSL', '0.15.1', 'f0a26070d6db0881de8bcc7846934b7c3c930d8f9c79d45883ee48984bc0d672', 'OpenSSL', ''],
	['ndg-httpsclient', '0.4.0', 'e8c155fdebd9c4bcb0810b4ed01ae1987554b1ee034dd7532d7b8fdae38a6274', 'ndg', 'ndg_httpsclient'],
	['pyasn1', '0.1.9', '853cacd96d1f701ddd67aa03ecc05f51890135b7262e922710112f12a2ed2a7f', 'pyasn1', '']
]
missing_modules = []
for m in required_modules:
	try:
		print 'testing '+m[0]
		if LooseVersion(__import__(m[0]).__version__) < LooseVersion(m[1]):
			print 'Newer version of '+m[0]+' available'
			raise ImportError
		importlib.import_module(m[0])
	except ImportError:
		missing_modules.append(m)
	except AttributeError: #Version number not specified
		try:
			importlib.import_module(m[0])
		except ImportError:
			missing_modules.append(m)

if len(missing_modules) > 0:

	from Updater import MainFrame

	app = wx.App(False)
	fr = MainFrame(None, -1, "Installing modules", missing_modules)
	fr.Show()
	app.MainLoop()

	for m in missing_modules:
		try:
			importlib.import_module(m[0])
		except ImportError:
			print 'Module '+m[0]+' still missing; assuming user stopped half way through'
			sys.exit()

import os
import BatotoFrame

os.chdir(os.path.dirname(os.path.realpath(__file__)))

batoto = wx.App(False)

options = wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX
frame = wx.Frame(None, style=options)
f = BatotoFrame.BatotoFrame(frame)

batoto.MainLoop()
