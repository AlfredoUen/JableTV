#!/usr/bin/env python
# coding: utf-8

import re
import cloudscraper
from M3U8Crawler import *
from bs4 import BeautifulSoup


class JableTVJob(M3U8Crawler):

    website_pattern = r'https://jable\.tv/videos/.+/'
    website_dirname_pattern = r'https://jable\.tv/videos/(.+)/$'
    #   https://jable.tv/videos/abw-312/

    def get_url_infos(self):
        url = self.get_url_full()
        htmlfile = cloudscraper.create_scraper(browser=request_headers, delay=10).get(url)
        if htmlfile.status_code == 200:
            result = re.search('og:title".+/>', htmlfile.text)
            self._targetName = result[0].split('"')[-2]
            self._targetName = re.sub(r'[^\w\-_\. ]', '', self._targetName)
            result = re.search('og:image".+jpg"', htmlfile.text)
            self._imageUrl = result[0].split('"')[-2]
            result = re.search("https://.+m3u8", htmlfile.text)
            self._m3u8url = result[0]
        else:
            raise Exception(f"Bad url names: {url}")


class JableTVList:

    sortby_dict = {'最高相關': '',
                   '近期最佳': 'post_date_and_popularity',
                   '最近更新': 'post_date',
                   '最多觀看': 'video_viewed',
                   '最高收藏': 'most_favourited'}

    def __init__(self, url, silence=False, *args, **kwargs):
        self.islist = None
        if JableTVJob.validate_url(url) is not None : return
        self.islist = self._url_get(url)
        if self.islist is None:
            if not silence:
                print(f"網址 {url} 錯誤!!", flush=True)
            return
        titleBox = self.islist.section.find('div', class_='title-box')
        self.totalLinks = int(str(titleBox.span.string).partition(" ")[0])
        self.listType = titleBox.h2.string
        activeSortType = self.islist.find('li', class_='active')
        if activeSortType is None: self.sortType = None
        else:  self.sortType = str(activeSortType.a.string)
        self.totalPages = (self.totalLinks + 23) // 24
        self._parser_url(url)
        if not silence:
            print(f"[{self.listType} {str(self.sortType)}]共有{self.totalPages}頁，{self.totalLinks}部影片。已取得{len(self.links)}部影片")

    def _url_get(self, url):
        try:
            htmlfile = cloudscraper.create_scraper(browser=request_headers, delay=10).get(url)
            if htmlfile.status_code == 200:
                content = htmlfile.content
                soup = BeautifulSoup(content, 'html.parser')
                divlist = soup.find('div', id="site-content")
                divlists_MemberOnly = soup.find_all('div', class_="ribbon-top-left")
                _memberOnly_urls = [del_url.find_parent('a')['href'] for del_url in divlists_MemberOnly if del_url.getText() == '會員']        
                if divlist is None: return None
                divlist = divlist.div
                self.links = []
                self.linkDescs = []
                tags = divlist.select('div.detail')
                for tag in tags:
                    tag_a = tag.h6.a
                    _url = tag_a['href']
                    if _url not in _memberOnly_urls:
                        self.links.append(_url)
                        self.linkDescs.append(str(tag_a.string))
            return divlist
        except Exception:
            return None

    def _parser_url(self, url):
        if not url or url == '': return False
        self.currentPage = 0
        self.searchKeyWord = None
        self.url = 'https://jable.tv'
        uu = url.split("/")
        if 'https://jable.tv' != '/'.join(uu[0:3]): return False
        if len(uu)>3:
            self.url = '/'.join(uu[:-1])+'/'
            if 'search' == uu[3]:
                self.searchKeyWord = uu[4]

    def getLinks(self): return self.links
    def getLinkDescs(self): return self.linkDescs
    def getListType(self): return self.listType
    def getTotalLinks(self): return self.totalLinks
    def getTotalPages(self): return self.totalPages
    def getCurrentPage(self): return self.currentPage
    def getSortType(self): return self.sortType
    def isVaildLinks(self): return False if self.islist is None else True

    def getSortTypeList(self):
        ll = list(JableTVList.sortby_dict)
        if self.searchKeyWord is None: del ll[0]
        return ll

    def loadPageAtIndex(self, index, sortby):
        if self.currentPage == index:
            if self.sortType is None: return
            if self.sortType == sortby: return

        if self.sortType is None:
            if self.searchKeyWord is None:
                newUrl = self.url + f"?from={index+1}"
            else:
                newUrl = f"https://jable.tv/search/?q={self.searchKeyWord}&from_videos={index+1}"
        else:
            if self.searchKeyWord is None:
                newUrl = self.url + f"?sort_by={JableTVList.sortby_dict[sortby]}&from={index+1}"
            else:
                newUrl = f"https://jable.tv/search/?q={self.searchKeyWord}&sort_by={JableTVList.sortby_dict[sortby]}&from_videos={index+1}"
        self._url_get(newUrl)
        self.currentPage = index
        self.sortType = sortby

def consoles_main(url, dest=None):
    # 使用者輸入Jable網址
    if not url or url == '':
        url = input('輸入jable網址:')
    jjob = JableTVJob(url, dest)
    if jjob.is_url_vaildate():
        jjob.start_download()
        print('下載完成!')

if __name__ == "__main__":
    consoles_main("")

