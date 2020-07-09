from selenium import webdriver
from selenium.webdriver.chrome.options import Options


driver = None


def get_driver(force=False):
    global driver

    if force and driver is not None:
        driver.quit()
        driver = None

    if driver is None:

        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')

        driver = webdriver.Chrome('/usr/bin/chromedriver', options=options)

    return driver


pending = 0

def get_pending():
    global pending
    pending += 1

    return pending

def decrease_pending():
    global pending
    pending -= 1