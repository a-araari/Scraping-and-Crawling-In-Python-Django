from django.conf import settings
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')

# (Webdriver: driver, Boolean: free)
driver_list = []

def _get_driver():
    global options

    return webdriver.Chrome('/usr/bin/chromedriver', options=options)

    
def init_driver_list():
    for i in range(settings.MAX_SCRAPE_COUNT):
        driver_list.append((get_driver, True))


def get_driver():
    try:
        global driver_list

        if len(driver_list) == 0:
            init_driver_list()

        driver = index = None
        for i in range(settings.MAX_SCRAPE_COUNT):
            if driver_list[i][1] == True:
                driver_list[i][1] = False
                driver = driver_list[i][0]
                index = i

        return driver, index
    except Exception as e:
        print(repr(e))
        raise e


def free_driver(index):
    driver_list[index][1] = True


p = -1

def get_p():
    global p

    p += 1
    return p


def decrease_p():
    global p

    p -= 1
