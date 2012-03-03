# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib2
import urllib
import re
import string
import sys
import os
import xunlei

# Offline Xunlei 

# Plugin constants 
__addonname__ = "迅雷视频(XunLei)"
__addonid__ = "plugin.video.xunlei"
__addon__ = xbmcaddon.Addon(id=__addonid__)
__addonicon__ = os.path.join( __addon__.getAddonInfo('path'), 'icon.png' )
__addoncookie__ = os.path.join( __addon__.getAddonInfo('path'), 'xunlei.cookie')
__settings__ = xbmcaddon.Addon(__addonid__)

UserAgent = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_5) '
            'AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.218 Safari/535.1')

def create_xunlei_client():
	return xunlei.XunLeiClient(__settings__.getSetting('username'), 
								__settings__.getSetting('password'), 
								__addoncookie__)

def is_media_file(ext):
	media_list = ['.mkv', '.avi', '.mp4', '.rmvb', 'wmv']
	for i in media_list:
		if i == ext:
			return True
	return False	

def get_root_list():
	client = create_xunlei_client()
	items = client.read_all_completed()
	total = len(items)
	for i in items:
		name, file_ext = os.path.splitext(i['name'].encode('utf-8'))
		xbmc.log(name, xbmc.LOGERROR)
		if not is_media_file(file_ext):
				continue
		download_url = i['xunlei_url'].encode('utf-8')
		li = xbmcgui.ListItem(name + file_ext)
		if download_url:
			u = '%s?mode=10&name=%s&url=%s' % (sys.argv[0], urllib.quote_plus(name), urllib.quote_plus(download_url))
			xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, total)
		elif i['type'] == 'bt':
			u = '%s?mode=20&name=%s&url=%s&id=%s' % (sys.argv[0], urllib.quote_plus(name), urllib.quote_plus('bt_download_url'), i['id'])
			xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True, total)
		xbmc.log(u, xbmc.LOGERROR)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def get_bt_list(id):
	client = create_xunlei_client()
	task = client.get_task_by_id(id)
	items = client.list_bt(task)
	total = len(items)
	for i in items:
		name, file_ext = os.path.splitext(i['name'].encode('utf-8'))
		xbmc.log(i['name'].encode('utf-8'), xbmc.LOGERROR)
		if not is_media_file(file_ext):
			continue
		download_url = i['xunlei_url'].encode('utf-8')
		u = '%s?mode=10&name=%s&url=%s' % (sys.argv[0], urllib.quote_plus(name), urllib.quote_plus(download_url))
		li = xbmcgui.ListItem(name + file_ext)
		xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, total)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))


def play_video(name, download_url):
	client = create_xunlei_client()
	data = {
         'User-Agent': UserAgent,
         'Cookie': "gdriveid=%s" % client.get_gdriveid()
    }
    # try to get the redirect url
	request = urllib2.Request(download_url)
	request.add_header('User-Agent', UserAgent)
	request.add_header('Cookie', 'gdriveid=%s' % client.get_gdriveid())
	response = urllib2.urlopen(request)
	video_url = response.geturl()
	video_url = '%s|%s' % (video_url, urllib.urlencode(data))
	playlist = xbmc.PlayList(1)
	playlist.clear()
	listitem = xbmcgui.ListItem("", thumbnailImage = __addonicon__)
	listitem.setInfo(type="Video", infoLabels={"Title":name})
	playlist.add(video_url, listitem)
	xbmc.Player().play(playlist)

def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param

params = get_params()
mode = None
name = None
id = None
cat = None
area = None
year = None
order = None
page = '1'
url = None
thumb = None
res = 0

try:
    res = int(params["res"])
except:
    pass
try:
    thumb = urllib.unquote_plus(params["thumb"])
except:
    pass
try:
    url = urllib.unquote_plus(params["url"])
except:
    pass
try:
    page = urllib.unquote_plus(params["page"])
except:
    pass
try:
    order = urllib.unquote_plus(params["order"])
except:
    pass
try:
    year = urllib.unquote_plus(params["year"])
except:
    pass
try:
    area = urllib.unquote_plus(params["area"])
except:
    pass
try:
    cat = urllib.unquote_plus(params["cat"])
except:
    pass
try:
    id = urllib.unquote_plus(params["id"])
except:
    pass
try:
    name = urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode = int(params["mode"])
except:
    pass

if mode == None:
    get_root_list()
elif mode == 10:
    play_video(name,url)
elif mode == 20:
	get_bt_list(id)

