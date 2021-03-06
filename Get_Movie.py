#*-* coding:utf-8 *-*

import re
import urllib2
import traceback
from bs4 import BeautifulSoup
import string,time
from pymongo import MongoClient

#/movie?subtype=100008&offset=150

Offset='&offset='
Subtype='subtype='
URL='http://v.qq.com/x/list/movie'

NUM=0
m_type = u''
m_site=u'qq影视'

#最简单的html内容,有些防爬虫网址不行
def getHtml(url):
	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	html = response.read()
	return html

#伪装成浏览器的爬虫
def getHtmlWithHead(url):
	req_header={'User-Agent':'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
	'Accept':'text/html;1=0.9,*/*;q=0.8',
	'Accept-Charset':'utf-8',
	'Accept-Encoding':'*',
	'Connection':'close',
	'Referer':None
	}
	req_timeout = 5
	req = urllib2.Request(url,None,req_header)
	response = urllib2.urlopen(req,None,req_timeout)
	html = response.read()
	return html

#获取电影的类型标签,及其对应的网址
def getTags(html):
	global m_type
	soup = BeautifulSoup(html,'lxml')
      	tags_all = soup.find_all('div',{'class' : 'filter_content'})
	if tags_all:
		re_tags = r'<a _stat=\"filter:params_类型_(.+?)\" class=\"item.*?\" href=\"\?offset=0&amp;subtype=(.+?)\">(.+?)</a>'
		p = re.compile(re_tags, re.DOTALL)
		tags = p.findall(str(tags_all[0])) 
	else:
		return ""
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
	#tag_html = getHtml(tag_url)
	tag_html = getHtmlWithHead(tag_url)
	soup = BeautifulSoup(tag_html,'lxml')
	div_page = soup.find_all('div', {'class' : 'mod_pages', 'r-notemplate' : 'true'})
	re_pages = r'<a _stat=\"pages_index:paging_page_\d{1,}\" class=\"page_num\" href=\".+?\">(\d{1,})</a>'
	p = re.compile(re_pages,re.DOTALL)
	pages = p.findall(str(div_page[0]))
	if len(pages) >= 1:	
		return pages[-1]
	else:
		return 1

#获取简单的电影信息:{类型,网址,电影名}
def getMoive(html):
	global NUM
	global m_type
	global m_site

	re_movie = r'<a _stat=\"videos-vert:title\" href=\"(.*?)\" target=\"_blank\" title=\".*?\">(.*?)</a>'
	p = re.compile(re_movie,re.DOTALL)
	movies  = p.findall(html)
	if movies:
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
#////////////////////////////////////////////////////
def getMoiveTitle(html):
	re_info = r'<a _stat=\"videos-vert:title\" href=\"(.+?)\" target=\"_blank\" title=\".*?\">(.+?)</a>'
	p = re.compile(re_info,re.DOTALL)	
	info = p.findall(html)
	if info: 
		return info[0][1],info[0][0]
	else:
		return "",""

def getMovieIntro(html):
	#re_intro = r'<div class=\"figure_caption figure_caption_score\">.*?<span class=\"figure_info\">(.+?)<\span>.*?</div>'
	
	re_intro = r'<div class=\"figure_caption figure_caption_score\">.*?<span class=\"figure_info\">(.*?)</span>.*?</div>'

	p = re.compile(re_intro,re.DOTALL)
	intro = p.findall(html)
	if intro:
		return intro[0]
	else:
		return ""

def getMoviePlaynum(html):
	re_playnum = r'<div class=\"figure_count\">.*?<i class=\"icon_sm icon_play_sm\">.*?</i>.*?<span class=\"num\">(.+?)</span>.*?</div>'
	p = re.compile(re_playnum,re.DOTALL)
	playnum = p.findall(html)
	if playnum:
		return playnum[0]
	else:
		return 0

def getMovieScore(html):
	re_score = r'<div class=\"figure_score\">.*?<em class=\"score_l\">(\d)</em>.*?<em class=\"score_s\">(\.?[0-9]*)</em>.*?</div>'
	p = re.compile(re_score,re.DOTALL)
	fscore = p.findall(html)
	if fscore:
		score = (float)(fscore[0][0]) + (float)(fscore[0][1])
		score = "%.1f" % score
		return score
	else:
		return 0.0


def getMovieActors(html):
	re_actors = r'<a _stat=\"videos-vert:actor\" href=\".*?\" target=\"_blank\" title=\".*?\">(.*?)</a>'
	p = re.compile(re_actors,re.DOTALL)
	actors = p.findall(html)
	if actors:
		actorslist=[]
		for actor in actors:
			actorslist.append(actor)	
		return actorslist
	else:
		return []

#获取详细的电影信息:{电影名称,电影链接,电影简介,导演,演员,评分,播放量}
def getMovieInfo(html):
	global NUM
	global m_type	
	global m_site

	soup = BeautifulSoup(html,'lxml')
	divs = soup.find_all('li', {'class' : 'list_item'})
	try:
		client = MongoClient('localhost',27017)
		MovieDB=client['test']
		MovieInfo=MovieDB['movie']
		for div_html in divs:
			info={}
			info['movie_site'] = m_site
			info['movie_type'] = m_type
			info['movie_title'],info['movie_url'] = getMoiveTitle(str(div_html))
			info['movie_introduction']= getMovieIntro(str(div_html))
			info['movie_actors'] = getMovieActors(str(div_html))
			info['movie_director'] = '' # 当前页面没有导演信息,暂时用空代替
			info['movie_score'] = getMovieScore(str(div_html))
			info['movie_playnum'] = getMoviePlaynum(str(div_html))
			print info
			MovieInfo.insert(info)
			print '_'*70
			NUM += 1
			print '%s:%d' % ('='*70,NUM)
	except:
		traceback.print_exc()

def getMovielist(html):
	soup = BeautifulSoup(html,'lxml')
	divs = soup.find_all('li', {'class' : 'list_item'})
	for div_html in divs:
		getMoive(str(div_html))
	


if __name__ == "__main__":
	global m_type
	tags_url = URL
	#获取电影地址html内容
	#tags_html = getHtml(tags_url)
	tags_html = getHtmlWithHead(tags_url)
	#获取所有电影类型的首页
	tag_urls = getTags(tags_html)
	if tag_urls:
		for url in tag_urls.items():
			#print url[0].encode('utf-8'),str(url[1]).encode('utf-8')
			#print str(url[1]).encode('utf-8')	
			m_type = url[0].encode('utf-8')
			#获取每个类型的电影有多少页
			maxpage = int(get_pages(str(url[1]).encode('utf-8')))
			#获取每一页的电影信息
			for x in range(0,maxpage):				
				m_url = str(url[1])[:str(url[1]).index(Offset)]			
				movie_url = '%s%s%d' % (m_url,Offset,x*30) 
				#movie_html = getHtml(movie_url.encode('utf-8'))
				movie_html = getHtmlWithHead(movie_url.encode('utf-8'))	
				#获取简单的电影信息
				#getMovielist(movie_html)		
				#获取更详细的电影信息
				getMovieInfo(movie_html)
				time.sleep(0.1)
	else:
		print "no tags"
