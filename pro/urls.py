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

urlpatterns = [
    path('admin/', admin.site.urls),

    # task1 api app
    path('page_data/', include('task1.urls')),

    # task2 api app
    path('crawl/', include('task2.urls')),
]


# ---------- Restart Uncompleted tasks on server cruch ----------
def run_p_task(task):
    print(task.task_id)


def run_n_task(task):
    print(task.task_id)
    

init_restart_done = False

def init_restart_tasks():
    global init_restart_done

    if not init_restart_done:
        init_restart_done = True
    else:
        return

    p_tasks = tbl_page_data.filter(process_status=tbl_page_data.PROCESS_STATUS)
    n_tasks = tbl_page_data.filter(process_status=tbl_page_data.NONE_STATUS)

    for p in p_tasks:
        run_p_task(p)

    for n in n_tasks:
        run_n_task(n)


init_restart_tasks()
# ---------------------------------------------------------------
