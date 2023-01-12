#!/usr/bin/env python
# coding: utf-8

import threading
import time
import tkinter
import tkinter.filedialog
from tkinter import simpledialog as sd
import os
import re
from PIL import ImageTk, Image

from mywidget import *
from JableTVJob import JableTVList
from Site91Porn import *
import M3U8Sites


def gui_main(url, dest):
    mainWnd = JableTVDownloadWindow(dest=dest, url=url)
    mainWnd.mainloop()
    mainWnd.cancel_download()


class JableTVDownloadWindow(tk.Tk):
    """JableTV downloader GUI Main Window"""
    def __init__(self, dest="download", url='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.protocol("WM_DELETE_WINDOW", self._on_window_closed)
        self._currentJob = None
        self._download_list = []
        self._cancel_all = False
        self._urls_list = []
        self._import_dest = dest
        self.create_widgets(dest, url)
        self._is_abort = False
        self._clp_text = ""
        self.clipborad_thread = None
        self.toggle_download_button()
        self.loadthumbnail_thread = None
        self.clipboard_checker = threading.Thread(target=self.check_clipboard)
        self.clipboard_checker.start()

    def create_widgets(self, dest, url):
        self.title('JableTV 下載器')
        self.geometry('1024x768')

        self.tree = MyDownloadListView(self)
        self.tree.pack(side="top", fill='both', expand=True, padx=4, pady=4)
        self.tree.on_item_selected = self.on_treeitem_selected
        self.tree.bind('<<TreeviewSelect>>', self.on_treeitem_selected)

        dest_frame = tk.Frame(self)
        dest_frame.pack(side=tk.TOP, fill='x', padx=12)
        dest_label = tk.Label(dest_frame, text='存放位置', width=10)
        dest_label.pack(side=tk.LEFT)
        self.dest_entry = tk.Entry(dest_frame, width=70)
        self.dest_entry.pack(side=tk.LEFT, fill='x', expand=True)

        url_frame = tk.Frame(self)
        url_frame.pack(side=tk.TOP, fill='x', padx=12)
        url_label = tk.Label(url_frame, text='下載網址', width=10)
        url_label.pack(side=tk.LEFT, fill="both")
        self.url_entry = tk.Entry(url_frame, width=70)
        self.url_entry.pack(side=tk.LEFT, fill='x', expand=True)

        btns_frame = tk.Frame(self)
        btns_frame.pack(side=tk.TOP, fill='x', padx=18, pady=2)
        btn_leftframe = tk.Frame(btns_frame)
        btn_leftframe.pack(side=tk.LEFT,  padx=18, pady=1)
        btn_rightframe = tk.Frame(btns_frame)
        btn_rightframe.pack(side=tk.LEFT, fill="x", expand=True, padx=18, pady=1)

        self.btn_importlist = tk.Button(btn_leftframe, text='導入文件', command=self.on_import_list)
        self.btn_importlist.pack(side=tk.LEFT, padx=2)
        self.btn_addlist = tk.Button(btn_leftframe, text='加入清單', command=self.on_add_list)
        self.btn_addlist.pack(side=tk.LEFT, padx=2)
        self.btn_download = tk.Button(btn_leftframe, text='開始下載', command=self.on_start_download)
        self.btn_download.pack(side=tk.LEFT, padx=2)
        self.btn_download_all = tk.Button(btn_leftframe, text='全部下載', command=self.on_start_all_download)
        self.btn_download_all.pack(side=tk.LEFT, padx=2)
        self.btn_cancel = tk.Button(btn_leftframe, text='全部取消', command=self.on_cancel_all_download)
        self.btn_cancel.pack(side=tk.RIGHT, padx=2)

        self.btn_clearText = tk.Button(btn_rightframe, text="清除訊息", command=self.on_clear_text)
        self.btn_clearText.pack(side=tk.LEFT, padx=2)

        self.bShowThumbnail = tkinter.BooleanVar()
        self.bShowThumbnail.set(1)
        self.chkbtn_thumbnail = ttk.Checkbutton(btn_rightframe, text="顯示縮圖",variable=self.bShowThumbnail, command=self.onEnableThumbnail)
        self.chkbtn_thumbnail.pack(side=tk.RIGHT, padx=2)

        self.text = RedirectConsole(self)
        self.text.pack(side=tk.LEFT, fill="both", expand=True, padx=8, pady=2)

        self.label_thumbnail_image = tk.Label(self, compound="top", wraplength=360, width=360)

        self.thumbnail = None

        self.dest = dest
        self._url = url

        self.load_on_create()
        self.dest_entry.insert(tk.END, dest)
        self.url_entry.insert(tk.END, url)

    def _loadThumbnail(self):
        self.loadthumbnail_thread = None
        self._get_entry_values()
        jjob = M3U8Sites.CreateSite(self._url, self.dest, silence=True)
        url = jjob.download_image()
        if url is not None and url != "":
            img = Image.open(url)
            w = 360 / img.size[0]
            h = 270 / img.size[1]
            __sz = (360, (int)(img.size[1]*w) )
            if w>h: __sz = ((int)(img.size[0]*h), 270)
            self.thumbnail = ImageTk.PhotoImage(img.resize(__sz))
            self.label_thumbnail_image.pack_forget()
            self.label_thumbnail_image["image"] = self.thumbnail
            self.label_thumbnail_image["text"] = jjob.target_name()
            self.label_thumbnail_image.pack(side=tk.LEFT)

    def showThumbnail(self):
        if not self.bShowThumbnail.get():
            self.label_thumbnail_image.pack_forget()
        else:
            if self.loadthumbnail_thread is None:
                self.loadthumbnail_thread = threading.Timer(0.5, self._loadThumbnail)
                self.loadthumbnail_thread.start()

    def onEnableThumbnail(self):
        self._get_entry_values()
        if self._url is not None and self._url != "":
            self.showThumbnail()

    def on_treeitem_selected(self, event):
        for selected_item in self.tree.selection():
            item = self.tree.item(selected_item)
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(tk.END, item['values'][2])
            self.url_entry.delete(0, tk.END)
            url_full = item['values'][0]
            self.url_entry.insert(tk.END, url_full)
            self._get_entry_values()
            self.toggle_download_button()
            self.onEnableThumbnail()

    def _defer_add_url_list(self):
        try:
            while self._urls_list != []:
                url = self._urls_list.pop(0)
                self._add_url_to_tree(url, self.dest)
        except Exception:
            pass
        finally:
            self.clipborad_thread = None

    def append_url_to_queue_for_defer_insertion(self, str):
        self._urls_list.append(str.strip())
        if self._urls_list != [] and not self.clipborad_thread:
            self.clipborad_thread = threading.Timer(0.5, self._defer_add_url_list)
            self.clipborad_thread.start()

    def check_clipboard(self):
        while not self._is_abort:
            try:
                clp = self.clipboard_get()
                if not type(clp) is type(self._clp_text) or self._clp_text != clp:
                    self._clp_text = clp
                    for site in M3U8Sites.siteList:
                        if site.skip_pattern: continue
                        result = re.findall(site.website_pattern, clp)
                        if len(result) == 0: continue
                        for str in result:
                            self.append_url_to_queue_for_defer_insertion(str)
                time.sleep(0.2)
            except:
                pass

    def _on_window_closed(self):
        self._is_abort = True
        self._urls_list = []
        self.on_terminate_window()
        self.save_on_close()
        os._exit(0)

    def _get_entry_values(self):
        self.dest = self.dest_entry.get()
        self._url = self.url_entry.get()

    def toggle_download_button(self):
        self.btn_download['text'] = "開始下載"
        self.btn_download['command'] = self.on_start_download
        self._get_entry_values()
        if self._url is None or self._url == "":
            self.btn_download["state"] = tk.DISABLED
        else:
            self.btn_download["state"] = tk.NORMAL
        if self._download_list != []:
            for dlist in self._download_list:
                if dlist[0] == self._url:
                    self.btn_download['text'] = "取消下載"
                    self.btn_download['command'] = self.on_cancel_download
        if self._currentJob and self._url == self._currentJob.get_url_full():
                self.btn_download['text'] = "取消下載"
                self.btn_download['command'] = self.on_cancel_download

        if len(self.tree.selection()) > 1:
            self.btn_download_all["state"] = tk.NORMAL
        else:
            self.btn_download_all["state"] = tk.DISABLED

        if self._download_list != [] or self._currentJob:
            self.btn_cancel["state"] = tk.NORMAL
        else:
            self.btn_cancel["state"] = tk.DISABLED

    def on_terminate_window(self):
        self._terminateJob, self._currentJob = self._currentJob, None
        for i in range(len(self._download_list), 0, -1):
            delete_url = self._download_list[i-1]
            self.tree.update_item_state(delete_url[0], "已取消")
            self._download_list.remove(delete_url)
        if(self._terminateJob):
            self.tree.update_item_state(self._terminateJob.get_url_full(), "未完成")
            threading.Thread(target=self._terminateJob.cancel_download).start()

    def on_cancel_all_download(self):
        self._cancel_all = True
        self.on_cancel_download()

    def on_cancel_download(self):
        if self._cancel_all or (self._currentJob and self._url == self._currentJob.get_url_full()):
            jjob, self._currentJob = self._currentJob, None
            if(jjob):
                self.tree.update_item_state(jjob.get_url_full(), "未完成")
                threading.Thread(target=jjob.cancel_download).start()
        else:
            for download_item in self._download_list:
                if download_item[0] == self._url:
                    self.tree.update_item_state(self._url, "已取消")
                    self._download_list.remove(download_item)
        self.toggle_download_button()

    def on_start_all_download(self):
        for it in self.tree.selection():
            data = self.tree.item(it)
            url_full = data['values'][0]
            self._download_list.append([url_full, data['values'][2]])
            self.tree.update_item_state(url_full, "等待中")
        self.toggle_download_button()
        if self._currentJob is None:
            threading.Timer(0.5, self._on_timer_downloading).start()

    def on_start_download(self):
        self._cancel_all = False
        self._get_entry_values()
        self._download_list.append([self._url, self.dest])
        self.tree.update_item_state(self._url, "等待中")
        self.toggle_download_button()
        if self._currentJob is None:
            threading.Timer(0.5, self._on_timer_downloading).start()

    def _on_timer_downloading(self):
        if self._currentJob:
            if self._currentJob.is_concurrent_dowload_completed():
                self._currentJob.end_concurrent_download()
                jjob, self._currentJob = self._currentJob, None
                self.tree.update_item_state(jjob.get_url_full(), "已下載")
                self.toggle_download_button()
                print('下載完成!')
                if self._download_list != []:
                    threading.Timer(0.5, self._on_timer_downloading).start()
            else:
                threading.Timer(0.5, self._on_timer_downloading).start()
        elif self._cancel_all :
            while self._download_list != []:
                download_url, download_dest = self._download_list.pop(0)
                self.tree.update_item_state(download_url, "已取消")
        elif self._download_list != [] :
            self.text.clear_contents()
            download_url, download_dest = self._download_list.pop(0)
            self._currentJob = M3U8Sites.CreateSite(download_url, download_dest)
            if self._currentJob:
                self.tree.update_item_state(download_url, "下載中")
                self._currentJob.begin_concurrent_download()
                threading.Timer(0.5, self._on_timer_downloading).start()
            else:
                if self.tree.isUrlExist(self._url):
                    self.tree.update_item_state(self._url, "網址錯誤")
                self._currentJob = None
                self.toggle_download_button()

    def _add_url_to_tree(self, url, savePath, showmsg=True):
        if not self.tree.isUrlExist(url):
            jjob = M3U8Sites.CreateSite(url, savePath)
            if jjob:
                self.tree.additem(url, jjob.target_name(), savePath)
                return True
            else:
                return False
        else:
            if showmsg:
                print(f"{url} 已存在下載清單中!!")
            return False

    def on_add_list(self):
        self.text.clear_contents()
        self._get_entry_values()
        if self.checkVideoLists(self._url):
            return False
        return self._add_url_to_tree(self._url, self.dest)

    def cancel_download(self):
        jjob, self._currentJob = self._currentJob, None
        if(jjob):
            threading.Thread(target=jjob.cancel_download).start()

    def load_on_create(self):
        self.tree.load_from_csv(os.path.join(os.getcwd(), "JableTV.csv"))

    def save_on_close(self):
        self.tree.save_to_csv(os.path.join(os.getcwd(), "JableTV.csv"))

    def _do_import_list(self):
        try:
            self.text.clear_contents()
            for i in range(5):
                while self._urls_list != []:
                    url = self._urls_list.pop(0)
                    if self._add_url_to_tree(url, self._import_dest, showmsg=False): break;
            if self._urls_list != []:
                threading.Timer(0.05, self._do_import_list).start()
            else:
                print("網址載入完成!!")
        except Exception:
            pass

    def on_import_list(self):
        self._get_entry_values()
        filename = tkinter.filedialog.askopenfilename()
        try:
            self._urls_list = []
            self._import_dest = self.dest
            with open(filename, "r", encoding='utf-8') as f:
                for line in f.readlines():
                    for site in M3U8Sites.siteList:
                        if site.skip_pattern: continue
                        result = re.findall(site.website_pattern, line)
                        if len(result) == 0: continue
                        for str in result:
                            self._urls_list.append(str.strip())
            if self._urls_list != []:
                threading.Timer(0.5, self._do_import_list).start()
            else:
                print("無有效的網址!!")
        except Exception:
            return

    def on_clear_text(self):
        self.text.clear_contents()

    def checkVideoLists(self, url):
        jlist = JableTVList(self._url)
        if not jlist.isVaildLinks(): return False
        self.videoList = JableTVVideoListWindow(self, jlist)
        return True


class JableTVVideoListWindow(tk.Toplevel):
    """JableTV downloader GUI Video listbox Window"""
    def __init__(self, master, jlist, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.jList:JableTVList = jlist
        self.mainWnd:JableTVDownloadWindow = master
        self.grab_set()
        self.title(f"[{jlist.getListType()}] 共有{jlist.getTotalPages()}頁，{jlist.getTotalLinks()}部影片")
        self.geometry('720x450')
        self.sortby = jlist.getSortType()
        self.create_widgets(jlist)
        self.loadPageAtIndex(jlist.getCurrentPage())

    def create_widgets(self, jlist:JableTVList):
        self.videoList = tk.Listbox(self, selectmode=tk.EXTENDED)
        self.videoList.pack(side=tk.TOP, fill='both', expand=True, padx=4, pady=4)

        frame1 = tk.Frame(self)
        frame1.pack(side=tk.TOP, fill='x', padx=12, pady=4)
        self.btn_first = tk.Button(frame1, text='<< 第一頁', command=self.on_first_page)
        self.btn_first.pack(side=tk.LEFT, padx=2)
        self.btn_prev  = tk.Button(frame1, text='< 前一頁', command=self.on_prev_page)
        self.btn_prev.pack(side=tk.LEFT, padx=2)
        self.txt_current = tk.Label(frame1, text='1', width=10)
        self.txt_current.pack(side=tk.LEFT, padx=2)
        self.btn_next  = tk.Button(frame1, text='下一頁 >', command=self.on_next_page)
        self.btn_next.pack(side=tk.LEFT, padx=2)
        self.btn_last  = tk.Button(frame1, text='最後頁 >>', command=self.on_last_page)
        self.btn_last.pack(side=tk.LEFT, padx=2)
        self.btn_any  = tk.Button(frame1, text='頁數...', command=self.on_any_page)
        self.btn_any.pack(side=tk.LEFT, padx=2)


        if self.sortby is not None:
            self.cbx_sortby = ttk.Combobox(frame1, values=jlist.getSortTypeList(), width=10, state='readonly');
            self.cbx_sortby.pack(side=tk.LEFT, padx=12)
            self.cbx_sortby.set(self.sortby)
            self.cbx_sortby.bind('<<ComboboxSelected>>', self.on_sortType_changed)

        self.btn_sel_quit = tk.Button(frame1, text='結束選取', command=self.on_select_quit)
        self.btn_sel_quit.pack(side=tk.RIGHT, padx=2)
        self.btn_sel_commit = tk.Button(frame1, text='加入清單', command=self.on_select_commit)
        self.btn_sel_commit.pack(side=tk.RIGHT, padx=12)

    def loadPageAtIndex(self, index):
        self.jList.loadPageAtIndex(index,self.sortby)
        self.videoList.delete(0, tk.END)
        linkDescs = self.jList.getLinkDescs()
        for desc in linkDescs:
            self.videoList.insert(tk.END, desc)
        self.txt_current['text']= f"{index+1}"
        totalPage = self.jList.getTotalPages()
        btnState = [tk.DISABLED,tk.DISABLED,tk.DISABLED,tk.DISABLED,tk.DISABLED]
        if totalPage != 1:
            btnState[4] = tk.NORMAL
            if index>0:
                btnState[0] = btnState[1] = tk.NORMAL
            if index < (totalPage-1):
                btnState[2] = btnState[3] = tk.NORMAL
        self.btn_first['state'] = btnState[0]
        self.btn_prev['state'] = btnState[1]
        self.btn_next['state'] = btnState[2]
        self.btn_last['state'] = btnState[3]
        self.btn_any['state'] = btnState[4]

    def on_first_page(self):
        self.loadPageAtIndex(0)

    def on_prev_page(self):
        nPage = self.jList.getCurrentPage() - 1
        if nPage<0: nPage = 0
        self.loadPageAtIndex(nPage)

    def on_next_page(self):
        nPage = self.jList.getCurrentPage() + 1
        if nPage >= self.jList.getTotalPages(): nPage = self.jList.getTotalPages() - 1
        self.loadPageAtIndex(nPage)

    def on_last_page(self):
        nPage = self.jList.getTotalPages() - 1
        self.loadPageAtIndex(nPage)

    def on_any_page(self):
        try:
            nPage = sd.askinteger(" ", "請輸入頁數", minvalue=1, maxvalue=self.jList.getTotalPages()) - 1
            self.loadPageAtIndex(nPage)
        except:
            pass
        self.grab_set()

    def on_select_commit(self):
        links = self.jList.getLinks()
        for i in self.videoList.curselection():
            self.mainWnd.append_url_to_queue_for_defer_insertion(links[i])

    def on_select_quit(self):
        self.destroy()

    def on_sortType_changed(self,event):
        self.sortby = self.cbx_sortby.get()
        self.loadPageAtIndex(self.jList.getCurrentPage())

if __name__ == "__main__":
    gui_main("", "download")
