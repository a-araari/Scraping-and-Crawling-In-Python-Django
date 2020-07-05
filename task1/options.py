import threading
import traceback
import time 
import re
import random

import requests
from requests.exceptions import ConnectionError as rce
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from bs4 import BeautifulSoup

from django.conf import settings

from .models import tbl_page_data


class WebScraper:
    """Web page scraper that scrape full page by providing the load button css class

        Attributes:
            url (str): web URL.
            waiting (int): waiting time after page load.
            scroll (int): max scroll height to be scraped.
    """
    def __init__(self, url, waiting, scroll, driver=None):
        """ Raise ValueError if url is not valid
        """ 
        self.url = url
        self.waiting = waiting
        self.scroll = scroll
        self.options = Options()
        self.options.add_argument('--incognito')
        self.options.add_argument('--headless')
        self.driver = driver
        self.quit = driver is None

        if not self.valid_url(self.url):
            raise ValueError(f'Unvalid Url: {self.url}')

    def valid_url(self, url):
        """Validate URLs, return True if url is True
        """
        regex = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
            r'localhost|' #localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        res = re.match(regex, url)

        return res is not None

    def scroll_down(self):
        return self.driver.execute_script("window.scroll({top: " + str(int(self.scroll * 40)) + ", left: 0, behavior: 'smooth'});")

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
        """) / 40)

    def get_content(self):
        return str(BeautifulSoup(self.driver.page_source, 'html.parser').prettify())

    def is_page_loaded(self, arg):
        resp = self.driver.execute_script('return document.readyState')
        # print('resp:', resp)
        return resp == 'complete'

    def wait_for_page_load(self):
        try:
            # print(f'waiting for page to be loaded')
            wait = WebDriverWait(self.driver, 30)
            wait.until(self.is_page_loaded)
        except:
            pass
        # print(f'waiting after page load for {self.waiting}\'s')
        time.sleep(self.waiting)

    def start_scraping(self):
        print('Creating driver..')
        self.driver = webdriver.Chrome('/usr/bin/chromedriver', options=self.options) if self.driver is None else self.driver
        print('Driver created!')

        page_content = ''
        try:

            print('Scraping the URL')
            self.driver.get(self.url)

            self.wait_for_page_load()

            page_content = self.get_content()
            # print(f'page content contain {len(page_content)} characters')
            old_scroll_top = -1
            new_scroll_top = self.get_scroll_top()
            # print(f'Initial page scroll count: {new_scroll_top} ')

            while new_scroll_top < self.scroll:
                # print('-'*20)
                if old_scroll_top == new_scroll_top:
                    break;

                self.scroll_down()

                self.wait_for_page_load()

                old_scroll_top = new_scroll_top
                new_scroll_top = self.get_scroll_top()
                print(f'New scroll count: {new_scroll_top}')

            print(f'Last page scroll count: {new_scroll_top} ')

            page_content = self.get_content()

            print('URL scraped!')

        except Exception as ex:
            traceback.print_exc()
            return page_content, repr(ex), False

        finally:
            if self.quit:
                self.driver.quit()

        return page_content, None, True


def get_pending_count():
    return tbl_page_data.objects.filter(status_process=tbl_page_data.PROCESSING_STATUS).count()

def _start_task(tbl):
    """
    Task work goes here!
    tbl saved each time status_code or status_process changed
    """

    pending_tasks = get_pending_count()
    while pending_tasks >= settings.RUNNING_TASKS_SIMULTANEOUSLY_COUNT:
        print(pending_tasks, tbl.task_id, 'waiting')
        time.sleep(float(f'{random.randint(1, 5)}.{random.randint(100000, 999999)}'))
        pending_tasks = get_pending_count()
        
    tbl.status_process = tbl_page_data.PROCESSING_STATUS
    tbl.save()
    try:
        # Check page status before scraping
        page = requests.get(tbl.url)

        tbl.status_code = page.status_code
        tbl.save()

        if page.status_code not in range(200, 300):
            tbl.status_process = tbl_page_data.ERROR_STATUS
            tbl.error_msg = f"page return {page.status_code} code"
            tbl.save()

            return

        task = WebScraper(
            url=tbl.url,
            waiting=int(tbl.waiting),
            scroll=int(tbl.scroll),
        )


        page_content, error_text, success = task.start_scraping()


        # save page content
        if success:
            tbl.page_content = page_content
        else:
            tbl.error_msg = error_text
        
        tbl.status_process = tbl_page_data.SUCCESS_STATUS if success else tbl_page_data.ERROR_STATUS

    except rce:
        tbl.status_process = tbl_page_data.ERROR_STATUS
        tbl.error_msg = f'URL not found: {tbl.url}'
    except Exception as e:
        tbl.status_process = tbl_page_data.ERROR_STATUS
        tbl.error_msg = "Cannot establish a connection with the url given!"

    finally:
        tbl.save()

def start_task(tbl):
    t = threading.Thread(target=_start_task, args=[tbl])
    t.setDaemon(True)
    t.start()


def delete_tbl(tbl):
    """
    Delete an instance on tbl_page_data
    None: this delete the instance without any confirmation!
    """
    tbl.delete()