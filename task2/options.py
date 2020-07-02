import threading
import time
import logging

import requests
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium import webdriver
from bs4 import BeautifulSoup
from urllib.parse import urlsplit
from urllib.parse import urlparse
from collections import deque

from .models import tbl_crawl_task, tbl_crawl_task_data


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
        self.base = '{0.netloc}'.format(self.linksparts) # e.g: www.youtube.com
        self.strip_base = self.base.replace('www.', '') # e.g: youtube.com
        self.base_url = '{0.scheme}://{0.netloc}'.format(self.linksparts)  # e.g: https://www.youtube.com
        # self.path = url[:url.rfind('/')+1] if '/' in self.linksparts.path else url

        self.processed_urls = []

        self.options = FirefoxOptions()
        self.options.add_argument('--incognito')
        self.options.add_argument('--headless')

        print('creating driver')
        self.driver = webdriver.Firefox(options=self.options)
        print('driver created')

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

    def get_soup(self):
        return BeautifulSoup(self.driver.page_source, 'html.parser')

    def scroll_down(self, current_scroll):
        return self.driver.execute_script("window.scroll({top: " + str(int(current_scroll + 100)) + ", left: 100, behavior: 'smooth'});")

    def get_scroll_top(self):
        return int(self.driver.execute_script("""
            if (window.pageYOffset != undefined) {
                return pageYOffset;
            } else {
                var sx, sy, d = document,
                    r = d.documentElement,
                    b = d.body;
                sx = r.scrollLeft || b.scrollLeft || 0;
                sy = r.scrollTop || b.scrollTop || 0;
                return sy;
            }
        """))

    def get_page(self, url):
        if not url.startswith('http'):
            url = 'https:' + ('//' if not url.startswith('//') else '') + url

        response = requests.get(url)
        url = response.url
        code = response.status_code

        soup = self.get_full_page(url)

        return soup, code, url

    def get_full_page(self, url):
        self.driver.get(url)

        soup = self.get_soup()
        old_scroll_top = -1
        new_scroll_top = self.get_scroll_top()

        while new_scroll_top < self.scroll:
            if old_scroll_top == new_scroll_top:
                time.sleep(self.waiting)
                new_scroll_top = self.get_scroll_top()

                if old_scroll_top == new_scroll_top:
                    break;

            print(old_scroll_top, new_scroll_top, self.scroll)

            self.scroll_down(self.scroll)

            old_scroll_top = new_scroll_top
            new_scroll_top = self.get_scroll_top()

        print(old_scroll_top, new_scroll_top, self.scroll)

        soup = self.get_soup()

        print('URL scraped!')

        return soup

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
            sub_soup, status_code, valid_url = self.get_page(sub_url)

            save(tbl, valid_url, tbl_crawl_task_data.INTERNAL_LINK_TYPE if internal else tbl_crawl_task_data.EXTERNAL_LINK_TYPE, status_code, depth_level)
            saved_links.append({"link": sub_url, "internal": internal, "soup": sub_soup})

        if self.count >= self.limit:
            return

        for sub_link_dict in saved_links:
            if self.count >= self.limit:
                return

            if not sub_link_dict['internal']:
                continue

            self._crawl(sub_link_dict['sub_soup'], save, tbl, count=self.count)

    def start_crawling(self, save, tbl):
        try:
            soup, status_code, valid_url = self.get_page(self.url)
            if status_code is not None:
                self._crawl(soup, save, tbl)
        except Exception as e:
            # passing the exception(just to quit the driver)
            raise e
        finally:

            self.driver.quit()

        return status_code


def _start_crawl_task(tbl):
    """
    Crawl work goes here!
    tbl saved each time status_code or status_process changed
    """
    status_code = None
    try:
        crw = Crawl(tbl.url, tbl.limit, tbl.waiting, tbl.scroll)

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
            tbl.error_msg = f'Cannot connect to {tbl.url}. status code: {status_code}'

        tbl.save()
    except Exception as e:
        print(repr(e))
        tbl.status_process = tbl_crawl_task.ERROR_STATUS
        tbl.error_msg = repr(e)
        tbl.status_code = status_code
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