import threading
import time

import requests
import requests.exceptions
from bs4 import BeautifulSoup
from urllib.parse import urlsplit
from urllib.parse import urlparse
from collections import deque

from .models import tbl_crawl_task, tbl_crawl_task_data


class Crawl:
    def __init__(self, url, limit):
        self.url = url
        self.limit = int(limit)
        self.count = 1

        # extract base url to resolve relative
        self.linksparts = urlsplit(url)
        self.base = '{0.netloc}'.format(self.linksparts) # e.g: www.youtube.com
        self.strip_base = self.base.replace('www.', '') # e.g: youtube.com
        self.base_url = '{0.scheme}://{0.netloc}'.format(self.linksparts)  # e.g: https://www.youtube.com
        # self.path = url[:url.rfind('/')+1] if '/' in self.linksparts.path else url
        self.processed_urls = []

    def get_page(self, url, waiting=0):
        # wait
        time.sleep(waiting)
        print(f'waiting for {waiting} seconds')

        if not url.startswith('http'):
            url = 'https:' + ('//' if not url.startswith('//') else '') + url
        try:
            response = requests.get(url)
            url = response.url
            code = response.status_code
        except Exception as e:
            print(e)
            return None, None, url

        soup = BeautifulSoup(response.text, 'html.parser')
        return soup, code, url

    def get_url(self, link):
        self.count += 1
        # extract link url from the anchor
        anchor = link.attrs['href'] if 'href' in link.attrs else ''
        anchor = anchor.replace('www.', '')

        if anchor.startswith('//'):
            return (anchor[2:], True)
        elif anchor.startswith('/'):
            return (self.base_url + anchor, True)
        elif self.strip_base in anchor[:len(self.strip_base) + 7 + 4]: # +7 for https:// and +4 for www.
            return (anchor, True)
        else:
            # External url
            return anchor, False

    def get_depth(self, url):
        count = url.replace('//', '').count('/')
        return  count - 1 if url.endswith('/') else count 

    def _crawl(self, soup, save, tbl, count=0):
        if self.count >= self.limit or soup is None:
            print(f'limit={self.limit} reached!')
            return

        links = soup.find_all('a')
        saved_links = list()

        for sub_link in links:
            if self.count > self.limit:
                break

            sub_url, internal = self.get_url(sub_link)
            
            if sub_url in self.processed_urls or sub_url.endswith('#'):
                self.count -= 1
                continue

            print('processing', sub_url)
            self.processed_urls.append(sub_url)
            depth_level = self.get_depth(sub_url)
            sub_soup, status_code, valid_url = self.get_page(sub_url, int(tbl.waiting))

            save(tbl, valid_url, tbl_crawl_task_data.INTERNAL_LINK_TYPE if internal else tbl_crawl_task_data.EXTERNAL_LINK_TYPE, status_code, depth_level)
            saved_links.append({"link": sub_url, "internal": internal})

        if self.count >= self.limit:
            return

        for sub_link_dict in saved_links:
            if self.count >= self.limit:
                return

            if not sub_link_dict['internal']:
                continue

            self._crawl(sub_soup, save, tbl, count=self.count)

    def start_crawling(self, save, tbl):
        soup, status_code, valid_url = self.get_page(self.url, int(tbl.waiting))
        if status_code is not None:
            self._crawl(soup, save, tbl)
            
        return status_code


def _start_crawl_task(tbl):
    """
    Crawl work goes here!
    tbl saved each time status_code or status_process changed
    """
        
    crw = Crawl(tbl.url, tbl.limit)

    def save(task_id, url, link_type, status_code, depth_level):
        print('saving', url, ':', status_code)
        if status_code is None:
            status_code = -1
        tbl_data = tbl_crawl_task_data(
            task_id=task_id,
            url=url,
            link_type=link_type,
            status_code=status_code,
            depth_level=depth_level
        )
        tbl_data.save()

    status_code = crw.start_crawling(save, tbl)
    tbl.status_code = status_code

    if status_code is not None and status_code in range(200, 300):
        tbl.status_process = tbl_crawl_task.SUCCESS_STATUS
    else:
        tbl.status_process = tbl_crawl_task.ERROR_STATUS
        tbl.error_mesg = f'Cannot connect to {tbl.url}. status code: {status_code}'

    tbl.save()


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