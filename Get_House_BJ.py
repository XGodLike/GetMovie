#*-* coding:utf-8 *-*

import sys
import re
import urllib2
import random
import Useragent
import traceback
from bs4 import BeautifulSoup
import string,time
from pymongo import MongoClient

Daili_URL = "http://www.xicidaili.com/nn/"
Postion='http://bj.lianjia.com'
URL='http://bj.lianjia.com/ershoufang/'

ip_listTXT = "./ip.txt"
m_ip_list=u''
NUM=0
m_Pos = u''
m_site=u'链家房产'


#/////////////////设置IP代理//////////////////////////////
def getIP(html):
	soup = BeautifulSoup(html,'lxml')
	ips = soup.find_all('tr')
	ip_list=[]
	for i in range(1,len(ips)):
		ip_info = ips[i]
		tds = ip_info.find_all('td')
		ip_list.append(tds[1].text+":"+tds[2].text)
	return ip_list	

def WriteIPlistTXT(ip_list):
	with open(ip_listTXT,'w+') as wf:
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
		#proxy_list.append('http://' + ip)
		proxy_list.append(ip.replace('\n',''))
	proxy_ip = random.choice(proxy_list)
	proxies = {'http':proxy_ip}
	print proxies
	return proxies

#设置代理IP
def setProxy(proxy):
	enable = True
	proxy_handler = urllib2.ProxyHandler(proxy)
	unproxy_handler = urllib2.ProxyHandler({})
	if enable:
		opener = urllib2.build_opener(proxy_handler)
	else:
		opener = urllib2.build_opener(unproxy_handler)
	urllib2.install_opener(opener)
#///////////////////////////////////////////////
#最简单的html内容,有些防爬虫网址不行
def getHtml(url):
	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	html = response.read()
	return html

#伪装成浏览器的爬虫/39.0.2171.95 Safari/537.36
def getHtmlWithHead(url):
	global m_ip_list
	req_header={'User-Agent':'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome',
	'Accept':'text/html;1=0.9,*/*;q=0.8',
	'Accept-Charset':'utf-8',
	#'Accept-Encoding':'*',
	'Connection':'close',
	'Referer':None
	}
	#req_header={'User-Agent':random.choice(Useragent.USER_AGENTS),
	#'Accept':'text/html;1=0.9,*/*;q=0.8',
	#'Accept-Charset':'utf-8',
	#'Accept-Encoding': 'gzip',
	#'Connection':'close',
	#'Referer':'None'
	#}
	
	setProxy(get_random_ip(m_ip_list))
	#setProxy({'http':'221.180.170.3:80'})
	req_timeout = 10
	req = urllib2.Request(url,None,req_header)
	#req = urllib2.Request(url)
	response = urllib2.urlopen(req,None,req_timeout)
	#response = urllib2.urlopen(req)
	html = response.read().decode('utf-8')
	return html


#获取链接_北京所有的区域,及其对应的网址
def getTags(html):
	global m_type
	soup = BeautifulSoup(html,'lxml')
      	tags_all = soup.find_all('div',{'data-role' : 'ershoufang'})
	if tags_all:
		re_tags = r'<a href=\"(.*?)\" title=\".*?\">(.+?)</a>'
		p = re.compile(re_tags, re.DOTALL)
		tags = p.findall(str(tags_all)) 
	else:
		return ""

	tags_url = {}
	if tags:
		for tag in tags:   
			tag_url = Postion + tag[0].decode('utf-8') 
			m_Pos = tag[1].decode('utf-8')   
			tags_url[m_Pos] = tag_url      
	else:   
		print "Not Find" 
	return tags_url


#获取每个区域的最大页数
def get_pages(tag_url):
	#tag_html = getHtml(tag_url)
	tag_html = getHtmlWithHead(tag_url)
	soup = BeautifulSoup(tag_html,'lxml')
	div_page = soup.find_all('div', {'class' : 'page-box fr'})
	re_pages = r'<div class=\"page-box house-lst-page-box\" comp-module=\"page\" page-data=\'\{\"totalPage\":(\d*),\"curPage\":.*?\}\' page-url=\".*?\"></div>'
	p = re.compile(re_pages,re.DOTALL)
	pages = p.findall(str(div_page))
	if len(pages) >= 1:	
		return pages[0]
	else:
		return 1

#获取房屋描述标题的信息
def getHouseTitle(html):
	re_housetitile = r'<a class="" data-el=\"ershoufang\" data-log_index=\"\d*\" data-sl=.*?href=\"(.*?)\" target=\"_blank\">(.*?)</a>'
	p = re.compile(re_housetitile,re.DOTALL)
	houseTitle = p.findall(html)
	if houseTitle:
		return houseTitle[0][1],houseTitle[0][0]
	else: 
		return "",""

#获取房屋信息{户型,面积,朝向,装修,有无电梯}
def getHouseInfo(html):
	re_info = r'<a data-el="region" data-log_index=\"\d*\" href=\".*?\" target=\"_blank\">(.*?) </a>(.*?)</div>' 

	p = re.compile(re_info,re.DOTALL)
	info = p.findall(html)
	if info:
		return info[0][0],info[0][1]
	else:
		return "",""

#获取房屋楼层信息
def getFlood(html):
	re_flood = r'<div class="positionInfo"><span class="positionIcon"></span>(.*?)<a href=.*? target="_blank">.*?</a></div>'
	p = re.compile(re_flood,re.DOTALL)
	flood = p.findall(html)
	if flood:
		return flood[0]
	else:
		return ""

#获取价格信息
def getPrice(html):
	re_tprice = r'<div class=\"totalPrice\">.*?<span>(.*?)</span>\s*(.*?)\s*</div>'
	p = re.compile(re_tprice,re.DOTALL)
	tprice = p.findall(html)
	if tprice:
		price1 = tprice[0][0]+tprice[0][1]
	else:
		price1=""
	
	re_unprice = r'<div class=\"unitPrice\" data-hid=\".*?\" data-price=\".*?\" data-rid=\".*?\"><span>(.*?)</span></div>'
	p = re.compile(re_unprice,re.DOTALL)
	unrince = p.findall(html)
	if unrince:
		price2 = unrince[0]
	else:
		price2=""
	return price1,price2

#获取其他信息{距离地铁,是否满五年,是否随时看房}
def getTagInfo(html):
	soup  = BeautifulSoup(html,'lxml')
	#tags = soup.find_all('div',{'class':'tag'})
	#re_tag = r'<span class=\"(.*)\">(.*)</span>' 
	#p = re.compile(re_tag,re.DOTALL)
	tagdic = {}
	#if tags:	
	subway = soup.find_all('span',attrs={'class':'subway'})
	if subway:
		tagdic['subway'] = subway[0].string
	taxfree = soup.find_all('span',attrs={'class':'taxfree'})
	if taxfree:
		tagdic['taxfree'] = taxfree[0].string
	haskey = soup.find_all('span',attrs={'class':'haskeys'})
	if haskey:
		tagdic['haskey'] = haskey[0].string
	#taginfo = p.findall(str(tags[0])) 
	print tagdic
	return tagdic


#获取详细的房屋信息:{区域,小区,楼层,户型,面积,朝向,装修,有无电梯,总价,单价}
def getHouse(html):
	global NUM
	global m_type	
	global m_site

	try:
		soup = BeautifulSoup(html,'lxml')
		#divs = soup.find_all('ul', {'class' : 'sellListContent','log-mod' : 'list'})
		divs = soup.find_all('li', {'class' : 'clear'})
		client = MongoClient('localhost',27017)
		MovieDB=client['House_BJ']
		MovieInfo=MovieDB['SellInfo']
		for div_html in divs:
			info={}
			info['House_site'] = m_site
			info['House_region'] = m_Pos
			info['House_title'],info['House_url'] = getHouseTitle(str(div_html))
			info['House_xiaoqu'],info['House_info']= getHouseInfo(str(div_html))
			info['House_flood'] = getFlood(str(div_html))
			info['House_totalprice'],info['House_Unprice'] = getPrice(str(div_html))
			info['House_tax_subway_key'] = getTagInfo(str(div_html))
			print info
			if MovieInfo.find({'House_title':info['House_title']}).count() ==0:
				MovieInfo.insert(info)
			else:
				print '********数据库中已有该条数据********'
				time.sleep(0.2)
				continue
			print '_'*70
			NUM += 1
			print '%s:%d' % ('='*70,NUM)
	except Exception,e:
		print Exception,':',e
		#traceback.print_exc()
	

if __name__ == "__main__":
	global m_type
	global m_ip_list
	reload(sys)
	coding = sys.setdefaultencoding('utf-8')
	#获取代理IP
	#DL_html = getHtmlWithHead(Daili_URL)
	#WriteIPlistTXT(getIP(DL_html))
	m_ip_list = ReadIPlist()
	#setProxy(get_random_ip(m_ip_list))


	#获取链家html内容
	#tags_html = getHtml(URL)
	while True:
		try:
			tags_html = getHtmlWithHead(URL)
			#获取所有在售房屋的区域及其对应的url
			tag_urls = getTags(tags_html)
			if tag_urls:
				for url in tag_urls.items():
					#print url[0].encode('utf-8'),str(url[1]).encode('utf-8')	
					m_Pos = url[0].encode('utf-8')
					maxpage = int(get_pages(str(url[1]).encode('utf-8')))
					#获取每一页的电影信息
					for x in range(0,maxpage):				
						m_url = "%spg%d" % (str(url[1]),x)		 
						#movie_html = getHtml(m_url.encode('utf-8'))
						try:
							movie_html = getHtmlWithHead(m_url.encode('utf-8'))			
							#获取各个区域的在售二手房信息
							getHouse(movie_html)
							time.sleep(2)
						except Exception,e:
							print Exception,":",e
							x = x-1
							continue
			else:
				print "***************no tags*****************"
				print "-"*50
				print tags_html
				print '-'*50
				continue
			break
		except Exception,e:
			print Exception,':',e
			continue
		
