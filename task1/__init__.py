import traceback

from django.conf import settings
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

chrome_options = ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')

# (Webdriver: driver, Boolean: free)
init = False
driver_list = []

def _get_driver():
    global chrome_options
    print('SCRAPE:', 'getting new driver')

    return webdriver.Chrome('/usr/bin/chromedriver', options=chrome_options)

    
def init_driver_list():
    global driver_list
    print('SCRAPE:', 'init drivers')
    for i in range(settings.MAX_SCRAPE_COUNT):
        driver_list.append([_get_driver(), True])


def get_driver():
    global driver_list, init
    try:

        print('SCRAPE:', 'G-D')
        if not init:
            init = True
            init_driver_list()

        driver = index = None
        for i in range(len(driver_list)):
            if driver_list[i][1] == True:
                driver_list[i][1] = False
                driver = driver_list[i][0]
                index = i
                break

        print('SCRAPE:', 'Driver', index, 'is available')

        return driver, index
    except Exception as e:
        traceback.print_exc()
        raise e


def free_driver(index):
    print('SCRAPE:', 'Freeing driver', index)
    driver_list[index][1] = True


p = -1

def get_p():
    global p

    p += 1
    return p


def decrease_p():
    global p

    p -= 1
