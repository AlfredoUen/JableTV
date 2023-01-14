#!/usr/bin/env python
# coding: utf-8

import M3U8Sites.SiteJableTV
import M3U8Sites.Site91Porn

siteList = (
M3U8Sites.SiteJableTV.SiteJableTV,
M3U8Sites.Site91Porn.SiteJableOrg,
M3U8Sites.Site91Porn.SiteThisAV,
M3U8Sites.Site91Porn.SitePigAV,
M3U8Sites.Site91Porn.SitePorn5F,
M3U8Sites.Site91Porn.Site85Tube,
M3U8Sites.Site91Porn.Site91Porn
)

siteUrlList = (
M3U8Sites.SiteJableTV.JableTVList
)

def VaildateUrl(url):
    for site in siteList:
        if site.validate_url(url): return site
    return None

def CreateSite(url, savepath="", silence=False):
    site = VaildateUrl(url)
    if site is None: return None
    return site(url, savepath=savepath, silence=silence)

def CreateSiteUrlList(url, silence):
    for urlList in siteUrlList:
        jList = urlList(url, silence=silence)
        if jList.isVaildLinks():
            return jList
    return None

def consoles_main(url, dest=None):
    if not url or url == '':
        url = input('輸入支援的網址:')
    jjob = CreateSite(url, dest)
    if jjob and jjob.is_url_vaildate():
        jjob.start_download()
        print('下載完成!')


if __name__ == "__main__":
    consoles_main("")

