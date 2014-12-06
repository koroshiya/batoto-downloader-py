#!/usr/bin/python2.7 -tt

from __future__ import unicode_literals
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
import multiprocessing
from multiprocessing import Queue, Process, current_process
from threading import Thread

reload(sys)
sys.setdefaultencoding("utf-8")

class URLParser:
	BUFFER = 4096
	
	work_queue = Queue()
	done_queue = Queue()
	processes = []
	workers = 4
	IOError_RepeatCount = 3
	
	def ContinueDownload(self, url, workdir, frame):
		filep = URLParser.LastFileInPath(self, url)
		#frame.SetStatusText('Downloading: ' + filep)
		print 'Downloading: ' + filep
		repeat = True
		repeatCount = self.IOError_RepeatCount
		while repeat:
			repeat = False
			try:
				urllib.urlretrieve(url, workdir + "/" + filep)
			except IOError:
				repeat = True
				repeatCount -= 1
				if repeatCount < 0:
					raise
		return "Page downloaded"
	
	def worker(self, work_queue, done_queue, workdir, frame):
		for url in iter(work_queue.get, 'STOP'):
			status_code = URLParser.ContinueDownload(self, url, workdir, frame)
			done_queue.put("%s - %s got %s." % (current_process().name, url, status_code))
		return True
	
	def arbitraryDownload(self, oldPath, home, frame):
		if (not(oldPath[:7] == "http://" or oldPath[:8] == "https://")): return False
		try:
			newDir = home + "/" + URLParser.LastFolderInPath(self, oldPath)
		except Exception, e:
			print repr(e)
			return False
		if not os.path.isdir(newDir):
			os.makedirs(newDir)
		i = 1
		boolContinue = True
		while boolContinue:
			boolContinue = False
			if i < 10:
				padding = "00" + str(i)
			elif i < 100:
				padding = "0" + str(i)
			elif i < 1000:
				padding = str(i)
			else:
				return
			try:
				for ext in [".jpg", ".png"]:
					nUrl = oldPath + str(i) + ext
					print "Testing URL:", nUrl
					if self.testURL(nUrl):
						print 'Downloading: ' + padding + ext
						wx.CallAfter(frame.UiPrint, 'Downloading: ' + padding + ext)
						urllib.urlretrieve(nUrl, newDir + "/" + padding + ext)
						boolContinue = True
						break
			except Exception, e:
				pass
			i += 1
	
	def downloadFullSeries(self, url, home, frame):
		newDir = ""
		if url[-1] != "/":
			url += "/"
		try:
			newDir = home + "/" + URLParser.LastFolderInPath(self, url)
		except Exception, e:
			print repr(e)
			return False
		
		workDir = home
		if not os.path.isdir(newDir):
			os.makedirs(newDir)
		workDir = newDir
		
		chapters = self.findChapters(url)
		
		for chapter in chapters[::-1]:
			print "Indexing " + chapter
			print "-----------------------"
			self.downloadFromURL(chapter, newDir, frame)
	
	def findChapters(self, url):
		
		request = urllib2.Request(url)
		request.add_header('Accept-encoding', 'gzip')
		aResp = urllib2.urlopen(request)
		if aResp.info().get('Content-Encoding') == 'gzip':
			buf = StringIO( aResp.read())
			f = gzip.GzipFile(fileobj=buf)
			web_pg = f.readlines()
		else:
			web_pg = aResp.readlines()
		
		pattern = "http://bato.to/read/\S*\""
		chapters = []
		lang = None
		for line in web_pg:
			if lang == "English":
				m = re.search(pattern, line)
				if m:
					inputLine = m.group(0)[:-1]
					if not "/" in inputLine[-4]:
						chapters.append(inputLine)
					lang = None
			else:
				try:
					if "lang_English" in line:
						lang = "English"
					else:
						lang = None
				except UnicodeDecodeError:
					lang = None
		
		return chapters

	def downloadFromURL(self, oldPath, home, frame):
		if (not(oldPath[:14] == "http://bato.to" or oldPath[:15] == "https://bato.to" or oldPath[:18] == "http://www.bato.to" or oldPath[:19] == "https://www.bato.to")):
			URLParser.arbitraryDownload(self, oldPath, home, frame)
			return False
		if "bato.to/comic/" in oldPath:
			URLParser.downloadFullSeries(self, oldPath, home, frame)
			return True
		else:
			if (not oldPath[-1] == "/" and not oldPath[-1] == "/1"): oldPath += "/1"
		
		url = oldPath
		newDir = ""
		lastPath = URLParser.LastFolderInPath(self, url)
		try:
			newDir = home + "/" + lastPath
		except Exception, e:
			print repr(e)
			return False
		
		workDir = home
		if not os.path.isdir(newDir):
			os.makedirs(newDir)
		workDir = newDir
		
		regex = ""
		boolContinue = True
		i = 1
		urls = []
		wx.CallAfter(frame.UiPrint, 'Indexing...')
		
		while boolContinue:
			try:
				arg = URLParser.AbsoluteFolder(self, url) + str(i)
				wx.CallAfter(frame.UiPrint, 'Indexing page ' + str(i))
				print 'Indexing page ' + str(i)
				regex = URLParser.findFormat(self, arg, False)
				if regex and regex[-4:] in [".jpg", ".png"]:
					if URLParser.Download(self, regex, workDir, frame):
						urls.append(regex)
				else:
					boolContinue = False
			except Exception, e:
				boolContinue = False
			i+=1
		
		print "\n"		
		print "Downloading " + lastPath
		print "-----------------------"
		wx.CallAfter(frame.UiPrint, 'Downloading '+lastPath)
		if len(urls) > 0:
			for url in urls:
				self.work_queue.put(url)
				
			for w in xrange(self.workers):
				if os.name == 'nt':
					p = Thread(target=self.worker, args=(self.work_queue, self.done_queue, workDir, frame))
				else:
					p = Process(target=self.worker, args=(self.work_queue, self.done_queue, workDir, frame))
				p.start()
				self.processes.append(p)
				self.work_queue.put('STOP')

			for p in self.processes:
				p.join()

			self.done_queue.put('STOP')
			print "\n"

			for status in iter(self.done_queue.get, 'STOP'):
				print status
		
		wx.CallAfter(frame.UiPrint, 'Finished')
		print "\n"
		print "Finished downloading chapter"
		print "\n"
		
		return i != 1
	
	def findExtension(self, path, i):
	
		extensions = [".png", ".jpg", ".gif"]

		for s in extensions:
			if (self.testURL(path + s)): return path + s
		
		form = self.FormatNumber(i + 1, 2)
		for s in extensions:
			url = path + "-" + form + s
			if (self.testURL(url)): return url
		

		return None
	
	def testURL(self, url):
		
		code = 0
		try:
			urllib2.urlopen(url)
			return True
		except Exception, ex:
			print repr(ex)
		
		return False
	
	def findFormat(self, url, dire):
		
		request = urllib2.Request(url)
		request.add_header('Accept-encoding', 'gzip')
		aResp = urllib2.urlopen(request)
		if aResp.info().get('Content-Encoding') == 'gzip':
			buf = StringIO( aResp.read())
			f = gzip.GzipFile(fileobj=buf)
			web_pg = f.readlines()
		else:
			web_pg = aResp.readlines()
		#print web_pg
		
		for line in web_pg:
			if "id=\"comic_page\"" in line:
				mn = re.search('src=\S*\"', line)
				if mn:
					inputLine = mn.group(0)[5:-1]
					inp = "" if inputLine[0:10] == "http://arc" else "img"
					return self.AbsoluteFolder(inputLine) + inp if dire else inputLine
		
		return False
	
	def Download(self, url, workDir, frame):
		filep = URLParser.LastFileInPath(self, url)
		lFile = workDir + "/" + filep
		if os.path.isfile(lFile) and os.path.getsize(lFile) == int(urllib2.urlopen(url).headers["Content-Length"]):
			wx.CallAfter(frame.UiPrint, filep + ' already exists')
			return False
		else:
			return True

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
		precede = 0
		
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
		
		strBuffer += i
		
		return strBuffer
