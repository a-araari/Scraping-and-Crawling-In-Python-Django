import threading
import time
import logging
import traceback
import random

import requests
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium import webdriver
from bs4 import BeautifulSoup
from urllib.parse import urlsplit
from urllib.parse import urlparse
from collections import deque

from .models import tbl_crawl_task, tbl_crawl_task_data
from task1.options import WebScraper


logger = logging.getLogger(__name__)



class Crawl:
    def __init__(self, url, limit, waiting, scroll):
        self.url = url
        self.limit = int(limit)
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

        self.options = FirefoxOptions()
        self.options.add_argument('--incognito')
        self.options.add_argument('--headless')

        print('creating driver')
        self.driver = webdriver.Firefox(options=self.options)
        print('driver created')


    def get_url(self, link):
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

    # return status_code, url
    def get_page(self, url):
        if not url.startswith('http'):
            url = 'https:' + ('//' if not url.startswith('//') else '') + url

        response = requests.get(url)
        url = response.url
        code = response.status_code

        return code, url

    # return soup, error_text, success
    def get_full_page(self, url):
        print(type(self.driver))
        task = WebScraper(
            url=url,
            waiting=self.waiting,
            scroll=self.scroll,
            driver=self.driver
        )

        page_content, error_text, success = task.start_scraping()

        return BeautifulSoup(page_content, 'html.parser'), error_text, success

    def _crawl(self, soup, save, tbl, count=0, dpt=0):
        if count >= self.limit or soup is None:
            print(f'limit={self.limit} reached!')
            return

        links = soup.find_all('a')
        saved_links = list()

        print('#'*70, ' '*5, dpt, ' '*5, '#'*70)

        for sub_link in links:
            try:
                if count > self.limit:
                    break

                sub_url, internal = self.get_url(sub_link)
                if sub_url in self.processed_urls or sub_url.endswith('#'):
                    continue
                print('processing:', sub_url)
                self.processed_urls.append(sub_url)

                link_type = tbl_crawl_task_data.INTERNAL_LINK_TYPE if internal else tbl_crawl_task_data.EXTERNAL_LINK_TYPE

                code, valid_url = self.get_page(sub_url)
                sub_url = valid_url

                try:
                    if code in range(200, 300):
                        sub_soup, error_msg, succ = self.get_full_page(sub_url)
                        print('scrape succ:', succ)
                        if succ:
                            save(tbl, sub_url, link_type, code, dpt)
                            saved_links.append({"link": sub_url, "internal": internal, "soup": sub_soup})
                            count += 1
                except:
                    save(tbl, sub_url, link_type, code, dpt)

            except Exception as e:
                print('sublink exc:', repr(e))
                # traceback.print_exc()

        for sub_link_dict in saved_links:
            if count >= self.limit:
                return

            if not sub_link_dict['internal']:
                continue

            self._crawl(sub_link_dict['soup'], save, tbl, count=count, dpt=dpt+1)


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
    print('saving', url, ':', status_code, tbl)
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


max_same_time = 2


def _start_crawl_task(tbl):
    """
    Crawl work goes here!
    tbl saved each time status_code or status_process changed
    """
    pending_tasks = tbl_crawl_task.objects.filter(status_process=tbl_crawl_task.PROCESSING_STATUS).count()
    while pending_tasks > 2:
        print(pending_tasks, tbl.task_id, 'waiting')
        time.sleep(float(f'{random.randint(1, 5)}.{random.randint(100000, 999999)}'))
        pending_tasks = tbl_crawl_task.objects.filter(status_process=tbl_crawl_task.PROCESSING_STATUS).count()
        
    tbl.status_process = tbl_crawl_task.PROCESSING_STATUS
    tbl.save()

    status_code = None
    try:
        page = requests.get(tbl.url)
        tbl.status_code = page.status_code

        if page.status_code in range(200, 300):
            crw = Crawl(tbl.url, tbl.limit, tbl.waiting, tbl.scroll)

            succ, error_msg = crw.start_crawling(save, tbl)
            if succ:
                tbl.status_process = tbl_crawl_task.SUCCESS_STATUS
            else:
                tbl.status_process = tbl_crawl_task.ERROR_STATUS
                tbl.error_msg = error_msg
            
        else:
            tbl.status_process = tbl_crawl_task.ERROR_STATUS
            tbl.error_msg = f"Cannot connect server: code returned: {status_code}"

        print(tbl.error_msg)

    except Exception as e:
        tbl.status_process = tbl_crawl_task.ERROR_STATUS
        tbl.error_msg = repr(e)
        tbl.status_code = status_code
        print(repr(e))
        traceback.print_exc()

    finally:
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