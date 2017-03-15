#*-* coding:utf-8 *-*

import re
import urllib2
from bs4 import BeautifulSoup
import string,time
import pymongo

NUM=0
m_type = u''
m_site=u'qq'

def getHtml(url):
	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	html = response.read()
	return html

def getTags(html):
	global m_type
	soup = BeautifulSoup(html)
	#tags_all = soup.find_all('ur',{'class':'clearfix _group','gname':'mi_type'})
      	tags_all = soup.find_all('div',{'class' : 'filter_content'})

	#re_tags = r'<a _hot=\"tag\.sub\" class=\"_gtag _hotkey\" href=\"(.+?)\" title=\"(.+?)\" tvalue=\"(.+?)\">.+?</a>'
	re_tags = r'<a href=\">'
	p = re.compile(re_tags, re.DOTALL)
	tags = p.findall(str(tags_all[0])) 
	if tags:
		tags_url = {}
		for tag in tags:   
			tag_url = tag[0].decode('utf-8')   #print tag_url   
			m_type = tag[1].decode('utf-8')   
			tags_url[m_type] = tag_url      
	else:   
		print "Not Find" 
	return tags_url

def get_pages(tag_url):
	tag_html = gethtml(tag_url)
	soup = BeautifulSoup(tag_html)
	div_page = soup.find_all('div', {'class' : 'mod_pagenav', 'id' : 'pager'})
	re_pages =  r'<a class=.+?><span>(.+?)</span></a>'
	p = re.compile(re_pages,re.DOTALL)
	pages = p.findall(str(div_page[0]))
	if len(pages) > 1:
		return pages[-2]
	else:
		return 1

def getMovielist(html):
	soup = BeautifulSoup(html)
	divs = soup.find_all('ul', {'class' : 'mod_list_pic_130'})
	for div_html in divs:
		div_html = str(div_html).replace('\n','')
		getMovie(div_html)

def getMoive(html):
	global NUM
	global m_type
	global m_site
	
	re_movie = r'<li><a class=\"mod_poster_130\" href=\"(.+?)\" target=\"_blank\" title=\"(.+?)\"><img.+?</li>'
	p = re.compile(re_movie,re.DOTALL)
	movies  = p.find_all(html)
	if movies:
		conn = pymongo.Connection('localhost',27017)
		movie_db = conn.dianying
		playlinks = movie_db.playlinks
		for movie in movies:
			NUM += 1
			print "%s:%d" % ('='*70,NUM)
			values = dict(
				movie_title = movie[1],
				movie_url = movie[0],
				movie_site = m_site,
				movie_type = m_type)

			print values
			playlinks.insert(values)
			print '_'*70
			NUM += 1
			print '%s:%d' % ('='*70,NUM)

def getMovieInfo(url):
	html = getHtml(url)
	soup = BeautifulSoup(html)
	divs = soup.find_all('div', {'class' : 'pack pack_album album_cover'})
	re_info = r'<a href=\"(.+?)\" target=\"new\" title=\"(.+?)\" wl=\".+?\"> </a>'
	p_info = re.compile(re_infom,re.DOTALL)
	m_info = p_info.findall(str(divs[0]))
	
	if m_info:
		return m_info
	else:
		print 'Not find movie info'
	return m_info


def insertDB(movieinfo):
	global conn
	movie_db = conn.dianying_at
	movies = movie_db.movies
	movies.insert(moviesinfo)
	

if __name__ == "__main__":
	global conn
	tags_url = "http://v.qq.com/list/1_-1_-1_-1_1_0_0_20_0_-1_0.html"
	tags_html = getHtml(tags_url)
	tag_urls = getTags(tags_html)
	
	for url in tag_urls.items():
		print str(url[1]).encode('utf-8')
		maxpage = int(get_pages(str(url[1]).encode('utf-8')))
		print maxpage
		for x in range(0,maxpage):
			m_url = str(url[1]).replace('0_20_0_-1_0.html','')
			movie_url = "%s%d_20_0_-1_0.html" % (m_url,x)
			print movie_url
			movie_url = getHtml(movie_url.encode('utf-8'))
			getMovielist(movie_html)
			time.sleep(0.1)

