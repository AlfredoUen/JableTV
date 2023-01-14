#!/usr/bin/env python
# coding: utf-8

import re
import cloudscraper
from M3U8Sites.M3U8Crawler import *
from bs4 import BeautifulSoup

#   https://www.jable.org
#   https://www.thisav.org
#   https://www.pigav.org
#   https://www.porn5f.org
#   https://www.85tube.org
#   https://www.91porn.best


class SiteCCCDNXYZ(M3U8Crawler):

    def get_url_infos(self):
        self._max_workers = 1
        url = self.get_url_full()
        htmlfile = cloudscraper.create_scraper(browser=request_headers, delay=10).get(url)
        if htmlfile.status_code == 200:
            result = re.search('meta name="keywords" content=.+"', htmlfile.text)
            self._targetName = result[0].split('"')[-2].split(',')[0]
            self._targetName = re.sub(r'[^\w\-_\. ]', '', self._targetName)
            result = re.search(r'thumbnail.+"', htmlfile.text)
            self._imageUrl = re.sub(r'\\', '', result[0].split('"')[2])
            result = re.search(r'://p.+/',htmlfile.text)
            port = result[0].split('/')[2].split('.')[1]
            self._imageUrl = f"https://p.{port}.cccdn.xyz{self._imageUrl}"
            self._m3u8url = re.sub('t.jpg','v.m3u8',self._imageUrl)
        else:
            raise Exception(f"Bad url names: {url}")

class SiteJableOrg(SiteCCCDNXYZ):
    website_pattern = r'https://www\.jable\.org/\d+\.html'
    website_dirname_pattern = r'https://www\.jable\.org/(\d+)\.html$'

class SiteThisAV(SiteCCCDNXYZ):
    website_pattern = r'https://www\.thisav\.org/\d+\.html'
    website_dirname_pattern = r'https://www\.thisav\.org/(\d+)\.html$'

class SitePigAV(SiteCCCDNXYZ):
    website_pattern = r'https://www\.pigav\.org/\d+\.html'
    website_dirname_pattern = r'https://www\.pigav\.org/(\d+)\.html$'

class SitePorn5F(SiteCCCDNXYZ):
    website_pattern = r'https://www\.porn5f\.org/\d+\.html'
    website_dirname_pattern = r'https://www\.porn5f\.org/(\d+)\.html$'

class Site85Tube(SiteCCCDNXYZ):
    website_pattern = r'https://www\.85tube\.org/\d+\.html'
    website_dirname_pattern = r'https://www\.85tube\.org/(\d+)\.html$'

class Site91Porn(SiteCCCDNXYZ):
    website_pattern = r'https://www\.91porn\.best/\d+\.html'
    website_dirname_pattern = r'https://www\.91porn\.best/(\d+)\.html$'
