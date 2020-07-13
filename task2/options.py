import threading
import time
import traceback
import random

import requests
from requests.exceptions import ConnectionError as rce
from bs4 import BeautifulSoup
from urllib.parse import urlsplit
from urllib.parse import urlparse
from collections import deque

from django.conf import settings

from .models import tbl_crawl_task, tbl_crawl_task_data
from task1.options import WebScraper
from .__init__ import get_driver, decrease_p, free_driver



class Crawl:
    def __init__(self, url, limit, waiting, scroll, driver):
        self.url = url
        self.limit = int(limit) - 1
        self.waiting = int(waiting)
        self.scroll = int(scroll)
        self.count = 1

        # extract base url to resolve relative
        self.linksparts = urlsplit(url)
        self.base = '{0.netloc}'.format(self.linksparts)
        self.strip_base = self.base.replace('www.', '')
        self.base_url = '{0.scheme}://{0.netloc}'.format(self.linksparts)
        self.path = url[:url.rfind('/')+1] if '/' in self.linksparts.path else url

        self.processed_urls = []
        self.saved_urls = []

        self.driver = driver

    def get_url(self, link):
        # extract link url from the anchor
        anchor = link.attrs['href'] if 'href' in link.attrs else ''
        anchor = anchor.replace('www.', '')

        if anchor.startswith('//'):
            return anchor[2:], True if self.strip_base in anchor[:len(self.strip_base) + 3 + (7 if anchor.startswith('http') else 1) ] else False
        elif anchor.startswith('/'):
            return (self.base_url + anchor), True
        elif anchor.startswith(self.base_url):
            return anchor, True
        else:
            # External url
            return anchor, False

    # return status_code, url
    def get_page(self, url):
        if not url.startswith('http'):
            url = 'https:' + ('//' if not url.startswith('//') else '') + url
        try:
            response = requests.get(url)
            url = response.url
            code = response.status_code

            return code, url
        except rce :
            raise Exception('URL not found')

    # return soup, error_text, success
    def get_full_page(self, url):
        task = WebScraper(
            url=url,
            waiting=self.waiting,
            scroll=self.scroll,
            driver=self.driver
        )

        page_content, error_text, success = task.start_scraping()

        return BeautifulSoup(page_content, 'html.parser'), error_text, success

    def _crawl(self, soup, save, tbl, count=0, dpt=0):
        if len(self.saved_urls) >= self.limit or soup is None:
            return

        links = soup.find_all('a')
        saved_links = list()

        for sub_link in links:
            if len(self.saved_urls) > self.limit:
                return

            try:
                sub_url, internal = self.get_url(sub_link)

                if sub_url in self.processed_urls or sub_url.endswith('#'):
                    continue
                self.processed_urls.append(sub_url)

                link_type = tbl_crawl_task_data.INTERNAL_LINK_TYPE if internal else tbl_crawl_task_data.EXTERNAL_LINK_TYPE

                code, valid_url = self.get_page(sub_url)
                sub_url = valid_url

                if sub_url not in self.saved_urls:
                    save(tbl, sub_url, link_type, code, dpt)
                    saved_links.append((sub_url, internal))
                    self.saved_urls.append(sub_url)
                    count += 1

            except Exception as e:
                pass

        for sub_link_list in saved_links:
            sub_link = sub_link_list[0]
            internal = sub_link_list[1]

            if len(self.saved_urls) > self.limit:
                return

            if not internal:
                continue

            try:
                sub_url = sub_link
            
                sub_soup, error_msg, succ = self.get_full_page(sub_url)

                print('succ', succ, error_msg)

                if succ and internal:
                    self._crawl(sub_soup, save, tbl, count=count, dpt=dpt+1)

            except Exception as e:
                pass


    def start_crawling(self, save, tbl):
        soup, error_text, success = self.get_full_page(tbl.url)

        try:
            if success:
                self._crawl(soup, save, tbl)
                return True, ''
            else:
                return False, error_text
        finally:
            self.driver.quit()


def save(tbl, url, link_type, status_code, depth_level):
    if status_code is None:
        status_code = -1
    tbl_data = tbl_crawl_task_data(
        task_id=tbl,
        url=url,
        link_type=link_type,
        status_code=status_code,
        depth_level=depth_level
    )
    tbl_data.save()


def get_pending_count():
    return tbl_crawl_task.objects.filter(status_process=tbl_crawl_task.PROCESSING_STATUS).count()


def decrease(pt):
    try:
        all_gt = tbl_crawl_task.objects.filter(pending_task__gte=pt)
        for t in all_gt:
            try:
                if t.pending_task == 0:
                    continue
                t.pending_task = t.pending_task - 1
                t.save()
            except:
                pass
    except:
        pass


def _start_crawl_task(tbl):
    """
    Crawl work goes here!
    tbl saved each time status_code or status_process changed
    """
    driver = None
    index = None
    try:
        pending_tasks = get_pending_count()
        while pending_tasks >= settings.MAX_CRAWL_COUNT or tbl.pending_task >= settings.MAX_CRAWL_COUNT:
            tbl = tbl_crawl_task.objects.get(task_id=tbl.task_id)
            time.sleep(1)
            pending_tasks = get_pending_count()

        tbl.pending_task = 0            
        tbl.status_process = tbl_crawl_task.PROCESSING_STATUS
        tbl.save()

        status_code = None
        t = 0
        
        driver, index = get_driver()
        while t < 3:
            try:
                page = requests.get(tbl.url)
                tbl.status_code = page.status_code

                if page.status_code in range(200, 300):

                    crw = Crawl(tbl.url, tbl.limit, tbl.waiting, tbl.scroll, driver)

                    crw.saved_urls.append(tbl.url)

                    succ, error_msg = crw.start_crawling(save, tbl)
                    if succ:
                        tbl.status_process = tbl_crawl_task.SUCCESS_STATUS
                    else:
                        tbl.status_process = tbl_crawl_task.ERROR_STATUS
                        tbl.error_msg = error_msg
                    
                else:
                    tbl.status_process = tbl_crawl_task.ERROR_STATUS
                    tbl.error_msg = f"Cannot connect server: code returned: {status_code}"

                break
            except rce:
                tbl.status_process = tbl_crawl_task.ERROR_STATUS
                tbl.error_msg = f'URL not found: {url}'
                tbl.status_code = status_code
            except Exception as e:
                traceback.print_exc()
                print(repr(e))
                tbl.status_process = tbl_crawl_task.ERROR_STATUS
                tbl.error_msg = repr(e) # "Server memory is Full, server cannot crawl more urls"
                tbl.status_code = status_code

            finally:
                t += 1
                tbl.pending_task = 0
                tbl.save()
    finally:
        if index:
            free_driver(index)
        decrease_p()
        decrease(tbl.pending_task)
            

def start_crawl_task(tbl):
    t = threading.Thread(target=_start_crawl_task, args=[tbl])
    t.setDaemon(True)
    t.start()


def delete_tbl(tbl):
    """
    Delete an instance on tbl_crawl_task
    None: this delete the instance without any confirmation!
    """
    tbl.delete()