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

try:
	from lxml import html as hlxml
	from lxml import etree
except ImportError:
	print "You do not appear to have lxml installed.\n"
	print "Without lxml, this program cannot run.\n"
	print "You can download lxml at: http://lxml.de/installation.html \n"
	sys.exit()

import urllib3
import os
from multiprocessing import Queue, current_process
if os.name == 'nt':
	from threading import Thread
else:
	from multiprocessing import Process
import zipfile
import tempfile
from time import strptime

reload(sys)
sys.setdefaultencoding("utf-8")

class URLParser:
	
	def __init__(self, proxy):

		self.work_queue = Queue()
		self.done_queue = Queue()
		self.processes = []
		self.workers = 4
		self.IOError_RepeatCount = 4
		self.imgServerMax = 4 #Number of image servers available
		self.imgServer = 1
		self.cancel = False
		self.extensions = [".jpeg", ".jpg", ".png", ".gif"]
		self.zf = None
		self.cookies = None

		if len(proxy) > 0:
			self.http = urllib3.ProxyManager(proxy)
		else:
			self.http = urllib3.PoolManager()


	def Cancel(self, state):
		self.cancel = True
		
	def buildHeaders(self, headers={}):
		if self.cookies:
			headers['Cookie'] = self.cookies
		return headers
	
	def updateSession(self, r):
		self.cookies = r.getheader('set-cookie')
	
	def ContinueDownload(self, url, workdir, frame):
		if not self.cancel:
			filep = URLParser.LastFileInPath(self, url)
			#frame.SetStatusText('Downloading: ' + filep)
			print 'Downloading: ' + filep
			repeatCount = self.IOError_RepeatCount
			while True:
				try:
					if self.imgServer > 1 and url[0:10] == "http://img": #Try another image server
						tmpUrl = url.replace('://img', '://img'+str(self.imgServer), 1)
					else:
						tmpUrl = url
					r = self.http.request('GET', tmpUrl, headers=self.buildHeaders())
					self.updateSession(r)
					if self.zf is None:
						with open(workdir + "/" + filep, "wb") as dlFile:
							dlFile.write(r.data)
					else:
						temp = tempfile.gettempdir() + '/' + filep + '.tmp'
						with open(temp, "wb") as dlFile:
							dlFile.write(r.data)
						return temp
					break
				except:
					repeatCount -= 1
					if url[0:10] == "http://img":
						if self.imgServer < self.imgServerMax:
							self.imgServer += 1
						else:
							self.imgServer = 1
					elif url[0:10] == "http://arc":
						raise
					elif url[0:10] == "http://cdn":
						url = "http://img" + url[10:] #CDN failed; go back to img server
					if repeatCount < 0:
						raise
			return "Page downloaded"
		else:
			return "Page skipped"
	
	def worker(self, work_queue, done_queue, workdir, frame):
		for url in iter(work_queue.get, 'STOP'):
			if self.cancel:
				return False
			status_code = URLParser.ContinueDownload(self, url, workdir, frame)
			done_queue.put(status_code)
		return True
	
	def arbitraryDownload(self, url, home, frame):
		if (not(url[:7] == "http://" or url[:8] == "https://")): return False
		workDir = home + "/" + URLParser.LastFolderInPath(self, url)
		if not os.path.isdir(workDir):
			os.makedirs(workDir)
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
				for ext in self.extensions:
					nUrl = url + str(i) + ext
					print "Testing URL:", nUrl
					data = self.testURL(nUrl)
					if data != False:
						print 'Downloading: ' + padding + ext
						wx.CallAfter(frame.UiPrint, 'Downloading: ' + padding + ext)
						with open(workDir + "/" + padding + ext, "wb") as dlFile:
							dlFile.write(data)
						boolContinue = True
						break
			except Exception, e:
				pass
			i += 1
	
	def downloadFullSeries(self, url, home, frame, isZip, language):

		if url[-1] != "/":
			url += "/"
		try:
			workDir = home + "/" + URLParser.LastFolderInPath(self, url)
		except Exception, e:
			print repr(e)
			return False
		
		if not os.path.isdir(workDir):
			os.makedirs(workDir)
		
		chapters = list(set(self.findChapters(url, language)))
		chapters.sort(key=LastFolderInPath)
		
		for chapter in chapters:
			if self.cancel:
				break
			print "Indexing " + chapter
			print "-----------------------"
			self.downloadFromURL(chapter, workDir, frame, isZip, language)
			
		print "Finished downloading series"
		print "-----------------------"
		
		return True
	
	def findChapters(self, url, language):
		
		r = self.http.request('GET', url, headers=self.buildHeaders())
		self.updateSession(r)
		dom = hlxml.fromstring(r.data)
		aList = dom.xpath('//tr[@class="row lang_'+language+' chapter_row"]//a')
		chapters = []

		for a in aList:
			href = a.get('href')
			if href is not None and 'http://bato.to/read/' in href:
				if href[-1] != '/':
					href += '/'
				chapters.append(href)
		
		return chapters

	def extractUUID(self, lastPath):
		parts = lastPath.split("#", 2)
		if len(parts) < 2:
			return False
	
		parts = parts[1].split("_", 1)
		if len(parts) < 1:
			return False
		return parts[0]


	def downloadFromURL(self, url, home, frame, isZip, language):
		if len(url) < 7:
			return False
		elif (len(url) < 19 or not(url[:14] == "http://bato.to" or url[:15] == "https://bato.to" or url[:18] == "http://www.bato.to" or url[:19] == "https://www.bato.to")):
			URLParser.arbitraryDownload(self, url, home, frame)
			return False
		elif "bato.to/comic/" in url:
			return URLParser.downloadFullSeries(self, url, home, frame, isZip, language)
		#else:
		#	if (not url[-1] == "/" and not url[-1] == "/1"): url += "/1"

		if '_by_' not in url:
			groupName = self.findGroupName(url)
			#if groupName:
			#	url = url[:url.rindex('/')] + '_by_'+groupName + '/1'
		
		uuid = self.extractUUID(url)
		print uuid
		if not uuid:
			print "UUID not found in URL\n"
			return False
		
		workDir = home + "/" + uuid
		self.zf = None
		if isZip:
			filename = workDir + '.zip'
			if os.path.exists(filename):
				os.remove(filename)
			self.zf = zipfile.ZipFile(filename, mode='w')
		elif not os.path.isdir(workDir):
			os.makedirs(workDir)
		
		i = 1
		urls = []
		wx.CallAfter(frame.UiPrint, 'Indexing...')
		
		while not self.cancel:
			try:
				arg = URLParser.AbsoluteFolder(self, url) + "areader?id=" + uuid + "&p=" + str(i)
				referer = URLParser.AbsoluteFolder(self, url) + "reader#" + uuid + "_" + str(i)
				print arg +"\n"
				wx.CallAfter(frame.UiPrint, 'Indexing page ' + str(i))
				print 'Indexing page ' + str(i)
				regex = URLParser.findFormat(self, arg, referer)
				if regex:
					extension = os.path.splitext(regex)[1].lower()
					if extension in self.extensions:
						if URLParser.Download(self, regex, workDir, frame):
							urls.append(regex)
					else:
						break
				else:
					break
			except Exception, e:
				break
			i += 1
		
		if self.cancel:
			return False
		
		print "\n"		
		print "Downloading " + uuid
		print "-----------------------"

		wx.CallAfter(frame.UiPrint, 'Downloading '+uuid)
		wx.CallAfter(frame.EnableCancel, False)

		if len(urls) > 0:
			for url in urls:
				if self.cancel:
					break
				self.work_queue.put(url)
				
			for w in xrange(self.workers):
				if self.cancel:
					return False
				elif os.name == 'nt':
					p = Thread(target=self.worker, args=(self.work_queue, self.done_queue, workDir, frame))
				else:
					p = Process(target=self.worker, args=(self.work_queue, self.done_queue, workDir, frame))
				p.start()
				self.processes.append(p)
				self.work_queue.put('STOP')

			for p in self.processes:
				if self.cancel:
					return False
				p.join()

			self.done_queue.put('STOP')
			print "\n"
			
			if not self.zf:
				for status in iter(self.done_queue.get, 'STOP'):
					print status
			
			if self.zf:
				files = []
				for f in iter(self.done_queue.get, 'STOP'): #TODO: reorder first?
					files.append(f)
				files.sort()
				for f in files:
					filename = self.LastFileInPath(f[:-4])
					print 'zipping file :'+filename
					self.zf.write(f, arcname=filename)
					os.remove(f)
				self.zf.close()
				self.zf = None
			
			print "\n"
			print "Finished downloading chapter"
			print "\n"
		else:
			print "No URLs found"
			
		wx.CallAfter(frame.UiPrint, 'Finished')
		wx.CallAfter(frame.EnableCancel, True)
		
		return not self.cancel and i != 1
	
	def findExtension(self, path, i):

		for s in self.extensions:
			if (self.testURL(path + s) != False):
				return path + s
		
		form = self.FormatNumber(i + 1, 2)
		for s in self.extensions:
			url = path + "-" + form + s
			if (self.testURL(url) != False):
				return url

		return None
	
	def testURL(self, url):
		
		r = self.http.request('GET', url, headers=self.buildHeaders())
		self.updateSession(r)
		return r.data if r.status == 200 else False
	
	def findFormat(self, url, referer):
		
		r = self.http.request('GET', url, headers=self.buildHeaders({'Referer':referer, 'supress_webtoon':'t'}))
		self.updateSession(r)
		dom = hlxml.fromstring(r.data)
		img = dom.xpath(".//*[@id='comic_page']")[0]
		src = img.get('src')

		if src is not None:
			if src[0:10] == "http://img":
				src = "http://cdn" + src[10:] #Try CDN first
			return src
		
		return False
	
	def findGroupName(self, url):
		
		r = self.http.request('GET', url, headers=self.buildHeaders())
		self.updateSession(r)
		dom = hlxml.fromstring(r.data)
		sel = dom.xpath(".//*[@name='group_select']")
		if len(sel) > 0:
			val = sel[0].value
			if val is not None:
				val = val[:val.rindex('/')] #Strip language
				val = val[:val.rindex('/')] #Strip chapter id
				val = val[val.rindex('/')+1:] #Get group name
				val = val[:val.rindex('-')] #Strip group id
				return val
		return False
	
	def Download(self, url, workDir, frame):
		if self.cancel:
			return False
		filep = URLParser.LastFileInPath(self, url)
		lFile = workDir + "/" + filep
		if os.path.isfile(lFile) and os.path.getsize(lFile) == int(http.urlopen('GET', url).headers["Content-Length"]):
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

	def getUpdates(self, url, lastParsed):

		req = self.http.request_encode_body('GET', url)
		
		if req.data[0:5] == 'ERROR':
			return [False, 'Invalid RSS feed']

		xml = etree.fromstring(req.data)
		items = xml.xpath('//item')
		newItems = ''

		newDateStr = lastParsed
		if len(lastParsed) > 0:
			newDate = lastParsed = strptime(lastParsed, "%a, %d %b %Y %H:%M:%S +0000")
		else:
			newDate = False
		
		if len(items) > 0:
			for item in items:
				dateStr = item.xpath('.//pubDate')[0].text
				date = strptime(dateStr, "%a, %d %b %Y %H:%M:%S +0000")
				if len(lastParsed) == 0 or date > lastParsed:
					if len(newItems) > 0:
						newItems += '\n'
					newItems += item.xpath('.//link')[0].text
					if not newDate or date > newDate:
						newDate = date
						newDateStr = dateStr
		
		return [True, newDateStr, newItems]


def LastFolderInPath(path):
	start = path.rindex('/')
	newPath = path[:start]
	start = newPath.rindex('/')
	return newPath[start + 1:]
