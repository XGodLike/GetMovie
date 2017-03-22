#coding:utf-8
import urllib2
import cookielib
import random
import threading
from bs4 import BeautifulSoup
import Useragent
from pymongo import MongoClient

#
goodNUM = 0
badNUM=0
URL = "http://www.xicidaili.com/nn/"
ip_file = './ip_list.txt'

m_ip_list=[]
ip_listTXT = "./ip.txt"
IP_db=None

def getHtml(url):
	global m_ip_list
	req_header={'User-Agent':'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome',
	'Accept':'text/html;1=0.9,*/*;q=0.8',
	'Accept-Charset':'utf-8',
	'Accept-Encoding':'*',
	'Connection':'close',
	'Referer':None
	}
	req_Header={'User-Agent':random.choice(Useragent.user_agents),
	'Accept':'text/html;1=0.9,*/*;q=0.8',
	'Accept-Charset':'utf-8',
	'Accept-Encoding': 'gzip',
	'Connection':'close',
	'Referer':'None'
	}
	#setProxy(get_random_ip(m_ip_list))
	cookie = cookielib.CookieJar()
	handler = urllib2.HTTPCookieProcessor(cookie)
	opener = urllib2.build_opener(handler)
	urllib2.install_opener(opener)
	req_timeout = 10

	req = urllib2.Request(url)
	response = urllib2.urlopen(req,None,req_timeout)
	html = response.read().decode('utf-8')
	return html



#获取西刺代理ip
def getXCIP(html):
	soup = BeautifulSoup(html,'lxml')
	ips = soup.find_all('tr')
	ip_list=[]
	for i in range(1,len(ips)):
		ip_info = ips[i]
		tds = ip_info.find_all('td')
		ip_list.append(tds[1].text+":"+tds[2].text)
	return ip_list	
#获取有代理ip
def getYDLIP(html):
	soup = BeautifulSoup(html,'lxml')
	ips = soup.find_all('div',{'class':'content'})
	ip_list=[]
	if ips:
		for iptag in ips:
			ip = iptag.find_all('p')
			print ip
			for i in range(0,len(ip)):
				ip_info = ip[i].string
				ip_info = ip_info[0:ip_info.index('@')]
				IP_db.insert(ip_info)
				print ip_info
				ip_list.append(ip_info)
	return ip_list	

def writeIP(ip_list):
	with open(ip_file,"a+") as wf:
		for ip in ip_list:
			wf.write(ip+'\n')

	return

def ReadIPlist():
	ip_list = []	
	with open(ip_listTXT,'r') as rf:
		lines = rf.readlines()
	return lines

def get_random_ip(ip_list):
	proxy_list = []
	for ip in ip_list:
		proxy_list.append('http://' + ip)
	proxy_ip = random.choice(proxy_list)
	proxies = {'http':proxy_ip}
	return proxies

def setProxy(proxy):
	enable = True
	proxy_handler = urllib2.ProxyHandler(proxy)
	unproxy_handler = urllib2.ProxyHandler({})
	if enable:
		opener = urllib2.build_opener(proxy_handler)
	else:
		opener = urllib2.build_opener(unproxy_handler)
	urllib2.install_opener(opener)

def checkIP():
	global goodNUM
	global badNUM
	#global ip_listTXT
	IPpool = []
	Checked = False
	#checked_file = open('./ip_checked.txt','w+')
	checked_file = open(ip_listTXT,'a+')
	pro = {}
	with open(ip_file ,'r+') as pf:
		ips = pf.readlines()		
		for ip in ips:
			ip = ip.replace('\n','')			
			pro['http'] = ip 
			print pro
			#proxy = {'http':pro}
			proxy_handler = urllib2.ProxyHandler(pro)
			opener = urllib2.build_opener(proxy_handler)
			urllib2.install_opener(opener)
			try:
				
				for x in range(0,10):
					req = urllib2.Request('http://www.baidu.com')
					html = urllib2.urlopen(req,None,5)
					if html.getcode() == 200:
						goodNUM += 1
						print '可用的代理IP:%' % ip
						checked_file.write(ip)
						IPpool.append(ip)
						Checked = True
						break
					else:
						print '第%d验证码IP' % x
						continue	
				if not Checked:
					print 'IP:%s不可用' % ip
					Checked=False			
			except Exception,e:
				badNUM += 1
				print Exception,":",e
				continue
	print 'good:%d\nbad:%d' % (goodNUM,badNUM)
	checked_file.close()
	return IPpool


def GetIP():
	#http://www.xicidaili.com/nn/
	#for i in range(1,100):
	#	url = URL+str(i)
	#	ip_list = getXCIP(getHtml(URL))
	#	print "获取第%d页的代理IP完成\n" % i
	#	writeIP(ip_list)

	#http://www.youdaili.net/Daili/
	url = 'http://www.youdaili.net/Daili/http/36043'#.html
	print url+".html"
	getYDLIP(getHtml(url+".html"))
	
	for i in range(1,5):
		url = "%s_%d\.html" % (url,i) 
		print url
		getYDLIP(getHtml(url))
		print "获取第%d页的代理IP完成\n" % i
		writeIP(ip_list)
	return 

class IPDB:
	def __init__(self,link_ip,link_port):
		self.link_ip = link_ip
		self.link_port = link_port


	def createDB(self):
		self.client = MongoClient(self.link_ip,self.port)
		self.IPDB = self.client['DL_IP']#代理ip数据库
		self.ip_db = self.IPDB['enable_ip']#可用的代理IP

	def findIP(self):
		return self.ip_db.find()	

	def insertDB(self,ip):
		self.ip_db.insert({"ip":ip})
	

	#删除数据库中的无用IP
	def deleteIP(self,ip)
		if self.ip_db.find({'ip':ip}).count()>0:
			self.ip_db.remove({'ip':ip})
			return True
		else:
			return False

	def checkIP(self,ip):
		pro_http = {}
		pro_http['http'] = ip
		proxy = urllib2.ProxyHandler(pro_http)
		opener = urllib2.build_opener(proxy)
		urllib2.install_opener(opener)
		url = 'http://www.baidu.com'
		res = urllib2.urlopen(url)
		if res == 200:
			print '*===========数据库中当前的ip可用==============*'
		else:
			print '*+++++++++++数据库中ip:%s不可用++++++++++++++*' % ip
			if deleteIP(ip):
				print '*-----------删除数据库中ip:%s----------------*' % ip
			else:
				print '************数据库中没有找到ip:%s**************' % ip

	def checkDB(self):
		self.ip_db.update()
		dbip_list = findIP()
		if dbip_list:
			for ip in dbip_list:
				checkIP(ip)	
		
	
	
if __name__ == "__main__":
	global m_ip_list
	IP_db = IPDB('localhost',27017)
	while True:
		try:
			m_ip_list = ReadIPlist()
			GetIP()	
			#checkIP()
			IP_db.checkDB()
			break
		except urllib2.URLError,e1:
			if hasattr(e1,'reason'):
				print "Reason:",e1.reason
			if hasattr(e1,'code'):
				print "Error code:",e1.code	
			continue		
		except Exception,e:
			print Exception,':',e
			continue
		ipf.close()
		checked_file.close()


