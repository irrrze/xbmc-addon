
import urllib
import urllib2
import re
import time
import os.path
import simplejson as json
import mechanize

UserAgent = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_5) '
            'AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.218 Safari/535.1')

class XunLeiClient(object):
	"""Offline XunLei Client"""
	def __init__(self, username, password, cookie_path):
		self.username = username
		self.password = password
		self.cookie_path = cookie_path
		self.cookiejar = mechanize.LWPCookieJar()
		self.opener = self.build_opener()
		if not os.path.exists(self.cookie_path):
			self.login()
		else:
			self.load_cookies()
			self.id = self.get_userid()
			self.set_page_size(9999)

	def build_opener(self):
		browser = mechanize.UserAgent()
		browser.set_handle_equiv(False)
		browser.set_handle_gzip(False)
		browser.set_handle_redirect(True)
		browser.set_handle_robots(False)
		browser.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
		browser.set_seekable_responses(False)
		browser.set_cookiejar(self.cookiejar)
		browser.addheaders = [
			('User-agent', UserAgent),
		]
		return browser 

	def urlopen(self, url, data=None):
		if data:
			data = urllib.urlencode(data)
		return self.opener.open(url, data)
	
	def load_cookies(self):
		self.cookiejar.load(self.cookie_path, ignore_discard=True, ignore_expires=True)

	def save_cookies(self):
		if self.cookie_path:
			self.cookiejar.save(self.cookie_path, ignore_discard=True)
	
	def set_cookie(self, domain, k, v):
		c = mechanize.Cookie(version=0, name=k, value=v, port=None, port_specified=False, domain=domain, domain_specified=True, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={}, rfc2109=False)
		self.cookiejar.set_cookie(c)

	def get_cookie(self, domain, k):
		if self.has_cookie(domain, k):
			return self.cookiejar._cookies[domain]['/'][k].value

	def has_cookie(self, domain, k):
		return domain in self.cookiejar._cookies and k in self.cookiejar._cookies[domain]['/']

	def set_gdriveid(self, id):
		self.set_cookie('.vip.xunlei.com', 'gdriveid', id)

	def get_gdriveid(self):
		return self.get_cookie('.vip.xunlei.com', 'gdriveid')

	def has_gdriveid(self):
		return self.has_cookie('.vip.xunlei.com', 'gdriveid')

	def get_userid(self):
		return self.get_cookie('.xunlei.com', 'userid')

	def set_page_size(self, n):
		self.set_cookie('.vip.xunlei.com', 'pagenum', str(n))

	def set_page_size(self, n):
		self.set_cookie('.vip.xunlei.com', 'pagenum', str(n))


	def current_timestamp(self):
		return int(time.time()*1000)

	def login(self):
		cachetime = self.current_timestamp()
		check_url = 'http://login.xunlei.com/check?u=%s&cachetime=%d' % (self.username, cachetime)
		login_page = self.urlopen(check_url).read()
		verifycode = self.get_cookie('.xunlei.com', 'check_result')[2:].upper()
		password = encypt_password(self.password, verifycode)
		login_page = self.urlopen('http://login.xunlei.com/sec2login/', data={'u': self.username, 'p': password, 'verifycode': verifycode})
		self.id = self.get_userid()
		login_page = self.urlopen('http://dynamic.lixian.vip.xunlei.com/login?cachetime=%d&from=0' % self.current_timestamp()).read()
		assert self.is_login_ok(login_page), 'login failed'
		self.save_cookies()

	def is_login_ok(self, html):
		return len(html) > 512

	def read_all_completed(self):
		return self.read_all_tasks(2)

	def read_all_tasks(self, st=0):
		all_links = []
		links, next_link = self.read_task_page(st)
		all_links.extend(links)
		while next_link:
			links, next_link = self.read_task_page_url(next_link)
			all_links.extend(links)
		return all_links

	def read_task_page(self, st, pg=None):
		if pg is None:
			url = 'http://dynamic.cloud.vip.xunlei.com/user_task?userid=%s&st=%d' % (self.id, st)
		else:
			url = 'http://dynamic.cloud.vip.xunlei.com/user_task?userid=%s&st=%d&p=%d' % (self.id, st, pg)
		return self.read_task_page_url(url)

	def read_task_page_url(self, url):
		req = self.urlopen(url)
		page = req.read().decode('utf-8')
		if not self.has_gdriveid():
			gdriveid = re.search(r'id="cok" value="([^"]+)"', page).group(1)
			self.set_gdriveid(gdriveid)
			self.save_cookies()
		tasks = parse_tasks(page)
		for t in tasks:
			t['client'] = self
		pginfo = re.search(r'<div class="pginfo">.*?</div>', page)
		match_next_page = re.search(r'<li class="next"><a href="([^"]+)">[^<>]*</a></li>', page)
		return tasks, match_next_page and 'http://dynamic.cloud.vip.xunlei.com'+match_next_page.group(1)

	def get_task_by_id(self, id):
		tasks = self.read_all_tasks(0)
		for x in tasks:
			if x['id'] == id:
				return x
		raise Exception('Not task found for id '+id)

	def list_bt(self, task):
		url = 'http://dynamic.cloud.vip.xunlei.com/interface/fill_bt_list?callback=fill_bt_list&tid=%s&infoid=%s&g_net=1&p=1&uid=%s&noCacheIE=%s' % (task['id'], task['bt_hash'], self.id, self.current_timestamp())
		html = self.urlopen(url).read().decode('utf-8')
		return parse_bt_list(html)

def encypt_password(password, verify_code):
	from md5 import md5
	m = md5()
	m.update(password)
	md5pwd = m.hexdigest()
	m = md5()
	m.update(md5pwd)
	md5pwd = m.hexdigest()
	m = md5()
	m.update(md5pwd + verify_code)
	md5pwd = m.hexdigest()
	return md5pwd

def parse_tasks(html):
	rwbox = re.search(r'<div class="rwbox".*<!--rwbox-->', html, re.S).group()
	rw_lists = re.findall(r'<div class="rw_list".*?<!-- rw_list -->', rwbox, re.S)
	return map(parse_task, rw_lists)

def parse_task(html):
	inputs = re.findall(r'<input[^<>]+/>', html)
	def parse_attrs(html):
		return dict((k, v1 or v2) for k, v1, v2 in re.findall(r'''\b(\w+)=(?:'([^']*)'|"([^"]*)")''', html))
	info = dict((x['id'], unescape_html(x['value'])) for x in map(parse_attrs, inputs))
	mini_info = {}
	mini_map = {}
	#mini_info = dict((re.sub(r'\d+$', '', k), info[k]) for k in info)
	for k in info:
		mini_key = re.sub(r'\d+$', '', k)
		mini_info[mini_key] = info[k]
		mini_map[mini_key] = k
	taskid = mini_map['durl'][4:]
	url = mini_info['f_url']
	task_type = re.match(r'[^:]+', url).group()
	task = {'id': taskid,
			'type': task_type,
			'name': mini_info['durl'],
			'status': int(mini_info['d_status']),
			'status_text': {'0':'waiting', '1':'downloading', '2':'completed', '3':'failed', '5':'pending'}[mini_info['d_status']],
			'size': int(mini_info['ysfilesize']),
			'original_url': mini_info['f_url'],
			'xunlei_url': mini_info['dl_url'],
			'bt_hash': mini_info['dcid'],
			'dcid': mini_info['dcid'],
			}
	return task

def parse_bt_list(js):
	result = json.loads(re.match(r'^fill_bt_list\((.+)\)\s*$', js).group(1))['Result']
	files = []
	for record in result['Record']:
		files.append({
			'id': int(record['taskid']),
			'index': record['id'],
			'type': 'bt',
			'name': record['title'], # TODO: support folder
			'status': int(record['download_status']),
			'status_text': {'0':'waiting', '1':'downloading', '2':'completed', '3':'failed'}[record['download_status']],
			'size': int(record['filesize']),
			'original_url': record['url'],
			'xunlei_url': record['downurl'],
			'dcid': record['cid'],
			'speed': '',
			'progress': '%s%%' % record['percent'],
			})
	return files

def unescape_html(html):
	import xml.sax.saxutils
	return xml.sax.saxutils.unescape(html)

