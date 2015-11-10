#!/usr/bin/env python2.7

#from __future__ import unicode_literals
import sys
import wx
from lxml import html as hlxml
from lxml import etree

import certifi
import urllib3
import pyOpenSSL
import urllib3.contrib.pyopenssl
urllib3.contrib.pyopenssl.inject_into_urllib3()

import os
from multiprocessing import Queue, current_process
if os.name == 'nt':
	from threading import Thread
else:
	from multiprocessing import Process
import zipfile
import tempfile
from time import strptime, strftime

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
			self.http = urllib3.ProxyManager(
				proxy,
				#cert_reqs='CERT_REQUIRED', # Force certificate check.
    			ca_certs=certifi.where()
			)
		else:
			self.http = urllib3.PoolManager(
				#cert_reqs='CERT_REQUIRED', # Force certificate check.
    			ca_certs=certifi.where()
			)


	def Cancel(self, state):
		self.cancel = True
	
	def ContinueDownload(self, url, workdir, frame):
		if not self.cancel:
			filep = self.LastFileInPath(url)
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
			status_code = self.ContinueDownload(url, workdir, frame)
			done_queue.put(status_code)
		return True
	
	def downloadFullSeries(self, url, home, frame, isZip, language, cookies):

		if url[-1] != "/":
			url += "/"
		try:
			workDir = home + "/" + self.LastFolderInPath(url)
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
			self.downloadFromURL(chapter, workDir, frame, isZip, language, cookies)
			
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

	def downloadFromURL(self, url, home, frame, isZip, language, cookies):
		if len(url) < 7:
			return False
		elif (len(url) < 19 or not(url[:14] == "http://bato.to" or url[:15] == "https://bato.to" or url[:18] == "http://www.bato.to" or url[:19] == "https://www.bato.to")):
			return False
		elif "bato.to/comic/" in url:
			return self.downloadFullSeries(url, home, frame, isZip, language, cookies)

		info = self.getChapterInfo(url, cookies)
		
		lastPath = info['series'] + " - " + info['chapter'] + " by " + info['group']
		workDir = home + "/" + lastPath
		self.zf = None
		if isZip:
			filename = workDir + '.zip'
			if os.path.exists(filename):
				os.remove(filename)
			self.zf = zipfile.ZipFile(filename, mode='w')
		elif not os.path.isdir(workDir):
			os.makedirs(workDir)
		
		wx.CallAfter(frame.UiPrint, 'Indexing...')

		if len(info['urls']) > 0:
			urls = info['urls']
		else:
			urls = []
			for i in range(1, info['pages']+1):
				try:
					wx.CallAfter(frame.UiPrint, 'Indexing page ' + str(i))
					print 'Indexing page ' + str(i)

					pageUrl = self.findExtension(info['format'], i)
					if pageUrl and self.Download(pageUrl, workDir, frame):
							urls.append(pageUrl)
				except Exception, e:
					break
				if self.cancel:
					break
		
		if self.cancel:
			return False
		
		print "\n"		
		print "Downloading " + lastPath
		print "-----------------------"

		wx.CallAfter(frame.UiPrint, 'Downloading '+lastPath)
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
		
		return not self.cancel and len(urls) > 0
	
	def findExtension(self, path, i):

		for s in self.extensions:
			url = path + 'img' + format(i, "06") + s
			if (self.testURL(url) != False):
				return url

		return None
	
	def testURL(self, url):
		
		cookies = {}
		if '#' in url:
			uuid = url[url.rindex('#')+1:]
			referer = self.AbsoluteFolder(url) + "reader#" + uuid + "_1"
			cookies = {'Referer':referer, 'supress_webtoon':'t'}

		r = self.http.urlopen('GET', url, headers=self.buildHeaders(cookies))
		self.updateSession(r)
		return r.data if r.status == 200 else False

	def getChapterInfo(self, url, cookies):
		if '#' in url:
			uuid = url[url.rindex('#')+1:]
			if len(url) > 0:
				referer = self.AbsoluteFolder(url) + "reader#" + uuid + "_1"
				url = str(self.AbsoluteFolder(url) + 'areader?id='+uuid+'&p=1')
				cookies = {'Referer':referer, 'supress_webtoon':'t'}

				req = self.http.urlopen('GET', url, headers=self.buildHeaders(cookies))
				dom = hlxml.fromstring(req.data)

				with open('/tmp/batoto.txt', 'w') as dlfile:
					dlfile.write(req.data)

				group = dom.xpath(".//*[@name='group_select']/option/text()")[0]
				group = group[:group.rindex(' -')]
				series = dom.xpath(".//ul/li/a")[0].text
				chapter = dom.xpath(".//*[@name='chapter_select']/option/text()")[0]
				pFormat = dom.xpath(".//img[starts-with(@src, 'http://img.bato.to/comics/2')]/@src")
				#comics/2 ensures we only get comics from year 2000 onwards; not misc images in comics dir
				pages = dom.xpath(".//*[@name='page_select']")
				if len(pages) > 0:
					pages = len(pages[0])
					pFormat = self.AbsoluteFolder(pFormat[0])
				else:
					pages = 1
					urls = pFormat
					pFormat = ''

				vals = {
					'group':group,
					'series':series,
					'chapter':chapter,
					'pages':pages,
					'format':pFormat,
					'urls':urls
				}
				print vals
				return vals
		return None

	def suppressWebtoon(self, url):
		if 'supress_webtoon' not in url:
			url += '&supress_webtoon=t' #Doesn't affect normal chapters, but makes webtoons easier to parse
		return str(url)
	
	def Download(self, url, workDir, frame):
		print 'downloading...'
		if self.cancel:
			return False
		filep = self.LastFileInPath(url)
		lFile = workDir + "/" + filep
		if os.path.isfile(lFile) and os.path.getsize(lFile) == int(self.http.urlopen('GET', url, headers=self.buildHeaders()).headers["Content-Length"]):
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

	def login(self, username, password):

		url = "https://bato.to/forums/"
		r = self.http.request('GET', url)
		dom = hlxml.fromstring(r.data)

		loginDiv = dom.xpath(".//*[@id='login']")[0]
		auth_key = loginDiv.xpath(".//*[@name='auth_key']")[0].value
		referer = loginDiv.xpath(".//*[@name='referer']")[0].value

		url = 'https://bato.to/forums/index.php?app=core&module=global&section=login&do=process'
		headers = {'cookie': r.getheader('set-cookie')}
		fields = {
			'anonymous':1,
			'rememberMe':1,
			'auth_key':auth_key,
			'referer':referer,
			'ips_username':username,
			'ips_password':password,
		}

		r = self.http.request_encode_body('POST', url, fields, headers, redirect=False)
		encHeaders = self.parseHeaders(r)

		#return False
		
		if 'member_id' in encHeaders:
			print 'login successful'
			return {'cookie': encHeaders} #Login successful
		else:
			print 'login failed'
			return False #Login failed

	#This method takes a request object, grabs its headers, and turns them into a dict.
	#Note, however, that it strips out duplicate headers, and doesn't differentiate
	#between individual set-cookie commands.
	#This should ideally be fixed, but is not a priority.
	def parseHeaders(self, r):

		#print r.getheaders()

		encHeaders = r.getheader('set-cookie') #.replace('httponly,', '').split("; ") #Get headers as list
		dictHeaders = {}

		# for h in encHeaders:
		# 	if '=' in h:
		# 		h = h.strip()
		# 		h = h.split("=", 1) #Turn each header into key/value pair
		# 		dictHeaders[h[0]] = h[1] #Add header to dictionary

		#return dictHeaders
		return encHeaders

	#Returns minutes until time passed in lapses
	def minutesUntil(self, time1):
		strFormat = "%a, %d-%b-%Y %H:%M:%S GMT"
		time1 = strptime(time1, strFormat)
		cTime = strftime("%a %b %d %H:%M:%S %Y")
		cTime = strptime(cTime)

		if time1 > cTime:
			return 0
		else:
			return (time.mktime(cTime) - time.mktime(time1)) / 60

	def getCookie(self, cookie, name):
		if cookie:
			if 'cookie' in cookie:
				cookie = cookie['cookie']
			if name in cookie:
				print cookie
				cookie = cookie[cookie.index(name) : ]
				print cookie
				return cookie[cookie.index('=')+1 : cookie.index(';')]
		return False

	def buildHeaders(self, headers={}):
		if self.cookies:
			headers['Cookie'] = self.cookies
		return headers
	
	def updateSession(self, r):
		self.cookies = r.getheader('set-cookie')


def LastFolderInPath(path):
	start = path.rindex('/')
	newPath = path[:start]
	start = newPath.rindex('/')
	return newPath[start + 1:]
