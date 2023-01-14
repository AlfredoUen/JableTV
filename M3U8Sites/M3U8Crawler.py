#!/usr/bin/env python
# coding: utf-8

import platform
import os
import re
import requests
import urllib.request
import m3u8
from Crypto.Cipher import AES
from config import headers
import concurrent.futures
import copy
import time

"""
import threading
#Thread safe print function
print_old = print
def print(*a, **b):
    with threading.Lock():
        print_old(*a, **b)
"""
request_headers =  {'browser': 'firefox', 'platform': platform.system().lower()}

class M3U8Crawler:
    """ A base class all m3u8 crawl website tool """
    skip_pattern = False

    @classmethod
    def validate_url(cls, url):
        if not url or url == '': return None
        result = re.match(cls.website_dirname_pattern, url, flags=re.I)
        if result: return result.group(1)
        else: return None

    def __init__(self, url, savepath="", silence=False):
        self.silence = silence
        self._tsList = []
        self._ci = None
        self._downloadList = []
        self._t_executor = None
        self._t_future = None
        self._t2_executor = None
        self._cancel_job = None
        self._dirName = None
        self._dest_folder = None
        self._temp_folder = None
        self._targetName = None
        self._imageUrl = None
        self._m3u8url = None
        self._max_workers = 8
        try:
            self._dirName = self.validate_url(url)
            if not self._dirName: return
            self._url = url
            self._temp_folder = os.path.join(os.getcwd(), self._dirName)
            if (savepath is None) or (savepath == ''):
                self._dest_folder = self._temp_folder
            else:
                self._dest_folder = os.path.join(os.getcwd(), savepath)
            self.get_url_infos()
            if self.is_url_vaildate():
                if not self.silence:
                    print("檔案名稱: " + self._targetName, flush=True)
                    print("儲存位置: " + self._dest_folder, flush=True)
                    print("檔案縮圖: " + self._imageUrl, flush=True)

        except Exception:
            self._targetName = self._imageUrl = self._m3u8url = None
            print(f"下載網址 {url} 錯誤!!", flush=True)

    def get_url_infos(self): pass
    def target_name(self): return self._targetName
    def dest_folder(self): return self._dest_folder
    def is_url_vaildate(self): return True if self._m3u8url else False

    def _create_temp_folder(self):
        if not os.path.exists(self._temp_folder):  os.makedirs(self._temp_folder)

    def _create_dest_folder(self):
        if not os.path.exists(self._dest_folder):  os.makedirs(self._dest_folder)

    def _get_video_savename(self): return os.path.join(self._dest_folder, self._targetName + ".mp4")
    def _get_image_savename(self): return os.path.join(self._dest_folder, self._targetName + ".jpg")
    def get_url_full(self): return self._url

    def is_target_image_exist(self): return os.path.exists (self._get_image_savename())
    def is_target_video_exist(self): return os.path.exists (self._get_video_savename())

    def _create_m3u8(self):
        # 得到 m3u8 網址
        m3u8urlList = self._m3u8url.split('/')
        m3u8urlList.pop(-1)
        downloadurl = '/'.join(m3u8urlList)
        # 儲存 m3u8 file 至資料夾
        m3u8file = os.path.join(self._temp_folder, self._dirName + '.m3u8')
        urllib.request.urlretrieve(self._m3u8url, m3u8file)
        # 得到 m3u8 file裡的 URI和 IV
        m3u8obj = m3u8.load(m3u8file)
        m3u8uri = ''
        m3u8iv = ''
        for key in m3u8obj.keys:
            if key:
                m3u8uri = key.uri
                m3u8iv = key.iv
        # 儲存 ts網址 in self._tsList
        self._tsList = []
        for seg in m3u8obj.segments:
            tsUrl = downloadurl + '/' + seg.uri
            self._tsList.append(tsUrl)
        # 有加密
        if m3u8uri:
            m3u8keyurl = downloadurl + '/' + m3u8uri  # 得到 key 的網址
            # 得到 key的內容
            response = requests.get(m3u8keyurl, headers=headers, timeout=10)
            contentKey = response.content
            vt = m3u8iv.replace("0x", "")[:16].encode()  # IV取前16位
            self._ci = AES.new(contentKey, AES.MODE_CBC, vt)  # 建構解碼器
        else:
            self._ci = ''
        # 刪除m3u8 file
        files = os.listdir(self._temp_folder)
        for file in files:
            if file.endswith('.m3u8'):
                os.remove(os.path.join(self._temp_folder, file))

    def _deleteMp4Chunks(self):
        for url in self._tsList:
            os.path.split(url)
            fileName = url.split('/')[-1][0:-3]
            saveName = os.path.join(self._temp_folder, fileName + ".mp4")
            if os.path.exists(saveName):
                os.remove(saveName)

    def _mergeMp4Chunks(self):
        start_time = time.time()
        saveName = self._get_video_savename()
        number_of_chunk = len(self._tsList)
        print(f'開始合成影片...共有 {number_of_chunk} 個片段', flush=True)
        for i in range(len(self._tsList)):
            file = self._tsList[i].split('/')[-1][0:-3] + '.mp4'
            full_path = os.path.join(self._temp_folder, file)
            if os.path.exists(full_path) and not self._cancel_job:
                with open(full_path, 'rb') as f1:
                    with open(saveName, 'ab') as f2:
                        f2.write(f1.read())
                        number_of_chunk -= 1
                        print(f'\r合成影片中, 剩餘 {number_of_chunk} 個片段', end="")#, flush=True)
            else:
                os.remove(saveName)
                if not self._cancel_job:
                    print(f"{file} 片段遺失, 合成影片失敗!!!", flush=True)
                return 0
        spent_time = time.time() - start_time
        print('\n花費 {0:.2f} 秒合成影片'.format(spent_time), flush=True)
        self._deleteMp4Chunks()
        if self._temp_folder != self._dest_folder:
            os.removedirs(self._temp_folder)
        return spent_time

    def _scrape(self, url):
        os.path.split(url)
        fileName = url.split('/')[-1][0:-3]
        saveName = os.path.join(self._temp_folder, fileName + ".mp4")
        if os.path.exists(saveName):
            # 跳過已下載
            print('\r當前目標: {0} 已下載, 故跳過...剩餘 {1} 個'.format(
                url.split('/')[-1], len(self._downloadList)), end='', flush=True)
            self._downloadList.remove(url)
        else:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == requests.codes.ok:
                content_ts = response.content
                if self._ci:
                    content_ts = self._ci.decrypt(content_ts)  # 解碼
                with open(saveName, 'ab') as f:
                    f.write(content_ts)
                self._downloadList.remove(url)
               # 輸出進度
                remain_job = len(self._downloadList)
                remain_time = remain_job * ( time.time() - self._start_time ) / (self._job_total - remain_job)
                if remain_time > 60:
                    rem_str = "{0:.0f} 分 {1:.1f} 秒".format(remain_time//60, remain_time%60)
                else:
                    rem_str = "{0:.1f} 秒".format(remain_time)
                print('\r當前下載: {0} , 剩餘 {1} 個, 預計等待時間: {2}, '.format(
                    url.split('/')[-1], remain_job, rem_str), end='', flush=True)

    def _startCrawl(self):
        self._start_time = time.time()
        _total = len(self._tsList)
        self._job_total = len(self._downloadList)
        print(f'下載 {_total} 個檔案, 已下載 {_total-self._job_total} 個檔案, 剩餘 {self._job_total} 個檔案.. ', flush=True)
        round = 0
        # 同時建立及啟用 8 個執行緒
        while self._downloadList != [] and not self._cancel_job:
            round += 1
            with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                self._t2_executor = executor
                executor.map(self._scrape, self._downloadList)
            print(f'round {round}')
        self._t2_executor = None
        spent_time = time.time() - self._start_time
        if not self._cancel_job:
            print('\n花費 {0:.2f} 分鐘 爬取完成 !'.format(spent_time / 60), flush=True)

    def _prepareCrawl(self):
        self._downloadList = copy.deepcopy(self._tsList)
        for url in self._tsList:
            os.path.split(url)
            fileName = url.split('/')[-1][0:-3]
            saveName = os.path.join(self._temp_folder, fileName + ".mp4")
            if os.path.exists(saveName):
                # 跳過已下載
                self._downloadList.remove(url)

        if(len(self._downloadList)>0):
            # 開始爬取
            self._startCrawl()

    def download_image(self):
        if not self.is_target_image_exist():
            self._create_dest_folder()
            # 下載預覽圖
            response = requests.get(self._imageUrl, headers=headers, timeout=10)
            if response.status_code != requests.codes.ok:
                return None
            with open(self._get_image_savename(), 'ab') as fs:
                fs.write(response.content)
        return  self._get_image_savename()

    def start_download(self):
        self._cancel_job = False
        self._create_dest_folder()
        self.download_image()
        if not self.is_target_video_exist():
            self._create_temp_folder()
            self._create_m3u8()
            # 開始爬蟲並下載mp4片段至資料夾
            if not self._cancel_job:
                self._prepareCrawl()
            # 合成mp4
            if not self._cancel_job:
                self._mergeMp4Chunks()
        else:
            print("檔案已存在!!")

    def cancel_download(self):
        print("\n取消下載....", flush=True)
        self._cancel_job = True
        if self._t2_executor:
            self._t2_executor.shutdown(wait=True, cancel_futures=True)
            self._t2_executor = None
        if self._t_executor:
            self._t_executor.shutdown(wait=True, cancel_futures=True)
            self._t_executor = None
        print("\n下載已取消!!!", flush=True)

    def begin_concurrent_download(self):
        max_worker = os.cpu_count()
        self._t_executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_worker)
        self._t_future = self._t_executor.submit(self.start_download)

    def is_concurrent_dowload_completed(self):
        if not self._t_future.done():
            return False
        self._t_future = None
        return True

    def end_concurrent_download(self):
        if self._t_executor:
            self._t_executor.shutdown()
            self._t_executor = None


class SiteUrlList_M3U8:

    def getLinks(self): return self.links
    def getLinkDescs(self): return self.linkDescriptions
    def getListType(self): return self.listType
    def getTotalLinks(self): return self.totalLinks
    def getTotalPages(self): return self.totalPages
    def getCurrentPage(self): return self.currentPage
    def getSortType(self): return self.sortType
    def isVaildLinks(self): return False if self.islist is None else True


