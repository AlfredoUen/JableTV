#!/usr/bin/env python
# coding: utf-8

import M3U8Sites.SiteJableTV
import M3U8Sites.Site91Porn
import M3U8Sites.SiteJavDB

siteList = (
M3U8Sites.SiteJableTV.SiteJableTV,              # https://jable.tv/
M3U8Sites.SiteJableTV.SiteJableTV_Backup,       # https://fs1.app/

M3U8Sites.Site91Porn.SiteJableOrg,              # https://jable.org/
M3U8Sites.Site91Porn.SiteThisAV,                # https://thisav.org/
M3U8Sites.Site91Porn.SitePigAV,                 # https://pigav.org/
M3U8Sites.Site91Porn.SitePorn5F,                # https://porn5f.org/
M3U8Sites.Site91Porn.Site85Tube,                # https://85tube.org/
M3U8Sites.Site91Porn.Site91Porn,                # https://91porn.best/
M3U8Sites.Site91Porn.SitePornBest,              # https://www.pornbest.org/

M3U8Sites.SiteJavDB.SiteJavdbLive,              # https://www.javdb.live/
M3U8Sites.SiteJavDB.SiteHAnimeXYZ,              # https://www.hanime.xyz/
M3U8Sites.SiteJavDB.SitePornTW,                 # https://www.porntw.com/
M3U8Sites.SiteJavDB.SitePornJP,                 # https://www.pornjp.org/
M3U8Sites.SiteJavDB.SitePornHK,                 # https://www.pornhk.org/
M3U8Sites.SiteJavDB.SitePornHoHo,               # https://www.pornhoho.com/
M3U8Sites.SiteJavDB.SitePornNVR,                # https://www.pornnvr.me/
M3U8Sites.SiteJavDB.SiteVideo01,                # https://www.video01.org/
M3U8Sites.SiteJavDB.SitePornLuLu,               # https://www.pornlulu.com/

M3U8Sites.SiteJavDB.SiteMIEN321,                # https://www.mien321.cc/
M3U8Sites.SiteJavDB.SiteAApp11,                 # https://www.aapp11.life/
M3U8Sites.SiteJavDB.SiteSeselah,                # https://www.seselah.com/
M3U8Sites.SiteJavDB.SiteXJISHI,                 # https://forum.xjishi.site/
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

def CreateSiteUrlList(url, silence=False):
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

