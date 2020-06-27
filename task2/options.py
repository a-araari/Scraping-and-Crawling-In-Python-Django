import threading

from bs4 import BeautifulSoup
import requests
import requests.exceptions
from urllib.parse import urlsplit
from urllib.parse import urlparse
from collections import deque


from .models import tbl_crawl_task, tbl_crawl_task_data






class Crawl:
    def __init__(self, url):
        self.url = url

        # extract base url to resolve relative
        self.linksparts = urlsplit(url)
        self.base = '{0.netloc}'.format(self.linksparts)
        self.strip_base = self.base.replace('www.', '')
        self.base_url = '{0.scheme}://{0.netloc}'.format(self.linksparts)
        self.path = url[:url.rfind('/')+1] if '/' in self.linksparts.path else url
        self.processed_urls = []

    def get_soup(self, url):
        try:
            response = requests.get(url)
            code = response.status_code
        except Exception as e:
            print(e)
            return None, None

        soup = BeautifulSoup(response.text, 'html.parser')
        return soup, code

    def get_url(self, link):
        # extract link url from the anchor
        anchor = link.attrs['href'] if 'href' in link.attrs else ''

        if anchor.startswith('//'):
            return (anchor[2:], True)
        elif anchor.startswith('/'):
            return (self.base_url + anchor, True)
        elif self.strip_base in anchor:
            return (anchor, True)
        else:
            # External url
            return anchor, False

    def get_depth(self, url):
        count = url.replace('//', '').count('/')
        return  count - 1 if url.endswith('/') else count 

    def _crawl(self, soup, save, tbl):
        if soup is None:
            return

        links = soup.find_all('a')

        for sub_link in links:
            sub_url, internal = self.get_url(sub_link)
            if sub_url in self.processed_urls or sub_url.endswith('#'):
                continue

            print('processing', sub_url)
            self.processed_urls.append(sub_url)
            depth_level = self.get_depth(sub_url)
            sub_soup, status_code = self.get_soup(sub_url)

            save(tbl, sub_url, tbl_crawl_task_data.INTERNAL_LINK_TYPE if internal else tbl_crawl_task_data.EXTERNAL_LINK_TYPE, status_code, depth_level)

            if not internal:
                return

            self._crawl(sub_soup, save, tbl)

    def start_crawling(self, save, tbl):
        soup, status_code = self.get_soup(self.url)
        if status_code is not None:
            self._crawl(soup, save, tbl)
        else:
            save(tbl, self.url, tbl_crawl_task_data.INTERNAL_LINK_TYPE, status_code, 0)
            raise Exception(status_code)



def _start_crawl_task(tbl):
    """
    Crawl work goes here!
    tbl saved each time status_code or status_process changed
    """
        
    crw = Crawl(tbl.url)

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

    try:
        crw.start_crawling(save, tbl)
        tbl.status_process = tbl_crawl_task.SUCCESS_STATUS
    except Exception as e:
        tbl.status_process = tbl_crawl_task.ERROR_STATUS
        tbl.error_mesg = f'Cannot connect to {tbl.url}. status code: {str(e)}'
        tbl.status_code = int(str(e))
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