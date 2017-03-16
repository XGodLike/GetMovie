#*-* coding:utf-8 *-*

import re
import urllib2
from bs4 import BeautifulSoup
import string,time
from pymongo import MongoClient

#/movie?subtype=100008&offset=150

Offset='&offset='
Subtype='subtype='
URL='http://v.qq.com/x/list/movie'

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
      	tags_all = soup.find_all('div',{'class' : 'filter_content'})
	re_tags = r'<a _stat=\"filter:params_类型_(.+?)\" class=\"item.*?\" href=\"\?offset=0&amp;subtype=(.+?)\">(.+?)</a>'
	p = re.compile(re_tags, re.DOTALL)
	tags = p.findall(str(tags_all[0])) 

	#for tag in tags[1:]:
	#	print tag[0].decode('utf-8'),tag[1].decode('utf-8')
	#return tags
	tags_url = {}
	if tags:
		for tag in tags[1:]:   
			tag_url = URL + '?subtype='+ tag[1].decode('utf-8') +'&offset=0' #print tag_url   
			m_type = tag[2].decode('utf-8')   
			tags_url[m_type] = tag_url      
	else:   
		print "Not Find" 
	return tags_url

def get_pages(tag_url):
	tag_html = getHtml(tag_url)
	soup = BeautifulSoup(tag_html)
	div_page = soup.find_all('div', {'class' : 'mod_pages', 'r-notemplate' : 'true'})
	re_pages = r'<a _stat=\"pages_index:paging_page_\d{1,}\" class=\"page_num\" href=\".+?\">(\d{1,})</a>'
	p = re.compile(re_pages,re.DOTALL)
	pages = p.findall(str(div_page[0]))
	if len(pages) >= 1:	
		return pages[-1]
	else:
		return 1

def getMoive(html):
	global NUM
	global m_type
	global m_site

	re_movie = r'<a _stat=\"videos-vert:title\" href=\"(.*?)\" target=\"_blank\" title=\".*?\">(.*?)</a>'
	p = re.compile(re_movie,re.DOTALL)
	movies  = p.findall(html)
	if movies:
		#conn = pymongo.Connection('localhost',27017)
		#movie_db = conn.dianying
		#playlinks = movie_db.playlinks
		client = MongoClient('localhost',27017)
		MovieDB=client['Movie']
		MovieInfo=MovieDB['movie_list']
		for movie in movies:
			NUM += 1
			print "%s:%d" % ('='*70,NUM)
			values = dict(
				#movie_title = movie[1],
				#movie_url = movie[0],
				#movie_site = m_site,
				#movie_type = m_type)
				movie_title = movie[1],
				movie_url = movie[0],
				movie_site = m_site,
				movie_type = m_type)
			print values
			MovieInfo.insert(values)
			print '_'*70
			NUM += 1
			print '%s:%d' % ('='*70,NUM)

def getMovielist(html):
	soup = BeautifulSoup(html)
	divs = soup.find_all('li', {'class' : 'list_item'})
	for div_html in divs:
		#div_html = str(div_html).replace('\n','')
		getMoive(str(div_html))

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
	tags_url = URL
	tags_html = getHtml(tags_url)
	tag_urls = getTags(tags_html)
	for url in tag_urls.items():
		#print str(url[1]).encode('utf-8')
		maxpage = int(get_pages(str(url[1]).encode('utf-8')))
		for x in range(0,maxpage):
			m_url = str(url[1]).replace(Offset,'')
			movie_url = '%s%s%d' % (m_url,Offset,x*30) 
			movie_html = getHtml(movie_url.encode('utf-8'))
			getMovielist(movie_html)
			time.sleep(0.1)

