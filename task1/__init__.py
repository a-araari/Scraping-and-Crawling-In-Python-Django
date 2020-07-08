from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from task2.models import Logger


driver = None
count = 0


def log(*text):
    l, created = Logger.objects.get_or_create(id=1)
    l.text = l.text + '\n' + str(text)
    l.save()


def get_driver():
    global driver, count
    
    log("Getting instance", count)

    if driver is None:

        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')

        driver = webdriver.Chrome('/usr/bin/chromedriver', options=options)
        count += 1
        log("new instance", count)

    return driver