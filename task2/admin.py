from django.contrib import admin

from .models import tbl_crawl_task, tbl_crawl_task_data, Logger


@admin.register(tbl_crawl_task)
class tbl_crawl_taskAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'url', 'status_process')


@admin.register(tbl_crawl_task_data)
class tbl_crawl_taskAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'url', 'depth_level')


@admin.register(Logger)
class LoggertaskAdmin(admin.ModelAdmin):
    list_display = ('text',)