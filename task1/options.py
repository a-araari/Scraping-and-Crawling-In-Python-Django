import threading

from bs4 import BeautifulSoup
import requests

from .models import tbl_page_data

def _start_task(tbl):
    """
    Task work goes here!
    tbl saved each time status_code or status_process changed
    """
    page = requests.get(tbl.url)

    tbl.status_code = page.status_code
    tbl.save()


    # check status code, return if status code not 2xx
    if page.status_code not in range(200, 300):
        tbl.status_process = tbl_page_data.ERROR_STATUS
        tbl.error_msg = "url doesn't return 2xx status code"
        tbl.save()

        return

    # page loaded successfully, continue
    tbl.status_process = tbl_page_data.PROCESSING_STATUS
    tbl.save()

    soup = BeautifulSoup(page.content, 'html.parser')

    # save page content
    tbl.page_content = soup.prettify()
    tbl.status_process = tbl_page_data.SUCCESS_STATUS

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