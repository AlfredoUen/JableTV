import JableTVJob
import Site91Porn

siteList = [
JableTVJob.JableTVJob,
Site91Porn.SiteJableOrg,
Site91Porn.SiteThisAV,
Site91Porn.SitePigAV,
Site91Porn.SitePorn5F,
Site91Porn.Site85Tube,
Site91Porn.Site91Porn,
]

def VaildateUrl(url):
    for site in siteList:
        if site.validate_url(url): return site
    return None

def CreateSite(url, savepath="", silence=False):
    site = VaildateUrl(url)
    if site is None: return None
    return site(url, savepath=savepath, silence=silence)


