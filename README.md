# Batoto is shutting down. As such, this application will no longer be developed.

**The code will remain here in case any Batoto clones pop up, or someone wants to re-use some of the code. However, this software should be considered unmaintained from here on out.**



batoto-downloader-py
====================
<br>
Uses wxpython: http://www.wxpython.org/download.php#stable<br>
Testing done with python 2.7.5 and wxpython 2.8.12.1<br>
Also uses lxml: http://lxml.de/installation.html<br>
<h4>*Note: if you cannot use lxml, or if you encounter problems with urllib3, you can still access the old, more thoroughly-tested version here: https://github.com/koroshiya/batoto-downloader-py/tree/urllib2</h4>
<br>
batoto-downloader-py is a graphical utility for downloading chapters and series from the website Batoto.<br>
Files will be downloaded into your home directory (or Documents directory for Windows) and placed
into appropriate folders.<br>
<br>
To begin:<br>
-paste a url into the URL field at the top of the application<br>
-Click "Add URL"<br>
-Repeat for each series/chapter you want to download<br>
-Click on the appropriate "Parse" button (the names are self-explanatory)<br>
-The series/chapters will begin downloading<br>
<br>
Example series URL: http://bato.to/comic/_/comics/kingdom-r642<br>
Example chapter URL: http://bato.to/read/_/272903/kingdom_v37_ch402_by_turnip-farmers<br>
<br>
The first example URL would create a folder called "kingdom-r642".<br>
It would then create individual folders inside there for each chapter.<br>
Each chapter folder would contain its own pages.<br>
<br>
The second example URL would create a folder called "kingdom_v37_ch402_by_turnip-farmers".<br>
All of the chapter's pages would be downloaded into that directory.<br>
<br>
<br>
<br>
Foreign comics haven't been tested and may not work at all.<br>
Only comics translated into English have been tested.
