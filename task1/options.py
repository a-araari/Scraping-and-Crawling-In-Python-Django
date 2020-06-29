import threading
import time 
import re

from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import requests

from .models import tbl_page_data


class WebScraper:
    """Web page scraper that scrape full page by providing the load button css class

        Attributes:
            url (str): web URL.
            load_btn_css_selector (str): load button css selector.
            waiting (int): waiting time after page load.
            scroll (int): max scroll height to be scraped.
    """
    def __init__(self, url, load_btn_css_selector, waiting, scroll):
        """ Raise ValueError if url is not valid
        """ 
        self.url = url
        self.load_btn_css_selector = load_btn_css_selector
        self.waiting = waiting
        self.scroll = scroll
        self.options = FirefoxOptions()
        self.options.add_argument('--incognito')
        self.options.add_argument('--headless')

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

    def get_scroll_count(self):
        return int(self.driver.execute_script("return document.documentElement.scrollHeight"))

    def get_content(self):
        return str(BeautifulSoup(self.driver.page_source, 'html.parser'))

    def start_scraping(self):
        print('Creating driver..')
        self.driver = webdriver.Firefox(options=self.options)
        print('Driver created!')

        page_content = ''
        try:

            print('Scraping the URL')
            self.driver.get(self.url)

            time.sleep(self.waiting)

            try:
                load_more_btn = self.driver.find_element_by_css_selector(self.load_btn_css_selector)
                page_content = self.get_content()
                old_scroll_count = 0
                new_sroll_count = self.get_scroll_count()
           
                while load_more_btn.is_displayed():
                    load_more_btn.click()
                    WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.load_btn_css_selector))).click()

                    old_scroll_count = new_sroll_count
                    new_sroll_count = self.get_scroll_count()

                    print(old_scroll_count, new_sroll_count, self.scroll)

                    if new_sroll_count > self.scroll:
                        print('scroll limit!')
                        break
            except:
                page_content = self.get_content()

            print('URL scraped!')

        except Exception as ex:
            return page_content, repr(ex), False
        finally:
            self.driver.quit()

        return page_content, None, True

def _start_task(tbl):
    """
    Task work goes here!
    tbl saved each time status_code or status_process changed
    """
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
            load_btn_css_selector='.button.J_LoadMoreButton',
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


    except Exception as e:
        tbl.status_process = tbl_page_data.ERROR_STATUS
        tbl.error_msg = str(e)

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