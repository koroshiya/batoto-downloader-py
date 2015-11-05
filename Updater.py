#!/usr/bin/env python2.7

import threading, wx, time, urllib2, sys, os, tarfile, shutil, hashlib, importlib
os.chdir(os.path.dirname(os.path.realpath(__file__)))

class MainFrame(wx.Frame):
    def __init__(self, parent, ID, title, missing_modules):
        wx.Frame.__init__(self, parent, ID, title, size=(300,150))

        self.txt = wx.StaticText(self, 0, "Downloading module...")
        self.bar = wx.Gauge(self, range=100)
        self.buCancel = wx.Button(self, label="Cancel")
        self.bt = wx.Button(self, wx.ID_OK)

        siMainV = wx.BoxSizer(wx.VERTICAL)
        siMainV.Add(self.txt, 1, wx.EXPAND | wx.CENTER)
        siMainV.Add(wx.StaticLine(self,), 0, wx.ALL|wx.EXPAND, 5)
        siMainV.Add(self.bar, 2, wx.EXPAND | wx.CENTER)
        siMainV.Add(wx.StaticLine(self,), 0, wx.ALL|wx.EXPAND, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.buCancel, 3, wx.EXPAND)
        box.Add(self.bt, 4, wx.EXPAND)

        siMainV.Add(box, 5, wx.EXPAND)

        self.SetAutoLayout(True)
        self.SetSizer(siMainV)
        self.Layout()
        #self.Fit()

        self.Bind(wx.EVT_BUTTON, self.onClose, self.bt)
        self.Bind(wx.EVT_BUTTON, self.onCancel, self.buCancel)
        self.bt.Disable()
        self.modules = missing_modules

        workThread = threading.Thread(target=self.doWork)
        workThread.start()

    def doWork(self):

        baseUrl = 'https://pypi.python.org/packages/source/'

        for m in self.modules:
            version = m[0] + '-' + m[1]
            if len(m[4]) > 0:
                fName = m[4] + '-' + m[1]
            else:
                fName = version
            fileName = fName + '.tar.gz'
            url = baseUrl + m[0][0] + '/' + m[0] + '/' + fileName

            self.chunk_read(url, fileName)

            if self.isCanceling():
                print 'canceling'
                self.silentremove(fileName)
                break

            if not self.sha256(fileName, m[2]):
                self.silentremove(fileName)
                #tkMessageBox.showinfo('Download error', 'Failed to download required module: '+m[0])
                break

            import tarfile
            tar = tarfile.open(fileName)
            tar.extractall()
            tar.close()
            self.silentremove(fileName)

            shutil.move(fName+'/'+m[3], './')
            shutil.rmtree(fName)
            os.rename(m[3], m[0])

            wx.CallAfter(
                self.updateGauge,
                100,
                "Extracting module: %s" % (m[0],)
            )

        wx.CallAfter(self.buCancel.Disable)


        for m in self.modules:
            try:
                importlib.import_module(m[0])
            except ImportError:
                wx.CallAfter(self.bt.Enable)
                wx.CallAfter(
                    self.updateGauge,
                    100,
                    "Download of module %s failed or canceled - Program aborting" % (m[0],)
                )

        self.onClose(None)

    def chunk_report(self, m, bytes_so_far, total_size):
        percent = float(bytes_so_far) / total_size
        percent = round(percent*100, 2)

        wx.CallAfter(
            self.updateGauge,
            int(percent),
            "Downloading module %s: %i%% complete" % (m[0], percent)
        )

    def chunk_read(self, url, fileName, chunk_size=8192, report_hook=None):
        print 'downloading: ' + url
        response = urllib2.urlopen(url)
        total_size = int(response.info().getheader('Content-Length').strip())
        bytes_so_far = 0

        with open(fileName, "wb") as dlFile:
          while 1:
              chunk = response.read(chunk_size)
              bytes_so_far += len(chunk)

              if not chunk: #Finished downloading
                 break
              elif self.isCanceling():
                 break

              dlFile.write(chunk)

              if report_hook:
                 report_hook(bytes_so_far, total_size)

    def sha256(self, fname, sha):
        hash = hashlib.sha256()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash.update(chunk)
        print 'hash of '+fname+' is '+hash.hexdigest()
        print 'comparing to '+sha
        return hash.hexdigest() == sha

    def isCanceling(self):
        return self.GetTitle() == "Cancelling..."

    def silentremove(self, filename):
        try:
            os.remove(filename)
        except OSError as e:
            pass

    def onCancel(self, e):
        self.txt.SetLabel("Aborting module download")
        self.SetTitle("Cancelling...")
        self.buCancel.Disable

    def onClose(self, e):
        wx.Exit()

    def updateGauge(self, value, message=""):
        self.bar.SetValue(value)
        if len(message) > 0:
            self.txt.SetLabel(message)