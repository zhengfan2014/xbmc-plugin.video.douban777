# -*- coding: utf-8 -*-
# Module: default
# Author: Roman V. M.
# Created on: 28.11.2014
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html


import re
from xbmcswift2 import Plugin
import requests
from bs4 import BeautifulSoup
import xbmcgui
import base64
import json
import urllib2
import sys
import HTMLParser
import re




def unescape(string):
    string = urllib2.unquote(string).decode('utf8')
    quoted = HTMLParser.HTMLParser().unescape(string).encode('utf-8')
    #转成中文
    return re.sub(r'%u([a-fA-F0-9]{4}|[a-fA-F0-9]{2})', lambda m: unichr(int(m.group(1), 16)), quoted)


plugin = Plugin()



headers = {'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_0_2 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12A366 Safari/600.1.4'}


def get_categories():
    return [{'name':'首页','link':'http://douban777.com/?m=vod-index-pg'},
            {'name': '电影', 'link': 'http://douban777.com/?m=vod-type-id-1-pg'},
            {'name':'电视剧','link':'http://douban777.com/?m=vod-type-id-2-pg'},
            {'name':'综艺','link':'http://douban777.com/?m=vod-type-id-3-pg'},
            {'name':'动漫','link':'http://douban777.com/?m=vod-type-id-4-pg'}]


def get_videos(category,page):
#爬视频列表的
    # if int(page) == 1:
    #     pageurl = category
    # else:
    #     pageurl = category + 'index_'+page+'.html'
    pageurl = category+'-'+page+'.html'

    r = requests.get(pageurl, headers=headers)
    r.encoding = 'UTF-8'
    soup = BeautifulSoup(r.text, "html5lib")
    videos = []
    #videoelements = soup.find('ul', id='list1').find_all('li')
    #videoelements = contenter.find_all("a", attrs={"data-original": True})
    videoelements = soup.find('ul', class_='videoContent').find_all('a', {'class', 'videoName'})

    if videoelements is None:
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('错误提示', '没有播放源')
    else:
        for videoelement in videoelements:
            movieitem = videoelement
	    rthumb = requests.get('http://douban777.com/'+movieitem['href'], headers=headers)
	    rthumb.encoding = 'UTF-8'
	    thumbsoup = BeautifulSoup(rthumb.text, "html5lib")
	    thumb1 = thumbsoup.find('div',class_='left')
	    thumb2 = thumb1.img['src']


            thumbsrc = thumb2

            videoitem = {}
            videoitem['name'] = movieitem.get_text()
            videoitem['href'] = 'http://douban777.com/'+movieitem['href']
            videoitem['thumb'] = thumbsrc
            videoitem['genre'] = '豆瓣电影'
            videos.append(videoitem)
        return videos

def get_search(keyword,page):
    # if int(page) == 1:
    #     pageurl = category
    # else:
    #     pageurl = category + 'index_'+page+'.html'
    serachUrl ='http://douban777.com/index.php?m=vod-search-pg-'+str(page)+'-wd-'+keyword+'.html'

    r = requests.get(serachUrl, headers=headers)
    r.encoding = 'UTF-8'
    soup = BeautifulSoup(r.text, "html5lib")
    videos = []
    #videoelements = soup.find('ul', id='list1').find_all('li')
    #videoelements = contenter.find_all("a", attrs={"data-original": True})
    #videoelements = soup.find('ul', id='list1').find_all('a', {'data-origin', True})
    videoelements = soup.find('ul', class_='videoContent').find_all('a', {'class', 'videoName'})

    if videoelements is None:
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('错误提示', '没有播放源')
    else:
        for videoelement in videoelements:
            movieitem = videoelement
            videoitem = {}
            videoitem['name'] = movieitem.get_text()
            videoitem['href'] = 'http://douban777.com/' + movieitem['href']
            videoitem['genre'] = '豆瓣电影'
            videos.append(videoitem)
        return videos


def get_sources(videolink):
    r = requests.get(videolink, headers=headers)
    r.encoding = 'UTF-8'
    soup = BeautifulSoup(r.text)
    sources = []
    allsources = soup.find('div', class_='ardess').find_all('a', {'title':True})
    

    if allsources is not None:
        for sourceitem in allsources:
            content = sourceitem.get_text()
            if content.find('.m3u8') == -1:
                continue
            sourceItem = content.split('$')
            videosource = {}
            videosource['name'] = sourceItem[0]
            videosource['href'] = sourceItem[1]
            sources.append(videosource)
        return sources
    else:
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('错误提示', '没有播放源')


@plugin.route('/play/<url>/')
def play(url):
    r = requests.get(url, headers=headers)
    r.encoding = 'UTF-8'
    pattern = re.compile("now\=unescape\(\"([^\"]*)\"\)")
    playurl = unescape(str(pattern.findall(r.text)[0]))

    item = {'label': '播放','path': playurl,'is_playable': True}
    items = []
    items.append(item)
    return items
    
    # if playurl is not None:
    #     plugin.set_resolved_url(item)
    # else:
    #     dialog = xbmcgui.Dialog()
    #     ok = dialog.ok('错误提示', '没有播放源')


@plugin.route('/sources/<url>/')
def sources(url):
    sources = get_sources(url)
    items = [{
        'label': source['name'],
        'path': source['href'],
        'is_playable': True
    } for source in sources]
    sorted_items = sorted(items, key=lambda item: item['label'])
    return sorted_items


@plugin.route('/category/<url>/<page>/')
def category(url,page):
    videos = get_videos(url, page)
    items = [{
        'label': video['name'],
        'path': plugin.url_for('sources', url=video['href']),
	'thumbnail': video['thumb'],
	'icon': video['thumb'],
	'rating': '6.4',
    } for video in videos]

    sorted_items = items
    #sorted_items = sorted(items, key=lambda item: item['label'])
    pageno = int(page) + 1
    nextpage = {'label': ' 下一页','path': plugin.url_for('category', url=url,page=pageno)}
    sorted_items.append(nextpage)
    return sorted_items

# get search result by input keyword
@plugin.route('/search')
def search():
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        keyword = keyboard.getText()
        #url = HOST_URL + '/index.php?m=vod-search&wd=' + keyword
        #https://www.nfmovies.com/search.php?page=1&searchword='+keyword+'&searchtype=

        videos = get_search(keyword, 1)
        items = [{
            'label': video['name'],
            'path': plugin.url_for('sources', url=video['href'])
        } for video in videos]

        sorted_items = items
        nextpage = {'label': ' 下一页', 'path': plugin.url_for('searchMore', keyword=keyword, page=2)}
        sorted_items.append(nextpage)
        return sorted_items

@plugin.route('/searchMore/<keyword>/<page>/')
def searchMore(keyword,page):
    videos = get_search(keyword, page)
    items = [{
        'label': video['name'],
        'path': plugin.url_for('sources', url=video['href'])
    } for video in videos]

    sorted_items = items
    # sorted_items = sorted(items, key=lambda item: item['label'])
    pageno = int(page) + 1
    nextpage = {'label': ' 下一页', 'path': plugin.url_for('searchMore', keyword=keyword, page=pageno)}
    sorted_items.append(nextpage)
    return sorted_items

@plugin.route('/')
def index():
    categories = get_categories()
    items = [{
        'label': category['name'],
        'path': plugin.url_for('category', url=category['link'], page=1),
    } for category in categories]

    items.append({
        'label': u'[COLOR yellow]搜索[/COLOR]',
        'path': plugin.url_for('search'),
    })
    #sorted_items = sorted(items, key=lambda item: item['label'])
    return items


if __name__ == '__main__':
    plugin.run()
    plugin.set_view_mode(500)
