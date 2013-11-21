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

import urllib
import urllib2
import re
import os
import traceback
from StringIO import StringIO
import gzip

class URLParser:
	BUFFER = 4096;
	FAILSAFE = True;

	def downloadFromURL(self, oldPath, home, statusbar):
		if (not oldPath[-1] == "/" and not oldPath[-1] == "/1"): oldPath += "/1"
		if (not(oldPath[:7] == "http://" or oldPath[:8] == "https://")): return False
		
		url = oldPath;
		newDir = "";
		try:
			newDir = home + "/" + URLParser.LastFolderInPath(self, url)
		except Exception, e:
			print repr(e)
			return False
		
		workDir = home;
		if not os.path.isdir(newDir):
			os.makedirs(newDir)
		workDir = newDir
		
		regex = ""
		boolContinue = True
		i = 1
		if (URLParser.FAILSAFE):
			while boolContinue:
				try:
					arg = URLParser.AbsoluteFolder(self, url) + str(i);
					regex = URLParser.findFormat(self, arg, False);
					URLParser.Download(self, regex, workDir, statusbar);
				except Exception, e:
					#print "Regex FAILSAFE " + repr(e)
					#traceback.print_exc(file=sys.stdout)
					#Commented out because this exception is usually hit at end of chapter regardless
					boolContinue = False
				i+=1
			statusbar.SetStatusText('')
		else:
			try:
				regex = URLParser.findFormat(self, url, True)
			except Exception, ex:
				print "regex" + repr(ex)
				return False
			
			while boolContinue:
				try:
					siz = 6 if (regex[:10] == "http://img" or regex[:9] == "http://eu") else 2
					form = URLParser.FormatNumber(i, siz)
					
					fmtImg = (regex + form)
					filePath = URLParser.findExtension(fmtImg, i)
					URLParser.Download(filePath, workDir, statusbar)
				except Exception, ex:
					print repr(ex)
					boolContinue = False
				
				i+=1
			statusbar.SetStatusText('')
		
		return i != 1;
	
	def findExtension(self, path, i):
	
		extensions = [".png", ".jpg", ".gif"]

		for s in extensions:
			if (testURL(path + s)): return path + s
		
		form = FormatNumber(i + 1, 2);
		for s in extensions:
			url = path + "-" + form + s
			if (testURL(url)): return url
		

		return null;	
	
	def testURL(self, url):
		
		code = 0;
		try:
			urllib2.urlopen(url)
			return True
		except Exception, ex:
			print repr(ex)
		
		return False
	
	def findFormat(self, url, dire):
		
		request = urllib2.Request(url)
		request.add_header('Accept-encoding', 'gzip')
		aResp = urllib2.urlopen(request);
		if aResp.info().get('Content-Encoding') == 'gzip':
		    buf = StringIO( aResp.read())
		    f = gzip.GzipFile(fileobj=buf)
		    web_pg = f.read()
		else:
			web_pg = aResp.read()
		
		pattern = ["http://img.batoto.net/comics/2\S*\"", "http://eu.batoto.net/comics/2\S*\"", "http://arc.batoto.net/comics/2\S*\""]
		for p in pattern:
			m = re.search(p, web_pg)
			if m:
				inputLine = m.group(0)[:-1]
				arc = re.search("http://arc.batoto.net/comics/2\S*\"", inputLine)
				inp = "img"
				if arc:
					inp = ""
				return URLParser.AbsoluteFolder(inputLine) + inp if dire else inputLine
		
		raise Exception("");
	
	def Download(self, url, workDir, statusbar):
		filep = URLParser.LastFileInPath(self, url);
		statusbar.SetStatusText('Downloading: ' + filep)
		urllib.urlretrieve(url, workDir + "/" + filep)
	
	def LastFileInPath(self, path):
		start = path.rindex('/')
		return path[start + 1:]
	
	def LastFolderInPath(self, path):
		start = path.rindex('/')
		newPath = path[:start]
		start = newPath.rindex('/')
		return newPath[start + 1:]
	
	def AbsoluteFolder(self, path):
		start = path.rindex('/')
		return path[:start + 1]
	
	def FormatNumber(self, i, places):
		strBuffer = ""
		precede = 0;
		
		if (i < 10):
			precede = 1
		elif (i < 100):
			precede = 2
		elif (i < 1000):
			precede = 3
		
		a = 0
		while (a < places - precede):
			strBuffer += "0"
			a += 1
		
		strBuffer += i;
		
		return strBuffer