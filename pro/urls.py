"""pro URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from task1.models import tbl_page_data
from task1 import options
from task1.__init__ import set_p as set_p1
from task2.models import tbl_crawl_task
from task2 import options as options2
from task2.__init__ import set_p as set_p2


urlpatterns = [
    path('admin/', admin.site.urls),

    # task1 api app
    path('page_data/', include('task1.urls')),

    # task2 api app
    path('crawl/', include('task2.urls')),
]


# ---------- Restart Uncompleted tasks on server cruch ----------
def run_p_p_task(task):
    # starting the task in a seperate Thread
    # see options.py
    options.start_task(task, force=True)


def run_p_n_task(task):
    options.start_task(task)
        

def run_c_p_task(task):
    # starting the task in a seperate Thread
    # see options.py
    options2.start_crawl_task(task, force=True)


def run_c_n_task(task):
    options2.start_crawl_task(task)
        

init_restart_done = False

def init_restart_tasks():
    global init_restart_done

    if init_restart_done:
        return

    init_restart_done = True

    p_p_tasks = tbl_page_data.objects.filter(status_process=tbl_page_data.PROCESSING_STATUS)
    p_n_tasks = tbl_page_data.objects.filter(status_process=tbl_page_data.NONE_STATUS)

    if p_p_tasks.count() == 0:
        options.decrease(0)

    for p in p_p_tasks:
        run_p_p_task(p)

    for n in p_n_tasks:
        run_p_n_task(n)


    c_p_tasks = tbl_crawl_task.objects.filter(status_process=tbl_crawl_task.PROCESSING_STATUS)
    c_n_tasks = tbl_crawl_task.objects.filter(status_process=tbl_crawl_task.NONE_STATUS)

    if c_p_tasks.count() == 0:
        options2.decrease(0)

    for p in c_p_tasks:
        try:
            p.tbl_crawl_task_data_set.all().delete()
        except:
            pass
        run_c_p_task(p)

    for n in c_n_tasks:
        run_c_n_task(n)

set_p = False


def set_p_count():
    global set_p
    if set_p:
        return

    set_p = True

    p_p_count = tbl_crawl_task.objects.filter(status_process=tbl_crawl_task.PROCESSING_STATUS).count()
    p_n_count = tbl_crawl_task.objects.filter(status_process=tbl_crawl_task.NONE_STATUS).count()

    set_p1(p_p_count + p_n_count - 1)

    c_p_count = tbl_crawl_task.objects.filter(status_process=tbl_crawl_task.PROCESSING_STATUS).count()
    c_n_count = tbl_crawl_task.objects.filter(status_process=tbl_crawl_task.NONE_STATUS).count()

    set_p2(c_p_count + c_n_count - 1)


set_p_count()

init_restart_tasks()
# ---------------------------------------------------------------